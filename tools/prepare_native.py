"""Check that the separately built native project compiles the existing Quarkus adapter."""
from pathlib import Path
import hashlib
import json
import os
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def verify_quarkus_adapter(jvm, native):
    with zipfile.ZipFile(jvm) as a, zipfile.ZipFile(native) as b:
        classes = {n for n in a.namelist() if n.startswith('bench/quarkus/') and n.endswith('.class')}
        assert classes, 'JVM adapter classes are missing'
        assert classes == {n for n in b.namelist() if n.startswith('bench/quarkus/') and n.endswith('.class')}, 'Native adapter class sets differ'
        for name in classes:
            assert a.read(name) == b.read(name), f'Native adapter bytecode differs: {name}'
        assert a.read('application.properties') == b.read('application.properties'), 'Application defaults differ'


def verify_trace_inputs():
    manifest=json.loads((ROOT/'quarkus-native/native-trace-inputs.json').read_text())
    dependencies={Path(p).name:Path(p) for p in (ROOT/'guicedee/target/classpath.txt').read_text().strip().split(os.pathsep)}
    for entry in manifest['sdkJars']:
        assert hashlib.sha256(dependencies[entry['name']].read_bytes()).hexdigest()==entry['sha256'], \
            'SDK changed; rerun trace_native.py and import_native_trace.py: '+entry['name']


if __name__ == '__main__':
    verify_quarkus_adapter(ROOT/'quarkus/target/comparison-quarkus-1.0-SNAPSHOT.jar',
                           ROOT/'quarkus-native/target/comparison-quarkus-native-1.0-SNAPSHOT.jar')
    verify_trace_inputs()
    print('Native and JVM Quarkus projects compile identical adapter bytecode and application defaults.')
