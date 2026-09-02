"""Rauchtests – prüfen nur, dass App + Datenzugriff grundsätzlich funktionieren."""

from fastapi.testclient import TestClient

from app import data
from app.main import app

client = TestClient(app)


def test_healthz():
    assert client.get("/healthz").json() == {"status": "ok"}


def test_index_renders():
    r = client.get("/")
    assert r.status_code == 200


def test_tips_latest_columns():
    df = data.tips_latest()
    assert {"Matchday", "HomeTeam", "AwayTeam", "tipp"} <= set(df.columns)


def test_points_rule():
    assert data.points((2, 1), (2, 1)) == 4
    assert data.points((2, 0), (3, 1)) == 3
    assert data.points((1, 0), (4, 2)) == 2
    assert data.points((1, 1), (3, 3)) == 2  # getipptes Remis, nicht exakt -> Tendenz
    assert data.points((0, 1), (2, 0)) == 0
