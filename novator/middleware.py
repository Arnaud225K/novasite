from django.core.cache import cache
from apps.filial.models import Filial 

class SubdomainFilialMiddleware:
    """
    Middleware qui détecte le sous-domaine, récupère la filiale correspondante 
    (en utilisant le cache pour la performance) et l'attache à la requête.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0]
        host_parts = host.split('.')
        subdomain = None

        if len(host_parts) > 2 and host_parts[0] != 'www':
            subdomain = host_parts[0]

        filial = self.get_filial(subdomain)

        request.filial = filial

        response = self.get_response(request)
        return response

    def get_filial(self, subdomain):
        """
        Récupère une filiale depuis le cache ou la base de données.
        
        Args:
            subdomain (str or None): Le sous-domaine détecté.
        
        Returns:
            Filiale or None: L'objet Filiale actif ou None.
        """
        filial = None
        
        if subdomain:
            cache_key = f"filial_subdomain_{subdomain}"
            filial = cache.get(cache_key)

            if filial is None:
                # Cache-miss : on cherche dans la BDD
                try:
                    filial = Filial.objects.get(subdomain=subdomain, is_hidden=False)
                except Filial.DoesNotExist:
                    # On stocke "None" dans le cache pour éviter de refaire une requête BDD
                    # pour un sous-domaine invalide à chaque fois.
                    filial = None 
                # On met le résultat (objet Filial ou None) dans le cache pour 1 heure
                # cache.set(cache_key, filial, 3600)
                cache.set(cache_key, filial, 300) #5min
        
        else:
            # Pas de sous-domaine, on cherche la filiale par défaut
            cache_key = "filial_default"
            filial = cache.get(cache_key)

            if filial is None:
                # Cache-miss : on cherche dans la BDD
                try:
                    filial = Filial.objects.get(is_default=True, is_hidden=False)
                except (Filial.DoesNotExist, Filial.MultipleObjectsReturned):
                    # Si aucune ou plusieurs filiales par défaut, on ne renvoie rien de sûr
                    filial = None
                # On met en cache
                # cache.set(cache_key, filial, 3600) #1h
                cache.set(cache_key, filial, 300) #5min
                
        return filial