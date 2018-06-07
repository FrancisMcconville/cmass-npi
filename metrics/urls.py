from django.conf.urls import include, url
from . import autocomplete_views

app_name = 'metrics'
urlpatterns = [
    url(r'autocomplete/manufacturingOrders$', autocomplete_views.MrpProductionAutocomplete.as_view(), name='autocompleteMo'),
    url(r'autocomplete/product$', autocomplete_views.ProductProductAutocomplete.as_view(), name='autocompleteProduct'),
    url(r'autocomplete/manufacturingOrdersUncompleted$', autocomplete_views.MrpProductionUncompletedAutocomplete.as_view(), name='autocompleteMoNotDone')
]
