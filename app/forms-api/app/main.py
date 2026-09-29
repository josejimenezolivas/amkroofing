import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import db, migrate
from .accounts import current_user
from .config import ALLOWED_ORIGINS
from .routers import auth, documents, render, templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Deploys migrate in the build step, so a cold start only opens a connection.
    if not os.environ.get("VERCEL"):
        migrate.run()
    try:
        yield
    finally:
        db.close()


app = FastAPI(title="AMK Roofing Forms", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mounted under /forms so the marketing site keeps /api/solar, /api/geocode
# and /api/tiles. The browser calls /forms/api/... on the same host.
# Everything but signing in and the health check needs a signed-in user.
signed_in = [Depends(current_user)]
app.include_router(auth.router, prefix="/forms")
app.include_router(templates.router, prefix="/forms", dependencies=signed_in)
app.include_router(documents.router, prefix="/forms", dependencies=signed_in)
app.include_router(render.router, prefix="/forms", dependencies=signed_in)


@app.get("/forms/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
