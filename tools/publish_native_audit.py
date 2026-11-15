"""Retain a complete paired native audit and the full-provider override validation."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from publish_results import compact
from summarize_native import sdk_evidence
import render_performance

ROOT = Path(__file__).resolve().parents[1]


def read_batch(directory):
    summary = json.loads((directory/'summary.json').read_text())
    environment = json.loads((directory/'environment.json').read_text())
    retained = compact(summary, environment)
    previous = render_performance.LATEST
    try:
        render_performance.LATEST = {'batches': {directory.name: retained}}
        render_performance.collect_group([directory.name], None)
    finally:
        render_performance.LATEST = previous
    evidence = sdk_evidence(summary['variants'], environment['imageBuildProvenance'])
    if not evidence['sdkHashesMatch'] or any(v['runtime'] != 'native' for v in summary['variants']):
        raise ValueError('The paired audit requires identical SDKs and native runtimes')
    roles = {v['comparisonRole']: v['id'] for v in summary['variants']}
    if set(roles) != {'before', 'after'} or len(summary['variants']) != 2:
        raise ValueError('Expected one complete baseline/candidate pair')
    return dict(batch=directory.name, **retained, sdkEvidence=evidence,
                inputSha256={name:hashlib.sha256((directory/name).read_bytes()).hexdigest()
                             for name in ['summary.json', 'environment.json']}), environment, roles


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('comparison', type=Path)
    parser.add_argument('provider_override', type=Path)
    parser.add_argument('--artifact-build-log', type=Path, required=True,
                        help='Native compiler output from the current immutable artifact build')
    args = parser.parse_args()
    comparison, environment, roles = read_batch(args.comparison)
    override, override_environment, override_roles = read_batch(args.provider_override)
    current = environment['images'][roles['after']]
    if override_environment['images'][override_roles['before']] != current:
        raise ValueError('Provider override must be compared against the audited candidate image')
    statistics = {role:json.loads(subprocess.check_output(
        ['docker','run','--rm','--entrypoint','cat',environment['images'][name],
         '/app/native-build-statistics.json'], text=True)) for role,name in roles.items()}
    build_log = args.artifact_build_log.read_text(encoding='utf-8')
    analysis = statistics['after']['analysis_results']
    if (f"{analysis['types']['reachable']:,} types" not in build_log
            or f"{analysis['methods']['reachable']:,} methods found reachable" not in build_log):
        raise ValueError('Artifact build log does not match the current compiler analysis')
    lines = [line.split('[INFO] [stdout] ',1)[-1] for line in build_log.splitlines()]
    start = next(i for i,line in enumerate(lines) if 'Top 10 origins of code area:' in line)
    end = next(i for i in range(start+1,len(lines)) if lines[i].startswith('---'))
    build_output = dict(logSha256=hashlib.sha256(args.artifact_build_log.read_bytes()).hexdigest(),
                        originsAndHeapTypes=lines[start:end])
    sources = environment['imageBuildProvenance'][roles['after']]['sourcesAtImageBuild']
    policy = next(s for s in sources if s['path'] == 'guicedee-native/native-excluded-providers.txt')
    providers = [line.split('#',1)[0].strip() for line in policy['content'].splitlines()]
    providers = [name for name in providers if name]
    result = dict(schemaVersion=1, comparison=comparison, providerOverride=override,
                  compilerStatistics=statistics, artifactBuildOutput=build_output,
                  currentImage=current, excludedProviders=providers,
                  sourceSha256={s['path']:s['sha256'] for s in sources
                                if s['path'].startswith('guicedee-native/')},
                  scope='Application native policy; original SDK JARs and module descriptors retained. '
                        'The override validation exercises the existing workload, not an xDS control plane.',
                  allocatorDefaults=dict(type='pooled', maxOrder=3, defaultPageBytes=8192,
                      propertyPrefixes=['io.netty','com.commercetools.internal.shaded.io.netty',
                          'com.google.firebase.internal.shaded.io.netty',
                          'com.google.firebase.internal.shaded.io.grpc.netty.shaded.io.netty']))
    (ROOT/'results/latest/native-audit.json').write_text(json.dumps(result,separators=(',',':'))+'\n',
                                                       encoding='utf-8',newline='\n')
    subprocess.run([sys.executable,ROOT/'tools/verify_latest.py','--refresh'],check=True)


if __name__ == '__main__':
    main()
