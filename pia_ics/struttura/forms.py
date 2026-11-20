from datetime import datetime

from django import forms
from .models import Macchina, Documento, TipoMacchina, Assistenza, Chat, Classificazione, Manutenzione, TipoManutenzione, FASCE_ORARIE_ASSISTENZA
from autenticazione.models import Cliente


class CustomCliente(forms.ModelChoiceField):
    def label_from_instance(self, cliente):
        return "%s" % cliente.ragione_sociale

class CustomTipoMacchina(forms.ModelChoiceField):
    def label_from_instance(self, tipo_macchina):
        return "%s" % tipo_macchina.tipomacchina

class MacchinaForm(forms.ModelForm):
    identificativo = forms.CharField(widget=forms.TextInput, label='ID')
    descrmacchina = forms.CharField(widget=forms.TextInput, label='Titolo')
    tipo_macchina = CustomTipoMacchina(widget=forms.Select, queryset=TipoMacchina.objects.all(),
                                               label='Tipo')
    cliente = CustomCliente(widget=forms.Select, queryset=Cliente.objects.all(),
                                               label='Cliente')
    desctipomacchina = forms.CharField(widget=forms.TextInput, label='Descrizione')

    class Meta:
        model = Macchina
        fields = ['tipo_macchina', 'desctipomacchina', 'identificativo', 'descrmacchina', 'cliente']

    def __init__(self, *args, **kwargs):
        super(MacchinaForm, self).__init__(*args, **kwargs)
        for f in self.fields:
            self.fields[f].widget.attrs.update({'class': 'form-control'})


class DocumentoForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ['nome_documento', 'path_documento', 'tipo_macchina']


class AssistenzaForm(forms.ModelForm):
    # personalizzato come macchina_form
    titolo = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Inserisci il titolo qui',
            'class': 'form-control width-custom-desc',
            'maxlength': 100
        }),
        label='Titolo',
        max_length=50,
        required=True
    )

    macchine = forms.ModelChoiceField(
        queryset=Macchina.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control width-custom-desc',
            'placeholder': 'Inserisci il nome della macchina',
            'maxlength': 100
        }),
        label='Macchine',
        required=True,
        empty_label="---Seleziona macchina---",
    )

    data = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control width-custom-desc'}),
        label='Data',
    )

    descassistenza = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'cols': 40,
            'placeholder': 'Inserisci la descrizione qui',
            'class': 'form-control width-custom-desc'
        }),
        label='Descrizione',
    )

    ora_inizio = forms.TypedChoiceField(
        choices=[('', '---Seleziona fascia---')] + [(t.strftime('%H:%M'), label) for t, label in FASCE_ORARIE_ASSISTENZA],
        coerce=lambda v: datetime.strptime(v, '%H:%M').time(),
        empty_value=None,
        widget=forms.Select(attrs={'class': 'form-control width-custom-desc'}),
        label='Fascia oraria',
        required=False,
    )

    class Meta:
        model = Assistenza
        fields = ['titolo', 'descassistenza', 'macchine', 'data', 'ora_inizio']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        user_role = kwargs.pop('user_role', None)
        super().__init__(*args, **kwargs)

        # Fascia obbligatoria per le nuove assistenze; facoltativa in modifica (assistenze storiche senza fascia)
        self.fields['ora_inizio'].required = self.instance.pk is None
        if self.instance.pk and self.instance.ora_inizio:
            self.initial['ora_inizio'] = self.instance.ora_inizio.strftime('%H:%M')

        if user_role == 'client':
            # Filtra le macchine per i clienti associati all'utente
            clienti_associati = user.clienti_associati.all()
            self.fields['macchine'].queryset = Macchina.objects.filter(cliente__in=clienti_associati)
        else:
            # Per admin o altri ruoli, mostra tutte le macchine
            self.fields['macchine'].queryset = Macchina.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        data = cleaned_data.get('data')
        ora = cleaned_data.get('ora_inizio')

        if data and ora:
            nuova = self.instance.pk is None
            if nuova and datetime.combine(data, ora) <= datetime.now():
                self.add_error('ora_inizio', "Non è possibile prenotare una fascia oraria passata.")
            elif Assistenza.objects.filter(data=data, ora_inizio=ora).exclude(pk=self.instance.pk).exists():
                etichetta = dict(FASCE_ORARIE_ASSISTENZA).get(ora, ora.strftime('%H:%M'))
                self.add_error('ora_inizio',
                               f"La fascia {etichetta} del {data.strftime('%d/%m/%Y')} è già occupata.")
        return cleaned_data


class ChatForm(forms.ModelForm):
    class Meta:
        model = Chat
        fields = ['messaggio', 'preventivo']


class ClassificazioneForm(forms.ModelForm):

    manutenzione = forms.ModelChoiceField(
        queryset=Manutenzione.objects.all(),
        label="Componente Manutenzione",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control custom-select'})
    )

    tipo_manutenzione = forms.ModelChoiceField(
        queryset=TipoManutenzione.objects.all(),
        label="Tipologia Manutenzione",
        required=False,
        empty_label="Seleziona tipo di manutenzione",
        widget=forms.Select(attrs={'class': 'form-control custom-select'})
    )

    class Meta:
        model = Classificazione
        fields = ['manutenzione', 'tipo_manutenzione']



