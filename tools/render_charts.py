"""Render the current startup and build charts (optional dependency: matplotlib)."""
import json
import hashlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]


def save(fig, name):
    svg = ROOT/f'docs/{name}.svg'
    fig.savefig(svg, metadata={'Date':None}, facecolor='white')
    plt.close(fig)
    fingerprint = hashlib.sha256((ROOT/'docs/current-performance.json').read_bytes()).hexdigest()
    content = '\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())
    svg.write_text(content+'\n<!-- performance-data-sha256: '+fingerprint+' -->\n',
                   encoding='utf-8', newline='\n')


def build_chart(data):
    values = data['builds']['variants']
    groups = [(['guicedee', 'guicedee-scan', 'quarkus-standard'], 'compile', 'Clean Java compilation'),
              (['guicedee', 'guicedee-scan', 'quarkus-standard'], 'package', 'Complete JVM packaging'),
              (['guicedee-jlink', 'guicedee-scan-jlink', 'guicedee-native', 'quarkus-standard-native'],
               'package', 'jlink and native packaging')]
    labels = {'guicedee':'GuicedEE SPI', 'guicedee-scan':'GuicedEE scanner', 'quarkus-standard':'Quarkus',
              'guicedee-jlink':'GuicedEE SPI jlink', 'guicedee-scan-jlink':'GuicedEE scanner jlink',
              'guicedee-native':'GuicedEE SPI native', 'quarkus-standard-native':'Quarkus native'}
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    for ax, (names, goal, title) in zip(axes, groups):
        seconds = [values[name][goal]['median'] for name in names]
        errors = [[values[name][goal]['median']-values[name][goal]['minimum'] for name in names],
                  [values[name][goal]['maximum']-values[name][goal]['median'] for name in names]]
        maximum = max(values[name][goal]['maximum'] for name in names)
        ax.barh(range(len(names)), seconds, xerr=errors, capsize=3, height=.6,
                color=['#167c80' if name.startswith('guicedee') else '#5950a3' for name in names])
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
             'Retained build cohort; newer JVM wrapper runtime measurements are separate.', fontsize=9)
    fig.tight_layout(rect=(0,.13,1,.94))
    save(fig, 'builds')


def main():
    data = json.loads((ROOT/'docs/current-performance.json').read_text())
    names = ['guicedee','guicedee-scan','quarkus-standard','guicedee-jlink',
             'guicedee-scan-jlink','guicedee-native','quarkus-standard-native']
    labels = ['GuicedEE SPI / JVM','GuicedEE scanner / JVM','Quarkus / JVM',
              'GuicedEE SPI / jlink','GuicedEE scanner / jlink','GuicedEE SPI / native','Quarkus / native']
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10, 'svg.hashsalt':'guicedee-benchmarks'})
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.4), sharey=True, sharex=True)
    def profile(group):
        return {**data['groups'][group]['variants'], **data['groups']['native-standard']['variants']}
    maximum = max(profile(group)[name]['launchToFirstBusinessMs']['median']/1000
                  for group in ['jvm-default','jvm-c1'] for name in names)
    for ax, group, title in zip(axes, ['jvm-default','jvm-c1'], ['Default JVM profile','Equal C1 JVM profile']):
        values = profile(group)
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
    native_starts = data['groups']['native-standard']['variants']['guicedee-native']['starts']
    fig.text(.02,.02,'250m CPU / 500 MiB · 3 JVM starts per mode/profile · commercetools + GraphQL + Firestore\n'
             f'Native reference rows repeat the separate retained cohort ({native_starts} starts/variant); native has no JIT.\n'
             'jlink workload passes, but the SDK scanner finds zero URLs: full SDK model discovery is not established.', fontsize=9)
    fig.tight_layout(rect=(0,.16,1,.94))
    save(fig, 'startup')
    build_chart(data)


if __name__ == '__main__':
    main()
