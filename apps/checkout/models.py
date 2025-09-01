from django.db import models
from apps.products.models import Product
from apps.filial.models import Filial
from decimal import Decimal
import uuid

class Order(models.Model):
	
    # --- TYPE DE DEMANDE ---
	TYPE_CART = 'cart'
	TYPE_CALLBACK = 'callback'
	TYPE_CONSULTATION = 'consultation'
	TYPE_PRICE_REQUEST = 'price_request'
	TYPE_SERVICE_REQUEST = 'service_request'
	ORDER_TYPE_CHOICES = [
		(TYPE_CART, 'Заявка из корзины'),
		(TYPE_CALLBACK, 'Заказ обратного звонка'),
		(TYPE_CONSULTATION, 'Запрос консультации'),
		(TYPE_PRICE_REQUEST, 'Запрос цены'),
		(TYPE_SERVICE_REQUEST, 'Заказ услуги'),
	]

	order_key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
	order_type = models.CharField("Тип заявки", max_length=20, choices=ORDER_TYPE_CHOICES, default=TYPE_CART)
	name = models.CharField("Имя / Ф.И.О.", max_length=100)
	phone = models.CharField("Телефон", max_length=20)
	email = models.EmailField("E-mail", max_length=254, blank=True, null=True)
	comment = models.TextField("Комментарий / Текст заявки", blank=True, null=True)
	file = models.FileField(upload_to='order_files/%Y/%m/', verbose_name="Прикрепленный файл", blank=True, null=True)
	text = models.CharField("Текст", max_length=255, blank=True, null=True)
	total_cost = models.DecimalField("Общая стоимость", max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Заполняется только для заявок из корзины")
	ip_address = models.GenericIPAddressField("IP адрес", null=True, blank=True)
	filial = models.ForeignKey(Filial, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Филиал")
	marketing_consent = models.BooleanField("Согласие на рекламу", default=False)
	created_at = models.DateTimeField("Создано", auto_now_add=True)
	updated_at = models.DateTimeField("Обновлено", auto_now=True)

	class Meta:
		ordering = ('-created_at',)
		verbose_name = "Заявка"
		verbose_name_plural = "Все заявки"

	def __str__(self):
		return f"Заявка №{self.id}"

	def calculate_total_cost(self):
		"""Calcule et met à jour le coût total basé sur les articles liés."""
		total = self.items.aggregate(
			total=models.Sum(models.F('price') * models.F('quantity'))
		)['total'] or Decimal('0.00')
		self.total_cost = total
		self.save(update_fields=['total_cost', 'updated_at'])

	def has_non_fixed_price(self):
		"""
		Vérifie si la commande contient au moins un article dont le prix
		n'était pas fixe (soit négociable, soit "à partir de").
		"""
		return self.items.filter(
			models.Q(price=0) | models.Q(price_type=Product.PRICE_TYPE_FROM)
		).exists()


class OrderItem(models.Model):
	order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name="Заявка")
	product = models.ForeignKey(Product, related_name='order_items', on_delete=models.SET_NULL, null=True, blank=True)
	product_title = models.CharField("Название товара", max_length=255)
	price = models.DecimalField("Цена за единицу", max_digits=12, decimal_places=2)
	quantity = models.PositiveIntegerField("Количество", default=1)
	price_type = models.CharField("Тип цены", max_length=10, choices=Product.PRICE_TYPE_CHOICES, default=Product.PRICE_TYPE_FIXED)


	def get_cost(self):
		"""
		Calcule le coût de cette ligne d'article.
		Version corrigée pour gérer le cas où le prix est None.
		"""
		price = self.price or Decimal('0.00')
		
		quantity = self.quantity or 0
		
		return price * quantity

	def __str__(self):
		# return str(self.id)
		return f"Заказ №{self.id}"
