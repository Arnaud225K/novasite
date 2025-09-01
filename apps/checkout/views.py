
import json
import logging
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.template.loader import render_to_string

from apps.products.models import Product
from .cart import CartManager
from .forms import OrderCreateForm, ZakazForm
from .models import Order, OrderItem

from apps.menu.templatetags.catalog_tags import format_price
from .tasks import send_order_notification_task

logger = logging.getLogger(__name__)




# FONCTION HELPER POUR LES RÉPONSES API

def _get_display_price_string(price_value, price_type):
    price_decimal = Decimal(price_value or '0')
    if price_decimal == 0:
        return "Договорная"
    prefix = "от " if price_type == Product.PRICE_TYPE_FROM else ""
    formatted_price = format_price(price_decimal)
    return f"{prefix}{formatted_price} ₽"
    


def _prepare_cart_api_response(cart, request):
    """
    Fonction centralisée pour construire une réponse JSON cohérente pour le panier.
    """
    cart_total_price = cart.get_total_price()
    if cart_total_price is None:
        cart_total_price_display = "Договорная"
    else:
        cart_total_price_display = f"{format_price(cart_total_price)} ₽"

    context = {
        'cart': cart, 
        'request': request
    }

    html_cart_items = render_to_string('includes/partials/_cart_items_list.html', context, request=request)

    return {
        'cart_unique_items_count': len(cart.cart),
        'cart_total_price_display': cart_total_price_display,
        'html_cart_items': html_cart_items,
    }


# VUE PRINCIPALE DU PANIER ET DE LA COMMANDE

class CheckoutView(View):
    template_name = 'checkout/p-checkout.html'
    form_class = OrderCreateForm

    def get(self, request, *args, **kwargs):
        cart = CartManager(request)
        form = self.form_class()

        context = {
            'cart': cart,
            'form': form,
            'is_cart_page': True,
        }

        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        cart = CartManager(request)
        if not cart.cart:
            return redirect('checkout:cart')

        form = self.form_class(request.POST, request.FILES)

        if form.is_valid():
            order = form.save(commit=False)
            order.filial = request.filial
            order.ip_address = request.META.get('REMOTE_ADDR')
            order.save()

            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    product_title=item['product'].full_title,
                    price=Decimal(item['price']),
                    quantity=item['quantity'],
                    price_type=item.get('price_type', Product.PRICE_TYPE_FIXED)
                )
            
            order.calculate_total_cost()
            cart.clear()


            # --- APPEL DE LA TÂCHE CELERY ---
            try:
                send_order_notification_task.delay(order.id)
                logger.info(f"Celery task queued for Order ID: {order.id} (from Simple Cart)")
            except Exception as e_celery_task:
                logger.error(f"Failed to queue Celery task for Zakaz {order.id}: {e_celery_task}", exc_info=True)
            # # =========================================

            
            return redirect(reverse('checkout:order_created', args=[order.order_key]))

        context = {
            'cart': cart,
            'form': form,
            'is_cart_page': True,
        }

        return render(request, self.template_name, context)        

# VUE DE CONFIRMATION
def order_created_view(request, order_key):
    order = get_object_or_404(Order, order_key=order_key)
    return render(request, 'checkout/order_created.html', {'order': order})


# VUES AJAX POUR LA GESTION DU PANIER
@require_POST
def cart_add(request, product_id):
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

    cart = CartManager(request)
    try:
        product = Product.objects.get(id=product_id, is_hidden=False)
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Товар не найден'}, status=404)

    try:
        data = json.loads(request.body.decode('utf-8'))
        quantity_to_add = int(data.get('quantity', 1))
    except (json.JSONDecodeError, ValueError):
        quantity_to_add = 1

    cart.add(product=product, quantity=quantity_to_add, update_quantity=False)
    
    response_data = _prepare_cart_api_response(cart, request)
    response_data['success'] = True
    response_data['message'] = 'Товар добавлен в корзину!'
    response_data['product_id'] = product.id # JSON-safe
    
    return JsonResponse(response_data)

@require_POST
def cart_update_quantity(request, product_id):
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

    cart = CartManager(request)
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found'}, status=404)
        
    try:
        data = json.loads(request.body.decode('utf-8'))
        quantity = int(data.get('quantity'))
        max_quantity = getattr(settings, 'CART_ITEM_MAX_QUANTITY', 1000)
        quantity = min(max(0, quantity), max_quantity)
        action = 'updated' if quantity > 0 else 'removed'
        
        if quantity > 0:
            cart.add(product=product, quantity=quantity, update_quantity=True)
        else:
            cart.remove(product)

        

        # On utilise le helper pour la réponse de base
        response_data = _prepare_cart_api_response(cart, request)
        response_data['success'] = True
        response_data['action'] = action
        
        # On ajoute le prix de l'article spécifique, qui est une chaîne (JSON-safe)
        item_total_price_display = "0 ₽"
        item_data = cart.cart.get(str(product_id))
        if action == 'updated' and item_data:
            item_price = Decimal(item_data.get('price', '0'))
            item_type = item_data.get('price_type', Product.PRICE_TYPE_FIXED)
            item_quantity = item_data.get('quantity', 0)
            item_total_price_display = _get_display_price_string(item_price * item_quantity, item_type)
        
        response_data['item_total_price_display'] = item_total_price_display
        
        return JsonResponse(response_data)

    except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
        logger.warning(f"Invalid data for cart quantity update: {e}")
        return JsonResponse({'success': False, 'error': 'Invalid data provided'}, status=400)

@require_POST
def cart_remove(request, product_id):
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return redirect('checkout:cart')

    cart = CartManager(request)
    message = "Товар удален из корзины."
    try:
        product = Product.objects.get(id=product_id)
        message = f"Товар '{product.full_title}' удален."
        cart.remove(product)
    except Product.DoesNotExist:
        product_id_str = str(product_id)
        if product_id_str in cart.cart:
            del cart.cart[product_id_str]
            cart.save()
            
    response_data = _prepare_cart_api_response(cart, request)
    response_data['success'] = True
    response_data['message'] = message
    response_data['product_id'] = product_id # JSON-safe
    
    return JsonResponse(response_data)






class SendFormOrder(View):

    def post(self, request):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        form = ZakazForm(request.POST)

        if form.is_valid():
            logger.info("Form submitted and is valid.")
            try:
                order = form.save(commit=False)
                order_type_from_form = request.POST.get('type', Order.TYPE_CALLBACK)

                # On vérifie que la valeur est valide pour éviter les injections de données
                valid_types = [choice[0] for choice in Order.ORDER_TYPE_CHOICES]
                if order_type_from_form in valid_types:
                    order.order_type = order_type_from_form
                else:
                    order.order_type = Order.TYPE_CALLBACK

                order.ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR')
                order.comment = request.POST.get('comment')
                order.filial = request.filial
                order.text = ''
                order.marketing_consent = request.POST.get('marketing_consent') == 'on'


                order.save()
                logger.info(f"Zakaz object {order.id} created successfully.")

                request.session['order_number'] = order.id


                # # === APPEL DE LA TÂCHE CELERY POUR ZAKAZ ===
                try:
                    send_order_notification_task.delay(order.id)
                    logger.info(f"Celery task queued for Order ID: {order.id} (from Simple Form)")
                except Exception as e_celery_task:
                    logger.error(f"Failed to queue Celery task for Zakaz {order.id}: {e_celery_task}", exc_info=True)
                # # =========================================

                # --- Réponse ---
                if is_ajax:
                    thank_you_url = request.build_absolute_uri(reverse('checkout:thank-you'))
                    return JsonResponse({'success': True, 'thank_you_url': thank_you_url})
                else:
                    return redirect('checkout:thank-you')

            except Exception as e_save:
                logger.error(f"Error saving Zakaz object after validation: {e_save}", exc_info=True)
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Ошибка сохранения данных.'}, status=500)
                else:
                    messages.error(request, "Произошла ошибка при сохранении заявки.")
                    return redirect('checkout:generic-error')

        else:
            logger.warning(f"Form submission invalid. Errors: {form.errors.as_json()}")
            
            honeypot_triggered = False
            if form.non_field_errors():
                for error in form.non_field_errors():
                    if hasattr(error, 'error_list'): 
                        for e_item in error.error_list:
                            if hasattr(e_item, 'code') and 'honeypot' in e_item.code:
                                honeypot_triggered = True; break
                    if honeypot_triggered: break
            
            for field_name in ['comp_input_hidden', 'website_url_confirm', 'form_render_timestamp']:
                if field_name in form.errors:
                    for error in form.errors[field_name]:
                        if hasattr(error, 'code') and 'honeypot' in error.code:
                            honeypot_triggered = True; break
                if honeypot_triggered: break
                            
            error_message_for_user = "Пожалуйста, исправьте ошибки в форме."
            ajax_error_message = error_message_for_user

            if honeypot_triggered:
                logger.warning(f"Honeypot triggered for submission from IP: {request.META.get('REMOTE_ADDR')}.")
                error_message_for_user = 'Обнаружена подозрительная активность. Пожалуйста, попробуйте позже.'
                ajax_error_message = 'Ошибка безопасности. Попробуйте снова.'
            
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': ajax_error_message,
                    'errors_dict': form.errors.get_json_data(escape_html=True) 
                }, status=400)
            else:
                messages.error(request, error_message_for_user)
                if honeypot_triggered:
                    return redirect(reverse('checkout:generic-error'))
                else:
                    return redirect(request.META.get('HTTP_REFERER', reverse('menu:index')))


class ThankYouView(View):
	def get(self, request):
		is_thank_you = True
        
		message = "Наш менеджер свяжется вами по указанным в форме при оформлении заказа данным."

		context = {
			'is_thank_you': is_thank_you,
			'message': message,
		}

		return render(request, 'catalog/thank-you.html', context)
	

class GenericErrorView(View):
	def get(self, request):
		is_generic_error = True
		message = "Ваша заявка не была успешной из-за мер безопасности. <br> Пожалуйста, повторите попытку позже."
		context = {
			'is_generic_error':is_generic_error,
			'message':message,
		}
		return render(request, 'catalog/generic-error.html', context)