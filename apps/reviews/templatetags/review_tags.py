from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def render_stars(rating):
    """
    Rend N balises SVG d'étoile en fonction de la note, et marque le HTML comme sûr.
    """
    try:
        # On verifie que la note est un entier entre 1 et 5
        rating = int(rating)
        rating = max(1, min(5, rating))
    except (ValueError, TypeError):
        rating = 0
    
    if rating == 0:
        return ""

    star_svg = '''
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#EDCF22">
            <path d="M12 2L14.9 8.6L22 9.2L17 14.1L18.4 21.1L12 17.8L5.6 21.1L7 14.1L2 9.2L9.1 8.6L12 2Z"></path>
        </svg>
    '''

    final_html = star_svg * rating
    
    return mark_safe(final_html)