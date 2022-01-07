from typing import List

from termcolor import colored

from aavm.types import AAVMMachine, AAVMRuntime


Table = List[List[str]]


def table_machine(machine: AAVMMachine) -> Table:
    return [
        ["Name", machine.name],
        ["Path", machine.path],
        ["Description", machine.description],
        ["Version", machine.version],
        ["Runtime", machine.runtime.image],
        # ["Configuration", None],
        ["Machine", machine.machine.name],
    ]


def table_runtime(runtime: AAVMRuntime, downloaded: bool, official: bool) -> Table:
    return [
        ["Image", runtime.image],
        ["Description", runtime.description],
        ["Maintainer", runtime.maintainer],
        ["Downloaded", colored('Yes', 'green') if downloaded else colored('No', 'red')],
        ["Official", colored('Yes', 'green') if official else colored('No', 'red')],
    ]


def table_image(runtime: AAVMRuntime) -> Table:
    return [
        ["Image", runtime.image],
        ["Registry", str(runtime.registry)],
        ["Organization", runtime.organization],
        ["Repository", runtime.name],
        ["Tag", runtime.tag],
        ["Arch", runtime.arch]
    ]
