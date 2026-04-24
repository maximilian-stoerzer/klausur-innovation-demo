# Rehearsal-Checkliste — Live-Demo Bücherregal

Zweck: mindestens zwei Trockenläufe unter realistischen Bedingungen (Präsentations-Notebook, Beamer-Anschluss, Internet wie im Vortragsraum). Ziel: das erste lauffähige Ergebnis nach zehn Minuten, die Ausbaustufe nach weiteren fünf Minuten, vier bis fünf Minuten Puffer für Kommentar und Reflexion.

## Pre-Flight (vor jedem Trockenlauf und vor dem Live-Termin)

- [ ] Präsentations-Notebook am Platz (auch beim Trockenlauf, nicht am Schreibtisch).
- [ ] Beamer-Kabel angesteckt, Zweitmonitor-Erweiterung aktiv, Terminal auf der Beamer-Seite lesbar (Schriftgröße mindestens 16pt).
- [ ] Internet stabil. Speed-Test ≥ 20 Mbit down. Mobile Hotspot als Backup.
- [ ] Stromversorgung gesichert, Bildschirm-Sleep auf mindestens 30 Minuten.
- [ ] Bildschirm-Notifications stumm (Teams, Outlook, Slack, Browser-Benachrichtigungen — alles aus).
- [ ] Demo-Projektordner frisch angelegt (nicht der Vorbereitungsordner selbst):
  ```powershell
  $demo = "C:\Temp\vorstand_demo"
  Remove-Item $demo -Recurse -Force -ErrorAction SilentlyContinue
  New-Item -ItemType Directory -Path $demo | Out-Null
  Copy-Item .\CLAUDE.md $demo
  Copy-Item .\fotos $demo -Recurse
  cd $demo
  ```
- [ ] `ANTHROPIC_API_KEY` in der Shell gesetzt und getestet:
  ```powershell
  $env:ANTHROPIC_API_KEY
  # zeigt sk-ant-... — falls leer, neu setzen
  ```
- [ ] Claude Code installiert und aktuell:
  ```powershell
  claude --version
  claude update   # falls verfügbar
  ```
- [ ] Python-Venv im Demo-Ordner anlegen (Claude Code nutzt ggf. das System-Python, aber Streamlit braucht ein venv):
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install anthropic pillow streamlit
  ```
- [ ] Fallback-Code einmal vorab testen (siehe `fallback/README.md`). Wenn der läuft, ist Plan B bestätigt funktionsfähig.
- [ ] Stoppuhr auf dem Smartphone griffbereit (nicht auf dem Notebook — das lenkt ab).

## Demo-Ablauf — Soll-Zeitraster

| Ab Min | Inhalt | Was du tust | Was der Vorstand sieht |
|---|---|---|---|
| 0:00 | Challenge-Folie zeigen | „Eingabe 20 Fotos, Ziel Bestandsliste, Zeit 10 Minuten" | Folie 5 der PPTX |
| 0:30 | Terminal-Fenster | Vom Folienmodus auf Terminal wechseln, `claude` starten | Leerer Claude-Prompt, Ordnerinhalt `fotos/` sichtbar |
| 0:45 | Prompt einfügen | Aus `claude_prompt.md` den Block kopieren, in Claude Code pasten, Enter | Prompt erscheint, Claude beginnt zu antworten |
| 1:30 | Plan-Phase | Claude fragt ggf. zurück — kurz bestätigen. Du kommentierst: „Claude denkt gerade über Architektur nach." | Claude listet geplante Schritte |
| 3:30 | Bau-Phase | Claude schreibt `extract.py`, installiert Dependencies. Du kommentierst den entstehenden Code kurz: „Das hier ist der Vision-API-Call." | Dateien entstehen, Code erscheint auf dem Screen |
| 8:30 | Erster Test (1 Foto) | Claude führt die Probe aus, zeigt Rohantwort. Du: „Das ist das Ergebnis für ein einzelnes Bild." | JSON-Antwort im Terminal |
| 10:00 | Vollausführung startet | Claude iteriert über alle Fotos. Du erzählst parallel: „Was vorher Wochen-Projekt, läuft jetzt in Minuten." | Fortschrittsanzeige, erste CSV-Zeilen |
| 13:00 | CSV fertig, Ausbau-Phase | Claude starten: „Jetzt bitte noch die Streamlit-UI wie in CLAUDE.md skizziert." | Neues Skript `app.py` entsteht |
| 16:00 | UI starten | `streamlit run app.py`, Browser öffnet | Tabelle mit Büchern, Filter, Miniaturen |
| 17:00 | Reflexion | „Was haben wir gerade gesehen?" — klassisch hätte das ein Projekt mit vier Wochen und fünfstelligem Budget gekostet | Zurück zur Präsentation |
| 20:00 | Übergang | Folie „3. Der Long Tail" | Nächstes Kapitel |

## Rote-Flagge-Szenarien und Reaktion

- **Claude hängt in der Plan-Phase länger als 90 Sekunden:** sanft nachhaken — „Mach weiter mit Schritt 2 und fang an zu implementieren."
- **API-Fehler beim ersten Vision-Call:** in Claude Code fragen — „Der Fehler ist XYZ, lies die Fehlermeldung, pass das Bild-Handling an." Falls zum zweiten Mal Fehler: Plan B aktivieren (siehe unten).
- **Einzelnes Foto wird nicht erkannt:** ignorieren, lauter erzählen. Kommentar: „KI kann dort an die Grenzen kommen, wo auch ein Mensch den Titel nicht mehr entziffert."
- **Streamlit-UI läuft nicht:** Ausbaustufe weglassen, direkt zur Reflexion. CSV-Datei in einem Editor öffnen und zeigen.
- **Internet bricht weg:** Plan B aktivieren (Fallback-Code copy-pasten, Demo zu Ende führen).

## Plan B aktivieren

Wenn Claude Code für mehr als 90 Sekunden nichts produziert oder zwei API-Fehler hintereinander kommen:

```powershell
# Im Demo-Ordner, Claude-Code schließen
cd $demo
Copy-Item -Recurse -Force "G:\OneDrive\Dokumente\2026\Buchprojekte\TODOs\05-narrativ-vorstand\demo_vorbereitung\fallback\*" .
python extract.py
streamlit run app.py
```

Kommentar bei der Umschaltung: „Wir nutzen für die Vorführung jetzt die vorab gebaute Version — dieselbe Logik, dieselbe API, nur ohne Live-Build. Das Ergebnis ist identisch."

## Nach-Trockenlauf-Review

Nach jedem Trockenlauf drei Fragen beantworten:

1. War der Zehn-Minuten-Punkt erreichbar? Wenn nicht: wo war die Verzögerung?
2. Ist der Prompt an einer Stelle unklar? Was musste Claude rückfragen?
3. War die Reflexions-Phase (16:00 bis 20:00) entspannt oder gehetzt?

Erkenntnisse in `rehearsal_log.md` festhalten (Datei bei Bedarf anlegen).

## Kostenrahmen

Jeder kompletter Trockenlauf kostet:

- 15 bis 25 Fotos × Claude Vision Call ≈ 0,02 bis 0,05 USD pro Bild = etwa 0,30 bis 1,25 USD pro Durchlauf.
- Claude-Code-Orchestrierung: wenige Cent pro Durchlauf.
- **Gesamt:** unter 2 USD pro kompletten Trockenlauf. Drei bis vier Läufe sind Standard vor einem Vorstandstermin.
