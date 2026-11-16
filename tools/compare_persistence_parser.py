"""Run the persistence matrix with interleaved secured Hibernate-parser controls.

Accepts the same arguments as compare_persistence.py. Only GuicedEE control starts
set GUICEDEE_PERSISTENCE_XML_PARSER=hibernate; descriptor security checks remain on.
Controls use identical images and fresh databases and are excluded from framework
ranking rows. Their complete measurements remain in the current raw dataset.
"""
import copy
import hashlib
import json
from pathlib import Path
import compare_persistence as runner


def parser_command(command):
    command = list(command)
    if (command[:2] == ['run', '-d'] and '--name' in command
            and '-guicedee-' in command[command.index('--name') + 1]):
        command[-1:-1] = ['-e', 'GUICEDEE_PERSISTENCE_XML_PARSER=hibernate']
    return command


def main():
    run_start, docker = runner.run_start, runner.docker
    controls = []

    def measured(args, data, output, db, network, variant, run):
        if variant != 'guicedee':
            return run_start(args, data, output, db, network, variant, run)
        reference = copy.deepcopy(data)
        reference['starts'] = []
        reference.pop('parserControl', None)
        directory = output/'parser-control'
        directory.mkdir(exist_ok=True)

        def control():
            runner.docker = lambda *command, **kw: docker(*parser_command(command), **kw)
            try:
                run_start(args, reference, directory, db, network, variant, 100 + run)
            finally:
                runner.docker = docker
            controls.extend(reference['starts'])
            data['parserControl'] = dict(
                environmentOverride={'GUICEDEE_PERSISTENCE_XML_PARSER': 'hibernate'},
                descriptorSecurityChecks=True, identicalApplicationImage=data['images']['guicedee'],
                scope='Current secured Hibernate fallback versus current fast parser; not a historical binary comparison.',
                driverSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), starts=controls)
            (directory/'summary.json').write_text(json.dumps(data['parserControl'], indent=2)+'\n', encoding='utf-8')

        if run % 2:
            control()
        run_start(args, data, output, db, network, variant, run)
        if not run % 2:
            control()
        if run == 1:
            data['protocol'] += (' Identical-image GuicedEE controls force the secured Hibernate descriptor parser, '
                'alternating before/after default-parser starts in fresh databases; controls are excluded from ranking rows.')

    runner.run_start = measured
    try:
        runner.main()
    finally:
        runner.run_start, runner.docker = run_start, docker


if __name__ == '__main__':
    main()
