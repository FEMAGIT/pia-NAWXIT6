"""Assegna a caso una sagoma a ogni commessa (stessa sagoma per lo stesso codicecommessa).

Viene già eseguito in automatico alla fine di importa_fema; a mano serve per rimescolare o provare:

    python manage.py assegna_sagome --dry-run   # mostra senza salvare
    python manage.py assegna_sagome --tutte     # rimescola tutte le commesse
"""
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from struttura.icone import MODELLO_FILE, SORGENTE_PREDEFINITA, CARTELLA, assegna_sagome, calcola_assegnazioni


class Command(BaseCommand):
    help = "Assegna a caso una delle sagome a ogni commessa (stessa sagoma per lo stesso codicecommessa)."

    def add_arguments(self, parser):
        parser.add_argument("--sorgente", default=str(SORGENTE_PREDEFINITA),
                            help="Cartella dei file Sagoma_*.png (predefinita: struttura/sagome).")
        parser.add_argument("--tutte", action="store_true",
                            help="Riassegna le sagome a tutte le commesse, anche a quelle che ne hanno già una.")
        parser.add_argument("--seed", type=int, help="Seme del generatore casuale (assegnazione ripetibile).")
        parser.add_argument("--dry-run", action="store_true", help="Mostra le assegnazioni senza salvarle.")

    def handle(self, *args, **opzioni):
        if opzioni["dry_run"]:
            sagome = [f"{CARTELLA}/{p.name}" for p in sorted(Path(opzioni["sorgente"]).glob(MODELLO_FILE))]
            if not sagome:
                raise CommandError(f"Nessun file {MODELLO_FILE} in {opzioni['sorgente']}.")
            assegnazioni, da_salvare = calcola_assegnazioni(sagome, opzioni["tutte"], opzioni["seed"])
            aggiornate = len(da_salvare)
        else:
            try:
                assegnazioni, aggiornate = assegna_sagome(opzioni["sorgente"], opzioni["tutte"], opzioni["seed"])
            except FileNotFoundError as exc:
                raise CommandError(str(exc)) from exc

        for codice, (sagoma, righe) in assegnazioni.items():
            self.stdout.write(f"{codice}: {sagoma} ({righe} righe)")
        if opzioni["dry_run"]:
            self.stdout.write(self.style.WARNING(f"Dry run: {aggiornate} righe da aggiornare, nulla salvato."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Aggiornate {aggiornate} righe di {len(assegnazioni)} commesse."))
