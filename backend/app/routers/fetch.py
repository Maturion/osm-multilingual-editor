import httpx
from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import FetchRequest, FetchResponse
from app.overpass import fetch_elements

router = APIRouter()


@router.post("/api/fetch", response_model=FetchResponse)
async def fetch(req: FetchRequest) -> FetchResponse:
    try:
        elements = await fetch_elements(
            settings.overpass_url, req.admin_id, req.object_types, settings.poi_tags
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502, detail=f"Overpass request failed: {exc.response.status_code}"
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return FetchResponse(elements=elements)
