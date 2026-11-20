import hashlib
import secrets

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Amministratore'),
        ('client', 'Cliente'),
        ('maintenance_worker', 'Manutentore'),
    ]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='client')
    date_joined = models.DateTimeField(default=timezone.now, null=True)



class Cliente(models.Model):
    ragione_sociale = models.CharField(max_length=255)
    p_iva = models.CharField(max_length=11, unique=True)
    email = models.EmailField()
    cf = models.CharField(max_length=16, unique=True)
    sede_legale = models.CharField(max_length=255)
    n_telefono = models.CharField(max_length=15, null=True, blank=True)
    users = models.ManyToManyField(CustomUser, blank=True, related_name='clienti_associati')

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clienti"

    def __str__(self):
        return self.ragione_sociale


class ApiToken(models.Model):
    """Token di accesso alle API (`Authorization: Bearer <token>`).

    Il token in chiaro viene mostrato una sola volta alla creazione; nel database resta solo
    l'hash SHA-256."""

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='api_tokens')
    nome = models.CharField(max_length=100, help_text="Descrizione dell'integrazione che usa il token")
    prefisso = models.CharField(max_length=8, editable=False)
    key_hash = models.CharField(max_length=64, unique=True, editable=False)
    attivo = models.BooleanField(default=True)
    creato = models.DateTimeField(default=timezone.now, editable=False)
    scadenza = models.DateTimeField(null=True, blank=True)
    ultimo_uso = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        verbose_name = "Token API"
        verbose_name_plural = "Token API"

    def __str__(self):
        return f"{self.nome} ({self.prefisso}…)"

    @staticmethod
    def calcola_hash(chiave):
        return hashlib.sha256(chiave.encode('utf-8')).hexdigest()

    @classmethod
    def crea(cls, user, nome, scadenza=None):
        """Restituisce (token, chiave_in_chiaro)."""
        chiave = secrets.token_urlsafe(32)
        token = cls.objects.create(user=user, nome=nome, scadenza=scadenza, prefisso=chiave[:8],
                                   key_hash=cls.calcola_hash(chiave))
        return token, chiave

    @property
    def valido(self):
        return self.attivo and self.user.is_active and (self.scadenza is None or self.scadenza > timezone.now())

