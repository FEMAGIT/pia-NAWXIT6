"""Salvataggio della valutazione in due file CSV, apribili con Excel.

Formato per Excel in italiano: separatore ";", virgola decimale, UTF-8 con BOM
(così le lettere accentate vengono lette correttamente).

    valutazione_<nome>.csv               una riga per foto, più la riga TOTALE
    valutazione_<nome>_testi.csv        una riga per ogni testo atteso
    confronto_preprocessing.csv          una riga per insieme e pre-elaborazione
"""
from __future__ import annotations

import csv
from pathlib import Path


def write_csv_reports(rows: list[dict], summary: dict, output_dir: Path, name: str) -> list[Path]:
    """Scrive i due CSV e restituisce i percorsi creati."""
    output_dir.mkdir(parents=True, exist_ok=True)
    photos_path = output_dir / f"valutazione_{name}.csv"
    fields_path = output_dir / f"valutazione_{name}_testi.csv"

    photos = [[
        "foto", "errore caratteri (CER) %", "testi trovati", "testi attesi",
        "errore sui testi %", "testo principale", "testo principale letto come",
        "caratteri sbagliati nel testo principale", "tempo s", "testo completo atteso", "testo completo letto",
        "errore di elaborazione",
    ]]
    for r in rows:
        photos.append([
            r["file"],
            _number(100 * r["edits"] / max(r["reference_chars"], 1)),
            r["fields_found"],
            r["fields_total"],
            _number(100 * r["fields_edits"] / max(r["fields_chars"], 1)),
            r["key"] or "",
            r["key_read_as"] or "",
            "" if r["key_edits"] is None else r["key_edits"],
            _number(r["seconds"]),
            r["text_expected"],
            r["text_read"],
            r["error"] or "",
        ])
    photos.append([
        f"TOTALE ({summary['images']} foto)",
        _number(summary["cer_pct"]),
        summary["fields_found"],
        summary["fields_total"],
        _number(summary["fields_cer_pct"]),
        f"{summary['key_in_text']} / {summary['keys_total']} letti senza errori",
        "",
        "",
        _number(summary["mean_seconds"]) + " (media)",
        "", "",
        f"{summary['errors']} errori" if summary["errors"] else "",
    ])

    fields = [["foto", "testo atteso", "letto come", "caratteri sbagliati", "esito"]]
    for r in rows:
        for f in r["fields"]:
            fields.append([r["file"], f["expected"], f["read_as"], f["edits"],
                           "OK" if f["found"] else "ERRATO"])

    _write(photos_path, photos)
    _write(fields_path, fields)
    return [photos_path, fields_path]


def write_comparison_csv(comparison: list[dict], output_dir: Path) -> Path:
    """confronto_preprocessing.csv: una riga per insieme e pre-elaborazione."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "confronto_preprocessing.csv"
    table = [["insieme", "pre-elaborazione", "foto", "errore caratteri (CER) %",
              "errore sui testi %", "testi letti senza errori", "testi attesi",
              "testi principali letti senza errori", "testi principali", "tempo medio s", "tempo massimo s",
              "errori di elaborazione"]]
    for c in sorted(comparison, key=lambda c: c["dataset"]):
        table.append([c["dataset"], c["preprocessing"], c["images"], _number(c["cer_pct"]),
                      _number(c["fields_cer_pct"]), c["fields_found"], c["fields_total"],
                      c["key_in_text"], c["keys_total"], _number(c["mean_seconds"]),
                      _number(c["max_seconds"]), c["errors"]])
    _write(path, table)
    return path


def _number(value: float) -> str:
    """Numero con una cifra decimale e la virgola (es. 9,5)."""
    return f"{value:.1f}".replace(".", ",")


def _write(path: Path, table: list[list]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        csv.writer(handle, delimiter=";").writerows(table)
