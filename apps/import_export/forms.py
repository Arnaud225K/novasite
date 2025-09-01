from django import forms
from apps.menu.models import MenuCatalog
from apps.products.models import FilterCategory
import os


PRODUCT_CATEGORY_TYPE_IDS = [7, 8]

# On importe les widgets Select2
try:
    from django_select2.forms import Select2Widget, Select2MultipleWidget
except ImportError:
    Select2Widget = forms.Select
    Select2MultipleWidget = forms.SelectMultiple


class AdminExportByCategoryForm(forms.Form):
    """
    Formulaire pour la page de configuration de l'export.
    Permet à l'administrateur de choisir une catégorie de produits.
    """
    category = forms.ModelChoiceField(
        # On ne propose que les catégories qui peuvent contenir des produits
        queryset=MenuCatalog.objects.filter(is_hidden=False, type_menu_id__in=PRODUCT_CATEGORY_TYPE_IDS).order_by('order_number'),
        label="Категория продуктов для экспорта",
        required=True,
        widget=Select2Widget(attrs={
            'data-placeholder': 'Выберите категорию...',
            'style': 'width: 100%;'
        }),
        empty_label=None
    )
    
    filter_categories_to_export = forms.ModelMultipleChoiceField(
        queryset=FilterCategory.objects.order_by('order', 'name'),
        label="Включить дополнительные колонки фильтров",
        required=False,
        widget=Select2MultipleWidget(attrs={
            'data-placeholder': 'Выберите фильтры для добавления в файл...',
            'style': 'width: 100%;'
        }),
        help_text="Фильтры, уже используемые в выбранной категории, будут добавлены автоматически."
    )


class AdminImportFileForm(forms.Form):
    """
    Formulaire simple pour l'upload d'un fichier Excel.
    Valide l'extension du fichier.
    """
    file = forms.FileField(
        label="Выберите файл Excel (.xlsx)",
        required=True,
        widget=forms.FileInput(attrs={'accept': '.xlsx'})
    )

    def clean_file(self):
        """
        Validation personnalisée pour s'assurer que le fichier est bien un .xlsx.
        """
        uploaded_file = self.cleaned_data.get('file')
        
        if uploaded_file:
            # On vérifie l'extension du fichier
            ext = os.path.splitext(uploaded_file.name)[1]
            if ext.lower() != '.xlsx':
                raise forms.ValidationError("Неверный формат файла. Пожалуйста, загрузите файл .xlsx.")
        
        return uploaded_file