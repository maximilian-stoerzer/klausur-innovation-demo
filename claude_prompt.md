# Claude-Code-Prompt für die Live-Demo (v3 — parallelisiert + Google-Books-Key)

> **Changelog v3 (2026-04-24, nachmittags):**
> - Parallelisierung: Vision-Calls laufen 2–3fach gleichzeitig, Verifikation beginnt streamweise, sobald ein Foto zurück ist. Erwartete Laufzeit 4–6 Min statt 12–14 Min.
> - Google-Books-API-Key wird aus `GOOGLE_BOOKS_API_KEY` gelesen (hebt Quota von 1.000 auf 100.000 Requests/Tag).
> - Verifikationsrate (found / not_found, OL vs. GB) wird am Ende explizit ausgegeben.
>
> **Changelog v2:** Opus 4.6 + strenge Anti-Halluzinations-Regeln + Pflicht-Verifikation gegen Open Library und Google Books.

## Wie du diesen Prompt benutzt

1. Vor dem Demo-Termin: Pre-Flight aus `ABLAUF.md` Abschnitt 1 abarbeiten. Installation MUSS fertig sein, bevor der Termin beginnt.
2. Im Termin: Terminal öffnen, in den vorbereiteten Demo-Projektordner wechseln, `claude` starten.
3. Den folgenden Block **zwischen den Trennstrichen** kopieren und in Claude Code einfügen. Enter.
4. Claude plant, fragt ggf. zurück — kurz bestätigen, dann implementieren lassen.

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

## Was gegenüber v2 neu ist

- **Parallelisierung (Abschnitt 2B):** Vision-Calls 3fach, Verifikation 6fach, Pipeline-Start sobald ein Foto zurück ist. Reduziert die reine Laufzeit von ~9 Min auf ~3–4 Min bei 11 Fotos.
- **Google-Books-API-Key:** wird aus `GOOGLE_BOOKS_API_KEY` gelesen. Ohne Key: Quota greift bei ~1.000 Requests/Tag (= ein Trockenlauf). Mit Key: 100.000/Tag — kein Problem mehr.
- **Explizite Zusammenfassung (Schritt 5):** vier wörtliche Output-Zeilen, damit du die Zahlen direkt vorlesen kannst, statt im Kopf zu rechnen.

## Warum so und nicht `asyncio`

ThreadPoolExecutor ist für dieses Szenario einfacher, robuster und für I/O-lastige Tasks (HTTP) völlig ausreichend. `asyncio` würde sowohl für die Anthropic-Library als auch für den Live-Build mehr Risiko bringen. Einfach > elegant.

## Variationen für spontane Anpassungen

- **Wenn Zeit knapp wird:** `max_workers=5` im Vision-Pool setzen (Anthropic schluckt das). Der Code ist parametrisiert.
- **Wenn Google Books Quota-Fehler (403):** `GOOGLE_BOOKS_API_KEY` in der Shell neu setzen — oder im Prompt „überspringe Google Books, nur Open Library" ergänzen.
- **Wenn ein Foto partout nicht klappt:** kommentieren „KI kommt an Grenzen, wo auch ein Mensch den Rücken nicht mehr lesen kann — und das ehrliche Eingeständnis ist besser als falsche Treffer."
