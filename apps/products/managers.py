from django.db import models
from django.db.models import OuterRef, Subquery, F, Value, BooleanField, Q, OuterRef, DecimalField
from collections import defaultdict


class ProductQuerySet(models.QuerySet):
    def with_filial_data(self, filial):
        from .models import ProductFilialData
        if not filial: return self.none()
        price_sq = Subquery(ProductFilialData.objects.filter(product=OuterRef('pk'), filial=filial).values('price')[:1])
        available_sq = Subquery(ProductFilialData.objects.filter(product=OuterRef('pk'), filial=filial).values('is_available')[:1])
        parent_price_sq, parent_available_sq = Value(None), Value(None)
        if filial.parent:
            parent_price_sq = Subquery(ProductFilialData.objects.filter(product=OuterRef('pk'), filial=filial.parent).values('price')[:1])
            parent_available_sq = Subquery(ProductFilialData.objects.filter(product=OuterRef('pk'), filial=filial.parent).values('is_available')[:1])
        return self.annotate(
            price=models.functions.Coalesce(price_sq, parent_price_sq, F('base_price')),
            is_available=models.functions.Coalesce(available_sq, parent_available_sq, Value(False), output_field=BooleanField())
        )

    def visible_in_filial(self, filial):
        from apps.menu.models import MenuCatalog, MenuCatalogFilialVisibility
        if not filial: return self.none()
        filiales_to_check = [filial.id]
        if filial.parent_id: filiales_to_check.append(filial.parent_id)
        hidden_roots = MenuCatalogFilialVisibility.objects.filter(filial_id__in=filiales_to_check, is_hidden=True).values_list('category_id', flat=True)
        if not hidden_roots: return self
        q_objects = Q()
        for tree in MenuCatalog.objects.filter(id__in=hidden_roots):
            q_objects |= Q(tree_id=tree.tree_id, lft__gte=tree.lft, lft__lte=tree.rght)
        all_hidden_ids = MenuCatalog.objects.filter(q_objects).values_list('id', flat=True)
        return self.exclude(category__id__in=all_hidden_ids)

    def get_visible_for_filial(self, filial):
        return self.visible_in_filial(filial).with_filial_data(filial)

class ProductManager(models.Manager):
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)

    def get_visible_for_filial(self, filial):
        return self.get_queryset().get_visible_for_filial(filial)


    def get_faceted_filters_for_queryset(self, product_queryset):
        """
        Analyse un queryset de produits et retourne la structure des
        filtres disponibles (facettes) avec les comptes de produits.
        Cette méthode est maintenant générique et ne dépend plus d'une catégorie.
        """
        from .models import FilterValue
        if not product_queryset.exists():
            return {}
            
        # On trouve toutes les valeurs de filtre présentes dans le queryset actuel
        values_with_counts = FilterValue.objects.filter(
            products__in=product_queryset
        ).annotate(
            product_count=models.Count('products', distinct=True)
        ).select_related('category') # Optimisation

        # On structure la réponse (logique inchangée)
        structured_filters = defaultdict(lambda: {'name': '', 'slug': '', 'values': []})
        for fv in values_with_counts:
            if fv.product_count > 0:
                cat_slug = fv.category.slug
                cat_data = structured_filters[cat_slug]
                if not cat_data['name']:
                    cat_data['name'] = fv.category.name
                    cat_data['slug'] = fv.category.slug
                cat_data['values'].append({'value': fv.value, 'slug': fv.slug, 'count': fv.product_count})
        
        # ... (tri optionnel des valeurs)
        return dict(structured_filters)
    