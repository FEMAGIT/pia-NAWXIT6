from django.urls import path

from . import views

app_name = 'api'

urlpatterns = [
    path('', views.indice, name='indice'),
    path('me', views.me, name='me'),

    path('clienti', views.clienti, name='clienti'),
    path('clienti/<int:pk>', views.cliente_dettaglio, name='cliente_dettaglio'),

    path('macchine', views.macchine, name='macchine'),
    path('macchine/<int:pk>', views.macchina_dettaglio, name='macchina_dettaglio'),
    path('macchine/<int:pk>/manutenzioni', views.macchina_manutenzioni, name='macchina_manutenzioni'),
    path('macchine/<int:pk>/documenti', views.macchina_documenti, name='macchina_documenti'),
    path('macchine/<int:pk>/assistenze', views.macchina_assistenze, name='macchina_assistenze'),
    path('tipi-macchina', views.tipi_macchina, name='tipi_macchina'),
    path('tipi-macchina/<int:pk>', views.tipo_macchina_dettaglio, name='tipo_macchina_dettaglio'),

    path('manutenzioni', views.manutenzioni, name='manutenzioni'),
    path('manutenzioni/<int:pk>', views.manutenzione_dettaglio, name='manutenzione_dettaglio'),
    path('documenti', views.documenti, name='documenti'),

    path('assistenze', views.assistenze, name='assistenze'),
    path('assistenze/<int:pk>', views.assistenza_dettaglio, name='assistenza_dettaglio'),
    path('assistenze/<int:pk>/chat', views.assistenza_chat, name='assistenza_chat'),
    path('calendario', views.calendario, name='calendario'),

    path('ordini', views.ordini, name='ordini'),
    path('ordini/<int:pk>', views.ordine_dettaglio, name='ordine_dettaglio'),
    path('ordini/<int:pk>/ciclo', views.ordine_ciclo, name='ordine_ciclo'),
    path('commesse', views.commesse, name='commesse'),
    path('commesse/<int:pk>', views.commessa_dettaglio, name='commessa_dettaglio'),
    path('articoli', views.articoli, name='articoli'),
    path('articoli/<int:pk>', views.articolo_dettaglio, name='articolo_dettaglio'),
    path('lavorazioni', views.lavorazioni, name='lavorazioni'),
    path('attivita', views.attivita, name='attivita'),
    path('log', views.log, name='log'),

    path('tracciabilita', views.tracciabilita, name='tracciabilita'),
    path('qualita/soglie', views.soglie_qualita, name='soglie_qualita'),
]
