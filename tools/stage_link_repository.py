"""Stage local framework artifacts for the Oracle Linux Maven reactor build."""
from pathlib import Path
import os
import shutil
ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
CACHE = Path.home()/'.m2/repository'
PROJECT = WORKSPACE/'.mvn/target/project-local-repo'
DEST = ROOT/'docker/repository'
def copy(source):
    if source.is_relative_to(PROJECT):
        parts=source.relative_to(PROJECT).parts
        relative=Path(*parts[0].split('.'), *parts[1:])
    else:
        relative=source.relative_to(CACHE)
    target=DEST/relative
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)
for application in ['guicedee','guicedee-scan']:
    for entry in (ROOT/application/'target/classpath.txt').read_text().strip().split(os.pathsep):
        jar=Path(entry)
        copy(jar)
        pom=jar.with_suffix('.pom')
        if pom.exists(): copy(pom)
# Local BOMs/parents are not necessarily published yet; preserve their real POMs.
for base in [PROJECT, CACHE/'com/guicedee']:
    for pom in base.rglob('*.pom'): copy(pom)
print('Staged runtime dependencies and local framework POMs:', DEST)
