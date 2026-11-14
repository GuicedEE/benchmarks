"""Relocate embedded SDK native-image metadata using the SDK wrappers' actual shade rules."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def rules(pom):
    result=[]
    root=ET.parse(pom).getroot()
    namespace={'m':root.tag.split('}')[0].removeprefix('{')}
    for relocation in root.findall('.//m:relocation',namespace):
        source=relocation.findtext('m:pattern',namespaces=namespace)
        target=relocation.findtext('m:shadedPattern',namespaces=namespace)
        exclusions=[e.text.removesuffix('.**') for e in relocation.findall('m:excludes/m:exclude',namespace)]
        result.append((source,target,exclusions))
    return sorted(result,key=lambda r:len(r[0]),reverse=True)


def relocate(text, relocations):
    def name(value):
        separator='/' if '/' in value else '.'
        dotted=value.replace('/','.')
        for source,target,excluded in relocations:
            if (dotted==source or dotted.startswith(source+'.')) and not any(dotted==e or dotted.startswith(e+'.') for e in excluded):
                return (target+dotted[len(source):]).replace('.',separator)
        return value
    # Protect Java regex quoting while mapping its quoted resource/package name.
    text=text.replace('\\Q','\\Q ')
    text=re.sub(r'(?:[A-Za-z_$][\w$]*[./])+[A-Za-z_$][\w$]*',lambda m:name(m.group()),text)
    return text.replace('\\Q ','\\Q')


def transform(value, relocations):
    if isinstance(value,str): return relocate(value,relocations)
    if isinstance(value,list): return [transform(v,relocations) for v in value]
    if isinstance(value,dict): return {k:transform(v,relocations) for k,v in value.items()}
    return value


def optional_logging(value):
    # google-http-client registers an optional Commons Logging adapter even without Log4j 1.x.
    # Querying all its methods requires the absent backend. Retain it conditionally instead.
    if isinstance(value,list):
        for entry in value:
            if isinstance(entry,dict) and entry.get('name','').endswith('.org.apache.commons.logging.impl.Log4JLogger'):
                prefix=entry['name'].split('org.apache.commons.logging.impl.Log4JLogger')[0]
                entry.setdefault('condition',{'typeReachable':prefix+'org.apache.log4j.Logger'})
    return value


def conditional_protobuf(value):
    # Generated Google client metadata eagerly registers every public method of
    # every protobuf, including products the application never uses. A message
    # still gets its full metadata when its type is reachable through application
    # code or another used message. Do not override upstream conditions.
    for entry in value:
        entry.setdefault('condition', {'typeReachable': entry['name']})
    return value


def prepare(repository=None, version=None):
    from build import framework_version
    version = version or framework_version()
    dependencies=([repository/f'com/guicedee/modules/services/{sdk}/{version}/{sdk}-{version}.jar'
                   for sdk in ['firebase-admin','commercetools']] if repository else
                  [Path(p) for p in (ROOT/'guicedee/target/classpath.txt').read_text().strip().split(os.pathsep)])
    base=ROOT/'quarkus-native/src/main/resources/META-INF/native-image/dev.guicedee.benchmarks'
    traced=json.loads((base/'sdk-trace/reachability-metadata.json').read_text())
    observed_types={entry['type'] for entry in traced['reflection'] if isinstance(entry.get('type'),str)}
    manifest=[]
    for sdk in ['firebase-admin','commercetools']:
        jar=next(p for p in dependencies if p.name==sdk+'-'+version+'.jar')
        with zipfile.ZipFile(jar) as z:
            # Read the recipe for this exact binary. Workspace shade rules can
            # change independently of the immutable SDK used in the comparison.
            pom_bytes=z.read(f'META-INF/maven/com.guicedee.modules.services/{sdk}/pom.xml')
            relocations=rules(io.BytesIO(pom_bytes))
            if not relocations: raise ValueError('Missing embedded SDK relocation rules: '+str(jar))
            # Quarkus disables GraalVM's automatic ServiceLoader feature. Keep the
            # shaded SDK descriptors and register provider constructors explicitly.
            services=[]
            providers=[]
            for entry in z.namelist():
                if not entry.startswith('META-INF/services/') or entry.endswith('/'):
                    continue
                service=entry.removeprefix('META-INF/services/')
                services.append({'pattern':r'\Q'+entry+r'\E'})
                implementations=[line.split('#',1)[0].strip() for line in z.read(entry).decode('utf-8').splitlines()]
                # Retain every provider of an exercised SPI. Unused SDK products
                # need their own trace before claiming native capability coverage.
                if any(provider in observed_types for provider in implementations):
                    for provider in filter(None,implementations):
                        providers.append({'name':provider,'condition':{'typeReachable':service},
                                          'methods':[{'name':'<init>','parameterTypes':[]}]})
            service_dir=base/sdk/'sdk-services'
            service_dir.mkdir(parents=True,exist_ok=True)
            (service_dir/'resource-config.json').write_text(json.dumps({'resources':{'includes':services}},indent=2)+'\n')
            (service_dir/'reflect-config.json').write_text(json.dumps(providers,indent=2)+'\n')
            for entry in z.namelist():
                if not entry.startswith('META-INF/native-image/') or entry.endswith('/'):
                    continue
                if not entry.endswith(('.json','.properties')): continue
                source=z.read(entry).decode('utf-8')
                if entry.endswith('.json'):
                    value=optional_logging(transform(json.loads(source),relocations))
                    if entry in {'META-INF/native-image/'+package+'/reflect-config.json' for package in
                                 ['com.google.storage.v2','com.google.cloud.monitoring.v3','com.google.cloud.firestore.v1']}:
                        value=conditional_protobuf(value)
                    output=json.dumps(value,indent=2)+'\n'
                else:
                    output=relocate(source,relocations)
                target=base/sdk/entry.removeprefix('META-INF/native-image/')
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_text(output,encoding='utf-8')
        manifest.append({'sdk':sdk,'jarSha256':hashlib.sha256(jar.read_bytes()).hexdigest(),
                         'shadePomSha256':hashlib.sha256(pom_bytes).hexdigest(),
                         'shadePomSource':'embedded SDK wrapper POM'})
    (ROOT/'quarkus-native/native-metadata-inputs.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Relocated SDK native-image metadata; original metadata is excluded only during native compilation.')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--repository',type=Path,help='Use the isolated benchmark SDK snapshot instead of host dependencies')
    parser.add_argument('--version',help='GuicedEE artifact version; defaults to the benchmark POM')
    args=parser.parse_args()
    prepare(args.repository,args.version)
