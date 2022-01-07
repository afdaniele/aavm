import argparse
import functools
import os
import re
from typing import Optional, Union, List

from cpk.machine import FromEnvMachine
from cpk.types import Machine
from .. import AbstractCLICommand
from ..logger import aavmlogger
from ... import aavmconfig
from ...constants import MACHINE_SCHEMA_DEFAULT_VERSION, MACHINE_DEFAULT_VERSION
from ...types import Arguments, AAVMMachine, AAVMRuntime
from ...utils.runtime import fetch_machine_runtimes

fields = {
    "name": {
        "title": "Name",
        "description": "A unique name for your machine",
        "pattern": r"^[a-zA-Z0-9-_]+$",
        "pattern_human": "an alphanumeric string [a-zA-Z0-9-_]",
        "validator": None
    },
    "description": {
        "title": "Description",
        "description": "A more user-friendly description for your machine",
        "pattern": r"^.+$",
        "pattern_human": "a non-empty free text",
        "validator": None
    },
    "runtime": {
        "title": "Runtime",
        "description": "The AAVM runtime to use as base for your machine",
        "pattern": r"^.+$",
        "pattern_human": "a valid Docker image name",
        "validator": None
    },
}


class CLICreateCommand(AbstractCLICommand):

    KEY = 'create'

    @staticmethod
    def parser(parent: Optional[argparse.ArgumentParser] = None,
               args: Optional[Arguments] = None) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(parents=[parent])
        return parser

    @staticmethod
    def execute(machine: Optional[Machine], parsed: argparse.Namespace) -> bool:
        # get list of runtimes available locally
        aavmlogger.info("Fetching list of available runtimes from the machine in use...")
        runtimes = fetch_machine_runtimes(machine=machine)
        aavmlogger.info(f"{len(runtimes)} runtimes found on the machine.")
        # define name validator
        # noinspection PyTypedDict
        fields["name"]["validator"] = validate_name
        # define runtime validator function
        # noinspection PyTypedDict
        fields["runtime"]["validator"] = functools.partial(validate_runtime, runtimes, machine)
        # collect info about the new machine
        aavmlogger.info("Please, provide information about your new machine:")
        machine_info = {}
        space = "    |"
        print(space)
        for key, field in fields.items():
            title = field["title"]
            pattern = field["pattern"]
            description = field["description"]
            pattern_human = field["pattern_human"]
            validator = field["validator"] or (lambda _: True)
            # ---
            done = False
            while not done:
                res = input(f"{space}\n{space}\t{title} ({description})\n{space}\t> ")
                # match against pattern
                if not re.match(pattern, res):
                    aavmlogger.error(f"Field '{title}' must be {pattern_human}.")
                    continue
                # run it through validator
                valid = validator(res)
                if valid is not True:
                    aavmlogger.error(valid)
                    continue
                # ---
                done = True
                machine_info[key] = res
        # get runtime object
        runtime = [r for r in runtimes if r.image == machine_info["runtime"]][0]
        # make new machine
        machine = AAVMMachine(
            schema=MACHINE_SCHEMA_DEFAULT_VERSION,
            version=MACHINE_DEFAULT_VERSION,
            name=machine_info["name"],
            path=os.path.join(aavmconfig.path, "machines", machine_info["name"]),
            runtime=runtime,
            description=machine_info["description"],
            configuration={},
            machine=machine
        )
        machine.to_disk()
        # make root directory
        # TODO
        aavmlogger.info(f"Machine '{machine_info['name']}' created successfully.")
        # ---
        return True


def validate_runtime(runtimes: List[AAVMRuntime], machine: Machine, runtime: str) -> \
        Union[str, bool]:
    # check whether the runtime is present in the machine
    matches = [r for r in runtimes if r.image == runtime]
    if len(matches) > 0:
        return True
    if not isinstance(machine, FromEnvMachine):
        return f"The runtime '{runtime}' was not found, make sure you pull it using " \
               f"'aavm runtime pull <runtime>' first."
    return f"The runtime '{runtime}' was not found on machine '{machine.name}', " \
           f"make sure you pull it using 'aavm -H {machine.name} runtime pull <runtime>' first."


def validate_name(name: str) -> Union[str, bool]:
    machine_dir = os.path.join(aavmconfig.path, "machines", name)
    if os.path.exists(machine_dir):
        return f"Another machine with the name '{name}' already exists. Choose another name."
    return True
