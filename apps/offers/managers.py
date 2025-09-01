from django.db import models
from django.db.models import Q

class OfferCollectionManager(models.Manager):
    def for_filial(self, filial):
        """
        Retourne un queryset de collections visibles pour une filiale donnée.
        
        Logique :
        1. Inclut les collections spécifiquement liées à cette filiale.
        2. Inclut les collections qui ne sont liées à AUCUNE filiale (globales).
        """
        queryset = self.get_queryset().filter(is_hidden=False)
        
        if filial:
            # On cherche les collections qui sont soit globales (filials=None),
            # soit spécifiquement liées à la filiale actuelle.
            return queryset.filter(
                Q(filials=None) | Q(filials=filial)
            ).distinct()
        else:
            # Si aucune filiale n'est active (domaine principal sans filiale par défaut),
            # on n'affiche que les collections globales.
            return queryset.filter(filials=None)