from django.urls import include, path, re_path
from . import views

app_name = 'checkout'

urlpatterns = [
    path('', views.CheckoutView.as_view(), name='checkout_page'),
    path('order/created/<uuid:order_key>/', views.order_created_view, name='order_created'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('cart/update/<int:product_id>/', views.cart_update_quantity, name='cart_update'),

    # --- URLs zayvka ---
    path('send_form_order/', views.SendFormOrder.as_view(), name='send_form_order'),
    path('thank-you/', views.ThankYouView.as_view(), name='thank-you'),
    path('generic-error/', views.GenericErrorView.as_view(), name='generic-error'),

]