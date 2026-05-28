# Fallback — vorab gebaute Version der Demo-App

Dieses Paket enthält eine komplette, funktionsfähige Version der Bücherregal-App. Zweck: im Demo-Termin als Plan B einsatzbereit, falls Claude Code live nicht durchkommt (API-Fehler, Internet-Probleme, Claude hängt sich auf).

**Plattform:** Windows 11 + WSL2 (Ubuntu). Alle Kommandos im WSL-Terminal, Bash.

## Dateien

- `extract.py` — Python-Skript, liest alle Fotos aus `./fotos/`, ruft Claude-Vision-API, schreibt `buecher.csv` und Rohdaten-JSON unter `./ergebnisse/`.
- `app.py` — Streamlit-UI, zeigt die CSV als sortierbare/filterbare Tabelle mit Foto-Vorschau.
- `requirements.txt` — minimale Abhängigkeiten.

## Setup (einmalig beim Trockenlauf)

Im Demo-Projektordner:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r fallback/requirements.txt

# .env aus Projekt-Vorlage anlegen und Keys eintragen
cp .env.example .env
nano .env

# Keys in die aktuelle Shell laden (pro neuer Shell wiederholen)
set -a; source .env; set +a
```

## Funktionstest

```bash
# Nur das erste Foto testen (Kostenrahmen: wenige Cent)
python fallback/extract.py --limit 1
```

Erfolg, wenn:

- Im Terminal erscheint eine Zeile `[ 1/1] <dateiname> ... X Buch/Bücher (Ns)`.
- `ergebnisse/<dateiname>.json` wurde angelegt und enthält gültiges JSON.
- `buecher.csv` wurde angelegt, mindestens eine Datenzeile.

Dann vollständiger Lauf:

```bash
python fallback/extract.py
```

Und UI:

```bash
streamlit run fallback/app.py
```

Browser öffnet `http://localhost:8501` mit der Tabelle. Unter WSL2 leitet Windows den Port automatisch weiter — du kannst die URL im Windows-Browser öffnen.

## Aktivierung im Live-Einsatz

Wenn während der Demo etwas zickt und du umschalten willst:

```bash
# Claude Code mit Ctrl+C beenden
# Im Demo-Projektordner:
cp -rf fallback/. .
set -a; source .env; set +a
python extract.py
streamlit run app.py
```

Kommentar Richtung Vorstand: „Für die Vorführung nutzen wir jetzt die vorab gebaute Version — selbe Logik, selber API-Call, nur ohne Live-Build."

## Was das Skript tut (damit du es im Vortrag erklären kannst)

1. **Bilder laden und skalieren**: Pillow öffnet das Foto, skaliert auf maximal 2048 Pixel Kantenlänge und speichert als JPEG mit 85% Qualität. Grund: Claude-Vision-API hat eine Obergrenze, größere Bilder werden abgelehnt.
2. **API-Call**: Bild als Base64 plus ein kurzer Textprompt an Claude. System-Prompt weist Claude an, ein striktes JSON zurückzugeben — ein Objekt `{"books": [{title, author, publisher, year, confidence}, ...]}`.
3. **Rohdaten sichern**: Die Antwort wandert als `ergebnisse/<dateiname>.json` auf Platte, bevor das Parsing läuft. Damit können wir später mit anderem Parser neu arbeiten, ohne API-Kosten.
4. **JSON parsen, CSV schreiben**: robuste Umklammerung auch für Claude-Antworten mit ```json-Umrandung.
5. **Fehler sammeln, nicht abbrechen**: ein kaputtes Foto stoppt den Gesamtlauf nicht.

## Bekannte Stolpersteine

| Symptom | Ursache | Lösung |
|---|---|---|
| `ANTHROPIC_API_KEY nicht gesetzt` | `.env` wurde in dieser Shell noch nicht geladen | `set -a; source .env; set +a` |
| `credit_balance_too_low` | API-Kontingent leer | Neues Guthaben laden auf console.anthropic.com |
| Antwort ist nicht parsbar | Claude hat mal keinen sauberen JSON geliefert | Im Skript `json_text`-Block prüfen; normalerweise hat die robuste Unrahmung das schon erledigt |
| Streamlit-Tabelle leer | `buecher.csv` existiert, aber ohne Datenzeilen | `extract.py` neu laufen lassen; Console-Ausgabe prüfen |
| Fotos werden nicht gefunden | Pfad falsch | `--fotos` setzen oder Ordner `./fotos/` im Projektordner anlegen |
| Streamlit-Browser öffnet nicht | WSL → Windows-Browser-Forwarding ist meist automatisch; sonst http://localhost:8501 manuell aufrufen | Im WSL `curl http://localhost:8501` zeigt, ob der Dienst läuft |
| Langsamer `pip install` oder Bild-Resize | Projekt liegt unter `/mnt/c/...` (Windows-Dateisystem) | Projekt nach `~/...` (Linux-Dateisystem) verschieben |
