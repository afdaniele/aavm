import argparse
from typing import Optional

from docker.errors import APIError

from aavm.cli import AbstractCLICommand, aavmlogger
from aavm.types import Arguments
from aavm.utils.docker import pull_image, sanitize_image_name
from aavm.utils.runtime import get_known_runtimes
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
        # noinspection DuplicatedCode
        parsed.runtime = sanitize_image_name(parsed.runtime[0])
        # get list of runtimes available locally
        aavmlogger.debug("Fetching list of known runtimes from disk...")
        known_runtimes = get_known_runtimes(machine=machine)
        aavmlogger.debug(f"{len(known_runtimes)} runtimes known locally.")
        # check whether the given runtime is known
        matches = [r for r in known_runtimes if r.image == parsed.runtime]
        match = matches[0] if matches else None
        # no matches?
        if match is None:
            aavmlogger.error(f"Runtime '{parsed.runtime}' not found.")
            return False
        # pull image
        try:
            aavmlogger.info(f"Downloading runtime '{parsed.runtime}'...")
            pull_image(machine, parsed.runtime)
            aavmlogger.info(f"Runtime '{parsed.runtime}' successfully downloaded.")
        except APIError as e:
            aavmlogger.error(str(e))
            return False
        # ---
        return True
