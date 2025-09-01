from django.contrib import admin
from .models import SearchLog

@admin.register(SearchLog)
class SearchLogAdmin(admin.ModelAdmin):
    list_display = ('query', 'search_date', 'ip_address', 'filial')
    list_filter = ('search_date', 'filial')
    search_fields = ('query', 'ip_address', 'user__username')
    readonly_fields = ('query', 'search_date', 'ip_address', 'filial')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False