"""FastAPI-App – Einstiegspunkt.

Hier schreibst du deine Routen und Templates. Alles drumherum (Daten, Docker,
Traefik) ist fertig eingerichtet:

- ``app.data``     : liest die CSVs von bundesliga_data, siehe Funktionen dort
- ``templates/``   : Jinja2-Templates (base.html ist schon da)
- ``static/``      : CSS/JS, gemountet unter /static

Lokal starten:   uv run uvicorn app.main:app --reload
Im Container:    uvicorn app.main:app --host 0.0.0.0 --port 8000   (siehe Dockerfile)
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import data

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="Bundesliga-Tipps")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    # TODO: hier deine echte Seite bauen.
    # Beispiel-Daten, die du nutzen kannst:
    md = data.current_matchday()
    tips = data.tips_latest()
    tips = tips[tips["Matchday"] == md]
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "matchday": md,
            "tips": tips.to_dict("records"),
        },
    )
