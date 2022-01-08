import base64
import dataclasses
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from types import SimpleNamespace
from typing import List, Dict, Optional, Any, Union, ClassVar

import jsonschema
from docker.models.containers import Container

from aavm.utils.docker import sanitize_image_name
from cpk.utils.machine import get_machine

from cpk.machine import FromEnvMachine

from cpk import cpkconfig

from aavm.exceptions import AAVMException
from aavm.schemas import get_machine_schema, get_runtime_schema
from cpk.types import Machine as CPKMachine, DockerImageName, DockerImageRegistry

Arguments = List[str]
Environment = Dict[str, str]
ContainerConfiguration = Dict[str, Any]
RuntimeMetadata = Dict[str, Any]


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


class AAVMMachineRoot(str, ISerializable):
    pass


@dataclasses.dataclass
class AAVMMachine(ISerializable):
    schema: str
    version: str
    name: str
    path: str
    runtime: AAVMRuntime
    description: str
    configuration: ContainerConfiguration
    machine: CPKMachine

    _container: Optional['AAVMContainer'] = None

    @property
    def root(self) -> AAVMMachineRoot:
        return AAVMMachineRoot(os.path.join(self.path, "root"))

    @property
    def container_name(self) -> str:
        return f"aavm-machine-{self.name}"

    @property
    def container(self) -> Optional['AAVMContainer']:
        from aavm.utils.machine import get_container
        if self._container is None:
            self._container = get_container(self)
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

    def make_root(self, exist_ok: bool = False):
        os.makedirs(self.root, exist_ok=exist_ok)

    def serialize(self) -> dict:
        return {
            "schema": self.schema,
            "version": self.version,
            "runtime": self.runtime.image.compile(allow_defaults=True),
            "description": self.description,
            "machine": self.machine.name,
        }

    @classmethod
    def deserialize(cls, name: str, data: dict, path: Optional[str] = None) -> 'AAVMMachine':
        # get runtime
        runtime = AAVMRuntime.from_image_name(data["runtime"])
        # get configuration
        configuration = cls.load_configuration(path) if path else {}
        # get machine
        cpk_machine_name = data["machine"]
        cpk_machine = None
        if cpk_machine_name:
            cpk_machine = cpkconfig.machines.get(cpk_machine_name, None)
            if cpk_machine is None:
                raise AAVMException(f"AAVM Machine with name '{name}' is set to run on the CPK "
                                    f"machine '{cpk_machine_name}' but such machine was not found.")
        # reconstruct AAVM machine object
        return AAVMMachine(
            schema=data["schema"],
            version=data["version"],
            runtime=runtime,
            name=name,
            path=path,
            description=data["description"],
            configuration=configuration,
            machine=cpk_machine
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
        # store only the machine's name
        data["machine"] = self.machine.name if not isinstance(self.machine, FromEnvMachine) \
            else None
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
        # expand CPK Machine field
        namespace = SimpleNamespace(machine=None)
        if data["machine"] != "from-environment":
            namespace.machine = data["machine"]
        # noinspection PyTypeChecker
        machine.machine = get_machine(namespace, cpkconfig.machines)
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

# @dataclasses.dataclass
# class AAVMFileMapping:
#     source: str
#     destination: str
#     required: bool
#
#     def __copy__(self):
#         return self.__deepcopy__({})
#
#     def __deepcopy__(self, memo):
#         return AAVMFileMapping(
#             source=self.source,
#             destination=self.destination,
#             required=self.required
#         )
#
#     @staticmethod
#     def from_dict(data: dict) -> 'AAVMFileMapping':
#         return AAVMFileMapping(
#             source=data['source'],
#             destination=data['destination'],
#             required=data.get('required', False)
#         )


# @dataclasses.dataclass
# class AAVMMachineInfo:
#     name: str
#     mappings: List[AAVMFileMapping] = dataclasses.field(default_factory=list)


# @dataclasses.dataclass
# class DockerImageRegistry:
#     hostname: str = "docker.io"
#     port: int = 5000
#
#     def is_default(self) -> bool:
#         defaults = DockerImageRegistry()
#         # add - registry
#         if self.hostname != defaults.hostname or self.port != defaults.port:
#             return False
#         return True
#
#     def compile(self, allow_defaults: bool = False) -> Optional[str]:
#         defaults = DockerImageRegistry()
#         name = None if not allow_defaults else f"{defaults.hostname}"
#         # add - registry
#         if self.hostname != defaults.hostname:
#             if self.port != defaults.port:
#                 name += f"{self.hostname}:{self.port}"
#             else:
#                 name += f"{self.hostname}"
#         # ---
#         return name
#
#     def __str__(self) -> str:
#         return self.compile(allow_defaults=True)


# @dataclasses.dataclass
# class DockerImageName:
#     """
#     The official Docker image naming convention is:
#
#         [REGISTRY[:PORT] /] USER / REPO [:TAG]
#
#     """
#     repository: str
#     user: str = "library"
#     registry: DockerImageRegistry = dataclasses.field(default_factory=DockerImageRegistry)
#     tag: str = "latest"
#     arch: Optional[str] = None
#
#     def compile(self) -> str:
#         name = ""
#         defaults = DockerImageName("_")
#         # add - registry
#         registry = self.registry.compile()
#         if registry:
#             name += f"{registry}/"
#         # add - user
#         if self.user != defaults.user:
#             name += f"{self.user}/"
#         # add - repository
#         name += self.repository
#         # add - tag
#         if self.tag != defaults.tag or self.arch:
#             name += f":{self.tag}"
#         # add - arch
#         if self.arch:
#             name += f"-{self.arch}"
#         # ---
#         return name
#
#     @staticmethod
#     def from_image_name(name: str) -> 'DockerImageName':
#         input_parts = name.split('/')
#         image = DockerImageName(
#             repository="X"
#         )
#         # ---
#         registry = None
#         # ---
#         if len(input_parts) == 3:
#             registry, image.user, image_tag = input_parts
#         elif len(input_parts) == 2:
#             image.user, image_tag = input_parts
#         elif len(input_parts) == 1:
#             image_tag = input_parts[0]
#         else:
#             raise ValueError("Invalid Docker image name")
#         image.repository, tag, *_ = image_tag.split(':') + ["latest"]
#         for arch in set(CANONICAL_ARCH.values()):
#             if tag.endswith(f"-{arch}"):
#                 tag = tag[:-(len(arch) + 1)]
#                 image.arch = arch
#                 break
#         image.tag = tag
#         if registry:
#             image.registry.hostname, image.registry.port, *_ = registry.split(':') + [5000]
#         # ---
#         return image
#
#     def __str__(self) -> str:
#         return f"""\
# Registry:\t{str(self.registry)}
# User:\t\t{self.user}
# Repository:\t{self.repository}
# Tag:\t\t{self.tag}
# Arch:\t\t{self.arch}
#         """


