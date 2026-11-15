"""Publish compiler inclusion data for the currently measured GuicedEE native image."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def verify_profile_settings(details):
    for key in ['NATIVE_FULL_REFLECTION', 'NATIVE_CLOUD_CONTROL_PLANE']:
        if f'{key}=false' not in details.splitlines():
            raise ValueError(f'Current inclusion profile requires {key}=false')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path, help='Current native runtime batch')
    parser.add_argument('--variant', default='guicedee-native')
    parser.add_argument('--artifact-build-log', type=Path, required=True,
                        help='Compiler output from the current immutable artifact build')
    args = parser.parse_args()
    environment = json.loads((args.directory/'environment.json').read_text())
    measurements = json.loads((ROOT/'results/latest/measurements.json').read_text())
    group = measurements['groups']['native-standard']
    if args.directory.name not in group['batches']:
        raise ValueError('Publish the current native runtime cohort before its compiler profile')
    current = environment['images'][args.variant]
    if any(measurements['batches'][batch]['environment']['images'][args.variant] != current
           for batch in group['batches']):
        raise ValueError('Compiler profile does not match the published native runtime images')
    verify_profile_settings(environment['nativeRuntimeDetailsByVariant'][args.variant])
    statistics = json.loads(subprocess.check_output(
        ['docker', 'run', '--rm', '--entrypoint', 'cat', current,
         '/app/native-build-statistics.json'], text=True))
    build_log = args.artifact_build_log.read_text(encoding='utf-8')
    parse_counts = re.findall(r'full reflection=false; unrooted static protobuf parse overloads=(\d+)', build_log)
    if len(parse_counts) != 1:
        raise ValueError('Expected one completed SDK metadata preparation in the artifact build')
    analysis = statistics['analysis_results']
    if (f"{analysis['types']['reachable']:,} types" not in build_log
            or f"{analysis['methods']['reachable']:,} methods found reachable" not in build_log):
        raise ValueError('Artifact build log does not match the current compiler analysis')
    lines = [line.split('[INFO] [stdout] ', 1)[-1] for line in build_log.splitlines()]
    start = next(i for i, line in enumerate(lines) if 'Top 10 origins of code area:' in line)
    end = next(i for i in range(start+1, len(lines)) if lines[i].startswith('---'))
    sources = environment['imageBuildProvenance'][args.variant]['sourcesAtImageBuild']
    policy = next(s for s in sources if s['path'] == 'guicedee-native/native-excluded-providers.txt')
    providers = [line.split('#', 1)[0].strip() for line in policy['content'].splitlines()]
    result = dict(schemaVersion=1, currentImage=current, compilerStatistics=statistics,
        artifactBuildOutput=dict(logSha256=hashlib.sha256(args.artifact_build_log.read_bytes()).hexdigest(),
                                 originsAndHeapTypes=lines[start:end]),
        excludedProviders=[name for name in providers if name],
        sourceSha256={s['path']:s['sha256'] for s in sources if s['path'].startswith('guicedee-native/')},
        scope='Compiler inclusion and application native policy for the current immutable executable. '
              'Runtime and clean-build samples are recorded separately.',
        sdkReflection=dict(conditionalModelQueries=True,
            staticProtobufParseRegistrationEntriesOmitted=int(parse_counts[0]),
            parseCountScope='Metadata occurrences across three schemas; not unique methods.'),
        nativeResourceTarget=dict(os='linux', architecture='x86-64',
            excludedForeignPlatforms=['Windows', 'macOS', 'Linux AArch64'],
            retainedLibraries=['Conscrypt Linux x86-64', 'gRPC TLS Linux x86-64', 'epoll x86-64']),
        allocatorDefaults=dict(type='pooled', maxOrder=3, defaultPageBytes=8192,
            propertyPrefixes=['io.netty', 'com.commercetools.internal.shaded.io.netty',
                'com.google.firebase.internal.shaded.io.netty',
                'com.google.firebase.internal.shaded.io.grpc.netty.shaded.io.netty']))
    (ROOT/'results/latest/native-profile.json').write_text(json.dumps(result, separators=(',', ':'))+'\n',
                                                         encoding='utf-8', newline='\n')
    subprocess.run([sys.executable, ROOT/'tools/verify_latest.py', '--refresh'], check=True)


if __name__ == '__main__':
    main()
