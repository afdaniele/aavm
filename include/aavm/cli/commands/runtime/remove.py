import argparse
from typing import Optional

from docker.errors import APIError

from aavm.cli import AbstractCLICommand, aavmlogger
from aavm.types import Arguments
from aavm.utils.docker import remove_image
from aavm.utils.runtime import fetch_machine_runtimes
from cpk.types import Machine


class CLIRuntimeRemoveCommand(AbstractCLICommand):
    KEY = 'runtime rm'

    @staticmethod
    def parser(parent: Optional[argparse.ArgumentParser] = None,
               args: Optional[Arguments] = None) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(parents=[parent], add_help=False)
        parser.add_argument(
            "runtime",
            nargs=1,
            help="Name of the runtimes to remove",
        )
        # ---
        return parser

    @staticmethod
    def execute(machine: Machine, parsed: argparse.Namespace) -> bool:
        parsed.runtime = parsed.runtime[0]
        # get list of runtimes available on the machine
        aavmlogger.debug("Fetching list of available runtimes from the machine...")
        runtimes = fetch_machine_runtimes(machine=machine)
        aavmlogger.debug(f"{len(runtimes)} runtimes found on the machine.")
        # check whether the runtime is present in the machine
        matches = [r for r in runtimes if r.image == parsed.runtime]
        match = matches[0] if matches else None
        # no matches?
        if match is None:
            aavmlogger.error(f"Runtime '{parsed.runtime}' not found on the machine.")
            return False
        # remove image
        image = match.image
        try:
            aavmlogger.info(f"Removing runtime '{parsed.runtime}'...")
            remove_image(machine, image)
            aavmlogger.info(f"Runtime '{parsed.runtime}' successfully removed.")
        except APIError as e:
            aavmlogger.error(str(e))
            return False
        # ---
        return True
