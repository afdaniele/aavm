import argparse
from typing import Optional

from cpk.types import Machine
from .. import AbstractCLICommand
from ..logger import aavmlogger
from ... import aavmconfig
from ...types import Arguments
from ...utils.runtime import get_known_runtimes


class CLIStartCommand(AbstractCLICommand):
    KEY = 'start'

    @staticmethod
    def parser(parent: Optional[argparse.ArgumentParser] = None,
               args: Optional[Arguments] = None) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(parents=[parent])
        parser.add_argument(
            "-t",
            "--attach",
            default=False,
            action="store_true",
            help="Attach to the container and consume its logs"
        )
        parser.add_argument(
            "name",
            type=str,
            nargs=1,
            help="Name of the machine to start"
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
        if (machine.links.machine is not None) and (machine.links.machine != cpk_machine):
            aavmlogger.error(f"Machine '{machine.name}' is already associated with the CPK "
                             f"machine '{cpk_machine.name}'. You can't run it on a different one.")
            return False
        # link this machine to the current cpk machine
        machine.links.machine = cpk_machine
        # try to get an existing container for this machine
        container = machine.container
        if container is None:
            # make sure the runtime is downloaded
            aavmlogger.debug("Fetching list of available runtimes from the machine in use...")
            machine_runtimes = get_known_runtimes(machine=cpk_machine)
            aavmlogger.debug(f"{len(machine_runtimes)} runtimes found on the machine.")
            machine_matches = [r for r in machine_runtimes if r.image == machine.runtime.image]
            if len(machine_matches) <= 0:
                aavmlogger.error(f"The machine '{machine.name}' uses the runtime "
                                 f"'{machine.runtime.image}' which is currently not installed. "
                                 f"Use the following command to install it,\n\n"
                                 f"\t$ aavm runtime pull {machine.runtime.image}\n")
                return False
            # make container
            container = machine.make_container()
            machine.links.container = container.id

        # TODO: implement '--attach'

        # store machine back to disk to update association with container and CPK machine
        machine.to_disk()

        # container exists, start it
        if container.status != "running":
            aavmlogger.info("Starting machine...")
            container.start()
            aavmlogger.info("Machine started, you should see it running with the container "
                            f"name '{container.name}'.")
        else:
            aavmlogger.info(f"The machine '{machine.name}' appears to be running already."
                            f" Nothing to do.")
        # ---
        return True
