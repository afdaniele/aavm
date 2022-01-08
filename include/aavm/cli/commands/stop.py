import argparse
import time
from typing import Optional

from cpk.types import Machine
from .. import AbstractCLICommand
from ..logger import aavmlogger
from ... import aavmconfig
from ...types import Arguments


class CLIStopCommand(AbstractCLICommand):

    KEY = 'stop'

    @staticmethod
    def parser(parent: Optional[argparse.ArgumentParser] = None,
               args: Optional[Arguments] = None) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(parents=[parent])
        parser.add_argument(
            "name",
            type=str,
            nargs=1,
            help="Name of the machine to stop"
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
        machine.machine = cpk_machine
        # try to get an existing container for this machine
        container = machine.container
        if container is None or container.status != "running":
            aavmlogger.info(f"The machine '{machine.name}' does not appear to be running right "
                            f"now. Nothing to do.")
            return True
        # attempt to stop the container
        aavmlogger.info("Stopping machine...")
        container.stop()
        # wait for container to be stopped
        t = 0
        while t < 15:
            container.reload()
            if container.status in ["stopped", "exited", "created"]:
                break
            time.sleep(1)
            t += 1
        # ---
        aavmlogger.info("Machine stopped.")
        # ---
        return True
