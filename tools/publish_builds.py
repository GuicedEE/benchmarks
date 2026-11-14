"""Replace the published build cohort with a complete, successful measurement matrix."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from compare_builds import validate

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    source = args.directory/'builds.json'
    data = json.loads(source.read_text(encoding='utf-8'))
    validate(data)
    if not data['eligible']:
        raise ValueError('Build cohort has not completed successfully')
    data['inputSha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    if 'dependencyJars' in data:
        data['dependencyCacheJars'] = data.pop('dependencyJars')
    (ROOT/'results/latest/builds.json').write_text(json.dumps(data, separators=(',', ':'))+'\n', encoding='utf-8', newline='\n')
    subprocess.run([sys.executable, ROOT/'tools/verify_latest.py', '--refresh'], check=True)


if __name__ == '__main__':
    main()
