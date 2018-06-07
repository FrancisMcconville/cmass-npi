from cmass_django_generics.views import CmassContextMixin
from dal import autocomplete
from django.db.models import Q
from django.shortcuts import get_object_or_404
from npi.models import Component, QuoteQuantity, SupplierComponent, Project, Parent
from metrics.models import ResPartner


class AutocompleteCustomer(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        queryset = ResPartner.objects.filter(customer=True, active=True, parent__isnull=True).order_by('name')
        if self.q:
            queryset = queryset.filter(name__icontains=self.q)
        return queryset


class AutocompleteSupplier(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        queryset = ResPartner.objects.filter(supplier=True, active=True).order_by('name')
        if self.q:
            queryset = queryset.filter(name__icontains=self.q)
        return queryset


class AutocompleteQuoteQuantity(autocomplete.Select2QuerySetView):
    project = None

    def dispatch(self, request, *args, **kwargs):
        if 'project_id' in kwargs:
            self.project = get_object_or_404(Project, pk=kwargs.pop('project_id'))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = QuoteQuantity.objects.all()

        if self.project:
            queryset = queryset.filter(project=self.project)

        if self.q:
            queryset = queryset.filter(quantity__icontains=self.q)
        return queryset


class AutocompleteSupplierComponent(autocomplete.Select2QuerySetView):
    component = None

    def dispatch(self, request, *args, **kwargs):
        self.component = get_object_or_404(Component, pk=kwargs.pop('component_id'))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = SupplierComponent.active_components.filter(component=self.component)

        if self.q:
            queryset = queryset.filter(Q(project_supplier__name__icontains=self.q) | Q(product_code__icontains=self.q))
        return queryset


class AutocompleteBomParent(autocomplete.Select2QuerySetView):
    project = None

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs.pop('project_id'))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Parent.objects.filter(project=self.project)

        if self.q:
            queryset = queryset.filter(name__icontains=self.q)
        return queryset


class NpiContextMixin(CmassContextMixin):
    navigation_template = 'npi/npi_navigation.html'


class AutocompleteParent(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        queryset = Parent.objects.all().order_by('name')

        if self.q:
            queryset = queryset.filter(name__icontains=self.q)
        return queryset
