from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin, MPTTModelAdmin
from .models import TypeMenu, MenuCatalog, MenuCatalogFilialVisibility

from apps.utils.utils import get_admin_image_thumbnail_html



class MenuCatalogFilialVisibilityInline(admin.TabularInline):
    model = MenuCatalogFilialVisibility
    extra = 1 
    verbose_name = "Правило видимости в филиале"
    verbose_name_plural = "Правила видимости в филиалах"
    fields = ('filial', 'is_hidden')



@admin.register(TypeMenu)
class TypeMenuAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'template', 'identifier', 'updated_at', 'created_at')
    search_fields = ('name', 'identifier')
    
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'template', 'identifier')
        }),
        ("Информация о записи", {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(MenuCatalog)
class MenuCatalogAdmin(DraggableMPTTAdmin):
    list_display = ('id', 'tree_actions', 'indented_title', 'order_number','display_catalog_image', 'slug', 'type_menu', 'is_hidden', 'updated_at')
    list_display_links = ('indented_title',)
    # list_display = ('id', 'name', 'display_catalog_image', 'slug', 'order_number', 'type_menu', 'is_hidden', 'updated_at')
    # list_display_links = ('id', 'name',)
    list_filter = ('type_menu', 'is_hidden', 'is_show_main')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    

    inlines = [MenuCatalogFilialVisibilityInline]

    readonly_fields = ('created_at','updated_at',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'parent', 'type_menu', 'order_number')
        }),
        ('Отображение', {
            'fields': ('is_hidden', 'is_show_main', 'is_show_in_header', 'show_footer_left', 'show_footer_rigth')
        }),
        ('Контент', {
            'fields': ('image', 'description')
        }),
        ('Фильтры категории', {
            'fields': ('applicable_filters',)
        }),
        ('SEO', {
            'classes': ('collapse',),
            'fields': ('seo_title', 'seo_description', 'seo_keywords')
        }),
    )


    def display_catalog_image(self, obj):
        return get_admin_image_thumbnail_html(obj, image_field_name='image', alt_text_base="Категория")
    display_catalog_image.short_description = 'Картинка'

    def get_queryset(self, request):
        # Optimisation pour charger le type_menu en même temps
        return super().get_queryset(request).select_related('type_menu')