"""Capture packaged inputs and fixture sources before building immutable benchmark images."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def capture():
    sources = []
    for path in ROOT.rglob('*'):
        relative = path.relative_to(ROOT)
        if any(part in ['target', 'node_modules', 'repository', 'results', '.idea', '.git', '__pycache__', 'analysis'] for part in relative.parts):
            continue
        if path.is_file() and (path.suffix in ['.java', '.py', '.xml', '.properties', '.ps1', '.sh']
                              or path.name in ['Dockerfile', '.env', 'jlink-modules.txt','native-metadata-inputs.json','native-trace-inputs.json',
                                               'native-resources.txt', 'native-excluded-providers.txt'] or 'META-INF' in relative.parts):
            data = path.read_bytes()
            sources.append({'path': relative.as_posix(), 'sha256': hashlib.sha256(data).hexdigest(),
                            'content': data.decode('utf-8')})
    jars = []
    for directory in [ROOT/'guicedee/target', ROOT/'guicedee-scan/target', ROOT/'quarkus/target/quarkus-app', ROOT/'quarkus-native/target/quarkus-app']:
        for path in directory.rglob('*.jar'):
            jars.append({'path': path.relative_to(ROOT).as_posix(),
                         'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    return {'sourcesAtImageBuild': sources, 'packagedJars': jars,
            'note': 'Source snapshot at image packaging; build the Maven reactor before packaging images.'}


if __name__ == '__main__':
    (ROOT/'docker/build-provenance.json').write_text(json.dumps(capture(), indent=2)+'\n', encoding='utf-8')
