"""Pydantic models for SudoLabs targets."""

from pydantic import BaseModel, Field


class Hint(BaseModel):
    level: int
    text: str


class Flag(BaseModel):
    type: str  # "user", "root", or "stage"
    path: str  # Path inside the container


class Stage(BaseModel):
    name: str
    description: str
    tools_suggested: list[str] = Field(default_factory=list)
    flag: Flag
    points: int = 100
    hints: list[Hint] = Field(default_factory=list)


class Service(BaseModel):
    name: str
    port: int
    protocol: str = "tcp"
    description: str = ""


class PostStartCommand(BaseModel):
    container: str
    command: str


class NetworkConfig(BaseModel):
    name: str
    subnet: str


class DockerConfig(BaseModel):
    compose_file: str = "docker-compose.yml"
    build_required: bool = True
    networks: list[NetworkConfig] = Field(default_factory=list)
    post_start: list[PostStartCommand] = Field(default_factory=list)


class Target(BaseModel):
    name: str
    slug: str
    version: str = "1.0.0"
    difficulty: str  # "easy", "medium", "hard", "elite"
    category: str = ""  # Injected from parent directory name
    description: str
    briefing: str = ""
    author: str = "sudolabs-team"
    cves: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    services: list[Service] = Field(default_factory=list)
    attack_chain: list[Stage] = Field(default_factory=list)
    par_time_minutes: int = 60
    docker: DockerConfig = Field(default_factory=DockerConfig)

    @property
    def total_points(self) -> int:
        return sum(stage.points for stage in self.attack_chain)

    @property
    def stage_count(self) -> int:
        return len(self.attack_chain)
