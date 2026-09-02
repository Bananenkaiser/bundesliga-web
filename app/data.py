"""Zugriff auf die CSV-Daten der bundesliga_data-Pipeline.

Alle Funktionen lesen nur die CSVs unter ``DATA_DIR`` (read-only). Die Dateien
sind winzig; wir cachen sie anhand ihrer mtime, damit jeder Request frische
Daten sieht, sobald die Pipeline neu geschrieben hat.

Standardpfad:
- lokal:  ../bundesliga_data/data  (Schwester-Repo unter ~/Documents/projects)
- Docker: /data                    (per Bind-Mount, siehe docker-compose.yml)
Override über die Umgebungsvariable ``DATA_DIR``.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import pandas as pd

_DEFAULT_LOCAL = Path(__file__).resolve().parents[2] / "bundesliga_data" / "data"
DATA_DIR = Path(os.environ.get("DATA_DIR", _DEFAULT_LOCAL))


def _path(name: str) -> Path:
    return DATA_DIR / name


def _mtime(name: str) -> float:
    try:
        return _path(name).stat().st_mtime
    except FileNotFoundError:
        return 0.0


def _read_csv(name: str, _mtime_key: float) -> pd.DataFrame:
    # _mtime_key ist nur da, damit der lru_cache bei Datei-Änderung verfällt.
    return pd.read_csv(_path(name))


@lru_cache(maxsize=16)
def _cached(name: str, mtime: float) -> pd.DataFrame:
    return _read_csv(name, mtime)


def load(name: str) -> pd.DataFrame:
    """Eine CSV aus DATA_DIR laden (gecacht bis sich die Datei ändert)."""
    return _cached(name, _mtime(name)).copy()


# ---------------------------------------------------------------------------
# Bequeme Zugriffe auf die einzelnen Dateien
# ---------------------------------------------------------------------------

def tips_latest() -> pd.DataFrame:
    """Aktueller Tipp-Stand aller Spiele mit Quoten.

    Spalten: Matchday, HomeTeam, AwayTeam, tipp, p_H, p_U, p_A, xTore, E_Punkte
    """
    return load("tips_latest.csv")


def tips_log() -> pd.DataFrame:
    """Eingefrorener Tipp *vor Anpfiff* je Spiel (Basis für die Bilanz).

    Zusätzliche Spalten ggü. tips_latest: Date, logged_at, pre_kickoff
    """
    df = load("tips_log.csv")
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")
    return df


def season(year: str = "2627") -> pd.DataFrame:
    """Spielplan + Quoten + echte Ergebnisse einer Saison.

    FTHG/FTAG sind leer (NaN), solange ein Spiel nicht gespielt ist.
    """
    df = load(f"season_{year}.csv")
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")
    return df


def team_adjustments() -> pd.DataFrame:
    """Ausfall-/Sperren-Faktoren je Team und Spieltag (attack_factor, defense_leak)."""
    return load("team_adjustments.csv")


# ---------------------------------------------------------------------------
# Abgeleitete Sichten
# ---------------------------------------------------------------------------

MATCH_KEYS = ["Matchday", "HomeTeam", "AwayTeam"]


def current_matchday() -> int:
    """Größter Spieltag, für den es bereits Tipps gibt."""
    return int(tips_latest()["Matchday"].max())


def parse_score(s: str) -> tuple[int, int]:
    """'2:1' -> (2, 1)."""
    h, a = str(s).split(":")
    return int(h), int(a)


def points(pred: tuple[int, int], actual: tuple[int, int]) -> int:
    """Punkte der Tippspiel-Gruppe: 4 exakt / 3 Differenz (kein Remis) / 2 Tendenz / 0.

    Identisch zu bundesliga_data/src/bundesliga_data/scoring.py.
    """
    if pred == actual:
        return 4
    dp = pred[0] - pred[1]
    if dp != 0 and dp == actual[0] - actual[1]:
        return 3
    sign = lambda h, a: (h > a) - (h < a)  # noqa: E731
    if sign(*pred) == sign(*actual):
        return 2
    return 0


def results_with_points(year: str = "2627") -> pd.DataFrame:
    """tips_log ⋈ echte Ergebnisse, nur gespielte Spiele, inkl. Punkte-Spalte.

    Zusätzliche Spalten: FTHG, FTAG, ftr ('H'/'D'/'A'), result ('3:1'), pts (0/2/3/4)
    """
    log = tips_log()
    res = season(year)[MATCH_KEYS + ["FTHG", "FTAG"]]
    df = log.merge(res, on=MATCH_KEYS, how="left")
    df = df.dropna(subset=["FTHG", "FTAG"]).copy()
    if df.empty:
        return df.assign(pts=pd.Series(dtype=int), result="", ftr="")
    df[["FTHG", "FTAG"]] = df[["FTHG", "FTAG"]].astype(int)

    def _row_points(r: pd.Series) -> int:
        return points(parse_score(r["tipp"]), (r["FTHG"], r["FTAG"]))

    df["pts"] = df.apply(_row_points, axis=1)
    df["result"] = df["FTHG"].astype(str) + ":" + df["FTAG"].astype(str)
    df["ftr"] = df.apply(
        lambda r: "H" if r["FTHG"] > r["FTAG"] else ("A" if r["FTHG"] < r["FTAG"] else "D"),
        axis=1,
    )
    return df


def standings(year: str = "2627") -> pd.DataFrame:
    """Punkte-Bilanz je Spieltag: Summe, Schnitt, Anzahl exakter Treffer."""
    df = results_with_points(year)
    if df.empty:
        return pd.DataFrame(columns=["Matchday", "games", "points", "avg", "exact"])
    g = df.groupby("Matchday")
    out = g.agg(
        games=("pts", "size"),
        points=("pts", "sum"),
        avg=("pts", "mean"),
        exact=("pts", lambda s: int((s == 4).sum())),
    ).reset_index()
    out["avg"] = out["avg"].round(2)
    return out
