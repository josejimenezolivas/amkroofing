from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import pdf, storage
from .config import ALLOWED_ORIGINS
from .routers import documents, render, templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    storage.seed_reference_documents()
    await pdf.startup()
    try:
        yield
    finally:
        await pdf.shutdown()


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
app.include_router(templates.router, prefix="/forms")
app.include_router(documents.router, prefix="/forms")
app.include_router(render.router, prefix="/forms")


@app.get("/forms/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
