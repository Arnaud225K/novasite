import os
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile



def process_and_convert_image(image_field, max_size=(724, 524), quality=85):
    """
    Traite une image : la redimensionne, la convertit en WebP et la retourne
    sous forme de ContentFile prêt à être sauvegardé dans un ImageField.

    Args:
        image_field: L'objet ImageFieldFile source (ex: self.image).
        max_size (tuple): Les dimensions maximales (largeur, hauteur) de l'image.
        quality (int): La qualité de la compression WebP (1-100).

    Returns:
        ContentFile or None: Le nouveau fichier image traité ou None si l'entrée est vide.
    """
    if not image_field:
        return None

    try:
        img = Image.open(image_field)
    except Exception:
        # Si le fichier n'est pas une image valide, on ne fait rien
        return None

    # Conversion du mode pour une meilleure compatibilité
    if img.mode in ('P', 'LA'):
        img = img.convert("RGBA")

    # Redimensionnement de haute qualité
    try:
        resampling_algorithm = Image.Resampling.LANCZOS
    except AttributeError:
        # Pour les anciennes versions de Pillow
        resampling_algorithm = Image.ANTIALIAS
    img.thumbnail(max_size, resampling_algorithm)

    # Sauvegarde en mémoire au format WebP
    thumb_io = BytesIO()
    img.save(thumb_io, format='WEBP', quality=quality)

    # Création du nouveau nom de fichier avec l'extension .webp
    original_filename = image_field.name
    base_name, _ = os.path.splitext(original_filename)
    new_filename = f"{base_name}.webp"

    # Création d'un fichier Django prêt à être sauvegardé
    new_image = ContentFile(thumb_io.getvalue(), name=new_filename)

    return new_image