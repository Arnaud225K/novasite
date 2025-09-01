from django import template
from django.template import Context, Template
import re
from apps.menu.models import MenuCatalog
from apps.products.models import Product
from apps.filial.models import Filial 

from django.utils.safestring import mark_safe, SafeString
from django.conf import settings
from functools import lru_cache
from decimal import Decimal

from django.utils.html import strip_tags
from html import unescape

register = template.Library()



class SafeRenderContext(Context):
    """Context that returns empty string for missing/None values"""
    def __getitem__(self, key):
        try:
            val = super().__getitem__(key)
            return "" if val is None else val
        except KeyError:
            return ""

@register.filter(name='my_safe', is_safe=True)
def my_safe(value, context_data=None):
    """
    Final working version that:
    1. Maintains original {{ content|my_safe:current_filial }} syntax
    2. Allows explicit {{ content|my_safe:template_vars }} syntax
    3. Never shows "None" values
    4. Doesn't auto-sniff other context variables
    """
    if not value:
        return ""

    try:
        t = Template(str(value))
        
        # Case 1: Original single parameter syntax
        if context_data is None or not isinstance(context_data, dict):
            ctx = SafeRenderContext({
                'current_filial': context_data,
                'str_filter_name': "",
                'str_filter_name_min': ""
            })
        
        # Case 2: Explicit context dictionary (must be named 'template_vars')
        elif isinstance(context_data, dict):
            # Create new dict with only allowed variables
            allowed_vars = {
                'current_filial': context_data.get('current_filial', ""),
                'str_filter_name': context_data.get('str_filter_name', ""),
                'str_filter_name_min': context_data.get('str_filter_name_min', ""),
            }
            ctx = SafeRenderContext(allowed_vars)
        
        return mark_safe(t.render(ctx))
    
    except Exception as e:
        if settings.DEBUG:
            return mark_safe(f"<!-- Template Error: {str(e)} -->")
        return mark_safe(value)
#-------------------------------------------------



@register.filter(name='clean_html')
def clean_html(value):
    """
    Nettoie le texte pour les meta descriptions :
    1. Supprime les balises HTML
    2. Convertit les entités HTML (&amp; -> &)
    3. Supprime les guillemets doubles superflus
    4. Échappe correctement pour le HTML
    """
    if not value:
        return ""

    if not isinstance(value, str):
        value = str(value)

    cleaned = strip_tags(value)

    cleaned = unescape(cleaned)

    cleaned = cleaned.replace('"', '')

    cleaned = re.sub(r'\s+', ' ', cleaned)

    return cleaned.strip()




@register.filter(name='remove_space_href')
def remove_space_href(value):
    """
    Supprime les espaces, parenthèses et tirets d'une chaîne.
    Idéal pour formater un numéro de téléphone pour un lien 'tel:'.
    """
    if not isinstance(value, str):
        return value if value is not None else ""
    characters_to_remove = ['-', '(', ')', ' ']
    pattern = '[' + ''.join(re.escape(char) for char in characters_to_remove) + ']'
    cleaned_value = re.sub(pattern, '', value)
    return cleaned_value


# @register.filter(name='format_price')
# def format_price(value):
#     if value is not None:
#         return f"{value:,.0f}".replace(",", " ")
#     return "0"
@register.filter(name='format_price')
def format_price(value):
    """
    Filtre de template pour formater un prix pour l'affichage public.
    - Si le prix est 0, retourne "Договорная".
    - Sinon, formate le nombre avec un séparateur pour les milliers.
    - Gère les valeurs None en retournant "по запросу" ou similaire.
    """
    if value is None:
        return "по запросу" # "Sur demande" - vous pouvez changer ce texte

    try:
        price_decimal = Decimal(value)
    except (ValueError, TypeError):
        return "по запросу" # Gère le cas où la valeur n'est pas un nombre

    # --- LA CONDITION CLÉ EST ICI ---
    # On vérifie si le prix est égal à zéro.
    if price_decimal == 0:
        return "Договорная" # "Négociable" ou "Prix contractuel"

    # Le reste de la logique de formatage
    try:
        price_int = int(price_decimal)
        return f"{price_int:,}".replace(",", " ")
    except (ValueError, TypeError):
        return "по запросу"


@register.filter
def to_decimal(value):
    """Convertit une chaîne de caractères en Decimal."""
    try:
        return Decimal(value)
    except:
        return Decimal('0')


@register.simple_tag
def get_filial_price(product, filiale, default_value="--"):
    """
    Un tag de template pour récupérer le prix d'un produit pour une filiale donnée.
    
    Usage dans le template:
    {% get_filial_price product_object request.filial as final_price %}
    {{ final_price|floatformat:0 }}
    """
    if not isinstance(product, Product):
        return default_value

    # On appelle la méthode que nous avons déjà créée sur le modèle.
    price = product.get_price_for_filial(filiale)
    
    if price is None:
        return default_value
        
    return price


@register.simple_tag
def pluralize_ru(number, one, few, many):
    """
    Tag de template pour la pluralisation correcte des noms en russe.
    Usage: {% pluralize_ru count 'наименование' 'наименования' 'наименований' %}
    """
    try:
        # S'assure que le nombre est un entier
        num = int(number)
    except (ValueError, TypeError):
        return many # Retourne la forme "many" en cas d'erreur

    num = abs(num) % 100
    last_digit = num % 10

    if 10 < num < 20:
        return many
    if 1 < last_digit < 5:
        return few
    if last_digit == 1:
        return one
    return many