import logging
from django.conf import settings
from django.urls import reverse
from django.template.loader import render_to_string
from celery import shared_task

from .models import Order
from apps.filial.models import Filial
from apps.project_settings.models import ProjectSettings 
from apps.utils.utils import send_html_email 

logger = logging.getLogger(__name__)



@shared_task(bind=True, max_retries=3, default_retry_delay=300) # 5 min de délai avant de réessayer
def send_order_notification_task(self, order_id):
    """
    Tâche Celery unique qui envoie une notification d'email à l'administrateur
    pour une nouvelle commande, en choisissant le template approprié.
    """
    logger.info(f"CELERY TASK: Starting email notification for Order ID: {order_id}")
    
    try:
        order = Order.objects.select_related('filial').prefetch_related('items__product').get(id=order_id)
        
        if order.order_type == Order.TYPE_CART:
            template_name = 'checkout/emails/email_cart_order.html'
            subject = f"Новый заказ из корзины №{order.id}"
        else:
            template_name = 'checkout/emails/email_request_order.html'
            subject = f"Новая заявка ({order.get_order_type_display()}) №{order.id}"
        
        logger.info(f"CELERY TASK: Using template '{template_name}' for order type '{order.order_type}'.")

        main_domain = getattr(settings, 'MAIN_DOMAIN', 'localhost:8000') # Pour le dev
        request_scheme = 'https' if not settings.DEBUG else 'http'
        
        if order.filial and not order.filial.is_default:
            site_domain = f"{order.filial.subdomain}.{main_domain}"
        else:
            site_domain = main_domain
            
        admin_order_url = None
        try:
            admin_url_path = reverse(f'admin:{order._meta.app_label}_{order._meta.model_name}_change', args=[order.id])
            admin_order_url = f"{request_scheme}://{site_domain}{admin_url_path}"
        except Exception:
            logger.warning(f"Could not generate admin URL for order {order.id} in Celery task.")

        # On récupère les settings globaux pour le template
        # project_settings = ProjectSettings.objects.first()

        context = {
            'order': order,
            'site_url': f"{request_scheme}://{site_domain}",
            'admin_order_url': admin_order_url,
            # 'project_settings': project_settings,
        }

        # 4. RENDRE LE TEMPLATE HTML
        html_content = render_to_string(template_name, context)
        
        # 5. PRÉPARER ET ENVOYER L'EMAIL
        recipient_list = [getattr(settings, 'INFO_EMAIL', 'kouakanarnaud@gmail.com')]
        reply_to = [f"{order.name} <{order.email}>"] if order.email else None

        # 6. On appelle la fonction avec les bons noms d'arguments
        email_sent = send_html_email(
            subject=subject,
            html_content=html_content,
            recipient_list=recipient_list,
            reply_to=reply_to
        )

        if not email_sent:
            logger.error(f"CELERY TASK: send_html_email function returned False for order {order.id}.")
            # On lève une exception pour que Celery puisse retenter la tâche.
            raise Exception("Email sending function failed.")

        logger.info(f"CELERY TASK: Email task for order {order.id} completed successfully.")
        return f"Email for order {order.id} sent."

    except Order.DoesNotExist:
        logger.error(f"CELERY TASK: Order with ID {order_id} not found. Task will not retry.")
        return f"Order {order_id} not found."
    except Exception as e:
        logger.exception(f"CELERY TASK: An unexpected error occurred for order ID {order_id}: {e}")
        # Celery va retenter automatiquement la tâche en cas d'exception.
        raise self.retry(exc=e)