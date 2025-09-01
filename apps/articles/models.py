# articles/models.py

from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from unidecode import unidecode
from django_ckeditor_5.fields import CKEditor5Field
from apps.utils.image_utils import process_and_convert_image




class Articles(models.Model):
    order_number = models.FloatField(verbose_name="Порядковый номер", default=100.0)
    name = models.CharField(max_length=512, verbose_name="Название")
    slug = models.SlugField(max_length=512, verbose_name="URL-ключ", unique=True, db_index=True, blank=True)
    date = models.DateTimeField(verbose_name='Дата публикации', blank=True, null=True)
    overview = models.CharField(max_length=512, verbose_name="Краткий обзор")
    description = CKEditor5Field(config_name='extends', verbose_name="Описание (для SEO и превью)", blank=True, null=True)
    text = CKEditor5Field(config_name='extends', verbose_name="Полный текст статьи", blank=True, null=True)
    image = models.ImageField(upload_to='articles/', verbose_name="Картинка", blank=True, null=True)
    title_main = models.CharField(max_length=1024, verbose_name="Заголовок страницы", blank=True, null=True)
    keywords = models.TextField(verbose_name="Ключевые слова (мета)", blank=True, null=True)
    keywords_description = models.TextField(verbose_name="Описание (мета)", blank=True, null=True)
    is_show_main = models.BooleanField(verbose_name="Показывать на главной", default=False)
    is_hidden = models.BooleanField(verbose_name="Скрыть", default=False)
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(unidecode(self.name))

        process_this_image = False
        try:
            original = Articles.objects.get(pk=self.pk)
            if self.image != original.image:
                process_this_image = True
        except Articles.DoesNotExist:
            if self.image:
                process_this_image = True
        
        if process_this_image and self.image:
            self.image = process_and_convert_image(self.image, max_size=(700, 481))

        super().save(*args, **kwargs)


    def get_absolute_url(self):
        return reverse('articles:article_detail', kwargs={'slug': self.slug})

    class Meta:
        ordering = ["order_number", "-date"]
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"