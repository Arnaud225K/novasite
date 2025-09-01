from django.contrib import admin
from .models import Filial
from .filters import IsParentFilter, ParentChoiceFilter 

@admin.register(Filial)
class FilialAdmin(admin.ModelAdmin):
    list_display = ('name', 'subdomain', 'phone', 'parent', 'is_default', 'homepage_offer_collection', 'is_hidden', 'order_number',)
    search_fields = ('name', 'subdomain', 'email', 'phone',)
    list_filter = ('is_hidden', ParentChoiceFilter, IsParentFilter)

    autocomplete_fields = ['parent', 'homepage_offer_collection']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'name_info', 'region', 'parent', 'homepage_offer_collection', 'order_number')
        }),
        ('Конфигурация Домена и Статус', {
            'fields': ('subdomain', 'is_default', 'is_hidden', 'is_base')
        }),
        ('Контактная информация', {
            'fields': ('phone', 'phone_dop', 'email', 'address', 'working_hours', 'map_code')
        }),
        ('Реквизиты Компании', {
            'classes': ('collapse',),
            'fields': (
                'full_name_req', 'short_name_req', 'requisites_file', 'director_req',
                ('inn_req', 'kpp_req'),
                'yr_address_req', 'fact_address_req',
                ('bank_req', 'ogrn_req'),
                'bik_req',
                ('chet_req', 'korr_chet_req'),
                'okved_req', 'okpo_req', 'okato_req', 'oktmo_req',
            )
        }),
        ('SEO и Скрипты', {
            'classes': ('collapse',),
            'fields': ('seo_text_head', 'seo_text_body')
        }),
    )

    def get_queryset(self, request):
        # Optimise la requête en pré-chargeant le parent pour éviter des requêtes N+1
        return super().get_queryset(request).select_related('parent')
    
