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
