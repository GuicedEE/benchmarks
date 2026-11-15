"""Verify the compact published measurements, without depending on Git history."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify_retention(data):
    used = {batch for group in data['groups'].values() for batch in group['batches']}
    used.update(phase['batch'] for phase in data.get('phases', []))
    if set(data['batches']) != used:
        raise ValueError('Published batches must exactly match the current groups and diagnostics')
    for path in data.get('inputSha256', {}):
        batch = path.removeprefix('results/').split('/')[0]
        if len(batch) == 15 and batch[:8].isdigit() and batch[8] == '-' and batch[9:].isdigit() and batch not in used:
            raise ValueError(f'Superseded batch hash in current evidence: {batch}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    evidence = ROOT/'results/latest/measurements.json'
    manifest = ROOT/'results/latest/manifest.json'
    verify_retention(json.loads(evidence.read_text(encoding='utf-8')))
    files = [evidence] + [evidence.with_name(name) for name in ['builds.json', 'native-profile.json', 'persistence.json']
                          if evidence.with_name(name).exists()]
    value = {'schemaVersion': 1, 'files': [{'path': p.name, 'bytes': p.stat().st_size,
                                         'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
    if args.refresh:
        manifest.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8', newline='\n')
    elif json.loads(manifest.read_text()) != value:
        raise ValueError('Published measurements differ from their manifest')
    print(f'Verified latest evidence: {len(files)} files, {sum(p.stat().st_size for p in files) / 2**20:.2f} MiB')


if __name__ == '__main__':
    main()
