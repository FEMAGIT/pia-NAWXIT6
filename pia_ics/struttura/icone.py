"""Sagome (icone) delle commesse: una delle Sagoma_*.png scelta a caso, uguale per tutte le righe
con lo stesso codicecommessa.

Le immagini sono versionate in struttura/sagome/ e vengono copiate in media/icon/, da cui il campo
icona le serve: così sono presenti su qualsiasi server dopo il pull. L'assegnazione viene eseguita
in automatico alla fine di importa_fema e si può lanciare a mano con il comando assegna_sagome.
"""
import random
import shutil
from collections import defaultdict
from pathlib import Path

from django.conf import settings
from django.db import transaction

from struttura.models import Commessa

CARTELLA = "icon"
MODELLO_FILE = "Sagoma_*.png"
SORGENTE_PREDEFINITA = Path(__file__).resolve().parent / "sagome"


def copia_sagome(sorgente=SORGENTE_PREDEFINITA):
    """Copia le sagome in media/icon/ e restituisce i loro nomi come valori del campo icona."""
    file = sorted(Path(sorgente).glob(MODELLO_FILE))
    if not file:
        raise FileNotFoundError(f"Nessun file {MODELLO_FILE} in {sorgente}.")
    destinazione = Path(settings.MEDIA_ROOT) / CARTELLA
    destinazione.mkdir(parents=True, exist_ok=True)
    for percorso in file:
        shutil.copy2(percorso, destinazione / percorso.name)
    return [f"{CARTELLA}/{p.name}" for p in file]


def calcola_assegnazioni(sagome, tutte=False, seed=None):
    """{codicecommessa: (sagoma, righe)} e la lista delle righe il cui campo icona va aggiornato.

    Senza tutte, una commessa che ha già una delle sagome la mantiene (e la estende alle righe nuove).
    """
    caso = random.Random(seed)
    righe = defaultdict(list)
    for commessa in Commessa.objects.order_by("codicecommessa", "id"):
        righe[commessa.codicecommessa].append(commessa)

    assegnazioni, da_salvare = {}, []
    for codice, commesse in righe.items():
        esistenti = [] if tutte else [c.icona.name for c in commesse if c.icona.name in sagome]
        sagoma = esistenti[0] if esistenti else caso.choice(sagome)
        for commessa in commesse:
            if commessa.icona.name != sagoma:
                commessa.icona.name = sagoma
                da_salvare.append(commessa)
        assegnazioni[codice] = (sagoma, len(commesse))
    return assegnazioni, da_salvare


def assegna_sagome(sorgente=SORGENTE_PREDEFINITA, tutte=False, seed=None):
    """Copia le sagome e le assegna alle commesse; restituisce (assegnazioni, righe aggiornate)."""
    sagome = copia_sagome(sorgente)
    assegnazioni, da_salvare = calcola_assegnazioni(sagome, tutte, seed)
    with transaction.atomic():
        Commessa.objects.bulk_update(da_salvare, ["icona"])
    return assegnazioni, len(da_salvare)
