"""Verify the byte-preserved evidence explicitly selected for version control."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT/'results/retained-evidence.json'
ALLOWED = {'.json', '.md', '.txt', '.tsv', '.csv', '.dot'}


def selected_files():
    names = subprocess.check_output(['git','-C',str(ROOT),'ls-files','-z','--','results'], text=True).split('\0')
    paths = sorted(name for name in names if name and name != 'results/retained-evidence.json')
    if not paths: raise ValueError('No retained evidence has been staged or committed')
    for name in paths:
        path = ROOT/name
        snapshot = 'sources' in path.relative_to(ROOT).parts and (path.suffix in {'.java','.xml','.ps1','.py','.properties'} or path.name == 'Dockerfile')
        if (path.suffix not in ALLOWED and not snapshot) or not path.is_file() or path.is_symlink():
            raise ValueError('Unexpected evidence file: ' + name)
    return paths


def inventory(paths):
    return [{'path':name, 'bytes':(ROOT/name).stat().st_size,
             'sha256':hashlib.sha256((ROOT/name).read_bytes()).hexdigest()} for name in paths]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true', help='Explicitly record the currently staged/committed evidence selection')
    args = parser.parse_args()
    entries = inventory(selected_files())
    if args.refresh:
        MANIFEST.write_text(json.dumps({'format':1, 'policy':'docs/RETENTION.md', 'files':entries},indent=2)+'\n')
    else:
        expected = json.loads(MANIFEST.read_text())['files']
        if entries != expected: raise ValueError('Evidence selection or bytes differ from the retained manifest')
    print(f'Verified {len(entries)} evidence files, {sum(entry["bytes"] for entry in entries)/2**20:.2f} MiB')


if __name__ == '__main__': main()
