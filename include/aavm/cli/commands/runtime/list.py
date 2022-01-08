import argparse
from typing import Optional

from termcolor import colored
from terminaltables import SingleTable as Table

from aavm.cli import AbstractCLICommand, aavmlogger
from aavm.types import Arguments
from aavm.utils.runtime import get_known_runtimes
from cpk.types import Machine


class CLIRuntimeListCommand(AbstractCLICommand):
    KEY = 'runtime list'

    @staticmethod
    def parser(parent: Optional[argparse.ArgumentParser] = None,
               args: Optional[Arguments] = None) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(parents=[parent], add_help=False)
        parser.add_argument(
            "--all",
            action="store_true",
            default=False,
            help="List runtimes of any architecture",
        )
        # ---
        return parser

    @staticmethod
    def execute(machine: Machine, parsed: argparse.Namespace) -> bool:
        # get list of runtimes available locally
        aavmlogger.debug("Fetching list of known runtimes from disk...")
        runtimes = get_known_runtimes(machine=machine)
        # filter by arch
        arch = machine.get_architecture()
        if not parsed.all:
            runtimes = [r for r in runtimes if r.image.arch == arch]
        aavmlogger.debug(f"{len(runtimes)} runtimes known locally.")
        # show list of runtimes available
        data = [
            ["#", "Name", "Description", "Arch", "Official", "Downloaded"] if
            parsed.all else ["#", "Name", "Description", "Official", "Downloaded"]
        ]
        for i, runtime in enumerate(runtimes):
            # whether it is an official image and it is downloaded
            official = colored('Yes', 'green') if runtime.official else colored('No', 'red')
            downloaded = colored('Yes', 'green') if runtime.downloaded else colored('No', 'red')
            # make row
            row = [str(i), runtime.image.compile(), runtime.description]
            # add arch
            if parsed.all:
                row.append(runtime.image.arch)
            # add official and downloaded
            row.extend([official, downloaded])
            # add row to table
            data += [row]
        table = Table(data)
        table.title = " Runtimes "
        table.justify_columns[4 - int(not parsed.all)] = 'center'
        table.justify_columns[5 - int(not parsed.all)] = 'center'
        print()
        print(table.table)
        # ---
        return True
