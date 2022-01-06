import argparse
from typing import Optional, Dict, Type

from aavm.cli import AbstractCLICommand
from aavm.cli.commands.runtime.info import CLIRuntimeInfoCommand
from aavm.cli.commands.runtime.fetch import CLIRuntimeFetchCommand
from aavm.types import Arguments

from cpk.types import Machine

_supported_subcommands: Dict[str, Type[AbstractCLICommand]] = {
    "info": CLIRuntimeInfoCommand,
    "fetch": CLIRuntimeFetchCommand,
}


class CLIRuntimeCommand(AbstractCLICommand):

    KEY = 'runtime'

    @staticmethod
    def parser(parent: Optional[argparse.ArgumentParser] = None,
               args: Optional[Arguments] = None) -> argparse.ArgumentParser:
        # create a temporary parser used to select the subcommand
        parser = argparse.ArgumentParser(parents=[parent], prog='aavm runtime')
        parser.add_argument(
            'subcommand',
            choices=_supported_subcommands.keys(),
            help=f"Subcommand. Can be any of {', '.join(_supported_subcommands.keys())}"
        )
        parsed, _ = parser.parse_known_args(args)
        # return subcommand's parser
        subcommand = _supported_subcommands[parsed.subcommand]
        return subcommand.parser(parser, args)

    @staticmethod
    def execute(machine: Machine, parsed: argparse.Namespace) -> bool:
        subcommand = _supported_subcommands[parsed.subcommand]
        return subcommand.execute(machine, parsed)
