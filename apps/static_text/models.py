from django.db import models
from django_ckeditor_5.fields import CKEditor5Field


class StaticText(models.Model):
	slug = models.SlugField(max_length=500, verbose_name="Латинское название [системное]")
	text = CKEditor5Field(config_name='extends', verbose_name="HTML текст", blank=True, null=True, default="")
	comment = models.CharField(max_length=500, verbose_name="Комментарий", blank=True, null=True, default="")
	
	def __str__(self):
		return self.slug
	
	class Meta:
		ordering = ["id"]
		verbose_name = "Статический текст"
		verbose_name_plural = "Статические тексты"