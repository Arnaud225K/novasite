from django.db import models
from django.conf import settings
from django.utils.html import format_html

def import_export_log_path(instance, filename):
    """
    Définit le chemin de stockage pour les fichiers de log, en les organisant
    par type d'action (import/export) et par date.
    Exemple: logs/imports/2025/08/mon_fichier.xlsx
    """
    action_folder = 'imports' if instance.action == instance.ACTION_IMPORT else 'exports'
    return f'logs/{action_folder}/{instance.timestamp.strftime("%Y/%m")}/{filename}'

class ImportExportLog(models.Model):
    ACTION_EXPORT = 'EXPORT'
    ACTION_IMPORT = 'IMPORT'
    ACTION_CHOICES = [
        (ACTION_EXPORT, 'Экспорт'),
        (ACTION_IMPORT, 'Импорт'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,null=True, verbose_name="Пользователь")
    action = models.CharField("Действие", max_length=10, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField("Дата и время", auto_now_add=True)
    file_name = models.CharField("Имя файла", max_length=255, blank=True, null=True)
    file = models.FileField("Файл", upload_to=import_export_log_path, null=True, blank=True)
    details = models.JSONField("Детали", default=dict, help_text="Контекст, такой как категория, количество строк и т.д.")
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Журнал имп/эксп"
        verbose_name_plural = "Журналы имп/эксп"

    def __str__(self):
        return f"{self.get_action_display()} by {self.user} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"