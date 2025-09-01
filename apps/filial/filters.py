from django.contrib import admin
from django.db.models import Q
from .models import Filial



class IsParentFilter(admin.SimpleListFilter):
    """
    Filtre personnalisé pour l'admin Django qui permet de filtrer les filiales
    selon qu'elles sont ou non un parent pour au moins une autre filiale.
    """
    title = "Является основным"

    # Nom du paramètre dans l'URL (ex: /admin/filial/filial/?is_parent=yes)
    parameter_name = 'is_parent'

    def lookups(self, request, model_admin):
        """
        Retourne les options cliquables pour l'utilisateur.
        Le premier élément de chaque tuple est la valeur passée dans l'URL.
        Le second est le texte affiché.
        """
        return (
            ('yes', 'Да'),
            ('no', 'Нет'),
        )

    def queryset(self, request, queryset):
        """
        Applique le filtre sur le queryset.
        La méthode est appelée avec la valeur choisie par l'utilisateur ('yes' ou 'no').
        """
        if self.value() == 'yes':
            return queryset.filter(children__isnull=False).distinct()
        
        if self.value() == 'no':
            return queryset.filter(children__isnull=True)
        
        return queryset



class ParentChoiceFilter(admin.SimpleListFilter):
    """
    Filtre personnalisé qui n'affiche que les filiales parentes comme options,
    et filtre la liste pour afficher leurs enfants lorsqu'une option est sélectionnée.
    """
    title = "Основной филиал"
    parameter_name = 'parent_id'

    def lookups(self, request, model_admin):
        """
        Cette méthode génère la liste des options cliquables.
        Nous allons ici chercher toutes les filiales qui ont au moins un enfant.
        """
        parents = Filial.objects.filter(children__isnull=False).distinct().order_by('name')
        
        return [(p.id, p.name) for p in parents]

    def queryset(self, request, queryset):
        """
        Cette méthode applique le filtre sur la liste principale.
        """
        if self.value():
            return queryset.filter(parent__id=self.value())
        
        return queryset