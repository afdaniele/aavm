from typing import Optional, List, Dict, Any

import docker
import requests
from cpk.types import Machine, DockerImageName

from aavm.cli import aavmlogger
from aavm.constants import AAVM_RUNTIMES_INDEX_URL
from aavm.types import AAVMRuntime
from aavm.utils.misc import aavm_label


def fetch_remote_runtimes(check_downloaded: bool = False, machine: Optional[Machine] = None) -> \
        List[AAVMRuntime]:
    # make sure we are given a machine when we want to know whether a runtime is downloaded
    if check_downloaded and not machine:
        raise ValueError("You need to provide a machine to check whether a runtime is downloaded")
    # get list of runtimes available
    index_url = AAVM_RUNTIMES_INDEX_URL
    aavmlogger.debug(f"GET: {index_url}")
    runtimes: List[Dict[str, Any]] = requests.get(index_url).json()
    # process runtimes
    out: List[AAVMRuntime] = []
    for runtime in runtimes:
        for arch in runtime["arch"]:
            r = AAVMRuntime(
                name=runtime["name"],
                tag=runtime["tag"],
                organization=runtime["organization"],
                description=runtime["description"],
                maintainer=runtime["maintainer"],
                arch=arch,
                configuration=runtime.get("configuration", {}),
                registry=runtime.get("registry", None),
                metadata=runtime.get("metadata", {})
            )
            # check whether it is downloaded already
            if check_downloaded:
                try:
                    machine.get_client().images.get(r.image)
                    r.downloaded = True
                except docker.errors.ImageNotFound:
                    r.downloaded = False
            # add runtime to output
            out.append(r)
    # ---
    return out


def fetch_machine_runtimes(machine: Machine) -> List[AAVMRuntime]:
    client = machine.get_client()
    runtime_label = aavm_label("runtime", "1")
    runtimes = client.images.list(filters={"label": runtime_label})
    out: List[AAVMRuntime] = []
    # get runtime descriptions from images
    for runtime in runtimes:
        names = runtime.tags
        # we don't consider runtimes that do not have a name
        if len(names) <= 0:
            continue
        # parse best name
        image: Optional[DockerImageName] = None
        for name in names:
            try:
                image = DockerImageName.from_image_name(name)
            except ValueError:
                pass
        # we don't consider runtimes that do not have at least a valid name
        if image is None:
            continue
        # flatten registry
        registry = image.registry.compile() if image.registry else None
        # create runtime descriptor
        r = AAVMRuntime(
            name=image.repository,
            tag=image.tag,
            organization=image.user,
            description=runtime.labels.get(aavm_label("environment.description")),
            maintainer=runtime.labels.get(aavm_label("environment.maintainer")),
            arch=runtime.labels.get(aavm_label("environment.arch")),
            configuration={},
            registry=registry,
            metadata=runtime.labels.get(aavm_label("environment.metadata"), {})
        )
        # add runtime to output
        out.append(r)
    # ---
    return out
