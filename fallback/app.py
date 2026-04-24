"""
Streamlit-UI für die Demo. Zeigt die buecher.csv als sortierbare, filterbare
Tabelle inklusive Miniaturbild des Ursprungsfotos.

Aufruf:
    streamlit run app.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import streamlit as st
from PIL import Image

CSV_FILE = Path("buecher.csv")
FOTO_DIR = Path("fotos")

st.set_page_config(
    page_title="Bücherregal-Katalog",
    page_icon="📚",
    layout="wide",
)


VERIFIKATIONS_LABEL = {
    "found": "✓ gefunden",
    "not_found": "✗ nicht gefunden",
    "unchecked": "— nicht geprüft",
    "error": "! Fehler",
}
SICHERHEITS_LABEL = {"high": "hoch", "medium": "mittel", "low": "niedrig"}


def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        return list(reader)


def pct(n: int, total: int) -> str:
    return f"{100 * n / total:.0f}%" if total else "-"


def main() -> None:
    st.title("Bücherregal-Katalog")
    st.caption(
        "Erzeugt aus Fotos von Buchrücken mit Claude Vision, "
        "verifiziert gegen Open Library und Google Books"
    )

    entries = load_csv(CSV_FILE)
    if not entries:
        st.warning(
            f"Keine Daten gefunden ({CSV_FILE} fehlt oder ist leer). "
            "Bitte zuerst `python extract.py` ausführen."
        )
        return

    total = len(entries)
    n_found = sum(1 for e in entries if e.get("Verifikation") == "found")
    n_high = sum(1 for e in entries if e.get("Sicherheit") == "high")
    n_fotos = len({e.get("Dateiname", "") for e in entries if e.get("Dateiname")})
    n_autoren_erkannt = len({e.get("Autor", "") for e in entries if e.get("Autor")})
    n_autoren_verif = len(
        {e.get("Verifizierter Autor", "") for e in entries if e.get("Verifizierter Autor")}
    )
    n_mit_isbn = sum(1 for e in entries if e.get("ISBN"))

    # Top-Metriken
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Bücher erkannt", total, help=f"aus {n_fotos} Fotos")
    col2.metric(
        "Verifiziert",
        f"{n_found} ({pct(n_found, total)})",
        help="in Open Library oder Google Books gefunden",
    )
    col3.metric(
        "Mit hoher Sicherheit (Claude)",
        f"{n_high} ({pct(n_high, total)})",
    )
    col4.metric(
        "Mit ISBN",
        n_mit_isbn,
        help="ISBN-13 oder ISBN-10 aus der Datenbank",
    )

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Autoren (Claude erkannt)", n_autoren_erkannt)
    col6.metric("Autoren (Datenbank ergänzt)", n_autoren_verif)
    n_ol = sum(1 for e in entries if e.get("Quelle") == "openlibrary")
    n_gb = sum(1 for e in entries if e.get("Quelle") == "googlebooks")
    col7.metric("Open-Library-Treffer", n_ol)
    col8.metric("Google-Books-Treffer", n_gb)

    st.divider()

    # Sidebar: Filter
    with st.sidebar:
        st.header("Filter")

        verif_values = [v for v in ["found", "not_found", "unchecked", "error"]
                        if any(e.get("Verifikation") == v for e in entries)]
        verif_default = [v for v in verif_values if v != "unchecked"]
        verif_filter = st.multiselect(
            "Verifikation",
            options=verif_values,
            default=verif_default,
            format_func=lambda v: VERIFIKATIONS_LABEL.get(v, v),
        )

        quelle_values = sorted({e.get("Quelle", "") for e in entries if e.get("Quelle")})
        quelle_filter = st.multiselect(
            "Quelle (Datenbank)",
            options=quelle_values,
            default=quelle_values,
            help="openlibrary = Open Library, googlebooks = Google Books",
        )
        include_quelle_leer = st.checkbox(
            "Einträge ohne Quellen-Treffer einschließen",
            value=True,
            help="Wenn deaktiviert: nur Einträge, die einer Datenbank zugeordnet wurden",
        )

        sicherheit_values = [s for s in ["high", "medium", "low"]
                             if any(e.get("Sicherheit") == s for e in entries)]
        sicherheit_filter = st.multiselect(
            "Sicherheit (Claude-Selbsteinschätzung)",
            options=sicherheit_values,
            default=sicherheit_values,
            format_func=lambda s: SICHERHEITS_LABEL.get(s, s),
        )

        mit_isbn = st.checkbox("Nur Einträge mit ISBN", value=False)
        autoren = sorted({e.get("Autor", "") for e in entries if e.get("Autor")})
        autor_filter = st.multiselect("Autor (aus Foto erkannt)", autoren, default=[])

        suche = st.text_input("Suche (Titel, verifizierter Titel, Verlag)", "")

    def match(e: dict) -> bool:
        if verif_filter and e.get("Verifikation") not in verif_filter:
            return False
        if quelle_filter:
            q = e.get("Quelle", "") or ""
            if q:
                if q not in quelle_filter:
                    return False
            else:
                if not include_quelle_leer:
                    return False
        elif not include_quelle_leer and not (e.get("Quelle", "") or ""):
            return False
        if sicherheit_filter and e.get("Sicherheit") not in sicherheit_filter:
            return False
        if mit_isbn and not e.get("ISBN"):
            return False
        if autor_filter and e.get("Autor") not in autor_filter:
            return False
        if suche:
            needle = suche.lower()
            hay = " ".join([
                e.get("Titel") or "",
                e.get("Verifizierter Titel") or "",
                e.get("Verlag") or "",
                e.get("Autor") or "",
                e.get("Verifizierter Autor") or "",
            ]).lower()
            if needle not in hay:
                return False
        return True

    filtered = [e for e in entries if match(e)]

    st.subheader(f"Ergebnisse: {len(filtered)} von {total}")

    # Tabelle
    if filtered:
        st.dataframe(
            filtered,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Dateiname": st.column_config.TextColumn("Foto", width="small"),
                "Titel": st.column_config.TextColumn("Titel (Claude)", width="large"),
                "Autor": st.column_config.TextColumn("Autor (Claude)", width="medium"),
                "Verlag": st.column_config.TextColumn(width="medium"),
                "Jahr": st.column_config.TextColumn(width="small"),
                "Sicherheit": st.column_config.TextColumn("Sicherheit", width="small"),
                "Verifikation": st.column_config.TextColumn("Verifikation", width="small"),
                "Verifizierter Titel": st.column_config.TextColumn("Titel (verif.)", width="large"),
                "Verifizierter Autor": st.column_config.TextColumn("Autor (verif.)", width="medium"),
                "Verifiziertes Jahr": st.column_config.TextColumn("Jahr (verif.)", width="small"),
                "ISBN": st.column_config.TextColumn(width="small"),
                "Quelle": st.column_config.TextColumn(width="small"),
            },
        )
    else:
        st.info("Keine Einträge passen zu den gesetzten Filtern.")

    st.divider()

    # Foto-Vorschau mit erkannten Büchern
    st.subheader("Foto-Vorschau mit erkannten Büchern")

    fotos = sorted({e["Dateiname"] for e in filtered if e.get("Dateiname")})
    if not fotos:
        st.info("Keine Fotos zur Anzeige (aktive Filter ausblenden alle Einträge).")
        return

    max_fotos = st.slider(
        "Anzahl angezeigter Fotos", min_value=1, max_value=max(len(fotos), 1),
        value=min(12, len(fotos)),
    )

    cols = st.columns(3)
    for idx, foto_name in enumerate(fotos[:max_fotos]):
        col = cols[idx % 3]
        foto_path = FOTO_DIR / foto_name
        with col:
            if foto_path.exists():
                try:
                    img = Image.open(foto_path)
                    img.thumbnail((600, 600))
                    st.image(img, caption=foto_name, use_container_width=True)
                except Exception as exc:
                    st.error(f"Kann {foto_name} nicht öffnen: {exc}")
            else:
                st.warning(f"Datei nicht gefunden: {foto_path}")

            buecher_im_foto = [e for e in filtered if e.get("Dateiname") == foto_name]
            st.caption(f"{len(buecher_im_foto)} Bücher in diesem Filter")
            for b in buecher_im_foto:
                # Wenn verifiziert: bevorzugt die Datenbank-Werte anzeigen
                titel = b.get("Verifizierter Titel") or b.get("Titel") or "?"
                autor = b.get("Verifizierter Autor") or b.get("Autor") or ""
                jahr = b.get("Verifiziertes Jahr") or b.get("Jahr") or ""
                isbn = b.get("ISBN") or ""
                status = b.get("Verifikation", "")
                icon = {"found": "✓", "not_found": "✗", "error": "!", "unchecked": "·"}.get(status, "·")
                meta = []
                if autor:
                    meta.append(autor)
                if jahr:
                    meta.append(jahr)
                if isbn:
                    meta.append(f"ISBN {isbn}")
                meta_str = " · ".join(meta) if meta else ""
                if meta_str:
                    st.markdown(f"{icon} **{titel}** — {meta_str}")
                else:
                    st.markdown(f"{icon} **{titel}**")


if __name__ == "__main__":
    main()
