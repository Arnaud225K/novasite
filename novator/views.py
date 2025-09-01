import datetime
import json
import os
from . import settings
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse, Http404, JsonResponse
from django.shortcuts import render

from django.core.cache import cache

from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from apps.project_settings.models import ProjectSettings, SocialLink

from apps.filial.models import Filial
from apps.offers.models import OfferCollection
# from filials.views import get_current_filial

from apps.menu.models import MenuCatalog
# from robots.models import RobotsTxt
from apps.checkout.cart import CartManager
from django.utils import timezone 

MAX_ITEM_IN_FILE = 20000

MAX_HEADER_MENU_ITEMS = 6

PRODUCT_CATEGORY_TYPE_IDS = [6, 7, 8]





def get_project_settings_cached():
    """
    Helper function to retrieve project settings from cache or DB.
    (This is the function from the previous answer)
    """
    cache_key = 'project_settings_main'
    cached_settings = cache.get(cache_key)

    if cached_settings is None:
        # print(f"CACHE MISS: Fetching settings for key '{cache_key}' from database.")
        try:
            settings_obj = ProjectSettings.objects.only(
                'id', 'name', 'start_year', 'site_name','text_body','text_head',
            ).first()

            if settings_obj:
                cached_settings = {
                    'id': settings_obj.id,
                    'name': settings_obj.name,
                    'start_year': settings_obj.start_year,
                    'site_name': settings_obj.site_name,
                    'text_body': settings_obj.text_body,
                    'text_body': settings_obj.text_head,
                }
                # Cache for 1 hour
                cache.set(cache_key, cached_settings, timeout=0)
            else:
                print("Project settings object not found in database.")
                cached_settings = {}
                cache.set(cache_key, cached_settings, timeout=0) # Cache 'missing' state

        except Exception as e:
            print(f"Error fetching project settings: {e}")
            return {} # Return empty dict on error

    else:
        # print(f"CACHE HIT: Using cached settings for key '{cache_key}'.") # for debugging
        pass

    return cached_settings


def global_views(request):
    """
    Context processor providing global template variables.
    Optimized with caching for project settings and social links.
    """
    # --- Project Settings (Cached) ---
    project_settings_data = get_project_settings_cached()
    start_year = project_settings_data.get('start_year')
    site_name_from_db = project_settings_data.get('site_name')

    footer_menu_items_list = MenuCatalog.objects.filter(
        show_footer_rigth=True,
        is_hidden=False,
        type_menu_id__in=PRODUCT_CATEGORY_TYPE_IDS).only(
        'id', 'name', 'slug', 'order_number'
    ).order_by('order_number')[:MAX_HEADER_MENU_ITEMS] 



    # --- Other Context Variables ---
    current_year = datetime.date.today().year
    url_site = settings.SITE_NAME 
    current_url = request.build_absolute_uri()
    version_name = settings.VERSION_NAME
    site_header = settings.SITE_NAME
    site_title = f"{site_header} {version_name}"
    media_url = settings.MEDIA_URL
    static_url = settings.STATIC_URL
    current_timestamp_for_form = str(timezone.now().timestamp())



    context = {
        'current_year': current_year,
        'project_settings': project_settings_data,
        'start_year': start_year,
        'url_site': url_site,
        'current_url': current_url,
        'version_name': version_name,
        'site_header': site_header,
        'site_title': site_title,
        'site_name': site_name_from_db or settings.SITE_NAME,
        'media_url': media_url,
        'static_url': static_url,
        'form_render_timestamp_value': current_timestamp_for_form,
        'current_filial': request.filial,
        'footer_menu_items_list': footer_menu_items_list,
    }
    return context



def filial_context(request):
    """
    Prépare et précharge les données des filiales pour une utilisation
    performante dans les templates.
    """
    # On charge toutes les filiales et on précharge les relations nécessaires
    # pour la logique de cascade des offres.
    all_filials = Filial.objects.filter(is_hidden=False).order_by('order_number').select_related(
        'homepage_offer_collection', # Précharge la collection directement liée
        'parent__homepage_offer_collection', # Précharge la collection du parent
        'parent__parent__homepage_offer_collection' # Et du grand-parent (adaptez si plus de niveaux)
    )
    
    default_collection_list = OfferCollection.objects.filter(is_default_collection=True, is_hidden=False).first()

    return {
        'all_filials': all_filials,
        'default_offer_collection': default_collection_list,
        'current_filial': request.filial,
    }


def cart_context(request):
    """
    Rend l'objet cart, le nombre d'articles uniques et une liste
    d'IDs de produits disponibles dans le contexte de tous les templates.
    """
    cart = CartManager(request)
    
    cart_data = cart.get_cart_data()
    
    product_id_strings = cart_data.keys()
    
    cart_product_ids_list = [int(pid) for pid in product_id_strings]
    
    cart_items_count = len(cart_product_ids_list)

    # --- Log pour débogage ---
    # print(f"Context Processor - Product IDs in Cart: {cart_product_ids_list}")
    # print(f"Context Processor - Unique Items Count: {cart_items_count}")
    # ------------------------

    return {
        'cart_object': cart,
        'cart_unique_items_count': cart_items_count,
        'cart_product_ids': cart_product_ids_list,
    }


#Page Error 404
def page404(request, exception):
	is_generic_error_404 = True
	response = render(request, 'catalog/404.html', {'is_generic_error_404': is_generic_error_404})
	response.status_code = 404
	return response


#Page Error 500
def page500(request):
	is_generic_error_500 = True
	response = render(request, 'catalog/500.html', {'is_generic_error_500': is_generic_error_500} )
	response.status_code = 500
	return response