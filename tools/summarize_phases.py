"""Summarize instrumented runs without promoting them to performance comparisons."""
import argparse
import collections
import json
from pathlib import Path
import statistics


def binding_dot(snapshot):
    lines=['digraph injector {', '  rankdir=LR;', '  node [shape=box];']
    for binding in snapshot['bindings']:
        label=binding['type']+'\n'+binding['module']
        if binding.get('interceptedMethods'): label+='\nAOP: '+', '.join(m['method'] for m in binding['interceptedMethods'])
        lines.append('  '+json.dumps(binding['id'])+' [label='+json.dumps(label)+
                     ',color='+('black' if binding['explicit'] else 'blue')+'];')
        for dependency in binding.get('dependencies',[]):
            if dependency['bindingId']!='not-in-snapshot':
                lines.append('  '+json.dumps(binding['id'])+' -> '+json.dumps(dependency['bindingId'])+';')
    return '\n'.join(lines+['}'])+'\n'


def summarize(directories):
    grouped=collections.defaultdict(list)
    for directory in directories:
        summary=json.loads((directory/'summary.json').read_text())
        if not summary.get('instrumented') or summary['eligibleComparison'] or not summary.get('allDiagnosticsPassed'):
            raise ValueError('Expected a passing diagnostic batch, never a ranked comparison: '+str(directory))
        for row in summary['runs']:
            if not row['phaseEvidence']['verified'] or not row['capabilitiesPassed']:
                raise ValueError('Missing capability or phase evidence')
            grouped[row['variant']].append((directory,row))
    result={'instrumented':True,'performanceComparison':False,'variants':{},
            'note':'Inclusive phase durations overlap. Guice graph is a runtime binding snapshot, not whole-program reachability.'}
    for variant,entries in grouped.items():
        startup=collections.defaultdict(list)
        workload=collections.defaultdict(list)
        inventories=[]
        for directory,row in entries:
            core=row['phaseEvidence']['startup']
            if core:
                per_run=collections.Counter()
                for event in core['events']: per_run[event['phase']]+=event['durationNs']/1e6
                for phase,milliseconds in per_run.items(): startup[phase].append(milliseconds)
                scan=core['scan']
                inventories.append({'scanPerformed':scan['performed'],'scannedClasses':scan.get('classCount',0),
                    'scanModules':sorted(m['name'] for m in scan.get('moduleSources',[])),
                    'classOrigins':sorted({c['origin'] for c in scan.get('classes',[])}),
                    'resourcesByOrigin':scan.get('resourcesByOrigin',{}),
                    'bindings':core['injector']['bindingCount'], 'explicitBindings':core['injector']['explicitBindingCount']})
                (directory/f"{variant}-{row['run']}-bindings.dot").write_text(binding_dot(core['injector']),encoding='utf-8')
            per_run_workload=collections.Counter()
            for operation in row['phaseEvidence']['workload']:
                for event in operation['events']: per_run_workload[event['phase']]+=event['durationNs']/1e6
            for phase,milliseconds in per_run_workload.items(): workload[phase].append(milliseconds)
        result['variants'][variant]={'runs':len(entries),
            'startupMedianMs':{k:statistics.median(v) for k,v in sorted(startup.items())},
            'workloadMedianMs':{k:statistics.median(v) for k,v in sorted(workload.items())},
            'inventories':inventories,
            'workloadConstructionsPerRun':[sum(o['operation']=='workload-construction' for o in row['phaseEvidence']['workload']) for _,row in entries],
            'rows':[str(directory/f"{variant}-{row['run']}.json") for directory,row in entries],
            'imageIds':sorted({row['container']['image'] for _,row in entries})}
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directories',nargs='+',type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    result=summarize(args.directories)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    for name,data in result['variants'].items():
        print(name, 'runs='+str(data['runs']))
        print('Startup:',{k:round(v,2) for k,v in data['startupMedianMs'].items() if not k.startswith(('provision:','pre-hook','post-hook'))})
        print('SDK:',{k:round(v,2) for k,v in data['workloadMedianMs'].items()})
        if data['inventories']: print('Inventory:',data['inventories'][0])
