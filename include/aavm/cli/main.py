import argparse
import logging
import sys

import termcolor

from cpk import cpkconfig

import aavm
from aavm.exceptions import AAVMException

from aavm.cli.logger import aavmlogger, update_logger
from aavm.cli.commands.create import CLICreateCommand
from aavm.cli.commands.inspect import CLIInspectCommand
from aavm.cli.commands.list import CLIListCommand
from aavm.cli.commands.start import CLIStartCommand
from aavm.cli.commands.stop import CLIStopCommand
from aavm.cli.commands.restart import CLIRestartCommand
# from aavm.cli.commands.clean import CLICleanCommand
# from aavm.cli.commands.push import CLIPushCommand
# from aavm.cli.commands.decorate import CLIDecorateCommand
from aavm.cli.commands.reset import CLIResetCommand
from aavm.cli.commands.runtime import CLIRuntimeCommand

from cpk.utils.machine import get_machine

_supported_commands = {
    'create': CLICreateCommand,
    'inspect': CLIInspectCommand,
    'ls': CLIListCommand,
    'list': CLIListCommand,
    'start': CLIStartCommand,
    'stop': CLIStopCommand,
    'restart': CLIRestartCommand,
    # 'decorate': CLIDecorateCommand,
    # 'machine': CLIMachineCommand,
    'reset': CLIResetCommand,
    'runtime': CLIRuntimeCommand,
}


def run():
    intro = f"AAVM - Almost A Virtual Machine - v{aavm.__version__}"
    separator = '-' * len(intro)
    aavmlogger.info(f"{termcolor.RESET}{intro}\n{termcolor.RESET}{separator}")
    # define global arguments
    # noinspection DuplicatedCode
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
        update_logger(logging.DEBUG)
    # get machine
    machine = get_machine(parsed, cpkconfig.machines)
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
