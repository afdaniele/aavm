from docker import DockerClient

from aavm.utils.progress_bar import ProgressBar
from cpk.types import Machine, DockerImageName

ALL_STATUSES = [
    "created", "restarting", "running", "removing", "paused", "exited", "dead"
]
STOPPED_STATUSES = [
    "created", "exited", "dead"
]
UNSTABLE_STATUSES = [
    "restarting", "removing"
]
RUNNING_STATUSES = [
    "running", "paused"
]


# noinspection DuplicatedCode
def pull_image(machine: Machine, image: str, progress: bool = True):
    client: DockerClient = machine.get_client()
    layers = set()
    pulled = set()
    pbar = ProgressBar() if progress else None
    for line in client.api.pull(image, stream=True, decode=True):
        if "id" not in line or "status" not in line:
            continue
        layer_id = line["id"]
        layers.add(layer_id)
        if line["status"] in ["Already exists", "Pull complete"]:
            pulled.add(layer_id)
        # update progress bar
        if progress:
            percentage = max(0.0, min(1.0, len(pulled) / max(1.0, len(layers)))) * 100.0
            pbar.update(percentage)
    if progress:
        pbar.done()


def remove_image(machine: Machine, image: str):
    client: DockerClient = machine.get_client()
    client.images.remove(image)


def merge_container_configs(*args) -> dict:
    out = {}
    for arg in args:
        assert isinstance(arg, dict)
        for k, v in arg.items():
            if k not in out:
                out[k] = v
            else:
                if not isinstance(arg[k], type(out[k])):
                    raise ValueError(f"Type clash '{type(out[k])}' !== '{type(arg[k])}' "
                                     f"for key '{k}'.")
                if isinstance(out[k], list):
                    out[k].extend(arg[k])
                elif isinstance(out[k], dict):
                    out[k].update(arg[k])
                else:
                    out[k] = arg[k]
    return out


def sanitize_image_name(image: str) -> str:
    return DockerImageName.from_image_name(image).compile(allow_defaults=True)
