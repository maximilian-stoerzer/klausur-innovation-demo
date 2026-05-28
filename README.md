# Demo-Vorbereitung — Bücherregal zum Katalog

Paket für die Live-Demo im Vorstandsvortrag (TOP 5, Block 2, 20 Minuten).

**Zielplattform:** Windows mit WSL2 (Ubuntu). Alle Kommandos sind Bash, ausgeführt im WSL-Terminal. Pfade liegen im Linux-Dateisystem (`~/Projekte/...`), nicht unter `/mnt/c/...` — letzteres ist auf I/O-lastigen Schritten (`pip install`, Bild-Resize) deutlich langsamer.

## Ziel der Demo

Vor laufendem Vorstand eine kleine App bauen, die aus mitgebrachten Fotos der Buchrücken ein strukturiertes Bücherverzeichnis erstellt. Die App soll nach etwa zehn Minuten Generierung lauffähig sein und ein Ergebnis liefern; die restliche Zeit dient der Ausbaustufe (Streamlit-UI) und der Reflexion.

## Technische Eckdaten

- **OS:** Windows 11 + WSL2 mit Ubuntu (getestet 22.04 / 24.04).
- **Programmiersprache:** Python 3.11 oder neuer.
- **Vision-API:** Anthropic Claude (Modell `claude-sonnet-4-5` oder `claude-opus-4-7`, fähig zu Bildverstehen).
- **UI-Framework:** Streamlit (Ausbaustufe).
- **Eingabe:** Fotos von Buchrücken, abgelegt im Unterordner `fotos/` des Demo-Projekts.
- **Ausgabe:** CSV-Datei `buecher.csv` plus optional Streamlit-UI mit Tabelle.

## Paketinhalt

- `README.md` — dieses Dokument.
- `claude_prompt.md` — der Prompt, den du im Demo-Termin in Claude Code pastest.
- `CLAUDE.md` — Projektkontext für Claude Code. Wird später in den eigentlichen Demo-Projektordner kopiert.
- `rehearsal_checklist.md` — Minute-für-Minute-Anleitung für Trockenläufe und den Live-Einsatz.
- `ABLAUF.md` — Single-Page-Cheatsheet für den Termin (Pre-Flight, Prompt, Zeitraster, Plan B).
- `.env.example` — Vorlage für API-Keys. Wird zu `.env` kopiert und mit echten Keys befüllt.
- `fotos/` — hier legst du vorab deine Bücherregal-Fotos ab.
- `fallback/` — eine funktionsfähige, vorab gebaute Version der App als Plan B (falls im Demo-Termin etwas nicht funktioniert).

## Einmal-Setup vor dem ersten Trockenlauf

Im WSL-Terminal (Ubuntu), im Projektordner:

```bash
cd ~/Projekte/klausur-innovation-demo

# 1. Python-Toolchain prüfen (Ubuntu 22.04+ bringt Python 3.10+ mit;
#    für 3.11+ ggf. python3.11 + python3.11-venv via apt nachziehen)
python3 --version
sudo apt update && sudo apt install -y python3-venv python3-pip

# 2. Virtuelle Umgebung anlegen und Abhängigkeiten installieren
python3 -m venv .venv
source .venv/bin/activate
pip install -r fallback/requirements.txt

# 3. API-Keys einrichten
cp .env.example .env
# .env in einem Editor öffnen und sk-ant-... eintragen (sowie Google-Books-Key, falls vorhanden)
nano .env

# 4. Keys in die aktuelle Shell laden (pro neuer Shell wiederholen)
set -a; source .env; set +a

# 5. Sanity-Check: Keys gesetzt, Imports funktionieren
echo "Anthropic: ${ANTHROPIC_API_KEY:0:10}..."
echo "Google Books: ${GOOGLE_BOOKS_API_KEY:0:10}..."
python -c "import anthropic, PIL, streamlit; print('OK')"
```

**Claude Code in WSL** installieren, falls noch nicht vorhanden — Node.js LTS via `nvm` ist der saubere Weg:

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
# Shell neu laden (oder neue WSL-Session öffnen)
nvm install --lts
npm install -g @anthropic-ai/claude-code
claude --version
```

**Fotos** in `fotos/` ablegen. Empfehlung: 15 bis 25 Fotos, unterschiedliche Buchrücken, Mischung aus guter und durchschnittlicher Qualität, damit die Robustheit zur Sprache kommt. Dateinamen belanglos.

## API-Keys: `.env`-Konvention

- `.env.example` ist die committete Vorlage mit Platzhaltern.
- `.env` enthält die echten Keys und ist via `.gitignore` aus dem Repo ausgenommen — niemals committen.
- Die Skripte laden `.env` **nicht** automatisch. In jeder neuen Shell-Session vor dem ersten Aufruf:
  ```bash
  set -a; source .env; set +a
  ```
  Damit werden alle `KEY=VALUE`-Zeilen aus `.env` in die Umgebung exportiert.
- Alternative für persistente User-Variablen (Eintrag in `~/.bashrc`):
  ```bash
  echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.bashrc
  echo 'export GOOGLE_BOOKS_API_KEY="..."' >> ~/.bashrc
  source ~/.bashrc
  ```
  Nur empfehlenswert auf dem eigenen Rechner, nicht auf geteilten Maschinen.

## Der Demo-Ablauf in Kürze

1. WSL-Terminal voll sichtbar, Claude Code gestartet.
2. Prompt aus `claude_prompt.md` einfügen.
3. Claude plant, implementiert, führt aus — Kommentar dazu parallel.
4. Fotoerfassung läuft, CSV entsteht.
5. Ausbaustufe: Streamlit-UI.
6. Reflexion: Was wäre das klassisch gewesen?

Details in `rehearsal_checklist.md` und vor allem in `ABLAUF.md`.

## Plan B

Wenn API-Key streikt, Internet wackelt oder Claude Code aus irgendeinem Grund nicht durchkommt: siehe `fallback/README.md`. Kurz: `cp fallback/*.py .` und `streamlit run app.py`. Die Demo läuft dann mit vorbereitetem Code — du kommentierst trotzdem live, nur dass du nicht parallel beim Bauen zugucken lässt.
