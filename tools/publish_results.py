"""Replace one current performance group with complete fresh benchmark batches.

Example: python tools/publish_results.py jvm-default target/runs/<batch>
Raw run logs/source snapshots stay under target; only measurements needed by the
published report are retained. Existing current groups remain until replaced.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
LATEST = ROOT/'results/latest/measurements.json'
ROW_KEYS = {'framework','variant','discovery','runtime','run','checks','samples','runtimeFlags',
            'jvmFlags','jvmFlagsSource','launch','dependencyMode','launchToReadyMs','firstBusinessStatus',
            'firstBusinessMs','launchToFirstBusinessMs','firstOpenApiJsonMs','warm','eligible',
            'container','containerStats','discoveryEvidence','instrumented','phaseEvidence'}


def compact(summary, environment, selected=None):
    summary = copy.deepcopy(summary)
    if selected:
        summary['variants'] = [v for v in summary['variants'] if v['id'] in selected]
        summary['runs'] = [r for r in summary['runs'] if r['variant'] in selected]
    names = {v['id'] for v in summary['variants']}
    if selected and names != set(selected):
        raise ValueError('Selected variants are missing')
    result = {k: summary[k] for k in ['eligibleComparison','variants','scope']}
    result['runs'] = [{k: v for k, v in r.items() if k in ROW_KEYS} for r in summary['runs']]
    for row in result['runs']:
        row.get('discoveryEvidence', {}).pop('logLines', None)
        if row.get('container'):
            row['container']['state'] = {k: v for k, v in row['container']['state'].items()
                                         if k in ['OOMKilled','ExitCode','Error']}
        elif row.get('launch'):
            # Local paths are not public build instructions; flags and hashes remain.
            row['launch'] = ['<linked-runtime>/bin/benchmark'] if row['runtime'] == 'jlink' else [
                '<JAVA_HOME>/bin/java', *row.get('jvmFlags', []), '--module-path',
                '<application.jar>:<resolved-dependencies>', '-m',
                'bench.guicedee.scan/bench.guicedee.Main' if row.get('discovery') == 'scan' else 'bench.guicedee/bench.guicedee.Main']
    env = {k: environment[k] for k in ['platform','java','flags','cpuQuota','profile','executionModel'] if k in environment}
    env['arguments'] = {k: environment['arguments'][k] for k in ['runs','requests','warmup','docker','tiered']}
    for key in ['images','imageSizeBytes','nativeRuntimeDetailsByVariant']:
        if key in environment:
            env[key] = {k: v for k, v in environment[key].items() if k in names}
    if 'nativeRuntimeDetails' in environment:
        env['nativeRuntimeDetails'] = environment['nativeRuntimeDetails']
    return {'summary': result, 'environment': env}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('group')
    parser.add_argument('directories', nargs='+', type=Path)
    parser.add_argument('--variants', nargs='+', help='Keep all starts of these variants; no per-start filtering')
    args = parser.parse_args()
    data = json.loads(LATEST.read_text(encoding='utf-8'))
    batches = []
    for directory in args.directories:
        summary = json.loads((directory/'summary.json').read_text())
        environment = json.loads((directory/'environment.json').read_text())
        if not summary['eligibleComparison'] or summary.get('instrumented'):
            raise ValueError('Only passing, uninstrumented complete comparisons can be published')
        batch = directory.name
        batches.append(batch)
        # A batch can back more than one current group. Keep it complete and select
        # whole variants in the group definition; never overwrite it with a subset.
        data['batches'][batch] = compact(summary, environment)
        for filename in ['summary.json','environment.json']:
            data['inputSha256'][f'{batch}/{filename}'] = hashlib.sha256((directory/filename).read_bytes()).hexdigest()
        for name, provenance in environment.get('imageBuildProvenance', {}).items():
            image = environment['images'][name]
            data.setdefault('imageInputs', {})[image] = {
                'sharedSourceHashes': [{'path': s['path'], 'sha256': s['sha256']}
                    for s in provenance.get('sourcesAtImageBuild', [])
                    if s['path'].startswith('common/src/main/java/bench/')],
                'sdkJarHashes': {entry['path']: entry['sha256']
                    for key in ['sdkJars','packagedJars','resolvedDependencies']
                    for entry in provenance.get(key, []) if 'sha256' in entry
                    and ('firebase-admin' in entry.get('path','') or 'commercetools' in entry.get('path',''))}}
    data['groups'][args.group] = {'batches': batches, 'variants': args.variants}
    used = {batch for group in data['groups'].values() for batch in group['batches']}
    used.update(phase['batch'] for phase in data.get('phases', []))
    data['batches'] = {k: v for k, v in data['batches'].items() if k in used}
    data['reportAsOf'] = date.today().isoformat()
    # Validate every complete selected group before replacing the public evidence.
    import render_performance
    render_performance.LATEST = data
    for group in data['groups'].values():
        render_performance.collect_group(group['batches'], group['variants'])
    LATEST.write_text(json.dumps(data, separators=(',',':'))+'\n', encoding='utf-8', newline='\n')
    subprocess.run([sys.executable, ROOT/'tools/verify_latest.py', '--refresh'], check=True)
    print('Updated latest evidence for', args.group, '; run tools/render_performance.py to update the report grids.')


if __name__ == '__main__':
    main()
