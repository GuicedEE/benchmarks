"""Audit the immutable jlink images in the current default-JVM cohort."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def output(*args):
    return subprocess.check_output(list(map(str, args)), text=True)


def main():
    path = ROOT/'results/latest/measurements.json'
    data = json.loads(path.read_text())
    group = data['groups']['jvm-default']
    images = {}
    for batch in group['batches']:
        for name, image in data['batches'][batch]['environment']['images'].items():
            if not name.endswith('-jlink') or group['variants'] and name not in group['variants']:
                continue
            if name in images and images[name] != image:
                raise ValueError('Different jlink images within the current cohort: ' + name)
            images[name] = image
    if not images:
        raise ValueError('No current jlink measurements')
    source = ROOT/'tools/LinkGraphAudit.java'
    audit = dict(measuredAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        auditSourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        performanceComparison=False, images={}, currentGraphs={},
        checks=dict(currentImagesMatchDefaultMatrix=True),
        method=dict(runtimeTreeBytes='du -sb /opt/java/openjdk inside each measured image',
            moduleImageBytes='stat size of /opt/java/openjdk/lib/modules',
            moduleGraph='ModuleFinder.ofSystem and application-root resolve / resolveAndBind against installed providers',
            dockerImageSizeBytes='daemon-local image accounting; not compressed registry size'))
    roots = {'guicedee-jlink': ('spi', 'bench.guicedee'),
             'guicedee-scan-jlink': ('scan', 'bench.guicedee.scan'),
             'guicedee-cdi-spi-jlink': ('cdi-spi', 'bench.guicedee.cdi.spi'),
             'guicedee-cdi-jlink': ('cdi-scan', 'bench.guicedee.cdi')}
    with tempfile.TemporaryDirectory() as temporary:
        subprocess.run(['javac', '--release', '25', '-d', temporary, str(source)], check=True)
        for name, image in images.items():
            mode, module = roots[name]
            info = json.loads(output('docker', 'image', 'inspect', image))[0]
            graph = json.loads(output('docker', 'run', '--rm', '--mount',
                f'type=bind,source={temporary},target=/audit,readonly', '--entrypoint',
                '/opt/java/openjdk/bin/java', image, '-cp', '/audit', 'LinkGraphAudit', module))
            sizes = output('docker', 'run', '--rm', '--entrypoint', 'sh', image, '-c',
                'du -sb /opt/java/openjdk; stat -c %s /opt/java/openjdk/lib/modules').splitlines()
            layers = [int(s.strip().removesuffix('B')) for s in output('docker', 'history',
                '--no-trunc', '--human=false', '--format', '{{.Size}}', image).splitlines()]
            modules = set(graph['modules'])
            audit['images'][mode] = dict(imageId=image, architecture=info['Architecture'], os=info['Os'],
                dockerImageSizeBytes=info['Size'], runtimeTreeBytes=int(sizes[0].split()[0]),
                moduleImageBytes=int(sizes[1]), layerBytes=layers, unpackedLayerBytes=sum(layers),
                moduleCount=len(modules), requiredClosureCount=len(graph['requiredClosure']),
                serviceBoundClosureCount=len(graph['serviceBoundClosure']),
                outsideRequiredClosure=sorted(modules-set(graph['requiredClosure'])),
                outsideServiceBoundClosure=sorted(modules-set(graph['serviceBoundClosure'])))
            audit['currentGraphs'][mode] = graph
            print(name, len(modules), 'modules', audit['images'][mode]['runtimeTreeBytes'], 'bytes')
    data['jlinkAudit'] = audit
    path.write_text(json.dumps(data, separators=(',', ':'))+'\n', encoding='utf-8', newline='\n')
    subprocess.run([sys.executable, ROOT/'tools/verify_latest.py', '--refresh'], check=True)


if __name__ == '__main__':
    main()
