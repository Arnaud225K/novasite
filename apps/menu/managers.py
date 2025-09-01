
from mptt.managers import TreeManager
from django.conf import settings 
from django.db.models import Count, Q, Prefetch
# from .models import MenuCatalog


VALID_TYPE_MENU_IDS = getattr(settings, 'VALID_TYPE_MENU_IDS', [6, 7, 8])

# class MenuCatalogManager(TreeManager):
#     """
#     Manager personnalisé pour le modèle MenuCatalog.
#     """
#     def get_root_categories_with_children(self):
#         """
#         Récupère les catégories racines (level=0) qui ne sont pas cachées,
#         et précharge efficacement leurs enfants directs.
        
#         C'est la méthode de choix pour construire la page principale du catalogue.
#         """
#         # On utilise self.get_queryset() pour pouvoir chaîner les méthodes
#         return self.get_queryset().filter(
#             level=1, 
#             is_hidden=False,
#             type_menu_id__in=VALID_TYPE_MENU_IDS
#         ).prefetch_related(
#             'children'
#         ).order_by('order_number', 'name')


class MenuCatalogManager(TreeManager):
    """
    Manager personnalisé pour le modèle MenuCatalog.
    """
    def get_root_categories_with_children(self):
        """
        Récupère les catégories racines et précharge TRÈS efficacement
        les 6 premiers enfants directs pour chaque catégorie.
        """
        # On importe ici pour éviter une boucle d'importation si ce manager est dans models.py
        from .models import MenuCatalog 

        return self.get_queryset().filter(
            level=1, 
            is_hidden=False,
            type_menu_id__in=VALID_TYPE_MENU_IDS
        ).prefetch_related(
            Prefetch(
                'children',
                queryset=MenuCatalog.objects.filter(is_hidden=False).order_by('order_number', 'pk')[:6],
                to_attr='prefetched_children'
            )
        ).order_by('order_number', 'pk')