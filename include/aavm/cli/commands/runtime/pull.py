import argparse
from typing import Optional

from docker.errors import APIError

from aavm.cli import AbstractCLICommand, aavmlogger
from aavm.types import Arguments
from aavm.utils.docker import pull_image
from aavm.utils.runtime import fetch_remote_runtimes
from cpk.types import Machine


class CLIRuntimePullCommand(AbstractCLICommand):
    KEY = 'runtime pull'

    @staticmethod
    def parser(parent: Optional[argparse.ArgumentParser] = None,
               args: Optional[Arguments] = None) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(parents=[parent], add_help=False)
        parser.add_argument(
            "runtime",
            nargs=1,
            help="Name of the runtimes to install",
        )
        # ---
        return parser

    @staticmethod
    def execute(machine: Machine, parsed: argparse.Namespace) -> bool:
        parsed.runtime = parsed.runtime[0]
        # get list of runtimes available on the index
        aavmlogger.debug("Fetching list of available runtimes from the index...")
        runtimes = fetch_remote_runtimes(check_downloaded=True, machine=machine)
        aavmlogger.debug(f"{len(runtimes)} runtimes found on the index.")
        # check whether the runtime is present in the index
        matches = [r for r in runtimes if r.image == parsed.runtime]
        match = matches[0] if matches else None
        # no matches?
        if match is None:
            aavmlogger.error(f"Runtime '{parsed.runtime}' not found on the index.")
            return False
        # pull image
        image = match.image
        try:
            aavmlogger.info(f"Downloading runtime '{parsed.runtime}'...")
            pull_image(machine, image)
            aavmlogger.info(f"Runtime '{parsed.runtime}' successfully downloaded.")
        except APIError as e:
            aavmlogger.error(str(e))
            return False
        # ---
        return True
