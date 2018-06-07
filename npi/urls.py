from npi.model_views import project_views, supplier_views, bom_views
from npi import views
from django.conf.urls import url

app_name = 'npi'
urlpatterns = []

# Project views
urlpatterns += [
    url(r'project/create$',
        project_views.CreateProject.as_view(),
        name='createProject'),
    url(r'project/$',
        project_views.ListProject.as_view(),
        name='listProjects'),
    url(r'project/delete/(?P<pk>[0-9]+)$',
        project_views.DeleteProject.as_view(),
        name='deleteProject'),
    url(r'project/(?P<pk>[0-9]+)$',
        project_views.ViewProject.as_view(),
        name='viewProject'),
    url(r'project/(?P<project_id>[0-9]+)/edit',
        project_views.EditProject.as_view(),
        name='editProject'),
    url(r'project/(?P<pk>[0-9]+)/update$',
        project_views.UpdateProjectBom.as_view(),
        name='updateProjectBom'),
    url(
        r'project/template$',
        project_views.get_project_template,
        name='getProjectTemplate'),
    url(
        r'datatable/project$',
        project_views.ProjectDatatable.as_view(),
        name='projectDatatable'),
    url(
        r'datatable/projectComponents$',
        project_views.ProjectProductComponentDatatable.as_view(),
        name='projectComponentsDatatable'),
]

# Supplier views
urlpatterns += [
    url(
        r'project/(?P<project_id>[0-9]+)/supplierinfo/create$',
        supplier_views.CreateProjectSupplier.as_view(),
        name='createSupplierInfo'),
    url(
        r'project/(?P<project_id>[0-9]+)/supplierinfo/edit$',
        supplier_views.EditProjectSupplier.as_view(),
        name='editSupplierInfo'),
    url(
        r'project/(?P<pk>[0-9]+)/supplierinfo/$',
        supplier_views.ViewProjectSupplier.as_view(),
        name='viewSupplierInfo'),
    url(
        r'project/(?P<project_id>[0-9]+)/supplierinfo/export$',
        supplier_views.ExportProjectSupplier.as_view(),
        name='exportSupplierInfo'),
    url(
        r'project/(?P<project_id>[0-9]+)/supplierinfo/upload$',
        supplier_views.UploadProjectSupplier.as_view(),
        name='uploadSupplierInfo'),
    url(
        r'project/(?P<project_id>[0-9]+)/supplierinfo/quotes$',
        supplier_views.ViewProjectSupplierQuotes.as_view(),
        name='viewSupplierInfoQuotes'),
    url(
        r'update_component_quote$',
        supplier_views.update_component_quote,
        name='updateComponentQuote'),
    url(
        r'project/(?P<pk>[0-9]+)/clean$',
        supplier_views.CleanProjectSupplier.as_view(),
        name='cleanProject'
    ),
    url(
        r'project/(?P<project_id>[0-9]+)/supplierinfo/quotes/export$',
        supplier_views.ExportToOpenERP.as_view(),
        name='exportSupplierInfoToOpenERP'
    ),
    url(
        r'datatable/supplierComponentAlternatives/(?P<project_id>[0-9]+)$',
        supplier_views.SupplierComponentAlternativesDatatable.as_view(),
        name='supplierComponentAlternatives'),
    url(
        r'project/(?P<project_id>[0-9]+)/supplierinfo/alternatives$',
        supplier_views.SupplierComponentAlternativeEdit.as_view(),
        name='editSupplierComponentAlternatives'
    ),
    url(
        r'project/(?P<project_id>[0-9]+)/supplierinfo/excel',
        supplier_views.export_to_excel,
        name='exportSupplierInfoExcel'
    ),
    url(
        r'project/(?P<project_supplier_id>[0-9]+)/api',
        supplier_views.supplier_api_pricing,
        name='getSupplierPricingApi'
    ),
    url(
        r'projectSupplier/(?P<project_supplier_id>[0-9]+)/quote',
        supplier_views.ExportExistingProjectSupplier.as_view(),
        name='exportSupplierInfoExistingExcel'
    ),
]

# Bom views
urlpatterns += [
    url(r'project/(?P<pk>[0-9]+)/bom$',
        bom_views.ViewBom.as_view(),
        name='viewBom'),
    url(r'project/(?P<project_id>[0-9]+)/bom/upload$',
        bom_views.UploadBom.as_view(),
        name='uploadBom'),
    url(
        r'project/(?P<project_id>[0-9]+)/bom/export$',
        bom_views.ExportToOpenERP.as_view(),
        name='exportBomToOpenERP'
    ),
    url(
        r'project/bom/template$',
        bom_views.get_bom_template,
        name='getBomTemplate'),
]

# General views
urlpatterns += [
    url(
        r'autocomplete/customer_id$',
        views.AutocompleteCustomer.as_view(),
        name='autocompleteCustomer'),
    url(
        r'autocomplete/supplier_id$',
        views.AutocompleteSupplier.as_view(),
        name='autocompleteSupplier'),
    url(
        r'autocomplete/quote_quantity/(?P<project_id>[0-9]+)$',
        views.AutocompleteQuoteQuantity.as_view(),
        name='autocompleteQuoteQuantity'),
    url(
        r'autocomplete/project_supplier/(?P<component_id>[0-9]+)$',
        views.AutocompleteSupplierComponent.as_view(),
        name='autocompleteSupplierComponent'),
    url(
        r'autocomplete/bom_parent/(?P<project_id>[0-9]+)$',
        views.AutocompleteBomParent.as_view(),
        name='autocompleteBomParent'),
    url(
        r'autocomplete/parent$',
        views.AutocompleteParent.as_view(),
        name='autocompleteParent'),

]
