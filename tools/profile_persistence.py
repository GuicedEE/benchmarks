"""Summarize a --diagnostics persistence run; JDK jfr must be on PATH."""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
import re
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sql_delta(before, after):
    previous = {(row['queryid'],row.get('toplevel',True)):row for row in before}
    result = []
    for row in after:
        old = previous.get((row['queryid'],row.get('toplevel',True)), {})
        delta = dict(query=row['query'], queryid=row['queryid'],toplevel=row.get('toplevel',True))
        delta.update({key:row[key]-old.get(key,0) for key in
                      ['calls','plans','total_plan_time','total_exec_time','rows']})
        if delta['calls'] > 0: result.append(delta)
    return sorted(result,key=lambda r:r['total_plan_time']+r['total_exec_time'],reverse=True)


def summarize(events, marks):
    marks = {m['event']:datetime.fromisoformat(m['at']) for m in marks}
    phases = {}
    for phase, start, end in [('startup','launch','first-transaction-complete'),
                               ('warm','warm-measurement-start','measurement-complete')]:
        allocation, samples, allocated_types = Counter(), Counter(), Counter()
        total, count = 0, 0
        for event in events:
            values = event['values']
            at = datetime.fromisoformat(values['startTime'])
            if not marks[start] <= at <= marks[end]: continue
            frames = (values.get('stackTrace') or {}).get('frames', [])
            stack = {f["method"]["type"]["name"].replace('/','.')+'.'+f['method']['name'] for f in frames}
            if event['type'] == 'jdk.ObjectAllocationSample':
                weight = values['weight']; total += weight
                allocated_types[values['objectClass']['name'].replace('/','.')] += weight
                for method in stack: allocation[method] += weight
            elif event['type'] == 'jdk.ExecutionSample':
                count += 1
                for method in stack: samples[method] += 1
        phases[phase] = dict(sampledAllocationBytes=total,executionSamples=count,
            inclusiveAllocationBytes=dict(allocation.most_common(40)),
            inclusiveExecutionSamples=dict(samples.most_common(40)),
            allocatedTypes=dict(allocated_types.most_common(20)),
            focusedAllocationBytes={name:allocation[name] for name in [
                'com.guicedee.client.scopes.mutiny.CallScopeUniInterceptor.existingScoper',
                'com.guicedee.client.scopes.mutiny.CallScopeUniInterceptor$ScopedUniSubscription.<init>',
                'com.guicedee.client.IGuiceContext.loaderToSet',
                'com.guicedee.persistence.implementations.PersistenceDescriptorParser.parse',
                'com.guicedee.modules.services.hibernate.scan.ClassGraphScanner.scan',
                'com.guicedee.modules.services.hibernate.scan.ExplicitPersistenceScanner.scan',
                'org.hibernate.bytecode.internal.bytebuddy.BytecodeProviderImpl.getReflectionOptimizer',
                'org.hibernate.bytecode.internal.bytebuddy.BytecodeProviderImpl.<init>',
                'org.hibernate.jpa.boot.spi.PersistenceXmlParser.loadUrlWithJaxb',
                'org.hibernate.boot.model.process.spi.MetadataBuildingProcess.complete',
                'org.hibernate.boot.internal.BootstrapContextImpl.createModelBuildingContext',
                'org.hibernate.models.CompleteAnnotationDescriptor.<init>',
                'org.hibernate.models.CompleteAnnotationDescriptor.getAttributes',
                'org.hibernate.models.internal.AnnotationDescriptorBuilding.extractAttributeDescriptors',
                'org.hibernate.boot.model.source.internal.hbm.ModelBinder.prepare',
                'org.hibernate.internal.SessionFactoryImpl.<init>',
                'org.hibernate.metamodel.model.domain.internal.MappingMetamodelImpl.finishInitialization',
                'org.hibernate.query.internal.QueryEngineImpl.<init>',
                'org.hibernate.metamodel.internal.EntityInstantiatorPojoStandard.instantiate',
                'org.hibernate.metamodel.internal.GuiceEntityProvider.get',
                'com.guicedee.client.scopes.mutiny.CallScopeUniInterceptor.captureCallScope',
                'com.guicedee.rest.pathing.OperationRegistry.handleRequest',
                'org.hibernate.query.sqm.tree.select.SqmQuerySpec.containsCollectionFetches',
                'org.hibernate.reactive.util.async.impl.AsyncTrampoline$TrampolineInternal.unroll']})
        phases[phase]['focusedExecutionSamples'] = {name:samples[name] for name in [
            'java.lang.ClassLoader.loadClass',
            'org.hibernate.boot.internal.BootstrapContextImpl.createModelBuildingContext',
            'org.hibernate.models.internal.AnnotationDescriptorBuilding.extractAttributeDescriptors',
            'org.hibernate.boot.model.process.spi.MetadataBuildingProcess.complete',
            'org.hibernate.internal.SessionFactoryImpl.<init>',
            'org.hibernate.metamodel.model.domain.internal.MappingMetamodelImpl.finishInitialization',
            'org.hibernate.query.internal.QueryEngineImpl.<init>',
            'org.hibernate.query.hql.internal.StandardHqlTranslator.translate',
            'org.hibernate.metamodel.internal.GuiceEntityProvider.get',
            'com.guicedee.client.scopes.mutiny.CallScopeUniInterceptor.captureCallScope',
            'com.guicedee.rest.pathing.OperationRegistry.handleRequest',
            'org.hibernate.reactive.util.async.impl.AsyncTrampoline$TrampolineInternal.unroll']}
    return phases


def render(report):
    text = ['# Current persistence profile', '',
            f"Diagnostic batch `{report['batch']}`; {report['requests']} measured reads and CRUD cycles per application.", '',
            '**Instrumented diagnostics, not benchmark timings.** Use [RESULTS.md](../RESULTS.md) for the uninstrumented comparison.', '',
            report['limitations'], '']
    if report.get('jvmFlags'):
        text += ['JVM flags: '+', '.join(f'`{flag}`' for flag in report['jvmFlags'])+'.', '']
    text += ['| Application | Startup sampled allocation (MiB) | Warm sampled allocation (MiB) | Warm SQL calls | Of which transaction control | Warm SQL planning (ms) | Warm SQL execution (ms) |',
             '|---|---:|---:|---:|---:|---:|---:|']
    for row in report['starts']:
        sql = [q for q in row['warmSql'] if q['toplevel']]
        transaction_calls = sum(q['calls'] for q in sql
                                if re.match(r'^(BEGIN|COMMIT|ROLLBACK|SAVEPOINT|RELEASE)\b', q['query'].strip(), re.I))
        text.append(f"| {row['variant']} | {row['phases']['startup']['sampledAllocationBytes']/2**20:.2f} | "
                    f"{row['phases']['warm']['sampledAllocationBytes']/2**20:.2f} | {sum(q['calls'] for q in sql)} | {transaction_calls} | "
                    f"{sum(q['total_plan_time'] for q in sql):.2f} | {sum(q['total_exec_time'] for q in sql):.2f} |")
    text += ['', 'Startup includes the first completed business transaction. Warm allocation covers the entire measured interval, '
             'not one request or retained memory. SQL times are database execution/planning totals and exclude application '
             'work, transport and CPU-quota waits. The table counts top-level SQL only; nested foreign-key checks '
             'are retained in the JSON and excluded from these totals to avoid double-counting execution time. '
             'They are not end-to-end transaction latency. Driver protocols can produce different transaction-control '
             'counters, including whether COMMIT appears as a separate statement. These counts do not imply omitted '
             'commits; the independent database checks verify committed visibility and rollback for every application.', '',
             '## GuicedEE startup phases', '', 'Inclusive phase timings overlap and cannot be added.', '',
             '| Phase | Instrumented duration (ms) |', '|---|---:|']
    for row in report['starts']:
        for name,elapsed in row.get('guicedeePhasesMs', {}).items():
            if name in ['application-startup','context-discovery','pre-startup','guice-module-discovery','guice-create-injector',
                        'post-startup','post-hook-complete:com.guicedee.persistence.PersistenceStartup']:
                text.append(f'| {name} | {elapsed:.2f} |')
        for phase in row.get('persistenceBootstrap', []):
            text.append(f"| persistence {phase['phase']} ({phase['unit']}) | {phase['durationMs']:.2f} |")
    for row in report['starts']:
        if row['variant'] != 'guicedee': continue
        phases = {p['phase']:p['durationMs'] for p in row.get('persistenceBootstrap', [])}
        required = ['persistence-xml','discovery-scan','metadata-bootstrap','mapping-model','session-factory']
        if all(name in phases for name in required):
            text += ['', f"The current instrumented sample records **{phases['persistence-xml']:.2f} ms** for descriptor parsing "
                f"and **{phases['discovery-scan']:.2f} ms** for persistence discovery. Metadata bootstrap "
                f"(**{phases['metadata-bootstrap']/1000:.3f} s**) and session-factory creation "
                f"(**{phases['session-factory']/1000:.3f} s**) are the largest recorded persistence phases; "
                f"mapping-model construction takes **{phases['mapping-model']/1000:.3f} s**. "
                'Discovery is nested within metadata bootstrap. These inclusive values must not be summed.', '']
    if report.get('parserControlBootstrap'):
        text += ['', '## Secured Hibernate parser control', '',
                 'Same application image, forced Hibernate descriptor parsing with security checks enabled. '
                 'These additional instrumented starts are separate from the default-parser profile and runtime rankings. '
                 'Inclusive phases overlap; a single diagnostic start is not a timing comparison.', '',
                 '| Start | Phase | Instrumented duration (ms) |', '|---|---|---:|']
        for row in report['parserControlBootstrap']:
            for phase in row['phases']:
                text.append(f"| {row['run']} | {phase['phase']} ({phase['unit']}) | {phase['durationMs']:.2f} |")
    if all('startupSql' in row for row in report['starts']):
        text += ['', '## Startup database work', '',
                 'SQL counters cover application launch through the first committed graph, excluding schema preparation. '
                 'Database execution time excludes transport, application work and CPU-quota waits.', '',
                 '| Application | SQL calls | Database execution (ms) |', '|---|---:|---:|']
        for row in report['starts']:
            sql = [q for q in row['startupSql'] if q['toplevel']]
            text.append(f"| {row['variant']} | {sum(q['calls'] for q in sql)} | {sum(q['total_exec_time'] for q in sql):.2f} |")
    for row in report['starts']:
        if row['variant'] != 'guicedee' or 'focusedExecutionSamples' not in row['phases']['startup']: continue
        text += ['', '## GuicedEE execution sample locations', '',
                 f"The recording contains {row['phases']['startup']['executionSamples']} startup and "
                 f"{row['phases']['warm']['executionSamples']} warm execution samples. "
                 'Counts below include any sample containing the method on its stack. '
                 'Stacks overlap; counts are not elapsed phase times or additive percentages. '
                 'Zero means that this recording did not sample the method.', '',
                 '| Stack location | Startup samples | Warm samples |', '|---|---:|---:|']
        for name,count in row['phases']['startup']['focusedExecutionSamples'].items():
            text.append(f"| `{name}` | {count} | {row['phases']['warm']['focusedExecutionSamples'][name]} |")
    text += ['', '## Focused allocation samples', '',
             'These inclusive stack estimates locate work; zero means no allocation sample observed on that stack.', '',
             '| GuicedEE stack | Startup (MiB) | Warm (MiB) |', '|---|---:|---:|']
    for row in report['starts']:
        if row['variant'] != 'guicedee': continue
        for name,allocated in row['phases']['startup']['focusedAllocationBytes'].items():
            text.append(f"| `{name}` | {allocated/2**20:.2f} | {row['phases']['warm']['focusedAllocationBytes'][name]/2**20:.2f} |")
    text += ['', '[Machine-readable profile](persistence-profile.json) includes SQL statements, sample counts and JFR hashes. '
             '[Reproduce](../persistence/README.md#profile-startup-and-crud) with the same immutable application images. '
             'Full JFR recordings remain in ignored `target/`. Only this current diagnostic summary is published.', '']
    return '\n'.join(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--publish',action='store_true',help='Replace the current diagnostic report after checking it matches published benchmark images')
    args = parser.parse_args()
    data = json.loads((args.directory/'summary.json').read_text())
    if not data.get('instrumented') or data.get('eligible'):
        parser.error('Expected an instrumented, publication-ineligible run')
    if len(data['starts']) != len(data['images'])*data['runs'] or any(not row['eligible'] for row in data['starts']):
        parser.error('Diagnostic summary requires complete, passing application starts')
    report = dict(instrumented=True, performanceComparison=False,batch=data['batch'],measuredAt=data['measuredAt'],
        requests=data['requests'],warmup=data['warmup'],images=data['images'],runnerSha256=data['runnerSha256'],
        jvmFlags=data['jvmFlags'],
        profilerSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        limitations='JFR allocation weights are estimates; inclusive stacks overlap. Execution samples '
                    'exclude native wait samples and do not measure elapsed phase time. '
                    'Instrumentation changes timings. SQL statistics describe database work only.',
        starts=[])
    for path in sorted(args.directory.glob('*.profile.json')):
        details = json.loads(path.read_text())
        prefix = f'{details["variant"]}-{details["run"]}'
        jfr = args.directory/f'{prefix}.jfr'
        exported = args.directory/f'{prefix}.jfr.json'
        with exported.open('w',encoding='utf-8') as stream:
            subprocess.run(['jfr','print','--json','--stack-depth','64','--events',
                            'jdk.ExecutionSample,jdk.ObjectAllocationSample',str(jfr)],stdout=stream,check=True)
        events = json.loads(exported.read_text(encoding='utf-8'))['recording']['events']
        row = dict(variant=details['variant'],run=details['run'],
            jfrSha256=hashlib.sha256(jfr.read_bytes()).hexdigest(),
            phases=summarize(events,details['marks']),
            warmSql=sql_delta(details['sql']['warm-measurement-start'],details['sql']['measurement-complete']))
        if 'launch' in details['sql']:
            row['startupSql'] = sql_delta(details['sql']['launch'], details['sql']['first-transaction-complete'])
        startup = args.directory/f'{prefix}.startup.json'
        if startup.exists():
            row['guicedeePhasesMs'] = {e['phase']:e['durationNs']/1e6 for e in json.loads(startup.read_text())['events']
                                       if not e['phase'].startswith('provision:')}
            row['persistenceBootstrap'] = [dict(phase=phase,unit=unit,durationMs=int(nanos)/1e6,success=success=='true')
                for phase,unit,nanos,success in re.findall(
                    r'\[PERSISTENCE-PHASE\] phase=(\S+) unit=(.*?) durationNs=(\d+) success=(true|false)',
                    (args.directory/f'{prefix}.log').read_text(encoding='utf-8'))]
        report['starts'].append(row)
    if len(report['starts']) != len(data['starts']): parser.error('Missing diagnostic recordings')
    if 'parserControl' in data:
        report['parserControlBootstrap'] = []
        control = data['parserControl']
        if control['identicalApplicationImage'] != data['images']['guicedee']:
            parser.error('Parser diagnostic control must use the same image')
        for row in control['starts']:
            if not row['eligible'] or not all(row['checks'].values()):
                parser.error('Parser diagnostic control failed')
            log = args.directory/'parser-control'/f"guicedee-{row['run']}.log"
            phases = [dict(phase=phase,unit=unit,durationMs=int(nanos)/1e6,success=success=='true')
                for phase,unit,nanos,success in re.findall(
                    r'\[PERSISTENCE-PHASE\] phase=(\S+) unit=(.*?) durationNs=(\d+) success=(true|false)',
                    log.read_text(encoding='utf-8'))]
            if not phases or not all(p['success'] for p in phases):
                parser.error('Missing or failed parser control phases')
            report['parserControlBootstrap'].append(dict(run=row['run'],image=row['image'],
                environmentOverride=control['environmentOverride'],phases=phases))
    destination = args.directory/'profile-summary.json'
    destination.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    if args.publish:
        current=json.loads((ROOT/'results/latest/persistence.json').read_text())
        if current['images'] != data['images'] or current['buildInputs'] != data['buildInputs']:
            parser.error('Diagnostic and published performance runs must use the same application builds')
        (ROOT/'docs/persistence-profile.json').write_text(destination.read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
        (ROOT/'docs/PERSISTENCE_PROFILE.md').write_text(render(report),encoding='utf-8',newline='\n')
    print(destination)


if __name__ == '__main__': main()
