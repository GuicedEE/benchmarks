"""Stage resolved dependencies from an explicit Maven repository for Linux builds."""
import argparse
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def stage(repository, applications):
    repository = repository.resolve()
    project_repository = (ROOT/'.mvn/target/project-local-repo').resolve()
    destination = ROOT/'docker/repository'
    def copy(source):
        source = source.resolve()
        if source.is_relative_to(repository):
            relative = source.relative_to(repository)
        elif source.is_relative_to(project_repository):
            parts = source.relative_to(project_repository).parts
            relative = Path(*parts[0].split('.'), *parts[1:])
        else:
            raise ValueError(f'Dependency {source} is outside --repository {repository}; '
                             'only this checkout\'s own Maven 4 reactor cache is also accepted')
        target = destination/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source != target.resolve():
            shutil.copy2(source, target)
    for application in applications:
        for name in (ROOT/application/'target/classpath.txt').read_text().strip().split(os.pathsep):
            jar = Path(name)
            copy(jar)
            if jar.with_suffix('.pom').exists():
                copy(jar.with_suffix('.pom'))
    # Parents and BOMs are not in dependency classpaths; only stage the chosen
    # repository's GuicedEE models, never unrelated source trees or global caches.
    for pom in (repository/'com/guicedee').rglob('*.pom'):
        copy(pom)
    for pom in project_repository.rglob('*.pom'):
        copy(pom)
    print('Staged resolved runtime artifacts and framework models:', destination)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, default=Path.home()/'.m2/repository')
    parser.add_argument('--applications', nargs='+', choices=['guicedee','guicedee-scan','guicedee-native','guicedee-cdi','guicedee-cdi-spi','guicedee-cdi-native'],
                        default=['guicedee','guicedee-scan'])
    args = parser.parse_args()
    stage(args.repository, args.applications)
