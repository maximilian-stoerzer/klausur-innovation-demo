# Demo-Vorbereitung — Bücherregal zum Katalog

Paket für die Live-Demo im Vorstandsvortrag (TOP 5, Block 2, 20 Minuten).

## Ziel der Demo

Vor laufendem Vorstand eine kleine App bauen, die aus mitgebrachten Fotos der Buchrücken ein strukturiertes Bücherverzeichnis erstellt. Die App soll nach etwa zehn Minuten Generierung lauffähig sein und ein Ergebnis liefern; die restliche Zeit dient der Ausbaustufe (Streamlit-UI) und der Reflexion.

## Technische Eckdaten

- **Programmiersprache:** Python 3.11 oder neuer.
- **Vision-API:** Anthropic Claude (Modell `claude-sonnet-4-5` oder `claude-opus-4-6`, fähig zu Bildverstehen).
- **UI-Framework:** Streamlit (Ausbaustufe).
- **Eingabe:** Fotos von Buchrücken, abgelegt im Unterordner `fotos/` des Demo-Projekts.
- **Ausgabe:** CSV-Datei `buecher.csv` plus optional Streamlit-UI mit Tabelle.

## Paketinhalt

- `README.md` — dieses Dokument.
- `claude_prompt.md` — der Prompt, den du im Demo-Termin in Claude Code pastest.
- `CLAUDE.md` — Projektkontext für Claude Code. Wird später in den eigentlichen Demo-Projektordner kopiert.
- `rehearsal_checklist.md` — Minute-für-Minute-Anleitung für Trockenläufe und den Live-Einsatz.
- `fotos/` — hier legst du vorab deine Bücherregal-Fotos ab.
- `fallback/` — eine funktionsfähige, vorab gebaute Version der App als Plan B (falls im Demo-Termin etwas nicht funktioniert).

## Einmal-Setup vor dem ersten Trockenlauf

1. Python und venv sind durch die Bild-Generierung bereits vorhanden. Neu:
   ```powershell
   cd "G:\OneDrive\Dokumente\2026\Buchprojekte\TODOs\05-narrativ-vorstand\demo_vorbereitung"
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install anthropic streamlit pillow
   ```
2. **Anthropic-API-Key** als Umgebungsvariable setzen:
   ```powershell
   $env:ANTHROPIC_API_KEY = "sk-ant-..."
   ```
   (Persistierung optional über Systemumgebungsvariablen.)
3. **Claude Code** installieren, falls noch nicht vorhanden — siehe [offizielle Anleitung](https://docs.claude.com/claude-code). Kurz: `npm install -g @anthropic-ai/claude-code` (benötigt Node.js).
4. **Fotos** in `fotos/` ablegen. Empfehlung: 15 bis 25 Fotos, unterschiedliche Buchrücken, mischung aus guter und durchschnittlicher Qualität, damit die Robustheit zur Sprache kommt. Dateinamen belanglos.

## Der Demo-Ablauf in Kürze

1. Beamer an, Terminal voll sichtbar, Claude Code gestartet.
2. Prompt aus `claude_prompt.md` einfügen.
3. Claude plant, implementiert, führt aus — Kommentar dazu parallel.
4. Fotoerfassung läuft, CSV entsteht.
5. Ausbaustufe: Streamlit-UI.
6. Reflexion: Was wäre das klassisch gewesen?

Details in `rehearsal_checklist.md`.

## Plan B

Wenn API-Key streikt, Internet wackelt oder Claude Code aus irgendeinem Grund nicht durchkommt: siehe `fallback/README.md`. Kurz: `cp fallback/*.py .` und `streamlit run app.py`. Die Demo läuft dann mit vorbereitetem Code — du kommentierst trotzdem live, nur dass du nicht parallel beim Bauen zugucken lässt.
