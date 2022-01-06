import argparse
from typing import Optional

from docker.errors import APIError
from termcolor import colored
from terminaltables import SingleTable as Table

from aavm.cli import AbstractCLICommand, aavmlogger
from aavm.types import Arguments
from aavm.utils.docker import remove_image
from aavm.utils.runtime import fetch_machine_runtimes, fetch_remote_runtimes
from cpk.types import Machine


class CLIRuntimeListCommand(AbstractCLICommand):
    KEY = 'runtime list'

    @staticmethod
    def parser(parent: Optional[argparse.ArgumentParser] = None,
               args: Optional[Arguments] = None) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(parents=[parent], add_help=False)
        # ---
        return parser

    @staticmethod
    def execute(machine: Machine, parsed: argparse.Namespace) -> bool:
        # get list of runtimes available on the index
        aavmlogger.debug("Fetching list of available runtimes from the index...")
        index_runtimes = fetch_remote_runtimes(check_downloaded=True, machine=machine)
        aavmlogger.debug(f"{len(index_runtimes)} runtimes found on the index.")
        # get list of runtimes available locally
        aavmlogger.info("Fetching list of available runtimes from the machine in use...")
        runtimes = fetch_machine_runtimes(machine=machine)
        aavmlogger.info(f"{len(runtimes)} runtimes found on the machine.")
        # show list of runtimes available
        data = [
            ["#", "Name", "Description", "Maintainer", "Arch", "Official"]
        ]
        for i, runtime in enumerate(runtimes):
            row = [str(i), runtime.image, runtime.description, runtime.maintainer, runtime.arch]
            # whether it is an official image
            official = len([r for r in index_runtimes if r.image == runtime.image])
            official = colored('Yes', 'green') if official else colored('No', 'red')
            row.append(official)
            # add row to table
            data += [row]
        table = Table(data)
        table.title = " Runtimes "
        print()
        print(table.table)
        # ---
        return True
