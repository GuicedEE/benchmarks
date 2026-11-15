"""Measure complete PostgreSQL transactions after strict, independent database checks.

Only containers, network and volume created by this invocation are removed. Every
fresh application start uses a newly created database with the same shared schema.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import re
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from compare import port, percentile
from persistence_diagnostics import PersistenceDiagnostics, JFR_FLAG, PG_FLAGS

ROOT = Path(__file__).resolve().parents[1]
ENTITIES = ['Country','Region','Address','Customer','Supplier','Category','Product','Warehouse',
            'Inventory','PurchaseOrder','OrderLine','Payment','Shipment','ShipmentItem','AuditEntry']
TABLES = ['bench_'+re.sub(r'(?<!^)(?=[A-Z])','_',name).lower() for name in ENTITIES]
VARIANTS = ['guicedee','quarkus']
FLAGS = ['-Xms128m','-Xmx384m','-XX:ActiveProcessorCount=2','-Dlog4j.shutdownHookEnabled=false']
CONTRACT = '15-entity-projection-read-stateless-write-enhanced-v2'
CHECKS = {'readinessAndTransactionMode','schemaAndRelationships','createGraph','committedFifteenRows',
          'joinedRead','updatesAndVersions','rollbackAfterFifteenInserts','rollbackInvisibleToNewTransaction',
          'duplicateKeyPreservesCommittedGraph','concurrentIndependentTransactions','foreignKeyEnforced',
          'deleteGraphInDependencyOrder','measuredResponsesAndNoRowLeaks','gracefulLifecycleShutdown'}


def docker(*args, input=None, check=True):
    return subprocess.run(['docker',*map(str,args)], input=input, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)


def expected(identifier, updated=False):
    return dict(id=identifier, entities={name:f'{name}:{identifier}'+(':updated' if updated else '') for name in ENTITIES},
                versions={name:int(updated) for name in ENTITIES})


def request(base, method, path):
    started = time.perf_counter()
    req = urllib.request.Request(base+path, method=method, data=b'' if method == 'POST' else None)
    try:
        response = urllib.request.urlopen(req, timeout=120)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        status, body = response.status, json.loads(response.read())
    return status, body, (time.perf_counter()-started)*1000


def expect(base, method, path, body, status=200):
    actual, payload, elapsed = request(base, method, path)
    if (actual,payload) != (status,body):
        raise ValueError(f'{method} {path}: expected {status} {body}, received {actual} {payload}')
    return elapsed


def psql(container, query, database='postgres', check=True):
    return docker('exec','-i',container,'psql','-X','-qAt','-v','ON_ERROR_STOP=1',
                  '-U','bench','-d',database, input=query, check=check)


def db_snapshot(container, database, identifier):
    query = ' union all '.join(f"select '{name}',label,version,(to_jsonb(t)-'label'-'version'-'id')::text from {table} t where id={int(identifier)}"
                              for name,table in zip(ENTITIES,TABLES))+';'
    rows = [line.split('|',3) for line in psql(container,query,database).stdout.splitlines() if line]
    return {name:dict(label=label, version=int(version), foreignKeys=json.loads(links)) for name,label,version,links in rows}


def check_database(container, database, identifier, updated=False, absent=False):
    actual = db_snapshot(container,database,identifier)
    schema = (ROOT/'persistence/schema.sql').read_text()
    links = {table:re.findall(r'(\w+_id) bigint not null references',definition)
             for table,definition in re.findall(r'create table (\w+) \((.*?)\);',schema,re.S)}
    wanted = {} if absent else {name:dict(label=f'{name}:{identifier}'+(':updated' if updated else ''),
        version=int(updated),foreignKeys={key:identifier for key in links[table]}) for name,table in zip(ENTITIES,TABLES)}
    if actual != wanted: raise ValueError(f'Independent PostgreSQL verification failed: {actual}')
    return actual


def cycle(base, identifier):
    started = time.perf_counter()
    samples = dict(createMs=expect(base,'POST',f'/graphs/{identifier}',expected(identifier)),
                   readMs=expect(base,'GET',f'/graphs/{identifier}',expected(identifier)),
                   updateMs=expect(base,'POST',f'/graphs/{identifier}/update',expected(identifier,True)),
                   deleteMs=expect(base,'DELETE',f'/graphs/{identifier}',dict(deleted=15,id=identifier)))
    samples['cycleMs'] = (time.perf_counter()-started)*1000
    return samples


def validate(data):
    if data.get('instrumented') or any('StartFlightRecording' in flag for flag in data.get('jvmFlags', [])):
        raise ValueError('Instrumented persistence diagnostics cannot be published as performance measurements')
    if data.get('contract') != CONTRACT:
        raise ValueError('Persistence evidence does not describe the current projection/transaction contract')
    rows = data['starts']
    if not data.get('eligible') or len(rows) != 2*data['runs']:
        raise ValueError('Persistence publication requires the complete passing matrix')
    if {(r['variant'],r['run']) for r in rows} != {(v,n) for v in VARIANTS for n in range(1,data['runs']+1)}:
        raise ValueError('Missing or duplicate persistence starts')
    for row in rows:
        if (not row['eligible'] or set(row['checks']) != CHECKS or not all(row['checks'].values())
                or len(row['readsMs']) != data['requests'] or len(row['cycles']) != data['requests']
                or row['image'] != data['images'][row['variant']] or row['jvmFlags'] != data['jvmFlags']
                or row['containerLimits'] != dict(nanoCpus=250000000,memoryBytes=500*2**20,memorySwapBytes=500*2**20)
                or row['oomKilled'] or 'oom_kill 0' not in row['memoryEvents'].splitlines()):
            raise ValueError('Incomplete, unequal or failed persistence start')
        shutdown = row.get('shutdown', {})
        if (shutdown.get('exitCode') not in [0,143] or shutdown.get('remainingConnections') != 0
                or not shutdown.get('lifecycleCompleted')):
            raise ValueError('Persistence shutdown evidence is incomplete or failed')
        values = row['readsMs']+[c[k] for c in row['cycles'] for k in ['createMs','readMs','updateMs','deleteMs','cycleMs']]
        if any(not math.isfinite(v) or v <= 0 for v in values): raise ValueError('Invalid persistence latency')
    inputs = data['buildInputs']
    if inputs['guicedee']['sources'] != inputs['quarkus']['sources'] or inputs['guicedee']['javaImage'] != inputs['quarkus']['javaImage']:
        raise ValueError('Persistence variants must share the source contract and JDK base')
    model = inputs['guicedee'].get('modelArtifacts', {})
    if len(model) != 2 or model != inputs['quarkus'].get('modelArtifacts'):
        raise ValueError('Persistence applications must use the same compiled source model and enhancement build')
    for variant in VARIANTS:
        expected_model = {name:digest for name,digest in model.items() if name.endswith('-enhanced.jar') == (variant=='guicedee')}
        packaged_model = {Path(path).name.removeprefix('dev.guicedee.benchmarks.'):digest
                          for path,digest in inputs[variant]['jarSha256'].items() if 'persistence-model-' in path}
        if len(expected_model) != 1 or packaged_model != expected_model:
            raise ValueError('Incorrect shared entity model artifact for framework enhancement')
    settings=data['postgres']['settings']
    if any(settings[key] != 'on' for key in ['fsync','synchronous_commit','full_page_writes']) or settings['isolation'] != 'read committed':
        raise ValueError('Persistence comparison requires durable READ COMMITTED transactions')


def run_start(args, data, output, db, network, variant, run):
    database = f'bench_{variant}_{run}'
    psql(db,f'create database {database};')
    psql(db,(ROOT/'persistence/schema.sql').read_text(),database)
    if args.diagnostics: psql(db,'create extension pg_stat_statements;',database)
    # Confirm Hibernate is using fifteen relational tables and all nineteen declared FKs.
    counts = psql(db,"select count(*) from pg_tables where schemaname='public' and tablename like 'bench_%'; "
                     "select count(*) from pg_constraint where contype='f';",database).stdout.splitlines()
    if counts != ['15','19']: raise ValueError(f'Unexpected schema inventory: {counts}')
    app = f'{network}-{variant}-{run}'
    http_port = port()
    base = f'http://127.0.0.1:{http_port}'
    row = dict(variant=variant,run=run,image=data['images'][variant],jvmFlags=data['jvmFlags'],
               eligible=False,checks={},readsMs=[],cycles=[])
    data['starts'].append(row)
    diagnostics = PersistenceDiagnostics(output,variant,run,app,db,database,docker,psql) if args.diagnostics else None
    if diagnostics: diagnostics.mark('launch')
    started = time.perf_counter()
    try:
        docker('run','-d','--name',app,'--network',network,'--cpus','0.25','--memory','500m','--memory-swap','500m',
               '-p',f'127.0.0.1:{http_port}:8080','-e','DB_HOST=postgres','-e',f'DB_NAME={database}',
               '-e','DB_USER=bench','-e','DB_PASSWORD=bench','-e','JAVA_TOOL_OPTIONS='+' '.join(data['jvmFlags']),
               *(['-e','GUICEDEE_DIAGNOSTICS_DIR=/tmp/diagnostics'] if diagnostics and variant=='guicedee' else []),data['images'][variant])
        deadline = time.monotonic()+240
        ready = None
        while time.monotonic() < deadline:
            try:
                code, body, _ = request(base,'GET','/ready')
                if code == 200 and body.get('ready'):
                    ready = body; break
            except (OSError,ValueError): pass
            state = json.loads(docker('inspect',app).stdout)[0]['State']
            if not state['Running']: raise ValueError(f'{variant} exited before database readiness: {state}')
            time.sleep(.1)
        if ready is None: raise TimeoutError(f'{variant} did not reach database readiness')
        row['launchToReadyMs'] = (time.perf_counter()-started)*1000
        if diagnostics: diagnostics.mark('ready')
        row['readiness'] = ready
        mode = 'hibernate-reactive-stateless' if variant == 'guicedee' else 'narayana-jta'
        if ready['entities'] != 15 or ready['transactionMode'] != mode: raise ValueError(f'Incorrect persistence wiring: {ready}')
        row['checks']['readinessAndTransactionMode'] = True
        row['checks']['schemaAndRelationships'] = True
        row['firstTransactionMs'] = expect(base,'POST','/graphs/1',expected(1))
        row['launchToFirstTransactionMs'] = (time.perf_counter()-started)*1000
        if diagnostics: diagnostics.mark('first-transaction-complete',sql=True)
        row['checks']['createGraph'] = True
        row['databaseEvidence'] = dict(committed=check_database(db,database,1))
        row['checks']['committedFifteenRows'] = True
        expect(base,'GET','/graphs/1',expected(1))
        row['checks']['joinedRead'] = True
        expect(base,'POST','/graphs/1/update',expected(1,True))
        row['databaseEvidence']['updated'] = check_database(db,database,1,updated=True)
        row['checks']['updatesAndVersions'] = True
        expect(base,'POST','/graphs/2/rollback',dict(error='ROLLBACK_PROBE'),409)
        row['databaseEvidence']['rolledBack'] = check_database(db,database,2,absent=True)
        row['checks']['rollbackAfterFifteenInserts'] = True
        expect(base,'GET','/graphs/2',dict(error='NOT_FOUND'),404)
        row['checks']['rollbackInvisibleToNewTransaction'] = True
        expect(base,'POST','/graphs/1',dict(error='DATABASE_FAILURE'),500)
        check_database(db,database,1,updated=True)
        row['checks']['duplicateKeyPreservesCommittedGraph'] = True
        with ThreadPoolExecutor(max_workers=2) as executor:
            list(executor.map(lambda n: expect(base,'POST',f'/graphs/{n}',expected(n)),[3,4]))
        for n in [3,4]: check_database(db,database,n)
        row['checks']['concurrentIndependentTransactions'] = True
        violation = psql(db,"insert into bench_region(id,label,version,country_id) values(9,'orphan',0,999999);",database,check=False)
        if violation.returncode == 0 or 'foreign key constraint' not in violation.stderr: raise ValueError('PostgreSQL did not enforce FK constraints')
        row['checks']['foreignKeyEnforced'] = True
        for n in [1,3,4]:
            expect(base,'DELETE',f'/graphs/{n}',dict(deleted=15,id=n))
            check_database(db,database,n,absent=True)
        row['checks']['deleteGraphInDependencyOrder'] = True
        expect(base,'POST','/graphs/10',expected(10))
        for n in range(args.warmup):
            expect(base,'GET','/graphs/10',expected(10)); cycle(base,100+n)
        if diagnostics: diagnostics.mark('warm-measurement-start',sql=True)
        for n in range(args.requests):
            row['readsMs'].append(expect(base,'GET','/graphs/10',expected(10)))
            row['cycles'].append(cycle(base,10000+n))
        if diagnostics: diagnostics.mark('measurement-complete',sql=True)
        check_database(db,database,10)
        remaining = psql(db,'select '+ ' + '.join(f'(select count(*) from {t})' for t in TABLES)+';',database).stdout.strip()
        if remaining != '15': raise ValueError(f'Rows leaked from completed CRUD cycles: {remaining}')
        row['checks']['measuredResponsesAndNoRowLeaks'] = True
        inspect = json.loads(docker('inspect',app).stdout)[0]
        host = inspect['HostConfig']
        row['containerLimits'] = dict(nanoCpus=host['NanoCpus'],memoryBytes=host['Memory'],memorySwapBytes=host['MemorySwap'])
        row['oomKilled'] = inspect['State']['OOMKilled']
        row['peakMemoryBytes'] = int(docker('exec',app,'cat','/sys/fs/cgroup/memory.peak').stdout)
        row['endMemoryBytes'] = int(docker('exec',app,'cat','/sys/fs/cgroup/memory.current').stdout)
        row['memoryEvents'] = docker('exec',app,'cat','/sys/fs/cgroup/memory.events').stdout
        row['cpuStat'] = docker('exec',app,'cat','/sys/fs/cgroup/cpu.stat').stdout
        # Shutdown is outside the timing/memory samples. Verify lifecycle ownership
        # instead of hiding a missing cleanup hook behind a forced container kill.
        docker('stop','--time','45',app)
        if diagnostics: diagnostics.collect()
        stopped = json.loads(docker('inspect',app).stdout)[0]['State']
        logs = docker('logs',app)
        connections = int(psql(db,f"select count(*) from pg_stat_activity where datname='{database}' and backend_type='client backend';").stdout)
        shutdown_log = logs.stdout+logs.stderr
        completed = ('Guice Context shutdown completed' in shutdown_log
                     and re.search(r'Pre-destroy services execution completed - Success: \d+, Failed: 0', shutdown_log)) if variant=='guicedee' else 'stopped in' in shutdown_log
        row['shutdown'] = dict(exitCode=stopped['ExitCode'],remainingConnections=connections,lifecycleCompleted=bool(completed))
        if stopped['ExitCode'] not in [0,143] or connections != 0 or not row['shutdown']['lifecycleCompleted']:
            raise ValueError(f'Persistence lifecycle did not shut down cleanly: {row["shutdown"]}')
        row['checks']['gracefulLifecycleShutdown'] = True
        row['eligible'] = True
        print(f'{variant} #{run}: full transaction {row["launchToFirstTransactionMs"]:.0f} ms; '
              f'warm read p50 {percentile(row["readsMs"],.5):.2f} ms; {len(CHECKS)} checks passed',flush=True)
    finally:
        log = docker('logs',app,check=False)
        content = log.stdout+log.stderr
        (output/f'{variant}-{run}.log').write_text(content,encoding='utf-8')
        row['logSha256'] = hashlib.sha256(content.encode()).hexdigest()
        docker('rm','-f',app,check=False)
        psql(db,f'drop database {database} with (force);',check=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs',type=int,default=3)
    parser.add_argument('--requests',type=int,default=30)
    parser.add_argument('--warmup',type=int,default=10)
    parser.add_argument('--image-tag',default='local')
    parser.add_argument('--postgres-image',default='postgres:17')
    parser.add_argument('--tiered',action='store_true',help='Apply equal C1 tuning to both JVMs')
    parser.add_argument('--diagnostics',action='store_true',help='Record JFR, GuicedEE phases and PostgreSQL query/plan statistics; ineligible for publication')
    args = parser.parse_args()
    if min(args.runs,args.requests)<1 or args.warmup<0: parser.error('Invalid sample counts')
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    output = ROOT/f'target/persistence-runs/{timestamp}'
    output.mkdir(parents=True)
    network = 'guicedee-persistence-'+uuid.uuid4().hex[:12]
    db,volume = network+'-db',network+'-data'
    data = dict(schemaVersion=1,contract=CONTRACT,measuredAt=datetime.now(timezone.utc).isoformat(),batch=timestamp,
        runs=args.runs,requests=args.requests,warmup=args.warmup,host=platform.platform(),
        profile='c1' if args.tiered else 'default', instrumented=args.diagnostics,
        jvmFlags=FLAGS+(['-XX:TieredStopAtLevel=1'] if args.tiered else [])+([JFR_FLAG] if args.diagnostics else []),
        protocol='Fresh JVM and database per start; sequential alternating variants; shared schema outside timing; '
                 'first business response includes 15 inserts, joined read and completed commit; '
                 'warm workload interleaves joined scalar-projection reads without explicit transactions with '
                 'create/read/update/delete cycles (three write transactions and one read); no L2 cache or JDBC batching.',
        images={},buildInputs={},starts=[],eligible=False,python=platform.python_version(),
        runnerSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),runtimeJava={})
    for variant in VARIANTS:
        data['images'][variant] = json.loads(docker('image','inspect',f'guicedee-bench-persistence-{variant}:{args.image_tag}').stdout)[0]['Id']
        data['buildInputs'][variant] = json.loads(docker('run','--rm','--entrypoint','cat',data['images'][variant],'/app/benchmark-inputs.json').stdout)
        java = docker('run','--rm','--entrypoint','java',data['images'][variant],'-version')
        data['runtimeJava'][variant] = java.stdout+java.stderr
    docker('pull',args.postgres_image)
    pg = json.loads(docker('image','inspect',args.postgres_image).stdout)[0]
    data['postgres'] = dict(image=pg['Id'],repoDigests=pg['RepoDigests'],cpuLimit=2,memoryBytes=1024*2**20)
    try:
        docker('network','create',network)
        docker('volume','create',volume)
        docker('run','-d','--name',db,'--network',network,'--network-alias','postgres','--cpus','2',
               '--memory','1g','--memory-swap','1g','--shm-size','256m','-v',f'{volume}:/var/lib/postgresql/data',
               '-e','POSTGRES_USER=bench','-e','POSTGRES_PASSWORD=bench',pg['Id'],
               '-c','shared_buffers=128MB','-c','max_connections=40','-c','fsync=on','-c','synchronous_commit=on',
               *(PG_FLAGS if args.diagnostics else []))
        for _ in range(120):
            if docker('exec',db,'pg_isready','-h','127.0.0.1','-U','bench',check=False).returncode == 0: break
            time.sleep(.5)
        else: raise TimeoutError('PostgreSQL did not become ready')
        data['postgres']['settings'] = json.loads(psql(db,"select json_build_object('version',version(),"
            "'fsync',current_setting('fsync'),'synchronous_commit',current_setting('synchronous_commit'),"
            "'full_page_writes',current_setting('full_page_writes'),'isolation',current_setting('default_transaction_isolation'));").stdout)
        for run in range(1,args.runs+1):
            for variant in VARIANTS if run % 2 else list(reversed(VARIANTS)):
                run_start(args,data,output,db,network,variant,run)
        data['eligible'] = not args.diagnostics
        if args.diagnostics: print('Instrumented diagnostics only; performance publication is disabled.',flush=True)
        else: validate(data)
    finally:
        (output/'summary.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
        print('Evidence:',output,flush=True)
        docker('rm','-f',db,check=False)
        docker('volume','rm',volume,check=False)
        docker('network','rm',network,check=False)


if __name__ == '__main__':
    main()
