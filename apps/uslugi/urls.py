from django.urls import path
from . import views

app_name = 'uslugi'

urlpatterns = [
    path('', views.UslugiListView.as_view(), name='uslugi_list'),
    
    path('<slug:slug>/', views.UslugiDetailView.as_view(), name='uslugi_detail'),
]