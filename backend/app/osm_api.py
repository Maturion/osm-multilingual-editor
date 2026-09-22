from xml.etree import ElementTree as ET

import httpx

OSM_API_TIMEOUT_SECONDS = 30
USER_AGENT = "osm-multilingual-editor/0.1"


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT}


async def create_changeset(base_url: str, token: str, comment: str) -> int:
    osm = ET.Element("osm")
    changeset = ET.SubElement(osm, "changeset")
    ET.SubElement(changeset, "tag", k="created_by", v="Maturion OSM Multilingual Name Editor")
    ET.SubElement(changeset, "tag", k="comment", v=comment)
    body = ET.tostring(osm, encoding="unicode")

    async with httpx.AsyncClient(timeout=OSM_API_TIMEOUT_SECONDS) as client:
        response = await client.put(
            f"{base_url}/api/0.6/changeset/create",
            content=body,
            headers={**_auth_headers(token), "Content-Type": "text/xml"},
        )
        response.raise_for_status()
        return int(response.text.strip())


async def close_changeset(base_url: str, token: str, changeset_id: int) -> None:
    async with httpx.AsyncClient(timeout=OSM_API_TIMEOUT_SECONDS) as client:
        response = await client.put(
            f"{base_url}/api/0.6/changeset/{changeset_id}/close",
            headers=_auth_headers(token),
        )
        response.raise_for_status()


async def _get_element(base_url: str, token: str, osm_type: str, osm_id: int) -> ET.Element:
    async with httpx.AsyncClient(timeout=OSM_API_TIMEOUT_SECONDS) as client:
        response = await client.get(
            f"{base_url}/api/0.6/{osm_type}/{osm_id}",
            headers=_auth_headers(token),
        )
        response.raise_for_status()
        root = ET.fromstring(response.text)
        element = root.find(osm_type)
        if element is None:
            raise ValueError(f"Unexpected response fetching {osm_type}/{osm_id}")
        return element


def _apply_tags(element: ET.Element, changeset_id: int, new_tags: dict[str, str]) -> None:
    element.set("changeset", str(changeset_id))
    for tag in list(element.findall("tag")):
        element.remove(tag)
    for key, value in new_tags.items():
        value = value.strip()
        if value == "":
            continue
        ET.SubElement(element, "tag", k=key, v=value)


async def update_element_tags(
    base_url: str,
    token: str,
    osm_type: str,
    osm_id: int,
    changeset_id: int,
    new_tags: dict[str, str],
) -> int:
    element = await _get_element(base_url, token, osm_type, osm_id)
    _apply_tags(element, changeset_id, new_tags)

    osm = ET.Element("osm")
    osm.append(element)
    body = ET.tostring(osm, encoding="unicode")

    async with httpx.AsyncClient(timeout=OSM_API_TIMEOUT_SECONDS) as client:
        response = await client.put(
            f"{base_url}/api/0.6/{osm_type}/{osm_id}",
            content=body,
            headers={**_auth_headers(token), "Content-Type": "text/xml"},
        )
        response.raise_for_status()
        return int(response.text.strip())


async def get_user_details(base_url: str, token: str) -> str:
    async with httpx.AsyncClient(timeout=OSM_API_TIMEOUT_SECONDS) as client:
        response = await client.get(
            f"{base_url}/api/0.6/user/details.json",
            headers=_auth_headers(token),
        )
        response.raise_for_status()
        return response.json()["user"]["display_name"]
