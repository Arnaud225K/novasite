"""
URL configuration for novator project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve
# from filials.views import RobotsView
# from apps.project_settings.views import ProjectSettingsViewSet
from . import settings
import os
from django.conf.urls.static import static
from .settings import SITE_NAME
# from .views import page404, page500
# from .views import page404, page500
import logging

logger = logging.getLogger(__name__)

#Custom admin site
admin.site.site_header = SITE_NAME
admin.site.site_title = SITE_NAME


# handler404 = page404
# handler500 = page500


urlpatterns = [
    path('novadmin/', admin.site.urls),
]

#Activate debug toolbar url
if settings.DEBUG:
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]

urlpatterns += [
    # --- CUSTOM APP URL ---
    # path('robots.txt', RobotsView.as_view(), name='robot'),
    # path('sitemap_gen/', include('sitemap_gen.urls')),
    path('search/', include('apps.search.urls', namespace='search')),
    path('select2/', include('django_select2.urls')),
    path('import-export/', include('apps.import_export.urls', namespace='import_export')),
    path('uslugi/', include('apps.uslugi.urls', namespace='uslugi')),
    path('articles/', include('apps.articles.urls', namespace='articles')),
    path('checkout/', include('apps.checkout.urls')),
    path('',include('apps.menu.urls')),
    # --- CUSTOM LIBRARY URL ---
    path("ckeditor5/", include('django_ckeditor_5.urls')),
]

#Serve static files
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)	
urlpatterns += [
        re_path(r'media/(?P<path>.*)$', serve, {'document_root': settings.WWW_ROOT}),
    ]

if hasattr(settings, 'WWW_ROOT') and settings.WWW_ROOT and os.path.isdir(settings.WWW_ROOT):
    sitemap_root_pattern = r'^(?P<path>sitemap(?:_[\w\.-]*)?\.xml(?:\.gz)?)$'
    # logger.info(f"Serving sitemap files from {settings.WWW_ROOT} with pattern {sitemap_root_pattern}")
    urlpatterns += [
        re_path(sitemap_root_pattern, serve, {'document_root': settings.WWW_ROOT}),
    ]
else:
    logger.warning(f"Settings.WWW_ROOT ('{getattr(settings, 'WWW_ROOT', 'Not Set')}') is not a valid directory. Sitemaps at root won't be served by runserver.")