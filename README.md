# UV-Widget Riederalp & Schweiz

Scriptable-Widget für den UV-Index, gerechnet mit [icon-uv](https://github.com/ofuhrer/icon-uv)
aus MeteoSwiss ICON-CH2 (Wolken, Schnee, Druck) und CAMS (Ozon, Aerosol).
icon-uv ist Python und läuft nicht auf dem iPhone. Darum rechnet ein GitHub-Workflow
täglich die Prognose und legt zwei JSON-Dateien ab, die das Widget lädt.

```
GitHub Actions (täglich ~06–08 Uhr)          iPhone
ICON-CH2 00 UTC ─┐
CAMS Vortag 12 ──┼─ icon-uv ─ docs/daily-uv.json ──► Scriptable-Widget
locations.json ──┘           docs/hourly-uv.json
```

## Einrichten

1. **Repo anlegen** (öffentlich ist am einfachsten) und diese Dateien hochladen:
   `locations.json`, `build_widget_json.py`, `.github/workflows/uv-forecast.yml`.
2. **CAMS-Zugang:** Konto auf ads.atmosphere.copernicus.eu erstellen, die Lizenz des
   Datensatzes *CAMS global atmospheric composition forecasts* akzeptieren und den
   API-Key kopieren. Im Repo unter *Settings → Secrets and variables → Actions* ein
   Secret `ADS_API_KEY` mit dem Key anlegen. (ICON-Daten sind ohne Konto frei.)
3. **Erster Lauf:** *Actions → UV-Prognose → Run workflow*. Danach läuft es täglich
   automatisch (04:45 UTC, Ersatzlauf 06:45 UTC).
4. **Scriptable:** neues Skript, Inhalt von `UV-Riederalp.js` einfügen und
   `DATA_BASE_URL` setzen:
   `https://raw.githubusercontent.com/<DEIN-NAME>/<REPO>/main/docs`
   Ohne URL zeigt das Widget einen fixen Demo-Snapshot (Brig, 7.9.2026).
5. **Widget** auf den Homescreen oder Sperrbildschirm ziehen, Skript wählen.
   Parameter optional: eine Standort-ID, z. B. `moosfluh` oder `walliser_alpen_3000`.

## Anpassen

- **Standorte:** `locations.json` (Punkt = Koordinaten + Höhe; Höhenband = Box + 1000/2000/3000 m).
  Im Widget bestimmen `FEATURED`, `REGION` und `SWISS`, was wo erscheint.
- **Ensemble (21 Member, mit P10–P90):** Repo-Variable `UV_ENSEMBLE=true` oder beim
  manuellen Start ankreuzen. Dauert deutlich länger als der CTRL-Lauf.
- **Privates Repo:** einmal in Scriptable ausführen:
  `Keychain.set("uv-widget-github-token", "github_pat_…")` (Fine-grained Token, nur *Contents: read*).

## Was die Zahlen bedeuten

- Tageswert = höchstes 30-Minuten-Mittel des Tages, horizontale Fläche, ohne
  Geländeabschattung. Spitzenzeit auf 15 Minuten gerundet.
- Punktstandorte nehmen Wolken und Schnee der nächsten ICON-Zelle und rechnen auf die
  angegebene Höhe um. Höhenbänder sind das 90. Perzentil aller Zellen ±200 m um die
  Höhe in der Box.
- ❄︎ = experimentelle Schnee-Albedo ≥ 0.3 (aus ICON SNOWC): Reflexion erhöht die Belastung.
- `*` = eingeschränkte Datenbasis, `–` = keine Prognose.
- icon-uv ist ausdrücklich experimentell und keine offizielle MeteoSchweiz-Prognose.

Quellen: MeteoSwiss ICON OGD, Copernicus CAMS (ECMWF), icon-uv (BSD-3-Clause).
