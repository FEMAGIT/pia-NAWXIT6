from django.contrib import admin
from django.utils.html import format_html

from .models import (Ordine,Articolo, Commessa, Macchina, TipoMacchina, TipoManutenzione, Manutenzione, OrdiniBlocco, Lavorazione, Documento,
                     Assistenza, Classificazione, Chat, SerialeArticolo, Log, Attività, QualitàAngoloAutomatico, QualitàTaglio)




class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('nome_documento', 'tipo_macchina', 'download_link')
    search_fields = ('nome_documento', 'tipo_macchina__tipomacchina')
    list_filter = ('tipo_macchina',)

    def download_link(self, obj):
        if obj.path_documento:
            return format_html('<a href="{}" download>Scarica</a>', obj.path_documento.url)
        return "Nessun file"
    download_link.short_description = "Download Documento"


admin.site.register(Ordine)
admin.site.register(Chat)
admin.site.register(Articolo)
admin.site.register(Commessa)
admin.site.register(Macchina)
admin.site.register(TipoMacchina)
admin.site.register(TipoManutenzione)
admin.site.register(Manutenzione)
admin.site.register(OrdiniBlocco)
admin.site.register(Lavorazione)
admin.site.register(Assistenza)
admin.site.register(Classificazione)
admin.site.register(Documento, DocumentoAdmin)
admin.site.register(Log)
admin.site.register(Attività)
admin.site.register(SerialeArticolo)
admin.site.register(QualitàAngoloAutomatico)
admin.site.register(QualitàTaglio)
