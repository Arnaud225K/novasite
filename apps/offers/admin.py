from django.contrib import admin
from .models import OfferCollection, SpecialOfferItem

class SpecialOfferItemInline(admin.TabularInline):
    """
    Inline pour gérer les produits directement depuis la page de la collection.
    """
    model = SpecialOfferItem
    extra = 1
    autocomplete_fields = ['product']
    fields = ('product', 'order_number')
    verbose_name = "Продукт в предложении"
    verbose_name_plural = "Продукты в предложениях"

@admin.register(OfferCollection)
class OfferCollectionAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour les collections d'offres.
    """
    list_display = ('name', 'slug', 'is_default_collection', 'is_hidden')
    prepopulated_fields = {'slug': ('name',)}
    
    # Widget pratique pour la sélection des filiales
    filter_horizontal = ('filials',)
    
    inlines = [SpecialOfferItemInline]
    
    list_filter = ('is_hidden', 'filials', 'is_default_collection',)
    search_fields = ('name', 'slug')