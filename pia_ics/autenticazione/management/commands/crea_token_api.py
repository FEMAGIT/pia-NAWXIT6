from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from autenticazione.models import ApiToken


class Command(BaseCommand):
    help = "Crea un token per le API per l'utente indicato (email). Il token viene mostrato una sola volta."

    def add_arguments(self, parser):
        parser.add_argument('email', help="Email dell'utente a cui associare il token")
        parser.add_argument('--nome', default='Integrazione API', help="Descrizione del token")
        parser.add_argument('--giorni', type=int, default=None, help="Validità in giorni (default: nessuna scadenza)")

    def handle(self, *args, email, nome, giorni, **options):
        try:
            user = get_user_model().objects.get(email=email)
        except get_user_model().DoesNotExist:
            raise CommandError(f"Nessun utente con email {email}.")
        scadenza = timezone.now() + timedelta(days=giorni) if giorni else None
        token, chiave = ApiToken.crea(user, nome, scadenza)
        self.stdout.write(f"Token creato per {user.email} ({token.nome}). Copiarlo ora, non sarà più visibile:\n")
        self.stdout.write(chiave)
