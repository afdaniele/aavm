import argparse
from typing import Optional

import docker
import requests
from termcolor import colored
from terminaltables import SingleTable as Table

from aavm.cli import AbstractCLICommand, aavmlogger
from aavm.constants import AAVM_RUNTIMES_INDEX_URL
from aavm.types import Arguments
from cpk.types import Machine


class CLIRuntimeFetchCommand(AbstractCLICommand):
    KEY = 'runtime fetch'

    @staticmethod
    def parser(parent: Optional[argparse.ArgumentParser] = None,
               args: Optional[Arguments] = None) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(parents=[parent], add_help=False)
        # ---
        return parser

    @staticmethod
    def execute(machine: Machine, parsed: argparse.Namespace) -> bool:
        # get list of runtimes available
        index_url = AAVM_RUNTIMES_INDEX_URL
        aavmlogger.info("Fetching list of available runtimes...")
        aavmlogger.debug(f"GET: {index_url}")
        runtimes = requests.get(index_url).json()
        # show list of runtimes available
        data = [
            ["#", "ID", "Description", "Maintainer", "Arch", "Downloaded"]
        ]
        # TODO: move this to a utility function that returns List[AAVMRuntime] w/ the option to fill in 'downloaded' field
        for i, runtime in enumerate(runtimes):
            registry = runtime.get('registry', '')
            organization = runtime['organization']
            name = runtime['name']
            tag = runtime['tag']
            arch = machine.get_architecture()
            # compile ID (docker image name)
            id = f"{registry}/{organization}/{name}:{tag}".lstrip("/")
            # check whether it is downloaded already
            try:
                machine.get_client().images.get(f"{id}-{arch}")
                downloaded = colored('Yes', 'green')
            except docker.errors.ImageNotFound:
                downloaded = colored('No', 'red')
            # add row to table
            data += [[str(i), id, runtime['description'], runtime['maintainer'], arch, downloaded]]
        table = Table(data)
        table.title = " Available Runtimes "
        print(table.table)
        # ---
        return True
