import argparse
import json
from typing import Optional

from cpk.types import Machine

from .. import AbstractCLICommand
from ..logger import aavmlogger
from ... import aavmconfig
from ...types import Arguments
from ...utils.docker import merge_container_configs
from ...utils.runtime import fetch_machine_runtimes


class CLIStartCommand(AbstractCLICommand):

    KEY = 'start'

    @staticmethod
    def parser(parent: Optional[argparse.ArgumentParser] = None,
               args: Optional[Arguments] = None) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(parents=[parent])
        parser.add_argument(
            "-n",
            "--container",
            default=None,
            help="Name of the container"
        )
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
        machine.machine = cpk_machine
        # try to get an existing container for this machine
        container = machine.container
        if container is not None:
            if container.status != "running":
                container.start()
                aavmlogger.info("Machine started, you should see it running with the container "
                                f"name '{container.name}'.")
                return True
        # make sure the runtime is downloaded
        aavmlogger.debug("Fetching list of available runtimes from the machine in use...")
        machine_runtimes = fetch_machine_runtimes(machine=cpk_machine)
        aavmlogger.debug(f"{len(machine_runtimes)} runtimes found on the machine.")
        machine_matches = [r for r in machine_runtimes if r.image == machine.runtime.image]
        if len(machine_matches) <= 0:
            aavmlogger.error(f"The machine '{machine.name}' uses the runtime "
                             f"'{machine.runtime.image}' which is currently not installed. Use "
                             f"the following command to install it,\n\n"
                             f"\t$ aavm runtime pull {machine.runtime.image}\n")
            return False
        # collect configurations from runtime and machine definition
        runtime_cfg = machine.runtime.configuration
        machine_cfg = machine.configuration
        container_cfg = merge_container_configs(runtime_cfg, machine_cfg)
        # add image from the runtime to the container configutation
        container_cfg["image"] = machine.runtime.image
        # define container's name
        container_name = f"aavm-machine-{machine.name}"
        container_cfg["name"] = container_name
        # make a new container for this machine
        docker = machine.machine.get_client()
        aavmlogger.debug(f"Creating container with configuration:\n"
                         f"{json.dumps(container_cfg, indent=4)}\n")
        container = docker.containers.create(**container_cfg)
        # start container
        container.start()
        aavmlogger.info("Machine started, you should see it running with the container "
                        f"name '{container.name}'.")
        # ---
        return True
