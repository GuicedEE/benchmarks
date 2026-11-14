"""Explicit artifacts and runtime modes used by the comparison matrix."""


def select_variants(framework='both', discovery='both', runtime='jre', native=False, quarkus_dependencies='wrapped'):
    if quarkus_dependencies not in ['wrapped', 'standard']:
        raise ValueError('Unknown Quarkus dependency mode')
    bases = []
    if framework in ['both', 'guicedee']:
        if discovery in ['both', 'spi']: bases.append(('guicedee', 'guicedee', 'spi'))
        if discovery in ['both', 'scan']: bases.append(('guicedee-scan', 'guicedee', 'scan'))
    if framework in ['both', 'quarkus']: bases.append(('quarkus', 'quarkus', None))
    modes = ['jre', 'jlink'] if runtime == 'both' else [] if runtime == 'native' else [runtime]
    variants = [{'id': name + ('-jlink' if mode == 'jlink' else ''), 'framework': family,
             'discovery': discovery_mode, 'runtime': mode}
            for mode in modes for name, family, discovery_mode in bases
            if mode != "jlink" or family == "guicedee"]
    if native or runtime == 'native':
        if framework in ['both','guicedee'] and discovery in ['both','spi']:
            variants.append({'id':'guicedee-native','framework':'guicedee','discovery':'spi','runtime':'native'})
        if framework in ['both','quarkus']:
            variants.append({'id':'quarkus-native', 'framework':'quarkus', 'discovery':None, 'runtime':'native'})
    if quarkus_dependencies == 'standard':
        for variant in variants:
            if variant['framework'] == 'quarkus':
                variant['id'] = 'quarkus-standard' + ('-native' if variant['runtime'] == 'native' else '')
                variant['dependencyMode'] = 'standard'
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
    if variant['runtime']=='native': return 'guicedee-native'
    return 'guicedee-scan' if variant['discovery'] == 'scan' else 'guicedee'
