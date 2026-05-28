"""
Extraktion Buchrücken → strukturiertes Buchverzeichnis.

Liest Fotos aus ./fotos/, schickt jedes an die Anthropic-Vision-API und erzeugt
buecher.csv. Jeder Titel wird gegen Open Library und (als Fallback) Google Books
verifiziert — nicht gefundene Titel bleiben als Halluzinations-Kandidaten stehen.

Rohdaten (volle API-Antwort) werden unter ./ergebnisse/<name>.json gesichert.
Beim zweiten Lauf wird das gecachte JSON verwendet und kein erneuter API-Call
gemacht (außer mit --force-vision oder wenn die JSON-Datei fehlt).

Aufruf:
    python extract.py                            # Opus, alle Fotos, Verifikation (OL+GB), Cache
    python extract.py --limit 1                  # nur erstes Foto
    python extract.py --model claude-sonnet-4-5  # anderes Modell
    python extract.py --no-verify                # ohne Datenbank-Check
    python extract.py --force-vision             # Cache ignorieren, neu rufen
    python extract.py --min-overlap 0.6          # lockerer Titel-Match (Default 0.7)
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    from anthropic import Anthropic
except ImportError:
    sys.stderr.write("FEHLER: pip install anthropic\n")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    sys.stderr.write("FEHLER: pip install pillow\n")
    sys.exit(1)

try:
    import urllib.parse
    import urllib.request
    import urllib.error
except ImportError:
    sys.stderr.write("FEHLER: urllib sollte in Python-Standardlib sein.\n")
    sys.exit(1)


# ============================================================
# KONFIGURATION
# ============================================================

DEFAULT_MODEL = "claude-opus-4-7"
DEFAULT_MIN_OVERLAP = 0.7
MAX_SIDE = 2048
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

SYSTEM_PROMPT = (
    "Du bist ein sorgfältiger Archivar, der Buchrücken in Regalfotos erfasst. "
    "Die absolute Priorität ist Genauigkeit, nicht Vollständigkeit.\n\n"
    "Strenge Regeln:\n"
    "1. Extrahiere nur Bücher, deren Titel du tatsächlich auf dem Buchrücken lesen kannst. "
    "Rate niemals. Erfinde niemals. Wenn du nicht mindestens den Titel deutlich erkennst, "
    "lass das Buch komplett weg.\n"
    "2. Verlagsnamen am Rückenfuß (z.B. 'Wiley', 'Springer', 'Carl Hanser Verlag', "
    "'Fachbuchverlag Leipzig') sind KEINE Buchtitel. Sie gehören in das Feld 'publisher'. "
    "Wenn du NUR einen Verlagsnamen siehst und keinen Titel, lass das Buch weg.\n"
    "3. Autor-Namen auf dem Rücken (häufig klein, oben oder unten) gehören in 'author', "
    "nicht in 'title'. Suche bewusst auch nach kleinem Text am oberen oder unteren "
    "Ende des Buchrückens — dort stehen Autor und Verlag oft. Wenn du dir beim Autor "
    "unsicher bist, setze null.\n"
    "4. Unterscheide Haupttitel von Untertitel: 'title' ist der prominente Haupttitel. "
    "Einen auffälligen Untertitel kannst du im Haupttitel als 'Haupttitel: Untertitel' "
    "zusammenfassen, wenn das eindeutig ist.\n"
    "5. Sicherheitsstufen: 'high' = Titel und Autor klar lesbar oder nur Titel, aber sehr "
    "eindeutig; 'medium' = Titel erkennbar, einzelne Zeichen unsicher; 'low' = ich lese "
    "einzelne Wörter, bin mir aber nicht sicher. 'low' nur verwenden, wenn du mindestens "
    "zu 50% sicher bist. Darunter: weglassen.\n"
    "6. Doppelte Bücher: wenn offensichtlich dasselbe Buch zweimal im Regal steht, liste "
    "es zweimal auf. Wenn du unsicher bist, ob es zwei Exemplare oder eine Ambiguität ist, "
    "liste es nur einmal auf.\n\n"
    "Output: ausschließlich ein JSON-Objekt dieser Struktur (ohne Markdown, ohne Kommentar):\n"
    '{"books":[{"title":"...","author":null,"publisher":null,"year":null,"confidence":"high|medium|low"}]}\n'
    "Pro Foto können es 0 bis viele Bücher sein. Bei 0 Büchern gib {\"books\": []} zurück."
)


# ============================================================
# DATENSTRUKTUREN
# ============================================================

@dataclass
class BookEntry:
    filename: str
    title: Optional[str]
    author: Optional[str]
    publisher: Optional[str]
    year: Optional[str]
    confidence: str
    verified_title: Optional[str] = None
    verified_author: Optional[str] = None
    verified_year: Optional[str] = None
    isbn: Optional[str] = None
    verification_source: Optional[str] = None  # openlibrary | googlebooks | None
    verification_status: str = "unchecked"     # unchecked | found | not_found | error


# ============================================================
# BILDVORBEREITUNG + VISION-API (mit Cache)
# ============================================================

def resize_if_needed(path: Path) -> bytes:
    with Image.open(path) as img:
        img = img.convert("RGB")
        w, h = img.size
        if max(w, h) > MAX_SIDE:
            ratio = MAX_SIDE / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
        import io
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85, optimize=True)
        return buf.getvalue()


def strip_json_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return text


def parse_books_from_raw(raw_text: str, filename: str) -> list[BookEntry]:
    data = json.loads(strip_json_fences(raw_text))
    entries: list[BookEntry] = []
    for b in data.get("books", []):
        entries.append(BookEntry(
            filename=filename,
            title=b.get("title"),
            author=b.get("author"),
            publisher=b.get("publisher"),
            year=str(b["year"]) if b.get("year") is not None else None,
            confidence=b.get("confidence", "low"),
        ))
    return entries


def analyse_foto(
    client: Anthropic,
    foto_path: Path,
    out_json: Path,
    model: str,
    force_vision: bool = False,
) -> tuple[list[BookEntry], bool]:
    if out_json.exists() and not force_vision:
        try:
            raw_text = out_json.read_text(encoding="utf-8").strip()
            entries = parse_books_from_raw(raw_text, foto_path.name)
            return entries, True
        except Exception:
            pass

    image_bytes = resize_if_needed(foto_path)
    image_b64 = base64.standard_b64encode(image_bytes).decode("ascii")

    resp = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_b64,
                    },
                },
                {
                    "type": "text",
                    "text": (
                        "Extrahiere alle deutlich lesbaren Bücher aus dem Foto. "
                        "Strenge Regeln befolgen. Im Zweifel weglassen. "
                        "Antworte ausschließlich mit dem JSON-Objekt."
                    ),
                },
            ],
        }],
    )

    raw_text = "".join(b.text for b in resp.content if b.type == "text").strip()

    out_json.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_json.with_suffix(out_json.suffix + ".tmp")
    tmp.write_text(raw_text, encoding="utf-8")
    os.replace(tmp, out_json)

    entries = parse_books_from_raw(raw_text, foto_path.name)
    return entries, False


# ============================================================
# VERIFIKATION — gemeinsame Helfer
# ============================================================

OL_SEARCH = "https://openlibrary.org/search.json"
GB_SEARCH = "https://www.googleapis.com/books/v1/volumes"
HTTP_TIMEOUT = 10
USER_AGENT = "BookshelfDemo/1.0 (demo use, contact: local)"


def _norm(s: Optional[str]) -> str:
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"[^\w\s]", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _token_overlap(a: str, b: str) -> float:
    ta = set(_norm(a).split())
    tb = set(_norm(b).split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _fetch_json(url: str) -> Optional[dict]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


# ============================================================
# VERIFIKATION — Open Library
# ============================================================

def verify_openlibrary(
    title: str, author: Optional[str], min_overlap: float
) -> dict:
    params = {"title": title, "limit": "5"}
    if author:
        params["author"] = author
    payload = _fetch_json(OL_SEARCH + "?" + urllib.parse.urlencode(params))
    if payload is None:
        return {"status": "error", "source": None, "error": "openlibrary unreachable"}

    docs = payload.get("docs", [])
    if not docs:
        return {"status": "not_found", "source": None}

    best, best_score = None, 0.0
    for doc in docs[:5]:
        score = _token_overlap(title, doc.get("title", "") or "")
        if score > best_score:
            best, best_score = doc, score

    if best is None or best_score < min_overlap:
        return {"status": "not_found", "source": None, "overlap": round(best_score, 2)}

    isbns = best.get("isbn", []) or []
    isbn = next((i for i in isbns if len(i) == 13), None) or (isbns[0] if isbns else None)
    authors = best.get("author_name", []) or []
    first_year = best.get("first_publish_year")

    return {
        "status": "found",
        "source": "openlibrary",
        "title": best.get("title"),
        "author": authors[0] if authors else None,
        "year": str(first_year) if first_year else None,
        "isbn": isbn,
        "overlap": round(best_score, 2),
    }


# ============================================================
# VERIFIKATION — Google Books (Fallback)
# ============================================================

def verify_googlebooks(
    title: str, author: Optional[str], min_overlap: float
) -> dict:
    # Google Books: Suchsyntax mit intitle: und inauthor:
    q_parts = [f'intitle:"{title}"']
    if author:
        q_parts.append(f'inauthor:"{author}"')
    params = {"q": " ".join(q_parts), "maxResults": "5"}
    payload = _fetch_json(GB_SEARCH + "?" + urllib.parse.urlencode(params))
    if payload is None:
        return {"status": "error", "source": None, "error": "googlebooks unreachable"}

    items = payload.get("items", []) or []
    if not items:
        return {"status": "not_found", "source": None}

    best, best_score = None, 0.0
    for item in items[:5]:
        vi = item.get("volumeInfo", {})
        score = _token_overlap(title, vi.get("title", "") or "")
        if score > best_score:
            best, best_score = vi, score

    if best is None or best_score < min_overlap:
        return {"status": "not_found", "source": None, "overlap": round(best_score, 2)}

    # ISBN aus industryIdentifiers ziehen, ISBN_13 bevorzugt
    isbn = None
    for ident in best.get("industryIdentifiers", []) or []:
        if ident.get("type") == "ISBN_13":
            isbn = ident.get("identifier")
            break
    if not isbn:
        for ident in best.get("industryIdentifiers", []) or []:
            if ident.get("type") == "ISBN_10":
                isbn = ident.get("identifier")
                break

    authors = best.get("authors", []) or []
    published = best.get("publishedDate", "") or ""
    year = published[:4] if len(published) >= 4 and published[:4].isdigit() else None

    return {
        "status": "found",
        "source": "googlebooks",
        "title": best.get("title"),
        "author": authors[0] if authors else None,
        "year": year,
        "isbn": isbn,
        "overlap": round(best_score, 2),
    }


# ============================================================
# VERIFIKATION — Orchestrierung
# ============================================================

def verify_title(
    title: str, author: Optional[str], min_overlap: float, try_googlebooks: bool = True
) -> dict:
    """Verifiziert erst gegen Open Library, dann als Fallback Google Books."""
    ol = verify_openlibrary(title, author, min_overlap)
    if ol["status"] == "found":
        return ol
    if not try_googlebooks:
        return ol
    gb = verify_googlebooks(title, author, min_overlap)
    if gb["status"] == "found":
        return gb
    # Wenn beide „not_found": kombinierter Status
    if ol["status"] == "error" and gb["status"] == "error":
        return ol
    return {"status": "not_found", "source": None}


def apply_verification(entry: BookEntry, result: dict) -> None:
    entry.verification_status = result.get("status", "error")
    entry.verification_source = result.get("source")
    if result.get("status") == "found":
        entry.verified_title = result.get("title")
        entry.verified_author = result.get("author")
        entry.verified_year = result.get("year")
        entry.isbn = result.get("isbn")


# ============================================================
# CSV-OUTPUT
# ============================================================

CSV_HEADERS = [
    "Dateiname", "Titel", "Autor", "Verlag", "Jahr", "Sicherheit",
    "Verifikation", "Verifizierter Titel", "Verifizierter Autor",
    "Verifiziertes Jahr", "ISBN", "Quelle",
]


def write_csv(entries: list[BookEntry], out_path: Path) -> Path:
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(CSV_HEADERS)
        for e in entries:
            writer.writerow([
                e.filename, e.title or "", e.author or "",
                e.publisher or "", e.year or "", e.confidence,
                e.verification_status, e.verified_title or "",
                e.verified_author or "", e.verified_year or "",
                e.isbn or "", e.verification_source or "",
            ])
    try:
        os.replace(tmp, out_path)
        return out_path
    except PermissionError:
        stamp = time.strftime("%Y%m%d_%H%M%S")
        fallback = out_path.with_stem(out_path.stem + "_" + stamp)
        os.replace(tmp, fallback)
        sys.stderr.write(
            f"\nWARNUNG: '{out_path.name}' ist gesperrt (in Excel offen?). "
            f"CSV wurde stattdessen als '{fallback.name}' gespeichert.\n"
        )
        return fallback


# ============================================================
# MAIN
# ============================================================

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fotos", default="fotos")
    parser.add_argument("--out", default="buecher.csv")
    parser.add_argument("--ergebnisse", default="ergebnisse")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"Default: {DEFAULT_MODEL}")
    parser.add_argument("--no-verify", action="store_true")
    parser.add_argument("--no-googlebooks", action="store_true",
                        help="Google Books als Fallback deaktivieren (nur Open Library)")
    parser.add_argument("--force-vision", action="store_true")
    parser.add_argument("--verify-sleep", type=float, default=0.3)
    parser.add_argument("--min-overlap", type=float, default=DEFAULT_MIN_OVERLAP,
                        help=f"Mindest-Token-Overlap Titel (Default {DEFAULT_MIN_OVERLAP})")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.stderr.write(
            "FEHLER: ANTHROPIC_API_KEY nicht gesetzt.\n"
            "  .env aus Vorlage anlegen:  cp .env.example .env  (dann Key eintragen)\n"
            "  In aktuelle Shell laden:   set -a; source .env; set +a\n"
            "  Oder direkt exportieren:   export ANTHROPIC_API_KEY=\"sk-ant-...\"\n"
        )
        return 1

    foto_dir = Path(args.fotos)
    if not foto_dir.is_dir():
        sys.stderr.write(f"FEHLER: Ordner '{foto_dir}' nicht gefunden.\n")
        return 2

    fotos = sorted(p for p in foto_dir.iterdir()
                   if p.is_file() and p.suffix.lower() in IMAGE_EXTS)
    if args.limit:
        fotos = fotos[: args.limit]
    if not fotos:
        sys.stderr.write(f"FEHLER: keine Bilder in '{foto_dir}' gefunden.\n")
        return 3

    verify_sources = []
    if not args.no_verify:
        verify_sources.append("Open Library")
        if not args.no_googlebooks:
            verify_sources.append("Google Books")

    print(f"Foto-Ordner:    {foto_dir.resolve()}")
    print(f"Bilder:         {len(fotos)}")
    print(f"Modell:         {args.model}")
    print(f"CSV:            {Path(args.out).resolve()}")
    print(f"Verifikation:   {', '.join(verify_sources) if verify_sources else 'aus'}")
    print(f"Min-Overlap:    {args.min_overlap}")
    print(f"Vision-Cache:   {'ignoriert (--force-vision)' if args.force_vision else 'aktiv'}")
    print("-" * 60)

    client = Anthropic()
    all_entries: list[BookEntry] = []
    vision_errors: list[tuple[str, str]] = []
    cache_hits = 0

    # Phase 1: Vision
    for i, foto in enumerate(fotos, start=1):
        out_json = Path(args.ergebnisse) / f"{foto.stem}.json"
        print(f"  [VISION {i:>2}/{len(fotos)}] {foto.name} ... ", end="", flush=True)
        try:
            t0 = time.time()
            entries, from_cache = analyse_foto(
                client, foto, out_json, args.model,
                force_vision=args.force_vision,
            )
            t1 = time.time()
            tag = " (aus Cache)" if from_cache else f" ({t1 - t0:.1f}s)"
            print(f"{len(entries)} Buch/Bücher{tag}")
            if from_cache:
                cache_hits += 1
            all_entries.extend(entries)
        except Exception as exc:
            print(f"FEHLER: {exc}")
            vision_errors.append((foto.name, str(exc)))

    written_to = write_csv(all_entries, Path(args.out))

    # Phase 2: Verifikation (OL, dann Google Books als Fallback)
    verify_errors: list[tuple[str, str]] = []
    if not args.no_verify and all_entries:
        print("-" * 60)
        src_info = "Open Library" + ("" if args.no_googlebooks else " → Google Books")
        print(f"Verifikation gegen {src_info} ...")
        for i, entry in enumerate(all_entries, start=1):
            if not entry.title:
                continue
            label = (entry.title[:50] + "…") if len(entry.title) > 50 else entry.title
            print(f"  [VERIFY {i:>3}/{len(all_entries)}] {label} ... ", end="", flush=True)
            try:
                result = verify_title(
                    entry.title, entry.author,
                    min_overlap=args.min_overlap,
                    try_googlebooks=not args.no_googlebooks,
                )
                apply_verification(entry, result)
                if result["status"] == "found":
                    src = result.get("source") or "?"
                    isbn = result.get("isbn") or "keine ISBN"
                    print(f"✓ [{src}] {result.get('title', '')} ({isbn})")
                elif result["status"] == "not_found":
                    print("✗ nicht gefunden")
                else:
                    print(f"! {result.get('error', 'Fehler')}")
            except Exception as exc:
                print(f"FEHLER: {exc}")
                entry.verification_status = "error"
                verify_errors.append((entry.title or "?", str(exc)))
            if args.verify_sleep > 0:
                time.sleep(args.verify_sleep)
        written_to = write_csv(all_entries, Path(args.out))

    # Zusammenfassung
    print("-" * 60)
    print(f"CSV geschrieben: {written_to.resolve()} ({len(all_entries)} Zeilen)")
    if cache_hits:
        print(f"Cache genutzt:   {cache_hits}/{len(fotos)} Fotos (keine API-Kosten für diese)")
    if vision_errors:
        print(f"Vision-Fehler:   {len(vision_errors)}")
        for name, msg in vision_errors:
            print(f"  - {name}: {msg}")
    if verify_errors:
        print(f"Verifikations-Fehler: {len(verify_errors)}")

    conf = {}
    for e in all_entries:
        conf[e.confidence] = conf.get(e.confidence, 0) + 1
    if conf:
        print("Sicherheit (Claude):", ", ".join(f"{k}={v}" for k, v in sorted(conf.items())))

    if not args.no_verify:
        vs = {}
        for e in all_entries:
            vs[e.verification_status] = vs.get(e.verification_status, 0) + 1
        print("Verifikation:       ", ", ".join(f"{k}={v}" for k, v in sorted(vs.items())))

        src = {}
        for e in all_entries:
            if e.verification_source:
                src[e.verification_source] = src.get(e.verification_source, 0) + 1
        if src:
            print("Treffer-Quelle:     ", ", ".join(f"{k}={v}" for k, v in sorted(src.items())))

        found = sum(1 for e in all_entries if e.verification_status == "found")
        not_found = sum(1 for e in all_entries if e.verification_status == "not_found")
        if len(all_entries) > 0:
            pct_found = 100 * found / len(all_entries)
            print(f"→ {found}/{len(all_entries)} ({pct_found:.0f}%) verifiziert")
            print(f"→ {not_found} nicht verifiziert (selten oder halluziniert)")

    return 0 if not vision_errors else 4


if __name__ == "__main__":
    sys.exit(main())
