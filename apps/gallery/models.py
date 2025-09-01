
from django.db import models
from django.utils.html import format_html
import os
import uuid
from django.utils import timezone
from apps.utils.image_utils import process_and_convert_image



def gallery_image_upload_path(instance, filename):
    """
    Définit le dossier de destination. Le nom du fichier sera géré dans l'admin.
    """
    now = timezone.now()
    return os.path.join('gallery_uploads', now.strftime('%Y/%m'), filename)

class GalleryImage(models.Model):
    title = models.CharField("Название (необязательно)", max_length=200, blank=True, help_text="Для вашего удобства, для поиска")
    image = models.ImageField("Изображение", upload_to=gallery_image_upload_path)
    uploaded_at = models.DateTimeField("Дата загрузки", auto_now_add=True)

    def __str__(self):
        return self.image.name

    def save(self, *args, **kwargs):
        if self.pk is None and self.image:
            self.image = process_and_convert_image(self.image, max_size=(700, 481))
        super().save(*args, **kwargs)

    
    def copyable_path(self):
        """Champ pour copier facilement le chemin."""
        if self.image:
            return self.image.name
        return ""
    copyable_path.short_description = "Путь для копирования"

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Импорт изображения"
        verbose_name_plural = "Импорт изображений"
