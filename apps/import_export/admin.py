# import_export/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import ImportExportLog

@admin.register(ImportExportLog)
class ImportExportLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'file_link', 'get_details_summary')
    list_filter = ('action', 'user', 'timestamp')
    search_fields = ('user__username', 'file_name', 'details__summary')
    
    # Tous les champs en lecture seule
    readonly_fields = [field.name for field in ImportExportLog._meta.fields]
    
    # On afficher le lien vers le fichier
    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{0}" target="_blank">{1}</a>', obj.file.url, obj.file_name)
        return "Нет файла"
    file_link.short_description = "Файл"
    file_link.admin_order_field = 'file_name'

    def get_details_summary(self, obj):
        return obj.details.get('summary', 'Нет данных')
    get_details_summary.short_description = "Сводка"

    def has_add_permission(self, request):
        # Personne ne peut ajouter de logs manuellement
        return False

    def has_change_permission(self, request, obj=None):
        # Personne ne peut modifier les logs
        return False

    def has_delete_permission(self, request, obj=None):
        # On peut autoriser la suppression si nécessaire, par exemple pour le superuser
        return request.user.is_superuser