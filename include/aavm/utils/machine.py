import glob
import os
from pathlib import Path
from typing import Dict, Optional

from aavm.cli import aavmlogger
from aavm.exceptions import AAVMException
from aavm.types import AAVMMachine, AAVMContainer
from aavm.utils.misc import aavm_label


def load_machines(path: str) -> Dict[str, AAVMMachine]:
    machines = {}
    # iterate over the machines on disk
    for machine_cfg_fpath in glob.glob(os.path.join(path, '*/machine.json')):
        machine_dir = Path(machine_cfg_fpath).parent
        machine_name = machine_dir.stem
        try:
            machine = AAVMMachine.from_disk(str(machine_dir))
        except (KeyError, ValueError) as e:
            aavmlogger.warning(f"An error occurred while loading the machine '{machine_name}', "
                               f"the error reads:\n{str(e)}")
            continue
        # we have loaded a valid machine
        machines[machine_name] = machine
    # ---
    return machines


def get_container(machine: AAVMMachine) -> Optional[AAVMContainer]:
    client = machine.machine.get_client()
    containers = client.containers.list(
        filters={
            "label": aavm_label("machine.name", machine.name),
        }
    )
    # make sure at most one container serves a single machine
    if len(containers) > 1:
        containers_list = "\t- " + "\n\t- ".join([str(c.id) for c in containers])
        raise AAVMException(f"{len(containers)} containers found for the machine {machine.name}. "
                            f"This should not have happened. Only one container can exist per "
                            f"machine. The clashing containers have the following IDs, manually "
                            f"remove them (optionally leave only one) and then retry.\n\n"
                            f"Containers:\n"
                            f"{containers_list}\n")
    # return container or nothing
    return containers[0] if containers else None
