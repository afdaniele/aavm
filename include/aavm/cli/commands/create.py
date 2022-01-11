import argparse
import os
import re
from typing import Optional

from cpk.types import Machine
from .. import AbstractCLICommand
from ..logger import aavmlogger
from ... import aavmconfig
from ...constants import MACHINE_SCHEMA_DEFAULT_VERSION, MACHINE_DEFAULT_VERSION
from ...exceptions import AAVMException
from ...types import Arguments, AAVMMachine, AAVMRuntime, MachineSettings, MachineLinks

EmptyValidator = lambda *_: _


fields = {
    "name": {
        "title": "Name",
        "description": "A unique name for your machine",
        "pattern": r"^[a-zA-Z0-9-_]+$",
        "pattern_human": "an alphanumeric string [a-zA-Z0-9-_]",
        "validator": EmptyValidator
    },
    "description": {
        "title": "Description",
        "description": "A more user-friendly description for your machine",
        "pattern": r"^.+$",
        "pattern_human": "a non-empty free text",
        "validator": EmptyValidator
    },
    "runtime": {
        "title": "Runtime",
        "description": "The runtime to use as base for your machine",
        "pattern": r"^.+$",
        "pattern_human": "a valid Docker image name",
        "validator": EmptyValidator
    },
    # "persistency": {
    #     "title": "Persistency",
    #     "suggestion": "y/n",
    #     "description": "[Requires root privileges] Make changes to the virtual machine's "
    #                    "root file system persistent across runs",
    #     "pattern": r"^[y|n|Y|N]$",
    #     "pattern_human": "either 'y' or 'n'",
    #     "validator": EmptyValidator
    # },
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
        # attach validators
        fields["name"]["validator"] = validate_name
        fields["runtime"]["validator"] = AAVMRuntime.from_image_name
        # collect info about the new machine
        aavmlogger.info("Please, provide information about your new machine:\n"
                        "(provide the string 'q' to quit at any time)")
        machine_info = {}
        space = "    |"
        for key, field in fields.items():
            title = field["title"]
            pattern = field["pattern"]
            description = field["description"]
            pattern_human = field["pattern_human"]
            suggestion = field.get("suggestion", None)
            suggestion = f" [{suggestion}]" if suggestion else ""
            validator = field["validator"] or (lambda _: True)
            # ---
            done = False
            while not done:
                res = input(f"{space}\n{space}\t{title}{suggestion}: ({description})\n{space}\t> ")
                # break when 'q' is given
                if res.lower().strip() == "q":
                    aavmlogger.info('Quitting...')
                    return False
                # match against pattern
                if not re.match(pattern, res):
                    aavmlogger.error(f"Field '{title}' must be {pattern_human}.")
                    continue
                # run it through validator
                try:
                    validator(res)
                except AAVMException as e:
                    aavmlogger.error(str(e))
                    continue
                # ---
                done = True
                machine_info[key] = res
        # make new machine
        machine = AAVMMachine(
            schema=MACHINE_SCHEMA_DEFAULT_VERSION,
            version=MACHINE_DEFAULT_VERSION,
            name=machine_info["name"],
            path=os.path.join(aavmconfig.path, "machines", machine_info["name"]),
            runtime=AAVMRuntime.from_image_name(machine_info["runtime"]),
            description=machine_info["description"],
            configuration={},
            settings=MachineSettings(
                persistency=bool(machine_info["persistency"] in ["y", "Y"])
            ),
            links=MachineLinks(
                machine=machine,
                container=None
            )
        )
        machine.to_disk()
        # ---
        aavmlogger.info(f"Machine '{machine_info['name']}' created successfully.")
        return True


def validate_name(name: str):
    machine_dir = os.path.join(aavmconfig.path, "machines", name)
    if os.path.exists(machine_dir):
        raise AAVMException(f"Another machine with the name '{name}' already exists. "
                            f"Choose another name.")
