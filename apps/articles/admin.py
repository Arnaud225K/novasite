from django.contrib import admin
from .models import Articles

@admin.register(Articles)
class ArticlesAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'order_number', 'is_hidden', 'is_show_main')
    # list_editable = ('order_number', 'is_hidden', 'is_show_main')
    search_fields = ('name', 'overview', 'text')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_hidden', 'is_show_main', 'date')