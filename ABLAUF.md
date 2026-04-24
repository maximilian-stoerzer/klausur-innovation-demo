# ABLAUF.md — Live-Demo Bücherregal (Einzeldatei für den Termin)

> **Zweck dieser Datei:** Alles, was du im Vorstandstermin brauchst, auf einer Seite. Nicht zwischen Dateien springen. Pre-Flight, Prompt, Zeitraster, Kommentare, rote Flaggen, Plan B — in dieser Reihenfolge.
>
> **Setup-Zeit am Termin:** 5 Minuten vor Slot-Beginn. **Durchführung:** 20 Minuten. **Puffer:** 4–5 Minuten Reflexion.

---

## 1. Pre-Flight-Checkliste (die fünf Zeilen, die zählen)

- [ ] Beamer klebt, Zweitmonitor erweitert, Terminal-Schrift ≥ 16pt.
- [ ] Internet ≥ 20 Mbit down, Handy-Hotspot als Backup bereit.
- [ ] `$env:ANTHROPIC_API_KEY` zeigt `sk-ant-…`, `claude --version` funktioniert.
- [ ] Frischer Demo-Ordner `C:\Temp\vorstand_demo` mit `CLAUDE.md` + `fotos/` kopiert, `cd` dorthin.
- [ ] Teams/Outlook/Slack/Browser-Notifications alle stumm, Bildschirm-Sleep ≥ 30 min.

```powershell
# Setup-Einzeiler für den Demo-Ordner
$demo = "C:\Temp\vorstand_demo"
Remove-Item $demo -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $demo | Out-Null
Copy-Item .\CLAUDE.md $demo
Copy-Item .\fotos $demo -Recurse
cd $demo
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install anthropic pillow streamlit
```

---

## 2. Claude-Prompt — Copy-Paste-Block für den Live-Termin

Terminal öffnen, `claude` starten, den Block **zwischen den Trennstrichen** pasten, Enter.

---

```
Ziel: Ich möchte aus den Bildern in ./fotos/ ein strukturiertes Bücherverzeichnis erstellen. Jedes Bild zeigt Buchrücken aus meinem Bücherregal. Am Ende soll eine CSV-Datei buecher.csv im Projektordner liegen mit den Spalten Dateiname, Titel, Autor, Verlag, Jahr (falls erkennbar), Sicherheit (high/medium/low).

Vorgehen:

1. Analysiere zuerst den Ordner ./fotos/. Zeig mir, welche Bilddateien du siehst und welches Format. Stelle eine kurze Rückfrage, falls etwas unklar ist.

2. Plane dann die Implementierung:
   - Nutze die Anthropic-Python-Library (`anthropic`, neueste Version) und das Vision-fähige Modell `claude-sonnet-4-5`.
   - Ein Python-Skript `extract.py` mit folgender Struktur: Funktion `analyse_foto(pfad)`, die das Bild als base64 an Claude sendet und strukturiertes JSON zurückbekommt (per `tool_use` oder strukturierter Output). Funktion `main()`, die über alle Fotos iteriert, Fortschritt auf der Konsole zeigt und am Ende `buecher.csv` schreibt.
   - Pro Foto kann es mehrere Bücher geben. Die CSV-Zeile enthält ein Buch pro Zeile, mit dem Dateinamen als Gruppierung.
   - Rohdaten-Backup: Pro Foto auch ein JSON unter ./ergebnisse/<dateiname>.json ablegen — wenn wir später das Parsing verbessern, müssen wir nicht neu analysieren.

3. Implementiere das Skript und führe es mit einem einzigen Foto probeweise aus, bevor du alle anfasst. Zeig mir die Rohantwort von Claude für dieses eine Bild, damit wir sehen, dass die Struktur stimmt.

4. Wenn das erste Foto sauber verarbeitet ist: starte die volle Verarbeitung aller Fotos in ./fotos/. Während das läuft, zeigst du Fortschritt im Terminal (Foto X von Y, erkannte Bücher).

5. Am Ende: Zusammenfassung anzeigen — wie viele Fotos, wie viele Bücher erkannt, Verteilung der Sicherheitsstufen.

Technische Hinweise:
- API-Key liest du aus der Umgebungsvariable ANTHROPIC_API_KEY.
- Bildgröße: falls ein Foto größer als 5 MB ist, vorher mit Pillow auf max. 2048px lange Seite herunterskalieren (JPEG-Qualität 85), sonst API-Fehler.
- Error Handling: bei einzelnen fehlgeschlagenen Fotos weiter machen, Fehler sammeln, am Ende auflisten. Kein harter Abbruch wegen eines einzelnen Bilds.

Nicht jetzt nötig, aber als nächster Schritt danach: ein kleines Streamlit-UI (app.py), das die CSV lädt und in einer sortierbaren Tabelle zeigt, mit Filter nach Autor/Sicherheit und Miniaturbild des Ursprungsfotos. Das kommt aber erst, wenn die Extraktion steht.

Los.
```

---

## 3. Minute-für-Minute — Soll-Zeitraster

| Ab Min | Inhalt | Was du tust | Was der Vorstand sieht |
|---|---|---|---|
| 0:00 | Challenge-Folie | „Eingabe 20 Fotos, Ziel Bestandsliste, Zeit 10 Minuten." | Folie 5 der PPTX |
| 0:30 | Terminal-Wechsel | Vom Folienmodus auf Terminal, `claude` starten | Leerer Claude-Prompt, `fotos/` sichtbar |
| 0:45 | Prompt einfügen | Block aus Abschnitt 2 pasten, Enter | Prompt erscheint, Claude antwortet |
| 1:30 | Plan-Phase | Ggf. Rückfragen bestätigen | Claude listet geplante Schritte |
| 3:30 | Bau-Phase | Claude schreibt `extract.py`, installiert Dependencies | Dateien entstehen, Code läuft über den Screen |
| 8:30 | Erster Test (1 Foto) | Claude führt Probe aus | JSON-Antwort im Terminal |
| 10:00 | Vollausführung startet | Claude iteriert über alle Fotos | Fortschrittsanzeige, erste CSV-Zeilen |
| 13:00 | CSV fertig, Ausbau | „Jetzt bitte noch die Streamlit-UI wie in `CLAUDE.md` skizziert." | `app.py` entsteht |
| 16:00 | UI starten | `streamlit run app.py` | Tabelle mit Büchern, Filter, Miniaturen |
| 17:00 | Reflexion | Einordnung: „Klassisch vier Wochen, fünfstelliges Budget." | Zurück zur Präsentation |
| 20:00 | Übergang | Folie „3. Der Long Tail" | Nächstes Kapitel |

**Kritischer Checkpoint:** Bei Minute 8:30 **muss** der Probelauf mit einem Foto JSON-Output zeigen. Wenn nicht → Plan B (Abschnitt 6).

---

## 4. Kommentar-Vorlagen — was du sagst, während Claude arbeitet

### Während Claude **plant** (Min 1:30–3:30, Plan-Phase)

> „Sie sehen hier gerade das, was wir klassischerweise einem Entwickler in einem ersten Workshop mitgeben würden — Ziel, Vorgehen, Abnahmekriterien. Der Unterschied ist: Claude liest das nicht und geht dann für zwei Tage weg, sondern beginnt sofort zu strukturieren."

> „Im Hintergrund läuft gerade das, was wir in unserer Methodik als *Architektur-Phase* bezeichnen. Claude entscheidet: welche Bibliothek, welcher API-Call, welche Fehlerbehandlung. Das ist keine Magie, das ist sauberes Engineering — nur eben in Sekunden statt in Meetings."

### Während Claude **baut** (Min 3:30–8:30, Bau-Phase)

> „Das hier ist der eigentliche Vision-API-Call — Bild rein, JSON raus. Dieselbe Technik, die ich im Buch auf 45.000 Zeilen Code angewendet habe."

> „Beachten Sie, dass Claude parallel auch das Error-Handling einbaut — was passiert bei einem kaputten Bild, bei einem API-Timeout. Das sind genau die Punkte, bei denen klassische Prototypen scheitern, weil sie nur den Happy Path abdecken."

> „Die Rohdaten werden zusätzlich als JSON gespeichert. Warum? Weil wir beim zweiten Durchlauf die API nicht nochmal bemühen müssen. Das ist Kosten-Disziplin — jede Architekturentscheidung hat eine Rechnung dahinter."

### Während der **erste Test läuft** (Min 8:30)

> „Hier haben wir jetzt den entscheidenden Moment: ein einzelnes Foto, ein einzelnes Ergebnis. Wenn die Struktur hier stimmt, läuft der Rest in Serie. Wenn nicht, korrigieren wir den Prompt, nicht den Code."

### Während die **Vollausführung läuft** (Min 10:00–13:00)

> „Das, was Sie gerade sehen, hätte klassisch so ausgesehen: Ausschreibung, Angebote, Projektstart in sechs Wochen, Ergebnis in vier Monaten, Budget mittlere fünfstellige Summe. Wir sind bei unter 20 Minuten und unter zwei Dollar Cloud-Kosten."

> „Wichtig für Sie als Entscheider: Das ist kein Spielzeug. Dieselbe Methode, dieselben Werkzeuge, mit denen in meinem Selbstversuch 45.000 Zeilen produktiver Code entstanden sind."

### Während **Streamlit baut und startet** (Min 13:00–16:00)

> „Die UI ist die Kür, nicht die Pflicht. Der Wert steckt in der CSV — aber für den Fachbereich ist eine klickbare Oberfläche oft der Unterschied zwischen 'interessant' und 'nutze ich jeden Tag'."

### In der **Reflexion** (Min 17:00–20:00)

> „Lassen Sie uns das kurz einordnen: Wir haben gerade, live, vor Ihren Augen, eine Anwendung gebaut, die — klassisch ausgeschrieben — ein vier-Wochen-Projekt gewesen wäre. Die Eingabe-Qualität war mittelmäßig, wir hatten keine Generalprobe auf genau dieser Beamer-Verbindung, und es hat funktioniert. Genau das meine ich, wenn ich von Größenordnungen-Effekt spreche."

---

## 5. Rote-Flagge-Szenarien — was tun, wenn was schiefläuft

| Symptom | Reaktion | Fallback-Trigger |
|---|---|---|
| Claude hängt in der Plan-Phase > 90 s | Sanft nachhaken: „Mach weiter mit Schritt 2 und fang an zu implementieren." | Nach 2. Hänger → Plan B |
| API-Fehler beim ersten Vision-Call | In Claude Code: „Der Fehler ist XYZ, lies die Fehlermeldung, pass das Bild-Handling an." | Nach 2. Fehler → Plan B |
| Einzelnes Foto nicht erkannt | Ignorieren, weitermachen. Kommentar: „KI kommt dort an Grenzen, wo auch ein Mensch den Titel nicht mehr entziffert." | — |
| Streamlit-UI startet nicht | Ausbaustufe weglassen, direkt zur Reflexion. CSV im Editor öffnen und zeigen. | — |
| Internet bricht weg | Hotspot aktivieren (30 s), dann Plan B wenn nicht stabil | Sofort |
| Claude schreibt Code, der nicht läuft | „Führ das Skript aus, lies die Fehlermeldung, korrigiere." Max. 2 Iterationen. | Nach 2. Fehlschlag → Plan B |
| Du merkst, dass du unter 7 Minuten Rest-Zeit bist und noch nicht bei Min 13:00 | UI weglassen, direkt CSV zeigen und zu Reflexion übergehen. | — |

**Goldene Regel:** Bleibe ruhig. Jede Panne ist didaktisches Material — wenn du sie bewusst kommentierst, wird sie Teil der Botschaft („KI ist kein Zauberstab, sie ist ein Werkzeug mit nachvollziehbarem Verhalten").

---

## 6. Plan-B-Aktivierung — drei Zeilen, 30 Sekunden

Trigger: zweimal in Folge Claude-Code-Fehler, oder Internet weg, oder Minute 8:30 ohne ersten Test-Output.

```powershell
cd $demo
Copy-Item -Recurse -Force "G:\OneDrive\Dokumente\2026\Buchprojekte\TODOs\05-narrativ-vorstand\demo_vorbereitung\fallback\*" .
python extract.py ; streamlit run app.py
```

**Umschalt-Satz für den Vorstand** (sag genau das, kein Stottern):

> „Wir nutzen für die Vorführung jetzt die vorab gebaute Version — dieselbe Logik, dieselbe API, nur ohne Live-Build. Das Ergebnis ist identisch, wir sparen fünf Minuten."

Weiter im Zeitraster bei Min 10:00 (Vollausführung).

---

## Kosten-Hinweis (falls der CFO fragt)

- Pro kompletter Durchlauf: 15–25 Fotos × 0,02–0,05 USD Vision-Call = **0,30–1,25 USD**.
- Claude-Code-Orchestrierung: wenige Cent.
- **Summe pro Trockenlauf oder Live-Demo: unter 2 USD.**

---

**Viel Erfolg. Dieses Dokument ist alles, was du am Termin öffnen musst.**
