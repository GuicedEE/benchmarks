"""Import upstream SDK reachability from a passing Quarkus or Micronaut JVM trace.

Framework support stays with its published integrations; Micronaut also retains observed
Firebase/auth/API-client reflection alongside Google's native-image support.
No relocated types, substitutions, or previous wrapper traces are copied.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile
from import_native_trace import verify_sdk_inputs

ROOT = Path(__file__).resolve().parents[1]
PREFIXES = ('com.commercetools.', 'io.vrap.', 'tools.jackson.', 'javax.money.', 'org.javamoney.', 'org.asynchttpclient.')


def select(metadata, framework='quarkus'):
    prefixes = PREFIXES + (('com.google.firebase.', 'com.google.auth.', 'com.google.api.client.', 'com.google.cloud.firestore.') if framework == 'micronaut' else ())
    return {
        'reflection': [entry for entry in metadata.get('reflection', [])
                       if isinstance(entry.get('type'), str) and entry['type'].startswith(prefixes)],
        'resources': [entry for entry in metadata.get('resources', [])
                      if entry.get('glob', '').startswith(tuple('META-INF/services/' + prefix for prefix in PREFIXES))
                      or entry.get('glob', '').startswith('org/asynchttpclient/')
                      or entry.get('glob') == 'javamoney.properties'
                      or framework == 'micronaut' and entry.get('glob','').startswith(('com/google/firebase/','com/google/auth/','com/google/api/client/','com/google/cloud/firestore/'))]
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--framework', choices=['quarkus','micronaut'], default='quarkus')
    parser.add_argument('--image')
    args = parser.parse_args()
    project = 'micronaut' if args.framework == 'micronaut' else 'quarkus-standard'
    args.image = args.image or f'devsuite-bench-{project}:local'
    diagnostic = json.loads((args.directory/'diagnostic.json').read_text())
    if not diagnostic.get('allCapabilitiesPassed') or diagnostic.get('dependencyMode') != 'standard':
        raise ValueError('A passing standard-dependency trace is required')
    image = json.loads(subprocess.check_output(['docker','image','inspect',args.image],text=True))[0]['Id']
    provenance = json.loads(subprocess.check_output(['docker','run','--rm','--entrypoint','cat',image,
                                                   '/app/build-provenance.json'],text=True))
    inputs = [{'name':entry['path'],'sha256':entry['sha256']} for entry in provenance['sdkJars']]
    verify_sdk_inputs(diagnostic['sdkJars'], inputs)
    if not diagnostic.get('sourceImage'): raise ValueError('Missing traced image identity')
    owner_paths = ('com/commercetools/sdk/', 'org/asynchttpclient/', 'tools/jackson/', 'org/javamoney/',
                   'javax/money/', 'com/fasterxml/jackson/core/jackson-annotations/')
    if args.framework == 'micronaut': owner_paths += ('com/google/',)
    def relevant(dependencies):
        return [{'name':entry['path'],'sha256':entry['sha256']} for entry in dependencies
                if entry['path'].startswith(owner_paths)]
    verify_sdk_inputs(relevant(diagnostic['resolvedDependencies']), relevant(provenance['resolvedDependencies']))
    source = args.directory/'reachability-metadata.json'
    metadata = select(json.loads(source.read_text()), args.framework)
    # The JDK 25 agent records provider type lookups but not ServiceLoader's
    # MethodHandle constructor invocation. Register the upstream JARs' declared
    # providers explicitly, as a Quarkus extension would, without enabling every
    # optional service from every transitive dependency.
    providers = {}
    reflection = {entry['type']:entry for entry in metadata['reflection']}
    resources = {entry['glob'] for entry in metadata['resources']}
    for dependency in provenance['resolvedDependencies']:
        if not dependency['path'].startswith('com/commercetools/sdk/'): continue
        parts = dependency['path'].split('/')
        jar = '/app/lib/'+parts[-1] if args.framework == 'micronaut' else '/app/lib/main/' + '.'.join(parts[:-3]) + '.' + parts[-1]
        data = subprocess.check_output(['docker','run','--rm','--entrypoint','cat',image,jar])
        if hashlib.sha256(data).hexdigest() != dependency['sha256']: raise ValueError('SDK dependency hash mismatch: ' + jar)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for path in archive.namelist():
                if not path.startswith(tuple('META-INF/services/' + prefix for prefix in PREFIXES)): continue
                resources.add(path)
                names = [line.split('#')[0].strip() for line in archive.read(path).decode().splitlines()]
                providers[path] = [name for name in names if name]
                for name in providers[path]:
                    entry = reflection.setdefault(name, {'type':name})
                    constructor = {'name':'<init>','parameterTypes':[]}
                    methods = entry.setdefault('methods', [])
                    if constructor not in methods: methods.append(constructor)
    metadata['reflection'] = sorted(reflection.values(), key=lambda entry:entry['type'])
    metadata['resources'] = [{'glob':path} for path in sorted(resources)]
    if not metadata['reflection'] or not metadata['resources']: raise ValueError('Empty upstream SDK metadata')
    target = ROOT/f'{project}/src/main/resources/META-INF/native-image/bench/{project}'
    target.mkdir(parents=True, exist_ok=True)
    (target/'reachability-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    (target/'trace-inputs.json').write_text(json.dumps({
        'sourceImage':diagnostic['sourceImage'],'sdkValidationImage':image,
        'sdkJars':inputs,'tracedSdkDependencies':relevant(diagnostic['resolvedDependencies']),
        'allCapabilitiesPassed':True,
        'agentSha256':diagnostic['agentSha256'],'traceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'included':{key:len(value) for key,value in metadata.items()},
        'declaredSdkProviders':providers,
        'scope':'Observed upstream commercetools, AsyncHttpClient, Jackson 3 and money types/resources, plus SDK-declared service providers; '
                + ('observed Firebase/auth/API-client/Firestore reflection; ' if args.framework == 'micronaut' else '')
                + 'no GuicedEE wrapper metadata'
    },indent=2)+'\n')
    print({key:len(value) for key,value in metadata.items()})


if __name__ == '__main__': main()
