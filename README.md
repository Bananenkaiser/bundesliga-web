# bundesliga-web

Web-Frontend für die Bundesliga-Tipps. Liest **nur** die CSVs, die die
`bundesliga_data`-Pipeline schreibt – keine eigene Datenhaltung, kein API-Call.

## Was schon eingerichtet ist

| Teil | Datei | Status |
|---|---|---|
| Daten-Zugriff | `app/data.py` | fertig – Funktionen s. u. |
| App-Einstieg | `app/main.py` | Skelett mit `/`, `/healthz` – **hier baust du** |
| Templates | `templates/base.html`, `index.html` | Platzhalter |
| Styles | `static/style.css` | minimal |
| Container | `Dockerfile` (uv, multi-arch) | fertig |
| Deployment | `docker-compose.yml` (Traefik-Labels, `tippspiel.lan`) | fertig |

## Lokal entwickeln

```bash
uv sync
uv run uvicorn app.main:app --reload
# http://127.0.0.1:8000
```

`app/data.py` findet die CSVs automatisch unter `../bundesliga_data/data`
(Schwester-Repo). Anderer Pfad: `export DATA_DIR=/pfad/zu/data`.

## Daten – `app/data.py`

| Funktion | liefert |
|---|---|
| `tips_latest()` | aktueller Tipp-Stand aller Spiele (DataFrame) |
| `tips_log()` | eingefrorene Tipps vor Anpfiff (mit `Date`) |
| `season("2627")` | Spielplan + Quoten + echte Ergebnisse (`FTHG`/`FTAG` NaN = ungespielt) |
| `team_adjustments()` | Ausfall-/Sperren-Faktoren je Team & Spieltag |
| `current_matchday()` | größter Spieltag mit Tipps (int) |
| `results_with_points("2627")` | gespielte Spiele + Punkte-Spalte `pts` + `result`, `ftr` |
| `standings("2627")` | Punkte-Bilanz je Spieltag (`points`, `avg`, `exact`) |
| `points(pred, actual)` | Punkteregel 4/3/2/0, `pred`/`actual` = `(h, a)` |
| `parse_score("2:1")` | `(2, 1)` |
| `load("name.csv")` | beliebige CSV aus `DATA_DIR`, gecacht bis mtime sich ändert |

Spalten `tips_latest` / `tips_log`: `Matchday, HomeTeam, AwayTeam, tipp,
p_H, p_U, p_A, xTore, E_Punkte` (+ `Date, logged_at, pre_kickoff` im Log).

## Workflow

Entwickelt wird **hier auf dem Rechner**, der Pi zieht den Stand aus GitHub.

```bash
# lokal
git add -A && git commit -m "..." && git push

# auf dem Pi (einmalig geklont nach ~/apps/bundesliga-web)
~/apps/bundesliga-web/deploy/update.sh      # git pull + docker compose up -d --build
```

### Pi-Setup (einmalig)

```bash
mkdir -p ~/apps && cd ~/apps
git clone https://github.com/Bananenkaiser/bundesliga_data.git
git clone https://github.com/Bananenkaiser/bundesliga-web.git
# -> ~/apps/bundesliga_data  und  ~/apps/bundesliga-web  liegen nebeneinander,
#    dann findet docker-compose.yml die Daten unter ../bundesliga_data/data automatisch.
docker network create traefik-net    # falls noch nicht vorhanden
cd ~/apps/bundesliga-web && docker compose up -d --build
```

Traefik + Pi-hole-Eintrag für `tippspiel.lan` siehe Repo `homelab`.
