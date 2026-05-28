# Projektkontext — Bücherregal-Katalog

Dieses Projekt baut eine kleine App, die aus Fotos von Buchrücken ein strukturiertes Bücherverzeichnis erzeugt. Es ist der Live-Demo-Inhalt des Vorstandsvortrags „KI-Impact auf Digitalisierung" (TOP 5).

## Aufgabe

Aus Bildern in `./fotos/` (Fotos von Buchrücken aus einem Bücherregal) mit Hilfe der Anthropic Vision-API (Claude mit Bildverstehen) eine `buecher.csv` erzeugen. Jede Zeile ein Buch mit den Feldern **Dateiname, Titel, Autor, Verlag, Jahr, Sicherheit (high/medium/low)**.

## Technische Constraints

- **Zielplattform:** Windows 11 + WSL2 (Ubuntu). Kommandos in Bash, Pfade im Linux-Dateisystem (`~/...`), nicht unter `/mnt/c/...`.
- Python 3.11+.
- Anthropic Python SDK (`anthropic`) aktuell. Modell: `claude-sonnet-4-5` (oder das in der Umgebung verfügbare Vision-fähige Modell).
- API-Keys liegen in `.env` (Vorlage: `.env.example`). Vor jedem Lauf in die Shell laden: `set -a; source .env; set +a`.
  - `ANTHROPIC_API_KEY` (Pflicht)
  - `GOOGLE_BOOKS_API_KEY` (optional, hebt Quota für Verifikation)
- Streamlit für optionale UI-Ausbaustufe.
- Pillow für Bild-Vorverarbeitung (Größen-Skalierung).
- Rohdaten-Backup: pro Foto eine JSON-Datei in `./ergebnisse/`.

## Verbindliche Projektregeln

1. **Saubere Fehlerbehandlung:** fehlgeschlagene Einzelfotos werden gesammelt und am Ende aufgelistet. Kein harter Abbruch wegen eines einzelnen Bildes.
2. **Fortschrittsanzeige:** während der Verarbeitung sichtbar (Foto X von Y, Anzahl erkannter Bücher).
3. **Reproduzierbarkeit:** Rohantworten der API werden unter `./ergebnisse/<dateiname>.json` gespeichert, damit die Pipeline bei Schema-Änderungen ohne erneute API-Kosten neu laufen kann.
4. **Moderate Bilder:** Fotos über 5 MB oder mit mehr als 2048 px Seitenlänge werden vor API-Call verkleinert.
5. **Strukturierter Output:** Claude-Antwort per Tool-Use oder explizitem JSON-Schema, kein Freitext-Parsing.

## Datei-Layout (Soll)

```
demo_projekt/
├── fotos/                  # Eingabe — vom Autor befüllt
│   └── *.jpg / *.jpeg / *.png
├── ergebnisse/             # Roh-JSONs (automatisch erzeugt)
├── extract.py              # Vision-Aufruf, CSV-Erzeugung
├── app.py                  # Streamlit-UI (Ausbaustufe)
├── buecher.csv             # Ergebnis
├── requirements.txt
├── .env.example            # Vorlage für API-Keys (committet)
├── .env                    # echte Keys (NICHT committet — via .gitignore)
└── CLAUDE.md               # diese Datei
```

## Autor-Präferenzen

- Deutsch, strukturiert, lieber einmal zu viel nachfragen als Annahmen treffen.
- Python-Grundkenntnisse vorhanden, aber eingerostet — Lesbarkeit vor Eleganz.
- Fließtext-Ausgaben bevorzugt, keine überladenen Bullet-Listen in der Konsole.
