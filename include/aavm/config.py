import os

from aavm.constants import AAVM_CONFIG_DIR
from aavm.types import AAVMConfiguration
from aavm.utils.machine import load_machines


aavmconfig: AAVMConfiguration = AAVMConfiguration(
    path=AAVM_CONFIG_DIR,
    machines=load_machines(os.path.join(AAVM_CONFIG_DIR, "machines"))
)

__all__ = [
    "aavmconfig"
]
