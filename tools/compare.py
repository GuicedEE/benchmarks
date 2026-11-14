"""Fresh-process capability and latency comparison; failed parity never becomes a performance win."""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import socket
import statistics
import subprocess
import threading
import time
import urllib.error
import urllib.request
import uuid
from upstream import Upstream
from variants import select_variants, ordered_variants, paired_image_variants, guicedee_jar, guicedee_project, runtime_flags

ROOT = Path(__file__).resolve().parents[1]


def request(base, path, body=None, raw=None, headers=None, timeout=15):
    data = raw if raw is not None else json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base+path, data=data, headers=headers or {"Content-Type": "application/json"})
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status, content = response.status, response.read().decode()
    except urllib.error.HTTPError as response:
        with response:
            status, content = response.code, response.read().decode()
    try: parsed = json.loads(content)
    except ValueError: parsed = content
    return status, parsed, (time.perf_counter()-started)*1000


def port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def stop(process):
    if process.poll() is not None: return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        import signal
        os.killpg(process.pid, signal.SIGTERM)
    try: process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        if os.name != "nt": os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)


def start(command, log, env, cwd=ROOT):
    return subprocess.Popen(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT,
                            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
                            start_new_session=os.name != "nt")


def percentile(values, quantile):
    return sorted(values)[min(len(values)-1, int((len(values)-1)*quantile))]


def metric_counts(body):
    if not isinstance(body, str): return {}
    values = {}
    for line in body.splitlines():
        if line.startswith('#') or 'benchmark_quotes' not in line: continue
        match = re.fullmatch(r'(.+?)\s+([0-9.eE+\-]+)(?:\s+[0-9]+)?', line)
        if match: values[match[1]] = float(match[2])
    return values


def eligible_comparison(rows, runs, variants):
    expected = {(v['id'], run) for v in variants for run in range(1, runs+1)}
    actual = {(r.get('variant'), r.get('run')) for r in rows}
    return len(variants) > 1 and len(rows) == len(expected) and actual == expected and all(
        r.get('eligible', False) and not r.get('instrumented', False) for r in rows)


def phase_evidence(log, directory, framework):
    operations = [json.loads(line.split('BENCH_PHASE ', 1)[1]) for line in log.splitlines() if line.startswith('BENCH_PHASE ')]
    expected = {'workload-construction', 'first-quote', 'first-firestore'}
    names = [o['operation'] for o in operations]
    # CDI client proxies may run superclass field initializers too. Retain those
    # extra constructions as evidence; require exactly one exercised SDK flow.
    passed = set(names) == expected and names.count('first-quote') == 1 and names.count('first-firestore') == 1 and all(o['success'] for o in operations)
    startup = directory/'startup.json'
    core = json.loads(startup.read_text()) if startup.is_file() else None
    if framework == 'guicedee':
        passed = passed and core is not None and core['droppedEvents'] == 0 and all(e['success'] for e in core['events'])
        passed = passed and {'application-startup', 'guice-create-injector', 'pre-startup', 'post-startup'}.issubset(
            {e['phase'] for e in core['events']} if core else set())
    return {'verified':bool(passed), 'workload':operations, 'startup':core}


def discovery_evidence(log, discovery):
    scanning = 'Initializing ClassGraph scanner for dependency discovery' in log
    deployments = {package: f'Deploying Verticle: {package} -' in log
                   for package in ['bench.guicedee.rest', 'bench.guicedee.service']}
    return {'classGraphInitialized':scanning, 'verticleDeployments':deployments,
            'verified':scanning == (discovery == 'scan') and all(deployments.values()),
            'logLines':[line for line in log.splitlines() if any(marker in line for marker in
                         ['Initializing ClassGraph', 'Classpath scan completed', 'Deploying Verticle: bench.guicedee'])]}


def probe(variant, run, out, upstream, flags, args):
    flags = runtime_flags(variant, flags)
    framework = variant['framework']
    application = guicedee_project(variant) if framework == 'guicedee' else 'quarkus-native' if variant['runtime']=='native' else 'quarkus'
    if variant.get('dependencyMode') == 'standard': application = 'quarkus-standard'
    app_port = port()
    env = dict(os.environ, HTTP_PORT=str(app_port), HTTPS_ENABLED="false", HTTP_HOST="127.0.0.1",
               BENCH_UPSTREAM=f"http://127.0.0.1:{upstream.server_port}", FIRESTORE_EMULATOR_HOST="127.0.0.1:18088",
               GCLOUD_PROJECT="demo-devsuite")
    # Remove implicit JVM tuning from the parent so both variants receive exactly the recorded flags.
    for name in ["JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS", "_JAVA_OPTIONS"]: env.pop(name, None)
    if framework == "guicedee":
        env['GUICEDEE_DISCOVERY_MODE']=variant['discovery']
        cp = (ROOT/application/'target/classpath.txt').read_text().strip() if not args.docker else ''
        module = 'bench.guicedee.scan' if variant['discovery'] == 'scan' else 'bench.guicedee'
        launch = [] if variant['runtime']=='native' else ['--module-path', str(ROOT/application/'target'/guicedee_jar(variant))+os.pathsep+cp, '-m', module+'/bench.guicedee.Main']
    else: launch = [] if variant['runtime']=='native' else ['-jar', str(ROOT/application/'target/quarkus-app/quarkus-run.jar')]
    name = f'{variant["id"]}-{run}'
    diagnostics = getattr(args, 'diagnostics', False)
    if diagnostics and framework == 'guicedee':
        flags.append('-Dguice_startup_diagnostics=true')
    diagnostic_dir = out/(name+'-diagnostics')
    if diagnostics:
        diagnostic_dir.mkdir()
        env['BENCH_PHASE_DIAGNOSTICS']='true'
        env['GUICEDEE_DIAGNOSTICS_DIR']=str(diagnostic_dir.resolve())
    container = None
    if args.docker:
        container = 'devsuite-bench-' + uuid.uuid4().hex[:12]
        env.update(HTTP_PORT='8080', HTTP_HOST='0.0.0.0', QUARKUS_HTTP_HOST='0.0.0.0',
                   BENCH_UPSTREAM=f'http://host.docker.internal:{upstream.server_port}',
                   FIRESTORE_EMULATOR_HOST='host.docker.internal:18088')
        launch = (['-m', module+'/bench.guicedee.Main'] if variant['runtime']=='jlink' else ['--module-path','/app/app.jar:/app/lib','-m',module+'/bench.guicedee.Main']) if framework=='guicedee' else [] if variant['runtime']=='native' else ['-jar','/app/quarkus-run.jar']
        if variant['runtime']=='native': launch=[]
    argfile = out/(name+'.args')
    argfile.write_text('\n'.join('"'+a.replace('\\','/')+'"' for a in flags+launch)+'\n')
    log = (out/(name+'.log')).open('w')
    started = time.perf_counter()
    command = [shutil.which('java'), '@'+str(argfile)]
    if variant['runtime'] == 'jlink' and not container:
        launcher = ROOT/(application+'-jlink')/'target/maven-jlink/default/bin'/('benchmark.bat' if os.name == 'nt' else 'benchmark')
        if not launcher.is_file(): raise RuntimeError('Build the application jlink module first: '+str(launcher))
        env['JAVA_TOOL_OPTIONS']=' '.join(flags)
        command = [str(launcher)]
    if container:
        command = ['docker','run','--name',container,'--cpus','0.25','--memory','500m','--memory-swap','500m',
                   '--publish',f'127.0.0.1:{app_port}:8080']
        if diagnostics:
            env['GUICEDEE_DIAGNOSTICS_DIR']='/diagnostics'
            command += ['--mount',f'type=bind,source={diagnostic_dir.resolve()},target=/diagnostics',
                        '--env','BENCH_PHASE_DIAGNOSTICS=true']
        for key in ['HTTP_PORT','HTTPS_ENABLED','HTTP_HOST','QUARKUS_HTTP_HOST','BENCH_UPSTREAM','FIRESTORE_EMULATOR_HOST',
                    'GCLOUD_PROJECT']:
            command += ['--env',key+'='+env[key]]
        if framework=='guicedee':
            # Defaults stay in the image's .env. Explicit host overrides retain their normal precedence.
            for key in sorted(env):
                if key.startswith(('GUICEDEE_', 'VERTX_', 'METRICS_', 'TELEMETRY_', 'OTEL_')):
                    command += ['--env',key+'='+env[key]]
            local_env=ROOT/application/'.env.local'
            if local_env.exists():
                command += ['--mount',f'type=bind,source={local_env},target=/app/.env.local,readonly']
        if variant['runtime'] == 'jlink':
            command += ['--env', 'JAVA_TOOL_OPTIONS='+' '.join(flags), args.images[variant['id']]]
        else:
            command += [args.images[variant['id']],*flags,*launch]
    process = start(command, log, env, ROOT/application)
    base = f'http://127.0.0.1:{app_port}'
    row = {'framework': framework, 'variant': variant['id'], 'discovery': variant['discovery'],
           'runtime': variant['runtime'], 'run': run, 'checks': {}, 'samples': [],
           'runtimeFlags':flags, 'jvmFlags':[] if variant['runtime']=='native' else flags,
           'jvmFlagsSource':'not-applicable' if variant['runtime']=='native' else 'JAVA_TOOL_OPTIONS' if variant['runtime']=='jlink' else 'arguments',
           'launch': (['/app/application',*flags] if variant['runtime']=='native' else [('/opt/java/openjdk/bin/benchmark' if container else str(launcher))] if variant['runtime']=='jlink' else flags+launch)}
    if 'comparisonRole' in variant:
        row.update(comparisonRole=variant['comparisonRole'],imageArtifact=variant['imageArtifact'],imageTag=variant['imageTag'])
    row['dependencyMode'] = variant.get('dependencyMode', 'wrapped')
    event_start = len(upstream.events)
    def check(name, condition, observed):
        row['checks'][name] = {'passed': bool(condition), 'observed': observed}
    try:
        deadline = started + 120
        while time.perf_counter() < deadline:
            if process.poll() is not None: raise RuntimeError(f'Application exited {process.returncode}; see {name}.log')
            try:
                response = request(base, '/ready', timeout=.5)
                if response[:2] == (200, {'ready': True}): break
            except (OSError, TimeoutError): pass
            time.sleep(.05)
        else: raise TimeoutError('Readiness timed out')
        row['launchToReadyMs'] = (time.perf_counter()-started)*1000
        route = '/quote?persist=true' if args.firebase else '/quote'
        order = {'sku': 'fixture', 'quantity': 2}
        expected = {'sku': 'fixture', 'quantity': 2, 'total': 250, 'available': 40, 'project': 'Fixture shop'}
        status, body, latency = request(base, route, order, timeout=60 if args.docker else 15)
        row['firstBusinessStatus'] = status
        row['firstBusinessMs'] = latency
        row['launchToFirstBusinessMs'] = (time.perf_counter()-started)*1000
        check('business', status == 200 and body == expected, {'status': status, 'body': body})
        events = upstream.events[event_start:]
        for label, path in [('vendorSdkOAuth','/oauth/token'),('vendorSdkRest','/benchmark'),('graphqlClient','/benchmark/graphql')]:
            hits = [e for e in events if e['path'] == path]
            check(label, bool(hits) and all(e['status']==200 for e in hits), hits)
        status, body, _ = request(base, '/quote', order)
        check('optionalPrimitiveQuery', status==200 and body==expected, {'status':status,'body':body})
        status, body, _ = request(base, '/quote?persist=false', {'sku':'fixture','quantity':0})
        check('validationError', status==400 and body=={'error':{'code':'INVALID_ORDER','status':400}}, {'status':status,'body':body})
        for label, data, header, expected_status in [('malformedJson',b'{',{'Content-Type':'application/json'},400),
                                                    ('unsupportedMedia',b'hello',{'Content-Type':'text/plain'},415)]:
            status, body, _ = request(base, '/quote?persist=false', raw=data, headers=header)
            check(label, status==expected_status, {'status':status,'body':body})
        retry_id = name
        status, body, _ = request(base, '/retry/'+retry_id)
        attempts = upstream.counts['/flaky/'+retry_id]
        check('reactiveRetry', status==200 and body=={'result':'ok'} and attempts==3, {'status':status,'body':body,'attempts':attempts})
        previous = upstream.counts['/flaky/always']
        status, body, _ = request(base, '/retry/always')
        attempts = upstream.counts['/flaky/always']-previous
        check('retryExhaustion', status==502 and body=={'error':{'code':'UPSTREAM_FAILURE','status':502}} and attempts==3,
              {'status':status,'body':body,'attempts':attempts})
        with concurrent.futures.ThreadPoolExecutor() as pool:
            pending = pool.submit(request, base, '/timeout')
            time.sleep(.02)
            _, _, ready_ms = request(base, '/ready')
            status, body, elapsed = pending.result()
        check('reactiveTimeout', status==504 and body=={'error':{'code':'UPSTREAM_TIMEOUT','status':504}} and elapsed<(1000 if args.docker else 225),
              {'status':status,'body':body,'elapsedMs':elapsed,'concurrentReadyMs':ready_ms})
        status, body, _ = request(base, '/metrics', headers={})
        before = metric_counts(body)
        request(base, route, order)
        after_status, after_body, _ = request(base, '/metrics', headers={})
        after = metric_counts(after_body)
        check('metrics', status==200 and after_status==200 and any(after.get(k,0)>v for k,v in before.items()),
              {'status':status,'before':before,'after':after})
        status, body, latency = request(base, '/openapi.json', headers={'Accept':'application/json'})
        row['firstOpenApiJsonMs'] = latency
        if status == 200 and isinstance(body, dict):
            (out/f'{variant["id"]}-{run}-openapi.json').write_text(json.dumps(body,indent=2)+'\n',encoding='utf-8')
        check('openapi', status==200 and isinstance(body,dict) and '/quote' in body.get('paths',{}), {'status':status,'paths':list(body.get('paths',{})) if isinstance(body,dict) else body[:300]})
        status, body, _ = request(base, '/swagger/' if framework=='quarkus' else '/swagger/index.html', headers={})
        assets={}
        for asset,marker in [('swagger-ui-bundle.js','SwaggerUIBundle'),('swagger-ui.css','.swagger-ui')]:
            asset_status,asset_body,_=request(base,'/swagger/'+asset,headers={})
            assets[asset]={'status':asset_status,'contentLength':len(asset_body),
                           'valid':asset_status==200 and isinstance(asset_body,str) and marker in asset_body}
        check('swagger', status==200 and isinstance(body,str) and 'swagger' in body.lower()
              and all(asset['valid'] for asset in assets.values()), {'status':status,'assets':assets})
        if args.firebase:
            status, body, _ = request(base, '/firebase/'+name)
            check('firebaseFirestore', status==200 and body=={'id':name,'sku':'fixture','total':250}, {'status':status,'body':body})
        else: row['checks']['firebaseFirestore']={'passed':False,'status':'not_run','reason':'--firebase not selected'}
        # Diagnostic warm latency is retained even if parity fails; reports cannot rank that run.
        for _ in range(args.warmup): request(base, route, order)
        for _ in range(args.requests):
            status, body, elapsed = request(base, route, order)
            row['samples'].append({'ms':elapsed,'ok':status==200 and body==expected,'status':status})
        times=[s['ms'] for s in row['samples']]
        row['warm']={'p50Ms':statistics.median(times),'p95Ms':percentile(times,.95),'p99Ms':percentile(times,.99),
                     'failures':sum(not s['ok'] for s in row['samples']), 'requests':len(times),'concurrency':1}
        row['eligible'] = all(c['passed'] for c in row['checks'].values()) and row['warm']['failures']==0
    except Exception as error:
        row['error']=str(error);row['eligible']=False
    finally:
        if container:
            inspected=subprocess.run(['docker','inspect',container],capture_output=True,text=True)
            if inspected.returncode==0:
                details=json.loads(inspected.stdout)[0]
                row['container']={'image':details['Image'],'state':details['State'],
                                  'nanoCpus':details['HostConfig']['NanoCpus'],'memoryBytes':details['HostConfig']['Memory'],
                                  'memorySwapBytes':details['HostConfig']['MemorySwap']}
                row['containerStats']=subprocess.run(['docker','exec',container,'sh','-c',
                    'cat /sys/fs/cgroup/cpu.stat /sys/fs/cgroup/memory.peak /sys/fs/cgroup/memory.current /sys/fs/cgroup/memory.events'],
                    capture_output=True,text=True).stdout
                if row['container']['nanoCpus']!=250000000 or row['container']['memoryBytes']!=524288000 or details['State']['OOMKilled']:
                    row['eligible']=False
            else: row['eligible']=False
            subprocess.run(['docker','rm','-f',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        stop(process);log.close()
        if framework == 'guicedee':
            row['discoveryEvidence']=discovery_evidence((out/(name+'.log')).read_text(errors='replace'), variant['discovery'])
            row['eligible']=row['eligible'] and row['discoveryEvidence']['verified']
        row['upstreamEvents']=upstream.events[event_start:]
        if diagnostics:
            row['instrumented']=True
            row['capabilitiesPassed']=row['eligible']
            row['phaseEvidence']=phase_evidence((out/(name+'.log')).read_text(errors='replace'), diagnostic_dir, framework)
            row['eligible']=False
        (out/(name+'.json')).write_text(json.dumps(row,indent=2)+'\n')
    print(name, 'eligible='+str(row['eligible']), 'failed='+str([k for k,v in row['checks'].items() if not v['passed']]), row.get('error',''), flush=True)
    return row


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--runs',type=int,default=5)
    parser.add_argument('--requests',type=int,default=100)
    parser.add_argument('--warmup',type=int,default=20)
    parser.add_argument('--firebase',action='store_true',help='Start the official Firestore emulator; required for full parity')
    parser.add_argument('--tiered',action='store_true',help='Apply TieredStopAtLevel=1 to BOTH frameworks')
    parser.add_argument('--docker',action='store_true',help='Use built Linux images with enforced 250m CPU / 500Mi RAM')
    parser.add_argument('--discovery',choices=['scan','spi','both'],default='both',help='Select separate SPI/scanner artifacts; default compares both')
    parser.add_argument('--runtime',choices=['jre','jlink','both','native'],default='jre',help='JVM, linked application, or native executables (Docker only)')
    parser.add_argument('--native',action='store_true',help='Include the separate GuicedEE SPI and Quarkus native projects in the selected matrix')
    parser.add_argument('--framework',choices=['both','guicedee','quarkus'],default='both')
    parser.add_argument('--quarkus-dependencies', choices=['wrapped','standard'], default='standard',
                        help='standard uses the independent upstream-SDK Quarkus project; wrapped preserves historical batches')
    parser.add_argument('--diagnostics',action='store_true',help='Collect startup/SDK phases and live scan/binding inventories; never a performance comparison')
    parser.add_argument('--image-tag',default='local',help='Docker image tag; immutable IDs are resolved before running')
    parser.add_argument('--baseline-image-tag',help='Alternate a baseline tag with --image-tag in the same Docker batch')
    parser.add_argument('--reverse-initial-order',action='store_true',help='Reverse the initial variant order for an independently counterbalanced batch')
    parser.add_argument('--initial-heap',default='128m',help='Initial heap for every selected variant; retained in the result flags')
    args=parser.parse_args()
    if min(args.runs,args.requests)<1 or args.warmup<0: parser.error('Invalid run/request counts')
    if not re.fullmatch(r'[1-9][0-9]*[mMgG]',args.initial_heap): parser.error('Initial heap must be a positive size such as 32m')
    variants = select_variants(args.framework, args.discovery, args.runtime, args.native, args.quarkus_dependencies)
    if args.baseline_image_tag:
        if not args.docker: parser.error('Paired image comparisons require --docker')
        try: variants = paired_image_variants(variants,args.baseline_image_tag,args.image_tag)
        except ValueError as error: parser.error(str(error))
    if not variants: parser.error('No supported variants selected; GuicedEE native requires SPI discovery and application jlink is GuicedEE-only')
    if args.reverse_initial_order: variants.reverse()
    if any(v['runtime']=='native' for v in variants) and not args.docker:
        parser.error('Native comparison requires --docker (the executable is built for Linux)')
    if args.diagnostics and not args.firebase:
        parser.error('Phase diagnostics require --firebase for complete SDK phases')
    out=ROOT/'target/runs'/time.strftime('%Y%m%d-%H%M%S')
    out.mkdir(parents=True)
    flags=['-Xms'+args.initial_heap,'-Xmx384m','-XX:ActiveProcessorCount=2']+(['-XX:TieredStopAtLevel=1'] if args.tiered else [])
    inputs=[]
    for directory in [ROOT/'guicedee/target',ROOT/'guicedee-scan/target',ROOT/'quarkus/target/quarkus-app',ROOT/'quarkus-standard/target/quarkus-app']:
        for file in directory.rglob('*.jar'):
            inputs.append({'path':str(file.relative_to(ROOT)),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
    for application in ['guicedee','guicedee-scan']:
        cp=ROOT/application/'target/classpath.txt'
        if cp.exists():
            for path in cp.read_text().strip().split(os.pathsep):
                file=Path(path);inputs.append({'path':str(file),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
    meta={'platform':platform.platform(),'java':subprocess.run(['java','-version'],capture_output=True,text=True).stderr,
          'flags':flags,'arguments':dict(vars(args)),'variants':variants,'inputs':inputs,'cpuQuota':'Docker 0.25 CPU / 500Mi RAM' if args.docker else 'unrestricted host; ActiveProcessorCount is NOT a CPU limit',
          'executionModel':'application-module-path-native-v2', 'historicalComparison':False,'profile':'firebase-full' if args.firebase else 'without-firebase',
          'sourceRevision':subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True).stdout.strip()}
    meta['linkedRuntimeArtifacts']={}
    if not args.docker:
        for application in ['guicedee','guicedee-scan']:
            image=ROOT/(application+'-jlink')/'target/maven-jlink/default'
            if (image/'lib/modules').is_file():
                meta['linkedRuntimeArtifacts'][application]={
                    'modulesSha256':hashlib.sha256((image/'lib/modules').read_bytes()).hexdigest(),
                    'release':(image/'release').read_text(),
                    'modules':subprocess.check_output([str(image/'bin'/('java.exe' if os.name=='nt' else 'java')), '--list-modules'],text=True)}
    meta['benchmarkSources']=[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
                              for p in ROOT.rglob('*') if p.is_file() and (p.suffix in ['.java','.py','.xml','.properties','.ps1'] or p.name=='.env')
                              and not any(part in ['target','node_modules','repository','results','.idea','.git','analysis'] for part in p.relative_to(ROOT).parts)]
    meta['guicedeeLocalEnvSha256']={}
    for application in ['guicedee','guicedee-scan']:
        local_env=ROOT/application/'.env.local'
        meta['guicedeeLocalEnvSha256'][application]=hashlib.sha256(local_env.read_bytes()).hexdigest() if local_env.exists() else None
    meta['emulatorInputs']=[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
                           for p in (Path.home()/'.cache/firebase/emulators').glob('cloud-firestore-emulator-*.jar')]
    if args.docker:
        inspected={v['id']:json.loads(subprocess.check_output(['docker','image','inspect',
            f'devsuite-bench-{v.get("imageArtifact",v["id"])}:{v.get("imageTag",args.image_tag)}'],text=True))[0] for v in variants}
        meta['images']={name:details['Id'] for name,details in inspected.items()}
        meta['imageSizeBytes']={name:details['Size'] for name,details in inspected.items()}
        meta['imageLaunchConfiguration']={name:{key:details['Config'].get(key) for key in ['Entrypoint','Cmd']}
                                          for name,details in inspected.items()}
        meta['imageBuildProvenance']={framework:json.loads(subprocess.check_output(
            ['docker','run','--rm','--entrypoint','cat',image,'/app/build-provenance.json'],text=True))
            for framework,image in meta['images'].items()}
        native_ids={v['id'] for v in variants if v['runtime']=='native'}
        meta['containerJava']={name:subprocess.run(['docker','run','--rm','--entrypoint','/opt/java/openjdk/bin/java',image,'-version'],capture_output=True,text=True).stderr
                               for name,image in meta['images'].items() if name not in native_ids}
        meta['runtimeDetails']={name:subprocess.check_output(['docker','run','--rm','--entrypoint','sh',image,'-c',
             'java --list-modules; du -sb /opt/java/openjdk; sha256sum /opt/java/openjdk/lib/modules; if test -f /oracle-jdk-sha256.txt; then cat /oracle-jdk-sha256.txt; fi; if test -f /opt/java/openjdk/bin/benchmark; then cat /opt/java/openjdk/bin/benchmark; fi; if test -f /app/runtime-analysis.txt; then cat /app/runtime-analysis.txt; fi'],text=True)
             for name,image in meta['images'].items() if name not in native_ids}
        meta['nativeRuntimeDetailsByVariant']={}
        for native_id in sorted(native_ids):
            native_image=meta['images'][native_id]
            details=subprocess.check_output(['docker','run','--rm','--entrypoint','sh',native_image,'-c',
                'test ! -e /opt/java/openjdk/bin/java && test -x /app/application && cat /app/native-build-info.txt && sha256sum /app/application && wc -c /app/application && od -An -tx1 -N4 /app/application && ldd /app/application'],text=True)
            meta['nativeRuntimeDetailsByVariant'][native_id]=details
            if native_id=='quarkus-native': meta['nativeRuntimeDetails']=details
            if '7f 45 4c 46' not in details or meta['imageLaunchConfiguration'][native_id]['Entrypoint']!=['/app/application']:
                raise RuntimeError('Native image must contain an ELF executable and launch it directly')
        for variant in variants:
            if variant['runtime'] == 'jlink':
                module = 'bench.guicedee.scan' if variant['discovery'] == 'scan' else 'bench.guicedee'
                details = meta['runtimeDetails'][variant['id']]
                if not re.search(r'^'+re.escape(module)+r'@', details, re.MULTILINE):
                    raise RuntimeError('Application module missing from linked runtime: '+variant['id'])
                if meta['imageLaunchConfiguration'][variant['id']]['Entrypoint'] != ['/opt/java/openjdk/bin/benchmark']:
                    raise RuntimeError('Linked image must use its generated application launcher: '+variant['id'])
    (out/'environment.json').write_text(json.dumps(meta,indent=2)+'\n')
    if args.docker: args.images=meta['images']
    server=Upstream('0.0.0.0' if args.docker else '127.0.0.1');thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    emulator=None;emulator_log=None;rows=[]
    try:
        if args.firebase:
            with socket.socket() as sock:
                if sock.connect_ex(('127.0.0.1',18088))==0: raise RuntimeError('Emulator port occupied; refusing to reuse unknown service')
            cli=ROOT/'fixtures/firebase/node_modules/firebase-tools/lib/bin/firebase.js'
            emulator_log=(out/'firestore.log').open('w')
            config=json.loads((ROOT/'fixtures/firebase/firebase.json').read_text())
            config['emulators']['firestore']['host']='0.0.0.0' if args.docker else '127.0.0.1'
            config['firestore']['rules']=str(ROOT/'fixtures/firebase/firestore.rules')
            (out/'firebase.json').write_text(json.dumps(config,indent=2)+'\n')
            emulator=start([shutil.which('node'),str(cli),'emulators:start','--only','firestore','--project','demo-devsuite','--non-interactive','--config',str(out/'firebase.json')],
                           emulator_log,dict(os.environ),ROOT/'fixtures/firebase')
            deadline=time.monotonic()+120
            while time.monotonic()<deadline:
                if emulator.poll() is not None: raise RuntimeError('Firestore emulator exited; see firestore.log')
                with socket.socket() as sock:
                    if sock.connect_ex(('127.0.0.1',18088))==0: break
                time.sleep(.2)
            else: raise TimeoutError('Firestore emulator startup timed out')
        for run in range(1,args.runs+1):
            for variant in ordered_variants(variants, run):
                rows.append(probe(variant,run,out,server,flags,args))
    finally:
        server.shutdown();server.server_close()
        if emulator: stop(emulator)
        if emulator_log: emulator_log.close()
        aggregates={}
        for variant in variants:
            selected=[r for r in rows if r['variant']==variant['id']]
            aggregates[variant['id']]={'completedRuns':len(selected), 'eligibleRuns':sum(r.get('eligible',False) for r in selected),
                'medianLaunchToReadyMs':statistics.median([r['launchToReadyMs'] for r in selected]) if selected and all('launchToReadyMs' in r for r in selected) else None,
                'medianLaunchToFirstBusinessMs':statistics.median([r['launchToFirstBusinessMs'] for r in selected]) if selected and all('launchToFirstBusinessMs' in r for r in selected) else None}
        summary={'eligibleComparison':eligible_comparison(rows,args.runs,variants), 'variants':variants, 'diagnosticMedians':aggregates,
                 'runs':rows,'scope':'Docker 250m/500Mi; no Kubernetes scale-out; native only when explicitly selected' if args.docker else 'Local JVM diagnostics; no Kubernetes CPU/memory enforcement or native image'}
        if args.diagnostics:
            summary.update(instrumented=True, performanceComparison=False,
                           allDiagnosticsPassed=len(rows)==args.runs*len(variants) and all(
                               r.get('capabilitiesPassed',False) and r.get('phaseEvidence',{}).get('verified',False) for r in rows))
        (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        print('Results:',out,flush=True)
    return 0 if (summary.get('allDiagnosticsPassed',False) if args.diagnostics else summary['eligibleComparison']) else 1


if __name__=='__main__': raise SystemExit(main())
