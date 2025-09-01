# uslugi/models.py

from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from unidecode import unidecode
from django_ckeditor_5.fields import CKEditor5Field
from apps.utils.image_utils import process_and_convert_image

class Uslugi(models.Model):
    order_number = models.PositiveIntegerField("Порядок", default=0)
    name = models.CharField(max_length=255, verbose_name="Название")
    slug = models.SlugField("URL-ключ (слаг)", max_length=255, unique=True, db_index=True, blank=True)
    image = models.ImageField(upload_to='uslugi/', null=True, blank=True, verbose_name="Картинка")
    description = models.CharField(max_length=512, verbose_name="Краткое описание")
    text = CKEditor5Field(config_name='extends', verbose_name="Полное описание", blank=True, null=True)
    is_hidden = models.BooleanField(verbose_name="Скрыть", default=False)
    title_main = models.CharField(max_length=1024, verbose_name="Заголовок страницы", blank=True, null=True)
    keywords = models.TextField(verbose_name="Ключевые слова (мета)", blank=True, null=True)
    keywords_description = models.TextField(verbose_name="Описание (мета)", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    def __str__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(unidecode(self.name))
        
        process_this_image = False
        try:
            original = Uslugi.objects.get(pk=self.pk)
            if self.image != original.image:
                process_this_image = True
        except Uslugi.DoesNotExist:
            if self.image:
                process_this_image = True
        
        if process_this_image and self.image:
            self.image = process_and_convert_image(self.image, max_size=(700, 481))
            
        super().save(*args, **kwargs)


    def get_absolute_url(self):
        return reverse('uslugi:uslugi_detail', kwargs={'slug': self.slug})

    class Meta:
        ordering = ["order_number"]
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"
        indexes = [
            models.Index(fields=['is_hidden', 'order_number'], name='idx_uslugi_hidden_order'),
        ]