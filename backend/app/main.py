from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.routers import auth, fetch, upload

app = FastAPI(title="OSM Multilingual Name Editor")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    same_site="lax",  # must stay "lax" (not "strict") so the cookie survives OSM's redirect back to /api/auth/callback
    https_only=True,  # the app is only ever reached via the Caddy HTTPS proxy now
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fetch.router)
app.include_router(auth.router)
app.include_router(upload.router)


@app.get("/api/config")
async def get_config():
    return {"environment": settings.environment}
