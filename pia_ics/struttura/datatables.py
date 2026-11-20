from django.urls import reverse
from django_datatables_view.base_datatable_view import BaseDatatableView
from django.utils.html import escape
from django.db.models import Q
from .models import Macchina, Documento, Manutenzione, Assistenza, Classificazione
from autenticazione.models import Cliente
from autenticazione.context_processors import user_info
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404

class MacchinaDatatables(BaseDatatableView):
    model = Macchina
    columns = ['identificativo', 'tipo_macchina', 'descrmacchina', 'cliente', 'azioni']
    order_columns = ['identificativo', 'tipo_macchina', 'descrmacchina', 'cliente', '']

    def get_initial_queryset(self):
        user = self.request.user
        macchina = Macchina.objects.all()
        user_context = user_info(self.request)

        if user.is_authenticated:
            if user.is_superuser:
                return macchina
            elif user_context['user_is_client']:
                clienti_associati = user.clienti_associati.all()
                return macchina.filter(cliente__in=clienti_associati)
            elif user_context['user_is_worker']:
                return macchina
        return Macchina.objects.none()

    def render_column(self, row, column):
        if column == 'identificativo':
            return escape('{0}'.format(row.identificativo))
        if column == 'tipo_macchina':
            return escape('{0}'.format(row.tipo_macchina))
        if column == 'descrmacchina':
            return escape('{0}'.format(row.descrmacchina))
        if column == 'cliente':
            return escape('{0}'.format(row.cliente))
        if column == 'azioni':
            buttons = '<div class="d-flex justify-content-around">'

            # Verifica se l'utente è un superuser
            if self.request.user.is_superuser:
                buttons += (
                    '<a href="{1}" class="btn-sm btn btn-danger text-white text-center ms-2" title="Modifica Macchina" data-bs-toggle="tooltip">'
                    '<i class="fa-regular fa-pen-to-square"></i></a>'  # BOTTONE MODIFICA
                    '<a class="btn-sm btn btn-danger text-white text-center" onclick="DeleteMacchina(\'{2}\')" title="Elimina Macchina" data-bs-toggle="tooltip">'
                    '<i class="fa-regular fa-trash-can"></i></a>'  # BOTTONE DELETE
                ).format(
                    # Nota: Aggiungiamo anche il link al documento
                    reverse('struttura:documento_template', args=[row.tipo_macchina_id]),  # DOCUMENTO
                    reverse('struttura:macchina_modifica', args=[row.pk]),  # MODIFICA
                    row.pk  # DELETE
                )

            # Aggiungi i bottoni sempre visibili
            buttons += (
                '<a href="{0}" class="btn-sm btn btn-danger text-white text-center" title="Visualizza Documento" data-bs-toggle="tooltip">'
                '<i class="fa-regular fa-file"></i></a>'  # BOTTONE DOCUMENTO
                '<a href="{3}" class="btn-sm btn btn-danger text-white text-center" title="Visualizza Manutenzione" data-bs-toggle="tooltip">'
                '<i class="fa-solid fa-diagram-predecessor"></i></a>'  # BOTTONE MANUTENZIONE
                '<a href="{4}" class="btn-sm btn btn-danger text-white text-center me-2" title="Genera QR Code" data-bs-toggle="tooltip">'
                '<i class="fa-solid fa-qrcode"></i></a>'  # BOTTONE QR-CODE
                '</div>'
            ).format(
                reverse('struttura:documento_template', args=[row.tipo_macchina_id]),  # DOCUMENTO
                reverse('struttura:macchina_modifica', args=[row.pk]),  # MODIFICA
                row.pk,  # DELETE
                reverse('struttura:manutenzione_view', args=[row.pk]),  # MANUTENZIONE
                reverse('struttura:genera_qr_code', args=[row.pk])  # QR-CODE
            )
            return buttons

        return super(MacchinaDatatables, self).render_column(row, column)

    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(Q(tipo_macchina__tipomacchina__icontains=search) |
                           Q(descrmacchina__icontains=search) |
                           Q(cliente__ragione_sociale__icontains=search)
                           )
        return qs

    def ordering(self, qs):
        order = []
        for i in range(len(self.order_columns)):
            order_col_index = self.request.GET.get(f'order[{i}][column]', None)
            if order_col_index is not None:
                order_col_index = int(order_col_index)
                sort_dir = self.request.GET.get(f'order[{i}][dir]', 'asc')
                sort_col = self.order_columns[order_col_index]

                # Ignora colonne non ordinabili (es. 'azioni' con '')
                if not sort_col:
                    continue

                # Determina la direzione dell'ordinamento
                prefix = '-' if sort_dir == 'desc' else ''
                order.append(f"{prefix}{sort_col}")

        if order:
            qs = qs.order_by(*order)
        return qs


class DocumentoDatatables(BaseDatatableView):
    model = Documento
    columns = ['nome_documento', 'tipo_macchina', 'azioni']
    order_columns = ['nome_documento', 'tipo_macchina', '']

    def get_initial_queryset(self):
        tipo_macchina_id = self.request.GET.get('tipo_macchina_id')
        if tipo_macchina_id:
            return self.model.objects.filter(tipo_macchina__id=tipo_macchina_id)
        return self.model.objects.none()

    def render_column(self, row, column):
        if column == 'nome_documento':
            return escape(row.nome_documento)
        if column == 'tipo_macchina':
            return escape(row.tipo_macchina.tipomacchina)
        if column == 'azioni':
            return (
                '<div class="d-flex justify-content-center">'
                '<a href="{}" target="_blank" class="btn-sm btn btn-danger text-white" title="Visualizza/Scarica" data-bs-toggle="tooltip"><i class="fas fa-download"></i></a>'
                '</div>'
            ).format(row.path_documento.url if row.path_documento else '#')
        return super(DocumentoDatatables, self).render_column(row, column)

    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(Q(nome_documento__icontains=search) | Q(tipo_macchina__nome__icontains=search))
        return qs


class ManutenzioneDatatables(BaseDatatableView):
    model = Manutenzione
    columns = ['componente', 'descrizionecomponente', 'link', 'azioni']
    order_columns = ['componente', 'descrizionecomponente', 'link', '']

    def get_initial_queryset(self):
        return self.model.objects.all()


    def render_column(self, row, column):
        if column == 'componente':
            return escape(row.componente)
        if column == 'descrizionecomponente':
            return escape(row.descrizionecomponente)
        if column == 'link':
            return escape(row.link)
        if column == 'azioni':
            return (
                '<div class="d-flex justify-content-center">'
                '<a href="{0}" target="_blank" class="btn-sm btn btn-danger text-white" title="Apri link" data-bs-toggle="tooltip">'
                '<i class="fas fa-info-circle"></i></a>'
                '</div>'
            ).format(escape(row.link))

        return super(ManutenzioneDatatables, self).render_column(row, column)

    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(componente__icontains=search) | Q(descrizionecomponente__icontains=search)
            )
        return qs

class AssistenzaDatatables(BaseDatatableView):
    model = Assistenza
    columns = ['titolo', 'descassistenza', 'data', 'stato', 'azioni']
    order_columns = ['titolo', 'descassistenza', 'data', 'stato']

    def get_initial_queryset(self):
        user = self.request.user
        assistenza = Assistenza.objects.all()
        user_context = user_info(self.request)

        if user.is_authenticated:
            if user.is_superuser:
                return assistenza.order_by('-data')
            elif user_context['user_is_client']:
                cliente = Cliente.objects.get(users=user)
                macchine_cliente = Macchina.objects.filter(cliente=cliente)
                return assistenza.filter(macchine__in=macchine_cliente).order_by('-data')
            elif user_context['user_is_worker']:
                return assistenza.filter(stato__in=['chiuso', 'chiuso_negativamente', 'accettato']).order_by('-data')
        return Assistenza.objects.none()

    def render_column(self, row, column):
        if column == 'titolo':
            return escape(f'{row.titolo}')
        if column == 'descassistenza':
            return escape(f'{row.descassistenza}')
        if column == 'data':
            return escape(f'{row.data}')
        if column == 'stato':
            return escape(f'{row.stato}')
        if column == 'azioni':
            if row.pk:
                classificazioni_exists = row.classificazioni.exists()
                start_buttons = '<div class="d-flex justify-content-center">'
                end_buttons = '</div>'

                if classificazioni_exists:

                    azioni = (

                        f'<a href="{reverse("struttura:chatview", args=[row.pk])}" class="btn-sm btn btn-danger text-white" title="Chat Assistenza" data-bs-toggle="tooltip"><i class="fas fa-eye"></i></a>'
                        f'<a href="{reverse("struttura:assistenza_classificazione", args=[row.pk])}" class="btn-sm btn btn-danger text-white" title="Classificazione" data-bs-toggle="tooltip"><i class="fas fa-cog"></i></a>'
                        f'<a href="{reverse("struttura:assistenza_modifica", args=[row.pk])}" class="btn-sm btn btn-danger text-white" title="Modifica" data-bs-toggle="tooltip"><i class="fas fa-edit"></i></a>'
                        f'<button type="button" class="btn btn-sm btn-danger" title="Elimina" data-bs-toggle="tooltip" onclick="DeleteAssistenza(\'{row.pk}\')"><i class="fas fa-trash"></i></button>'
                    )

                    if row.stato == 'chiuso':


                        azioni += (

                            f'<a href="{reverse("struttura:changestatuspositive", args=[row.pk])}" class="btn-sm btn btn-danger text-white" title="Status Positivo" data-bs-toggle="tooltip"><i class="fas fa-check"></i></a>'
                            f'<a href="{reverse("struttura:changestatusnegative", args=[row.pk])}" class="btn-sm btn btn-danger text-white" title="Status Negativo" data-bs-toggle="tooltip"><i class="fas fa-xmark"></i></a>'

                        )
                    html_result = start_buttons + azioni + end_buttons
                    return html_result
                else:
                    azioni = (

                        f'<a href="{reverse("struttura:assistenza_classificazione", args=[row.pk])}" class="btn-sm btn btn-danger text-white" title="Assistenza Classificazione" data-bs-toggle="tooltip"><i class="fas fa-cog"></i></a>'
                        f'<a href="{reverse("struttura:assistenza_modifica", args=[row.pk])}" class="btn-sm btn btn-danger text-white" title="Modifica Assistenza" data-bs-toggle="tooltip"><i class="fas fa-edit"></i></a>'
                        f'<button type="button" class="btn btn-sm btn-danger" title="Elimina" data-bs-toggle="tooltip" onclick="DeleteAssistenza(\'{row.pk}\')"><i class="fas fa-trash"></i></button>'

                    )
                    if row.stato == 'chiuso':
                        azioni += (
                            f'<a href="{reverse("struttura:changestatuspositive", args=[row.pk])}" class="btn-sm btn btn-danger text-white" title="Status Positivo" data-bs-toggle="tooltip"><i class="fas fa-check"></i></a>'
                            f'<a href="{reverse("struttura:changestatusnegative", args=[row.pk])}" class="btn-sm btn btn-danger text-white" title="Status Negativo" data-bs-toggle="tooltip"><i class="fas fa-xmark"></i></a>'
                        )
                    html_result = start_buttons + azioni + end_buttons
                    return html_result

            else:
                print('No actions avaiable')
        return super().render_column(row, column)

    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            try:
                qs = qs.filter(
                    Q(titolo__icontains=search) |
                    Q(descassistenza__icontains=search) |
                    Q(data__icontains=search) |
                    Q(macchine__identificativo__icontains=search)
                )
            except Exception as e:
                print(f'Error during filtering: {e}')
        return qs

class ClassificazioniDatatables(BaseDatatableView):
    model = Classificazione
    columns = ['assistenza', 'manutenzione', 'validate', 'timestamp', 'azioni']
    order_columns = ['assistenza', 'manutenzione', 'validate', 'timestamp']

    def render_column(self, row, column):
        csrf_token = get_token(self.request)

        if column == 'timestamp':
            return escape('{0}'.format(row.timestamp))
        if column == 'validate':
            return escape('{0}'.format(row.validate))
        if column == 'assistenza':
            return escape('{0}'.format(row.assistenza))
        if column == 'manutenzione':
            return escape('{0}'.format(row.manutenzione))
        if column == 'azioni':
            if row.assistenza.stato == 'accettazione' or row.assistenza.stato == 'accettato':
                validate_button = (
                    f'<form action="{reverse("struttura:set_validate_true", args=[row.pk])}" method="POST" style="display:inline;">'
                    f'<input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}" />'
                    f'<button type="submit" class="btn-sm btn btn-danger"'
                    f'title="Valida manutenzione">'
                    f'<i class="fas fa-edit"></i></button>'
                    f'</form>'
                )
            else:
                validate_button = ''

            delete_button = (
                f'<button type="button" class="btn btn-sm btn-danger" title="Cancella manutenzione" onclick="DeleteClassificazione(\'{row.pk}\')">'
                f'<i class="fas fa-trash"></i></button>'
            )

            open_link_button = (
                f'<a href="{row.manutenzione.link}" target="_blank" class="btn btn-sm btn-danger" '
                f'title="Apri link manutenzione">'
                f'<i class="fas fa-external-link-alt"></i></a>'
            ) if row.manutenzione.link else ''


            return f'{validate_button}{open_link_button}{delete_button}'
        return super(ClassificazioniDatatables, self).render_column(row, column)

    def filter_queryset(self, qs):
        assistenza_titolo = self.request.GET.get('assistenza', None)
        print("titolo filtro:", assistenza_titolo)
        if assistenza_titolo:
            qs = qs.filter(assistenza__titolo=assistenza_titolo)
        return qs


class DocumentiDatatables(BaseDatatableView):
    model = Documento
    columns = ['nome_documento', 'tipo_macchina', 'azioni']
    order_columns = ['nome_documento', 'tipo_macchina', '']

    def render_column(self, row, column):
        if column == 'nome_documento':
            return escape(row.nome_documento)
        if column == 'tipo_macchina':
            return escape(str(row.tipo_macchina))
        if column == 'azioni':
            link_url = row.path_documento.url
            return (
                f'<a href="{link_url}" target="_blank" class="btn-sm btn btn-danger text-white" title="Link Documento">'
                f'<i class="fa-regular fa-file"></i>'
                f'</a>'
            )
        return super().render_column(row, column)

    def get_initial_queryset(self):
        assistenza_id = self.request.GET.get('assistenza_id')
        assistenza = get_object_or_404(Assistenza, id=assistenza_id)
        return Documento.objects.filter(tipo_macchina=assistenza.macchine.tipo_macchina)


