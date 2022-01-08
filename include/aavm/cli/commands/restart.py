import argparse
from typing import Optional

from cpk.types import Machine
from .start import CLIStartCommand
from .stop import CLIStopCommand
from .. import AbstractCLICommand
from ...types import Arguments


class CLIRestartCommand(AbstractCLICommand):

    KEY = 'restart'

    @staticmethod
    def parser(parent: Optional[argparse.ArgumentParser] = None,
               args: Optional[Arguments] = None) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(parents=[parent])
        parser.add_argument(
            "name",
            type=str,
            nargs=1,
            help="Name of the machine to restart"
        )
        return parser

    @staticmethod
    def execute(cpk_machine: Machine, parsed: argparse.Namespace) -> bool:
        parsed.machine = parsed.name[0].strip()
        # stop
        stopped = CLIStopCommand.execute(cpk_machine, parsed)
        if not stopped:
            return False
        # start
        return CLIStartCommand.execute(cpk_machine, parsed)
