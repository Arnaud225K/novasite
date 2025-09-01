from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import Articles



class ArticleListView(ListView):
    """ Affiche la liste de tous les articles non cachés, avec pagination. """
    model = Articles
    template_name = 'articles/articles.html'
    context_object_name = 'articles'
    paginate_by = 2

    def get_queryset(self):
        return Articles.objects.filter(is_hidden=False).order_by('order_number', '-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_articles_page'] = True
        return context


class ArticleDetailView(DetailView):
    """ Affiche la page de détail d'un article spécifique. """
    model = Articles
    template_name = 'articles/p-articles.html'
    context_object_name = 'article'

    def get_queryset(self):
        return super().get_queryset().filter(is_hidden=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # On peut ajouter d'autres articles à lire ici si besoin
        return context