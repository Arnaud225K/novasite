from django import template
from django.conf import settings
from apps.offers.models import OfferCollection

register = template.Library()






# @register.simple_tag(takes_context=True)
# def get_filial_url(context, target_filial):
#     """
#     Construit l'URL complète pour la page actuelle sur un autre sous-domaine.
#     Gère le cas de la filiale par défaut pour qu'elle pointe vers le domaine principal.
#     """
#     request = context['request']
    
#     # On récupère le domaine principal depuis les settings
#     main_domain = getattr(settings, 'MAIN_DOMAIN', 'localhost')
    
#     # On détermine le nouveau nom d'hôte
#     new_host = ""
#     if target_filial.is_default:
#         new_host = main_domain
#     else:
#         new_host = f"{target_filial.subdomain}.{main_domain}"

#     # On ajoute le port s'il est présent dans la requête originale (pour le dev)
#     host_parts = request.get_host().split(':')
#     if len(host_parts) > 1:
#         port = host_parts[1]
#         new_host = f"{new_host}:{port}"
    
#     # On garde le chemin actuel et les paramètres GET
#     full_path = request.get_full_path()
    
#     return f"{request.scheme}://{new_host}{full_path}"


# @register.simple_tag(takes_context=True)
# def get_filial_url(context, target_filial):
#     """
#     Construit l'URL complète pour une autre filiale.
#     - Si on est sur une page d'offres, essaie de trouver l'offre équivalente
#       dans la nouvelle filiale, sinon redirige vers l'accueil.
#     """
#     request = context['request']
    
#     main_domain = getattr(settings, 'MAIN_DOMAIN', 'localhost')
#     new_host = main_domain if target_filial.is_default else f"{target_filial.subdomain}.{main_domain}"
#     host_parts = request.get_host().split(':')
#     if len(host_parts) > 1:
#         new_host = f"{new_host}:{host_parts[1]}"
    
#     path_to_use = request.get_full_path()


#     # SPECIAL OFFERS LOGIQUE
    
#     # On vérifie si on est sur une page de détail d'offres.
#     if context.get('is_offer_page'):
#         # On a trouvé la collection parente de la page actuelle.
#         current_collection = context.get('current_menu') # Dans cette vue, current_menu est la collection
        
#         equivalent_collection = None
        
#         # On cherche la collection équivalente pour la filiale CIBLE.
#         # On remonte la hiérarchie de la filiale CIBLE.
#         filial_to_check = target_filial
#         while filial_to_check and not equivalent_collection:
#             equivalent_collection = filial_to_check.homepage_offer_collection
#             filial_to_check = filial_to_check.parent
        
#         # Si on n'en trouve pas, on prend la collection par défaut du site.
#         if not equivalent_collection:
#             equivalent_collection = OfferCollection.objects.filter(is_default_collection=True, is_hidden=False).first()

#         if equivalent_collection:
#             # Si on a trouvé une collection équivalente, on génère l'URL vers sa page
#             # en utilisant get_absolute_url() qui est déjà sur le modèle OfferCollection.
#             path_to_use = equivalent_collection.get_absolute_url()
#         else:
#             # En dernier recours, si aucune collection n'est trouvée pour la nouvelle ville,
#             # on redirige vers sa page d'accueil.
#             path_to_use = '/'
            
#     # ----------------------------------------------
    
#     return f"{request.scheme}://{new_host}{path_to_use}"



@register.simple_tag(takes_context=True)
def get_filial_url(context, target_filial):
    """
    Construit l'URL complète pour une autre filiale de manière performante,
    en utilisant les données préchargées du context processor.
    """
    request = context['request']
    
    main_domain = getattr(settings, 'MAIN_DOMAIN', 'localhost')
    new_host = main_domain if target_filial.is_default else f"{target_filial.subdomain}.{main_domain}"
    host_parts = request.get_host().split(':')
    if len(host_parts) > 1:
        new_host = f"{new_host}:{host_parts[1]}"
    
    # --- LOGIQUE DE CHEMIN ---
    path_to_use = request.get_full_path()

    # On vérifie si on est sur une page d'offres
    if context.get('is_offer_page'):
        equivalent_collection = None
        
        # On utilise les données préchargées pour remonter la hiérarchie
        filial_to_check = target_filial
        while filial_to_check and not equivalent_collection:
            equivalent_collection = filial_to_check.homepage_offer_collection
            filial_to_check = filial_to_check.parent 
        
        # Si on n'a rien trouvé, on utilise la collection par défaut préchargée
        if not equivalent_collection:
            equivalent_collection = context.get('default_offer_collection')

        if equivalent_collection:
            path_to_use = equivalent_collection.get_absolute_url()
        else:
            path_to_use = '/'
            
    
    return f"{request.scheme}://{new_host}{path_to_use}"