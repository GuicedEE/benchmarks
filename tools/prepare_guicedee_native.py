"""Prepare native inputs from a successful GuicedEE trace and the isolated SDK snapshot."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile
from image_provenance import ROOT, capture
from import_native_trace import verify_sdk_inputs


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(trace=None):
    repository=ROOT/'docker/repository'
    manifest_path=ROOT/'guicedee-native/native-trace-inputs.json'
    diagnostic=json.loads((trace/'diagnostic.json' if trace else manifest_path).read_text())
    check_count=len(diagnostic.get('checks',{})) if trace else diagnostic.get('capabilityCount',0)
    if not diagnostic.get('allCapabilitiesPassed') or check_count!=15:
        raise ValueError('Native metadata requires a successful full GuicedEE capability trace')
    sdk_inputs=[]
    for sdk in ['firebase-admin','commercetools']:
        jar=repository/f'com/guicedee/modules/services/{sdk}/2.5.1/{sdk}-2.5.1.jar'
        sdk_inputs.append({'name':jar.name,'sha256':sha(jar)})
    verify_sdk_inputs(diagnostic['sdkJars'],sdk_inputs)
    staged=[]
    for source,coordinate in [('services/Google/guice-core','modules/services/guice'),('native-image','native-image'),
                              ('openapi','openapi'),('swagger-ui','swagger-ui')]:
        name=coordinate.split('/')[-1]
        directory=ROOT.parent/'GuicedEE'/source
        jar=directory/f'target/{name}-2.5.1.jar'
        with zipfile.ZipFile(jar) as archive:
            if 'module-info.class' not in archive.namelist(): raise ValueError('Missing module descriptor: '+str(jar))
        destination=repository/f'com/guicedee/{coordinate}/2.5.1'
        destination.mkdir(parents=True,exist_ok=True)
        shutil.copy2(jar,destination/jar.name)
        pom=directory/('flatter.pom' if (directory/'flatter.pom').exists() else 'pom.xml')
        shutil.copy2(pom,destination/f'{name}-2.5.1.pom')
        staged.append({'path':str(jar.relative_to(ROOT.parent)),'sha256':sha(jar)})
    output=ROOT/'guicedee-native/src/main/resources/META-INF/native-image/dev.guicedee.benchmarks/guicedee-trace'
    metadata=json.loads((trace/'reachability-metadata.json' if trace else output/'reachability-metadata.json').read_text())
    def generated(entry):
        return any(marker in str(entry.get('type','')) for marker in ['$$EnhancerByGuice$$','$$FastClassByGuice$$'])
    metadata['reflection']=[entry for entry in metadata['reflection'] if not generated(entry)]
    for entry in metadata['reflection']:
        name=entry.get('type','')
        if isinstance(name,str) and name.startswith(('com.guicedee.','com.google.inject.','bench.guicedee.')):
            # JVM fast constructors bypass the tracing agent; native Guice uses reflection.
            # Keep traced member access instead of making every framework method invocable.
            # That blanket registration retained unrelated runtime paths in the native image.
            entry['allDeclaredConstructors']=True
            entry.pop('allDeclaredMethods',None)
            entry.pop('allDeclaredFields',None)
        if isinstance(name,str) and name.startswith('io.swagger.v3.oas.models.'):
            # Model serialization metadata belongs to the optional OpenAPI library.
            for flag in ('allDeclaredConstructors','allDeclaredMethods','allDeclaredFields'):
                entry.pop(flag,None)
        if isinstance(name,str) and name.startswith('com.commercetools.internal.shaded.io.netty.handler.ssl.ReferenceCountedOpenSsl'):
            entry['condition']={'typeReached':'com.commercetools.internal.shaded.io.netty.internal.tcnative.SSL'}
    output.mkdir(parents=True,exist_ok=True)
    (output/'reachability-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    resources=sorted({entry['glob'] for entry in metadata.get('resources',[]) if 'glob' in entry})
    if any(any(char in resource for char in '*\\\"\n') for resource in resources):
        raise ValueError('Expected literal traced resource paths for modular registration')
    (ROOT/'guicedee-native/native-resources.txt').write_text('\n'.join(resources)+'\n')
    manifest={'traceSha256':sha(trace/'reachability-metadata.json') if trace else diagnostic['traceSha256'],
              'metadataSha256':sha(output/'reachability-metadata.json'),
              'sdkJars':sdk_inputs,'frameworkJars':staged,'capabilityCount':15,
              'allCapabilitiesPassed':True,'agentSha256':diagnostic['agentSha256']}
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    provenance=capture()
    provenance['guicedeeNativeInputs']=manifest
    provenance['guicedeeNativeInputs']['stagedJars']=[{'path':p.relative_to(repository).as_posix(),'sha256':sha(p)}
                                                    for p in sorted(repository.rglob('*.jar'))]
    (ROOT/'docker/build-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print('Prepared native Guice support and full capability trace; retained verified SDK snapshot.')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('trace',type=Path,nargs='?',help='Fresh agent trace, or reuse committed metadata for the exact recorded SDKs')
    prepare(parser.parse_args().trace)
