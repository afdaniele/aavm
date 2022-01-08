import argparse
from typing import Optional

from terminaltables import SingleTable as Table

from aavm.cli import AbstractCLICommand, aavmlogger
from aavm.types import Arguments
from aavm.utils.docker import sanitize_image_name
from aavm.utils.runtime import get_known_runtimes
from aavm.utils.tables import table_runtime, table_image, table_configuration
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

    # noinspection DuplicatedCode
    @staticmethod
    def execute(machine: Machine, parsed: argparse.Namespace) -> bool:
        parsed.runtime = sanitize_image_name(parsed.runtime[0])
        # get list of runtimes available locally
        aavmlogger.debug("Fetching list of known runtimes from disk...")
        known_runtimes = get_known_runtimes(machine=machine)
        aavmlogger.debug(f"{len(known_runtimes)} runtimes known locally.")
        # check whether the given runtime is known
        matches = [r for r in known_runtimes if r.image == parsed.runtime]
        runtime = matches[0] if matches else None
        # no matches?
        if runtime is None:
            aavmlogger.error(f"Runtime '{parsed.runtime}' not found.")
            return False
        # show runtime info
        data = table_runtime(runtime)
        runtime_table = Table(data)
        runtime_table.inner_heading_row_border = False
        runtime_table.justify_columns[0] = 'right'
        runtime_table.title = " Runtime "
        print()
        print(runtime_table.table)
        # show image info
        data = table_image(runtime)
        image_table = Table(data)
        image_table.inner_heading_row_border = False
        image_table.justify_columns[0] = 'right'
        image_table.title = " Image "
        print()
        print(image_table.table)
        # show configuration info
        data = table_configuration(runtime.configuration)
        config_table = Table(data)
        config_table.inner_heading_row_border = False
        config_table.justify_columns[0] = 'right'
        config_table.title = " Configuration "
        print()
        print(config_table.table)
        # ---
        return True
