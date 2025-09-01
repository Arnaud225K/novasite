import os
from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from django.urls import reverse
from django.utils.text import slugify
from unidecode import unidecode
from django_ckeditor_5.fields import CKEditor5Field
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from apps.utils.image_utils import process_and_convert_image

from .managers import MenuCatalogManager 




class TypeMenu(models.Model):
    """
    Определяет тип элемента каталога, чтобы фронтенд знал,
    какой компонент страницы отображать.
    """
    name = models.CharField("Название типа", max_length=256)
    template = models.CharField(max_length=724, verbose_name="Название файла шаблона")
    identifier = models.SlugField("Идентификатор", max_length=100, unique=True, help_text="Короткий ключ для использования (напр., 'catalog', 'product')")
    created_at = models.DateTimeField(verbose_name='Создано', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='Обновлено', auto_now=True)


    def __str__(self):
        return self.name

    class Meta:
        ordering = ["id"]
        verbose_name = "Тип меню"
        verbose_name_plural = "Типы меню"





class MenuCatalog(MPTTModel):
    """
    Иерархическая модель для каталога меню, категорий продуктов,
    сервисных страниц и т.д.
    """
    name = models.CharField("Название пункта", max_length=255, db_index=True)
    slug = models.SlugField("URL-ключ (слаг)", max_length=255, unique=True, db_index=True, blank=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name="Родительский пункт")
    type_menu = models.ForeignKey(TypeMenu, verbose_name="Тип меню", on_delete=models.PROTECT, related_name="catalogs")
    image = models.ImageField("Картинка", upload_to='uploads/catalog/', blank=True, null=True)
    description = CKEditor5Field(config_name="extends", verbose_name="Описание", blank=True, null=True)
    applicable_filters = models.ManyToManyField("products.FilterCategory",verbose_name="Применимые категории фильтров", blank=True, help_text="Выберите, какие группы фильтров будут отображаться для товаров в этой категории.")
    order_number = models.PositiveIntegerField("Порядок", default=100)
    is_hidden = models.BooleanField("Скрыть", default=False, db_index=True)
    is_show_main = models.BooleanField(verbose_name="Отображать на главной", default=False)
    show_footer_left = models.BooleanField(verbose_name="Показывать в подвале (левый столбец)", default=False, help_text="Отметьте, чтобы этот пункт появился в подвале (левый столбец) сайта.")
    show_footer_rigth = models.BooleanField(verbose_name="Показывать в подвале (правый столбец)", default=False, help_text="Отметьте, чтобы этот пункт появился в подвале (правый столбец) сайта.")
    is_show_in_header = models.BooleanField("Показывать в верхнем меню",default=False, help_text="Отметьте, чтобы этот пункт появился в выпадающем меню в шапке сайта.")
    show_descendants_products = models.BooleanField(
        "Показывать товары из подкатегорий",
        default=True,
        help_text="Если отмечено, на этой странице будут отображаться товары из всех вложенных подкатегорий. Снимите галочку, чтобы показывать только товары, напрямую связанные с этой категорией."
    )    
    seo_title = models.CharField("SEO Заголовок (Title)", max_length=255, blank=True)
    seo_description = models.TextField("SEO Описание (Description)", blank=True)
    seo_keywords = models.TextField(verbose_name="Ключевые слова (мета)", blank=True, null=True)
    created_at = models.DateTimeField(verbose_name='Создано', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='Обновлено', auto_now=True)

    
    objects = MenuCatalogManager()

    class MPTTMeta:
        order_insertion_by = ['order_number', 'created_at', 'name']


    class Meta:
        ordering = ["order_number"]
        verbose_name = "Меню/Каталог"
        verbose_name_plural = "Меню/Каталог"


    def __str__(self):
        # Affiche le chemin complet dans l'admin pour plus de clarté
        return ' → '.join([ancestor.name for ancestor in self.get_ancestors(include_self=True)])
    

    def get_hierarchical_path(self):
        """
        Méthode HELPER qui construit la chaîne de slugs hiérarchique.
        Exemple de retour : "catalog/trubnyj-prokat/truba-profilnaya"
        """
        # get_ancestors inclut les parents jusqu'à la racine MPTT, puis l'objet lui-même.
        ancestors = self.get_ancestors(include_self=True)
        return '/'.join([cat.slug for cat in ancestors])

    def get_absolute_url(self):
        """
        La méthode OFFICIELLE de Django.
        Utilise le chemin hiérarchique pour construire une URL complète et correcte.
        Retourne : "/catalog/trubnyj-prokat/truba-profilnaya/"
        """
        # On appelle notre helper pour obtenir le chemin
        path = self.get_hierarchical_path()
        
        # On utilise 'reverse' pour trouver la bonne URL en se basant sur le nom
        # que nous avons donné dans urls.py ('menu_catalog').
        return reverse('menu:menu_catalog', kwargs={'hierarchical_slug': path})


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(unidecode(self.name))

        process_this_image = False
        try:
            original = MenuCatalog.objects.get(pk=self.pk)
            if self.image != original.image:
                process_this_image = True
        except MenuCatalog.DoesNotExist:
            if self.image:
                process_this_image = True

        if process_this_image and self.image:
            self.image = process_and_convert_image(self.image, max_size=(500, 340))

        super().save(*args, **kwargs)
    


class MenuCatalogFilialVisibility(models.Model):
    """
    Определяет правила видимости для категорий каталога в конкретных филиалах.
    По умолчанию, все категории видны везде. Запись в этой таблице означает,
    что категория (и все ее дочерние элементы) будет СКРЫТА.
    """
    category = models.ForeignKey(
        MenuCatalog,
        on_delete=models.CASCADE,
        related_name="filial_visibility_rules",
        verbose_name="Категория каталога"
    )
    filial = models.ForeignKey(
        'filial.Filial',
        on_delete=models.CASCADE,
        related_name="hidden_categories",
        verbose_name="Филиал"
    )
    is_hidden = models.BooleanField(
        "Скрыть в этом филиале",
        default=True,
        help_text="Если отмечено, эта категория и все ее подкатегории будут скрыты в указанном филиале."
    )
    class Meta:
        unique_together = ('category', 'filial')
        verbose_name = "Видимость категории"
        verbose_name_plural = "Видимость категории."

    def __str__(self):
        return f"Категория '{self.category.name}' скрыта в филиале '{self.filial.name}'"