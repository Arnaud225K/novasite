from django.contrib import admin
from .models import Uslugi




@admin.register(Uslugi)
class UslugiAdmin(admin.ModelAdmin):
    list_display = ('name', 'order_number', 'is_hidden', 'updated_at')
    # list_editable = ('order_number', 'is_hidden')
    search_fields = ('name', 'description', 'text')
    prepopulated_fields = {'slug': ('name',)}