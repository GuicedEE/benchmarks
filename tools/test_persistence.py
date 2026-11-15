import copy
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from compare_persistence import CHECKS, CONTRACT, validate, check_database


def complete():
    rows=[]
    for variant in ['guicedee','quarkus']:
        rows.append(dict(variant=variant,run=1,eligible=True,checks=dict.fromkeys(CHECKS,True),
            readsMs=[1.0],cycles=[dict.fromkeys(['createMs','readMs','updateMs','deleteMs','cycleMs'],2.0)],
            image=variant,jvmFlags=['same'],oomKilled=False,memoryEvents='oom_kill 0\n',
            shutdown=dict(exitCode=143,remainingConnections=0,lifecycleCompleted=True),
            containerLimits=dict(nanoCpus=250000000,memoryBytes=500*2**20,memorySwapBytes=500*2**20)))
    return dict(eligible=True,contract=CONTRACT,runs=1,requests=1,starts=rows,jvmFlags=['same'],
        images={n:n for n in ['guicedee','quarkus']},
        buildInputs={n:dict(sources={'model.java':'same'},javaImage='same-jdk',
                           jarSha256={'lib/persistence-model-1.0-SNAPSHOT.jar':'same-model'}) for n in ['guicedee','quarkus']},
        postgres=dict(settings=dict(fsync='on',synchronous_commit='on',full_page_writes='on',isolation='read committed')))


class PersistenceTest(unittest.TestCase):
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
        with self.assertRaisesRegex(ValueError,'identical shared entity model'):validate(value)

    def test_rollback_gate_uses_independent_database_visibility(self):
        with patch('compare_persistence.psql',return_value=SimpleNamespace(stdout='')):
            check_database('db','schema',2,absent=True)
        with patch('compare_persistence.psql',return_value=SimpleNamespace(stdout='Country|Country:2|0|{}\n')):
            with self.assertRaisesRegex(ValueError,'Independent PostgreSQL'):
                check_database('db','schema',2,absent=True)


if __name__=='__main__':unittest.main()
