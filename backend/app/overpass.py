import re

import httpx

from app.models import ObjectType, OsmElement

OVERPASS_TIMEOUT_SECONDS = 90
USER_AGENT = "osm-multilingual-editor/0.1"


NAME_PRESENCE_FILTER = '[~"^name(:.+)?$"~"."]'


def _poi_regex(poi_tags: list[str]) -> str:
    escaped = "|".join(re.escape(tag) for tag in poi_tags)
    return f"^({escaped})$"


def build_query(admin_id: int, object_types: list[ObjectType], poi_tags: list[str]) -> str:
    # Every category requires at least one name/name:<lang> tag to be present -
    # this tool is for editing names, not for browsing unnamed infrastructure.
    clauses = []
    if "streets" in object_types:
        clauses.append(f'way["highway"]{NAME_PRESENCE_FILTER}(area.searchArea);')
    if "poi" in object_types:
        regex = _poi_regex(poi_tags)
        clauses.append(f'nwr[~"{regex}"~"."]{NAME_PRESENCE_FILTER}(area.searchArea);')
    if "relations" in object_types:
        clauses.append(f"relation{NAME_PRESENCE_FILTER}(area.searchArea);")
    if "named" in object_types:
        clauses.append(f"nwr{NAME_PRESENCE_FILTER}(area.searchArea);")
    if "named_no_highway" in object_types:
        clauses.append(f'nwr{NAME_PRESENCE_FILTER}[!"highway"](area.searchArea);')

    if not clauses:
        raise ValueError("At least one object type must be selected")

    clauses_str = "\n  ".join(clauses)

    return f"""
[out:json][timeout:{OVERPASS_TIMEOUT_SECONDS}];
relation({admin_id})->.admin;
.admin map_to_area -> .searchArea;
(
  {clauses_str}
) -> .matched;
(.matched; - .admin;);
out center meta;
""".strip()


def _extract_lat_lon(element: dict) -> tuple[float | None, float | None]:
    if "lat" in element and "lon" in element:
        return element["lat"], element["lon"]
    center = element.get("center")
    if center:
        return center["lat"], center["lon"]
    return None, None


async def fetch_elements(
    overpass_url: str, admin_id: int, object_types: list[ObjectType], poi_tags: list[str]
) -> list[OsmElement]:
    query = build_query(admin_id, object_types, poi_tags)

    async with httpx.AsyncClient(timeout=OVERPASS_TIMEOUT_SECONDS + 15) as client:
        response = await client.post(
            overpass_url, data={"data": query}, headers={"User-Agent": USER_AGENT}
        )
        response.raise_for_status()
        payload = response.json()

    elements: list[OsmElement] = []
    for el in payload.get("elements", []):
        lat, lon = _extract_lat_lon(el)
        elements.append(
            OsmElement(
                osm_type=el["type"],
                osm_id=el["id"],
                lat=lat,
                lon=lon,
                version=el.get("version", 0),
                tags=el.get("tags", {}),
            )
        )
    return elements
