import argparse
from typing import Optional

from aavm.cli.commands.info import CLIInfoCommand

from cpk import CPKProject

from .. import AbstractCLICommand, aavmlogger
from ...types import Arguments

from cpk.types import Machine


class CLIRemoveCommand(AbstractCLICommand):

    KEY = 'remove'

    @staticmethod
    def parser(parent: Optional[argparse.ArgumentParser] = None,
               args: Optional[Arguments] = None) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(parents=[parent])
        return parser

    @staticmethod
    def execute(machine: Machine, parsed: argparse.Namespace) -> bool:
        # get project
        project = CPKProject(parsed.workdir, parsed=parsed)

        # show info about project
        CLIInfoCommand.execute(machine, parsed)

        # pick right value of `arch` given endpoint
        if parsed.arch is None:
            aavmlogger.info("Parameter `arch` not given, will resolve it from the endpoint.")
            parsed.arch = machine.get_architecture()
            aavmlogger.info(f"Parameter `arch` automatically set to `{parsed.arch}`.")

        # create docker client
        docker = machine.get_client()

        # TODO: perform clean

        return True
