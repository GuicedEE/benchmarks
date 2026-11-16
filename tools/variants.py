"""Explicit artifacts and runtime modes used by the comparison matrix."""


def select_variants(framework='both', discovery='both', runtime='jre', native=False, quarkus_dependencies='wrapped', cdi_config=False):
    if quarkus_dependencies not in ['wrapped', 'standard']:
        raise ValueError('Unknown Quarkus dependency mode')
    if cdi_config and (framework not in ['all', 'both', 'guicedee']):
        raise ValueError('CDI/config requires a GuicedEE framework selection')
    bases = []
    if framework in ['all', 'both', 'guicedee']:
        if discovery in ['both', 'spi']: bases.append(('guicedee', 'guicedee', 'spi'))
        if discovery in ['both', 'scan']: bases.append(('guicedee-scan', 'guicedee', 'scan'))
    if framework in ['all', 'both', 'quarkus']: bases.append(('quarkus', 'quarkus', None))
    if framework in ['all', 'micronaut']: bases.append(('micronaut', 'micronaut', None))
    modes = ['jre', 'jlink'] if runtime == 'both' else [] if runtime == 'native' else [runtime]
    variants = [{'id': name + ('-jlink' if mode == 'jlink' else ''), 'framework': family,
             'discovery': discovery_mode, 'runtime': mode}
            for mode in modes for name, family, discovery_mode in bases
            if mode != "jlink" or family == "guicedee"]
    if cdi_config:
        for mode in modes:
            for name, discovery_mode in [('guicedee-cdi', 'scan'), ('guicedee-cdi-spi', 'spi')]:
                if discovery in ['both', discovery_mode]:
                    variants.append({'id': name + ('-jlink' if mode == 'jlink' else ''),
                                     'framework': 'guicedee', 'discovery': discovery_mode,
                                     'runtime': mode, 'configuration': 'cdi-config'})
        if native or runtime == 'native':
            if discovery == 'scan':
                raise ValueError('Native scanner discovery is unavailable; use SPI for CDI/config native')
            variants.append({'id': 'guicedee-cdi-native', 'framework': 'guicedee',
                             'discovery': 'spi', 'runtime': 'native', 'configuration': 'cdi-config'})
    if native or runtime == 'native':
        if framework in ['all','both','guicedee'] and discovery in ['both','spi']:
            variants.append({'id':'guicedee-native','framework':'guicedee','discovery':'spi','runtime':'native'})
        if framework in ['all','both','quarkus']:
            variants.append({'id':'quarkus-native', 'framework':'quarkus', 'discovery':None, 'runtime':'native'})
        if framework in ['all','micronaut']:
            variants.append({'id':'micronaut-native', 'framework':'micronaut', 'discovery':None, 'runtime':'native'})
    if quarkus_dependencies == 'standard':
        for variant in variants:
            if variant['framework'] == 'quarkus':
                variant['id'] = 'quarkus-standard' + ('-native' if variant['runtime'] == 'native' else '')
                variant['dependencyMode'] = 'standard'
    for variant in variants:
        if variant['framework'] == 'micronaut': variant['dependencyMode'] = 'standard'
    return variants


def runtime_flags(variant, flags):
    # Native has no tiered JIT. Keep heap and processor controls equal and record the distinction.
    return [flag for flag in flags if not flag.startswith('-XX:TieredStopAtLevel=')] if variant['runtime']=='native' else list(flags)


def ordered_variants(variants, run):
    # Rotate each pair of rounds, reversing the second. Rotating on every round
    # AND reversing canceled out for two variants, always running SPI first.
    shift = ((run - 1) // 2) % len(variants)
    order = variants[shift:] + variants[:shift]
    return order if run % 2 else list(reversed(order))


def paired_image_variants(variants, baseline_tag, candidate_tag):
    if baseline_tag == candidate_tag:
        raise ValueError('Baseline and candidate tags must differ')
    return [dict(v,id=v['id']+'-'+role,imageArtifact=v['id'],imageTag=tag,comparisonRole=role)
            for v in variants for role,tag in [('before',baseline_tag),('after',candidate_tag)]]


def guicedee_jar(variant):
    return 'comparison-' + guicedee_project(variant) + '-1.0-SNAPSHOT.jar'


def guicedee_project(variant):
    if variant.get('configuration') == 'cdi-config':
        return 'guicedee-cdi-native' if variant['runtime'] == 'native' else 'guicedee-cdi-spi' if variant['discovery'] == 'spi' else 'guicedee-cdi'
    if variant['runtime']=='native': return 'guicedee-native'
    return 'guicedee-scan' if variant['discovery'] == 'scan' else 'guicedee'


def guicedee_module(variant):
    if variant.get("configuration") == "cdi-config":
        return "bench.guicedee.cdi.spi" if variant["discovery"] == "spi" else "bench.guicedee.cdi"
    return "bench.guicedee.scan" if variant["discovery"] == "scan" else "bench.guicedee"
