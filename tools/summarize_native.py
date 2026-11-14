"""Summarize an eligible native batch, retaining ranges and immutable image identities."""
import argparse
import json
from pathlib import Path
import re
import statistics


def sdk_evidence(variants, provenances):
    """Accept deliberate packaging differences only when each image proves its declared inputs."""
    by_variant = {}
    by_mode = {}
    workloads = set()
    for variant in variants:
        name = variant['id']
        mode = variant.get('dependencyMode', 'wrapped')
        provenance = provenances[name]
        if provenance.get('dependencyMode', 'wrapped') != mode:
            raise ValueError('Image dependency mode differs from requested variant: ' + name)
        sources = provenance['sourcesAtImageBuild']
        workload = {s['path']: s['sha256'] for s in sources
                    if s['path'].startswith('common/src/main/java/bench/') and s['path'].endswith('.java')}
        if not workload: raise ValueError('Missing shared business source evidence: ' + name)
        workloads.add(json.dumps(workload, sort_keys=True))
        if mode == 'standard':
            jars = provenance['sdkJars']
            prefixes = {'firebase-admin':'com/google/firebase/firebase-admin/',
                        'commercetools':'com/commercetools/sdk/commercetools-sdk-java-api/'}
            sdk = {}
            for label, prefix in prefixes.items():
                matches = [entry for entry in jars if entry['path'].startswith(prefix)]
                if len(matches) != 1: raise ValueError('Missing/ambiguous upstream SDK: ' + label)
                sdk[label] = matches[0]['sha256']
            if any(entry['path'].startswith('com/guicedee/') for entry in provenance['resolvedDependencies']):
                raise ValueError('GuicedEE dependency in standard Quarkus image')
        else:
            source = next(s for s in sources if s['path'] == 'quarkus-native/native-metadata-inputs.json')
            sdk = {entry['sdk']:entry['jarSha256'] for entry in json.loads(source['content'])}
        by_variant[name] = sdk
        by_mode.setdefault(mode, set()).add(json.dumps(sdk, sort_keys=True))
    if len(workloads) != 1: raise ValueError('Shared business sources differ')
    if any(len(hashes) != 1 for hashes in by_mode.values()): raise ValueError('SDK compiler inputs differ within a dependency mode')
    return {'sdkJarsByVariant':by_variant,
            'sdkHashesMatch':len({json.dumps(s,sort_keys=True) for s in by_variant.values()}) == 1,
            'dependencyComparison':'independent-upstream-vs-wrapped' if len(by_mode) > 1 else next(iter(by_mode)),
            'sharedBusinessSourcesMatch':True}


def summarize(directory):
    summary=json.loads((directory/'summary.json').read_text())
    environment=json.loads((directory/'environment.json').read_text())
    result = calculate(summary, environment, directory.name)
    (directory/'native-summary.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def calculate(summary, environment, batch):
    if not summary['eligibleComparison'] or any(v['runtime']!='native' for v in summary['variants']):
        raise ValueError('Expected a complete, eligible native comparison')
    result={'batch':batch,'eligibleComparison':True,'variants':{},'sdkJarsByVariant':{}}
    rows=summary['runs']
    result['capabilityChecksPassed']=sum(c['passed'] for row in rows for c in row['checks'].values())
    result['measuredRequests']=sum(len(row['samples']) for row in rows)
    result['failedMeasuredRequests']=sum(not sample['ok'] for row in rows for sample in row['samples'])
    for variant in summary['variants']:
        name=variant['id']; runs=[row for row in rows if row['variant']==name]
        item={'runs':len(runs),'image':environment['images'][name],
              'imageBytes':environment['imageSizeBytes'][name]}
        for key in ['launchToReadyMs','firstBusinessMs','launchToFirstBusinessMs','firstOpenApiJsonMs']:
            values=[row[key] for row in runs]
            item[key]={'median':statistics.median(values),'min':min(values),'max':max(values)}
        item['warm']={key:statistics.median(row['warm'][key] for row in runs) for key in ['p50Ms','p95Ms','p99Ms']}
        # compare.py records cpu.stat, memory.peak, memory.current, memory.events in this order.
        memory=[[int(line) for line in row['containerStats'].splitlines() if line.isdigit()] for row in runs]
        if any(len(values)!=2 for values in memory): raise ValueError('Missing cgroup memory evidence')
        item['peakContainerMemoryBytes']=statistics.median(values[0] for values in memory)
        item['endContainerMemoryBytes']=statistics.median(values[1] for values in memory)
        details=environment['nativeRuntimeDetailsByVariant'][name]
        item['executableBytes']=int(re.search(r'(?m)^(\d+) /app/application\s*$',details)[1])
        item['compilerVersion']=details.splitlines()[0]
        result['variants'][name]=item
    result.update(sdk_evidence(summary['variants'], environment['imageBuildProvenance']))
    for name,item in result['variants'].items():
        print(name, 'ready',round(item['launchToReadyMs']['median'],2),
              'first business',round(item['launchToFirstBusinessMs']['median'],2),
              'peak MiB',round(item['peakContainerMemoryBytes']/2**20,2),
              'ELF MiB',round(item['executableBytes']/2**20,2))
    return result


def combine(directories, output):
    if len({directory.resolve() for directory in directories}) != len(directories):
        raise ValueError('A batch must not be counted twice')
    summaries = [json.loads((directory/'summary.json').read_text()) for directory in directories]
    environments = [json.loads((directory/'environment.json').read_text()) for directory in directories]
    for summary, environment in zip(summaries, environments):
        if not summary['eligibleComparison'] or any(row.get('instrumented') for row in summary['runs']):
            raise ValueError('Every batch must be complete and uninstrumented')
        for key in ['images','flags','cpuQuota','profile','platform']:
            if environment[key] != environments[0][key]: raise ValueError('Batches differ: ' + key)
        sdk_evidence(summary['variants'], environment['imageBuildProvenance'])
    merged = dict(summaries[0], runs=[dict(row, sourceBatch=directory.name)
                  for directory, summary in zip(directories, summaries) for row in summary['runs']])
    result = calculate(merged, environments[0], 'combined')
    result['batches'] = [directory.name for directory in directories]
    result['initialOrders'] = [[variant['id'] for variant in summary['variants']] for summary in summaries]
    result['aggregation'] = 'Medians of all fresh starts; warm percentiles are medians of per-start percentiles; no runs removed'
    (output or directories[-1]/'combined-native-summary.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('directories',type=Path,nargs='+')
    parser.add_argument('--output',type=Path,help='Combined JSON destination when passing multiple batches')
    args = parser.parse_args()
    if len(args.directories) == 1: summarize(args.directories[0])
    else: combine(args.directories, args.output)
