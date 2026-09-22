import os
from dataclasses import dataclass
from pathlib import Path

import yaml

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = BACKEND_DIR / "config.yaml"


@dataclass
class EnvironmentConfig:
    osm_base_url: str
    oauth_authorize_url: str
    oauth_token_url: str
    client_id: str
    client_secret: str


@dataclass
class Settings:
    environment: str
    overpass_url: str
    poi_tags: list[str]
    frontend_url: str
    redirect_uri: str
    session_secret: str
    environments: dict[str, EnvironmentConfig]

    @property
    def active(self) -> EnvironmentConfig:
        return self.environments[self.environment]


def load_settings(path: Path | None = None) -> Settings:
    config_path = path or Path(os.environ.get("OSM_EDITOR_CONFIG", DEFAULT_CONFIG_PATH))
    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found at {config_path}. "
            f"Copy config.example.yaml to config.yaml and fill in your OAuth credentials."
        )

    with open(config_path) as f:
        raw = yaml.safe_load(f)

    environments = {
        name: EnvironmentConfig(**env_raw) for name, env_raw in raw["environments"].items()
    }

    return Settings(
        environment=raw["environment"],
        overpass_url=raw["overpass_url"],
        poi_tags=raw["poi_tags"],
        frontend_url=raw["frontend_url"],
        redirect_uri=raw["redirect_uri"],
        session_secret=raw["session_secret"],
        environments=environments,
    )


settings = load_settings()
