from dal import autocomplete
from django.db.models import Q
from .models import *


class MrpProductionAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = MrpProduction.objects.exclude(state__in=('cancel',)).order_by('product__default_code', '-name', )
        if self.q:
            qs = qs.filter(Q(name__icontains=self.q) | Q(product__default_code__icontains=self.q))
        return qs


class ProductProductAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = ProductProduct.objects.filter(active=True).order_by('default_code')
        if self.q:
            qs = qs.filter(default_code__icontains=self.q)
        return qs


class MrpProductionUncompletedAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = MrpProduction.objects.exclude(state__in=('cancel', 'done')).order_by('product__default_code', '-name', )
        if self.q:
            qs = qs.filter(Q(name__icontains=self.q) | Q(product__default_code__icontains=self.q))
        return qs
