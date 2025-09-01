from django.contrib import admin
from .models import GalleryImage
from apps.utils.utils import get_admin_product_image_thumbnail_html




@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('copyable_path', 'display_product_image', 'title', 'uploaded_at')
    readonly_fields = ('display_product_image', 'copyable_path')
    search_fields = ('title', 'image')

    fieldsets = (
        (None, {
            'fields': ('title', 'image', 'display_product_image', 'copyable_path')
        }),
    )

    def save_model(self, request, obj, form, change):

        if not change:
            files = request.FILES.getlist('image')
            for a_file in files:
                
                new_obj = GalleryImage()
                new_obj.image = a_file
                new_obj.title = a_file.name

                new_obj.save()
        else:
            super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        """
        Modifie le widget du champ 'image' pour autoriser la sélection multiple à la création.
        """
        form = super().get_form(request, obj, **kwargs)
        if obj is None:
            form.base_fields['image'].widget.attrs.update({
                'multiple': 'multiple'
            })
        return form

    def display_product_image(self, obj):
        return get_admin_product_image_thumbnail_html(obj, image_field_name='image', alt_text_base="Продукт")
    display_product_image.short_description = 'Картинка'
