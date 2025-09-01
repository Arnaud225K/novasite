from decimal import Decimal
from django.conf import settings
from apps.products.models import Product 

CART_SESSION_ID = 'zakaz'
    



class CartManager:
    """
    Gère le panier d'achat stocké dans la session Django, en prenant en compte
    les prix par filiale et les différents types de prix des produits.
    """
    def __init__(self, request):
        """Initialise le panier en se basant sur la session et la filiale actuelles."""
        self.session = request.session
        self.filial = request.filial  # La filiale est nécessaire pour les calculs de prix
        cart_data = self.session.get(settings.CART_SESSION_ID)
        if not cart_data:
            cart_data = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart_data

    def save(self):
        """Marque la session comme modifiée pour garantir sa sauvegarde."""
        self.session.modified = True

    def add(self, product, quantity=1, update_quantity=False):
        """
        Ajoute un produit au panier ou met à jour sa quantité.
        Stocke le prix de la filiale et le type de prix au moment de l'ajout.
        """
        product_id = str(product.id)
        
        price = product.get_price_for_filial(self.filial) or Decimal('0.00')
        
        price_type = product.price_type

        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0, 
                'price': str(price), 
                'price_type': price_type
            }

        if update_quantity:
            self.cart[product_id]['quantity'] = int(quantity)
        else:
            self.cart[product_id]['quantity'] += int(quantity)
        
        if self.cart[product_id]['quantity'] <= 0:
            self.remove(product)
            return

        self.cart[product_id]['price'] = str(price)
        self.cart[product_id]['price_type'] = price_type
        
        self.save()

    def remove(self, product):
        """Supprime un produit du panier."""
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()


    def __iter__(self):
        """
        Itère sur les articles du panier, récupère les objets Product,
        et retourne une COPIE de chaque article enrichie avec l'objet Product.
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids).prefetch_related('images')
        product_dict = {str(p.id): p for p in products}

        for product_id, item_data in self.cart.copy().items():
            product = product_dict.get(product_id)
            if product:
                item_copy = item_data.copy()
                
                item_price = Decimal(item_copy['price'])
                item_copy['product'] = product
                item_copy['total_price'] = item_price * item_copy['quantity']
                item_copy['price_type'] = self.cart[product_id].get('price_type', Product.PRICE_TYPE_FIXED)
                
                yield item_copy 
            else:
                del self.cart[product_id]
                self.save()

    def __len__(self):
        """Retourne la quantité totale de tous les articles dans le panier."""
        return sum(item['quantity'] for item in self.cart.values())

    def has_non_fixed_price(self):
        """
        Vérifie si le panier contient au moins un article dont le prix
        n'est pas fixe (soit négociable, soit "à partir de").
        """
        for item in self.cart.values():
            # Si le prix est 0 OU si le type est 'from', le total est non fixe.
            if Decimal(item.get('price', '0')) == 0 or item.get('price_type') == Product.PRICE_TYPE_FROM:
                return True
        return False

    def get_total_price(self):
        """
        Calcule le prix total. Si un article a un prix non fixe (négociable ou "à partir de"),
        retourne None pour signaler que le total est "Договорная".
        """
        if self.has_non_fixed_price():
            return None  # Signal pour "Prix Négociable"
        
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        """Vide le panier de la session."""
        if settings.CART_SESSION_ID in self.session:
            del self.session[settings.CART_SESSION_ID]
            self.save()

    def get_cart_data(self):
        """Retourne la structure de données brute du panier."""
        return self.cart


