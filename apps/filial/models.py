from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Fonction de validation pour s'assurer qu'une seule filiale est par défaut
def validate_only_one_default(obj):
    if obj.is_default:
        defaults_exist = Filial.objects.filter(is_default=True).exclude(pk=obj.pk).exists()
        if defaults_exist:
            raise ValidationError({
                'is_default': _('Только один филиал может быть основным (без поддомена). Пожалуйста, снимите этот флажок с другого филиала перед сохранением.')
            })

class Filial(models.Model):
    """
    Модель для управления филиалами, городами и регионами.
    Поддерживает иерархию (главный филиал -> дочерний) и
    один основной филиал для сайта без поддомена.
    """
    name = models.CharField("Название", max_length=100, help_text="Например, 'Москва'.")
    name_info = models.CharField("Название (падеж для подстановки)",max_length=100, blank=True, null=True)
    region = models.CharField("Область", max_length=100, blank=True, null=True)
    parent = models.ForeignKey('self', verbose_name="Основной (родительский) филиал", on_delete=models.SET_NULL, blank=True, null=True, related_name='children', help_text="Выберите главный филиал.")
    order_number = models.FloatField("Порядок", default=100.0, help_text="Чем меньше число, тем выше в списке.")
    is_hidden = models.BooleanField("Скрыть", default=False, db_index=True, help_text="Отключите, чтобы скрыть филиал со всего сайта.")
    subdomain = models.CharField("Поддомен", max_length=100, unique=True, db_index=True, help_text="Например, 'sp' для sp.kzmc.kz")
    is_default = models.BooleanField("Основной сайт (без поддомена)", default=False, db_index=True, help_text="Отметьте для филиала, который будет отображаться на основном домене.")
    phone = models.CharField("Телефон", max_length=50, blank=True)
    phone_dop = models.CharField("Телефон (дополнительный)", max_length=50, blank=True, null=True)
    email = models.EmailField("Электронная почта", max_length=254, blank=True)
    address = models.CharField("Адрес", max_length=256, blank=True)
    working_hours = models.CharField("Режим работы", max_length=1024, blank=True, null=True)
    full_name_req = models.CharField("Полное наименование предприятия", max_length=256, blank=True)
    short_name_req = models.CharField("Краткое наименование предприятия", max_length=256, blank=True)
    inn_req = models.CharField(verbose_name="ИНН", max_length=100,blank=True, null=True)
    kpp_req = models.CharField(verbose_name="КПП",max_length=100, blank=True, null=True)
    bin_req = models.CharField(verbose_name="БИН (КЗ)",max_length=100, blank=True, null=True)
    ikk_1_req = models.CharField(verbose_name="ИКК 1 (КЗ)",max_length=100, blank=True, null=True)
    ikk_2_req = models.CharField(verbose_name="ИКК 2 (КЗ)", max_length=100, blank=True, null=True)
    yr_address_req = models.CharField(verbose_name="Юридический адрес", max_length=256, blank=True, null=True)
    fact_address_req = models.CharField(verbose_name="Фактический адрес",max_length=256, blank=True, null=True)
    phone_req = models.CharField(verbose_name="Телефон (реквизиты)",max_length=256, blank=True, null=True)
    email_req = models.CharField(verbose_name="Электронная почта (реквизиты)",max_length=256, blank=True, null=True)
    okved_req = models.CharField(verbose_name="ОКВЭД", max_length=100, blank=True, null=True)
    okpo_req = models.CharField(verbose_name="ОКПО", max_length=100, blank=True, null=True)
    okato_req = models.CharField(verbose_name="ОКАТО", max_length=100, blank=True, null=True)
    okfs_req = models.CharField(verbose_name="ОКФС", max_length=100, blank=True, null=True)
    okopf_req = models.CharField(verbose_name="ОКОПФ", max_length=100, blank=True, null=True)
    bank_req = models.CharField(verbose_name="Банк", max_length=256, blank=True, null=True)
    bik_req = models.CharField(verbose_name="БИК", max_length=100, blank=True, null=True)
    chet_req = models.CharField(verbose_name="Расчетный счет", max_length=100, blank=True, null=True)
    korr_chet_req = models.CharField(verbose_name="Коректирующий счет", max_length=100, blank=True, null=True)
    nalog_req = models.CharField(verbose_name="Постановка в налоговый учет", max_length=256, blank=True, null=True)
    reg_req = models.CharField(verbose_name="Госрегистрация", max_length=256, blank=True, null=True)
    ogrn_req = models.CharField(verbose_name="ОГРН", max_length=100, blank=True, null=True)
    oktmo_req = models.CharField(verbose_name="ОКТМО", max_length=100, blank=True, null=True)
    director_req = models.CharField(verbose_name="Директор (на основании устава)", max_length=100, blank=True, null=True)
    requisites_file = models.FileField("Файл с реквизитами", upload_to='filials/requisites/', blank=True, null=True)
    map_code = models.TextField("Код карты проезда", blank=True, help_text="HTML-код для вставки карты, например, с Яндекс.Карт.")
    seo_text_head = models.TextField("Блок в <head> для филиала", blank=True, help_text="Дополнительные скрипты или мета-теги, которые будут добавлены в <head>.")
    seo_text_body = models.TextField("Блок в <body> для филиала", blank=True,help_text="Дополнительные скрипты, которые будут добавлены в конце <body>.")
    is_base = models.BooleanField(verbose_name="Популярные города", blank=True,  default=False)
    homepage_offer_collection = models.ForeignKey(
        'offers.OfferCollection',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='homepage_for_filials',
        verbose_name="Коллекция спецпредложений",
        help_text="Выберите коллекцию спецпредложений, которая будет отображаться на главной странице этого филиала."
    )


    def clean(self):
        validate_only_one_default(self)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["order_number"]
        verbose_name = "Филиал"
        verbose_name_plural = "Филиалы (Города)"
