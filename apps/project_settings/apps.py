from django.apps import AppConfig


class ProjectSettingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.project_settings'
    verbose_name = 'Настройки проекта'

    def ready(self):
        # Importation des signaux pour qu'ils soient connectés au démarrage
        import apps.project_settings.signals
