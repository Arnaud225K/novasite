import datetime
import json
import os
import random
import sys
import smtplib
import requests
from urllib.parse import urlencode as original_urlencode
from email import encoders as Encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse

from django.core import serializers
from django.shortcuts import get_object_or_404
# from transliterate import translit

# from filials.views import get_current_filial

from apps.products.models import Product
from project_settings.models import ProjectSettings
from novator.settings import MEDIA_ROOT, CONTACTS_SESSION_KEY
from checkout.models import Zakaz


def get_today():
	return datetime.datetime.today().strftime("%Y-%m-%d %H:%M")


def create_order(request, type_order=None):
	# current_filial = get_current_filial(request)
	post_data = request.POST.copy()
	order = Zakaz()

	order.name = post_data['name']
	order.email = post_data['email']
	order.phone = post_data['phone']
	order.ip_address = request.META.get('REMOTE_ADDR')
	order.type_client = post_data.get('type_client', '')

	if type_order:
		order.type_order = type_order
	else:
		order.type_order = ''

	text_order = ""
	try:
		text_order = request.POST['comment'] + "\n"
	except:
		pass


	if order.type_order == 'Под заказ' or order.type_order == 'Быстрый заказ':
		produit_title = post_data.get('produit_title', '')
		produit_price = post_data.get('produit_price', '')
		
		text_order += f"Заказ: {produit_title}\n"
		text_order += f"Стоимость - {produit_price}\n"

	order.text = text_order

	order.save()
	order_number = order.id

	if order_number:
		request.session['order_number'] = order_number

	return order



def task_send_mail_order(order, request):
	# current_filial = get_current_filial(request)
	current_filial = request.filial
	address_to = current_filial.email

	# if request.session.get(CONTACTS_SESSION_KEY, '') == 'yclid':
	# 	if current_filial.email_yclid:
	# 		address_to = current_filial.email_yclid
	# if request.session.get(CONTACTS_SESSION_KEY, '') == 'gclid':
	# 	if current_filial.email_gclid:
	# 		address_to = current_filial.email_gclid

	# if 'Подписка на рассылку' in order.type_order: 
	# 	host = address_to.split('@')[-1]
	# 	address_to = 'collector@{}'.format(host)
	order.email_to = address_to
	order.save()
	order_id = order.id
	# try:
	# 	import threading
	# 	thr = threading.Thread(target=send_mail_order,
	# 						   args=[request, serializers.serialize('json', [order]),
	# 								 address_to, current_filial, order_id])
	# 	thr.setDaemon(True)
	# 	thr.start()
	# except:
	# 	pass


# send_mail_order(serializers.serialize('json', [order]), get_current_filial(request).id)


# def send_client_zayavka(email, order, fio, product=None):
# 	subject = u"Вы оформили заявку на сайте E&R"
# 	if product:
# 		body = u"""Здравствуйте, %s!\nСпасибо за ваш запрос. """ % (fio)
# 		body += u"""В ближайшее время Вам придет информация о цене и наличии продукции %s\n""" % (product)
# 	else:
# 		body = u"""Здравствуйте, %s!\nСпасибо за ваш запрос. В ближайшее время с Вами свяжется наш специалист!\n""" % (
# 			fio)
# 		body += u"""%s\nВозникли вопросы или дополнение? пишите на электронную почту info@industrial.kz""" % (order)
	
# 	# project_settings = ProjectSettings.objects.all().first()
# 	project_settings = False
# 	if project_settings:
# 		address = project_settings.tech_email
# 		msg = MIMEMultipart('alternative')
# 		msg['From'] = project_settings.tech_email
# 		msg['To'] = email
# 		msg['Subject'] = subject
		
# 		part1 = MIMEText(body, 'plain', 'UTF-8')
# 		msg.attach(part1)
# 		send_msg = smtplib.SMTP(project_settings.tech_mail_server, 465)
# 		send_msg.ehlo()
# 		send_msg.esmtp_features["auth"] = "LOGIN PLAIN"
# 		send_msg.debuglevel = 5
# 		send_msg.login(project_settings.tech_email, project_settings.tech_email_pass)
# 		send_msg.sendmail(address, email, msg.as_string())
# 		send_msg.quit()

def send_mail_order(request, order, address_to, current_filial, order_id):
	# from python_bitrix24.python_bitrix24_django import bitrix24Connection
	order = json.loads(order)[0]['fields']
	fio = order["name"]
	phone = order["phone"]
	email = order["email"]
	text = order["text"]
	date = order["date"]
	file_name = order["file"]
	type_order = order["type_order"]
	type_client = order["type_client"]

	# if type_order == "Консультация" or type_order == "Консультация (потребность)":
	# 	source_id = "2"
	# elif type_order == "Запрос цены" or type_order == "Запрос цены (категория)":
	# 	source_id = "1"
	# elif type_order == "Корзина":
	# 	source_id = "3"
	# elif type_order == "Запрос обратного звонка":
	# 	source_id = "CALLBACK"
	# else:
	# 	source_id = "OTHER"
	
	subject = u"""Поступил новый заказ: %s от %s""" % (fio, date)
	body = u"""Заказ от %s\nТип заявки: %s\nФ.И.О: %s \nТелефон %s\nEmail: %s\n%s\n""" % (date, type_order, fio, phone, email, text)
	if type_client:
		body += 'Клиент: {}\n'.format(type_client)

	# order_names = 'Заказ с сайта # ' + str(order_id) + ' (' + str(current_filial.name) + ')'
	# bitrix24Connection.add_lead(
	# 	order_names, {
	# 		'FIELDS[NAME]': fio,
	# 		'FIELDS[PHONE][0][VALUE]': phone,
	# 		'FIELDS[PHONE][0][VALUE_TYPE]': 'WORK',
	# 		'FIELDS[EMAIL][0][VALUE]': email,
	# 		'FIELDS[EMAIL][0][VALUE_TYPE]': 'WORK',
	# 		'FIELDS[COMMENTS]': text,
	# 		'FIELDS[SOURCE_ID]': source_id,
	# 		'FIELDS[SOURCE_DESCRIPTION]': current_filial.name + ', ' + type_order + ', ' + type_client,
	# 		'FIELDS[UTM_CAMPAIGN]': request.session.get('bt_utm_campaign', ''),
	# 		'FIELDS[UTM_CONTENT]': request.session.get('bt_utm_content', ''),
	# 		'FIELDS[UTM_MEDIUM]': request.session.get('bt_utm_medium', ''),
	# 		'FIELDS[UTM_SOURCE]': request.session.get('bt_utm_source', ''),
	# 		'FIELDS[UTM_TERM]': request.session.get('bt_utm_term', ''),
	# 		# 'FIELDS[UF_CRM_1675925698]': roistat_visit,
	# 		'FIELDS[ASSIGNED_BY_ID]': '76'
	# 	}
	# )


	project_settings = ProjectSettings.objects.all().first()
	
	if project_settings:
		address = project_settings.tech_email
		msg = MIMEMultipart('alternative')
		msg['From'] = project_settings.tech_email
		msg['To'] = address_to
		msg['Subject'] = subject
		
		part1 = MIMEText(body, 'plain', 'UTF-8')
		msg.attach(part1)
		if file_name:
			part = MIMEBase('application', "octet-stream")
			part.set_payload(open(MEDIA_ROOT + file_name, "rb").read())
			Encoders.encode_base64(part)
			part.add_header('Content-Disposition',
							'attachment; filename="%s"' % os.path.basename(MEDIA_ROOT + file_name))
			msg.attach(part)
		
		send_msg = smtplib.SMTP(project_settings.tech_mail_server, 465)
		send_msg.ehlo()
		send_msg.esmtp_features["auth"] = "LOGIN PLAIN"
		send_msg.debuglevel = 5
		send_msg.login(project_settings.tech_email, project_settings.tech_email_pass)
		send_msg.sendmail(address, address_to, msg.as_string())
		send_msg.quit()
	# try:
	# 	if email:
	# 		send_client_zayavka(email, text, fio)
	# except:
	# 	pass
