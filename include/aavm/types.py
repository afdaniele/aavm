import dataclasses
from typing import List, Dict, Optional

from .constants import CANONICAL_ARCH

Arguments = List[str]


@dataclasses.dataclass
class AAVMFileMapping:
    source: str
    destination: str
    required: bool

    def __copy__(self):
        return self.__deepcopy__({})

    def __deepcopy__(self, memo):
        return AAVMFileMapping(
            source=self.source,
            destination=self.destination,
            required=self.required
        )

    @staticmethod
    def from_dict(data: dict) -> 'AAVMFileMapping':
        return AAVMFileMapping(
            source=data['source'],
            destination=data['destination'],
            required=data.get('required', False)
        )


@dataclasses.dataclass
class AAVMMachineInfo:
    name: str
    mappings: List[AAVMFileMapping] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class DockerImageRegistry:
    hostname: str = "docker.io"
    port: int = 5000

    def is_default(self) -> bool:
        defaults = DockerImageRegistry()
        # add - registry
        if self.hostname != defaults.hostname or self.port != defaults.port:
            return False
        return True

    def compile(self, allow_defaults: bool = False) -> Optional[str]:
        defaults = DockerImageRegistry()
        name = None if not allow_defaults else f"{defaults.hostname}"
        # add - registry
        if self.hostname != defaults.hostname:
            if self.port != defaults.port:
                name += f"{self.hostname}:{self.port}"
            else:
                name += f"{self.hostname}"
        # ---
        return name

    def __str__(self) -> str:
        return self.compile(allow_defaults=True)


@dataclasses.dataclass
class DockerImageName:
    """
    The official Docker image naming convention is:

        [REGISTRY[:PORT] /] USER / REPO [:TAG]

    """
    repository: str
    user: str = "library"
    registry: DockerImageRegistry = dataclasses.field(default_factory=DockerImageRegistry)
    tag: str = "latest"
    arch: Optional[str] = None

    def compile(self) -> str:
        name = ""
        defaults = DockerImageName("_")
        # add - registry
        registry = self.registry.compile()
        if registry:
            name += f"{registry}/"
        # add - user
        if self.user != defaults.user:
            name += f"{self.user}/"
        # add - repository
        name += self.repository
        # add - tag
        if self.tag != defaults.tag or self.arch:
            name += f":{self.tag}"
        # add - arch
        if self.arch:
            name += f"-{self.arch}"
        # ---
        return name

    @staticmethod
    def from_image_name(name: str) -> 'DockerImageName':
        input_parts = name.split('/')
        image = DockerImageName(
            repository="X"
        )
        # ---
        registry = None
        # ---
        if len(input_parts) == 3:
            registry, image.user, image_tag = input_parts
        elif len(input_parts) == 2:
            image.user, image_tag = input_parts
        elif len(input_parts) == 1:
            image_tag = input_parts[0]
        else:
            raise ValueError("Invalid Docker image name")
        image.repository, tag, *_ = image_tag.split(':') + ["latest"]
        for arch in set(CANONICAL_ARCH.values()):
            if tag.endswith(f"-{arch}"):
                tag = tag[:-(len(arch) + 1)]
                image.arch = arch
                break
        image.tag = tag
        if registry:
            image.registry.hostname, image.registry.port, *_ = registry.split(':') + [5000]
        # ---
        return image

    def __str__(self) -> str:
        return f"""\
Registry:\t{str(self.registry)}
User:\t\t{self.user}
Repository:\t{self.repository}
Tag:\t\t{self.tag}
Arch:\t\t{self.arch}
        """


@dataclasses.dataclass
class AAVMConfiguration:
    path: str
    machines: Dict[str, AAVMMachineInfo]
