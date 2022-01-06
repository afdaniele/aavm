import argparse
import logging
import os
import sys

import aavm
from aavm import aavmconfig
from aavm.exceptions import AAVMException

from aavm.cli.logger import aavmlogger
from aavm.cli.commands.create import CLICreateCommand
from aavm.cli.commands.info import CLIInfoCommand
# from aavm.cli.commands.build import CLIBuildCommand
# from aavm.cli.commands.run import CLIRunCommand
# from aavm.cli.commands.clean import CLICleanCommand
# from aavm.cli.commands.push import CLIPushCommand
# from aavm.cli.commands.decorate import CLIDecorateCommand
# from aavm.cli.commands.machine import CLIMachineCommand
from aavm.cli.commands.runtime import CLIRuntimeCommand
from aavm.utils.machine import get_machine

_supported_commands = {
    'create': CLICreateCommand,
    'info': CLIInfoCommand,
    # 'build': CLIBuildCommand,
    # 'run': CLIRunCommand,
    # 'clean': CLICleanCommand,
    # 'push': CLIPushCommand,
    # 'decorate': CLIDecorateCommand,
    # 'machine': CLIMachineCommand,
    'runtime': CLIRuntimeCommand,
}


def run():
    aavmlogger.info(f"AAVM - Almost A Virtual Machine - v{aavm.__version__}")
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        'command',
        choices=_supported_commands.keys()
    )
    # print help (if needed)
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        parser.print_help()
        return
    # ---
    # parse `command`
    parsed, remaining = parser.parse_known_args()
    # get command
    command = _supported_commands[parsed.command]
    # let the command parse its arguments
    cmd_parser = command.get_parser(remaining)
    parsed = cmd_parser.parse_args(remaining)
    # enable debug
    if parsed.debug:
        aavmlogger.setLevel(logging.DEBUG)
    # get machine
    machine = get_machine(parsed, aavmconfig.machines)
    # avoid commands using `parsed.machine`
    parsed.machine = None
    # execute command
    try:
        with machine:
            command.execute(machine, parsed)
    except AAVMException as e:
        aavmlogger.error(str(e))
    except KeyboardInterrupt:
        aavmlogger.info(f"Operation aborted by the user")


if __name__ == '__main__':
    run()
