from io import BytesIO
import qrcode
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404,redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, UpdateView, DeleteView, TemplateView
from .models import Macchina, Manutenzione, Assistenza, Chat, Classificazione, TipoManutenzione, SerialeArticolo, FASCE_ORARIE_ASSISTENZA
from .forms import  AssistenzaForm, ClassificazioneForm
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from .forms import MacchinaForm
from collections import defaultdict
from datetime import timedelta
from django.utils import timezone
from django.views import View
from django.core.files.storage import default_storage
from google.cloud import vision
from google.oauth2 import service_account
from django.conf import settings
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)


class MacchinaHomePageView(LoginRequiredMixin, TemplateView):
    template_name = 'homepage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['macchine'] = Macchina.objects.all()
        return context

class MacchinaCreateView(LoginRequiredMixin, CreateView):
    model = Macchina
    form_class = MacchinaForm
    template_name = 'macchina_form.html'
    success_url = reverse_lazy('struttura:macchina_homepage')

class MacchinaUpdateView(LoginRequiredMixin, UpdateView):
    model = Macchina
    form_class = MacchinaForm
    template_name = 'macchina_form.html'
    success_url = reverse_lazy('struttura:macchina_homepage')

class AssistenzaClassificazioneView(LoginRequiredMixin, UpdateView):
    model = Assistenza
    form_class = AssistenzaForm
    template_name = 'Assistenza_Classificazione.html'
    success_url = reverse_lazy('struttura:assistenza')

class MacchinaDeleteView(LoginRequiredMixin, DeleteView):
    model = Macchina
    template_name = 'macchina_confirm_delete.html'
    success_url = reverse_lazy('struttura:macchina_homepage')

    def post(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
            obj.delete()
            return JsonResponse({"response": "Macchina eliminata con successo."}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


class DocumentoTemplateView(TemplateView):
    template_name = 'documento_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipo_macchina_id'] = self.kwargs['tipo_macchina_id']
        return context


class ManutenzioneView(LoginRequiredMixin, TemplateView):
    template_name = 'manutenzione_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        macchina_id = self.kwargs['macchina_id']
        macchina = get_object_or_404(Macchina, pk=macchina_id)
        tipo_macchina_id = macchina.tipo_macchina.id
        context['tipo_macchina_id'] = tipo_macchina_id
        return context

@login_required(login_url='/autenticazione/login/')
def generate_pdf_qr_code(request, id):
    # Recupera l'oggetto usando l'ID passato
    obj = get_object_or_404(Macchina, id=id)
    # Genera il contenuto del QR code
    qr_content = f"ID: {obj.id}"
    # Crea il QR code e salvalo in memoria
    qr_image = qrcode.make(qr_content)
    qr_buffer = BytesIO()
    qr_image.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)  # Sposta il puntatore all'inizio del buffer
    # Usa ImageReader per rendere compatibile l'immagine con ReportLab
    qr_image_reader = ImageReader(qr_buffer)
    # Crea la risposta PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="qr_code_{id}.pdf"'
    # Crea il PDF con ReportLab
    p = canvas.Canvas(response, pagesize=letter)
    p.drawString(100, 750, f"QR Code per ID: {obj.id}")
    # Aggiungi il QR code al PDF usando ImageReader
    p.drawImage(qr_image_reader, 100, 600, width=200, height=200)  # Adatta le dimensioni come necessario
    p.showPage()
    p.save()

    return response

class AssistenzaHomePageView(LoginRequiredMixin, TemplateView):
    template_name = 'Assistenza.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assistenze = Assistenza.objects.all()
        context['assistenze'] = assistenze
        return context


class AssistenzaDeleteView(LoginRequiredMixin, DeleteView):
    model = Assistenza
    template_name = 'Assistenza_confirm_delete.html'
    success_url = reverse_lazy('struttura:assistenza_homepage')

    def post(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
            obj.delete()
            return JsonResponse({"response": "Assistenza eliminata con successo."}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

class ClassificazioneDeleteView(LoginRequiredMixin, DeleteView):
    model = Classificazione
    template_name = 'Classificazione_confirm_delete.html'
    success_url = reverse_lazy('struttura:assistenza_homepage')

    def post(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
            obj.delete()
            return JsonResponse({"response": "Classificazione eliminata con successo."}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


class AssistenzaCreateView(LoginRequiredMixin, CreateView):
    model = Assistenza
    form_class = AssistenzaForm
    template_name = 'Assistenza_form.html'
    success_url = reverse_lazy('struttura:assistenza_homepage')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user = self.request.user

        if user.is_superuser:
            kwargs['user_role'] = 'admin'
        elif hasattr(user, 'role') and user.role == 'client':
            kwargs['user_role'] = 'client'

        kwargs['user'] = user
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.stato = 'aperto'
        self.object.save()
        form.save_m2m()
        return HttpResponseRedirect(self.get_success_url())


class ChatView(LoginRequiredMixin, TemplateView):
    template_name = 'Chat.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assistenza_id = self.kwargs.get('assistenza_id')
        assistenza = get_object_or_404(Assistenza, pk=assistenza_id)
        context['assistenza'] = assistenza
        return context

@require_POST
@login_required(login_url='/autenticazione/login/')
def chat_add_message(request, assistenza_id):
    assistenza = get_object_or_404(Assistenza, id=assistenza_id)
    message_content = request.POST.get('messaggio')
    allegato = request.FILES.get('allegato')

    if message_content or allegato:
        ultimo_messaggio = assistenza.assistenze.order_by('-datacorrente').first()
        due_giorni_fa = timezone.now() - timedelta(days=2)
        allegati_recenti = assistenza.assistenze.filter(
            preventivo__isnull=False,
            datacorrente__gte=due_giorni_fa
        )
        if allegati_recenti.exists():
            assistenza.stato = 'accettazione'
            assistenza.save()

        elif ultimo_messaggio and timezone.now() > ultimo_messaggio.datacorrente + timedelta(days=2):
            assistenza.stato = 'sospeso'
            assistenza.save()

        elif assistenza.stato == 'aperto' and not assistenza.assistenze.exists():
            assistenza.stato = 'in_elaborazione'
            assistenza.save()

        if request.user.is_staff:
            isstaff = True;
        else:
            isstaff = False;

        Chat.objects.create(
            messaggio=message_content,
            assistenze=assistenza,
            utentecorrente=request.user,
            datacorrente=timezone.now(),
            preventivo=allegato,
            is_staff = isstaff,
        )

    return redirect('struttura:chatview', assistenza_id=assistenza.id)

class OpenControlRoom(LoginRequiredMixin, TemplateView):
    template_name = 'Controlroom.html'

class QRcodefilter(LoginRequiredMixin, TemplateView):
        template_name = 'QRcodefilter.html'

class QRcodemacchina(LoginRequiredMixin, TemplateView):
        template_name = 'QRcodemacchina.html'

@login_required(login_url='/autenticazione/login/')
def get_macchina_identificativo(request, pk):
    try:
        macchina = Macchina.objects.get(pk=pk)
        return JsonResponse({'identificativo': macchina.identificativo})
    except Macchina.DoesNotExist:
        return JsonResponse({'error': 'Macchina non trovata'}, status=404)

@login_required(login_url='/autenticazione/login/')
def ClassificazioneCreateView(request, assistenza_id):
    assistenza = get_object_or_404(Assistenza, pk=assistenza_id)

    is_assistenza_chiusa = assistenza.stato in ["chiuso","accettazione","chiuso_positivamente","chiuso_negativamente"]

    if request.method == 'POST' and not is_assistenza_chiusa:
        form = ClassificazioneForm(request.POST)
        if form.is_valid():
            classificazione = form.save(commit=False)
            classificazione.assistenza = assistenza
            classificazione.manutenzione = form.cleaned_data['manutenzione']
            classificazione.tipo_manutenzione = form.cleaned_data['tipo_manutenzione']
            classificazione.save()
            success_url = reverse_lazy('struttura:assistenza_classificazione', args=[assistenza.pk])
            return redirect(success_url)
        else:
            print("Errori nel form:", form.errors)
    else:
        form = ClassificazioneForm()

    return render(request, 'Assistenza_classificazione.html', {
        'form': form,
        'assistenza': assistenza,
        'is_assistenza_chiusa': is_assistenza_chiusa,
    })

@login_required(login_url='/autenticazione/login/')
def AssistenzaUpdateView(request, assistenza_id):
    assistenza = get_object_or_404(Assistenza, pk=assistenza_id)
    print("Dati assistenza esistenti:", assistenza)

    if request.method == 'POST':
        form = AssistenzaForm(request.POST, instance=assistenza)
        if form.is_valid():
            form.save()
            return redirect(reverse_lazy('struttura:assistenza_homepage'))
        else:
            print("Errori nel form:", form.errors)
    else:
        form = AssistenzaForm(instance=assistenza)
        print("Dati nel form:", form.initial)

    return render(request, 'Assistenza_form_update.html', {'form': form, 'assistenza': assistenza})

@login_required(login_url='/autenticazione/login/')
def ClassificazioneUpdateView(request, pk):
    classificazione = get_object_or_404(Classificazione, pk=pk)
    print("Dati assistenza esistenti:", classificazione)

    if request.method == 'POST':
        form = ClassificazioneForm(request.POST, instance=classificazione)
        if form.is_valid():
            form.save()
            return redirect(reverse_lazy('struttura:assistenza_homepage'))
        else:
            print("Errori nel form:", form.errors)
    else:
        form = ClassificazioneForm(instance=classificazione)
        print("Dati nel form:", form.initial)

    return render(request, 'Classificazione_form_update.html', {'form': form, 'classificazione': classificazione})

@login_required(login_url='/autenticazione/login/')
def get_manutenzioni(request, value):
    print(f"TipoManutenzione ID: {value}")

    try:
        tipo_manutenzione = get_object_or_404(TipoManutenzione, tipomanutenzione=value)
        manutenzioni = Manutenzione.objects.filter(tipo_manutenzione=tipo_manutenzione)
        if manutenzioni.exists():
            manutenzioni_data = [{"id": m.id, "componente": m.componente} for m in manutenzioni]
        else:
            manutenzioni_data = []
        return JsonResponse({"manutenzioni": manutenzioni_data})

    except TipoManutenzione.DoesNotExist:
        return JsonResponse({"error": "TipoManutenzione not found"}, status=404)

@login_required(login_url='/autenticazione/login/')
def Calendar(request):
    # Restituisce solo quali fasce orarie sono occupate per ogni giorno: titoli e descrizioni
    # delle assistenze non vengono esposti (il calendario è visibile anche ai clienti).
    occupati_per_giorno = defaultdict(list)
    prenotazioni = Assistenza.objects.filter(data__isnull=False, ora_inizio__isnull=False).values_list('data', 'ora_inizio')
    for data, ora in prenotazioni:
        occupati_per_giorno[data.strftime('%Y-%m-%d')].append(ora.strftime('%H:%M'))

    fasce = [
        {'inizio': inizio.strftime('%H:%M'), 'fine': f'{inizio.hour + 1:02d}:00', 'etichetta': etichetta}
        for inizio, etichetta in FASCE_ORARIE_ASSISTENZA
    ]
    return JsonResponse({'fasce': fasce, 'occupati_per_giorno': occupati_per_giorno})

class ConfermaPreventivoView(View):
    def get(self, request, assistenza_id, risposta):
        assistenza = get_object_or_404(Assistenza, id=assistenza_id)

        if risposta == 'si':
            assistenza.stato = 'accettato'
        else:
            assistenza.stato = 'chiuso_negativamente'
        assistenza.save()

        if assistenza.classificazioni.exists():
            solo_informatico = assistenza.classificazioni.all().filter(
                classificazione__manutenzione__tipo_manutenzione='informatico'
            ).count() == assistenza.classificazioni.count()
        classificazioni = Classificazione.objects.filter(assistenza_id=assistenza.pk)

        for classificazione in classificazioni:
            if solo_informatico:
                if classificazione.validate == True:
                    assistenza.stato = 'chiuso_positivamente'
                    assistenza.save(update_fields=['stato'])
                else:
                    classificazione.validate = True
                    assistenza.stato = 'chiuso'
                assistenza.save(update_fields=['stato'])
                classificazione.save(update_fields=['validate'])


        return redirect('struttura:chatview', assistenza_id=assistenza.id)

@login_required(login_url='/autenticazione/login/')
def set_validate_true(request, classificazione_id):
    classificazione = get_object_or_404(Classificazione, id=classificazione_id)

    classificazione.validate = True
    classificazione.save()

    altre_classificazioni_non_validate = Classificazione.objects.filter(
        assistenza=classificazione.assistenza,
        validate=False
    )

    if not altre_classificazioni_non_validate.exists():
        assistenza = classificazione.assistenza
        assistenza.stato = 'chiuso'
        assistenza.save()
    else:
        assistenza = classificazione.assistenza
        # if assistenza.stato != 'accettazione':
        #     assistenza.stato = 'accettazione'
        #     assistenza.save()

    return redirect('struttura:assistenza_classificazione', assistenza_id=assistenza.id)

class ChiudiAssistenzaPositivamente(View):
    def get(self, request, assistenza_id):
        assistenza = get_object_or_404(Assistenza, id= assistenza_id)
        assistenza.stato = 'chiuso_positivamente'
        assistenza.save()

        return redirect('struttura:assistenza_homepage')

class ChiudiAssistenzaNegativamente(View):
    def get(self, request, assistenza_id):
        assistenza = get_object_or_404(Assistenza , id= assistenza_id)
        assistenza.stato = 'chiuso_negativamente'
        assistenza.save()

        return redirect('struttura:assistenza_homepage')

class Validate(LoginRequiredMixin, TemplateView):
    template_name = 'Validate.html'
    success_url = reverse_lazy('struttura:assistenza_classificazione')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        assistenza_id = self.kwargs.get('assistenza_id')

        assistenza = get_object_or_404(Assistenza, pk=assistenza_id)

        context['assistenza'] = assistenza

        return context

@login_required(login_url='/autenticazione/login/')
def detect_text_view(request, assistenza_id):
    assistenza = get_object_or_404(Assistenza, pk=assistenza_id)

    if request.method == 'POST' and request.FILES.get('image'):

        torna_alla_classificazione = redirect('struttura:assistenza_classificazione', assistenza_id=assistenza.id)

        if not settings.GOOGLE_APPLICATION_CREDENTIALS:
            logger.error('Text detection: GOOGLE_APPLICATION_CREDENTIALS non impostata.')
            esito_scansione(request, messages.ERROR, SCANSIONE_NON_RIUSCITA)
            return torna_alla_classificazione

        image_file = request.FILES['image']
        file_path = default_storage.save(f'temp/{image_file.name}', image_file)
        try:
            credentials = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_APPLICATION_CREDENTIALS
            )
            client = vision.ImageAnnotatorClient(credentials=credentials)
            with default_storage.open(file_path, 'rb') as img_file:
                content = img_file.read()
            image = vision.Image(content=content)
            response = client.text_detection(image=image)
        except Exception as exc:  # credenziali non valide, rete, quota...
            logger.exception("Text detection non riuscita per l'assistenza %s", assistenza.id)
            esito_scansione(request, messages.ERROR, SCANSIONE_NON_RIUSCITA)
            return torna_alla_classificazione
        finally:
            default_storage.delete(file_path)

        if response.error.message:
            logger.error("Text detection non riuscita per l'assistenza %s: %s", assistenza.id, response.error.message)
            esito_scansione(request, messages.ERROR, SCANSIONE_NON_RIUSCITA)
            return torna_alla_classificazione

        texts = response.text_annotations
        componenti_validati = []
        seriali_non_previsti = []

        detected_texts = []
        for text in texts:
            vertices = ', '.join(f"({v.x},{v.y})" for v in text.bounding_poly.vertices)
            serial_text = text.description.strip()

            seriale_articolo = SerialeArticolo.objects.filter(codice_articolo_fornitore=serial_text).first()

            if seriale_articolo:
                manutenzione = seriale_articolo.manutenzione
                if manutenzione:

                    classificazioni = Classificazione.objects.filter(manutenzione=manutenzione, assistenza=assistenza)
                    if classificazioni.exists():
                        componenti_validati.append(str(manutenzione))
                    else:
                        seriali_non_previsti.append(f'{serial_text} ({manutenzione})')
                    for classificazione in classificazioni:

                        if classificazione.assistenza == assistenza and classificazione.manutenzione == manutenzione:

                            classificazione.validate = True
                            classificazione.save()
                            altre_classificazioni_non_validate = Classificazione.objects.filter(
                                assistenza=classificazione.assistenza,
                                validate=False
                            )

                            if not altre_classificazioni_non_validate.exists():
                                assistenza = classificazione.assistenza
                                assistenza.stato = 'chiuso'
                                assistenza.save()
                            else:
                                assistenza = classificazione.assistenza
                                if assistenza.stato != 'accettazione':
                                    assistenza.stato = 'accettazione'
                                    assistenza.save()

            detected_texts.append({
                'description': serial_text,
                'bounds': vertices,
                'validated': seriale_articolo is not None
            })

        componenti_validati = list(dict.fromkeys(componenti_validati))
        seriali_non_previsti = list(dict.fromkeys(seriali_non_previsti))
        if componenti_validati:
            da_validare = Classificazione.objects.filter(assistenza=assistenza, validate=False).count()
            esito_scansione(request, messages.SUCCESS,
                            'Seriale validato. Assistenza chiusa.' if da_validare == 0 else 'Seriale validato.')
        elif seriali_non_previsti:
            esito_scansione(request, messages.WARNING, 'Seriale non previsto per questa assistenza.')
        elif texts:
            esito_scansione(request, messages.WARNING, 'Seriale non riconosciuto.')
        else:
            esito_scansione(request, messages.WARNING, 'Nessun testo riconosciuto.')
        return torna_alla_classificazione

    return render(request, 'Validate.html', {'assistenza': assistenza})


SCANSIONE_NON_RIUSCITA = 'Scansione non riuscita.'


def esito_scansione(request, livello, testo):
    """Esito della scansione con text detection, mostrato come SweetAlert dopo il redirect (vedi base.html)."""
    messages.add_message(request, livello, testo, extra_tags='swal')
