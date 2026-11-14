"""Collect SDK reachability metadata with the existing capability workload.

Diagnostic only: the single instrumented JVM cannot form an eligible comparison.
The caller supplies the Mandrel native-image agent shared library on Linux Docker.
"""
import json
import hashlib
from pathlib import Path
import sys
import argparse
import compare


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('agent',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--framework',choices=['quarkus','guicedee'],default='quarkus')
    parser.add_argument('--image-tag',default='local')
    parser.add_argument('--quarkus-dependencies',choices=['wrapped','standard'],default='wrapped')
    options=parser.parse_args()
    library=options.agent.resolve()
    output=options.output.resolve()
    if not library.is_file(): raise SystemExit('Native-image agent library is missing')
    if output.exists() and any(output.iterdir()):raise SystemExit('Choose a fresh metadata output directory; old traces must not be reused')
    output.mkdir(parents=True,exist_ok=True)
    start=compare.start
    def traced_start(command,log,env,cwd=compare.ROOT):
        if command[:2]==['docker','run'] and '--publish' in command:
            command=list(command)
            # Metadata collection is not a timed comparison and needs extra headroom.
            command[command.index('--cpus')+1]='2'
            command[command.index('--memory')+1]='2g'
            command[command.index('--memory-swap')+1]='2g'
            command[2:2]=['--mount',f'type=bind,source={library},target=/native-agent.so,readonly',
                          '--mount',f'type=bind,source={output},target=/native-metadata']
            launch=command.index('--module-path') if options.framework=='guicedee' else command.index('-jar')
            command[launch:launch]=['--add-modules=jdk.unsupported',
                '-agentpath:/native-agent.so=config-output-dir=/native-metadata,config-write-period-secs=1,config-write-initial-delay-secs=0']
        return start(command,log,env,cwd)
    compare.start=traced_start
    probe=compare.probe
    rows=[]
    outputs=[]
    sdk_jars=[]
    traced_images=[]
    resolved_dependencies=[]
    def traced_probe(*args,**kwargs):
        row=probe(*args,**kwargs)
        row['instrumented']=True
        row['diagnosticLimits']='2 CPU / 2 GiB; metadata collection only'
        rows.append(row)
        out=args[2]
        outputs.append(out)
        (out/f"{row['variant']}-{row['run']}.json").write_text(json.dumps(row,indent=2)+'\n')
        environment=json.loads((out/'environment.json').read_text())
        traced_images.append(environment['images'][row['variant']])
        environment.update(instrumented=True,cpuQuota=row['diagnosticLimits'])
        if options.framework == 'quarkus' and options.quarkus_dependencies == 'standard':
            provenance=environment['imageBuildProvenance']['quarkus-standard']
            sdk_jars.extend({'name':entry['path'],'sha256':entry['sha256']} for entry in provenance['sdkJars'])
            resolved_dependencies.extend(provenance['resolvedDependencies'])
        for sdk in ([] if options.framework == 'quarkus' and options.quarkus_dependencies == 'standard' else ['firebase-admin','commercetools']):
            artifact=sdk+'-2.5.1.jar'
            provenance=environment['imageBuildProvenance'][options.framework]
            if 'phaseDiagnosticInputs' in provenance:
                matched=[entry for entry in provenance['phaseDiagnosticInputs']['stagedJars']
                         if entry['path'].endswith('/'+artifact)]
            else:
                prefix='quarkus/target/quarkus-app/lib/' if options.framework=='quarkus' else 'guicedee/target/lib/'
                matched=[entry for entry in provenance['packagedJars']
                         if entry['path'].startswith(prefix) and entry['path'].endswith(artifact)]
            if len(matched)!=1:raise RuntimeError('Cannot identify traced SDK artifact: '+artifact)
            sdk_jars.append({'name':artifact,'sha256':matched[0]['sha256']})
        (out/'environment.json').write_text(json.dumps(environment,indent=2)+'\n')
        return row
    compare.probe=traced_probe
    sys.argv=[sys.argv[0],'--docker','--firebase','--framework',options.framework,'--discovery','spi',
              '--quarkus-dependencies',options.quarkus_dependencies,
              '--image-tag',options.image_tag,'--runs','1','--requests','2','--warmup','1']
    result=compare.main()
    for out in outputs:
        summary=json.loads((out/'summary.json').read_text())
        summary.update(instrumented=True,scope='Native-image agent diagnostic: 2 CPU / 2 GiB; excluded from performance comparisons')
        (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    # Single-variant diagnostics intentionally return 1 even when all checks pass.
    passed=len(rows)==1 and len(rows[0]['checks'])==15 and all(c['passed'] for c in rows[0]['checks'].values())
    (output/'diagnostic.json').write_text(json.dumps({'instrumented':True,'performanceComparison':False,
        'harnessExitCode':result,'allCapabilitiesPassed':passed,'checks':rows[0]['checks'] if rows else {},
        'agentSha256':hashlib.sha256(library.read_bytes()).hexdigest(),'sdkJars':sdk_jars,
        'sourceImage':traced_images[0] if len(traced_images)==1 else None,
        'resolvedDependencies':resolved_dependencies,
        'dependencyMode':options.quarkus_dependencies if options.framework=='quarkus' else 'wrapped'},indent=2)+'\n')
    return 0 if passed and any((output/name).exists() for name in ['reachability-metadata.json','reflect-config.json']) else 1


if __name__=='__main__':raise SystemExit(main())
