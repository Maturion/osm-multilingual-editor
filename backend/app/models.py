from typing import Literal

from pydantic import BaseModel

ObjectType = Literal["streets", "poi", "relations", "named", "named_no_highway"]
OsmType = Literal["node", "way", "relation"]


class FetchRequest(BaseModel):
    admin_id: int
    object_types: list[ObjectType]
    languages: list[str] = []


class OsmElement(BaseModel):
    osm_type: OsmType
    osm_id: int
    lat: float | None
    lon: float | None
    version: int
    tags: dict[str, str]


class FetchResponse(BaseModel):
    elements: list[OsmElement]


class AuthStatus(BaseModel):
    logged_in: bool
    username: str | None = None
    environment: str


class UploadElement(BaseModel):
    osm_type: OsmType
    osm_id: int
    tags: dict[str, str]


class UploadRequest(BaseModel):
    comment: str
    elements: list[UploadElement]


class UploadElementResult(BaseModel):
    osm_type: OsmType
    osm_id: int
    success: bool
    new_version: int | None = None
    error: str | None = None


class UploadResponse(BaseModel):
    changeset_id: int
    results: list[UploadElementResult]
