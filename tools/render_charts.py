"""Render the current startup and build charts (optional dependency: matplotlib)."""
import json
import hashlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]


def color(name):
    return '#167c80' if name.startswith('guicedee') else '#bd661c' if name.startswith('micronaut') else '#5950a3'


def save(fig, name):
    svg = ROOT/f'docs/{name}.svg'
    fig.savefig(svg, metadata={'Date':None}, facecolor='white')
    plt.close(fig)
    dataset = 'persistence-performance.json' if name == 'persistence' else 'current-performance.json'
    fingerprint = hashlib.sha256((ROOT/'docs'/dataset).read_bytes()).hexdigest()
    content = '\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())
    svg.write_text(content+'\n<!-- performance-data-sha256: '+fingerprint+' -->\n',
                   encoding='utf-8', newline='\n')


def build_chart(data):
    values = data['builds']['variants']
    jvm = ['guicedee', 'guicedee-scan', 'guicedee-cdi-spi', 'guicedee-cdi', 'quarkus-standard', 'micronaut']
    groups = [(jvm, 'compile', 'Clean Java compilation'),
              (jvm, 'package', 'Complete JVM packaging'),
              (['guicedee-jlink', 'guicedee-scan-jlink', 'guicedee-cdi-spi-jlink', 'guicedee-cdi-jlink',
                'guicedee-native', 'guicedee-cdi-native', 'quarkus-standard-native','micronaut-native'],
               'package', 'jlink and native packaging')]
    labels = {'guicedee':'GuicedEE SPI', 'guicedee-scan':'GuicedEE scanner', 'quarkus-standard':'Quarkus',
              'guicedee-jlink':'GuicedEE SPI jlink', 'guicedee-scan-jlink':'GuicedEE scanner jlink',
              'guicedee-native':'GuicedEE SPI native', 'quarkus-standard-native':'Quarkus native',
              'micronaut':'Micronaut','micronaut-native':'Micronaut native',
              'guicedee-cdi-spi':'GuicedEE CDI SPI', 'guicedee-cdi':'GuicedEE CDI scanner',
              'guicedee-cdi-spi-jlink':'GuicedEE CDI SPI jlink', 'guicedee-cdi-jlink':'GuicedEE CDI scanner jlink',
              'guicedee-cdi-native':'GuicedEE CDI SPI native'}
    fig, axes = plt.subplots(1, 3, figsize=(18, 6.4))
    for ax, (names, goal, title) in zip(axes, groups):
        names = [name for name in names if name in values]
        seconds = [values[name][goal]['median'] for name in names]
        errors = [[values[name][goal]['median']-values[name][goal]['minimum'] for name in names],
                  [values[name][goal]['maximum']-values[name][goal]['median'] for name in names]]
        maximum = max(values[name][goal]['maximum'] for name in names)
        ax.barh(range(len(names)), seconds, xerr=errors, capsize=3, height=.6,
                color=[color(name) for name in names])
        ax.set_yticks(range(len(names)), [labels[name] for name in names])
        ax.invert_yaxis()
        ax.set_xlim(0, maximum*1.32)
        ax.set_xlabel('Wall time (seconds)')
        ax.set_title(title, loc='left', fontsize=11, fontweight='bold')
        ax.grid(axis='x', alpha=.15)
        ax.set_axisbelow(True)
        ax.spines[['top','right','left']].set_visible(False)
        for index, (name, value) in enumerate(zip(names, seconds)):
            ax.text(values[name][goal]['maximum']+maximum*.02, index, f'{value:.2f} s', va='center', fontsize=9)
    fig.suptitle('Build cost by artifact type', x=.02, ha='left', fontsize=15, fontweight='bold')
    fig.text(.02,.02, f"Medians and min–max of {data['builds']['runs']} clean, offline builds per task · warm dependency cache · new Maven process each time\n"
             'Same Linux JDK 25 / Maven 4 toolchain · no runtime CPU quota · package includes compilation; do not add columns. Panels use different scales.\n'
             'Framework-native packaging with upstream SDKs for Quarkus and Micronaut.', fontsize=9)
    fig.tight_layout(rect=(0,.13,1,.94))
    save(fig, 'builds')


def main():
    data = json.loads((ROOT/'docs/current-performance.json').read_text())
    labels_by_name = {
        'guicedee':'GuicedEE SPI / JVM', 'guicedee-scan':'GuicedEE scanner / JVM',
        'guicedee-cdi-spi':'GuicedEE CDI SPI / JVM', 'guicedee-cdi':'GuicedEE CDI scanner / JVM',
        'quarkus-standard':'Quarkus / JVM', 'micronaut':'Micronaut / JVM',
        'guicedee-jlink':'GuicedEE SPI / jlink', 'guicedee-scan-jlink':'GuicedEE scanner / jlink',
        'guicedee-cdi-spi-jlink':'GuicedEE CDI SPI / jlink', 'guicedee-cdi-jlink':'GuicedEE CDI scanner / jlink',
        'guicedee-native':'GuicedEE SPI / native', 'guicedee-cdi-native':'GuicedEE CDI SPI / native',
        'quarkus-standard-native':'Quarkus / native', 'micronaut-native':'Micronaut / native'}
    available = {**data['groups']['jvm-default']['variants'], **data['groups']['native-standard']['variants']}
    names = [name for name in labels_by_name if name in available]
    labels = [labels_by_name[name] for name in names]
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10, 'svg.hashsalt':'guicedee-benchmarks'})
    fig, axes = plt.subplots(1, 2, figsize=(14, 9), sharey=True, sharex=True)
    def profile(group):
        return {**data['groups'][group]['variants'], **data['groups']['native-standard']['variants']}
    maximum = max(profile(group)[name]['launchToFirstBusinessMs']['median']/1000
                  for group in ['jvm-default','jvm-c1'] for name in names)
    for ax, group, title in zip(axes, ['jvm-default','jvm-c1'], ['Default JVM profile','Equal C1 JVM profile']):
        values = profile(group)
        seconds = [values[name]['launchToFirstBusinessMs']['median']/1000 for name in names]
        colors = [color(name) for name in names]
        ax.barh(range(len(names)), seconds, color=colors, height=.65)
        ax.set_yticks(range(len(names)), labels)
        ax.set_xlim(0, maximum*1.27)
        ax.set_xlabel('Launch to completed business response (seconds)')
        ax.set_title(title, loc='left', fontweight='bold')
        ax.grid(axis='x', alpha=.15)
        ax.set_axisbelow(True)
        ax.spines[['top','right','left']].set_visible(False)
        for index, value in enumerate(seconds):
            ax.text(value+maximum*.02, index, f'{value:.3f} s', va='center', fontsize=9)
    axes[0].invert_yaxis()
    fig.suptitle('GuicedEE, Quarkus and Micronaut', x=.02, ha='left', fontsize=15, fontweight='bold')
    native_starts = data['groups']['native-standard']['variants']['guicedee-native']['starts']
    fig.text(.02,.02,'250m CPU / 500 MiB · 3 JVM starts per mode/profile · commercetools + GraphQL + Firestore\n'
             f'Native rows repeat the separate native cohort ({native_starts} starts/variant); native has no JIT.\n'
             'jlink workload passes, but the SDK scanner finds zero URLs: full SDK model discovery is not established.', fontsize=9)
    fig.tight_layout(rect=(0,.16,1,.94))
    save(fig, 'startup')
    build_chart(data)
    persistence_path = ROOT/'docs/persistence-performance.json'
    if persistence_path.exists():
        persistence_chart(json.loads(persistence_path.read_text()))


def persistence_chart(data):
    variants = data['variants']
    names = ['guicedee','quarkus','micronaut']
    has_control = 'parserControl' in data
    fig, axes = plt.subplots(2 if has_control else 1,2 if has_control else 3,
                             figsize=(13,7.6 if has_control else 4.4))
    axes = axes.ravel()
    metrics = [('Launch to committed graph','launchToFirstTransactionMs','median',1000,'Seconds'),
               ('Joined read, warm p50','read','p50Ms',1,'Milliseconds'),
               ('CRUD cycle, warm p50','cycle','p50Ms',1,'Milliseconds')]
    for ax,(title,key,stat,scale,unit) in zip(axes,metrics):
        values=[variants[n][key][stat]/scale for n in names]
        upper=values
        error=None
        if key == 'launchToFirstTransactionMs':
            lower=[variants[n][key]['minimum']/scale for n in names]
            upper=[variants[n][key]['maximum']/scale for n in names]
            error=[[v-low for v,low in zip(values,lower)],[high-v for v,high in zip(values,upper)]]
        ax.barh(range(len(names)),values,color=[color(n) for n in names],height=.5,
                xerr=error,ecolor='#374151',capsize=3)
        ax.set_yticks(range(len(names)),['GuicedEE stateless','Quarkus Narayana','Micronaut ORM'])
        ax.invert_yaxis();ax.set_xlim(0,max(upper)*1.35)
        ax.set_title(title+f'\nGuicedEE vs Quarkus {(values[0]/values[1]-1)*100:+.1f}%',loc='left',fontsize=11,fontweight='bold');ax.set_xlabel(unit)
        ax.spines[['top','right','left']].set_visible(False);ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
        for index,value in enumerate(values):ax.text(upper[index]+max(upper)*.025,index,f'{value:.3f}',va='center',fontsize=9)
    if has_control:
        ax = axes[3]
        startup = [variants['guicedee']['launchToFirstTransactionMs'],data['parserControl']['launchToFirstTransactionMs']]
        values = [s['median']/1000 for s in startup]
        upper = [s['maximum']/1000 for s in startup]
        errors = [[(s['median']-s['minimum'])/1000 for s in startup],
                  [(s['maximum']-s['median'])/1000 for s in startup]]
        ax.barh([0,1],values,color=['#167c80','#708892'],height=.5,xerr=errors,ecolor='#374151',capsize=3)
        ax.set_yticks([0,1],['Fast parser','Hibernate fallback'])
        ax.invert_yaxis();ax.set_xlim(0,max(upper)*1.35)
        ax.set_title(f'Identical-image parser control\nFast vs fallback {(values[0]/values[1]-1)*100:+.1f}%',
                     loc='left',fontsize=11,fontweight='bold')
        ax.set_xlabel('Launch to committed graph (seconds)')
        ax.spines[['top','right','left']].set_visible(False);ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
        for index,value in enumerate(values):ax.text(upper[index]+max(upper)*.025,index,f'{value:.3f}',va='center',fontsize=9)
    fig.suptitle('PostgreSQL: 15 entities, 19 foreign keys',x=.02,ha='left',fontsize=15,fontweight='bold')
    fig.text(.02,.02,f"{data['runs']} fresh starts per application · {data['requests']} measured reads and CRUD cycles per start · {data['profile']} JVM profile\n"
             'Apps: 250m CPU / 500 MiB · PostgreSQL: separate 2 CPU / 1 GiB · CRUD cycle = three write transactions and one read, over four HTTP requests\n'
             'Shared schema/model/query · Startup whiskers show min–max, bars show medians · Panels use different scales'
             + ('\nParser control: 3 additional starts, same image, descriptor security enabled for both paths' if has_control else ''),fontsize=9)
    fig.tight_layout(rect=(0,.17,1,.94))
    save(fig,'persistence')


if __name__ == '__main__':
    main()
