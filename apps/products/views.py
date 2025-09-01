from django.shortcuts import render
from django.conf import settings
from .models import Product






class RecentlyViewed:
    """
    Gère une liste de produits récemment vus stockée dans la session de l'utilisateur.
    """
    def __init__(self, request):
        self.session = request.session
        # On récupère la liste depuis la session, ou on en crée une nouvelle
        recently_viewed = self.session.get(settings.RECENTLY_VIEWED_SESSION_ID)
        if not recently_viewed:
            recently_viewed = self.session[settings.RECENTLY_VIEWED_SESSION_ID] = []
        self.recently_viewed = recently_viewed

    def add(self, product):
        """
        Ajoute un produit à la liste des produits récemment vus.
        """
        product_id = product.id

        # Évite les doublons et déplace le produit en tête de liste
        if product_id in self.recently_viewed:
            self.recently_viewed.remove(product_id)
        
        # On ajoute l'ID du produit au début de la liste
        self.recently_viewed.insert(0, product_id)
        
        # On limite la liste aux N derniers produits
        max_items = getattr(settings, 'MAX_RECENTLY_VIEWED_ITEMS', 10)
        self.recently_viewed = self.recently_viewed[:max_items]

        self.save()

    def get_products(self, current_product_id=None):
        """
        Récupère les objets Product correspondants aux IDs dans la session,
        en excluant le produit actuellement consulté.
        """
        product_ids = self.recently_viewed
        
        # On exclut le produit de la page actuelle de la liste
        if current_product_id and current_product_id in product_ids:
            product_ids.remove(current_product_id)
        
        if not product_ids:
            return Product.objects.none()

        # On récupère les produits en une seule requête, en préservant l'ordre
        products = Product.objects.filter(pk__in=product_ids)
        # On trie les résultats pour qu'ils correspondent à l'ordre dans la session (du plus récent au plus ancien)
        preserved_order = sorted(products, key=lambda p: product_ids.index(p.pk))
        return preserved_order

    def save(self):
        self.session.modified = True