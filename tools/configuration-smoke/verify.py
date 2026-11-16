from pathlib import Path
import os, subprocess, tempfile, time, urllib.request, urllib.error, json, socket, re
root=Path(__file__).resolve().parents[3]
output=root/'benchmarks/target/annotation-smoke'
output.mkdir(exist_ok=True)
replacement={f'{name}-2.6.0.jar':root/f'GuicedEE/{name}/target/{name}-2.6.0.jar' for name in ['client','inject','vertx','web','metrics']}
replacement['guiced-telemetry-2.6.0.jar']=root/'GuicedEE/telemetry/target/guiced-telemetry-2.6.0.jar'
replacement['comparison-common-1.0-SNAPSHOT.jar']=root/'benchmarks/common/target/comparison-common-1.0-SNAPSHOT.jar'
java=Path(os.environ.get('JAVA_HOME', 'C:/Software/jdk/25'))/'bin'/('java.exe' if os.name=='nt' else 'java')
results=[]
cases=[('guicedee','spi',18080,False),('guicedee-scan','scan',18080,False),('guicedee-cdi','scan',18080,False),('guicedee-cdi-spi','spi',18080,False),('guicedee','spi',18081,True),('guicedee-scan','scan',18082,'dedicated'),('persistence/guicedee','spi',0,False)]
for app,mode,port,override in cases:
 label=app.replace('/','-')+('-'+str(override) if override else '')
 jars=[replacement.get(p.name,p) for p in (root/'benchmarks'/app/'target/lib').glob('*.jar')]
 jars.append(root/'benchmarks'/app/'target/classes')
 args=['--module-path',os.pathsep.join(p.as_posix() for p in jars),'--add-modules','ALL-MODULE-PATH','-XX:ActiveProcessorCount=2']
 if override: args+=['-DHTTP_PORT='+str(port),'-DMETRICS_PROMETHEUS_ENDPOINT=/custom-metrics']
 if override=='dedicated': args+=['-DMETRICS_PROMETHEUS_PORT=0']
 args+=[(root/('benchmarks/tools/configuration-smoke/AnnotationRuntimeProbe.java' if port else 'benchmarks/tools/configuration-smoke/AnnotationPersistenceProbe.java')).as_posix(),'persistence' if not port else 'http',mode]
 argfile=output/(label+'.args')
 argfile.write_text('\n'.join('"'+a.replace('"','\\"')+'"' for a in args),encoding='utf-8')
 logpath=output/(label+'.log')
 with tempfile.TemporaryDirectory(prefix='guicedee-annotation-') as temporary:
  # Sentinel entries prevent unrelated parent/classpath dot-env fallback; no application settings.
  for filename in ['.env','.env.local']: (Path(temporary)/filename).write_text('ANNOTATION_SMOKE_SENTINEL=true\n')
  env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','TEMP','TMP'}}
  if port:
   with socket.socket() as s: s.bind(('127.0.0.1',port))
  with logpath.open('w',encoding='utf-8') as log:
   process=subprocess.Popen([str(java),'@'+str(argfile)],cwd=temporary,env=env,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT)
   try:
    deadline=time.monotonic()+45
    while time.monotonic()<deadline:
     if 'ANNOTATION_PROBE_OK' in logpath.read_text(encoding='utf-8',errors='replace'): break
     if process.poll() is not None: raise RuntimeError(f'{label} exited {process.returncode}: {logpath}')
     time.sleep(.2)
    else: raise RuntimeError(f'{label} startup timeout: {logpath}')
    if port:
     for endpoint in ['/ready','/custom-metrics' if override else '/metrics']:
      endpoint_port=port
      if override=='dedicated' and endpoint!='/ready': endpoint_port=int(re.search(r'METRICS_PORT=(\d+)',logpath.read_text(encoding='utf-8',errors='replace'))[1])
      with urllib.request.urlopen(f'http://127.0.0.1:{endpoint_port}{endpoint}',timeout=10) as response:
       assert response.status==200,(label,endpoint,response.status)
       body=response.read()
       if endpoint=='/ready': assert json.loads(body)['ready'] is True
    if port:
     if override=='dedicated':
      try: urllib.request.urlopen(f'http://127.0.0.1:{port}/custom-metrics',timeout=5); raise AssertionError('Dedicated route leaked to application listener')
      except urllib.error.HTTPError as error: assert error.code==404
     process.stdin.write(b'\n');process.stdin.flush()
     process.wait(timeout=20)
     assert 'ANNOTATION_SHUTDOWN_OK' in logpath.read_text(encoding='utf-8',errors='replace')
     if override=='dedicated':
      with socket.socket() as check: assert check.connect_ex(('127.0.0.1',endpoint_port))!=0
    results.append({'app':app,'discovery':mode,'override':override,'passed':True,'validation':'metadata and database defaults' if not port else 'startup, resolved configuration, readiness and metrics'})
    print(label+' PASS',flush=True)
   finally:
    if process.poll() is None: process.terminate()
    try: process.wait(timeout=8)
    except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=5)
(output/'summary.json').write_text(json.dumps(results,indent=2))
