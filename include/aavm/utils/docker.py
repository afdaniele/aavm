from docker import DockerClient

from aavm.utils.progress_bar import ProgressBar
from cpk.types import Machine


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
