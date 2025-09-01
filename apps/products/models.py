from django.db import models
from django.utils.text import slugify
from unidecode import unidecode
from apps.filial.models import Filial
from .managers import ProductManager
from apps.gallery.models import GalleryImage
from apps.utils.image_utils import process_and_convert_image
from django.core.exceptions import ValidationError
from django.urls import reverse, NoReverseMatch
import random
import string
import time
import uuid

from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.contrib.postgres.indexes import GinIndex


import logging 
logger = logging.getLogger(__name__)


class FilterCategory(models.Model):
    """
    Категория фильтра, которая группирует значения.
    Например: 'Производитель', 'Цвет', 'Материал'.
    """
    name = models.CharField("Название фильтра", max_length=100, unique=True)
    slug = models.SlugField("Ключ для URL", max_length=100, unique=True, help_text="Используется в URL (латиница, цифры, дефис)")
    order = models.PositiveIntegerField("Порядок", default=100, help_text="Порядок отображения в списке фильтров")
    unit = models.CharField("Единица измерения", max_length=20, blank=True, help_text="(Напр., 'мм', 'кг')")

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Категория фильтра"
        verbose_name_plural = "Категории фильтров"

    def __str__(self):
        return self.name

class FilterValue(models.Model):
    """
    Конкретное значение внутри категории фильтра.
    Например: 'Aquaviva' (для Производителя), 'Красный' (для Цвета).
    """
    category = models.ForeignKey(FilterCategory, verbose_name="Категория фильтра", related_name='values', on_delete=models.CASCADE)
    value = models.CharField("Значение", max_length=255, db_index=True)
    slug = models.SlugField("Ключ для URL", max_length=255, blank=True)
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ['category__order', 'category__name', 'order', 'value']
        unique_together = ('category', 'slug')
        verbose_name = "Значение фильтра"
        verbose_name_plural = "Значения фильтров"

    def __str__(self):
        return f"{self.category.name}: {self.value}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(unidecode(self.value))
        super().save(*args, **kwargs)



class Product(models.Model):
    """
    Основная модель продукта в каталоге.
    Содержит общую информацию, не зависящую от филиала.
    """

    # --- CONSTANTES POUR LES TYPES DE PRIX ---
    PRICE_TYPE_FIXED = 'fixed'
    PRICE_TYPE_FROM = 'from'
    PRICE_TYPE_CHOICES = [
        (PRICE_TYPE_FIXED, 'Фиксированная цена'),
        (PRICE_TYPE_FROM, 'от'),
    ]

    base_name = models.CharField("Базовое название", max_length=200, blank=True, help_text="Основное название без характеристик, напр., 'Канат одинарной свивки'")
    title = models.CharField("Полное название", max_length=512, db_index=True, blank=True, help_text="Генерируется автоматически")
    slug = models.SlugField("URL-ключ (слаг)", max_length=255, unique=True, db_index=True, blank=True)
    sku = models.CharField("Артикул (SKU)", max_length=100, unique=True, db_index=True, blank=True, help_text="Генерируется автоматически при сохранении, если пустое.")
    category = models.ForeignKey("menu.MenuCatalog", verbose_name="Категория", on_delete=models.PROTECT, related_name="products")
    description = models.TextField("Описание", blank=True)
    base_price = models.DecimalField("Базовая цена", max_digits=10, decimal_places=2, help_text="Цена по умолчанию, если не переопределена в филиале.")
    price_type = models.CharField("Тип цены", max_length=10, choices=PRICE_TYPE_CHOICES, default=PRICE_TYPE_FROM, help_text="Определяет, как отображается цена (например, 'от 2000 ₽').")    
    unit = models.CharField("Единица измерения", max_length=50, blank=True, help_text="напр., шт, кг, м²")
    filters = models.ManyToManyField(FilterValue, verbose_name="Значения фильтров", related_name="products", blank=True)
    is_hidden = models.BooleanField("Скрыть", default=False, db_index=True, help_text="Скрыть товар со всего сайта.")
    is_hit = models.BooleanField("Хит продаж", default=False, db_index=True, help_text="Показывать в блоке 'Хиты' на главной.")
    manufacturer = models.CharField("Производитель", max_length=255, blank=True)
    country_of_origin = models.CharField("Страна производства", max_length=100, blank=True)
    warranty_info = models.CharField("Гарантия", max_length=100, blank=True)
    material = models.CharField("Материал", max_length=100, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True, editable=False)
    updated_at = models.DateTimeField("Обновлено", auto_now=True, editable=False)
    search_vector = SearchVectorField(null=True, editable=False)
    

    objects = ProductManager()

    class Meta:
        ordering = ['title']
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"
        indexes = [
            GinIndex(fields=['search_vector'], name='product_search_vector_idx'),
        ]
            

    @property
    def full_title(self):
        """
        Génère et retourne le titre complet à la volée.
        Ce n'est PAS un champ de base de données.
        """
        if not self.pk:
            return self.base_name
        parts = [self.base_name]
        for fv in self.filters.select_related('category').order_by('category__order'):
            value, unit = fv.value, fv.category.unit
            parts.append(f"{value} {unit}" if unit else value)
        return " ".join(parts)

    def save(self, *args, **kwargs):
        """
        Gère la sauvegarde et la génération automatique des champs.
        Garantit un SKU numérique et un Slug propre.
        """
        if self.pk is None and not self.sku:
            self.sku = f"temp-sku-{uuid.uuid4().hex}"
            if not self.slug:
                self.slug = self.sku

        super().save(*args, **kwargs)

        update_fields = []

        if "temp-sku" in self.sku:
            category_id_part = str(self.category_id or '0').zfill(3)
            product_id_part = str(self.pk).zfill(6)
            random_part = str(random.randint(100, 999))
            self.sku = f"{category_id_part}{product_id_part}{random_part}"
            update_fields.append('sku')

        current_full_title = self.full_title
        if self.title != current_full_title:
            self.title = current_full_title
            update_fields.append('title')

        potential_slug = slugify(unidecode(self.title))

        if Product.objects.filter(slug=potential_slug).exclude(pk=self.pk).exists():
            final_slug = f"{potential_slug}-{self.sku}"
        else:
            final_slug = potential_slug

        if self.slug != final_slug:
            self.slug = final_slug
            update_fields.append('slug')
        
        if update_fields:
            Product.objects.filter(pk=self.pk).update(**{field: getattr(self, field) for field in set(update_fields)})


        if 'update_fields' not in kwargs or 'search_vector' not in kwargs['update_fields']:
            vector = (
                SearchVector('base_name', weight='A', config='russian') +
                SearchVector('sku', weight='A', config='russian') +
                SearchVector('title', weight='B', config='russian') +
                SearchVector('description', weight='C', config='russian')
            )
            Product.objects.filter(pk=self.pk).update(search_vector=vector)

    def __str__(self):
        return self.full_title


    def get_price_for_filial(self, filiale):
        """
        Récupérer le prix d'un produit
        en suivant la hiérarchie de filiales, avec des logs de débogage.
        """
        logger.debug(f"--- Calcul du prix pour Produit ID {self.id} ('{self.title}') ---")
        
        if not filiale:
            logger.debug(f"Aucune filiale fournie. Retour du prix de base: {self.base_price}")
            return self.base_price

        logger.debug(f"Filiale de départ: '{filiale.name}' (ID: {filiale.id})")
        
        current_filiale = filiale
        
        while current_filiale:
            logger.debug(f"Vérification de la filiale: '{current_filiale.name}'...")

            # On utilise .filter().first() au lieu de .get() pour éviter les erreurs "DoesNotExist"
            filial_data = self.filial_data.filter(filial=current_filiale).first()
            
            if filial_data:
                logger.debug(f"Données de filiale trouvées. Prix spécifique: {filial_data.price}")
                # Si un prix est explicitement défini pour cette filiale, on le retourne.
                if filial_data.price is not None:
                    logger.debug(f"Prix trouvé ! Retour de {filial_data.price}")
                    return filial_data.price
            else:
                logger.debug("Aucune donnée spécifique pour cette filiale.")

            # On passe à la filiale parente
            logger.debug(f"Passage à la filiale parente de '{current_filiale.name}'.")
            current_filiale = current_filiale.parent
        
        # Si la boucle se termine, on retourne le prix de base
        logger.debug(f"Aucun prix de filiale trouvé dans la hiérarchie. Retour du prix de base: {self.base_price}")
        return self.base_price

    def get_absolute_url(self):
        return reverse('menu:product', kwargs={'product_slug': self.slug})



class ProductImage(models.Model):
    """
    Lie un Produit à une Image de la Galerie.
    Définit l'ordre et si c'est l'image principale.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="Продукт")
    gallery_image = models.ForeignKey(GalleryImage, on_delete=models.CASCADE, related_name='product_links', verbose_name="Изображение из галереи", null=True, blank=True,)
    alt_text = models.CharField("Alt текст (для SEO)", max_length=255, blank=True)
    order = models.PositiveIntegerField("Порядок", default=0, db_index=True)
    is_main = models.BooleanField("Основное изображение", default=False, help_text="Если отмечено, это изображение будет использоваться как главное для продукта.")

    class Meta:
        ordering = ['order']
        verbose_name = "Изображение продукта"
        verbose_name_plural = "Изображения продуктов"

    @property
    def image(self):
        """
        Propriété pour accéder facilement à l'objet ImageField de la galerie.
        Permet de garder une compatibilité avec l'ancien code (ex: `product_image.image.url`).
        """
        if self.gallery_image:
            return self.gallery_image.image
        return None

    def clean(self):
        """ La méthode 'clean' reste identique et fonctionnelle. """
        super().clean()
        if self.is_main and self.product_id:
            other_main_images = ProductImage.objects.filter(
                product_id=self.product_id, 
                is_main=True
            ).exclude(pk=self.pk)
            if other_main_images.exists():
                raise ValidationError("Для этого продукта уже установлено основное изображение.")

    def save(self, *args, **kwargs):
        """
        La méthode 'save' est maintenant beaucoup plus simple.
        Plus besoin de traiter l'image ici, car c'est géré par la Galerie.
        """
        self.clean()
        super().save(*args, **kwargs)


class ProductFilialData(models.Model):
    """
    Хранит данные, специфичные для каждого филиала (цена, остатки).
    Создается только для переопределения базовых значений продукта.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="filial_data", verbose_name="Продукт")
    filial = models.ForeignKey(Filial, on_delete=models.CASCADE, related_name="product_data", verbose_name="Филиал")
    price = models.DecimalField("Цена для филиала", max_digits=10, decimal_places=2, null=True, blank=True, help_text="Оставьте пустым, чтобы использовать цену родительского филиала или базовую цену.")
    is_available = models.BooleanField("В наличии (для филиала)", default=True)

    class Meta:
        unique_together = ('product', 'filial')
        verbose_name = "Данные продукта по филиалу"
        verbose_name_plural = "Данные продуктов по филиалам"