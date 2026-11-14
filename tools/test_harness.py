import json
import io
import threading
import unittest
import tempfile
import zipfile
import subprocess
from pathlib import Path
from unittest.mock import patch
import image_provenance
from build import verify_framework
import stage_link_repository
from compare import request, eligible_comparison, metric_counts, discovery_evidence, phase_evidence
from upstream import Upstream
from variants import select_variants, ordered_variants, paired_image_variants, guicedee_jar, runtime_flags
from prepare_jlink import verify_scanner_artifact, DISCOVERY_ENTRIES
from prepare_native import verify_quarkus_adapter
from prepare_native_metadata import relocate, transform, conditional_protobuf, rules
from import_native_trace import verify_sdk_inputs
from summarize_native import sdk_evidence


class HarnessTest(unittest.TestCase):
    def test_build_checks_explicit_framework_inputs_before_native_build(self):
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            client = repository/'com/guicedee/client/2.6.0/client-2.6.0.jar'
            client.parent.mkdir(parents=True)
            with zipfile.ZipFile(client, 'w') as jar:
                jar.writestr('module-info.class', b'descriptor')
            with self.assertRaisesRegex(ValueError, 'IGuiceDiscovery'):
                verify_framework(repository, '2.6.0')
            with zipfile.ZipFile(client, 'a') as jar:
                jar.writestr('com/guicedee/client/services/IGuiceDiscovery.class', b'spi')
            verify_framework(repository, '2.6.0')
            with self.assertRaisesRegex(ValueError, 'native-image'):
                verify_framework(repository, '2.6.0', native=True)

    def test_staging_rejects_dependencies_outside_the_selected_repository(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = root/'chosen-repository'
            repository.mkdir()
            (root/'guicedee/target').mkdir(parents=True)
            outside = root/'unselected.jar'
            outside.write_bytes(b'not-from-selected-repository')
            (root/'guicedee/target/classpath.txt').write_text(str(outside))
            with patch.object(stage_link_repository, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'outside --repository'):
                    stage_link_repository.stage(repository, ['guicedee'])
            self.assertFalse((root/'docker/repository').exists())

    def test_staging_maps_this_checkouts_maven4_reactor_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = root/'chosen-repository'
            repository.mkdir()
            artifact = root/'.mvn/target/project-local-repo/dev.guicedee.benchmarks/common/1/common-1.jar'
            artifact.parent.mkdir(parents=True)
            artifact.write_bytes(b'current-reactor-output')
            artifact.with_suffix('.pom').write_text('<project/>')
            (root/'guicedee/target').mkdir(parents=True)
            (root/'guicedee/target/classpath.txt').write_text(str(artifact))
            with patch.object(stage_link_repository, 'ROOT', root):
                stage_link_repository.stage(repository, ['guicedee'])
            staged = root/'docker/repository/dev/guicedee/benchmarks/common/1/common-1.jar'
            self.assertEqual(artifact.read_bytes(), staged.read_bytes())
            self.assertTrue(staged.with_suffix('.pom').exists())

    def test_standard_quarkus_is_separate_and_provenance_cannot_be_mislabeled(self):
        variants = select_variants(runtime='native', quarkus_dependencies='standard')
        self.assertEqual(['guicedee-native','quarkus-standard-native'],[v['id'] for v in variants])
        shared = {'path':'common/src/main/java/bench/workload/Workload.java','sha256':'same'}
        wrapped = {'sourcesAtImageBuild':[shared, {'path':'quarkus-native/native-metadata-inputs.json',
                    'content':json.dumps([{'sdk':name,'jarSha256':'wrapped-'+name} for name in ['firebase-admin','commercetools']])}]}
        standard = {'dependencyMode':'standard','sourcesAtImageBuild':[shared], 'resolvedDependencies':[],
                    'sdkJars':[{'path':path,'sha256':'upstream-'+path} for path in
                               ['com/google/firebase/firebase-admin/9.12.0/sdk.jar',
                                'com/commercetools/sdk/commercetools-sdk-java-api/20.4.0/sdk.jar']]}
        provenances = dict(zip([v['id'] for v in variants],[wrapped,standard]))
        evidence = sdk_evidence(variants,provenances)
        self.assertFalse(evidence['sdkHashesMatch'])
        self.assertEqual('independent-upstream-vs-wrapped',evidence['dependencyComparison'])
        with self.assertRaises(ValueError): sdk_evidence(variants,dict.fromkeys(provenances,wrapped))
        standard['sourcesAtImageBuild'] = [dict(shared,sha256='changed')]
        with self.assertRaises(ValueError): sdk_evidence(variants,provenances)
        standard['sourcesAtImageBuild'] = [shared]
        standard['resolvedDependencies'] = [{'path':'com/guicedee/services/firebase-admin/wrapper.jar'}]
        with self.assertRaises(ValueError): sdk_evidence(variants,provenances)

    def test_sdk_shade_recipe_accepts_both_embedded_pom_versions(self):
        for version in ['4.0.0','4.1.0']:
            pom=f'<project xmlns="http://maven.apache.org/POM/{version}"><relocations><relocation><pattern>io.netty</pattern><shadedPattern>private.io.netty</shadedPattern><excludes><exclude>io.netty.keep.**</exclude></excludes></relocation></relocations></project>'
            recipe=rules(io.BytesIO(pom.encode()))
            self.assertEqual('private.io.netty.channel.epoll',relocate('io.netty.channel.epoll',recipe))
            self.assertEqual('io.netty.keep.API',relocate('io.netty.keep.API',recipe))

    def test_protobuf_metadata_retains_members_and_existing_conditions(self):
        entries=[{'name':'UnusedMessage','allPublicMethods':True},
                 {'name':'UsedMessage','condition':{'typeReachable':'Client'},'methods':[{'name':'parse'}]}]
        result=conditional_protobuf(entries)
        self.assertEqual({'typeReachable':'UnusedMessage'},result[0]['condition'])
        self.assertTrue(result[0]['allPublicMethods'])
        self.assertEqual({'typeReachable':'Client'},result[1]['condition'])
        self.assertEqual([{'name':'parse'}],result[1]['methods'])

    def test_paired_images_preserve_artifacts_and_reverse_execution_order(self):
        bases=select_variants('guicedee',runtime='jlink')
        variants=paired_image_variants(bases,'baseline','candidate')
        self.assertEqual(4,len({v['id'] for v in variants}))
        self.assertEqual(['baseline','candidate']*2,[v['imageTag'] for v in variants])
        self.assertEqual(['guicedee-jlink']*2+['guicedee-scan-jlink']*2,[v['imageArtifact'] for v in variants])
        self.assertEqual(list(reversed(bases)),ordered_variants(bases,2))
        self.assertEqual(list(reversed(variants)),ordered_variants(variants,2))
        self.assertEqual(['comparison-guicedee-1.0-SNAPSHOT.jar']*2+['comparison-guicedee-scan-1.0-SNAPSHOT.jar']*2,
                         [guicedee_jar(v) for v in variants])
        with self.assertRaises(ValueError): paired_image_variants(bases,'same','same')
        native=paired_image_variants(select_variants(runtime='native'),'before','after')
        self.assertEqual(['guicedee-native']*2+['quarkus-native']*2,[v['imageArtifact'] for v in native])
        self.assertTrue(all(v['runtime']=='native' for v in native))
        self.assertTrue(all('-XX:TieredStopAtLevel=1' not in runtime_flags(v,['-Xmx384m','-XX:TieredStopAtLevel=1']) for v in native))

    def test_workload_phase_waits_for_completion_and_preserves_disabled_stage(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary)
            probe=directory/'TraceProbe.java'
            probe.write_text('''package bench.workload;
import java.io.*;
import java.util.concurrent.*;
public class TraceProbe {
  public static void main(String[] args) {
    var pending = new CompletableFuture<String>();
    var output = new ByteArrayOutputStream();
    var original = System.out;
    System.setOut(new PrintStream(output));
    var trace = WorkloadTrace.start("pending", true);
    var result = trace.complete(trace.async("network", () -> pending));
    if (result.toCompletableFuture().isDone() || output.size()!=0) throw new AssertionError("Premature completion");
    pending.complete("done");
    if (!result.toCompletableFuture().join().equals("done")) throw new AssertionError();
    var disabled = WorkloadTrace.start("disabled", false);
    if (disabled.async("network", () -> pending)!=pending || disabled.complete(pending)!=pending) throw new AssertionError("Disabled observer changed stage");
    var failure = new CompletableFuture<String>();
    var failedTrace = WorkloadTrace.start("failed", true);
    var failedResult = failedTrace.complete(failedTrace.async("network", () -> failure));
    failure.completeExceptionally(new IllegalStateException("expected"));
    if (!failedResult.toCompletableFuture().isCompletedExceptionally()) throw new AssertionError("Failure lost");
    System.setOut(original);
    System.out.print(output);
  }
}''')
            source=Path(__file__).resolve().parents[1]/'common/src/main/java/bench/workload/WorkloadTrace.java'
            subprocess.run(['javac','-d',temporary,str(source),str(probe)],check=True,capture_output=True,text=True)
            output=subprocess.check_output(['java','-cp',temporary,'bench.workload.TraceProbe'],text=True)
            rows=[json.loads(line.removeprefix('BENCH_PHASE ')) for line in output.splitlines()]
            self.assertEqual(['pending','failed'],[row['operation'] for row in rows])
            self.assertEqual([True,False],[row['success'] for row in rows])
            self.assertEqual([True,False],[row['events'][0]['success'] for row in rows])

    def test_instrumented_runs_cannot_be_ranked_and_missing_phase_evidence_fails(self):
        variants=select_variants('guicedee')
        rows=[{'variant':v['id'],'run':1,'eligible':True,'instrumented':True} for v in variants]
        self.assertFalse(eligible_comparison(rows,1,variants))
        with tempfile.TemporaryDirectory() as temporary:
            self.assertFalse(phase_evidence('',Path(temporary),'guicedee')['verified'])
            self.assertFalse(phase_evidence('',Path(temporary),'quarkus')['verified'])
            operations=[{'operation':name,'success':True,'events':[]} for name in
                        ['workload-construction','workload-construction','first-quote','first-firestore']]
            log='\n'.join('BENCH_PHASE '+json.dumps(op) for op in operations)
            self.assertTrue(phase_evidence(log,Path(temporary),'quarkus')['verified'])
            self.assertFalse(phase_evidence(log+'\nBENCH_PHASE '+json.dumps(operations[-1]),Path(temporary),'quarkus')['verified'])

    def test_native_trace_rejects_stale_or_unidentified_sdk_images(self):
        inputs=[{'name':'sdk.jar','sha256':'current'}]
        verify_sdk_inputs(inputs,inputs)
        with self.assertRaises(ValueError):verify_sdk_inputs([],inputs)
        with self.assertRaises(ValueError):verify_sdk_inputs([{'name':'sdk.jar','sha256':'old'}],inputs)

    def test_sdk_native_metadata_preserves_hosted_and_jni_apis(self):
        rules=[('org','private.org',['org.graalvm','org.conscrypt']),('io','private.io',[])]
        self.assertEqual('--initialize-at-run-time=private.io.grpc.netty,org.conscrypt',
                         relocate('--initialize-at-run-time=io.grpc.netty,org.conscrypt',rules))
        self.assertEqual(r'\Qprivate/io/grpc/Netty\E',relocate(r'\Qio/grpc/Netty\E',rules))
        self.assertEqual('org.graalvm.nativeimage.hosted.Feature',relocate('org.graalvm.nativeimage.hosted.Feature',rules))
        self.assertEqual('--initialize-at-build-time=private.io.netty',
                         relocate('--initialize-at-build-time=io.netty',[('io.netty','private.io.netty',[])]))
        self.assertEqual({'name':'private.io.grpc.netty.shaded.io.netty.Foo'},transform({'name':'io.grpc.netty.shaded.io.netty.Foo'},rules))

    def test_native_rejects_different_adapter_bytecode_or_defaults(self):
        with tempfile.TemporaryDirectory() as temporary:
            a,b=Path(temporary)/'jvm.jar',Path(temporary)/'native.jar'
            def write(path,code=b'same',properties=b'same'):
                with zipfile.ZipFile(path,'w') as jar:
                    jar.writestr('bench/quarkus/Resource.class',code)
                    jar.writestr('application.properties',properties)
            write(a);write(b);verify_quarkus_adapter(a,b)
            write(b,code=b'different')
            with self.assertRaises(AssertionError):verify_quarkus_adapter(a,b)
            write(b,properties=b'different')
            with self.assertRaises(AssertionError):verify_quarkus_adapter(a,b)

    def test_native_is_explicit_preserves_spi_and_never_receives_jit_flags(self):
        variants=select_variants(runtime='both',native=True)
        self.assertEqual(7,len(variants))
        native=variants[-1]
        self.assertEqual('quarkus-native',native['id'])
        self.assertEqual([native],select_variants('quarkus',runtime='native'))
        self.assertEqual([variants[-2]],select_variants('guicedee',runtime='native'))
        self.assertEqual('spi',variants[-2]['discovery'])
        self.assertEqual([],select_variants('guicedee','scan',runtime='native'))
        flags=['-Xms128m','-Xmx384m','-XX:ActiveProcessorCount=2','-XX:TieredStopAtLevel=1']
        self.assertEqual(flags[:-1],runtime_flags(native,flags))
        self.assertEqual(flags,runtime_flags(variants[0],flags))

    def test_provenance_captures_defaults_but_not_private_local_overrides(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'guicedee').mkdir()
            (root/'guicedee/.env').write_text('TELEMETRY_ENABLED=false\n')
            (root/'guicedee/.env.local').write_text('PRIVATE_OVERRIDE=do-not-archive\n')
            (root/'.git').mkdir()
            (root/'.git/private.xml').write_text('VCS metadata must not enter image provenance')
            with patch.object(image_provenance, 'ROOT', root):
                result = image_provenance.capture()
            self.assertEqual(['guicedee/.env'], [s['path'] for s in result['sourcesAtImageBuild']])
            self.assertNotIn('do-not-archive', json.dumps(result))

    def test_incomplete_duplicate_failed_and_single_variant_results_cannot_rank(self):
        variants = select_variants(runtime='both')
        rows = [{'variant':v['id'], 'run':run, 'eligible':True} for v in variants for run in [1,2]]
        self.assertTrue(eligible_comparison(rows, 2, variants))
        self.assertFalse(eligible_comparison([], 2, variants))
        self.assertFalse(eligible_comparison(rows[:-1], 2, variants))
        self.assertFalse(eligible_comparison(rows[:-1]+[rows[0]], 2, variants))
        self.assertFalse(eligible_comparison(rows[:-1]+[dict(rows[-1],eligible=False)], 2, variants))
        self.assertFalse(eligible_comparison([rows[0]], 1, variants[:1]))

    def test_variants_select_distinct_artifacts_and_rotate_order(self):
        variants = select_variants(runtime='both')
        self.assertEqual(['guicedee','guicedee-scan','quarkus','guicedee-jlink','guicedee-scan-jlink'], [v['id'] for v in variants])
        self.assertNotEqual(guicedee_jar(variants[0]), guicedee_jar(variants[1]))
        self.assertEqual(['guicedee-scan-jlink'], [v['id'] for v in select_variants('guicedee','scan','jlink')])
        for run in range(1,7): self.assertCountEqual(variants, ordered_variants(variants,run))
        self.assertNotEqual(ordered_variants(variants,1),ordered_variants(variants,2))

    def test_scanner_artifact_rejects_hidden_provider_and_different_business_bytecode(self):
        with tempfile.TemporaryDirectory() as temporary:
            spi, scan = Path(temporary)/'spi.jar', Path(temporary)/'scan.jar'
            with zipfile.ZipFile(spi,'w') as jar:
                for entry in DISCOVERY_ENTRIES: jar.writestr(entry,b'provider')
                jar.writestr('module-info.class',b'spi-descriptor')
                jar.writestr('bench/guicedee/rest/Resource.class',b'business')
            def write_scan(bytecode, provider=False, descriptor=True):
                with zipfile.ZipFile(scan,'w') as jar:
                    if descriptor: jar.writestr('module-info.class',b'scanner-descriptor')
                    jar.writestr('bench/guicedee/rest/Resource.class',bytecode)
                    if provider: jar.writestr('bench/guicedee/BenchmarkDiscovery.class',b'provider')
            write_scan(b'business')
            verify_scanner_artifact(spi,scan)
            write_scan(b'business',provider=True)
            with self.assertRaises(AssertionError): verify_scanner_artifact(spi,scan)
            write_scan(b'different')
            with self.assertRaises(AssertionError): verify_scanner_artifact(spi,scan)
            write_scan(b'business',descriptor=False)
            with self.assertRaises(AssertionError): verify_scanner_artifact(spi,scan)

    def test_metric_parser_requires_actual_samples(self):
        self.assertEqual({}, metric_counts('# HELP benchmark_quotes Counter\n# TYPE benchmark_quotes counter\n'))
        self.assertEqual({'benchmark_quotes_total{scope="application"}':2}, metric_counts('benchmark_quotes_total{scope="application"} 2.0\n'))

    def test_discovery_evidence_requires_the_requested_scanner_and_both_deployments(self):
        deployed = 'Deploying Verticle: bench.guicedee.rest - pool\nDeploying Verticle: bench.guicedee.service - pool'
        self.assertTrue(discovery_evidence(deployed,'spi')['verified'])
        self.assertFalse(discovery_evidence(deployed,'scan')['verified'])
        scanning = 'Initializing ClassGraph scanner for dependency discovery\n'+deployed
        self.assertTrue(discovery_evidence(scanning,'scan')['verified'])
        self.assertFalse(discovery_evidence(scanning,'spi')['verified'])
        self.assertFalse(discovery_evidence('Initializing ClassGraph scanner for dependency discovery','scan')['verified'])

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
