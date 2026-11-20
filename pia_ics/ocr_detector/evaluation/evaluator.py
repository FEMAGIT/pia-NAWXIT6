"""Misura delle prestazioni rispetto a un testo di riferimento trascritto a mano."""
from __future__ import annotations

import re

from ocr_detector.pipeline.entities import ImageResult


class Evaluator:
    """Confronta il risultato del motore OCR con il testo atteso (ground truth).

    Formato del ground truth (JSON, una voce per foto, indicizzata per nome file):

        {
          "foto.jpg": {
            "text":   "testo dell'etichetta\\nriga per riga",
            "fields": ["testo 1", "testo 2", ...],
            "key":    "testo principale (opzionale)"
          }
        }

    Metriche, per foto e complessive:

    Tutte si basano sulla distanza di Levenshtein (numero minimo di caratteri
    da inserire, togliere o sostituire) e confrontano in maiuscolo e senza
    spazi. Servono SOLO a misurare: il testo letto non viene mai corretto.

    * CER (Character Error Rate): distanza fra tutto il testo letto e tutto
      il testo atteso, divisa per i caratteri attesi (0% = perfetto). È la
      metrica standard dell'OCR. Limite: penalizza anche il testo letto in
      ordine diverso o il testo in più (es. scritte fuori dall'etichetta).
    * Testi attesi (`fields`): le singole righe o parole attese. Per ognuno,
      la distanza dal tratto del testo letto che gli somiglia di più (0 =
      presente identico). Non dipende dall'ordine né dal testo in più. Si
      riportano i testi trovati identici e l'errore sui soli testi attesi
      (caratteri da correggere / caratteri attesi).
    * Testo principale (`key`): stessa misura, solo per il testo che
      identifica l'oggetto (es. 6205ZZC3).
    * Tempo di elaborazione per foto.
    """

    def evaluate(self, result: ImageResult, reference: dict) -> dict:
        """Metriche di una singola foto.

        Args:
            result: Risultato del motore OCR.
            reference: Voce del ground truth per questa foto.
        """
        all_text = " ".join(line for roi in result.rois for line in roi.lines)
        read, positions = self._normalize_with_positions(all_text)
        expected = self._normalize(reference["text"])

        fields = []
        for value in reference.get("fields", []):
            target = self._normalize(value)
            edits, start, end = self._best_match(target, read)
            fields.append({"expected": value, "read_as": self._original(all_text, positions, start, end),
                           "chars": len(target), "edits": edits, "found": edits == 0})
        key = reference.get("key")
        key_edits, key_match = None, None
        if key:
            key_edits, start, end = self._best_match(self._normalize(key), read)
            key_match = self._original(all_text, positions, start, end)

        return {
            "file": result.image.name,
            "error": result.error,
            "reference_chars": len(expected),
            "edits": self._edit_distance(read, expected),
            "fields_total": len(fields),
            "fields_found": sum(f["found"] for f in fields),
            "fields_chars": sum(f["chars"] for f in fields),
            "fields_edits": sum(f["edits"] for f in fields),
            "fields": fields,
            "key": key,
            "key_edits": key_edits,
            "key_read_as": key_match,
            "key_in_text": key_edits == 0 if key else None,
            "seconds": round(sum(result.timings.values()), 3),
            "text_expected": " ".join(reference["text"].split()),
            "text_read": all_text,
        }

    def summarize(self, rows: list[dict]) -> dict:
        """Metriche complessive (i CER sono calcolati sul totale dei caratteri)."""
        chars = sum(r["reference_chars"] for r in rows) or 1
        keys = [r for r in rows if r["key"]]
        seconds = sorted(r["seconds"] for r in rows)
        return {
            "images": len(rows),
            "errors": sum(1 for r in rows if r["error"]),
            "cer_pct": round(100 * sum(r["edits"] for r in rows) / chars, 2),
            "fields_found": sum(r["fields_found"] for r in rows),
            "fields_total": sum(r["fields_total"] for r in rows),
            "fields_cer_pct": round(100 * sum(r["fields_edits"] for r in rows)
                                    / (sum(r["fields_chars"] for r in rows) or 1), 2),
            "key_in_text": sum(bool(r["key_in_text"]) for r in keys),
            "key_cer_pct": round(100 * sum(r["key_edits"] for r in keys)
                                 / (sum(len(self._normalize(r["key"])) for r in keys) or 1), 2),
            "keys_total": len(keys),
            "mean_seconds": round(sum(seconds) / len(seconds), 2) if seconds else 0.0,
            "max_seconds": seconds[-1] if seconds else 0.0,
        }

    @staticmethod
    def _normalize(text: str) -> str:
        """Maiuscolo, senza spazi né a capo, "×" -> "X"."""
        return re.sub(r"\s+", "", text.upper().replace("×", "X"))

    @classmethod
    def _normalize_with_positions(cls, text: str) -> tuple[str, list[int]]:
        """Come `_normalize`, ma ricorda per ogni carattere la sua posizione nel
        testo originale (per mostrare il tratto letto così com'era)."""
        normalized, positions = [], []
        for index, char in enumerate(text):
            for piece in cls._normalize(char):
                normalized.append(piece)
                positions.append(index)
        return "".join(normalized), positions

    @staticmethod
    def _original(text: str, positions: list[int], start: int, end: int) -> str:
        """Tratto del testo originale corrispondente a [start, end) del testo normalizzato."""
        return text[positions[start]:positions[end - 1] + 1] if end > start else ""

    @staticmethod
    def _best_match(pattern: str, text: str) -> tuple[int, int, int]:
        """Tratto di `text` che somiglia di più a `pattern`: distanza di
        Levenshtein (0 = `pattern` compare identico in `text`), inizio e fine.

        È la normale distanza di Levenshtein, ma il tratto può iniziare e
        finire in qualsiasi punto di `text` (prima riga a zero, minimo
        sull'ultima riga). Per ogni cella si ricorda dove inizia il tratto.
        """
        previous, previous_start = [0] * (len(text) + 1), list(range(len(text) + 1))
        for i, char_p in enumerate(pattern, start=1):
            current, current_start = [i], [0]
            for j, char_t in enumerate(text, start=1):
                options = [(previous[j - 1] + (char_p != char_t), previous_start[j - 1]),   # sostituzione
                           (previous[j] + 1, previous_start[j]),                             # carattere mancante
                           (current[j - 1] + 1, current_start[j - 1])]                       # carattere in più
                cost, start = min(options, key=lambda option: option[0])
                current.append(cost)
                current_start.append(start)
            previous, previous_start = current, current_start
        end = min(range(len(previous)), key=lambda j: previous[j])
        return previous[end], previous_start[end], end

    @staticmethod
    def _edit_distance(a: str, b: str) -> int:
        """Distanza di modifica (inserimenti + cancellazioni + sostituzioni)."""
        previous = list(range(len(b) + 1))
        for i, char_a in enumerate(a, start=1):
            current = [i]
            for j, char_b in enumerate(b, start=1):
                current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (char_a != char_b)))
            previous = current
        return previous[-1]
