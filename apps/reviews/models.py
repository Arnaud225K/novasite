from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator





class Review(models.Model):
    name = models.CharField("Имя", max_length=100)
    surname = models.CharField("Фамилия", max_length=100, blank=True)
    order_number = models.PositiveIntegerField("Порядок", default=100)
    avatar = models.ImageField("Аватар", upload_to='avatars/', null=True, blank=True)
    rating = models.PositiveSmallIntegerField("Рейтинг", default=5, validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField("Текст отзыва")
    is_hidden = models.BooleanField("Скрыть", default=False, db_index=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    def __str__(self):
        return f"Отзыв от {self.name} {self.surname}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"