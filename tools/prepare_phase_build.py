"""Prepare a phase build using an existing, isolated Docker Maven repository snapshot."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile
from image_provenance import ROOT, capture


def prepare(update_openapi=False):
    repository=ROOT/'docker/repository'
    source=ROOT.parent/'GuicedEE/inject/target/inject-2.5.1.jar'
    target=repository/'com/guicedee/inject/2.5.1/inject-2.5.1.jar'
    if not target.is_file(): raise ValueError('Stage the benchmark Docker repository before building diagnostics')
    with zipfile.ZipFile(source) as jar:
        if not {'module-info.class','com/guicedee/guicedinjection/StartupDiagnostics.class'}.issubset(jar.namelist()):
            raise ValueError('Build the modular inject artifact with startup diagnostics first')
    for name in ['firebase-admin','commercetools']:
        with zipfile.ZipFile(repository/f'com/guicedee/modules/services/{name}/2.5.1/{name}-2.5.1.jar') as jar:
            if 'module-info.class' not in jar.namelist(): raise ValueError('Staged SDK is not modular: '+name)
    shutil.copy2(source,target)
    if update_openapi:
        source=ROOT.parent/'GuicedEE/openapi/target/openapi-2.5.1.jar'
        with zipfile.ZipFile(source) as jar:
            if 'module-info.class' not in jar.namelist(): raise ValueError('OpenAPI artifact must be modular')
        shutil.copy2(source,repository/'com/guicedee/openapi/2.5.1/openapi-2.5.1.jar')
    inputs={'note':'Linux Maven builds the applications from captured sources. Staged artifacts are authoritative; host target JARs are not used.',
            'frameworkSources':[],'stagedJars':[]}
    for filename in ['GuiceApplication.java','GuiceContext.java','StartupDiagnostics.java']:
        path=ROOT.parent/'GuicedEE/inject/src/main/java/com/guicedee/guicedinjection'/filename
        inputs['frameworkSources'].append({'path':path.relative_to(ROOT.parent).as_posix(),
                                         'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    if update_openapi:
        for path in sorted((ROOT.parent/'GuicedEE/openapi/src/main').rglob('*')):
            if path.is_file():
                inputs['frameworkSources'].append({'path':path.relative_to(ROOT.parent).as_posix(),
                    'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'content':path.read_text(encoding='utf-8')})
    for jar in sorted(repository.rglob('*.jar')):
        inputs['stagedJars'].append({'path':jar.relative_to(repository).as_posix(),'sha256':hashlib.sha256(jar.read_bytes()).hexdigest()})
    provenance=capture()
    provenance.pop('packagedJars')
    provenance['phaseDiagnosticInputs']=inputs
    (ROOT/'docker/build-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
    print('Prepared phase inputs; retained staged SDKs and updated inject'+(' and OpenAPI.' if update_openapi else '.'))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--update-openapi',action='store_true',help='Stage the freshly packaged modular OpenAPI artifact')
    prepare(parser.parse_args().update_openapi)
