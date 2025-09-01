from django.db import models
from django.core.exceptions import ValidationError
from django.urls import reverse
from apps.products.models import Product 
from apps.filial.models import Filial
from .managers import OfferCollectionManager

class OfferCollection(models.Model):
    """
    Une collection d'offres spéciales, directement liée à des filiales.
    La logique d'affichage est en cascade (fallback).
    """
    name = models.CharField("Название коллекции", max_length=255)
    slug = models.SlugField( "Ключ для URL", max_length=100, unique=True, help_text="Уникальный ключ для использования в коде и URL (напр., 'homepage-offers')")
    is_hidden = models.BooleanField("Скрыть", default=False, db_index=True, help_text="Скрыть коллекцию со всего сайта.")
    filials = models.ManyToManyField(Filial, related_name='offer_collections', verbose_name="Филиалы", blank=True, help_text="Выберите филиалы, в которых будет отображаться эта коллекция")
    description = models.TextField("Описание", blank=True, help_text="Внутреннее описание для администраторов.")
    is_default_collection = models.BooleanField("Коллекция по умолчанию",default=False, help_text="Отметьте, если эта коллекция должна использоваться по умолчанию.")
    objects = OfferCollectionManager()

    class Meta:
        verbose_name = "коллекция/Продукт"
        verbose_name_plural = "Коллекции/Продукты"
        ordering = ['name']

    def __str__(self):
        return self.name

    def clean(self):
        """
        Garantit qu'une seule collection peut être marquée comme 'par défaut'.
        Cette méthode est appelée automatiquement par l'admin Django.
        """
        if self.is_default_collection:
            # On cherche si une autre collection (en excluant l'objet actuel)
            # est déjà marquée comme par défaut.
            qs = OfferCollection.objects.filter(is_default_collection=True).exclude(pk=self.pk)
            if qs.exists():
                # Si on trouve une autre collection, on lève une erreur de validation.
                raise ValidationError(
                    "Коллекция по умолчанию уже существует. Пожалуйста, снимите отметку с другой коллекции перед сохранением."
                )
        super().clean()

    def get_absolute_url(self):
        """
        Retourne l'URL canonique pour une instance de cette collection.
        Utilisée par l'admin et les templates.
        """
        return reverse('menu:offer_collection_detail', kwargs={'slug': self.slug})
    # --------------------------------



class SpecialOfferItem(models.Model):
    """
    Un produit spécifique à l'intérieur d'une collection d'offres.
    Ce modèle définit l'ordre d'affichage.
    """
    collection = models.ForeignKey( OfferCollection, on_delete=models.CASCADE, related_name="items", verbose_name="Коллекция")
    product = models.ForeignKey( Product, on_delete=models.CASCADE, related_name="special_offers", verbose_name="Продукт")
    order_number = models.PositiveIntegerField("Порядок", default=100, help_text="Чем меньше число, тем выше позиция.")

    class Meta:
        ordering = ['order_number']
        unique_together = ('collection', 'product')
        verbose_name = "Спецпредложение"
        verbose_name_plural = "Спецпредложения"

    def __str__(self):
        # return f"{self.product.title} в коллекции '{self.collection.name}'"
        return self.product.title