from django.urls import path , re_path

from django.views.decorators.cache import cache_page
from . import views

app_name = 'menu'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    # path('catalog/', views.CatalogIndexView.as_view(), name='catalog_index'),
    # path('api/filter-values/<slug:filter_category_slug>/', views.LoadMoreFilterValuesAPIView.as_view(), name='api_load_more_filter_values'),
    path('ajax/get-mega-menu/', views.AjaxMegaMenuView.as_view(), name='ajax_get_mega_menu'),
    # path('api/get-more-children/<int:category_id>/', views.get_more_children_api, name='api_get_more_children'),
    # URLS MODIFIÉES AVEC re_path
    path('offers/<slug:slug>/', views.OfferCollectionDetailView.as_view(), name='offer_collection_detail'),
    path('product/<str:product_slug>/', views.ProductView.as_view(), name='product'),
    re_path(r'^api/filter/(?P<hierarchical_slug>[\w\/-]+)/(?P<filter_segment>f\/.*)$', views.FilterProductsAPIView.as_view(), name='api_filter_products_with_segment'),
    path('api/filter/<path:hierarchical_slug>/', views.FilterProductsAPIView.as_view(), name='api_filter_products'),
    re_path(r'^(?P<hierarchical_slug>[\w\/-]+)/(?P<filter_segment>f\/.*)$', views.MenuView.as_view(), name='menu_catalog_with_filters'),
    path('<path:hierarchical_slug>/', views.MenuView.as_view(), name='menu_catalog'),
]