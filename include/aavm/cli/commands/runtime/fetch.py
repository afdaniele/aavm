import argparse
from typing import Optional

from termcolor import colored
from terminaltables import SingleTable as Table

from aavm.cli import AbstractCLICommand, aavmlogger
from aavm.types import Arguments
from aavm.utils.runtime import fetch_remote_runtimes
from cpk.types import Machine


class CLIRuntimeFetchCommand(AbstractCLICommand):
    KEY = 'runtime fetch'

    @staticmethod
    def parser(parent: Optional[argparse.ArgumentParser] = None,
               args: Optional[Arguments] = None) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(parents=[parent], add_help=False)
        parser.add_argument(
            "--all",
            action="store_true",
            default=False,
            help="Show runtimes of any architecture",
        )
        # ---
        return parser

    @staticmethod
    def execute(machine: Machine, parsed: argparse.Namespace) -> bool:
        # get list of runtimes available
        aavmlogger.info("Fetching list of available runtimes...")
        runtimes = fetch_remote_runtimes(check_downloaded=True, machine=machine)
        # filter by arch
        arch = machine.get_architecture()
        if not parsed.all:
            runtimes = [r for r in runtimes if r.arch == arch]
        # show list of runtimes available
        data = [
            ["#", "Name", "Description", "Maintainer", "Arch", "Downloaded"] if parsed.all else
            ["#", "Name", "Description", "Maintainer", "Downloaded"]
        ]
        for i, runtime in enumerate(runtimes):
            row = [str(i), runtime.image, runtime.description, runtime.maintainer]
            # architecture
            if parsed.all:
                row.append(runtime.arch)
            # whether it is downloaded already
            downloaded = colored('Yes', 'green') if runtime.downloaded else colored('No', 'red')
            row.append(downloaded)
            # add row to table
            data += [row]
        table = Table(data)
        table.title = " Available Runtimes "
        print()
        print(table.table)
        # ---
        return True
