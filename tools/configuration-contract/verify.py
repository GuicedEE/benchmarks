"""Run isolated class/package discovery probes against locally built 5.2.3 jars.

Build client, vertx, metrics, telemetry and benchmark dependencies first. This script
compiles the fixtures into target/, never loads the workspace .env, and starts no services.
"""
from pathlib import Path
import os, subprocess, tempfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
TARGET = ROOT / 'benchmarks/target/configuration-contract'
TARGET.mkdir(parents=True, exist_ok=True)
java_home = Path(os.environ.get('JAVA_HOME', 'C:/Software/jdk/25'))
suffix = '.exe' if os.name == 'nt' else ''
java, javac = (java_home / 'bin' / (tool + suffix) for tool in ('java', 'javac'))
excluded = {'client-2.6.0.jar', 'vertx-2.6.0.jar', 'inject-2.6.0.jar', 'metrics-2.6.0.jar', 'guiced-telemetry-2.6.0.jar'}
cp = [ROOT / f'GuicedEE/{module}/target/classes' for module in ['client', 'vertx', 'metrics', 'telemetry']]
cp += [p for p in (ROOT / 'benchmarks/guicedee/target/lib').glob('*.jar') if p.name not in excluded]
cp += list((Path.home() / '.m2/repository/io/vertx').glob('*/5.2.3/*-5.2.3.jar'))
classes = TARGET / 'classes'
classes.mkdir(exist_ok=True)
args = ['-cp', os.pathsep.join(map(str, cp)), '-d', str(classes), *map(str, HERE.rglob('*.java'))]
(TARGET / 'compile.args').write_text('\n'.join('"'+a.replace('\\','/')+'"' for a in args), encoding='utf-8')
subprocess.run([str(javac), '@'+str(TARGET / 'compile.args')], check=True)
services = classes / 'META-INF/services'
services.mkdir(parents=True, exist_ok=True)
(services / 'com.guicedee.client.services.IGuiceProvider').write_text('configcontract.ProbeContext\n')
(services / 'com.guicedee.client.services.IGuiceDiscovery').write_text('configcontract.ProbeIndex\n')
for mode in ['spi', 'scan']:
    for declaration in ['pkg', 'type', 'duplicate']:
        args = ['-cp', os.pathsep.join(map(str, [classes, *cp])), '-DGUICEDEE_DISCOVERY_MODE='+mode,
                '-Dconfig.contract.declaration='+declaration, 'configcontract.Probe']
        argfile = TARGET / f'{mode}-{declaration}.args'
        argfile.write_text('\n'.join('"'+a.replace('\\','/')+'"' for a in args), encoding='utf-8')
        with tempfile.TemporaryDirectory(prefix='guicedee-config-contract-') as cwd:
            Path(cwd, '.env').write_text('VERTX_EVENT_WORKER_ORDERS_CREATED=true\nVERTX_WORKER_POOL_SIZE=5\nCONTRACT_HA_GROUP=shared-group\nCONTRACT_DNS=8.8.8.8\nCONTRACT_WORKER=contract-worker\nCONTRACT_REGISTRY=contract-registry\nCONTRACT_SERVICE=contract-service\nCONTRACT_CACHE_PATH=contract-cache\n')
            Path(cwd, '.env.local').write_text('VERTX_WORKER_POOL_SIZE=7\nCONTRACT_HA_GROUP=local-group\nCONTRACT_SEARCH_DOMAINS=local.test,example.test\n')
            env = {k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','TEMP','TMP'}}
            env['VERTX_WORKER_POOL_SIZE'] = '9'
            env['CONTRACT_HA_GROUP'] = 'os-group'
            result = subprocess.run([str(java), '@'+str(argfile)], cwd=cwd, env=env, capture_output=True,
                                    text=True, encoding='utf-8', errors='replace', timeout=40)
            (TARGET / f'{mode}-{declaration}.log').write_text(result.stdout+result.stderr, encoding='utf-8')
            if result.returncode: print(result.stdout, result.stderr); result.check_returncode()
            assert 'CONFIGURATION_CONTRACT_OK' in result.stdout
            print(mode+' '+declaration+' PASS', flush=True)
