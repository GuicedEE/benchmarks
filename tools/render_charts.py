"""Render the current startup chart (optional report dependency: matplotlib)."""
import json
import hashlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]


def main():
    data = json.loads((ROOT/'docs/current-performance.json').read_text())
    names = ['guicedee','guicedee-scan','quarkus-standard','guicedee-jlink',
             'guicedee-scan-jlink','guicedee-native','quarkus-standard-native']
    labels = ['GuicedEE SPI / JVM','GuicedEE scanner / JVM','Quarkus / JVM',
              'GuicedEE SPI / jlink','GuicedEE scanner / jlink','GuicedEE SPI / native','Quarkus / native']
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10, 'svg.hashsalt':'guicedee-benchmarks'})
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True, sharex=True)
    maximum = max(data['groups'][group]['variants'][name]['launchToFirstBusinessMs']['median']/1000
                  for group in ['jvm-default','jvm-c1'] for name in names)
    for ax, group, title in zip(axes, ['jvm-default','jvm-c1'], ['Default JVM profile','Equal C1 JVM profile']):
        values = data['groups'][group]['variants']
        seconds = [values[name]['launchToFirstBusinessMs']['median']/1000 for name in names]
        colors = ['#167c80' if name.startswith('guicedee') else '#5950a3' for name in names]
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
    fig.suptitle('GuicedEE and normal-dependency Quarkus', x=.02, ha='left', fontsize=15, fontweight='bold')
    fig.text(.02,.02,'250m CPU / 500 MiB · 3 fresh starts per mode/profile · commercetools + GraphQL + Firestore\n'
             'Native repeats the same binaries without a JIT flag. Medians; all starts and capability checks retained.', fontsize=9)
    fig.tight_layout(rect=(0,.11,1,.94))
    fig.savefig(ROOT/'docs/startup.svg', metadata={'Date':None}, facecolor='white')
    plt.close(fig)
    with (ROOT/'docs/startup.svg').open('a', encoding='utf-8', newline='\n') as image:
        image.write('<!-- performance-data-sha256: '+hashlib.sha256((ROOT/'docs/current-performance.json').read_bytes()).hexdigest()+' -->\n')
    svg = ROOT/'docs/startup.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n',
                   encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
