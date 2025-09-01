from django.shortcuts import render

from django.template import Context, Template

from novator.views import global_views
from .models import StaticText
from apps.filial.models import Filial



def get_static_text(request, global_context, slug):
	try:
		global_context.update(global_views(request))
		try:
			current_filial = request.filial
			region = slug
			if current_filial.subdomain_name == '/':
				region += '_main'
			else:
				region += '_'
				region += current_filial.subdomain_name[:-1]
			html_static_text = Template(StaticText.objects.get(slug=region).text).render(Context(global_context))
		except:
			html_static_text = Template(StaticText.objects.get(slug=slug).text).render(Context(global_context))
	except:
		html_static_text = ''
	return html_static_text



def static_text(request):
	static_text_list = {}
	for item in list(StaticText.objects.values('slug', 'text').distinct().order_by('slug')):
		static_text_list[item['slug']] = item
	
	try:
		text_cover_home_page_1 = static_text_list['text_cover_home_page_1']['text']
	except:
		text_cover_home_page_1 = ""

		
	return locals()

