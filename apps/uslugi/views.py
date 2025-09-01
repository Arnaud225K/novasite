from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import Uslugi

class UslugiListView(ListView):
    """ Affiche la liste de tous les services non cachés. """
    model = Uslugi
    template_name = 'uslugi/uslugi.html'
    context_object_name = 'services'

    def get_queryset(self):
        return Uslugi.objects.filter(is_hidden=False).order_by('order_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_uslugi_page'] = True
        return context


class UslugiDetailView(DetailView):
    model = Uslugi
    template_name = 'uslugi/p-uslugi.html'
    context_object_name = 'service'

    def get_queryset(self):
        return super().get_queryset().filter(is_hidden=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # On passe la variable 'service' au contexte du fil d'ariane
        return context
