import json
import threading
import unittest
from compare import request, eligible_comparison, metric_counts
from upstream import Upstream


class HarnessTest(unittest.TestCase):
    def test_incomplete_failed_and_single_framework_results_cannot_rank(self):
        self.assertFalse(eligible_comparison([], 1, 'both'))
        self.assertFalse(eligible_comparison([{'eligible':True}], 1, 'both'))
        self.assertFalse(eligible_comparison([{'eligible':True},{'eligible':False}], 1, 'both'))
        self.assertFalse(eligible_comparison([{'eligible':True},{'eligible':True}], 1, 'guicedee'))
        self.assertTrue(eligible_comparison([{'eligible':True},{'eligible':True}], 1, 'both'))

    def test_metric_parser_requires_actual_samples(self):
        self.assertEqual({}, metric_counts('# HELP benchmark_quotes Counter\n# TYPE benchmark_quotes counter\n'))
        self.assertEqual({'benchmark_quotes_total{scope="application"}':2}, metric_counts('benchmark_quotes_total{scope="application"} 2.0\n'))

    def test_fixture_requires_auth_and_records_retry_attempts(self):
        server=Upstream();thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base=f'http://127.0.0.1:{server.server_port}'
        try:
            self.assertEqual(401, request(base,'/benchmark')[0])
            self.assertEqual(401, request(base,'/oauth/token',raw=b'grant_type=client_credentials')[0])
            self.assertEqual(200, request(base,'/oauth/token',raw=b'grant_type=client_credentials',headers={'Authorization':'Basic Zml4dHVyZTpmaXh0dXJl'})[0])
            self.assertEqual([503,503,200],[request(base,'/flaky/test')[0] for _ in range(3)])
            self.assertEqual(3,server.counts['/flaky/test'])
            self.assertEqual(400,request(base,'/benchmark/graphql',{'query':'{ inventoryEntries }'})[0])
            self.assertEqual(200,request(base,'/benchmark/graphql',{'query':'{ inventoryEntries }'},headers={'Authorization':'Bearer fixture-token'})[0])
        finally:server.shutdown();server.server_close()


if __name__=='__main__':unittest.main()
