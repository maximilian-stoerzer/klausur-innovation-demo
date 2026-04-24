# Claude-Code-Prompt für die Live-Demo

## Wie du diesen Prompt benutzt

1. Im Demo-Termin: Terminal öffnen, in den vorbereiteten Demo-Projektordner wechseln (dort liegt die `CLAUDE.md` und `fotos/` mit den Aufnahmen).
2. `claude` starten.
3. Den folgenden Block **zwischen den Trennstrichen** kopieren und in Claude Code einfügen. Enter.
4. Claude plant, fragt ggf. zurück — kurz bestätigen, dann implementieren lassen.

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

## Warum so formuliert

- **Ziel zuerst**, dann **Vorgehen** in Schritten — das strukturiert Claudes Plan.
- **Rückfrage erlaubt** (Schritt 1), damit Claude bei Unklarheit fragt statt falsch implementiert.
- **Probelauf vor Vollausführung** (Schritt 3) — vermeidet Totalabbruch, wenn das Prompt-Schema nicht stimmt.
- **Rohdaten-Backup** (`./ergebnisse/<datei>.json`) — falls wir später Parsing-Logik ändern wollen, müssen wir nicht erneut die API bemühen.
- **Nicht jetzt nötig**-Abschnitt am Ende: schafft einen optionalen Ausbauweg ohne ihn zu erzwingen. Wenn die Haupt-Extraktion zügig läuft, kann Claude weitermachen.
- **Bildgrößen-Hinweis** erspart einen klassischen API-Fehler („image too large").
- **Fehler-Toleranz**: explizit definiert, damit ein einzelnes schlechtes Foto nicht den ganzen Lauf killt.

## Variationen für spontane Anpassungen im Termin

- **Wenn Zeit knapp wird:** nach Schritt 4 direkt zur Reflexion übergehen; Streamlit-UI weglassen oder aus `fallback/app.py` schnell nachladen.
- **Wenn du mehr zeigen willst:** in Schritt 2 ein zusätzliches Feld aufnehmen, z. B. „Genre" oder „Sprache" — Claude erweitert das Schema sauber.
- **Wenn ein Foto partout nicht klappt:** darum kommentierst du „das zeigt auch die Grenzen — manche Eingabe-Qualität reicht nicht, KI macht keine Wunder, wo der Mensch nichts erkennt."
