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
            expected, actual = original.read(name), scan.read(name)
            if name == 'bench/guicedee/Main.class':
                # The launcher declares its discovery mode via @GuiceOptions. Only
                # that UTF-8 constant may differ; all code and other settings match.
                actual = actual.replace(b'\x01\x00\x04SCAN', b'\x01\x00\x03SPI')
            assert expected == actual, f'Business bytecode differs: {name}'


if __name__ == '__main__':
    verify_scanner_artifact(ROOT/'guicedee/target/comparison-guicedee-1.0-SNAPSHOT.jar',
                            ROOT/'guicedee-scan/target/comparison-guicedee-scan-1.0-SNAPSHOT.jar')
    import sys
    applications = ['guicedee', 'guicedee-scan']
    if '--cdi-config' in sys.argv:
        verify_scanner_artifact(ROOT/'guicedee-cdi-spi/target/comparison-guicedee-cdi-spi-1.0-SNAPSHOT.jar',
                                ROOT/'guicedee-cdi/target/comparison-guicedee-cdi-1.0-SNAPSHOT.jar')
        applications += ['guicedee-cdi', 'guicedee-cdi-spi']
    for application in applications:
        jar = ROOT/application/'target'/('comparison-'+application+'-1.0-SNAPSHOT.jar')
        libraries = ROOT/application/'target/lib'
        subprocess.run(['java', '--module-path', str(jar)+os.pathsep+str(libraries), '--validate-modules'], check=True)
    print('Module descriptors retained; scanner has no discovery provider; matching bytecode verified except launcher discovery enum.')
