"""Measure clean compilation and complete packaging with warm dependency caches.

Each timed invocation starts a new, offline Maven process. Outputs are cleaned; dependency
downloads, preparation and Docker image assembly are outside the measurement. Native
compilation is included in native packaging. All samples, including failures, are retained.
"""
import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = ['guicedee', 'guicedee-scan', 'quarkus-standard', 'guicedee-jlink',
            'guicedee-scan-jlink', 'guicedee-native', 'quarkus-standard-native', 'micronaut', 'micronaut-native',
            'guicedee-cdi', 'guicedee-cdi-spi', 'guicedee-cdi-jlink',
            'guicedee-cdi-spi-jlink', 'guicedee-cdi-native']


def command(variant, goal, version, maven='mvn', offline=True):
    args = [maven, '-B', '-ntp', '-DskipTests']
    if offline:
        args += ['-o']
    if variant.startswith(('quarkus-standard','micronaut')):
        args += ['-f', ('micronaut' if variant.startswith('micronaut') else 'quarkus-standard')+'/pom.xml']
        if variant.endswith('-native'):
            args += ['-Pnative']
    else:
        args += [f'-Dguicedee.version={version}', '-pl', variant, '-am']
        profiles = ['cdi-config'] if variant.startswith('guicedee-cdi') else []
        if variant.endswith('-jlink'):
            profiles += ['cdi-jlink' if variant.startswith('guicedee-cdi') else 'jlink']
        elif variant.endswith('-native'):
            profiles += ['native', 'cdi-native' if variant.startswith('guicedee-cdi') else 'native-app']
        if profiles:
            args += ['-P' + ','.join(profiles)]
    args += ['clean', goal]
    if goal == 'package' and variant.startswith('guicedee') and not variant.endswith(('-native', '-jlink')):
        # Include the runtime dependencies, just as Quarkus fast-JAR does.
        args += ['dependency:copy-dependencies', '-DincludeScope=runtime', '-DoutputDirectory=target/lib']
    return args


def tasks(variants):
    return [(v, 'compile') for v in variants if not v.endswith(('-native','-jlink'))] + [(v, 'package') for v in variants]


def ordered(items, run):
    offset = (run - 1) % len(items)
    return items[offset:] + items[:offset]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_native_inputs(repository, version, variant='guicedee-native'):
    traced = json.loads((ROOT/variant/'native-trace-inputs.json').read_text())
    sdk = [repository/f'com/guicedee/modules/services/{name}/{version}/{name}-{version}.jar'
           for name in ['firebase-admin', 'commercetools']]
    if {p.name:digest(p) for p in sdk} != {e['name']:e['sha256'] for e in traced['sdkJars']}:
        raise ValueError('Native SDK inputs differ from the capability trace; rebuild and retrace before measuring')


def validate(data):
    if (data['runs'] < 1 or not data['variants'] or len(data['variants']) != len(set(data['variants']))
            or not set(data['variants']).issubset(VARIANTS)):
        raise ValueError('Expected positive repetitions and unique supported build variants')
    expected = {(v, g, r) for v, g in tasks(data['variants']) for r in range(1, data['runs'] + 1)}
    actual = [(r['variant'], r['goal'], r['run']) for r in data['samples']]
    if len(actual) != len(set(actual)) or set(actual) != expected:
        raise ValueError('Build measurement matrix is incomplete or duplicated')
    if any(r['exitCode'] or not r['buildSuccess'] or not math.isfinite(r['wallSeconds'])
           or r['wallSeconds'] <= 0 or '-o' not in r['command']
           or 'clean' not in r['command'] for r in data['samples']):
        raise ValueError('Failed build or non-offline/non-clean timed sample')
    for row in data['samples']:
        if row['variant'].endswith('-native') and not any('Finished generating' in line for line in row['evidence']):
            raise ValueError('Native package sample has no completed native compiler invocation')
        if row['goal'] == 'compile' and not any('Compiling ' in line for line in row['evidence']):
            raise ValueError('Compile sample did not compile sources')
    if len(data['preparation']) != len(data['variants']) or any(
            r['exitCode'] or not r['buildSuccess'] for r in data['preparation']):
        raise ValueError('Every variant requires successful untimed preparation')


def run_build(args, variant, goal, run, output, offline):
    invocation = command(variant, goal, args.guicedee_version, args.maven, offline)
    if args.maven_repository:
        invocation.insert(1, f'-Dmaven.repo.local={args.maven_repository}')
    log = output / f'{variant}-{goal}-{run}.log'
    print(f"{'Measure' if offline else 'Prepare'} {variant} {goal} {run}", flush=True)
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    before = time.perf_counter()
    with log.open('w', encoding='utf-8') as stream:
        process = subprocess.run(invocation, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
    elapsed = time.perf_counter() - before
    content = log.read_text(encoding='utf-8', errors='replace')
    lines = [line for line in content.splitlines() if any(marker in line for marker in
             ['Total time:', 'BUILD SUCCESS', 'BUILD FAILURE', 'Finished generating',
              'Quarkus augmentation completed', 'Compiling ', 'Nothing to compile'])]
    row = dict(variant=variant, goal=goal, run=run, startedAt=started, wallSeconds=elapsed,
               exitCode=process.returncode, buildSuccess='BUILD SUCCESS' in content,
               command=invocation, logSha256=digest(log), evidence=lines)
    peak = re.findall(r'Peak RSS: ([\d.]+)GB', content)
    if variant.endswith('-native') and len(peak) == 1:
        row['nativeCompilerPeakRssGB'] = float(peak[0])
    print(f"  {elapsed:.3f}s; exit={process.returncode}", flush=True)
    if process.returncode:
        print(content[-5000:], flush=True)
    return row


def inputs():
    files = [ROOT/'pom.xml', ROOT/'tools/compare_builds.py']
    for name in ['common', 'guicedee', 'guicedee-scan', 'guicedee-jlink', 'guicedee-scan-jlink',
                 'guicedee-native', 'quarkus', 'quarkus-native', 'quarkus-standard', 'micronaut',
                 'guicedee-cdi', 'guicedee-cdi-spi', 'guicedee-cdi-jlink',
                 'guicedee-cdi-spi-jlink', 'guicedee-cdi-native']:
        base = ROOT/name
        files.extend(p for p in base.rglob('*') if p.is_file() and 'target' not in p.relative_to(base).parts)
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(set(files))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--docker', action='store_true', help='Build and use the common Linux/Mandrel toolchain')
    parser.add_argument('--runs', type=int, default=3)
    parser.add_argument('--variants', nargs='+', choices=VARIANTS)
    parser.add_argument('--cdi-config', action='store_true', help='Include all five CDI/config artifact modes')
    parser.add_argument('--guicedee-version', default=ET.parse(ROOT/'pom.xml').findtext('{*}properties/{*}guicedee.version'))
    parser.add_argument('--maven', default=shutil.which('mvn') or 'mvn')
    parser.add_argument('--maven-repository', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.variants is None:
        args.variants = [v for v in VARIANTS if args.cdi_config or not v.startswith('guicedee-cdi')]
    if args.runs < 1 or len(set(args.variants)) != len(args.variants):
        parser.error('Specify positive runs and unique variants')
    output = (args.output or ROOT/'target/build-runs'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S')).resolve()
    output.mkdir(parents=True, exist_ok=True)
    result = output/'builds.json'
    if result.exists():
        parser.error('Output already contains measurements; use a new output directory')
    if args.docker:
        if args.maven_repository:
            parser.error('Docker uses docker/repository staged by tools/build.py; --maven-repository is for host runs')
        for variant in ['guicedee-native', 'guicedee-cdi-native']:
            if variant in args.variants:
                verify_native_inputs(ROOT/'docker/repository', args.guicedee_version, variant)
        tag = 'devsuite-bench-build-toolchain:local'
        subprocess.run(['docker', 'build', '--target', 'build-benchmark', '-t', tag,
                        '--build-arg', f'GUICEDEE_VERSION={args.guicedee_version}',
                        '-f', 'docker/Dockerfile', '.'], cwd=ROOT, check=True)
        image = subprocess.check_output(['docker', 'image', 'inspect', tag, '--format', '{{.Id}}'], text=True).strip()
        host = json.loads(subprocess.check_output(['docker', 'info', '--format', '{{json .}}'], text=True))
        (output/'container.json').write_text(json.dumps(dict(image=image, operatingSystem=host['OperatingSystem'],
            kernel=host['KernelVersion'], cpus=host['NCPU'], memoryBytes=host['MemTotal'],
            cpuLimit=None, memoryLimit=None), indent=2)+'\n')
        subprocess.run(['docker', 'run', '--rm', '--mount', f'type=bind,source={output},target=/results',
                        '--entrypoint', 'python3', image, '/src/tools/compare_builds.py', '--runs', str(args.runs),
                        '--variants', *args.variants, '--guicedee-version', args.guicedee_version,
                        '--output', '/results'], check=True)
        print(f'Build measurements: {result}')
        return
    if any(v.endswith('-native') for v in args.variants) and not shutil.which('native-image'):
        parser.error('Native variants need Mandrel/native-image; use --docker or select JVM/jlink variants')
    for variant in ['guicedee-native', 'guicedee-cdi-native']:
        if variant in args.variants:
            verify_native_inputs(args.maven_repository or Path.home()/'.m2/repository', args.guicedee_version, variant)
    data = dict(schemaVersion=1, measuredAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                runs=args.runs, variants=args.variants, guicedeeArtifactVersion=args.guicedee_version,
                protocol='Warm dependencies; new Maven process; clean outputs; timed invocations offline; tests skipped; sequential rotated order.',
                platform=platform.platform(), cpuCount=os.cpu_count(),
                environment={key:os.environ.get(key) for key in ['JAVA_TOOL_OPTIONS', 'JDK_JAVA_OPTIONS', 'MAVEN_OPTS']},
                maven=subprocess.check_output([args.maven, '-version'], text=True, stderr=subprocess.STDOUT),
                java=subprocess.check_output(['java', '-version'], text=True, stderr=subprocess.STDOUT),
                sourceFiles=inputs(), preparation=[], samples=[], eligible=False)
    if (output/'container.json').exists():
        data['container'] = json.loads((output/'container.json').read_text())
    def save():
        result.write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')
    save()
    for variant in args.variants:
        row = run_build(args, variant, 'package', 0, output, False)
        data['preparation'].append(row)
        save()
        if row['exitCode'] or not row['buildSuccess']:
            raise SystemExit('Preparation failed; see retained log')
    # Snapshot the resolved input JARs after preparation, before any measured build.
    repository = args.maven_repository or Path.home()/'.m2/repository'
    data['dependencyCacheJars'] = {p.relative_to(repository).as_posix(): digest(p) for p in sorted(repository.rglob('*.jar'))}
    schedule = tasks(args.variants)
    for run in range(1, args.runs + 1):
        for variant, goal in ordered(schedule, run):
            row = run_build(args, variant, goal, run, output, True)
            data['samples'].append(row)
            save()
            if row['exitCode'] or not row['buildSuccess']:
                raise SystemExit('Measured build failed; incomplete matrix retained, not eligible')
    validate(data)
    data['eligible'] = True
    save()
    print(f'Complete: {len(data["samples"])} successful clean builds; {result}', flush=True)


if __name__ == '__main__':
    main()
