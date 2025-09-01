from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Permet d'accéder à une clé de dictionnaire en utilisant une variable
    dans un template Django.
    Exemple: {{ mon_dict|get_item:ma_cle_variable }}
    Retourne None si la clé n'existe pas.
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None
