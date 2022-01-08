from typing import List

import yaml
from termcolor import colored

from aavm.types import AAVMMachine, AAVMRuntime, ContainerConfiguration

Table = List[List[str]]


def table_machine(machine: AAVMMachine) -> Table:
    return [
        ["Name", machine.name],
        ["Path", machine.path],
        ["Description", machine.description],
        ["Version", machine.version],
        ["Runtime", machine.runtime.image.compile()],
        ["Machine", machine.machine.name],
    ]


def table_runtime(runtime: AAVMRuntime) -> Table:
    return [
        ["Description", runtime.description],
        ["Maintainer", runtime.maintainer],
        ["Downloaded", colored('Yes', 'green') if runtime.downloaded else colored('No', 'red')],
        ["Official", colored('Yes', 'green') if runtime.official else colored('No', 'red')],
    ]


def table_image(runtime: AAVMRuntime) -> Table:
    return [
        ["Image", runtime.image.compile()],
        ["Registry", str(runtime.image.registry)],
        ["User", runtime.image.user],
        ["Repository", runtime.image.repository],
        ["Tag", runtime.image.tag],
        ["Arch", runtime.image.arch]
    ]


def table_configuration(configuration: ContainerConfiguration) -> Table:
    table = []
    for k, v in configuration.items():
        field = k.title().replace("_", " ")
        value = str(v)
        if isinstance(v, dict):
            # noinspection PyBroadException
            try:
                value = yaml.dump(v)
            except BaseException:
                pass
        table.append([field, value])
    # make sure the table is not empty
    if len(table) <= 0:
        table = [["          (empty)          "]]
    # ---
    return table
