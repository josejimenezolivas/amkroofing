"""The PDF renderer: headless Chromium, used by PDF export and nothing else.

It has no public route. The forms API checks that the user is signed in and
then reaches this service through a Vercel service binding, so signing in or
opening a document never waits for a browser to start.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response

from . import pdf
from .models import RenderJob


@asynccontextmanager
async def lifespan(app: FastAPI):
    await pdf.startup()
    try:
        yield
    finally:
        await pdf.shutdown()


app = FastAPI(title="AMK Roofing Forms PDF", version="0.1.0", lifespan=lifespan)


@app.post("/render")
async def render(job: RenderJob) -> Response:
    return Response(content=await pdf.render_pdf(job, base_url=job.base_url), media_type="application/pdf")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
