import dataclasses
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from types import SimpleNamespace
from typing import List, Dict, Optional, Any, Union

import jsonschema
from docker.models.containers import Container

from cpk.utils.machine import get_machine

from cpk.machine import FromEnvMachine

from cpk import cpkconfig

from aavm.exceptions import AAVMException
from aavm.schemas import get_machine_schema
from cpk.types import Machine as CPKMachine, DockerImageName

Arguments = List[str]
Arch = str
Environment = dict
ContainerConfiguration = dict


class ISerializable(ABC):

    @abstractmethod
    def serialize(self) -> Union[str, dict]:
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, data: Any) -> Any:
        pass


@dataclasses.dataclass
class DataclassSerializable(ISerializable):

    def serialize(self) -> dict:
        data = {}
        for field in dataclasses.fields(self):
            key = field.name
            if key.startswith("_"):
                continue
            value = getattr(self, key)
            if isinstance(value, ISerializable):
                value = value.serialize()
            data[key] = value
        return data

    @classmethod
    def deserialize(cls, data) -> 'DataclassSerializable':
        out = {}
        for field in dataclasses.fields(cls):
            key = field.name
            if key.startswith("_"):
                continue
            value = data[key]
            if issubclass(field.type, ISerializable):
                value = field.type.deserialize(value)
            out[key] = value
        return cls(**out)


@dataclasses.dataclass
class AAVMRuntime(DataclassSerializable):
    name: str
    tag: str
    organization: str
    description: str
    maintainer: str
    arch: Arch
    configuration: ContainerConfiguration
    registry: Optional[str] = None
    metadata: Dict[str, Any] = dataclasses.field(default_factory=dict)
    downloaded: Optional[bool] = None

    def serialize(self) -> str:
        return self.image

    @classmethod
    def deserialize(cls, image: str) -> 'AAVMRuntime':
        return cls.from_docker_image_obj(DockerImageName.from_image_name(image))

    @classmethod
    def from_docker_image_obj(cls, image: DockerImageName) -> 'AAVMRuntime':
        # flatten registry
        registry = image.registry.compile() if image.registry else None
        # create runtime descriptor
        return AAVMRuntime(
            name=image.repository,
            tag=image.tag,
            organization=image.user,
            description="",
            maintainer="",
            arch=image.arch,
            registry=registry,
            metadata={},
            configuration={}
        )

    @property
    def image(self) -> str:
        registry = self.registry or ""
        organization = self.organization
        name = self.name
        tag = self.tag
        arch = self.arch
        # compile image name
        return f"{registry}/{organization}/{name}:{tag}-{arch}".lstrip("/")


class AAVMMachineRoot(str, ISerializable):
    pass


@dataclasses.dataclass
class AAVMMachine(DataclassSerializable):
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
        # do not store 'name', 'configuration' and 'path'
        del data["name"]
        del data["path"]
        del data["configuration"]
        # write dictionary to disk
        with open(machine_file, "wt") as fout:
            json.dump(data, fout, indent=4)
        # write configuration to file
        configuration_file = os.path.join(machine_dir, "configuration.json")
        with open(configuration_file, "wt") as fout:
            json.dump(self.configuration, fout, indent=4)

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
        # populate 'name', 'configuration' and 'path'
        data["name"] = Path(path).stem
        data["path"] = path
        data["configuration"] = {}
        # deserialize
        machine = cls.deserialize(data)
        # load configuration file
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
        machine.configuration = config
        # expand CPK Machine field
        namespace = SimpleNamespace(machine=None)
        if data["machine"] != "from-environment":
            namespace.machine = data["machine"]
        # noinspection PyTypeChecker
        machine.machine = get_machine(namespace, cpkconfig.machines)
        # ---
        return machine


@dataclasses.dataclass
class AAVMConfiguration:
    path: str
    machines: Dict[str, AAVMMachine]


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
