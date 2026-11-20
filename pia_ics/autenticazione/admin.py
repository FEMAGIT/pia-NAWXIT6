from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ApiToken, Cliente, CustomUser


class ClienteAdmin(admin.ModelAdmin):
    list_display = ('ragione_sociale', 'p_iva', 'email', 'sede_legale', 'n_telefono')
    search_fields = ('ragione_sociale', 'p_iva', 'email')
    ordering = ('ragione_sociale',)
    fields = ('ragione_sociale', 'p_iva', 'email', 'cf', 'sede_legale', 'n_telefono', 'users')  # Aggiungi 'users' ai campi
    filter_horizontal = ('users',)




class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # Aggiungi i campi che vuoi visualizzare nel pannello admin
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'role')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')


    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Informazioni personali', {'fields': ('first_name', 'last_name')}),
        ('Permessi', {'fields': ('is_staff', 'is_active')}),
        ('Ruolo', {'fields': ('role',)}),
    )


    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role'),
        }),
    )


admin.site.register(Cliente, ClienteAdmin)
admin.site.register(CustomUser, CustomUserAdmin)



class ApiTokenAdmin(admin.ModelAdmin):
    """I token si creano con `python manage.py crea_token_api` (la chiave in chiaro si vede una sola volta);
    da qui si possono solo consultare, disattivare o far scadere."""
    list_display = ('nome', 'user', 'prefisso', 'attivo', 'creato', 'scadenza', 'ultimo_uso')
    list_filter = ('attivo',)
    search_fields = ('nome', 'user__email', 'prefisso')
    readonly_fields = ('user', 'nome', 'prefisso', 'creato', 'ultimo_uso')
    fields = ('user', 'nome', 'prefisso', 'attivo', 'scadenza', 'creato', 'ultimo_uso')

    def has_add_permission(self, request):
        return False


admin.site.register(ApiToken, ApiTokenAdmin)
