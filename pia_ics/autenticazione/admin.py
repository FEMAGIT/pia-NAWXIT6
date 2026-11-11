from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Cliente, CustomUser


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

