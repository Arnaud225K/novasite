from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.base import TemplateView, View
from django.views.generic import DetailView, ListView
from .models import MenuCatalog, TypeMenu, MenuCatalogFilialVisibility
from apps.products.models import Product, FilterCategory, FilterValue
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.http import HttpResponseNotFound, HttpResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, Page
from django.http import HttpResponse, JsonResponse, Http404
from django.urls import reverse
import logging
from django.utils.text import slugify
from django.db.models.functions import Concat
from django.db.models import Q, Case, When, IntegerField, Value, Count, Prefetch
import random
from django.conf import settings
from collections import defaultdict
import urllib.parse
from django.template.loader import render_to_string
from unidecode import unidecode 
from apps.static_text.views import get_static_text
from apps.checkout.cart import CartManager
from django.middleware.csrf import get_token
from apps.utils.utils import (
    parse_filters_from_segment, 
    apply_filters_to_queryset, 
    get_available_filters,
    get_active_filters_data,
    build_filter_url_segment,
    get_active_filters_display_string,
)
from apps.products.views import RecentlyViewed
from apps.offers.models import OfferCollection
from apps.reviews.models import Review
from apps.articles.models import Articles
from apps.project_settings.models import ProjectSettings


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)



INDEX_TITLE_PAGE = 'index_title_page'
INDEX_META_DESCRIPTION = 'index_meta_description'
INDEX_META_KEYWORDS = 'index_meta_keywords'


CATEGORY_META_TITLE_PAGE = 'category_meta_title_page'
CATEGORY_META_DESCRIPTION = 'category_meta_description'
CATEGORY_META_KEYWORDS = 'category_meta_keywords'
CATEGORY_AUTOTEXT = 'category_autotext'

PRODUCT_META_TITLE_PAGE = 'product_meta_title_page'
PRODUCT_META_DESCRIPTION = 'product_meta_description'
PRODUCT_META_KEYWORDS = 'product_meta_keywords'
PRODUCT_AUTOTEXT = 'product_autotext'


SIZE_SALE_INDEX = 20
PRODUCTS_PER_PAGE = 2
SIZE_OFFERS_INDEX = 6
SIZE_INDEX_STROI = 6
SIZE_SPEC_OFFERS = 10
MAX_ITEM = 20
PRODUCT_CATEGORY_TYPE_IDS = [6, 7, 8]
SIZE_POP_CATEG_INDEX = 7










class IndexView(TemplateView):
    template_name = "catalog/index.html"

    def get(self, request):
        
        is_index = True
        current_filial = request.filial
        
        # 1. Popular categories
        popular_categories = MenuCatalog.objects.filter(type_menu_id__in=PRODUCT_CATEGORY_TYPE_IDS, is_hidden=False, is_show_main=True).order_by('order_number')[:SIZE_POP_CATEG_INDEX]

        # 2. Special offers collection 
        homepage_collection = None
        special_offers = []

        if current_filial:
            filial_to_check = current_filial
            while filial_to_check and not homepage_collection:
                homepage_collection = filial_to_check.homepage_offer_collection
                filial_to_check = filial_to_check.parent
        
        if not homepage_collection:
            try:
                homepage_collection = OfferCollection.objects.get(
                    is_default_collection=True,
                    is_hidden=False
                )
            except OfferCollection.DoesNotExist:
                logger.warning("No default homepage offer collection is configured.")
                pass
            except OfferCollection.MultipleObjectsReturned:
                logger.error("CRITICAL: Multiple default offer collections found. Please fix in admin.")
                homepage_collection = OfferCollection.objects.filter(
                    is_default_collection=True, is_hidden=False
                ).first()

        if homepage_collection:
            special_offers = homepage_collection.items.filter(
                product__is_hidden=False
            ).select_related(
                'product', 
                'product__category'
            ).prefetch_related(
                'product__images',
                'product__filial_data'
            ).order_by('order_number')[:10]

            for offer_item in special_offers:
                offer_item.product.display_price = offer_item.product.get_price_for_filial(current_filial)

        # 3. Reviews section
        homepage_reviews = Review.objects.filter(is_hidden=False).order_by('order_number')[:10]

        # 4. Articles section
        homepage_articles = Articles.objects.filter(is_show_main=True, is_hidden=False).order_by('order_number', '-date')[:4]

        # 5. Advantage
        cache_key = 'homepage_advantages'
        homepage_advantages = cache.get(cache_key)

        if homepage_advantages is None:
            settings_obj = ProjectSettings.objects.first()
            if settings_obj:
                homepage_advantages = list(settings_obj.advantages.filter(is_hidden=False).order_by('order_number'))
            else:
                homepage_advantages = []
            
            cache.set(cache_key, homepage_advantages, 3600)

        # 6 About

        about_page_content = None
        try:
            about_page_content = MenuCatalog.objects.get(slug='o-nas', is_hidden=False)
        except MenuCatalog.DoesNotExist:
            pass
            
        index_title_page = get_static_text(request, locals(), INDEX_TITLE_PAGE)
        index_meta_description = get_static_text(request, locals(), INDEX_META_DESCRIPTION)
        index_meta_keywords = get_static_text(request, locals(), INDEX_META_KEYWORDS)


        context = {
            'is_index' : is_index,
            'popular_categories':popular_categories,
            'homepage_collection':homepage_collection,
            'special_offers':special_offers,
            'homepage_reviews':homepage_reviews,
            'homepage_articles':homepage_articles,
            'homepage_advantages':homepage_advantages,
            'about_page_content':about_page_content,
            'index_title_page':index_title_page,
            'index_meta_description':index_meta_description,
            'index_meta_keywords':index_meta_keywords,
        }

        return render(request, self.template_name, context)
    


class MenuView(View):
    """
    Une vue de base qui gère l'affichage des pages de catégories/menus.
    Toute la logique est contenue dans la méthode get().
    """

    template_name = 'catalog/catalog.html'
    
    def get(self, request, hierarchical_slug, filter_segment=None, *args, **kwargs):
        """
        Gère les requêtes GET pour une page de catégorie.
        
        Args:
            request: L'objet de la requête HTTP.
            hierarchical_slug (str): Le chemin hiérarchique capturé depuis l'URL.
        """
        
        # 1. Trouver et Valider la Catégorie Actuelle 
        hierarchy_path = hierarchical_slug
        slugs = hierarchy_path.strip('/').split('/')
        current_slug = slugs[-1]

        target_item = None
        try:
            target_item = MenuCatalog.objects.select_related('parent', 'type_menu').get(slug=current_slug, is_hidden=False)
            ancestors = target_item.get_ancestors(include_self=True)
            candidate_slugs = [slugify(unidecode(a.slug or f"cat-{a.id}")) for a in ancestors] # Utilise unidecode
            if candidate_slugs != slugs:
                logger.warning(f"Path mismatch for slug '{current_slug}'. Expected '{'/'.join(candidate_slugs)}', got '{hierarchy_path}'. Raising 404.")
                raise Http404("Category path mismatch or inactive")
        except MenuCatalog.DoesNotExist:
            raise Http404("Category not found")
        except MenuCatalog.MultipleObjectsReturned:
            # Gérer le cas où le slug final n'est pas unique globalement
            logger.error(f"Multiple categories found with slug '{current_slug}'. This should ideally not happen if slugs are unique per level or globally.")
            raise Http404("Ambiguous category slug")

        current_menu = target_item

        current_filial = request.filial

        root_categories = MenuCatalog.objects.get_root_categories_with_children()

        # ON PARSE LE SEGMENT DE L'URL AU LIEU DES PARAMÈTRES GET
        active_filters = parse_filters_from_segment(filter_segment)

        # On ajoute les produits (en incluant les produits des sous-catégories)
        descendant_categories = current_menu.get_descendants(include_self=True)
        
        # On ajoute les sous-catégories directes
        subcategories = current_menu.get_children().filter(is_hidden=False)
        

        # 2. GESTION DES PRODUITS ET FILTRES 
        # A. Comportement spécifique : on ne prend QUE la catégorie actuelle
        product_categories_qs = MenuCatalog.objects.filter(pk=current_menu.pk)
            
        # B. On construit le queryset de base des produits
        base_products_queryset = Product.objects.filter(category__in=product_categories_qs, is_hidden=False).select_related('category').prefetch_related('images')


        # C. Appliquer ces filtres au queryset en utilisant votre fonction
        filtered_products_qs = apply_filters_to_queryset(base_products_queryset, active_filters)

        # D. ÉTAPE CRUCIALE MANQUANTE : Calculer les facettes pour l'affichage initial !
        # faceted_filters = get_faceted_filters(current_menu, filtered_products_qs)
        # available_filters = get_available_filters(current_menu, filtered_products_qs, active_filters)
        


        # 3. PAGINATION DES PRODUITS 
        paginator = Paginator(filtered_products_qs.prefetch_related('images','filial_data__filial'), PRODUCTS_PER_PAGE)
        page_number = request.GET.get('page')
        products_page_obj = paginator.get_page(page_number)

        # 4. Recalculer la disponibilité des filtres en passant le queryset déjà filtré
        available_filters = get_available_filters(
            category=current_menu, 
            base_queryset=base_products_queryset, 
            active_filters=active_filters,
            filtered_products_qs=filtered_products_qs 
        )

        # On génère la liste pour les tags
        active_filters_list = get_active_filters_data(active_filters)

        for product in products_page_obj.object_list:
            product.display_price = product.get_price_for_filial(current_filial)
        

        # mis a jout de la construction h1 ---
        display_string = get_active_filters_display_string(active_filters)
        
        # On construit le titre de base
        h1_title = current_menu.name
        if display_string:
            h1_title += f", {display_string}"

        current_page_number = products_page_obj.number
        if current_page_number > 1:
            h1_title += f" - страница {current_page_number}"

        base_api_url = reverse('menu:api_filter_products', kwargs={'hierarchical_slug': hierarchical_slug})
        # --- 4. Préparer le Contexte pour le Template ---
        context = {
            'current_menu': current_menu,
            'current_filial': current_filial,
            'root_categories': root_categories,
            'ancestors': ancestors,
            'subcategories':subcategories,
            'products_list': products_page_obj, 
            'base_api_url': base_api_url,
            'available_filters': available_filters,
            'active_filters': active_filters,
            'active_filters_list': active_filters_list,
            'h1_title': h1_title,
        }

        # 5. Déterminer quel Template utiliser 
        template_to_render = self.template_name
        if hasattr(current_menu, 'type_menu') and current_menu.type_menu and current_menu.type_menu.template:
            # on s'assure que current_menu.type_menu.template est un chemin de template valide
            if isinstance(current_menu.type_menu.template, str) and current_menu.type_menu.template.endswith('.html'):
                template_to_render = current_menu.type_menu.template
            else:
                logger.warning(f"Invalid template path for MenuCatalog {current_menu.id} TypeMenu: {current_menu.type_menu.template}. Using default.")
        else:
            logger.debug(f"No specific template for MenuCatalog {current_menu.id}. Using default: {template_to_render}")
        
        # 6. Rendre la réponse HTTP 
        return render(request, template_to_render, context)




# class CatalogIndexView(View):
#     """
#     Affiche la page principale du catalogue, qui liste les catégories racines
#     et un aperçu de leurs enfants.
#     """
#     template_name = 'menu/catalog_index.html'

#     def get(self, request, *args, **kwargs):
#         """
#         Gère la requête GET pour la page d'index du catalogue.
#         """
#         # On utilise directement votre manager personnalisé.
#         # La méthode get_root_categories_with_children() est optimisée
#         # avec Prefetch pour ne charger que les premiers enfants.
#         root_categories = MenuCatalog.objects.get_root_categories_with_children()

#         # On prépare le contexte pour le template.
#         context = {
#             'root_categories': root_categories,
#         }
        
#         # On rend le template principal de la page d'index du catalogue.
#         return render(request, self.template_name, context)



# def get_more_children_api(request, category_id):
#     """
#     Vue API paginée pour retourner les enfants d'une catégorie.
#     Accepte un paramètre GET 'page'.
#     """
#     try:
#         parent_category = MenuCatalog.objects.get(pk=category_id)

#         all_children = parent_category.get_children().filter(is_hidden=False).order_by('order_number', 'pk')

#         # LOGIQUE DE PAGINATION
#         page_size = 5 
#         paginator = Paginator(all_children, page_size)
        
#         page_number = request.GET.get('page', 5)
        
#         page_obj = paginator.get_page(page_number)

#         children_data = [
#             {'name': child.name, 'url': child.get_absolute_url()} 
#             for child in page_obj.object_list
#         ]
        
#         response_data = {
#             'children': children_data,
#             'has_next_page': page_obj.has_next()
#         }
        
#         return JsonResponse(response_data)
        
#     except MenuCatalog.DoesNotExist:
#         return JsonResponse({'error': 'Category not found'}, status=404)
    





class FilterProductsAPIView(View):
    def get(self, request, hierarchical_slug, filter_segment=None, *args, **kwargs):
        
        # 1. Obtenir la catégorie et le queryset de base
        try:
            current_slug = hierarchical_slug.strip('/').split('/')[-1]
            current_menu = MenuCatalog.objects.get(slug=current_slug, is_hidden=False)
        except MenuCatalog.DoesNotExist:
            return JsonResponse({'error': 'Category not found'}, status=404)
        
        # On détermine quelles catégories inclure dans la recherche de produits

        product_categories_qs = MenuCatalog.objects.filter(pk=current_menu.pk)

        csrf_token_value = get_token(request)
            
        base_products_queryset = Product.objects.filter(category__in=product_categories_qs, is_hidden=False)
        
        # 2. Parser et appliquer les filtres depuis l'URL
        active_filters = parse_filters_from_segment(filter_segment)
        filtered_products_qs = apply_filters_to_queryset(base_products_queryset, active_filters)

        # 3. Compter les produits et paginer
        product_count = filtered_products_qs.count()
        paginator = Paginator(filtered_products_qs.prefetch_related('images', 'filial_data__filial'), PRODUCTS_PER_PAGE)
        page_number = request.GET.get('page')
        products_page_obj = paginator.get_page(page_number)

        # 4. Recalculer la disponibilité des filtres
        available_filters = get_available_filters(
            category=current_menu, 
            base_queryset=base_products_queryset, 
            active_filters=active_filters,
            filtered_products_qs=filtered_products_qs
        )

        # 5. Préparer les données pour les partiels
        active_filters_list = get_active_filters_data(active_filters)
        
        for product in products_page_obj.object_list:
            product.display_price = product.get_price_for_filial(request.filial)

        # 6. Construire le H1 dynamique
        display_string = get_active_filters_display_string(active_filters)
        h1_title = current_menu.name
        if display_string:
            h1_title += f", {display_string}"
        current_page_number = products_page_obj.number
        if current_page_number > 1:
            h1_title += f" - страница {current_page_number}"


        # On récupère les données du panier manuellement
        cart = CartManager(request)
        cart_product_ids_list = [int(pid) for pid in cart.cart.keys()]

        # 7. Rendre les partiels en HTML
        context_products = {
            'products_list': products_page_obj, 
            'request': request,
            'cart_product_ids': cart_product_ids_list,
        }
        html_products = render_to_string('includes/partials/_products_partial.html', context_products)
        
        context_filters = {
            'available_filters': available_filters, 
            'active_filters': active_filters,
            'request': request,
            'csrf_token': csrf_token_value,
        }
        html_filters = render_to_string('includes/partials/_filters_partial.html', context_filters)
        

        context_active_filters = {
            'active_filters_list': active_filters_list
        }
        html_active_filters = render_to_string(
            'includes/partials/_active_filters.html',
            context_active_filters,
            request=request
        )
        
        context_pagination = {
            'products_list': products_page_obj
        }
        html_pagination = render_to_string(
            'includes/partials/_pagination_partial.html',
            context_pagination,
            request=request
        )

        # 8. CONSTRUCTION DE L'URL FINALE ---
        base_url = current_menu.get_absolute_url()
        filter_segment = build_filter_url_segment(active_filters)
        
        url_path = base_url
        if filter_segment:
            if not url_path.endswith('/'):
                url_path += '/'
            url_path += filter_segment

        query_params = {}
        # on ajoute le paramètre 'page' SEULEMENT si ce n'est pas la première page.
        if products_page_obj.number > 1:
            query_params['page'] = products_page_obj.number
        
        final_new_url = url_path
        if query_params:
            query_string = urllib.parse.urlencode(query_params)
            final_new_url += '?' + query_string

        # 9. Renvoyer la réponse JSON
        return JsonResponse({
            'html_products': html_products,
            'html_filters': html_filters,
            'html_active_filters': html_active_filters,
            'html_pagination': html_pagination,
            'new_url': final_new_url,
            'product_count': product_count,
            'h1_title': h1_title,
        })



class ProductView(View):
    """
    Gère l'affichage de la page de détail d'un produit.
    """
    template_name = 'catalog/product.html'

    def get(self, request, product_slug):
        
        current_filial = request.filial

        # 1. RÉCUPÉRER LE PRODUIT PRINCIPAL AVEC OPTIMISATIONS
        try:
            product = Product.objects.select_related(
                'category'
            ).prefetch_related(
                'images', 
                'filters__category',
                'filial_data__filial'
            ).get(
                slug=product_slug,
                is_hidden=False
            )
        except Product.DoesNotExist:
            raise Http404("Product not found")

        # 2. GESTION DES PRODUITS "RÉCEMMENT VUS"
        recently_viewed_handler = RecentlyViewed(request)
        recently_viewed_handler.add(product)
        recently_viewed_products = recently_viewed_handler.get_products(
            current_product_id=product.id
        )
        for p in recently_viewed_products:
            p.display_price = p.get_price_for_filial(current_filial)

        # 3. PRÉPARER LES DONNÉES SPÉCIFIQUES À L'AFFICHAGE
        # On calcule le prix du produit principal pour la filiale
        product.display_price = product.get_price_for_filial(current_filial)
        
        # On structure les caractéristiques (filtres) pour un affichage propre
        product_features = {}
        for f in product.filters.all():
            cat_name = f.category.name
            if cat_name not in product_features:
                product_features[cat_name] = []
            product_features[cat_name].append(f.value)

        # 4. PRÉPARER LES DONNÉES DE NAVIGATION (FIL D'ARIANE)
        current_menu = product.category
        ancestors = current_menu.get_ancestors(include_self=True)


        h1_title = product.full_title

        # 5. PRÉPARER LE CONTEXTE FINAL
        context = {
            'product': product,
            'current_filial': current_filial,
            'current_menu': current_menu,
            'ancestors': ancestors,
            'product_features': product_features,
            'recently_viewed_products': recently_viewed_products,
            'h1_title':h1_title,
        }
        
        return render(request, self.template_name, context)
    


class AjaxMegaMenuView(View):
    template_name = 'includes/partials/_mega_menu_content.html'

    def get(self, request, *args, **kwargs):
        if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return HttpResponse("Invalid request", status=400)

        # On peut mettre en cache le HTML final pour encore plus de performance
        # cache_key = f"mega_menu_html_filial_{request.filial.id if request.filial else 'none'}"
        # cached_html = cache.get(cache_key)
        # if cached_html:
        #     return HttpResponse(cached_html)

        # On récupère les catégories racines du catalogue
        # (Niveau 1 du menu, enfants de la catégorie "Каталог" racine)
        try:
            catalog_root = MenuCatalog.objects.get(slug='catalog', level=0)
            catalog_list = catalog_root.get_children().filter(
                is_hidden=False
            ).prefetch_related(
                'children' # Précharge le niveau 2
            ).order_by('order_number')
        except MenuCatalog.DoesNotExist:
            catalog_list = MenuCatalog.objects.none()

        # Cacher les catégories spécifiques à la filiale si nécessaire
        if request.filial:
            hidden_pks = request.filial.hidden_categories.values_list('category__pk', flat=True)
            catalog_list = catalog_list.exclude(pk__in=hidden_pks)
        
        context = {'catalog_list': catalog_list}
        html_content = render_to_string(self.template_name, context, request=request)
        
        # cache.set(cache_key, html_content, 3600) # Mettre en cache pour 1 heure
        return HttpResponse(html_content)
    




class OfferCollectionDetailView(View):
    template_name = 'offers/offers.html'

    def get(self, request, slug, *args, **kwargs):

        current_filial = request.filial

        try:
            collection = OfferCollection.objects.for_filial(current_filial).get(slug=slug)
        except OfferCollection.DoesNotExist:
            raise Http404("Offer collection not found or not available in this region.")


        product_ids = collection.items.order_by('order_number').values_list('product_id', flat=True)
        
        products_qs = Product.objects.filter(
            id__in=list(product_ids),
            is_hidden=False
        ).prefetch_related('images', 'filial_data__filial')
        
        from django.db.models import Case, When
        preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(product_ids)])
        products_qs = products_qs.order_by(preserved_order)

        paginator = Paginator(products_qs, PRODUCTS_PER_PAGE)
        page_number = request.GET.get('page')
        products_page_obj = paginator.get_page(page_number)

        current_filial = request.filial
        for product in products_page_obj.object_list:
            product.display_price = product.get_price_for_filial(current_filial)

        h1_title = collection.name
        if products_page_obj.number > 1:
            h1_title += f" - Страница {products_page_obj.number}"
        
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

        if is_ajax:
            html_products = render_to_string(
                'includes/partials/_products_partial.html', 
                {'products_list': products_page_obj, 'request': request},
                request=request
            )
            html_pagination = render_to_string(
                'includes/partials/_pagination_partial.html',
                {'products_list': products_page_obj, 'request': request}
            )

            url_path = request.path
            query_params = {}
            if products_page_obj.number > 1:
                query_params['page'] = products_page_obj.number
            
            query_string = urllib.parse.urlencode(query_params)
            final_new_url = url_path
            if query_string:
                final_new_url += '?' + query_string
            # --------------------------------------------------

            return JsonResponse({
                'html_products': html_products,
                'html_pagination': html_pagination,
                'h1_title': h1_title,
                'new_url': final_new_url,
            })

        context = {
            'current_menu': collection,
            'h1_title': h1_title,
            'products_list': products_page_obj,
            'is_offer_page': True,
            'base_path_for_js': request.path,
        }
        
        return render(request, self.template_name, context)

