from django.contrib import admin
from .models import (Product, ProductImage, ProductFilialData, FilterCategory, FilterValue)

from apps.utils.utils import format_price_admin, get_admin_product_image_thumbnail_html



class FilterValueInline(admin.TabularInline):
    model = FilterValue
    extra = 1
    prepopulated_fields = {'slug': ('value',)}

@admin.register(FilterCategory)
class FilterCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'unit', 'order')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [FilterValueInline]
    search_fields = ('name', 'slug')


@admin.register(FilterValue)
class FilterValueAdmin(admin.ModelAdmin):
    list_display = ('value', 'category', 'order')
    list_filter = ('category',)
    search_fields = ('value', 'category__name')
    list_select_related = ('category',)
    autocomplete_fields = ['category']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('gallery_image', 'alt_text', 'is_main', 'order')

class ProductFilialDataInline(admin.TabularInline):
    model = ProductFilialData
    extra = 1
    fields = ('filial', 'price', 'is_available')
    autocomplete_fields = ['filial']



@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'display_full_title', 'sku', 'display_product_image', 'price_type', 'display_formatted_price', 'category', 'is_hidden', 'created_at', 'updated_at')
    list_filter = ('category', 'is_hidden', 'price_type')
    search_fields = ('id', 'display_full_title', 'sku', 'description', 'category__name')
    filter_horizontal = ('filters',)
    list_display_links = ('id', 'display_full_title',)
    inlines = [ProductImageInline, ProductFilialDataInline]

    readonly_fields = ('created_at', 'updated_at', 'sku', 'display_full_title')

    autocomplete_fields = ['filters']

    fieldsets = (
        ('Основная информация и Статус', 
            {'fields': (
                'base_name', 
                'display_full_title',
                'slug', 
                'sku', 
                'category', 
                'is_hidden', 
                'is_hit',
                )
        }),
        ('Контент и Цены', {
            'fields': ('description', ('price_type', 'base_price'), 'unit',) 
        }),
        ('Статус и Фильтры', 
            {'fields': ( 'filters',)} 
        ),
    )

    @admin.display(description='Полное название (авто)', ordering='base_name')
    def display_full_title(self, obj):
        """
        Méthode pour afficher la propriété 'full_title' dans l'admin.
        """
        return obj.full_title

    def display_product_image(self, obj):
        return get_admin_product_image_thumbnail_html(obj, image_field_name='gallery_image', alt_text_base="Продукт")
    display_product_image.short_description = 'Картинка'

    def display_formatted_price(self, obj):
        """Affiche le prix formaté du produit dans list_display."""
        return format_price_admin(obj.base_price)
    display_formatted_price.short_description = 'Цена'
    display_formatted_price.admin_order_field = 'base_price'


    # --- OPTIMISATION DES REQUÊTES ---
    def get_queryset(self, request):
        """
        Optimise le chargement des données pour la liste des produits.
        """
        qs = super().get_queryset(request)
        # On précharge les relations pour éviter N+1 requêtes
        # 'images' est préchargé pour display_product_image
        # 'category' est préchargé pour l'affichage de la catégorie
        return qs.select_related('category').prefetch_related('images__gallery_image')