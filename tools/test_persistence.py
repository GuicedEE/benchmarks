import copy
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from compare_persistence import CHECKS, CONTRACT, validate, check_database
from profile_persistence import sql_delta, summarize
from compare_persistence_parser import parser_command
from render_persistence import collect as collect_report


class ParserControlTest(unittest.TestCase):
    def test_report_rejects_incomplete_or_unmatched_parser_controls(self):
        data = complete()
        data.update(measuredAt='2026-11-16',batch='test',profile='default',warmup=0)
        for row in data['starts']:
            row.update(readiness={'ormVersion':'test'},launchToReadyMs=1,firstTransactionMs=1,
                       launchToFirstTransactionMs=2,peakMemoryBytes=3,endMemoryBytes=2)
        control = dict(data['starts'][0],run=101)
        data['parserControl'] = dict(environmentOverride={'GUICEDEE_PERSISTENCE_XML_PARSER':'hibernate'},
            descriptorSecurityChecks=True,identicalApplicationImage='guicedee',starts=[control],scope='test')
        self.assertEqual(1,collect_report(data)['parserControl']['starts'])
        for change in [dict(starts=[]),dict(starts=[dict(control,image='different-image')]),
                       dict(descriptorSecurityChecks=False),dict(identicalApplicationImage='other')]:
            bad = copy.deepcopy(data)
            bad['parserControl'].update(change)
            with self.assertRaises(ValueError): collect_report(bad)

    def test_only_guicedee_application_launch_receives_override(self):
        base = ['run', '-d', '--name', 'network-guicedee-101', '-e', 'DB_HOST=postgres', 'sha256:image']
        self.assertEqual(base[:-1] + ['-e', 'GUICEDEE_PERSISTENCE_XML_PARSER=hibernate', base[-1]], parser_command(base))
        for name in ['network-db', 'network-quarkus-1', 'network-micronaut-1']:
            command = ['run', '-d', '--name', name, 'sha256:image']
            self.assertEqual(command, parser_command(command))
        self.assertEqual(['run', '--rm', '--entrypoint', 'cat', 'image'],
                         parser_command(['run', '--rm', '--entrypoint', 'cat', 'image']))


def complete():
    rows=[]
    for variant in ['guicedee','quarkus','micronaut']:
        rows.append(dict(variant=variant,run=1,eligible=True,checks=dict.fromkeys(CHECKS,True),
            readsMs=[1.0],cycles=[dict.fromkeys(['createMs','readMs','updateMs','deleteMs','cycleMs'],2.0)],
            image=variant,jvmFlags=['same'],oomKilled=False,memoryEvents='oom_kill 0\n',
            shutdown=dict(exitCode=143,remainingConnections=0,lifecycleCompleted=True),
            containerLimits=dict(nanoCpus=250000000,memoryBytes=500*2**20,memorySwapBytes=500*2**20)))
    return dict(eligible=True,contract=CONTRACT,runs=1,requests=1,starts=rows,jvmFlags=['same'],
        images={n:n for n in ['guicedee','quarkus','micronaut']},
        buildInputs={n:dict(sources={'model.java':'same'},javaImage='same-jdk',
                           modelArtifacts={'persistence-model-1.0-SNAPSHOT.jar':'original','persistence-model-1.0-SNAPSHOT-enhanced.jar':'enhanced'},
                           jarSha256={('lib/'+('' if n=='guicedee' else 'dev.guicedee.benchmarks.')+'persistence-model-1.0-SNAPSHOT'+('-enhanced' if n=='guicedee' else '')+'.jar'):
                                      'enhanced' if n=='guicedee' else 'original'}) for n in ['guicedee','quarkus','micronaut']},
        postgres=dict(settings=dict(fsync='on',synchronous_commit='on',full_page_writes='on',isolation='read committed')))


class PersistenceTest(unittest.TestCase):
    def test_sql_profile_subtracts_warmup_and_keeps_new_statements(self):
        query=dict(queryid='1',query='select label',calls=10,plans=6,total_plan_time=3,total_exec_time=5,rows=10)
        after=dict(query,calls=14,total_exec_time=7,rows=14)
        new=dict(query,queryid='2',query='update label',calls=2,rows=2)
        rows={r['queryid']:r for r in sql_delta([query],[after,new])}
        self.assertEqual((rows['1']['calls'],rows['1']['plans'],rows['1']['total_exec_time']),(4,0,2))
        self.assertEqual(rows['2']['calls'],2)
        nested_before=dict(query,toplevel=False,calls=30)
        nested_after=dict(nested_before,calls=36)
        split={(r['queryid'],r['toplevel']):r['calls'] for r in sql_delta([query,nested_before],[after,nested_after])}
        self.assertEqual(split,{('1',True):4,('1',False):6})

    def test_jfr_profile_separates_intervals_and_does_not_count_wait_samples(self):
        marks=[dict(event=name,at=f'2026-11-15T00:00:0{n}+00:00') for n,name in
               [(0,'launch'),(2,'first-transaction-complete'),(4,'warm-measurement-start'),(6,'measurement-complete')]]
        frame=dict(method=dict(type=dict(name='example/Work'),name='run'))
        allocation=dict(startTime='2026-11-15T00:00:05Z',weight=100,objectClass=dict(name='byte[]'),
                        stackTrace=dict(frames=[frame,frame]))
        events=[dict(type='jdk.ObjectAllocationSample',values=allocation),
                dict(type='jdk.ObjectAllocationSample',values=dict(allocation,startTime='2026-11-15T00:00:03Z')),
                dict(type='jdk.NativeMethodSample',values=allocation)]
        result=summarize(events,marks)
        self.assertEqual(result['startup']['sampledAllocationBytes'],0)
        self.assertEqual(result['warm']['sampledAllocationBytes'],100)
        self.assertEqual(result['warm']['inclusiveAllocationBytes'],{'example.Work.run':100})
        self.assertEqual(result['warm']['executionSamples'],0)

    def test_publication_rejects_instrumented_runs_even_if_marked_eligible(self):
        value=complete();value['instrumented']=True
        with self.assertRaisesRegex(ValueError,'Instrumented'):validate(value)
        value=complete();value['jvmFlags'].append('-XX:StartFlightRecording=filename=profile.jfr')
        with self.assertRaisesRegex(ValueError,'Instrumented'):validate(value)

    def test_publication_rejects_incomplete_or_failed_transactions(self):
        baseline=complete();validate(baseline)
        mutations=[lambda d:d['starts'].pop(),
                   lambda d:d.__setitem__('contract','older-entity-hydration-contract'),
                   lambda d:d['starts'][0]['checks'].__setitem__('rollbackAfterFifteenInserts',False),
                   lambda d:d['starts'][0]['readsMs'].clear(),
                   lambda d:d['starts'][0].__setitem__('memoryEvents','oom_kill 1\n'),
                   lambda d:d['starts'][0]['shutdown'].__setitem__('exitCode',137),
                   lambda d:d['starts'][0]['shutdown'].__setitem__('remainingConnections',1),
                   lambda d:d['starts'][0]['shutdown'].__setitem__('lifecycleCompleted',False),
                   lambda d:d['starts'][0]['readsMs'].__setitem__(0,float('nan'))]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                value=copy.deepcopy(baseline);mutation(value)
                with self.assertRaises(ValueError):validate(value)

    def test_publication_rejects_unequal_contract_or_nondurable_database(self):
        baseline=complete()
        for field in ['sources','javaImage']:
            value=copy.deepcopy(baseline);value['buildInputs']['quarkus'][field]='different'
            with self.assertRaisesRegex(ValueError,'source contract and JDK'):validate(value)
        value=copy.deepcopy(baseline);value['postgres']['settings']['synchronous_commit']='off'
        with self.assertRaisesRegex(ValueError,'durable'):validate(value)
        value=copy.deepcopy(baseline);value['buildInputs']['quarkus']['jarSha256']['lib/persistence-model-1.0-SNAPSHOT.jar']='older-model'
        with self.assertRaisesRegex(ValueError,'shared entity model'):validate(value)

    def test_rollback_gate_uses_independent_database_visibility(self):
        with patch('compare_persistence.psql',return_value=SimpleNamespace(stdout='')):
            check_database('db','schema',2,absent=True)
        with patch('compare_persistence.psql',return_value=SimpleNamespace(stdout='Country|Country:2|0|{}\n')):
            with self.assertRaisesRegex(ValueError,'Independent PostgreSQL'):
                check_database('db','schema',2,absent=True)


if __name__=='__main__':unittest.main()
