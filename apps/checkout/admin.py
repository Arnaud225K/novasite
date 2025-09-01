from django.contrib import admin
from .models import Order, OrderItem
from django.utils.html import format_html
from rangefilter.filters import DateRangeFilterBuilder
from apps.utils.utils import format_price_admin, format_price_with_type_admin
from apps.products.models import Product 




class OrderItemInline(admin.TabularInline):
    model = OrderItem
    fields = ('product', 'product_title', 'display_formatted_price', 'quantity', 'get_cost_display')
    readonly_fields = ('product', 'product_title', 'display_formatted_price', 'quantity', 'get_cost_display')
    extra = 0
    can_delete = False
    
    def display_formatted_price(self, obj):
        """Affiche le prix formaté pour cet article, en incluant 'от' si nécessaire."""
        return format_price_with_type_admin(obj.price, obj.price_type)
    display_formatted_price.short_description = 'Цена за ед.'

    def get_cost_display(self, obj):
        """Affiche le coût total formaté pour cette ligne."""
        return format_price_with_type_admin(obj.get_cost(), obj.price_type)
    get_cost_display.short_description = 'Стоимость'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        '__str__', 
        'order_type', 
        'name',
        'phone', 
        # 'display_formatted_total', 
        'filial',
        'created_at'
    )
    list_filter = ('order_type', 'filial', 'created_at')
    search_fields = ('id', 'phone', 'email', 'name', 'comment')
    readonly_fields = (
        'id', 'order_key', 'created_at', 'updated_at', 'ip_address', 
        'display_formatted_total', 'file_link'
    )
    inlines = [OrderItemInline]

    def get_fieldsets(self, request, obj=None):
        if obj and obj.order_type == Order.TYPE_CART:
            return (
                ("Информация о заявке (Корзина)", {
                    "fields": ("id", "order_type", "display_formatted_total", "created_at", "filial")
                }),
                ("Данные клиента", {
                    "fields": ("name", "phone", "email", "comment", "file_link", "ip_address", "marketing_consent")
                }),
            )
        return (
            ("Информация о заявке", {
                "fields": ("id", "order_type", "created_at", "filial")
            }),
            ("Данные клиента", {
                "fields": ("name", "phone", "email", "comment", "text", "ip_address", "marketing_consent")
            }),
        )

    def get_inline_instances(self, request, obj=None):
        # On n'affiche les articles que si la commande vient du panier
        if obj and obj.order_type == Order.TYPE_CART:
            return super().get_inline_instances(request, obj)
        return []
    
    def display_formatted_total(self, obj):
        """
        Affiche le coût total formaté. Affiche "Договорная" si la commande
        contient des articles à prix non-fixe.
        """
        if obj.has_non_fixed_price():
            return "Договорная"
        # Sinon, on utilise le formateur simple (sans le type "от")
        return format_price_admin(obj.total_cost)
    display_formatted_total.short_description = 'Общая стоимость'
    display_formatted_total.admin_order_field = 'total_cost'

    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{0}" target="_blank">{1}</a>', obj.file.url, obj.file.name.split('/')[-1])
        return "Нет файла"
    file_link.short_description = 'Прикрепленный файл'

