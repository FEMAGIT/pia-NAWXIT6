from datetime import time

from django.db import models
from django.utils import timezone
from autenticazione.models import Cliente

# Fasce orarie prenotabili per un'assistenza (1 ora ciascuna, una prenotazione per fascia)
FASCE_ORARIE_ASSISTENZA = [
    (time(9, 0), '09:00 – 10:00'),
    (time(10, 0), '10:00 – 11:00'),
    (time(11, 0), '11:00 – 12:00'),
    (time(15, 0), '15:00 – 16:00'),
    (time(16, 0), '16:00 – 17:00'),
    (time(17, 0), '17:00 – 18:00'),
]


class Articolo(models.Model):
    tipo = models.CharField(max_length=6)
    codice = models.CharField(max_length=510)
    altezza = models.DecimalField(max_digits=13, decimal_places=2)
    larghezza = models.DecimalField(max_digits=13, decimal_places=2)
    spessore = models.DecimalField(max_digits=13, decimal_places=2)
    peso = models.DecimalField(max_digits=13, decimal_places=2)
    data_creazione = models.DateTimeField()
    # Id del blocco in PIA_FEMA.wms.ARTICOLI (valorizzato dal comando importa_fema)
    id_esterno = models.IntegerField(null=True, blank=True, unique=True)

    def __str__(self):
        return self.codice

    class Meta:
        verbose_name = "Articolo"
        verbose_name_plural = "Articoli"

class Ordine(models.Model):
    descordine = models.CharField(max_length=510)
    dataconsegna = models.DateField()
    materiale = models.CharField(max_length=510)
    articoli = models.ManyToManyField(Articolo, through='OrdiniBlocco')
    id_ordine_esterno = models.CharField (max_length=50, null=True, blank=True, default=None)
    # Inizio/fine lavorazione da PIA_FEMA.dbo.Ordini: delimitano i log quando lo start ciclo non riporta l'ID ordine
    data_inizio = models.DateTimeField(null=True, blank=True)
    data_fine = models.DateTimeField(null=True, blank=True)


    def __str__(self):
        return self.descordine


    class Meta:
        verbose_name = "Ordine"
        verbose_name_plural = "Ordini"


class Commessa(models.Model):
    ordine = models.ForeignKey(Ordine, on_delete=models.CASCADE)
    id_macchina = models.CharField(max_length=255)
    codicecommessa = models.CharField(max_length=255)
    descrizione = models.CharField(max_length=255)
    id_record = models.CharField(max_length=50)
    cliente = models.CharField(max_length=250)
    modello = models.TextField(null=True, blank=True, default=None)
    componente = models.TextField(null=True, blank=True, default=None)
    desccomponente = models.TextField(null=True, blank=True, default=None)
    dima = models.CharField (verbose_name="Dima (mmXmm)", max_length=50, null=True, blank=True, default=None)
    profondità = models.FloatField (verbose_name="Profondità (mm)",null=True, blank=True, default=None)
    qtalav = models.IntegerField(null=True, blank=True, default=None)
    qta = models.IntegerField(null=True, blank=True, default=None)
    icona = models.FileField(upload_to='icon/', null=True)


    def __str__(self):
        return self.codicecommessa


    class Meta:
        verbose_name = "Commessa"
        verbose_name_plural = "Commesse"


class Macchina(models.Model):
    tipo_macchina = models.ForeignKey('TipoMacchina', on_delete=models.CASCADE)
    desctipomacchina = models.CharField(max_length=50)
    identificativo = models.CharField(max_length=255)
    descrmacchina = models.CharField(max_length=255)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)

    def __str__(self):
        return self.identificativo

    class Meta:
        verbose_name = "Macchina"
        verbose_name_plural = "Macchine"



class Assistenza(models.Model):
    STATUS_CHOICES = [
        ('aperto', 'Aperto'),
        ('in_elaborazione', 'In Elaborazione'),
        ('sospeso', 'Sospeso'),
        ('accettazione', 'Accettazione'),
        ('accettato', 'Accettato'),
        ('chiuso', 'Chiuso'),
        ('chiuso_positivamente', 'Chiuso Positivamente'),
        ('chiuso_negativamente', 'Chiuso Negativamente'),
    ]

    titolo = models.CharField(max_length=250)
    descassistenza = models.TextField()
    data = models.DateField(null = True, blank = True)
    ora_inizio = models.TimeField(verbose_name="Fascia oraria", choices=FASCE_ORARIE_ASSISTENZA, null=True, blank=True)
    macchine = models.ForeignKey(Macchina, on_delete = models.CASCADE)
    classificazioni = models.ManyToManyField('Manutenzione', through='Classificazione', related_name='assistenza')
    stato = models.CharField(max_length=50, choices=STATUS_CHOICES, null=True, blank=True, default=None)


    def __str__(self):
        return self.titolo

    class Meta:
        verbose_name = "Assistenza"
        verbose_name_plural = "Assistenze"
        constraints = [
            # Una sola assistenza per fascia oraria (le assistenze senza fascia, NULL, non sono vincolate)
            models.UniqueConstraint(fields=['data', 'ora_inizio'], name='assistenza_fascia_unica'),
        ]

class Lavorazione(models.Model):
    macchina = models.ForeignKey(Macchina, on_delete=models.CASCADE)
    commessa = models.ForeignKey(Commessa, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    # ID di PIA_FEMA.dbo.LavorazioneOrdine (valorizzato dal comando importa_fema)
    id_esterno = models.BigIntegerField(null=True, blank=True, unique=True)


    def __str__(self):
        return f"Lavorazione {self.commessa} su {self.macchina}"

    class Meta:
        verbose_name = "Lavorazione"
        verbose_name_plural = "Lavorazioni"

class TipoMacchina(models.Model):
    tipomacchina = models.CharField(max_length=150)
    desctipomacchina = models.CharField(max_length=50)
    manutenzioni = models.ManyToManyField('TipoManutenzione', through='Manutenzione', related_name='tipomacchine')

    def __str__(self):
        return self.desctipomacchina

    class Meta:
        verbose_name = "TipoMacchina"
        verbose_name_plural = "TipoMacchine"


class TipoManutenzione(models.Model):
    tipomanutenzione = models.CharField(max_length=14, primary_key=True)
    settore = models.CharField(max_length=50)

    def __str__(self):
        return self.tipomanutenzione

    class Meta:
        verbose_name = "TipoManutenzione"
        verbose_name_plural = "TipoManutenzioni"


class Manutenzione(models.Model):
    componente = models.CharField(max_length=50)
    descrizionecomponente = models.CharField(max_length=150)
    link = models.URLField(max_length=2000, blank=True)
    tipo_manutenzione = models.ForeignKey(TipoManutenzione, on_delete=models.CASCADE)
    tipo_macchina = models.ForeignKey(TipoMacchina, on_delete=models.CASCADE)

    def __str__(self):
        return self.componente

    class Meta:
        verbose_name = "Manutenzione"
        verbose_name_plural = "Manutenzioni"

class Classificazione (models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    validate = models.BooleanField(blank= True, default = False)
    assistenza = models.ForeignKey(Assistenza, on_delete = models.CASCADE)
    manutenzione = models.ForeignKey(Manutenzione, on_delete = models.CASCADE)

    class Meta:
        verbose_name = "Classificazione"
        verbose_name_plural = "Classificazioni"

class OrdiniBlocco(models.Model):
    articolo = models.ForeignKey(Articolo, on_delete=models.CASCADE)
    ordine = models.ForeignKey(Ordine, on_delete=models.CASCADE)

    def __str__(self):
        return f"Ordine {self.ordine} - Articolo {self.articolo}"

    class Meta:
        verbose_name = "OrdiniBlocco"
        verbose_name_plural = "OrdiniBlocchi"


class Documento(models.Model):
    nome_documento = models.CharField(max_length=255)
    path_documento = models.FileField(upload_to='documenti/', null=True, blank=True)
    tipo_macchina = models.ForeignKey(TipoMacchina, on_delete=models.CASCADE, related_name='documenti')

    def __str__(self):
        return self.nome_documento

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documenti"

class Chat (models.Model):
    messaggio = models.TextField()
    assistenze = models.ForeignKey(Assistenza, on_delete=models.CASCADE, related_name='assistenze')
    utentecorrente = models.CharField (max_length=100, null=True, blank=True)
    datacorrente = models.DateTimeField (null=True, blank=True)
    preventivo = models.FileField (null=True, blank=True)
    is_staff = models.BooleanField (null=True, blank=True)

    class Meta:
        verbose_name = "Chat"
        verbose_name_plural = "Chats"

class SerialeArticolo(models.Model):
    codice_interno = models.CharField(null=True, blank=True, max_length=50)
    nome_fornitore = models.CharField(null=True, blank=True, max_length=100)
    codice_articolo_fornitore = models.CharField(null=True, blank=True, max_length=50)
    descrizione_articolo_fornitore = models.CharField(null=True, blank=True, max_length=250)
    manutenzione = models.ForeignKey(Manutenzione, on_delete=models.CASCADE, related_name='seriali')

    def __str__(self):
        return self.codice_interno

    class Meta:
        verbose_name = "Seriale Articolo"
        verbose_name_plural = "Seriali Articolo"


class Attività(models.Model):
    tipo_attività = models.CharField(null=True, blank=True, max_length=100)
    macchine = models.ManyToManyField(Macchina, through='Log')

    def __str__(self):
        return self.tipo_attività

    class Meta:
        verbose_name = "Attività"
        verbose_name_plural = "Attività"


class Log(models.Model):
    macchine = models.ForeignKey(Macchina, on_delete=models.CASCADE)
    attività = models.ForeignKey(Attività, on_delete=models.CASCADE)
    # Non auto_now_add: in import deve essere conservato l'orario reale della macchina (Logs.DataLogs)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    # ID di PIA_FEMA.dbo.Logs (valorizzato dal comando importa_fema)
    id_esterno = models.BigIntegerField(null=True, blank=True, unique=True)
    descrizione = models.CharField(null=True, blank=True, max_length=250)
    input = models.IntegerField(null=True, blank=True)
    output = models.IntegerField(null=True, blank=True)
    valore = models.FloatField(null=True, blank=True)
    lunghezza = models.FloatField(null=True, blank=True, default=None)
    larghezza = models.FloatField(null=True, blank=True, default=None)
    unita_misura = models.CharField(null=True, blank=True, max_length=5)

    def __str__(self):
        return f"macchine {self.macchine} - attività {self.attività}"

    class Meta:
        verbose_name = "Log"
        verbose_name_plural = "Logs"


class QualitàAngoloAutomatico (models.Model):
    soglia_ottimo = models.FloatField (null=True, blank=True)
    soglia_rettifica = models.FloatField (null=True, blank=True)

    def __str__(self):
        return  f" {self.soglia_ottimo} + {self.soglia_rettifica}"

    class Meta:
        verbose_name = "QualitàAngoloAutomatico"
        verbose_name_plural = "QualitàAngoloAutomatico"

class QualitàTaglio (models.Model):
    soglia_accettabile = models.FloatField (null=True, blank=True)

    def __str__(self):
        return f" {self.soglia_accettabile}"

    class Meta:
        verbose_name = "QualitàTaglio"
        verbose_name_plural = "QualitàTaglio"


