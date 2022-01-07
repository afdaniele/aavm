import argparse
from typing import Optional

from termcolor import colored
from terminaltables import SingleTable as Table

from cpk.types import Machine
from .. import AbstractCLICommand
from ... import aavmconfig
from ...types import Arguments


class CLIListCommand(AbstractCLICommand):

    KEY = 'list'

    @staticmethod
    def parser(parent: Optional[argparse.ArgumentParser] = None,
               args: Optional[Arguments] = None) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(parents=[parent])
        return parser

    @staticmethod
    def execute(machine: Optional[Machine], parsed: argparse.Namespace) -> bool:
        # make a table with all the machines
        data = [
            ["#", "Name", "Description", "Runtime", "Status"]
        ]
        for i, machine in enumerate(aavmconfig.machines.values()):
            status = colored("Running", "green") if machine.running \
                else colored(machine.status.title(), "red")
            data.append([str(i), machine.name, machine.description, machine.runtime.image, status])
        table = Table(data)
        table.title = " Machines "
        print()
        print(table.table)
        # ---
        return True
