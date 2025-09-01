from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'surname', 'rating', 'is_hidden', 'created_at')
    list_filter = ('is_hidden', 'rating')
    search_fields = ('name', 'surname', 'text')