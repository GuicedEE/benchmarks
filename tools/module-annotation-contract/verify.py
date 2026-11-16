"""Verify module annotation consumers using fresh reactor classes, without external services.

Build the modules with dependency:build-classpath and
-Dmdep.outputFile=target/annotation-text-classpath.txt first.
"""
from pathlib import Path
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
TARGET = ROOT / 'benchmarks/target/module-annotation-contract'
TARGET.mkdir(parents=True, exist_ok=True)
modules = ['client', 'inject', 'vertx', 'web', 'metrics', 'telemetry', 'health', 'kafka',
           'ibmmq', 'rabbitmq', 'mailclient', 'consul', 'service-discovery', 'service-registry',
           'hazelcast', 'rest', 'rest-client', 'runtime-autoconfigure', 'persistence']
cp = [str(ROOT / 'GuicedEE' / module / 'target/classes') for module in modules]
for module in modules:
    cp += (ROOT / 'GuicedEE' / module / 'target/annotation-text-classpath.txt').read_text().strip().split(os.pathsep)
cp = list(dict.fromkeys(cp))
java_home = Path(os.environ.get('JAVA_HOME', 'C:/Software/jdk/25'))
suffix = '.exe' if os.name == 'nt' else ''
classes = TARGET / 'classes'
classes.mkdir(exist_ok=True)
args = ['-cp', os.pathsep.join(cp), '-d', str(classes), *map(str, HERE.rglob('*.java'))]
argfile = TARGET / 'compile.args'
argfile.write_text('\n'.join('"'+v.replace('\\', '/')+'"' for v in args), encoding='utf-8')
subprocess.run([str(java_home / 'bin' / ('javac'+suffix)), '@'+str(argfile)], check=True)
args = ['-cp', os.pathsep.join([str(classes), *cp]), 'ModuleAnnotationProbe']
argfile = TARGET / 'run.args'
argfile.write_text('\n'.join('"'+v.replace('\\', '/')+'"' for v in args), encoding='utf-8')
with tempfile.TemporaryDirectory(prefix='guicedee-module-annotations-') as cwd:
    Path(cwd, '.env').write_text('')
    Path(cwd, '.env.local').write_text('')
    env = {k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP'}}
    env['MODULE_OS_REFERENCE'] = 'os-value'
    result = subprocess.run([str(java_home / 'bin' / ('java'+suffix)), '@'+str(argfile)],
                            cwd=cwd, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
    (TARGET / 'result.log').write_text(result.stdout+result.stderr, encoding='utf-8')
    if result.returncode:
        print(result.stdout, result.stderr)
        result.check_returncode()
    print(result.stdout.strip())
