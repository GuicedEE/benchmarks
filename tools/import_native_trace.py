"""Retain observed SDK reflection/resources from a passing diagnostic agent run."""
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def verify_sdk_inputs(traced,current):
    if not traced or {e['name']:e['sha256'] for e in traced}!={e['name']:e['sha256'] for e in current}:
        raise ValueError('Traced Docker SDKs differ from local SDKs; rebuild the matching JVM image and retrace')


def main():
    if len(sys.argv)!=2: raise SystemExit('Usage: import_native_trace.py <agent-output-directory>')
    directory=Path(sys.argv[1])
    diagnostic=json.loads((directory/'diagnostic.json').read_text())
    if not diagnostic.get('allCapabilitiesPassed'): raise SystemExit('All workload checks must pass before importing a trace')
    source=directory/'reachability-metadata.json'
    metadata=json.loads(source.read_text())
    entries=set()
    inputs=[]
    for path in (ROOT/'guicedee/target/classpath.txt').read_text().strip().split(os.pathsep):
        jar=Path(path)
        if jar.name not in {entry['name'] for entry in diagnostic.get('sdkJars',[])}:continue
        with zipfile.ZipFile(jar) as archive: entries.update(archive.namelist())
        inputs.append({'name':jar.name,'sha256':hashlib.sha256(jar.read_bytes()).hexdigest()})
    verify_sdk_inputs(diagnostic.get('sdkJars'),inputs)
    classes={entry[:-6].replace('/','.') for entry in entries if entry.endswith('.class')}
    selected={'reflection':[entry for entry in metadata.get('reflection',[])
                            if isinstance(entry.get('type'),str) and entry['type'].removesuffix('[]') in classes],
              'resources':[entry for entry in metadata.get('resources',[]) if entry.get('glob') in entries]}
    # The JVM agent observes class-name queries for optional OpenSSL exception
    # types. Retain these only with their backend; otherwise native-image roots
    # the outer engine's initializer, which cannot run without tcnative either.
    for entry in selected['reflection']:
        if entry['type'].startswith('com.commercetools.internal.shaded.io.netty.handler.ssl.ReferenceCountedOpenSsl'):
            entry['condition']={'typeReached':'com.commercetools.internal.shaded.io.netty.internal.tcnative.SSL'}
    target=ROOT/'quarkus-native/src/main/resources/META-INF/native-image/dev.guicedee.benchmarks/sdk-trace'
    target.mkdir(parents=True,exist_ok=True)
    (target/'reachability-metadata.json').write_text(json.dumps(selected,indent=2)+'\n')
    (ROOT/'quarkus-native/native-trace-inputs.json').write_text(json.dumps({
        'agentSha256':diagnostic['agentSha256'],'traceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'allCapabilitiesPassed':True,'sdkJars':inputs,'included':{key:len(value) for key,value in selected.items()},
        'scope':'Only types and resources owned by the two SDK wrapper JARs; no workload code changes'},indent=2)+'\n')
    print('Imported SDK reachability metadata:',{key:len(value) for key,value in selected.items()})


if __name__=='__main__':main()
