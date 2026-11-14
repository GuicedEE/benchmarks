"""Verify the independently compiled modular applications before image packaging."""
from pathlib import Path
import zipfile
import subprocess
import os

ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_ENTRIES = {'bench/guicedee/BenchmarkDiscovery.class',
                     'META-INF/services/com.guicedee.client.services.IGuiceDiscovery'}


def verify_scanner_artifact(spi, scanner):
    with zipfile.ZipFile(spi) as original, zipfile.ZipFile(scanner) as scan:
        assert 'module-info.class' in original.namelist(), 'SPI module descriptor is missing'
        assert 'module-info.class' in scan.namelist(), 'Scanner module descriptor is missing'
        assert all(name in original.namelist() for name in DISCOVERY_ENTRIES), 'SPI discovery registration is missing'
        assert not DISCOVERY_ENTRIES.intersection(scan.namelist()), 'Scanner artifact contains explicit discovery'
        assert b'BenchmarkDiscovery' not in scan.read('module-info.class'), 'Scanner descriptor registers discovery'
        business = {name for name in original.namelist() if name.endswith('.class')
                    and name != 'module-info.class' and name not in DISCOVERY_ENTRIES}
        assert business == {name for name in scan.namelist() if name.endswith('.class') and name != 'module-info.class'}, 'Application class sets differ'
        for name in business:
            assert original.read(name) == scan.read(name), f'Business bytecode differs: {name}'


if __name__ == '__main__':
    verify_scanner_artifact(ROOT/'guicedee/target/comparison-guicedee-1.0-SNAPSHOT.jar',
                            ROOT/'guicedee-scan/target/comparison-guicedee-scan-1.0-SNAPSHOT.jar')
    for application in ['guicedee', 'guicedee-scan']:
        jar = ROOT/application/'target'/('comparison-'+application+'-1.0-SNAPSHOT.jar')
        libraries = ROOT/application/'target/lib'
        subprocess.run(['java', '--module-path', str(jar)+os.pathsep+str(libraries), '--validate-modules'], check=True)
    print('Both module descriptors retained; scanner has no discovery provider; matching business bytecode verified.')
