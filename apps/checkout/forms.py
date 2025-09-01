from django import forms
from django.conf import settings 
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import datetime, timezone as dt_timezone
import re
import os 
from .models import Order
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)



# Taille max en octets (5MB)
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.webp', '.gif', '.txt', '.rtf']

MIN_FORM_SUBMISSION_TIME_SECONDS = 3




class OrderCreateForm(forms.ModelForm):
    phone = forms.CharField(
        label="Телефон*", 
        required=True,
        error_messages={'required': 'Пожалуйста, введите ваш номер телефона.'},
        widget=forms.TextInput(attrs={'placeholder': '+7 999 999-99-99*'})
    )
    comment = forms.CharField(
        label="Комментарий", 
        required=False, 
        widget=forms.TextInput(attrs={'placeholder': 'Комментарий'})
    )
    file = forms.FileField(
        label="Прикрепить файл", 
        required=False
    )
    agreement = forms.BooleanField(
        required=True,
        initial=True,
        error_messages={'required': 'Вы должны согласиться на обработку персональных данных.'},
        widget=forms.HiddenInput() 
    )
    marketing_consent = forms.BooleanField(
        label="Я соглашаюсь получать информационно-рекламные материалы",
        required=False,
        initial=True
    )

    class Meta:
        model = Order
        fields = ['phone', 'comment', 'file', 'marketing_consent']

    def clean_phone(self):
        """Valide et nettoie le numéro de téléphone."""
        phone_number = self.cleaned_data.get('phone')
        if not phone_number:
            return phone_number

        # Enlève tout sauf les chiffres
        cleaned_phone = re.sub(r'\D', '', phone_number)

        # Normalise le '8' russe en '7'
        if cleaned_phone.startswith('8') and len(cleaned_phone) == 11:
            cleaned_phone = '7' + cleaned_phone[1:]

        # Valide le format (doit commencer par 7 et avoir 11 chiffres)
        russian_phone_regex = r'^7\d{10}$'
        if not re.match(russian_phone_regex, cleaned_phone):
            raise forms.ValidationError(
                _("Пожалуйста, введите действительный российский номер телефона."),
                code='invalid_phone_format'
            )
        
        # On retourne le numéro original entré par l'utilisateur, qui est plus lisible
        return phone_number

    def clean_file(self):
        """Valide la taille et l'extension du fichier uploadé."""
        file = self.cleaned_data.get('file')
        if file:
            # Validation de la taille
            if file.size > MAX_UPLOAD_SIZE_BYTES:
                max_size_mb = int(MAX_UPLOAD_SIZE_BYTES / (1024*1024))
                raise forms.ValidationError(
                    _("Файл слишком большой. Максимальный размер: %(max_size)s МБ."),
                    params={'max_size': max_size_mb},
                    code='file_too_large'
                )

            # Validation de l'extension
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise forms.ValidationError(
                    _("Недопустимое расширение файла. Разрешены: %(exts)s"),
                    params={'exts': ', '.join(ALLOWED_EXTENSIONS)},
                    code='invalid_file_extension'
                )
        return file
    




class ZakazForm(forms.ModelForm):
    # Champs visibles pour l'utilisateur
    name = forms.CharField(label="Ф.И.О", max_length=50, required=False)
    email = forms.EmailField(label="E-mail", max_length=50, required=False)
    phone = forms.CharField(label="Телефон", max_length=20, required=True)
    comment = forms.CharField(label="Комментарий", required=False, widget=forms.HiddenInput())

    #  Honeypots 
    comp_input_hidden = forms.CharField(required=False, widget=forms.HiddenInput(), label="_hp_h")
    website_url_confirm = forms.CharField(required=False, label="_hp_c")
    form_render_timestamp = forms.CharField(required=False, label="_hp_t")

    agreement = forms.BooleanField(
        required=True,
        error_messages={'required': 'Необходимо согласие.'}
    )

    marketing_consent = forms.BooleanField(
        label="Я соглашаюсь получать информационно-рекламные материалы",
        required=False,
        initial=True
    )

    class Meta:
        model = Order
        fields = ['name', 'email', 'phone', 'marketing_consent'] 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'form_render_timestamp' not in self.initial:
            self.initial['form_render_timestamp'] = str(timezone.now().timestamp())
        
    def clean_phone(self):
        phone_number = self.cleaned_data.get('phone')
        if phone_number:
            cleaned_phone = re.sub(r'\D', '', phone_number)
            if cleaned_phone.startswith('8'): cleaned_phone = '7' + cleaned_phone[1:]
            russian_phone_regex = r'^7\d{10}$'
            if not re.match(russian_phone_regex, cleaned_phone):
                raise forms.ValidationError("Неверный формат номера телефона.")
            return phone_number
        return phone_number


    def clean(self):
        cleaned_data = super().clean()
        
        honeypot1 = cleaned_data.get('comp_input_hidden') # Doit correspondre au 'name' dans HTML
        if honeypot1:
            logger.warning(f"Honeypot (comp_input_hidden / ancien 'comp_input_hidden') triggered. Value: '{honeypot1}'")
            self.add_error(None, forms.ValidationError("Обнаружена подозрительная активность (H1).", code='honeypot'))

        honeypot2 = cleaned_data.get('website_url_confirm') # Doit correspondre au 'name' dans HTML
        if honeypot2:
            logger.warning(f"Honeypot (website_url_confirm) triggered. Value: '{honeypot2}'")
            self.add_error(None, forms.ValidationError("Обнаружена подозрительная активность (H2).", code='honeypot'))

        render_timestamp_str = cleaned_data.get('form_render_timestamp') # Doit correspondre au 'name' dans HTML
        if render_timestamp_str:
            try:
                # render_time = datetime.fromtimestamp(float(render_timestamp_str), tz=timezone.utc)
                render_time = datetime.fromtimestamp(float(render_timestamp_str), tz=dt_timezone.utc)
                submission_time = timezone.now()
                time_diff_seconds = (submission_time - render_time).total_seconds()

                if time_diff_seconds < 0: 
                    logger.warning(f"Honeypot (time-based) < 0. Diff: {time_diff_seconds}s")
                    self.add_error(None, forms.ValidationError("Ошибка времени отправки формы.", code='honeypot_time_negative'))
                elif time_diff_seconds < MIN_FORM_SUBMISSION_TIME_SECONDS:
                    logger.warning(f"Honeypot (time-based) too fast. Time: {time_diff_seconds:.2f}s")
                    self.add_error(None, forms.ValidationError("Форма отправлена слишком быстро.", code='honeypot_time_too_fast'))
                else:
                    logger.debug(f"Form submission time ok: {time_diff_seconds:.2f}s")
            except ValueError:
                logger.warning("Honeypot (time-based) error: Invalid timestamp format.")
                self.add_error(None, forms.ValidationError("Ошибка данных формы (времени).", code='honeypot_time_invalid'))
        else:
            logger.warning("Honeypot (time-based) failed: form_render_timestamp missing.")
            self.add_error(None, forms.ValidationError("Отсутствует временная метка формы.", code='honeypot_time_missing'))
        
        return cleaned_data