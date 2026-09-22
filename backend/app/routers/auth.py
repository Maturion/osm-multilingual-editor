from authlib.integrations.httpx_client import AsyncOAuth2Client
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.config import settings
from app.models import AuthStatus
from app.osm_api import get_user_details

router = APIRouter()

SCOPE = "read_prefs write_api"


def _make_client() -> AsyncOAuth2Client:
    env = settings.active
    return AsyncOAuth2Client(
        client_id=env.client_id,
        client_secret=env.client_secret,
        redirect_uri=settings.redirect_uri,
        scope=SCOPE,
    )


@router.get("/api/auth/login")
async def login(request: Request):
    env = settings.active
    client = _make_client()
    url, state = client.create_authorization_url(env.oauth_authorize_url)
    request.session["oauth_state"] = state
    return RedirectResponse(url)


@router.get("/api/auth/callback")
async def callback(request: Request):
    env = settings.active
    expected_state = request.session.get("oauth_state")
    if not expected_state or request.query_params.get("state") != expected_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    client = _make_client()
    token = await client.fetch_token(
        env.oauth_token_url,
        authorization_response=str(request.url),
    )
    username = await get_user_details(env.osm_base_url, token["access_token"])

    request.session["token"] = dict(token)
    request.session["username"] = username
    request.session.pop("oauth_state", None)

    return RedirectResponse(settings.frontend_url)


@router.get("/api/auth/status", response_model=AuthStatus)
async def status(request: Request) -> AuthStatus:
    token = request.session.get("token")
    return AuthStatus(
        logged_in=token is not None,
        username=request.session.get("username"),
        environment=settings.environment,
    )


@router.post("/api/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return {"ok": True}
