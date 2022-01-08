from aavm.constants import AAVM_CONFIG_DIR
from aavm.types import AAVMConfiguration


aavmconfig: AAVMConfiguration = AAVMConfiguration(
    path=AAVM_CONFIG_DIR
)

__all__ = [
    "aavmconfig"
]
