from django.urls import path
from . import views

app_name = 'import_export'

urlpatterns = [
    path('product-export/', views.ProductExportSetupView.as_view(), name='product_export_setup'),
    path('product-export/download/', views.ProductExportDownloadView.as_view(), name='product_export_download'),
    path('product-import/', views.ProductImportView.as_view(), name='product_import'),
    path('product-import/process/', views.ProductImportProcessView.as_view(), name='product_import_process'),
    path('ajax/get-relevant-filters/<int:category_id>/', views.ajax_get_relevant_filters, name='ajax_get_relevant_filters'),
]