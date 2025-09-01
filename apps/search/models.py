from django.db import models
from django.conf import settings

class SearchLog(models.Model):
    query = models.CharField("Поисковый запрос", max_length=255, db_index=True)
    search_date = models.DateTimeField("Дата поиска", auto_now_add=True)
    ip_address = models.GenericIPAddressField("IP адрес", null=True, blank=True)
    filial = models.ForeignKey('filial.Filial', on_delete=models.SET_NULL,  null=True, blank=True, verbose_name="Филиал")

    def __str__(self):
        return f"'{self.query}' at {self.search_date.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ["-search_date"]
        verbose_name = "Поисковый запрос"
        verbose_name_plural = "Поисковых запросов"