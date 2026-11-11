from django.urls import path, include

from . import views
from .datatables import MacchinaDatatables, DocumentoDatatables, ManutenzioneDatatables, AssistenzaDatatables, ClassificazioniDatatables, DocumentiDatatables
from .views import (MacchinaHomePageView, MacchinaCreateView, MacchinaUpdateView, MacchinaDeleteView, ChatView, OpenControlRoom, QRcodefilter, get_macchina_identificativo, get_manutenzioni,
                    ClassificazioneDeleteView, ClassificazioneUpdateView,Calendar,ConfermaPreventivoView, ChiudiAssistenzaPositivamente, ChiudiAssistenzaNegativamente,
                    DocumentoTemplateView, ManutenzioneView,AssistenzaHomePageView, AssistenzaDeleteView, AssistenzaUpdateView, AssistenzaCreateView, QRcodemacchina,
                    ClassificazioneCreateView, Validate )

app_name = 'struttura'


urlpatterns = [
    path('', MacchinaHomePageView.as_view(), name='macchina_homepage'),

    # LINK PER MACCHINA
    path('macchina/crea/', MacchinaCreateView.as_view(), name='macchina_crea'),
    path('macchina/<int:pk>/modifica/', MacchinaUpdateView.as_view(), name='macchina_modifica'),
    path('macchina/<int:pk>/elimina/', MacchinaDeleteView.as_view(), name='macchina_elimina'),
    path('macchina/datatables/', MacchinaDatatables.as_view(), name='macchina_datatables'),
    path('macchina/<int:pk>/', get_macchina_identificativo, name='get_macchina_identificativo'),

    # LINK PER DOCUMENTO
    path('macchina/documenti/template/<int:tipo_macchina_id>/', DocumentoTemplateView.as_view(), name='documento_template'),
    path('macchina/documenti/datatables/', DocumentoDatatables.as_view(), name='documento_datatables'),

    # LINK PER MANUTENZIONE
    path('macchina/<int:macchina_id>/manutenzione/', ManutenzioneView.as_view(), name='manutenzione_view'),
    path('manutenzione_datatables/', ManutenzioneDatatables.as_view(), name='manutenzione_datatables'),

    #LINK PER ASSISTENZA
    path('assistenza/', AssistenzaHomePageView.as_view(), name='assistenza_homepage'),
    path('assistenza/crea/', AssistenzaCreateView.as_view(), name='assistenza_crea'),
    path('assistenza/datatables/', AssistenzaDatatables.as_view(), name='assistenza_datatables'),
    path('classificazione/datatables/', ClassificazioniDatatables.as_view(), name='classificazione_datatables'),
    path('documenti/datatables/', DocumentiDatatables.as_view(), name='documenti_datatables'),
    path('assistenza/<int:pk>/elimina/', AssistenzaDeleteView.as_view(), name='assistenza_elimina'),
    path('classificazione/<int:pk>/elimina/', ClassificazioneDeleteView.as_view(), name='classificazione_elimina'),
    path('assistenza/<int:assistenza_id>/modifica/', AssistenzaUpdateView, name='assistenza_modifica'),
    path('classificazione/<int:pk>/modifica/', ClassificazioneUpdateView, name='classificazione_modifica'),
    path('assistenza/<int:assistenza_id>/classifica/', ClassificazioneCreateView, name='assistenza_classificazione'),
    path('assistenza/chat/<int:assistenza_id>', ChatView.as_view(), name='chatview'),
    path('assistenza/chat/<int:assistenza_id>/add/', views.chat_add_message, name='chat_add_message'),
    path('assistenza/controlroom/', OpenControlRoom.as_view(), name='open_control_room'),
    path('assistenza/qrcodefilter/', QRcodefilter.as_view(), name='QRcodefilter'),
    path('assistenza/qrcodemacchina/', QRcodemacchina.as_view(), name='QRcodemacchina'),
    path('get_manutenzioni/<str:value>/', get_manutenzioni, name='get_manutenzioni'),
    path('conferma_preventivo/<int:assistenza_id>/<str:risposta>/', ConfermaPreventivoView.as_view(), name='conferma_preventivo'),
    path('classificazione/validate/<int:classificazione_id>/', views.set_validate_true, name='set_validate_true'),
    path('assistenza/cambiastatopositivo/<int:assistenza_id>/', ChiudiAssistenzaPositivamente.as_view(), name='changestatuspositive'),
    path('assistenza/cambiastatonegativo/<int:assistenza_id>/', ChiudiAssistenzaNegativamente.as_view(), name='changestatusnegative'),
    path('validate/<int:assistenza_id>/', Validate.as_view(), name='Validate'),
    path('detect-text/<int:assistenza_id>/', views.detect_text_view, name='detect_text_view'),

    # LINK PER QR-CODE
    path('qr_code/<int:id>/', views.generate_pdf_qr_code, name='genera_qr_code'),

    #LINK PER CALENDAR
    path('calendar/', Calendar, name = "calendar_view"),

]

