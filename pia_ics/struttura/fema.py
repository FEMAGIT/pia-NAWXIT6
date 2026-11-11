"""Regole di interpretazione dei dati del DB di produzione PIA_FEMA.

I log macchina (PIA_FEMA.dbo.Logs) sono testo libero, es.:
    "Start Ciclo Automatico ID_Ordine 2600028 (2359.96 x 75.00 mm)"
    "Start Movimentazione Sponda alla quota 60.00 mm"
    "Feedback Accelerometro Arco 0.11 °"
    "Ciclo Automatico ID Ordine 2600028 Terminato Durata 00:02:11"

`interpreta_log` replica le regole della vista PIA_FEMA.dbo.LOGS_TipoAttivita_4,
così i dati importati hanno la stessa forma usata finora dalla tracciabilità
(Sponda = asse X, Carro = asse Y, Arco = angolo alpha).
"""

import re
from dataclasses import dataclass
from typing import Optional

MOV_X = "Movimentazione x"
MOV_Y = "Movimentazione y"
MOV_ALPHA = "Movimentazione alpha"
STATO_LAMA = "Stato lama"
STATO_CICLO = "Stato ciclo Automatico"
AZIONE = "Azione"

TIPI_ATTIVITA = (MOV_X, MOV_Y, MOV_ALPHA, STATO_LAMA, STATO_CICLO, AZIONE)

PREFISSO_START_CICLO = "Start Ciclo Automatico"

_NUMERO = re.compile(r"^[-+]?\d+(?:\.\d+)?$")
_DIMENSIONI = re.compile(r"\(\s*([-+]?\d+(?:\.\d+)?)\s*x\s*([-+]?\d+(?:\.\d+)?)", re.IGNORECASE)
_ID_NOTE = re.compile(r"id\s*:\s*(\d+)", re.IGNORECASE)


@dataclass(frozen=True)
class LogInterpretato:
    tipo_attivita: str
    input: int
    output: int
    valore: float
    lunghezza: Optional[float]
    larghezza: Optional[float]
    unita_misura: str


def interpreta_log(descrizione: str) -> LogInterpretato:
    testo = (descrizione or "").strip()
    basso = testo.lower()

    if "carro" in basso:
        tipo = MOV_Y
    elif "sponda" in basso:
        tipo = MOV_X
    elif "arco" in basso:
        tipo = MOV_ALPHA
    elif "lama" in basso:
        tipo = STATO_LAMA
    elif "ciclo" in basso:
        tipo = STATO_CICLO
    else:
        tipo = AZIONE

    comando = (
        basso.startswith("start") or "lama" in basso or "ciclo" in basso
    ) and not basso.startswith("feedback")
    valore_input = 1 if comando else 0

    valore = None
    for parola in testo.split(" "):
        if _NUMERO.match(parola):
            valore = float(parola)
            break
    if valore is None:
        if basso.endswith(" attivo") or basso.startswith("accensione"):
            valore = 1.0
        elif basso.endswith(" disattivo") or basso.startswith("spegnimento"):
            valore = 0.0
        else:
            valore = -1.0

    lunghezza = larghezza = None
    dimensioni = _DIMENSIONI.search(testo)
    if dimensioni:
        lunghezza, larghezza = float(dimensioni.group(1)), float(dimensioni.group(2))

    if " mm" in basso:
        unita = "mm"
    elif "°" in testo:
        unita = "gradi"
    else:
        unita = ""

    return LogInterpretato(tipo, valore_input, 1 - valore_input, valore, lunghezza, larghezza, unita)


def id_record_da_note(note: Optional[str]) -> Optional[int]:
    """Estrae l'idRecord di V_COMMESSE_ESPLOSE dalla nota "id:xxx" di una riga ordine."""
    if not note:
        return None
    trovato = _ID_NOTE.search(note)
    return int(trovato.group(1)) if trovato else None


def formatta_misura(valore) -> str:
    """60.0 -> "60", 22.5 -> "22.5" (per comporre la dima "PRIMISxSECMIS")."""
    return f"{float(valore):g}"
