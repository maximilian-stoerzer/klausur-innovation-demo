# ABLAUF.md — Live-Demo Bücherregal (Einzeldatei für den Termin)

> **Zweck dieser Datei:** Alles, was du im Vorstandstermin brauchst, auf einer Seite. Nicht zwischen Dateien springen. Pre-Flight (zwei Blöcke), Prompt v3, Zeitraster, Kommentare, rote Flaggen, Plan B — in dieser Reihenfolge.
>
> **Zeit-Rechnung nach Trockenlauf 2:** Installation + `claude`-Start kostete 5–6 Min, reine Skript-Laufzeit 9 Min sequentiell → im 20-Min-Slot eng. **Fix:** Installation VOR Termin (1.1), Parallelisierung im Prompt (Abschnitt 2). Neue Laufzeit im Slot: **4–6 Min für Extraktion + Verifikation**.

---

## 1. Pre-Flight — zwei Blöcke

### 1.1 VOR dem Termin (am Vortag oder mindestens 30 Min vorher)

Installation, Keys setzen, einmal durchtesten. **Diese Punkte dürfen nicht im Slot stattfinden.**

- [ ] Node.js LTS + Claude Code installiert: `claude --version` gibt Versionsnummer.
- [ ] Python 3.12+ installiert: `python --version`.
- [ ] `ANTHROPIC_API_KEY` dauerhaft gesetzt (User-Scope, nicht nur Session):
  ```powershell
  [Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "sk-ant-DEIN-KEY", "User")
  ```
- [ ] `GOOGLE_BOOKS_API_KEY` dauerhaft gesetzt (hebt Quota von 1.000 auf 100.000 Requests/Tag — sonst hängen im Slot die Verifikationen):
  ```powershell
  [Environment]::SetEnvironmentVariable("GOOGLE_BOOKS_API_KEY", "DEIN-GOOGLE-KEY", "User")
  ```
  PowerShell-Fenster danach neu öffnen, damit die Variablen greifen.
- [ ] Demo-Ordner einmal angelegt und Venv installiert:
  ```powershell
  $demo = "C:\Temp\vorstand_demo"
  Remove-Item $demo -Recurse -Force -ErrorAction SilentlyContinue
  New-Item -ItemType Directory -Path $demo | Out-Null
  Copy-Item "G:\OneDrive\Dokumente\2026\Buchprojekte\TODOs\05-narrativ-vorstand\demo_vorbereitung\CLAUDE.md" $demo
  Copy-Item "G:\OneDrive\Dokumente\2026\Buchprojekte\TODOs\05-narrativ-vorstand\demo_vorbereitung\fotos" $demo -Recurse
  cd $demo
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install anthropic pillow streamlit
  python -c "import anthropic, PIL, streamlit; print('OK')"
  ```
  Die letzte Zeile MUSS `OK` ausgeben.
- [ ] Einmal einen Trockenlauf mit `claude` durchgespielt. Die `./ergebnisse/`-Dateien bleiben danach als Cache liegen — im Live-Termin entscheidest du spontan: neu laufen oder Cache nutzen.

### 1.2 IM Termin, 3 Minuten vor Slot-Start

- [ ] Beamer klebt, Zweitmonitor erweitert, Terminal-Schrift ≥ 16pt.
- [ ] Internet ≥ 20 Mbit down, Handy-Hotspot als Backup bereit.
- [ ] Teams/Outlook/Slack/Browser-Notifications alle stumm, Bildschirm-Sleep ≥ 30 min.
- [ ] Stoppuhr auf Smartphone griffbereit.
- [ ] Demo-Ordner frisch, Venv aktiv, beide Keys gesetzt, `claude` einsatzbereit:
  ```powershell
  $demo = "C:\Temp\vorstand_demo"
  Remove-Item "$demo\ergebnisse" -Recurse -Force -ErrorAction SilentlyContinue
  Remove-Item "$demo\buecher.csv" -Force -ErrorAction SilentlyContinue
  cd $demo
  .\.venv\Scripts\Activate.ps1
  echo "Anthropic: $($env:ANTHROPIC_API_KEY.Substring(0,10))..."
  echo "Google Books: $($env:GOOGLE_BOOKS_API_KEY.Substring(0,10))..."
  # Beide Zeilen müssen Key-Präfixe zeigen, nicht leer sein.
  ```

**Entscheidung Cache vs. Live:** Wenn du den Slot absolut sicher halten willst, lösche `ergebnisse/` NICHT — dann nutzt Claude den Cache, Vision-Calls entfallen, Laufzeit <1 Min. Kommentiere das transparent: „Die API-Calls aus dem Trockenlauf sind gecacht — gleicher Prompt, gleiches Modell, nur vorgezogen."

---

## 2. Claude-Prompt v3 — Copy-Paste-Block für den Live-Termin

Terminal öffnen, `claude` starten, den Block **zwischen den Trennstrichen** pasten, Enter.

> **Wichtig:** Der Prompt verlangt explizit `claude-opus-4-6`, **Parallelisierung** (2–3 Vision-Calls gleichzeitig, Verifikation stream-parallel) und Pflicht-Verifikation gegen Open Library + Google Books. Das hebt die Laufzeit von 9 auf ~4 Min. Nicht abkürzen.

---

```
Ziel: Ich möchte aus den Bildern in ./fotos/ ein strukturiertes, verifiziertes Bücherverzeichnis erstellen. Jedes Bild zeigt Buchrücken aus meinem Bücherregal. Am Ende soll eine CSV-Datei buecher.csv im Projektordner liegen mit den Spalten:
Dateiname, Titel, Autor, Verlag, Jahr, Sicherheit, Verifikation, Verifizierter Titel, Verifizierter Autor, Verifiziertes Jahr, ISBN, Quelle.

Das wichtigste Qualitätsziel: KEINE Halluzinationen. Lieber weniger Bücher, aber jedes erkannte Buch soll wirklich auf dem Foto stehen UND in einer öffentlichen Bibliotheks-Datenbank existieren.

Zweites Ziel: Geschwindigkeit. Der Vortrag hat ein Zeitbudget — parallelisiere, wo es geht (siehe Schritt 2B).

Vorgehen:

1. Analysiere zuerst den Ordner ./fotos/. Zeig mir, welche Bilddateien du siehst. Kurze Rückfrage, falls etwas unklar ist.

2. Plane dann die Implementierung. Drei Bausteine:

   A) Vision-Extraktion — extract.py
   - Nutze die Anthropic-Python-Library (`anthropic`) und das Modell `claude-opus-4-6` (NICHT sonnet — Opus halluziniert deutlich weniger).
   - System-Prompt mit folgenden strengen Regeln (wortwörtlich übernehmen, das ist kritisch):
     "Du bist ein sorgfältiger Archivar, der Buchrücken in Regalfotos erfasst. Die absolute Priorität ist Genauigkeit, nicht Vollständigkeit.
     1. Extrahiere nur Bücher, deren Titel du tatsächlich auf dem Buchrücken lesen kannst. Rate niemals. Erfinde niemals. Wenn du nicht mindestens den Titel deutlich erkennst, lass das Buch komplett weg.
     2. Verlagsnamen am Rückenfuß (z.B. 'Wiley', 'Springer', 'Carl Hanser Verlag') sind KEINE Buchtitel. Sie gehören in 'publisher'. Wenn du NUR einen Verlagsnamen siehst und keinen Titel, lass das Buch weg.
     3. Autor-Namen gehören in 'author', nicht in 'title'. Bei Unsicherheit beim Autor: null.
     4. Untertitel im Haupttitel nur aufnehmen, wenn eindeutig ('Haupttitel: Untertitel').
     5. Sicherheitsstufen streng: 'high' = klar lesbar; 'medium' = erkennbar, einzelne Zeichen unsicher; 'low' = mindestens 50 % sicher. Alles darunter: weglassen.
     6. Doppelte Bücher nur auflisten, wenn offensichtlich. Bei Unsicherheit: nur einmal.
     Output: JSON der Form {\"books\":[{\"title\":...,\"author\":null,\"publisher\":null,\"year\":null,\"confidence\":\"high|medium|low\"}]}"
   - Funktion `analyse_foto(pfad)`: Bild als base64 an Claude, JSON zurück, Rohantwort als Backup unter ./ergebnisse/<dateiname>.json speichern.
   - Cache: wenn ./ergebnisse/<dateiname>.json existiert, diese nutzen statt erneut API rufen (außer mit --force-vision).
   - Bildgröße: falls Foto > 5 MB oder lange Seite > 2048 px, mit Pillow herunterskalieren.

   B) Pipeline — PARALLELISIERT, das ist wichtig für die Laufzeit
   - Nutze `concurrent.futures.ThreadPoolExecutor` mit zwei Pools:
     * Vision-Pool: max_workers=3 (Anthropic verträgt das problemlos, drei Fotos laufen gleichzeitig in Vision-Calls).
     * Verification-Pool: max_workers=6 (OL/GB sind HTTP und warten viel, können mehr parallel).
   - Ablauf: `submit()` alle Fotos in den Vision-Pool. Sobald eins fertig ist (`as_completed()`), lies das JSON, extrahiere die Bücher, und `submit()` pro Buch sofort die Verifikation in den Verification-Pool. Die Verifikation darf also anlaufen, während spätere Fotos noch in Vision sind.
   - Fortschrittsanzeige: zwei Zähler, z.B. `Vision 4/11  Verifiziert 37 (29 OL, 5 GB, 3 pending)`. Zeile pro Sekunde aktualisieren, nicht pro Event.
   - Erst am Ende, nach `wait()` auf beide Pools, CSV schreiben.

   C) Verifikation — in extract.py
   - Für jeden erkannten Titel: Abgleich gegen Open Library (https://openlibrary.org/search.json?title=...&author=... falls Autor vorhanden, sonst nur title).
   - Wenn Open Library keinen Treffer liefert: Fallback Google Books. Der API-Key wird aus der Umgebungsvariable GOOGLE_BOOKS_API_KEY gelesen und als `&key=...` an den Request angehängt. Wenn die Variable leer ist, Google Books ohne Key aufrufen (begrenzte Quota, max. 1.000 Requests/Tag).
   - URL Google Books: https://www.googleapis.com/books/v1/volumes?q=intitle:<title>+inauthor:<author>&key=<key>
   - Match-Kriterium: Token-Overlap (Jaccard-ähnlich) zwischen Claude-Titel und Datenbank-Titel >= 0.7 nach Normalisierung (lowercase, Satzzeichen weg, Stopwörter raus: the, der, die, das, a, an, and, und).
   - Ergebnis pro Buch:
     - Verifikation: found | not_found | error
     - Verifizierter Titel / Autor / Jahr / ISBN aus der Datenbank, falls gefunden
     - Quelle: openlibrary | googlebooks | (leer bei not_found)
   - Kein Verwerfen: auch nicht-gefundene Bücher bleiben in der CSV, nur mit Verifikation=not_found markiert.
   - HTTP-Timeout: 5 s. Bei Timeout oder 429: Verifikation=error, weiter machen.

3. Implementiere extract.py. Führe es dann mit --limit 1 und --print-raw probeweise aus, bevor du alle anfasst. Zeig mir die Rohantwort UND das Verifikationsergebnis (gefunden/nicht gefunden + Quelle) für dieses eine Foto.

4. Wenn das Einzelfoto sauber ist: volle Verarbeitung aller Fotos in ./fotos/ mit beiden Pools parallel. Fortschrittsanzeige im Terminal (Vision X/Y, Verifiziert Z).

5. Am Ende explizite Zusammenfassung — diese Zeilen WÖRTLICH im Output:
   - "Fotos verarbeitet: X"
   - "Bücher erkannt: Y (high: a, medium: b, low: c)"
   - "Verifikationsrate: P % (found: Z, not_found: N, error: E)"
   - "Quellen: Open Library: O, Google Books: G"

Technische Hinweise:
- Anthropic-API-Key aus Umgebungsvariable ANTHROPIC_API_KEY.
- Google-Books-API-Key aus Umgebungsvariable GOOGLE_BOOKS_API_KEY (optional, hebt Quota-Limit).
- Error Handling: einzelne fehlgeschlagene Fotos überspringen, Fehler sammeln, am Ende anzeigen. Kein harter Abbruch.
- CSV: UTF-8 mit BOM (Excel-kompatibel), Semikolon als Trennzeichen.

Nicht jetzt nötig, aber als nächster Schritt danach: Streamlit-UI (app.py), die die CSV lädt, Filter nach Verifikation/Sicherheit/Autor bietet und Foto-Vorschau zeigt. Das kommt erst, wenn Extraktion + Verifikation stehen.

Los.
```

---

## 3. Minute-für-Minute — Soll-Zeitraster (v3, parallelisiert)

Zwei Varianten, je nach Pre-Flight-Entscheidung in 1.2:

### 3A Variante LIVE (Vision-Calls laufen frisch, keine Cache-Nutzung)

| Ab Min | Inhalt | Was du tust | Was der Vorstand sieht |
|---|---|---|---|
| 0:00 | Challenge-Folie | „Eingabe ~11 Fotos, Ziel verifizierte Bestandsliste, Zeit 10 Minuten." | Folie 5 der PPTX |
| 0:30 | Terminal-Wechsel | Vom Folienmodus auf Terminal, `claude` starten | Leerer Claude-Prompt, `fotos/` sichtbar |
| 0:45 | Prompt einfügen | Block aus Abschnitt 2 pasten, Enter | Prompt erscheint, Claude antwortet |
| 1:30 | Plan-Phase | Rückfragen kurz bestätigen | Claude listet die drei Bausteine (Vision / Pipeline / Verifikation) |
| 3:00 | Bau-Phase | Claude schreibt `extract.py`, installiert Dependencies, baut ThreadPool-Pipeline und Verifikationsfunktionen | Dateien entstehen, Code erscheint |
| 7:30 | Erster Test (1 Foto) | `python extract.py --limit 1 --print-raw` | JSON-Antwort + Verifikations-Ergebnis |
| 8:30 | Vollausführung parallel | Claude startet vollen Lauf, Pool 3 Vision / 6 Verifikation | Fortschrittszeile `Vision 4/11 Verifiziert 37` |
| 12:00 | CSV fertig + Zusammenfassung | Claude liest die vier Zusammenfassungszeilen vor | Zahlen im Terminal: Fotos, Bücher, Verifikationsrate, Quellen |
| 13:00 | Ausbau Streamlit | „Jetzt bitte noch die UI wie in `CLAUDE.md`." | `app.py` entsteht |
| 16:00 | UI starten | `streamlit run app.py` | Tabelle mit Filtern + Foto-Vorschau im Browser |
| 17:00 | Reflexion | Einordnung: „Klassisch vier Wochen, fünfstelliges Budget — wir: unter 20 Minuten." | Zurück zur Präsentation |
| 20:00 | Übergang | Folie „3. Der Long Tail" | Nächstes Kapitel |

**Kritischer Checkpoint:** Minute 7:30 — erster Test muss JSON-Output zeigen. Wenn nicht → Plan B (Abschnitt 6).

### 3B Variante CACHE (Vision-Ergebnisse aus Trockenlauf bleiben liegen)

Wenn du in 1.2 den Ordner `ergebnisse/` nicht gelöscht hast: Claude baut Code, Test ist sofort fertig, Vollausführung dauert <1 Min. Du gewinnst 4–5 Min Puffer für Reflexion und Diskussion.

| Ab Min | Inhalt | Differenz zu 3A |
|---|---|---|
| 0:00–7:30 | Wie 3A | — |
| 7:30 | Erster Test | Cache-Hit, antwortet sofort |
| 8:00 | Vollausführung | <1 Min wegen Cache |
| 9:00 | Zusammenfassung + CSV fertig | 3 Min früher als 3A |
| 10:00 | Ausbau Streamlit | — |
| 13:00 | UI fertig | — |
| 14:00–20:00 | Reflexion + Diskussion (6 Min statt 3) | Deutlich entspannter |

Kommentar-Ansage bei Cache-Variante (Minute 8:00): „Die Vision-Calls sind gecacht aus dem Trockenlauf — gleiche API, gleicher Prompt, nur vorgezogen. Das Ergebnis ist identisch, wir sparen die API-Wartezeit."

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
