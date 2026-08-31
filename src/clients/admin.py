from django.contrib import admin

from clients.models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("client_number", "name", "firm", "client_type", "status")
    search_fields = ("client_number", "name", "email", "phone", "firm__display_name")
    list_filter = ("client_type", "status")
