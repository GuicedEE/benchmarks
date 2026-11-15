"""Render the current evidence grids; --check verifies without rewriting reports.

Selections are complete named variants from explicit batches, never individual starts.
The raw results and their retention manifest are read-only inputs.
"""
import argparse
import collections
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import statistics
from compare_builds import validate as validate_builds


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = ROOT
LATEST = None
MIB = 2 ** 20
LABELS = {
    'guicedee': 'GuicedEE SPI / full JDK',
    'guicedee-scan': 'GuicedEE scanner / full JDK',
    'guicedee-jlink': 'GuicedEE SPI / application jlink',
    'guicedee-scan-jlink': 'GuicedEE scanner / application jlink',
    'guicedee-native': 'GuicedEE SPI / native',
    'quarkus': 'Quarkus wrapped SDKs / fast-JAR',
    'quarkus-standard': 'Quarkus upstream SDKs / fast-JAR',
    'quarkus-native': 'Quarkus wrapped SDKs / native',
    'quarkus-standard-native': 'Quarkus upstream SDKs / native',
}
GROUPS = {}
PHASES = []


def read(relative):
    if relative == 'results/jlink-audit-verification.json':
        return LATEST['jlinkAudit']
    _, batch, filename = relative.split('/')
    return LATEST['batches'][batch][Path(filename).stem]


def stats(values):
    return dict(median=statistics.median(values), minimum=min(values), maximum=max(values))


def collect_builds(evidence):
    raw = json.loads(evidence.read_text(encoding='utf-8'))
    validate_builds(raw)
    if not raw['eligible']:
        raise ValueError('Build cohort is not eligible')
    result = {key: raw[key] for key in ['measuredAt', 'runs', 'protocol', 'platform', 'cpuCount',
                                       'maven', 'java', 'guicedeeArtifactVersion']}
    result['container'] = raw.get('container')
    result['sharedSources'] = {key:value for key, value in raw['sourceFiles'].items()
                               if key.startswith('common/src/main/java/bench/')}
    result['nativeSources'] = {key:value for key, value in raw['sourceFiles'].items()
                               if key.startswith('guicedee-native/')}
    result['variants'] = {}
    for name in raw['variants']:
        values = {}
        for goal in ['compile', 'package']:
            rows = [r for r in raw['samples'] if r['variant'] == name and r['goal'] == goal]
            if rows:
                values[goal] = dict(stats([r['wallSeconds'] for r in rows]), samples=len(rows))
                if all('nativeCompilerPeakRssGB' in row for row in rows):
                    values[goal]['nativeCompilerPeakRssGB'] = stats([row['nativeCompilerPeakRssGB'] for row in rows])
        result['variants'][name] = values
    for name, values in result['variants'].items():
        baseline = 'quarkus-standard-native' if name.endswith(('-native', '-jlink')) else 'quarkus-standard'
        for goal, item in values.items():
            reference = result['variants'].get(baseline, {}).get(goal)
            if reference:
                item['baseline'] = baseline
                item['differencePercent'] = (item['median'] / reference['median'] - 1) * 100
    return result


def verify_build_runtime_sources(data, image_inputs):
    expected = data['builds']['sharedSources']
    if not expected:
        raise ValueError('Build evidence is missing the shared workload source hashes')
    for group, values in data['groups'].items():
        if group == 'local-windows':
            continue
        for name, item in values['variants'].items():
            actual = {e['path']:e['sha256'] for e in image_inputs.get(item['image'], {}).get('sharedSourceHashes', [])}
            if actual != expected:
                raise ValueError(f'Build/runtime workload source mismatch: {group}/{name}')
    if data.get('nativeAudit'):
        native_sources = data['builds']['nativeSources']
        for path, digest in data['nativeAudit']['sourceSha256'].items():
            if native_sources.get(path) != digest:
                raise ValueError(f'Build/runtime native policy source mismatch: {path}')


def collect_native_audit(path, current_image):
    global LATEST
    raw = json.loads(path.read_text(encoding='utf-8'))
    if raw['currentImage'] != current_image:
        raise ValueError('Native audit does not describe the current executable')
    saved = LATEST
    cohorts = {}
    try:
        for key in ['comparison', 'providerOverride']:
            batch = raw[key]
            LATEST = {'batches': {batch['batch']: batch}}
            cohorts[key] = collect_group([batch['batch']], None)
    finally:
        LATEST = saved
    return {**{k:v for k,v in raw.items() if k not in ['comparison', 'providerOverride']}, **cohorts}


def build_sections(data):
    values = data['builds']['variants']
    reference = values['quarkus-standard']
    spi = values['guicedee']
    linked_spi = values['guicedee-jlink']['package']['median']
    linked_scan = values['guicedee-scan-jlink']['package']['median']
    native_g = values['guicedee-native']['package']['median']
    native_q = values['quarkus-standard-native']['package']['median']
    def difference(a, b):
        delta = (a / b - 1) * 100
        return f"{abs(delta):.1f}% {'less' if delta < 0 else 'more'} time"
    headline = (
        f"**Clean JVM build:** GuicedEE SPI compiles in **{spi['compile']['median']:.2f} s** versus "
        f"**{reference['compile']['median']:.2f} s** for Quarkus "
        f"(**{difference(spi['compile']['median'], reference['compile']['median'])}**). "
        f"Complete runnable JVM packaging takes **{spi['package']['median']:.2f} / "
        f"{reference['package']['median']:.2f} s** (GuicedEE / Quarkus), "
        f"**{difference(spi['package']['median'], reference['package']['median'])}**. "
        f"Medians of {data['builds']['runs']} clean, offline builds per task; dependency preparation is excluded.\n\n"
        f"**jlink versus native build:** GuicedEE SPI/scanner jlink packages in "
        f"**{linked_spi:.2f} / {linked_scan:.2f} s**, versus **{native_q:.2f} s** for Quarkus native "
        f"(**{difference(linked_spi, native_q)} / {difference(linked_scan, native_q)}**).")
    rows = []
    for name, item in values.items():
        package = item['package']
        compile_time = item.get('compile')
        rows.append([LABELS[name], number(item.get('compile', {}).get('median')),
                     f"{compile_time['minimum']:.2f}–{compile_time['maximum']:.2f}" if compile_time else '—',
                     number(package['median']), f"{package['minimum']:.2f}–{package['maximum']:.2f}",
                     'Quarkus native' if package['baseline'] == 'quarkus-standard-native' else 'Quarkus fast-JAR',
                     f"{package['differencePercent']:+.1f}%" if name.startswith('guicedee') else 'Baseline'])
    grid = table(['Artifact', 'Clean compile (s)', 'Compile min–max (s)', 'Complete package (s)', 'Package min–max (s)',
                  'Build baseline', 'Package difference'], rows)
    tradeoffs = []
    for name, item in values.items():
        group = 'native-standard' if name.endswith('-native') else 'jvm-default'
        runtime = data['groups'][group]['variants'][name]
        tradeoffs.append([LABELS[name], number(item['package']['median']),
                          number(runtime['launchToFirstBusinessMs']['median'] / 1000, 3),
                          number(runtime['warm']['p50Ms'])])
    phases = data['phases']
    guice = phases['SPI jlink']['workload']['vendor-client-initialization'] / 1000
    quarkus = phases['Quarkus upstream JVM']['workload']['vendor-client-initialization'] / 1000
    sdk = (f"**Commercetools first-use initialization:** GuicedEE SPI jlink records **{guice:.3f} s** "
           f"versus **{quarkus:.3f} s** for standard Quarkus JVM: **{quarkus-guice:.3f} s less** "
           f"(**{difference(guice, quarkus)}**). These are instrumented phase diagnostics "
           f"(GuicedEE n={phases['SPI jlink']['starts']}, Quarkus n={phases['Quarkus upstream JVM']['starts']}), "
           'separate from build time and the uninstrumented runtime rankings. The samples identify a first-use cost; '
           'they do not establish its cause or a general SDK performance ratio.')
    interpretation = (
        f"GuicedEE's JVM package requires **{difference(spi['package']['median'], reference['package']['median'])}** "
        'than Quarkus fast-JAR.\n\n'
        f"**jlink versus native:** SPI/scanner jlink take **{linked_spi:.2f} / {linked_scan:.2f} s**. "
        f"Against Quarkus native's **{native_q:.2f} s**, that is **{difference(linked_spi, native_q)} / "
        f"{difference(linked_scan, native_q)}**; against GuicedEE native's **{native_g:.2f} s**, it is "
        f"**{difference(linked_spi, native_g)} / {difference(linked_scan, native_g)}**.\n\n"
        f"The complete GuicedEE native build takes **{native_g:.2f} s** versus **{native_q:.2f} s**, "
        f"or **{difference(native_g, native_q)}**. jlink produces a bundled JVM runtime; native builds produce "
        'ahead-of-time executables. The runtime grid shows the startup and request-latency tradeoffs for each artifact.')
    sections = {'build-headline': headline, 'build-grid': grid, 'build-findings': interpretation, 'build-runtime': table(
        ['Artifact', 'Complete package (s)', 'Full-business startup (s)', 'Warm p50 (ms)'], tradeoffs),
        'sdk-headline': sdk}
    memory = []
    for name in ['guicedee-native', 'quarkus-standard-native']:
        item = values[name]['package']
        if item.get('nativeCompilerPeakRssGB'):
            rss = item['nativeCompilerPeakRssGB']
            memory.append([LABELS[name], item['samples'], f"{rss['median']:.2f}",
                           f"{rss['minimum']:.2f}–{rss['maximum']:.2f}"])
    if memory:
        sections['build-memory'] = table(['Native compiler', 'Builds', 'Median peak RSS (GB)', 'Min–max (GB)'], memory)
    return sections


def collect_group(batches, selected):
    grouped = collections.defaultdict(list)
    environments = []
    all_rows = []
    for batch in batches:
        summary = read(f'results/{batch}/summary.json')
        environment = read(f'results/{batch}/environment.json')
        if not summary['eligibleComparison'] or summary.get('instrumented'):
            raise ValueError(f'Not an eligible, uninstrumented comparison: {batch}')
        variants = [v['id'] for v in summary['variants']]
        expected = {(v, run) for v in variants for run in range(1, environment['arguments']['runs'] + 1)}
        actual = [(r['variant'], r['run']) for r in summary['runs']]
        if len(actual) != len(set(actual)) or set(actual) != expected:
            raise ValueError(f'Incomplete or duplicated variant/start matrix: {batch}')
        for row in summary['runs']:
            if (not row['eligible'] or row.get('instrumented') or row['firstBusinessStatus'] != 200
                    or len(row['checks']) != 15 or not all(c['passed'] for c in row['checks'].values())
                    or row['warm']['failures'] or not all(s['ok'] for s in row['samples'])
                    or len(row['samples']) != environment['arguments']['requests']):
                raise ValueError(f'Failed/incomplete result: {batch}/{row["variant"]}/{row["run"]}')
            if environment['arguments']['docker']:
                container = row['container']
                if (container['nanoCpus'] != 250_000_000 or container['memoryBytes'] != 500 * MIB
                        or container['memorySwapBytes'] != 500 * MIB or container['state']['OOMKilled']
                        or container['image'] != environment['images'][row['variant']]):
                    raise ValueError(f'Container identity or quota mismatch: {batch}')
            all_rows.append(row)
            if selected is None or row['variant'] in selected:
                grouped[row['variant']].append((batch, row, environment))
        environments.append(environment)
    if selected is not None and set(grouped) != set(selected):
        raise ValueError('Missing selected variant')
    for environment in environments[1:]:
        for key in ['images', 'flags', 'cpuQuota', 'profile', 'platform']:
            if environment[key] != environments[0][key]:
                raise ValueError(f'Cannot pool differing {key}')
    result = {'batches': batches, 'batchStarts': len(all_rows),
              'batchCapabilityChecks': sum(len(r['checks']) for r in all_rows),
              'batchMeasuredRequests': sum(len(r['samples']) for r in all_rows),
              'warmupsPerStart': environments[0]['arguments']['warmup'],
              'requestsPerStart': environments[0]['arguments']['requests'], 'variants': {}}
    for name, entries in grouped.items():
        rows = [r for _, r, _ in entries]
        env = entries[0][2]
        base = re.sub(r'-(before|after)$', '', name)
        item = dict(label=LABELS[base], starts=len(rows),
                    capabilityChecks=sum(len(r['checks']) for r in rows),
                    measuredRequests=sum(len(r['samples']) for r in rows),
                    image=env.get('images', {}).get(name),
                    imageMiB=env.get('imageSizeBytes', {}).get(name, 0) / MIB or None,
                    rowSources=[f'{b}/{r["variant"]}/{r["run"]}' for b, r, _ in entries])
        for key in ['launchToReadyMs', 'firstBusinessMs', 'launchToFirstBusinessMs', 'firstOpenApiJsonMs']:
            values = [r[key] for r in rows if key in r]
            item[key] = stats(values) if len(values) == len(rows) else None
        item['warm'] = {key: statistics.median(r['warm'][key] for r in rows)
                        for key in ['p50Ms', 'p95Ms', 'p99Ms']}
        memory = [[int(line) / MIB for line in r.get('containerStats', '').splitlines() if line.isdigit()]
                  for r in rows]
        if env['arguments']['docker'] and any(len(m) != 2 for m in memory):
            raise ValueError('Missing peak/current cgroup memory')
        item['peakMiB'] = stats([m[0] for m in memory]) if all(memory) else None
        item['endMiB'] = stats([m[1] for m in memory]) if all(memory) else None
        details = env.get('nativeRuntimeDetailsByVariant', {}).get(name)
        if details is None and rows[0]['runtime'] == 'native':
            details = env.get('nativeRuntimeDetails', '')
        match = re.search(r'(?m)^(\d+) /app/application\s*$', details or '')
        item['executableMiB'] = int(match[1]) / MIB if match else None
        result['variants'][name] = item
    return result


def collect_phases():
    result = {}
    for label, batch, variant in PHASES:
        summary = read(f'results/{batch}/summary.json')
        if not summary.get('instrumented') or summary['eligibleComparison'] or not summary['allDiagnosticsPassed']:
            raise ValueError('Expected validated diagnostic capture')
        rows = [r for r in summary['runs'] if r['variant'] == variant]
        startup, workload = collections.defaultdict(list), collections.defaultdict(list)
        for row in rows:
            phase = row['phaseEvidence']
            if not phase['verified'] or not all(c['passed'] for c in row['checks'].values()):
                raise ValueError('Failed phase capture')
            for target, events in [(startup, (phase['startup'] or {}).get('events', [])),
                                   (workload, [e for op in phase['workload'] for e in op['events']])]:
                totals = collections.Counter()
                for event in events:
                    totals[event['phase']] += event['durationNs'] / 1e6
                for key, value in totals.items():
                    target[key].append(value)
        result[label] = dict(batch=batch, variant=variant, starts=len(rows),
                             image=rows[0]['container']['image'],
                             startup={k: statistics.median(v) for k, v in startup.items()},
                             workload={k: statistics.median(v) for k, v in workload.items()})
        if all(row.get('memoryDiagnostics') for row in rows):
            snapshots = [dict((key, int(value)/1024) for key,value in re.findall(
                r'^(Rss|Pss|Pss_Anon|Pss_File):\s+(\d+) kB', row['memoryDiagnostics']['processSmaps'], re.M))
                for row in rows]
            result[label]['processMemoryMiB'] = {key:statistics.median(s[key] for s in snapshots)
                                                 for key in ['Rss','Pss','Pss_Anon','Pss_File']}
    return result


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |',
                      '| ' + ' | '.join(['---'] + ['---:'] * (len(headers) - 1)) + ' |'] +
                     ['| ' + ' | '.join(str(v) for v in row) + ' |' for row in rows])


def number(value, decimals=2):
    return '—' if value is None else f'{value:,.{decimals}f}'


def median(item, key, scale=1, decimals=2):
    return number(item[key]['median'] / scale, decimals) if item[key] else '—'


def timing_tables(group):
    items = group['variants'].values()
    timing = table(['Variant', 'Starts', 'Ready (s)', 'First request (ms)', 'Full business (s)',
                    'Full business min–max (s)', 'First OpenAPI (ms)'],
                   [[i['label'], i['starts'], median(i, 'launchToReadyMs', 1000, 3),
                     median(i, 'firstBusinessMs'), median(i, 'launchToFirstBusinessMs', 1000, 3),
                     number(i['launchToFirstBusinessMs']['minimum'] / 1000, 3) + '–' +
                     number(i['launchToFirstBusinessMs']['maximum'] / 1000, 3),
                     median(i, 'firstOpenApiJsonMs')] for i in items])
    warm = table(['Variant', 'Warm p50 (ms)', 'Warm p95 (ms)', 'Warm p99 (ms)',
                  'Peak memory median (MiB)', 'Peak memory min–max (MiB)', 'End memory median (MiB)'],
                 [[i['label'], *[number(i['warm'][key]) for key in ['p50Ms', 'p95Ms', 'p99Ms']],
                   median(i, 'peakMiB'), (number(i['peakMiB']['minimum']) + '–' + number(i['peakMiB']['maximum']))
                   if i['peakMiB'] else '—', median(i, 'endMiB')] for i in items])
    links = ', '.join(f'`{batch}`' for batch in group['batches'])
    selected = list(items)
    counts = (f"Displayed rows: **{sum(i['starts'] for i in selected)} starts / "
              f"{sum(i['capabilityChecks'] for i in selected)} passing checks / "
              f"{sum(i['measuredRequests'] for i in selected)} successful measured requests**. "
              f"Each start: {group['warmupsPerStart']} warmups, {group['requestsPerStart']} measured requests. "
              f'Batch IDs in [latest measurements](results/latest/measurements.json): {links}.')
    return counts + '\n\n' + timing + '\n\n' + warm


def overview(groups, prefix=''):
    def cell(group, name):
        value = median(groups[group]['variants'][name], 'launchToFirstBusinessMs', 1000, 3)
        return f'[{value}]({prefix}RESULTS.md#{group})'
    return table(['Application', 'Full JDK default (s)', 'Full JDK C1 (s)',
                  'Application jlink default (s)', 'Application jlink C1 (s)', 'Native (s)'], [
        ['GuicedEE SPI', cell('jvm-default', 'guicedee'), cell('jvm-c1', 'guicedee'),
         cell('jvm-default', 'guicedee-jlink'), cell('jvm-c1', 'guicedee-jlink'), cell('native-standard', 'guicedee-native')],
        ['GuicedEE scanner', cell('jvm-default', 'guicedee-scan'), cell('jvm-c1', 'guicedee-scan'),
         cell('jvm-default', 'guicedee-scan-jlink'), cell('jvm-c1', 'guicedee-scan-jlink'), 'SPI only'],
        ['Quarkus / upstream SDKs', cell('jvm-default', 'quarkus-standard'), cell('jvm-c1', 'quarkus-standard'),
         'Not implemented', 'Not implemented', cell('native-standard', 'quarkus-standard-native')],
    ])



def render(data):
    groups = data['groups']
    sections = {name: timing_tables(group) for name, group in groups.items()}
    sections['overview'] = overview(groups)
    native = groups['native-standard']['variants']
    a, b = native['guicedee-native'], native['quarkus-standard-native']
    delta = []
    for label, av, bv, unit in [
        ('Full-business startup', a['launchToFirstBusinessMs']['median'], b['launchToFirstBusinessMs']['median'], 'ms'),
        ('First business request', a['firstBusinessMs']['median'], b['firstBusinessMs']['median'], 'ms'),
        ('Warm p50', a['warm']['p50Ms'], b['warm']['p50Ms'], 'ms'),
        ('Warm p95', a['warm']['p95Ms'], b['warm']['p95Ms'], 'ms'),
        ('Warm p99', a['warm']['p99Ms'], b['warm']['p99Ms'], 'ms'),
        ('Peak container memory', a['peakMiB']['median'], b['peakMiB']['median'], 'MiB'),
        ('Executable size', a['executableMiB'], b['executableMiB'], 'MiB'),
        ('Docker local image size', a['imageMiB'], b['imageMiB'], 'MiB'),
    ]:
        delta.append([label, f'{av:.2f} {unit}', f'{bv:.2f} {unit}', f'{(av / bv - 1) * 100:+.1f}%'])
    sections['native-deltas'] = table(['Metric', 'GuicedEE native', 'Quarkus upstream native', 'GuicedEE difference'], delta)
    if 'native-extended' in groups:
        extended = groups['native-extended']['variants']
        eg, eq = extended['guicedee-native'], extended['quarkus-standard-native']
        sections['extended-findings'] = (
            f"In this separate {eg['starts']}-start-per-framework cohort, median peak charged memory is "
            f"**{eg['peakMiB']['median']:.2f} / {eq['peakMiB']['median']:.2f} MiB** (GuicedEE / Quarkus), "
            f"a GuicedEE difference of **{(eg['peakMiB']['median']/eq['peakMiB']['median']-1)*100:+.1f}%**. "
            f"Its full-business startup medians are **{eg['launchToFirstBusinessMs']['median']:.0f} / "
            f"{eq['launchToFirstBusinessMs']['median']:.0f} ms**. Keep this smaller startup sample separate "
            'from the primary counterbalanced comparison; longer request sequences also change allocation and GC behavior.')
    if data.get('nativeAudit'):
        audit = data['nativeAudit']
        before = audit['comparison']['variants']['guicedee-native-before']
        after = audit['comparison']['variants']['guicedee-native-after']
        old, new = (audit['compilerStatistics'][key] for key in ['before', 'after'])
        rows = []
        for label, av, bv, unit in [
            ('Executable', before['executableMiB'], after['executableMiB'], 'MiB'),
            ('Reachable methods', old['analysis_results']['methods']['reachable'], new['analysis_results']['methods']['reachable'], 'count'),
            ('Compiled code area', old['image_details']['code_area']['bytes']/MIB, new['image_details']['code_area']['bytes']/MIB, 'MiB'),
            ('Image heap', old['image_details']['image_heap']['bytes']/MIB, new['image_details']['image_heap']['bytes']/MIB, 'MiB'),
            ('Artifact compiler peak RSS', old['resource_usage']['memory']['peak_rss_bytes']/MIB, new['resource_usage']['memory']['peak_rss_bytes']/MIB, 'MiB'),
            ('Full-business startup', before['launchToFirstBusinessMs']['median'], after['launchToFirstBusinessMs']['median'], 'ms'),
            ('Peak charged memory', before['peakMiB']['median'], after['peakMiB']['median'], 'MiB')]:
            values = [f'{v:,.0f}' if unit=='count' else f'{v:.2f} {unit}' for v in [av,bv]]
            rows.append([label,*values,f'{(bv/av-1)*100:+.1f}%'])
        sections['native-audit'] = table(['Metric','Previous GuicedEE artifact','Current GuicedEE artifact','Difference'],rows)
        sections['native-audit'] += (
            f"\n\nRuntime rows use {before['starts']} alternating starts per artifact, with the same CPU, memory, "
            'heap and request settings. Compiler counts and peak RSS describe the single builds that produced the two artifacts; clean-build time is measured '
            'separately in the build grid. '
            f"The full-provider override also passed **{audit['providerOverride']['batchCapabilityChecks']} capability checks** "
            f"across {audit['providerOverride']['batchStarts']} starts. This validates the existing workload with the override, "
            'not connectivity to a real xDS control plane. [Raw audit evidence](results/latest/native-audit.json).')
    memory = []
    for label in ['GuicedEE native', 'Quarkus upstream native']:
        phase = data['phases'][label]
        if phase.get('processMemoryMiB'):
            memory.append([label,phase['starts'],*[f"{phase['processMemoryMiB'][key]:.2f}"
                                                   for key in ['Rss','Pss','Pss_Anon','Pss_File']]])
    if memory:
        sections['native-memory'] = table(['Instrumented native process','Starts','End RSS (MiB)',
            'End PSS (MiB)','Anonymous PSS (MiB)','File-backed PSS (MiB)'],memory)
    startup_change = (a['launchToFirstBusinessMs']['median'] / b['launchToFirstBusinessMs']['median'] - 1) * 100
    sections['headline'] = (
        f"GuicedEE native completes the first full business request in **{a['launchToFirstBusinessMs']['median']:.0f} ms**, "
        f"versus **{b['launchToFirstBusinessMs']['median']:.0f} ms** for Quarkus native "
        f"(**{abs(startup_change):.1f}% {'less' if startup_change < 0 else 'more'} time**). "
        f"Warm p50 is **{a['warm']['p50Ms']:.2f} / {b['warm']['p50Ms']:.2f} ms** (GuicedEE / Quarkus). "
        f"Peak charged memory is **{a['peakMiB']['median']:.2f} / {b['peakMiB']['median']:.2f} MiB**; "
        f"executables are **{a['executableMiB']:.2f} / {b['executableMiB']:.2f} MiB**. "
        f"The native sample contains **{a['starts'] + b['starts']} starts and "
        f"{a['capabilityChecks'] + b['capabilityChecks']} passing capability checks**.")
    native_startup_winner = 'GuicedEE' if a['launchToFirstBusinessMs']['median'] < b['launchToFirstBusinessMs']['median'] else 'Quarkus'
    native_latency_winner = 'GuicedEE' if a['warm']['p50Ms'] < b['warm']['p50Ms'] else 'Quarkus'
    native_memory_winner = 'GuicedEE' if a['peakMiB']['median'] < b['peakMiB']['median'] else 'Quarkus'
    sections['runtime-findings'] = (
        f"{native_startup_winner} native records the lower median full-business startup; "
        f"{native_latency_winner} native records the lower warm p50. {native_memory_winner} native has the lower "
        'peak container memory. The JVM grids separately report HTTP readiness and completion of the cold '
        'SDK/Firestore business request, so both startup costs remain visible.')
    relative = []
    for group in ['jvm-default', 'jvm-c1']:
        values = groups[group]['variants']
        for name, item in values.items():
            if not name.startswith('guicedee'):
                continue
            baseline = values['quarkus-standard-native' if name == 'guicedee-native' else 'quarkus-standard']
            pairs = [(item['launchToReadyMs']['median'], baseline['launchToReadyMs']['median']),
                     (item['launchToFirstBusinessMs']['median'], baseline['launchToFirstBusinessMs']['median']),
                     (item['warm']['p50Ms'], baseline['warm']['p50Ms']),
                     (item['warm']['p95Ms'], baseline['warm']['p95Ms']),
                     (item['peakMiB']['median'], baseline['peakMiB']['median'])]
            relative.append([group, item['label'], 'Native' if name == 'guicedee-native' else 'JVM',
                             *[f'{(a / b - 1) * 100:+.1f}%' for a, b in pairs]])
    sections['relative'] = table(['Profile', 'GuicedEE mode', 'Quarkus baseline', 'Ready', 'Full business',
                                  'Warm p50', 'Warm p95', 'Peak memory'], relative)
    findings = []
    for group, label in [('jvm-default', 'Default JVM'), ('jvm-c1', 'C1 JVM')]:
        values = groups[group]['variants']
        reference = values['quarkus-standard']['launchToFirstBusinessMs']['median']
        spi = values['guicedee-jlink']['launchToFirstBusinessMs']['median']
        scan = values['guicedee-scan-jlink']['launchToFirstBusinessMs']['median']
        percent = (spi / reference - 1) * 100
        findings.append(f"**{label}:** linked SPI/scanner complete the first business response in "
                        f"**{spi / 1000:.3f}/{scan / 1000:.3f} s**, versus **{reference / 1000:.3f} s** "
                        f"for Quarkus JVM. SPI jlink uses **{abs(percent):.1f}% {'less' if percent < 0 else 'more'} "
                        'time**. The separate readiness and first-request columns show where that difference occurs.')
    sections['findings'] = '\n\n'.join(findings)
    packaging = []
    packaged_images = set()
    for name in ['native-standard', 'jvm-default']:
        for item in groups[name]['variants'].values():
            if item['image'] in packaged_images:
                continue
            packaged_images.add(item['image'])
            packaging.append([item['label'], name, number(item['imageMiB']), number(item['executableMiB']),
                              '`' + item['image'].removeprefix('sha256:')[:12] + '`'])
    sections['packaging'] = table(['Variant', 'Evidence group', 'Docker local image (MiB)', 'Executable (MiB)', 'Image ID prefix'], packaging)
    audit = read('results/jlink-audit-verification.json')
    sections['jlink-size'] = table(['Measured jlink payload', 'SPI', 'Scanner'],
        [[label, *[number(audit['images'][key][field] / MIB) for key in ['spi', 'scan']]] for label, field in [
            ('Runtime including application (MiB)', 'runtimeTreeBytes'), ('Module image (MiB)', 'moduleImageBytes'),
            ('Unpacked Docker layers (MiB)', 'unpackedLayerBytes')]] +
        [[label, *[audit['images'][key][field] for key in ['spi', 'scan']]] for label, field in [
            ('Installed modules', 'moduleCount'), ('Mandatory module closure', 'requiredClosureCount'),
            ('Closure including installed service providers', 'serviceBoundClosureCount')]])
    phases = data['phases']
    sections['phase-sources'] = table(['Diagnostic variant', 'Starts', 'Evidence', 'Image ID prefix'],
        [[label, item['starts'], f"`{item['batch']}`",
          '`' + item['image'].removeprefix('sha256:')[:12] + '`'] for label, item in phases.items()])
    for kind, names, keys in [
        ('startup', ['SPI jlink', 'Scanner jlink', 'GuicedEE native'], [
            ('Context discovery', 'context-discovery'), ('Discovery', 'discovery'), ('ClassGraph scan', 'classgraph-scan'),
            ('Pre-startup hooks', 'pre-startup'), ('Guice module discovery', 'guice-module-discovery'),
            ('Guice injector creation', 'guice-create-injector'),
            ('OpenAPI provider (within injector)', 'provision:com.guicedee.guicedservlets.openapi.implementations.OpenAPIProvider'),
            ('Post-startup hooks', 'post-startup')]),
        ('workload', list(phases), [
            ('JDK HTTP client construction', 'jdk-http-client-initialization'),
            ('Commercetools client initialization', 'vendor-client-initialization'),
            ('Commercetools REST + first OAuth', 'vendor-rest-including-oauth'), ('GraphQL completion', 'vendor-graphql'),
            ('Firestore client initialization', 'firestore-client-initialization'),
            ('Firestore write completion', 'firestore-write-await'), ('Firestore read completion', 'firestore-read-await')]),
    ]:
        sections['phase-' + kind] = table(['Inclusive phase (ms)'] + names,
            [[label] + [number(phases[name][kind].get(key)) for name in names] for label, key in keys])
    sections['image-identities'] = table(['Group', 'Variant', 'Immutable Docker image ID'],
        [[group, item['label'], '`' + item['image'] + '`'] for group, values in groups.items()
         if group != 'local-windows' for item in values['variants'].values()])
    return sections


def replace_sections(path, sections):
    content = path.read_text(encoding='utf-8')
    for name, replacement in sections.items():
        pattern = rf'(<!-- BEGIN GENERATED: {name} -->\n).*?(<!-- END GENERATED: {name} -->)'
        content, count = re.subn(pattern, lambda m: m[1] + replacement + '\n' + m[2], content, flags=re.S)
        if count != 1:
            raise ValueError(f'Expected one report section {name}: {path}')
    return content


def main():
    global EVIDENCE_ROOT, LATEST, GROUPS, PHASES
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--evidence-root', type=Path, default=ROOT,
                        help='Benchmark checkout containing the retained results (defaults to this checkout)')
    args = parser.parse_args()
    EVIDENCE_ROOT = args.evidence_root.resolve()
    evidence = EVIDENCE_ROOT / 'results/latest/measurements.json'
    LATEST = json.loads(evidence.read_text(encoding='utf-8'))
    GROUPS = {name: (value['batches'], value['variants']) for name, value in LATEST['groups'].items()}
    PHASES = [(v['label'], v['batch'], v['variant']) for v in LATEST['phases']]
    data = {'measuredOn': LATEST['measuredOn'], 'reportAsOf': LATEST['reportAsOf'],
            'aggregation': 'All starts retained; warm percentiles are medians of per-start percentiles.',
            'groups': {name: collect_group(*config) for name, config in GROUPS.items()}, 'phases': collect_phases()}
    audit_path = EVIDENCE_ROOT/'results/latest/native-audit.json'
    if audit_path.exists():
        data['nativeAudit'] = collect_native_audit(audit_path, data['groups']['native-standard']['variants']['guicedee-native']['image'])
    if LATEST.get('hostObservations'):
        host = LATEST['hostObservations']
        before = [row for row in host['observations'] if row['stage'].endswith('-before')]
        data['hostCondition'] = dict(bootTimeUtc=host['bootTimeUtc'], samples=len(before),
            cpuPercent=stats([row['cpuPercent'] for row in before]),
            availableMemoryMiB=stats([row['availableMemoryMiB'] for row in before]),
            stages=sorted({row['stage'] for row in before}),
            recoveredBoundaryCpuPercent=host.get('recoveredBoundaryCpuPercent', {}),
            coverage=host['coverage'])
    data['inputSha256'] = {'results/latest/measurements.json': hashlib.sha256(evidence.read_bytes()).hexdigest()}
    if audit_path.exists():
        data['inputSha256']['results/latest/native-audit.json'] = hashlib.sha256(audit_path.read_bytes()).hexdigest()
    output = io.StringIO(newline='')
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(['group', 'variant', 'starts', 'ready_ms', 'first_request_ms', 'full_business_ms',
                     'full_business_min_ms', 'full_business_max_ms', 'openapi_ms', 'warm_p50_ms',
                     'warm_p95_ms', 'warm_p99_ms', 'peak_memory_mib', 'end_memory_mib', 'image_mib', 'executable_mib', 'image_id'])
    for group, values in data['groups'].items():
        for name, item in values['variants'].items():
            writer.writerow([group, name, item['starts'],
                *[item[k]['median'] if item[k] else '' for k in ['launchToReadyMs', 'firstBusinessMs', 'launchToFirstBusinessMs']],
                item['launchToFirstBusinessMs']['minimum'], item['launchToFirstBusinessMs']['maximum'],
                item['firstOpenApiJsonMs']['median'] if item['firstOpenApiJsonMs'] else '',
                *[item['warm'][k] for k in ['p50Ms', 'p95Ms', 'p99Ms']],
                *[item[k]['median'] if item[k] else '' for k in ['peakMiB', 'endMiB']],
                item['imageMiB'], item['executableMiB'], item['image']])
    sections = render(data)
    if data.get('hostCondition'):
        host = data['hostCondition']
        cpu, memory = host['cpuPercent'], host['availableMemoryMiB']
        boundaries = host['recoveredBoundaryCpuPercent']
        preparation = boundaries.get('builds-before', [])
        runtime = boundaries.get('default-before', [])
        preparation_note = (
            f"The recovered build-stage CPU snapshots were **{min(preparation):.1f}–{max(preparation):.1f}%** "
            'before untimed dependency preparation; '
            f"the default-runtime stage began at **{min(runtime):.1f}–{max(runtime):.1f}%**. "
            if preparation and runtime else '')
        sections['host-condition'] = (
            f"All timing profiles were rerun after the host boot at **{host['bootTimeUtc']}**. "
            f"Across {host['samples']} retained one-second preflight samples, host CPU utilization "
            f"ranged **{cpu['minimum']:.1f}–{cpu['maximum']:.1f}%**, available physical memory "
            f"**{memory['minimum']/1024:.1f}–{memory['maximum']/1024:.1f} GiB**. "
            + preparation_note + 'Build, runtime and diagnostic stages ran sequentially. '
            'Host observations have partial coverage and are boundary snapshots, not continuous '
            'measurements of background load during each run. Available observations and their '
            'coverage are included in the latest measurement dataset.')
    build_evidence = EVIDENCE_ROOT/'results/latest/builds.json'
    data['builds'] = collect_builds(build_evidence)
    verify_build_runtime_sources(data, LATEST['imageInputs'])
    data['inputSha256']['results/latest/builds.json'] = hashlib.sha256(build_evidence.read_bytes()).hexdigest()
    sections.update(build_sections(data))
    build_csv = io.StringIO(newline='')
    build_writer = csv.writer(build_csv, lineterminator='\n')
    build_writer.writerow(['variant', 'goal', 'samples', 'median_seconds', 'minimum_seconds', 'maximum_seconds',
                           'baseline', 'difference_percent'])
    for name, values in data['builds']['variants'].items():
        for goal, item in values.items():
            build_writer.writerow([name, goal, item['samples'], item['median'], item['minimum'], item['maximum'],
                                   item.get('baseline', ''), item.get('differencePercent', '')])
    outputs = {
        ROOT / 'RESULTS.md': replace_sections(ROOT / 'RESULTS.md', sections),
        ROOT / 'README.md': replace_sections(ROOT / 'README.md', dict(
            overview=overview(data['groups']), **{key: sections[key] for key in
            ['headline', 'build-headline', 'build-grid', 'sdk-headline']})),
        ROOT / 'docs/current-performance.json': json.dumps(data, indent=2) + '\n',
        ROOT / 'docs/current-performance.csv': output.getvalue(),
        ROOT / 'docs/build-performance.csv': build_csv.getvalue(),
    }
    for path, content in outputs.items():
        if args.check:
            if not path.exists() or path.read_text(encoding='utf-8') != content:
                raise ValueError(f'Stale generated report: {path.relative_to(ROOT)}')
        else:
            path.write_text(content, encoding='utf-8', newline='\n')
    if args.check:
        digest = hashlib.sha256((ROOT/'docs/current-performance.json').read_bytes()).hexdigest()
        for name in ['startup', 'builds']:
            chart = ROOT/f'docs/{name}.svg'
            if not chart.exists() or f'performance-data-sha256: {digest}' not in chart.read_text(encoding='utf-8'):
                raise ValueError(f'Stale {name} chart; run tools/render_charts.py')
    print(f"{'Verified' if args.check else 'Rendered'} {len(data['groups'])} performance groups, "
          f"{sum(len(g['variants']) for g in data['groups'].values())} metric rows and {len(data['phases'])} diagnostic variants")


if __name__ == '__main__':
    main()
