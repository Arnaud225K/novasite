from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Advantage

@receiver([post_save, post_delete], sender=Advantage)
def invalidate_advantages_cache(sender, instance, **kwargs):
    """ Supprime le cache des avantages de la page d'accueil. """
    cache.delete('homepage_advantages')