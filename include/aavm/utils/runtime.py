import base64
import copy
import glob
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

import docker
import jsonschema
import requests

from aavm.exceptions import AAVMException
from aavm.schemas import get_index_schema
from cpk.types import Machine

from aavm.cli import aavmlogger
from aavm.constants import AAVM_RUNTIMES_INDEX_URL, AAVM_RUNTIMES_INDEX_VERSION
from aavm.types import AAVMRuntime


def fetch_remote_runtimes(check_downloaded: bool = False, machine: Optional[Machine] = None) -> \
        List[AAVMRuntime]:
    # make sure we are given a machine when we want to know whether a runtime is downloaded
    if check_downloaded and not machine:
        raise ValueError("You need to provide a machine to check whether a runtime is downloaded")
    # get list of runtimes available
    index_url = AAVM_RUNTIMES_INDEX_URL
    aavmlogger.debug(f"GET: {index_url}")
    runtimes: List[Dict[str, Any]] = requests.get(index_url).json()
    # validate data against its declared schema
    schema = get_index_schema(AAVM_RUNTIMES_INDEX_VERSION)
    try:
        jsonschema.validate(runtimes, schema=schema)
    except jsonschema.ValidationError as e:
        raise AAVMException(str(e))
    # process runtimes
    out: List[AAVMRuntime] = []
    for runtime in runtimes:
        for arch in runtime["image"]["arch"]:
            data = copy.deepcopy(runtime)
            data["image"]["arch"] = arch
            r = AAVMRuntime.deserialize(data)
            # add configuration as well
            r.configuration = data["configuration"]
            # mark this runtime as official (it is coming from the index after all)
            r.official = True
            # check whether it is downloaded already
            if check_downloaded:
                try:
                    machine.get_client().images.get(r.image.compile())
                    r.downloaded = True
                except docker.errors.ImageNotFound:
                    r.downloaded = False
            # add runtime to output
            out.append(r)
    # ---
    return out


def get_known_runtimes(machine: Optional[Machine] = None) -> List[AAVMRuntime]:
    from aavm import aavmconfig
    runtimes_dir = os.path.join(aavmconfig.path, "runtimes")
    runtime_pattern = os.path.join(runtimes_dir, "**/runtime.json")
    # iterate over the runtimes on disk
    runtimes = []
    for runtime_cfg_fpath in glob.glob(runtime_pattern, recursive=True):
        runtime_dir = Path(runtime_cfg_fpath).parent
        runtime_name = os.path.relpath(runtime_dir, runtimes_dir)
        try:
            runtime = AAVMRuntime.from_disk(str(runtime_dir))
        except (KeyError, ValueError) as e:
            aavmlogger.warning(f"An error occurred while loading the runtime '{runtime_name}', "
                               f"the error reads:\n{str(e)}")
            continue
        # check whether the runtime is available on the given machine (if any)
        if machine is not None:
            try:
                machine.get_client().images.get(runtime.image.compile())
                runtime.downloaded = True
            except docker.errors.ImageNotFound:
                runtime.downloaded = False
        # we have loaded a valid runtime
        runtimes.append(runtime)
    # ---
    return runtimes
