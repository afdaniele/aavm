import dataclasses
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from types import SimpleNamespace
from typing import List, Dict, Optional, Any, Union, ClassVar

import jsonschema
from docker.errors import NotFound
from docker.models.containers import Container

from aavm.cli import aavmlogger
from aavm.exceptions import AAVMException
from aavm.schemas import get_machine_schema, get_runtime_schema
from aavm.utils.docker import sanitize_image_name, merge_container_configs, RUNNING_STATUSES
from aavm.utils.misc import aavm_label
from cpk import cpkconfig
from cpk.machine import FromEnvMachine
from cpk.types import Machine as CPKMachine, DockerImageName, DockerImageRegistry
from cpk.utils.machine import get_machine

Arguments = List[str]
Environment = Dict[str, str]
ContainerConfiguration = Dict[str, Any]
RuntimeMetadata = Dict[str, Any]
MachineSettings = Dict[str, Any]


class ISerializable(ABC):

    @abstractmethod
    def serialize(self) -> Union[str, dict]:
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, *args, **kwargs) -> Any:
        pass


@dataclasses.dataclass
class AAVMRuntime(ISerializable):
    schema: str
    version: str
    description: str
    image: DockerImageName
    maintainer: str
    configuration: ContainerConfiguration
    metadata: RuntimeMetadata = dataclasses.field(default_factory=dict)
    downloaded: Optional[bool] = None
    official: bool = False

    _registry: ClassVar[Dict[str, 'AAVMRuntime']] = {}

    def __post_init__(self):
        # update registry
        self._registry[self.image.compile(allow_defaults=True)] = self

    def serialize(self) -> dict:
        return {
            "schema": self.schema,
            "version": self.version,
            "description": self.description,
            "image": dataclasses.asdict(self.image),
            "maintainer": self.maintainer,
            "metadata": self.metadata,
            "official": self.official
        }

    @classmethod
    def deserialize(cls, data: dict) -> 'AAVMRuntime':
        # get image name
        image = DockerImageName(**data["image"])
        # update registry if any is given
        if "registry" in data["image"]:
            image.registry = DockerImageRegistry(**data["image"]["registry"])
        # create runtime object
        return AAVMRuntime(
            schema=data["schema"],
            version=data["version"],
            description=data["description"],
            image=image,
            maintainer=data["maintainer"],
            configuration={},
            metadata=data.get("metadata", {}),
            official=data.get("official", False)
        )

    @classmethod
    def from_image_name(cls, image: str) -> 'AAVMRuntime':
        image = sanitize_image_name(image)
        if image in cls._registry:
            return cls._registry[image]
        # (attempt to) load from disk
        from aavm import aavmconfig
        runtimes_dir = os.path.join(aavmconfig.path, "runtimes")
        runtime_dir = os.path.join(runtimes_dir, image)
        if not os.path.exists(runtime_dir) or not os.path.isdir(runtime_dir):
            raise AAVMException(f"Runtime with image '{image}' not found.")
        # load from disk
        return cls.from_disk(runtime_dir)

    # noinspection DuplicatedCode
    @classmethod
    def from_disk(cls, path: str) -> 'AAVMRuntime':
        # compile runtime file path
        runtime_file = os.path.join(path, "runtime.json")
        # make sure a config file exists
        if not os.path.exists(runtime_file):
            raise AAVMException(f"Path '{path}' does not contain a 'runtime.json' file.")
        if not os.path.isfile(runtime_file):
            raise AAVMException(f"Path '{runtime_file}' is not a file.")
        # load runtime file
        try:
            with open(runtime_file, "rt") as fin:
                data = json.load(fin)
        except json.JSONDecodeError as e:
            raise AAVMException(f"File '{runtime_file}' is not a valid JSON file. "
                                f"Error reads: {e}")
        # make sure the object we loaded is a dictionary
        if not isinstance(data, dict):
            raise AAVMException(f"File '{runtime_file}' must contain a JSON-serialized "
                                f"dictionary.")
        # make sure the object loaded contains the field 'schema'
        if "schema" not in data:
            raise AAVMException(f"File '{runtime_file}' must declare a field 'schema' "
                                f"at its root.")
        schema_version = data["schema"]
        # validate data against its declared schema
        schema = get_runtime_schema(schema_version)
        try:
            jsonschema.validate(data, schema=schema)
        except jsonschema.ValidationError as e:
            raise AAVMException(str(e))
        # create runtime object
        runtime = cls.deserialize(data)
        # load configuration file
        runtime.configuration = cls.load_configuration(path)
        # ---
        return runtime

    # noinspection DuplicatedCode
    @classmethod
    def load_configuration(cls, path: str) -> ContainerConfiguration:
        configuration_file = os.path.join(path, "configuration.json")
        # make sure the config file exists
        if not os.path.exists(configuration_file):
            raise AAVMException(f"Path '{path}' does not contain a 'configuration.json' file.")
        if not os.path.isfile(configuration_file):
            raise AAVMException(f"Path '{configuration_file}' is not a file.")
        # load configuration file
        try:
            with open(configuration_file, "rt") as fin:
                config = json.load(fin)
        except json.JSONDecodeError as e:
            raise AAVMException(f"File '{configuration_file}' is not a valid JSON file. "
                                f"Error reads: {e}")
        # ---
        return config

    def to_disk(self):
        from aavm.config import aavmconfig
        # compile runtime dir path and make sure it exists on disk
        image_name = self.image.compile(allow_defaults=True)
        runtime_dir = os.path.join(aavmconfig.path, "runtimes", image_name)
        os.makedirs(runtime_dir, exist_ok=True)
        # compile runtime file path
        runtime_file = os.path.join(runtime_dir, "runtime.json")
        # serialize self to disk
        data = self.serialize()
        with open(runtime_file, "wt") as fout:
            json.dump(data, fout, indent=4)
        # write configuration to file
        configuration_file = os.path.join(runtime_dir, "configuration.json")
        with open(configuration_file, "wt") as fout:
            json.dump(self.configuration, fout, indent=4)


@dataclasses.dataclass
class MachineSettings(ISerializable):
    persistency: bool = False

    def serialize(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def deserialize(cls, data: dict) -> 'MachineSettings':
        return MachineSettings(**data)


@dataclasses.dataclass
class MachineLinks(ISerializable):
    machine: CPKMachine
    container: Optional[str]

    def serialize(self) -> dict:
        return {
            "machine": self.machine.name if not isinstance(self.machine, FromEnvMachine)
            else None,
            "container": self.container
        }

    @classmethod
    def deserialize(cls, machine: str, data: dict) -> 'MachineLinks':
        # reconstruct machine
        cpk_machine_name = data["machine"]
        cpk_machine = None
        # we have a name for the CPK machine
        if cpk_machine_name:
            cpk_machine = cpkconfig.machines.get(cpk_machine_name, None)
            if cpk_machine is None:
                raise AAVMException(f"AAVM Machine with name '{machine}' is set to run on the CPK "
                                    f"machine '{cpk_machine_name}' but such machine was not "
                                    f"found.")
        # get a default machine
        if cpk_machine is None:
            # noinspection PyTypeChecker
            cpk_machine = get_machine(SimpleNamespace(machine=None), cpkconfig.machines)
        # ---
        data["machine"] = cpk_machine
        # ---
        return MachineLinks(**data)


@dataclasses.dataclass
class AAVMMachine(ISerializable):
    schema: str
    version: str
    name: str
    path: str
    runtime: AAVMRuntime
    description: str
    configuration: ContainerConfiguration
    settings: MachineSettings
    links: MachineLinks

    _container: Optional['AAVMContainer'] = None

    # @property
    # def root(self) -> str:
    #     return os.path.realpath(os.path.join(self.path, "root"))

    @property
    def container_name(self) -> str:
        return f"aavm-machine-{self.name}"

    @property
    def machine(self) -> CPKMachine:
        return self.links.machine

    @property
    def container(self) -> Optional['AAVMContainer']:
        if self._container is None and self.links.container is not None:
            client = self.machine.get_client()
            container = None
            try:
                container = client.containers.get(self.links.container)
            except NotFound:
                # annotate that the container is gone
                self.links.container = None
                self.to_disk()
            # return container or nothing
            self._container = container
        # ---
        return self._container

    @property
    def running(self) -> bool:
        container = self.container
        if container is None:
            return False
        return container.status == "running"

    @property
    def status(self) -> str:
        container = self.container
        if container is None:
            return "down"
        return container.status

    def reset(self):
        # try to get an existing container for this machine
        container = self.container
        if container is not None:
            if container.status in RUNNING_STATUSES:
                raise AAVMException(f"Machine '{self.name}' is in status '{container.status}', "
                                    "you can only reset a machine after you stopped it.")
            else:
                aavmlogger.debug(f"Removing container '{container.name}'...")
                container.remove()
                aavmlogger.debug(f"Container '{container.name}' removed.")

        # # reset root file system
        # if root:
        #     client = docker.from_env()
        #     aavmlogger.debug(f"Removing root file system stored at '{self.root}'...")
        #     client.containers.run(
        #         image="alpine",
        #         remove=True,
        #         command=["rmdir", self.root],
        #         volumes={
        #             self.path: {'bind': self.path, 'mode': 'rw'}
        #         }
        #     )
        #     aavmlogger.debug(f"Root file system stored at '{self.root}' removed.")
        #     # recreate empty root
        #     self.make_root()

    # def make_root(self, exist_ok: bool = False):
    #     os.makedirs(self.root, exist_ok=exist_ok)

    def make_container(self) -> 'AAVMContainer':
        # collect configurations from runtime and machine definition
        runtime_cfg = self.runtime.configuration
        machine_cfg = self.configuration
        container_cfg = merge_container_configs(runtime_cfg, machine_cfg)
        # add image from the runtime to the container configutation
        container_cfg["image"] = self.runtime.image.compile()
        # define container's name
        container_cfg["name"] = self.container_name
        # add self.name label
        container_cfg["labels"] = {
            aavm_label("machine.name"): self.name
        }
        # make a new container for this machine
        config_str = json.dumps(container_cfg, indent=4)
        aavmlogger.debug(f"Creating container with configuration:\n\n{config_str}\n")
        client = self.machine.get_client()
        container = client.containers.create(**container_cfg)
        # ---
        return container

        # # mount root fs (if needed)
        # if self.settings.persistency:
        #     aavmlogger.debug("Persistency is enabled, mounting root file system to machine "
        #                      f"'{self.name}'...")
        #     try:
        #         self._mount_root()
        #     except AAVMException as e:
        #         aavmlogger.error(str(e))
        #         container_name = container.name
        #         aavmlogger.debug(f"Removing container '{container_name}'...")
        #         container.remove()
        #         aavmlogger.debug(f"Container '{container_name}' removed.")
        #     aavmlogger.debug(f"Root file system mounted on machine '{self.name}'.")

    # @property
    # def root_is_mounted(self) -> bool:
    #     # root is not mounted if not requested
    #     if not self.settings.persistency:
    #         return False
    #     # root is not mounted if container does not exist
    #     container = self.container
    #     if container is None:
    #         return False
    #     # root can only be mounted with 'overlay' storage driver
    #     fs_driver: str = container.attrs["Driver"]
    #     if not fs_driver.startswith("overlay"):
    #         return False
    #     # ---
    #     return True
    #
    # def _mount_root(self):
    #     # nothing to do if the root disk is already mounted
    #     if self.root_is_mounted:
    #         return
    #     # attempt to mount root file system
    #     root_dir = self.root
    #     container = self.container
    #     # make sure we are using 'overlay' driver
    #     fs_driver: str = container.attrs["Driver"]
    #     if not fs_driver.startswith("overlay"):
    #         raise AAVMException(f"Container '{container.name}' for machine '{self.name}' is "
    #                             f"using the file system driver '{fs_driver}' which is not "
    #                             f"supported for persistent root.")
    #     # make sure the container is stopped
    #     if container.status not in STOPPED_STATUSES:
    #         raise AAVMException(f"Container '{container.name}' for machine '{self.name}' has "
    #                             f"currently status '{container.status}'. The root can be mounted "
    #                             f"only while the container is in one of these statuses: "
    #                             f"{', '.join(STOPPED_STATUSES)}.")
    #     # find location of the machine's container's overlay
    #     container_overlay = str(Path(container.attrs["GraphDriver"]["Data"]["UpperDir"]).parent)
    #     # perform relinking of the overlay
    #     # refuse to do anything if the layer is not empty
    #     root_layer_num_files = len(os.listdir(root_layer))
    #     if root_layer_num_files > 0:
    #         raise AAVMException(f"Container '{container.name}' for machine '{self.name}' has a "
    #                             f"volatile non-empty root layer. This should not have happened, "
    #                             f"you need to recreate the container to recover.")
    #     # delete empty volatile root layer dir
    #     container_dir = str(Path(root_layer_dir).parent)
    #     client = self.machine.get_client()
    #     aavmlogger.debug(f"Machine '{self.name}': Removing empty directory '{root_layer_dir}'")
    #     client.containers.run(
    #         image="alpine",
    #         remove=True,
    #         command=["rmdir", root_layer_dir],
    #         volumes={
    #             container_dir: {'bind': container_dir, 'mode': 'rw'}
    #         }
    #     )
    #     # create symlink between the container's diff layer and the persistent root directory
    #     aavmlogger.debug(f"Machine '{self.name}': Making symlink '{root_dir}' -> "
    #                      f"'{root_layer_dir}'")
    #     client.containers.run(
    #         image="alpine",
    #         remove=True,
    #         command=["ln", "-s", root_dir, root_layer_dir],
    #         volumes={
    #             container_dir: {'bind': container_dir, 'mode': 'rw'}
    #         }
    #     )

    def serialize(self) -> dict:
        return {
            "schema": self.schema,
            "version": self.version,
            "runtime": self.runtime.image.compile(allow_defaults=True),
            "description": self.description,
            "settings": self.settings.serialize(),
            "links": self.links.serialize()
        }

    @classmethod
    def deserialize(cls, name: str, data: dict, path: Optional[str] = None) -> 'AAVMMachine':
        # get runtime
        runtime = AAVMRuntime.from_image_name(data["runtime"])
        # get configuration
        configuration = cls.load_configuration(path) if path else {}
        # get settings
        settings = MachineSettings.deserialize(data["settings"])
        # get links
        links = MachineLinks.deserialize(name, data["links"])
        # reconstruct AAVM machine object
        return AAVMMachine(
            schema=data["schema"],
            version=data["version"],
            runtime=runtime,
            name=name,
            path=path,
            description=data["description"],
            configuration=configuration,
            settings=settings,
            links=links
        )

    def to_disk(self):
        from aavm import aavmconfig
        aavm_config_dir = aavmconfig.path
        machine_dir = os.path.join(aavm_config_dir, "machines", self.name)
        # make sure the machine's dir exists
        os.makedirs(machine_dir, exist_ok=True)
        # compile machine file
        machine_file = os.path.join(machine_dir, "machine.json")
        # serialize machine
        data = self.serialize()
        # write dictionary to disk
        with open(machine_file, "wt") as fout:
            json.dump(data, fout, indent=4)
        # write configuration to file
        configuration_file = os.path.join(machine_dir, "configuration.json")
        with open(configuration_file, "wt") as fout:
            json.dump(self.configuration, fout, indent=4)

    # noinspection DuplicatedCode
    @classmethod
    def from_disk(cls, path: str) -> 'AAVMMachine':
        path = os.path.abspath(path)
        # make sure the given path exists
        if not os.path.exists(path):
            raise AAVMException(f"Path '{path}' does not exist.")
        # make sure the given path is a directory
        if not os.path.isdir(path):
            raise AAVMException(f"Path '{path}' is not a directory.")
        # compile machine file path
        machine_file = os.path.join(path, "machine.json")
        # make sure a config file exists
        if not os.path.exists(machine_file):
            raise AAVMException(f"Path '{path}' does not contain a 'machine.json' file.")
        if not os.path.isfile(machine_file):
            raise AAVMException(f"Path '{machine_file}' is not a file.")
        # load machine file
        try:
            with open(machine_file, "rt") as fin:
                data = json.load(fin)
        except json.JSONDecodeError as e:
            raise AAVMException(f"File '{machine_file}' is not a valid JSON file. "
                                f"Error reads: {e}")
        # make sure the object we loaded is a dictionary
        if not isinstance(data, dict):
            raise AAVMException(f"File '{machine_file}' must contain a JSON-serialized "
                                f"dictionary.")
        # make sure the object loaded contains the field 'schema'
        if "schema" not in data:
            raise AAVMException(f"File '{machine_file}' must declare a field 'schema' "
                                f"at its root.")
        schema_version = data["schema"]
        # validate data against its declared schema
        schema = get_machine_schema(schema_version)
        try:
            jsonschema.validate(data, schema=schema)
        except jsonschema.ValidationError as e:
            raise AAVMException(str(e))
        # deserialize
        machine = cls.deserialize(
            name=Path(path).stem,
            path=path,
            data=data
        )
        # load configuration file
        machine.configuration = cls.load_configuration(path)
        # ---
        return machine

    @classmethod
    def load_configuration(cls, path: str) -> ContainerConfiguration:
        configuration_file = os.path.join(path, "configuration.json")
        # make sure the config file exists
        if not os.path.exists(configuration_file):
            raise AAVMException(f"Path '{path}' does not contain a 'configuration.json' file.")
        if not os.path.isfile(configuration_file):
            raise AAVMException(f"Path '{configuration_file}' is not a file.")
        # load configuration file
        try:
            with open(configuration_file, "rt") as fin:
                config = json.load(fin)
        except json.JSONDecodeError as e:
            raise AAVMException(f"File '{configuration_file}' is not a valid JSON file. "
                                f"Error reads: {e}")
        return config


@dataclasses.dataclass
class AAVMConfiguration:
    path: str

    _machines: Dict[str, AAVMMachine] = dataclasses.field(init=False, default=None)

    @property
    def machines(self) -> Dict[str, AAVMMachine]:
        if self._machines is None:
            from aavm.utils.machine import load_machines
            self._machines = load_machines(os.path.join(self.path, "machines"))
        return self._machines


class AAVMContainer(Container):
    pass
