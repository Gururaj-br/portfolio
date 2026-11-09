"""FastAPI service: renders the profile page and serves the profile as an API."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.retriever import Retriever

ROOT = Path(__file__).resolve().parent.parent
PROFILE_PATH = Path(os.getenv("PROFILE_PATH", ROOT / "data" / "profile.yaml"))


@lru_cache(maxsize=1)
def load_profile() -> dict:
    with PROFILE_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def get_retriever() -> Retriever:
    return Retriever(load_profile()["index"])


app = FastAPI(title="Gururaja BR — profile API", version="1.0.0", docs_url="/api/docs", redoc_url=None)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
templates = Jinja2Templates(directory=ROOT / "templates")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"p": load_profile()})


@app.get("/api/profile")
def profile():
    """The full profile, minus the retrieval index."""
    return {k: v for k, v in load_profile().items() if k != "index"}


@app.get("/api/profile/{section}")
def profile_section(section: str):
    data = load_profile()
    if section == "index" or section not in data:
        raise HTTPException(404, f"Unknown section '{section}'. Try: {', '.join(k for k in data if k != 'index')}")
    return data[section]


@app.get("/api/ask")
def ask(q: str = Query(..., min_length=1, max_length=200), k: int = Query(3, ge=1, le=8)):
    """Retrieve the top-k profile chunks for a question. Answers come only from the index."""
    return get_retriever().search(q, k)


@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"ok": True}
