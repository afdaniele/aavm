import argparse
from typing import Optional

from aavm.cli import AbstractCLICommand, aavmlogger
from aavm.types import Arguments
from cpk.types import Machine


class CLIRuntimeInfoCommand(AbstractCLICommand):
    KEY = 'runtime info'

    @staticmethod
    def parser(parent: Optional[argparse.ArgumentParser] = None,
               args: Optional[Arguments] = None) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(parents=[parent], add_help=False)
        # ---
        return parser

    @staticmethod
    def execute(machine: Machine, parsed: argparse.Namespace) -> bool:
        # get info about runtime
        print("ASD")
