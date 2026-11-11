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










