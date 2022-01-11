import argparse
from typing import Optional

from cpk.types import Machine
from .. import AbstractCLICommand
from ..logger import aavmlogger
from ... import aavmconfig
from ...exceptions import AAVMException
from ...types import Arguments


class CLIResetCommand(AbstractCLICommand):
    KEY = 'reset'

    @staticmethod
    def parser(parent: Optional[argparse.ArgumentParser] = None,
               args: Optional[Arguments] = None) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(parents=[parent])
        parser.add_argument(
            "--root",
            default=False,
            action="store_true",
            help="Revert changes to the root file system to the factory conditions"
        )
        parser.add_argument(
            "name",
            type=str,
            nargs=1,
            help="Name of the machine to reset"
        )
        return parser

    @staticmethod
    def execute(cpk_machine: Machine, parsed: argparse.Namespace) -> bool:
        parsed.machine = parsed.name[0].strip()
        # check if the machine exists
        if parsed.machine not in aavmconfig.machines:
            aavmlogger.error(f"The machine '{parsed.machine}' does not exist.")
            return False
        # get the machine
        machine = aavmconfig.machines[parsed.machine]
        # reset machine
        aavmlogger.info(f"Resetting machine '{machine.name}'...")
        try:
            machine.reset()
        except AAVMException as e:
            aavmlogger.error(str(e))
            return False
        aavmlogger.info("Machine reset.")
        # ---
        return True
