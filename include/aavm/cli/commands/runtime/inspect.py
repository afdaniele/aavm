import argparse
from typing import Optional

from terminaltables import SingleTable as Table

from aavm.cli import AbstractCLICommand, aavmlogger
from aavm.types import Arguments
from aavm.utils.runtime import fetch_remote_runtimes, fetch_machine_runtimes
from aavm.utils.tables import table_runtime, table_image
from cpk.types import Machine


class CLIRuntimeInspectCommand(AbstractCLICommand):
    KEY = 'runtime inspect'

    @staticmethod
    def parser(parent: Optional[argparse.ArgumentParser] = None,
               args: Optional[Arguments] = None) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(parents=[parent], add_help=False)
        parser.add_argument(
            "runtime",
            nargs=1,
            help="Name of the runtimes to show",
        )
        # ---
        return parser

    @staticmethod
    def execute(machine: Machine, parsed: argparse.Namespace) -> bool:
        parsed.runtime = parsed.runtime[0]
        # get list of runtimes available on the index
        aavmlogger.debug("Fetching list of available runtimes from the index...")
        index_runtimes = fetch_remote_runtimes(check_downloaded=True, machine=machine)
        aavmlogger.debug(f"{len(index_runtimes)} runtimes found on the index.")
        # check whether the runtime is present in the index
        index_matches = [r for r in index_runtimes if r.image == parsed.runtime]
        index_match = index_matches[0] if index_matches else None
        # get list of runtimes available locally
        aavmlogger.debug("Fetching list of available runtimes from the machine in use...")
        machine_runtimes = fetch_machine_runtimes(machine=machine)
        aavmlogger.debug(f"{len(machine_runtimes)} runtimes found on the machine.")
        # check whether the runtime is present in the machine
        machine_matches = [r for r in machine_runtimes if r.image == parsed.runtime]
        machine_match = machine_matches[0] if machine_matches else None
        # no matches?
        if machine_match is None and index_match is None:
            aavmlogger.error(f"Runtime '{parsed.runtime}' not found.")
            return False
        # choose one match
        runtime = machine_match if machine_match else index_match
        # show runtime info
        downloaded = machine_match is not None
        official = machine_match is not None
        data = table_runtime(runtime, downloaded=downloaded, official=official)
        table = Table(data)
        table.inner_heading_row_border = False
        table.justify_columns[0] = 'right'
        table.title = " Runtime "
        print()
        print(table.table)
        # show image info
        data = table_image(runtime)
        table = Table(data)
        table.inner_heading_row_border = False
        table.justify_columns[0] = 'right'
        table.title = " Image "
        print()
        print(table.table)
        # ---
        return True
