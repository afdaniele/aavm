import os

from cpk.constants import CPK_CONFIG_DIR
from cpk.types import CPKConfiguration
from cpk.utils.machine import load_machines


aavmconfig: CPKConfiguration = CPKConfiguration(
    path=CPK_CONFIG_DIR,
    machines=load_machines(os.path.join(CPK_CONFIG_DIR, "machines"))
)

__all__ = [
    "aavmconfig"
]
