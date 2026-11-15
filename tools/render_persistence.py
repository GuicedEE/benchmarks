"""Publish one complete persistence cohort and render its current comparison grids."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import statistics
import subprocess
import sys
from compare import percentile
from compare_persistence import validate, VARIANTS
from render_performance import table, replace_sections, stats

ROOT = Path(__file__).resolve().parents[1]
LATEST = ROOT/'results/latest/persistence.json'
LABELS = dict(guicedee='GuicedEE reactive stateless',quarkus='Quarkus ORM / Narayana')


def collect(raw):
    validate(raw)
    result = dict(measuredAt=raw['measuredAt'],batch=raw['batch'],profile=raw['profile'],
                  runs=raw['runs'],requests=raw['requests'],warmup=raw['warmup'],variants={})
    for variant in VARIANTS:
        rows = [r for r in raw['starts'] if r['variant']==variant]
        item = dict(label=LABELS[variant],image=raw['images'][variant],checks=sum(len(r['checks']) for r in rows),
                    ormVersion=rows[0]['readiness']['ormVersion'])
        for key in ['launchToReadyMs','firstTransactionMs','launchToFirstTransactionMs','peakMemoryBytes','endMemoryBytes']:
            item[key] = stats([r[key] for r in rows])
        for key in ['read','create','update','delete','cycle']:
            per_start = [r['readsMs'] if key == 'read' else [c[key+'Ms'] for c in r['cycles']] for r in rows]
            item[key] = dict(p50Ms=statistics.median(percentile(v,.5) for v in per_start),
                             p95Ms=statistics.median(percentile(v,.95) for v in per_start),
                             p99Ms=statistics.median(percentile(v,.99) for v in per_start),
                             samples=sum(len(v) for v in per_start))
        result['variants'][variant] = item
    return result


def render(data, raw):
    values = data['variants']
    a,b = (values[name] for name in VARIANTS)
    delta = lambda x,y: f'{(x/y-1)*100:+.1f}%'
    rows = []
    for name in VARIANTS:
        item=values[name]; startup=item['launchToFirstTransactionMs']
        rows.append([item['label'],data['runs'],f"{item['launchToReadyMs']['median']/1000:.3f}",
                     f"{item['firstTransactionMs']['median']:.2f}",f"{startup['median']/1000:.3f}",
                     f"{startup['minimum']/1000:.3f}–{startup['maximum']/1000:.3f}",
                     f"{item['peakMemoryBytes']['median']/2**20:.2f}",item['ormVersion']])
    content = (f"Measured **{data['measuredAt'][:10]}**, **{data['profile']} JVM profile**, batch `{data['batch']}`. "
               f"**{2*data['runs']} fresh starts / {a['checks']+b['checks']} passing checks**. "
               f"Each start has {data['warmup']} warmup reads and CRUD cycles, then {data['requests']} measured reads "
               f"and {data['requests']} measured CRUD cycles. All samples are retained.\n\n"
               '![PostgreSQL startup and transaction latency](docs/persistence.svg)\n\n'
               +table(['Application','Starts','DB-ready (s)','First transaction (ms)','Launch to committed graph (s)',
                       'Full startup min–max (s)','Peak charged memory (MiB)','Hibernate ORM'],rows))
    rows=[]
    for label,key in [('Joined graph read','read'),('Create 15 rows','create'),('Update 15 rows','update'),
                      ('Delete 15 rows','delete'),('Complete CRUD cycle','cycle')]:
        rows.append([label,*[f'{v[key][p]:.2f}' for v in [a,b] for p in ['p50Ms','p95Ms','p99Ms']],
                     delta(a[key]['p50Ms'],b[key]['p50Ms'])])
    content += '\n\n'+table(['Operation','GuicedEE p50 (ms)','p95','p99','Quarkus p50 (ms)','p95','p99','GuicedEE p50 difference'],rows)
    rows=[]
    for row in raw['starts']:
        rows.append([LABELS[row['variant']],row['run'],f"{percentile(row['readsMs'],.5):.2f}",
                     *[f"{percentile([c[key+'Ms'] for c in row['cycles']],.5):.2f}"
                       for key in ['create','update','delete','cycle']]])
    content += ('\n\nPer-start warm medians expose the variation within this small, CPU-capped cohort. '
                'No individual start is dropped.\n\n'
                +table(['Application','Start','Read p50 (ms)','Create p50 (ms)','Update p50 (ms)',
                        'Delete p50 (ms)','CRUD cycle p50 (ms)'],rows))
    update_medians = {name:[percentile([c['updateMs'] for c in row['cycles']],.5)
                           for row in raw['starts'] if row['variant']==name] for name in VARIANTS}
    content += (f"\n\nUpdate p50 spans **{min(update_medians['guicedee']):.2f}–{max(update_medians['guicedee']):.2f} ms** for GuicedEE "
                f"and **{min(update_medians['quarkus']):.2f}–{max(update_medians['quarkus']):.2f} ms** for Quarkus across starts. ")
    if all(any(line.startswith('nr_throttled ') and int(line.split()[1]) > 0
               for line in row['cpuStat'].splitlines()) for row in raw['starts']):
        content += ('Every container records CPU throttling; these measurements do not separate database work from quota waits. ')
    content += 'Individual operation medians do not add up to the median of a complete CRUD cycle.'
    content += (f"\n\nGuicedEE's launch-to-commit median differs by **{delta(a['launchToFirstTransactionMs']['median'],b['launchToFirstTransactionMs']['median'])}**; "
                f"its peak charged container memory differs by **{delta(a['peakMemoryBytes']['median'],b['peakMemoryBytes']['median'])}**. "
                'Negative differences mean less time or memory. Warm percentiles are medians of per-start percentiles. '
                'A CRUD cycle includes four HTTP requests, three completed write transactions and one read without an explicit transaction; its latency is not one transaction. '
                'Database memory is separate from the application memory figures.\n\n'
                'Both full-JDK applications use the same immutable JDK base, schema, graph/query source and five-connection limit. '
                'The database runs separately at 2 CPU / 1 GiB with durable commit settings. '
                'Application limits are 250m CPU / 500 MiB. These are different persistence patterns: managed stateful JPA/Narayana '
                'versus explicit reactive stateless operations. This is not a distributed-transaction, saturation-throughput, '
                'native or jlink result.\n\n'
                '[Protocol and reproduction](persistence/README.md) · [All current raw samples](results/latest/persistence.json) · '
                '[CSV](docs/persistence-performance.csv)\n\n')
    content += table(['Application','Immutable image'],[[values[n]['label'],f"`{values[n]['image']}`"] for n in VARIANTS])
    content += f"\n\nPostgreSQL image: `{raw['postgres']['image']}`. JDK base: `{raw['buildInputs']['guicedee']['javaImage']}`."
    return content


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish',type=Path,help='Replace current raw evidence with this complete passing cohort')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    if args.publish and args.check: parser.error('--publish and --check are mutually exclusive')
    if args.publish:
        raw=json.loads(args.publish.read_text(encoding='utf-8'))
        validate(raw)
        raw['inputSha256']=hashlib.sha256(args.publish.read_bytes()).hexdigest()
        LATEST.write_text(json.dumps(raw,separators=(',',':'))+'\n',encoding='utf-8',newline='\n')
        subprocess.run([sys.executable,ROOT/'tools/verify_latest.py','--refresh'],check=True)
    raw=json.loads(LATEST.read_text(encoding='utf-8'))
    data=collect(raw)
    data['inputSha256']=hashlib.sha256(LATEST.read_bytes()).hexdigest()
    output=io.StringIO(newline='');writer=csv.writer(output,lineterminator='\n')
    writer.writerow(['variant','profile','starts','metric','median','minimum','maximum','unit'])
    for name,item in data['variants'].items():
        for key in ['launchToReadyMs','firstTransactionMs','launchToFirstTransactionMs','peakMemoryBytes','endMemoryBytes']:
            v=item[key];writer.writerow([name,data['profile'],data['runs'],key,v['median'],v['minimum'],v['maximum'], 'bytes' if key.endswith('Bytes') else 'ms'])
        for key in ['read','create','update','delete','cycle']:
            for pct in ['p50Ms','p95Ms','p99Ms']:
                writer.writerow([name,data['profile'],data['runs'],key+'_'+pct,item[key][pct],'','','ms'])
    outputs={ROOT/'RESULTS.md':replace_sections(ROOT/'RESULTS.md',{'persistence':render(data,raw)}),
             ROOT/'docs/persistence-performance.json':json.dumps(data,indent=2)+'\n',
             ROOT/'docs/persistence-performance.csv':output.getvalue()}
    for path,content in outputs.items():
        if args.check:
            if path.read_text(encoding='utf-8')!=content: raise ValueError(f'Stale persistence report: {path}')
        else:path.write_text(content,encoding='utf-8',newline='\n')
    if args.check:
        fingerprint=hashlib.sha256((ROOT/'docs/persistence-performance.json').read_bytes()).hexdigest()
        if f'performance-data-sha256: {fingerprint}' not in (ROOT/'docs/persistence.svg').read_text(encoding='utf-8'):
            raise ValueError('Stale persistence chart')
    print(f"{'Verified' if args.check else 'Rendered'} current persistence comparison: {len(raw['starts'])} starts")


if __name__=='__main__':main()
