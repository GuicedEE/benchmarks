"""Build benchmark applications from this checkout and an explicit Maven repository.

No neighboring framework source tree is inspected or modified. PowerShell entry points
delegate here so Linux/macOS/Windows use the same build flow.
"""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from variants import select_variants

ROOT = Path(__file__).resolve().parents[1]


def framework_version():
    pom = ET.parse(ROOT / 'pom.xml')
    return pom.findtext('{*}properties/{*}guicedee.version')


def run(command):
    print('+', subprocess.list2cmdline([str(v) for v in command]), flush=True)
    subprocess.run([str(v) for v in command], cwd=ROOT, check=True)


def verify_framework(repository, version, native=False):
    """Reject an incompatible published/local artifact before a long build starts."""
    client = repository / f'com/guicedee/client/{version}/client-{version}.jar'
    if not client.is_file():
        raise ValueError(f'Missing {client}. Resolve the GuicedEE version under test into the selected '
                         'Maven repository first. See RUNNING.md#guicedee-artifacts.')
    with zipfile.ZipFile(client) as jar:
        if 'com/guicedee/client/services/IGuiceDiscovery.class' not in jar.namelist():
            raise ValueError(f'GuicedEE {version} in {repository} lacks IGuiceDiscovery. '
                             'Select compatible framework artifacts with --guicedee-version.')
    if native and not (repository / f'com/guicedee/native-image/{version}/native-image-{version}.jar').is_file():
        raise ValueError(f'Native mode requires com.guicedee:native-image:{version} in {repository}. '
                         'See RUNNING.md#guicedee-artifacts.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--framework', choices=['guicedee', 'quarkus', 'both'], default='both')
    parser.add_argument('--runtime', choices=['jre', 'jlink', 'both', 'native'], default='jre')
    parser.add_argument('--native', action='store_true', help='Also build native executables')
    parser.add_argument('--docker', action='store_true', help='Build Linux container images')
    parser.add_argument('--quarkus-dependencies', choices=['standard', 'wrapped'], default='standard')
    parser.add_argument('--guicedee-version', default=framework_version())
    parser.add_argument('--maven-repository', type=Path, default=Path.home()/'.m2/repository')
    parser.add_argument('--maven', default=shutil.which('mvn'))
    parser.add_argument('--tag', default='local')
    parser.add_argument('--skip-emulator', action='store_true')
    parser.add_argument('--trace-directory', type=Path, help='Fresh GuicedEE native capability trace')
    parser.add_argument('--audit-native', action='store_true')
    parser.add_argument('--include-desktop', action='store_true')
    args = parser.parse_args()
    variants = select_variants(args.framework, 'both', args.runtime, args.native, args.quarkus_dependencies)
    if not variants:
        parser.error('No supported variants selected; application jlink is GuicedEE-only')
    native = any(v['runtime'] == 'native' for v in variants)
    if native and not args.docker:
        parser.error('Native builds require --docker (Linux compiler/runtime)')
    repository = args.maven_repository.expanduser().resolve()
    guicedee = args.framework in ['both', 'guicedee']
    wrapped = args.framework in ['both', 'quarkus'] and args.quarkus_dependencies == 'wrapped'
    standard = args.framework in ['both', 'quarkus'] and not wrapped
    if guicedee or wrapped or not args.docker:
        if not args.maven:
            parser.error('Maven 4 must be on PATH, or supply --maven')
        version = subprocess.check_output([args.maven, '-version'], text=True, stderr=subprocess.STDOUT)
        if not re.search(r'Apache Maven 4\.', version):
            parser.error('Maven 4 is required')
    mvn = [args.maven, '-B', '-ntp', f'-Dmaven.repo.local={repository}',
           f'-Dguicedee.version={args.guicedee_version}']
    if guicedee or wrapped:
        # Let Maven resolve released inputs normally. Never source them from a sibling checkout.
        for artifact in ['client'] + (['native-image'] if native and guicedee else []):
            if not (repository / f'com/guicedee/{artifact}/{args.guicedee_version}/{artifact}-{args.guicedee_version}.jar').is_file():
                run(mvn + ['-f', ROOT/'tools/resolver-pom.xml', 'dependency:get',
                           f'-Dartifact=com.guicedee:{artifact}:{args.guicedee_version}', '-Dtransitive=false'])
        verify_framework(repository, args.guicedee_version, native and guicedee)
        modules = ['guicedee', 'guicedee-scan']
        profiles = []
        if native and guicedee:
            modules.append('guicedee-native')
            profiles.append('native-app')
        if wrapped:
            modules += ['quarkus', 'quarkus-native']
            profiles.append('wrapped-control')
        if not args.docker and any(v['runtime'] == 'jlink' for v in variants):
            modules += ['guicedee-jlink', 'guicedee-scan-jlink']
            profiles.append('jlink')
        profile_flags = ['-P' + ','.join(profiles)] if profiles else []
        run(mvn + ['-f', ROOT/'pom.xml', '-pl', ','.join(modules), '-am', *profile_flags, 'clean', 'install'])
        applications = ['guicedee', 'guicedee-scan'] + (['guicedee-native'] if native and guicedee else [])
        for app in applications:
            run(mvn + ['-f', ROOT/app/'pom.xml', 'dependency:build-classpath',
                       '-Dmdep.outputFile=target/classpath.txt', '-Dmdep.regenerateFile=true'])
        for app in ['guicedee', 'guicedee-scan']:
            run(mvn + ['-f', ROOT/app/'pom.xml', 'dependency:copy-dependencies',
                       '-DincludeScope=runtime', f'-DoutputDirectory={ROOT/app/"target/lib"}'])
        run([sys.executable, ROOT/'tools/prepare_jlink.py'])
        if args.docker:
            run([sys.executable, ROOT/'tools/stage_link_repository.py', '--repository', repository,
                 '--applications', *applications])
    if standard and not args.docker:
        run(mvn + ['-f', ROOT/'quarkus-standard/pom.xml', 'clean', 'package'])
    if native and (guicedee or wrapped):
        if args.trace_directory:
            run([sys.executable, ROOT/'tools/import_native_trace.py', args.trace_directory.resolve()])
        run([sys.executable, ROOT/'tools/prepare_native_metadata.py', '--repository', ROOT/'docker/repository',
             '--version', args.guicedee_version])
        if wrapped:
            run([sys.executable, ROOT/'tools/prepare_native.py'])
        if guicedee:
            command = [sys.executable, ROOT/'tools/prepare_guicedee_native.py', '--repository', repository,
                       '--version', args.guicedee_version]
            if args.trace_directory:
                command += [args.trace_directory.resolve()]
            run(command)
    if args.docker:
        # Standard Quarkus uses an independent Maven dependency graph in Docker.
        # Its final provenance replaces this shared-stage input.
        if not (native and guicedee):
            run([sys.executable, ROOT/'tools/image_provenance.py'])
        for variant in variants:
            run(['docker', 'build', '--target', variant['id'], '-t', f'devsuite-bench-{variant["id"]}:{args.tag}',
                 '--build-arg', f'GUICEDEE_VERSION={args.guicedee_version}',
                 '--build-arg', f'NATIVE_AUDIT={str(args.audit_native).lower()}',
                 '--build-arg', f'NATIVE_DESKTOP={str(args.include_desktop).lower()}',
                 '-f', ROOT/'docker/Dockerfile', ROOT])
    if not args.skip_emulator:
        npm = shutil.which('npm')
        node = shutil.which('node')
        if not npm or not node:
            parser.error('Node.js/npm are required for the Firestore emulator; or use --skip-emulator')
        run([npm, 'ci', '--prefix', ROOT/'fixtures/firebase', '--ignore-scripts', '--no-audit'])
        run([node, ROOT/'fixtures/firebase/node_modules/firebase-tools/lib/bin/firebase.js', 'setup:emulators:firestore'])


if __name__ == '__main__':
    try:
        main()
    except (ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error))
