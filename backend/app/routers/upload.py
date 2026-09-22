import httpx
from fastapi import APIRouter, HTTPException, Request

from app.config import settings
from app.models import UploadElementResult, UploadRequest, UploadResponse
from app.osm_api import close_changeset, create_changeset, update_element_tags

router = APIRouter()


@router.post("/api/upload", response_model=UploadResponse)
async def upload(req: UploadRequest, request: Request) -> UploadResponse:
    token = request.session.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Not logged in")

    base_url = settings.active.osm_base_url
    access_token = token["access_token"]

    changeset_id = await create_changeset(base_url, access_token, req.comment)

    results: list[UploadElementResult] = []
    for element in req.elements:
        try:
            new_version = await update_element_tags(
                base_url,
                access_token,
                element.osm_type,
                element.osm_id,
                changeset_id,
                element.tags,
            )
            results.append(
                UploadElementResult(
                    osm_type=element.osm_type,
                    osm_id=element.osm_id,
                    success=True,
                    new_version=new_version,
                )
            )
        except httpx.HTTPStatusError as exc:
            results.append(
                UploadElementResult(
                    osm_type=element.osm_type,
                    osm_id=element.osm_id,
                    success=False,
                    error=f"{exc.response.status_code}: {exc.response.text.strip()}",
                )
            )

    await close_changeset(base_url, access_token, changeset_id)

    return UploadResponse(changeset_id=changeset_id, results=results)
