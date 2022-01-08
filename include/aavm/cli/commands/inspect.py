import argparse
import os.path
from typing import Optional

from terminaltables import SingleTable as Table

from cpk.types import Machine
from .. import AbstractCLICommand
from ..logger import aavmlogger
from ... import aavmconfig
from ...types import Arguments
from ...utils.tables import table_machine, table_configuration


class CLIInspectCommand(AbstractCLICommand):

    KEY = 'inspect'

    @staticmethod
    def parser(parent: Optional[argparse.ArgumentParser] = None,
               args: Optional[Arguments] = None) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(parents=[parent])
        parser.add_argument(
            "name",
            type=str,
            nargs=1,
            help="Name of the machine to show information about"
        )
        return parser

    @staticmethod
    def execute(machine: Optional[Machine], parsed: argparse.Namespace) -> bool:
        parsed.machine = parsed.name[0].strip()
        # check if the machine exists
        if parsed.machine not in aavmconfig.machines:
            aavmlogger.error(f"The machine '{parsed.machine}' does not exist.")
            return False
        # get the machine
        machine = aavmconfig.machines[parsed.machine]
        # make a table of info
        data = table_machine(machine)
        data.append(["Configuration", os.path.join(machine.path, "configuration.json")])
        machine_table = Table(data)
        machine_table.inner_heading_row_border = False
        machine_table.justify_columns[0] = 'right'
        machine_table.title = " Machine "
        print()
        print(machine_table.table)
        # show configuration info
        data = table_configuration(machine.configuration)
        config_table = Table(data)
        config_table.inner_heading_row_border = False
        config_table.justify_columns[0] = 'right'
        config_table.title = " Configuration "
        print()
        print(config_table.table)
        # ---
        return True
