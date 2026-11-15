"""Build the independent PostgreSQL/Narayana and reactive-stateless JVM comparison."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from build import framework_version

ROOT = Path(__file__).resolve().parents[1]


def source_hashes():
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (ROOT/'persistence').rglob('*') if p.is_file()
            and not any(part in ['target', '__pycache__'] for part in p.relative_to(ROOT).parts)
            and p.name != '.env.local'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--guicedee-version', default=framework_version())
    parser.add_argument('--maven-repository', type=Path, default=Path.home()/'.m2/repository')
    parser.add_argument('--maven', default=shutil.which('mvn'))
    parser.add_argument('--java-image', default='eclipse-temurin:25-jdk')
    parser.add_argument('--tag', default='local')
    args = parser.parse_args()
    if not args.maven: parser.error('Maven 4 is required')
    mvn = [args.maven, '-B', '-ntp', f'-Dmaven.repo.local={args.maven_repository.resolve()}',
           f'-Dguicedee.version={args.guicedee_version}']
    def run(command):
        print('+', subprocess.list2cmdline([str(v) for v in command]), flush=True)
        subprocess.run(command, cwd=ROOT, check=True)
    run(mvn+['-Ppersistence', '-pl', 'persistence/guicedee', '-am', 'clean', 'install'])
    run(mvn+['-f', 'persistence/guicedee/pom.xml', 'dependency:copy-dependencies',
             '-DincludeScope=runtime', '-DoutputDirectory=target/lib'])
    run(mvn+['-f', 'persistence/quarkus/pom.xml', 'clean', 'package'])
    # Both images use precisely the same immutable JDK base even if a tag moves between builds.
    run(['docker', 'pull', args.java_image])
    base = json.loads(subprocess.check_output(['docker','image','inspect',args.java_image],text=True))[0]
    base_reference = base['RepoDigests'][0]
    provenance = dict(schemaVersion=1, sources=source_hashes(), javaImage=base_reference,
                      guicedeeVersion=args.guicedee_version,
                      maven=subprocess.check_output([args.maven,'-version'],text=True),
                      java=subprocess.check_output(['java','-version'],stderr=subprocess.STDOUT,text=True))
    output = ROOT/'persistence/target'
    output.mkdir(exist_ok=True)
    for variant in ['guicedee','quarkus']:
        packaged = ROOT/f'persistence/{variant}/target'
        jars = {p.relative_to(packaged).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in packaged.rglob('*.jar')}
        (output/f'{variant}-inputs.json').write_text(json.dumps(dict(provenance, variant=variant, jarSha256=jars)),encoding='utf-8')
        run(['docker','build','--target',variant,'--build-arg',f'JAVA_IMAGE={base_reference}',
             '-t',f'guicedee-bench-persistence-{variant}:{args.tag}', '-f','persistence/Dockerfile','persistence'])


if __name__ == '__main__':
    main()
