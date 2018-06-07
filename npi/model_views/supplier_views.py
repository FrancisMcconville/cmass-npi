import zipfile
from cmass_django_generics.views import CmassDeleteView
from django.db import transaction
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import reverse, get_object_or_404
from django.views.generic import DetailView, FormView, View, TemplateView, DeleteView
from cmass_django_datatables_view.base_datatable_view import BaseDatatableView
from io import BytesIO
from npi.forms import CreateProjectSupplierForm, EditProjectSupplierForm, SupplierComponentAlternativeForm
from npi.forms import SupplierInformationUploadForm, QuoteQuantityForm, ExportSupplierInformationToOpenErpForm
from npi.models import Project, ProjectSupplier, SupplierComponent, Component, SupplierProductQuote, QuoteQuantity
from npi.tables import ProjectSupplierInformationTable, ComponentsWithoutQuotesTable
from npi.utils import NPI_PROJECT_MAX_QUOTATION_QUANTITY, ExcelUtils, SUPPLIER_INFO_TEMPLATE
from npi.views import NpiContextMixin
import csv
import xlrd
import xlwt
from django.utils.encoding import smart_str


class CreateProjectSupplier(NpiContextMixin, FormView):
    template_name = 'npi/supplier_info/create.html'
    form_class = CreateProjectSupplierForm
    project = None

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, id=kwargs.get('project_id', None))
        return super().dispatch(request, *args, **kwargs)

    def get_title(self):
        return '%s Create Supplier Information' % self.project

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.project
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['formset'] = context['form'].formset
        context['project'] = self.project
        return context

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(reverse('npi:viewSupplierInfo', kwargs={'pk': self.project.id}))


class EditProjectSupplier(CreateProjectSupplier):
    form_class = EditProjectSupplierForm

    def get_title(self):
        return '%s Edit Supplier Information' % self.project


class CleanProjectSupplier(NpiContextMixin, CmassDeleteView):
    model = Project
    template_name = 'npi/supplier_info/delete.html'
    modal_id = 'deleteProjectSuppliers'

    def get_success_url(self):
        return reverse('npi:viewSupplierInfo', kwargs={'pk': self.get_object().pk})

    def get_title(self):
        return 'Clean %s Suppliers' % self.get_object()

    def get_post_url(self):
        return reverse('npi:cleanProject', kwargs={'pk': self.get_object().id})

    def get_cancel_url(self):
        return reverse('npi:viewSupplierInfo', kwargs={'pk': self.get_object().id})

    def delete(self, request, *args, **kwargs):
        with transaction.atomic():
            ProjectSupplier.objects.filter(project=self.get_object()).delete()
            self.get_object().wkf_supplier_info_draft()
        if request.is_ajax():
            return self.close_modal()
        return HttpResponseRedirect(self.get_success_url())


class ViewProjectSupplier(NpiContextMixin, DetailView):
    model = Project
    template_name = 'npi/supplier_info/view.html'
    ajax_refresh_page = True

    def get_title(self):
        return '%s Supplier Information' % self.get_object()

    def get_navigation_buttons(self):
        buttons = self.get_object().supplier_info_actions_available()
        for button in buttons:
            button.update({'class': button['button-class'], 'link': button['url']})
        return buttons

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['table'] = ProjectSupplierInformationTable(ProjectSupplier.objects.filter(project=self.get_object()))
        context['pending_products_table'] = ComponentsWithoutQuotesTable(
            Component.objects.filter(project=self.get_object()).exclude(
                id__in=[
                    supplier_product.component.id for supplier_product in SupplierComponent.active_components.filter(
                        project_supplier__project=self.get_object()
                    )
                ]
            )
        )
        context['alternatives'] = SupplierComponent.objects.filter(
            component__project=self.get_object(), alternative=True
        )
        return context


class ExportProjectSupplier(View, NpiContextMixin):
    project = False
    suppliers = False
    zip = False
    output_file = BytesIO()
    http_method_names = ['get']
    spreadsheet_filename = "%(project)s_%(supplier)s_RFQ.xls"
    zip_filename = '%(project)s_RFQs.zip'

    @staticmethod
    def _file_safe_string(string):
        string = str(string)
        bad_characters = ['/']
        for character in bad_characters:
            string = string.replace(character, ' ')
        return string

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs.pop('project_id'))
        self.suppliers = ProjectSupplier.objects.filter(project=self.project)
        if len(self.suppliers) > 1:
            self.zip = True
        return super().dispatch(request, *args, **kwargs)

    def get_filename(self):
        if not self.zip:
            return self.spreadsheet_filename % {
                'project': self._file_safe_string(self.project),
                'supplier': self._file_safe_string(self.suppliers.first())
            }
        return self.zip_filename % {'project': self._file_safe_string(self.project)}

    def get_content_type(self):
        if not self.zip:
            return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return "application/x-zip-compressed"

    def get_supplier_spreedsheet(self, supplier):
        return supplier.generate_rfq_spreadsheet()

    def get_output_file(self):
        if not self.zip:
            return self.get_supplier_spreedsheet(self.suppliers.first())

        zip_file = zipfile.ZipFile(self.output_file, mode='w', compression=zipfile.ZIP_DEFLATED)
        for supplier in self.suppliers:
            rfq_spreadsheet = self.get_supplier_spreedsheet(supplier)
            zip_file.writestr(
                self.spreadsheet_filename % {
                    'project': self._file_safe_string(self.project),
                    'supplier': self._file_safe_string(supplier)
                },
                rfq_spreadsheet.getvalue()
            )
        zip_file.close()
        return self.output_file

    def get(self, request):
        response = HttpResponse(self.get_output_file().getvalue(), content_type=self.get_content_type())
        response['Content-Disposition'] = 'attachment; filename="%s"' % self.get_filename()
        return response


class ExportExistingProjectSupplier(ExportProjectSupplier):

    def dispatch(self, request, *args, **kwargs):
        self.suppliers = ProjectSupplier.objects.filter(pk=kwargs.pop('project_supplier_id'))
        self.project = self.suppliers.first().project
        return super(ExportProjectSupplier, self).dispatch(request, *args, **kwargs)

    def get_supplier_spreedsheet(self, supplier):
        return supplier.generate_existing_spreadsheet()


class UploadProjectSupplier(NpiContextMixin, FormView):
    template_name = 'npi/supplier_info/upload.html'
    form_class = SupplierInformationUploadForm
    project = None

    def get_title(self):
        return '%s Upload Supplier Information' % self.project

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('npi:viewSupplierInfo', kwargs={'pk': self.project.id})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.project
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['project'] = self.project
        context['table'] = ProjectSupplierInformationTable(ProjectSupplier.objects.filter(project=self.project))
        return context

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, id=kwargs.pop('project_id'))
        return super().dispatch(request, *args, **kwargs)


class ViewProjectSupplierQuotes(NpiContextMixin, TemplateView):
    template_name = 'npi/supplier_pricing/view.html'
    project = None
    quotation_quantity = None

    def get_title(self):
        return '%(project)s Supplier Quotes for Quotation Quantity %(quantity)g' % {
            'project': self.project, 'quantity': self.quotation_quantity.quantity
        }

    def get_navigation_buttons(self):
        buttons = [{
            'id': 'exportExcelButton',
            'class': 'btn btn-success',
            'link': reverse('npi:exportSupplierInfoExcel', kwargs={'project_id': self.project.id}),
            'text': 'Excel'
        }]
        if self.project.supplier_info_state != 'uploaded':
            buttons.append({
                'id': 'exportButton',
                'class': 'btn btn-primary',
                'link': "%(url)s?quote_quantity=%(quote_quantity_id)s" % {
                    'url': reverse(
                        'npi:exportSupplierInfoToOpenERP',
                        kwargs={'project_id': self.project.id}
                    ),
                    'quote_quantity_id': self.quotation_quantity.id
                },
                'text': 'Export'
            })
        return buttons

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs.pop('project_id'))

        quote_quantity_id = request.GET.get('quote_quantity', None)
        if quote_quantity_id:
            self.quotation_quantity = get_object_or_404(QuoteQuantity, pk=quote_quantity_id)
        else:
            self.quotation_quantity = QuoteQuantity.objects.filter(project=self.project).order_by('quantity').first()

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['project'] = self.project
        context['components'] = Component.objects.filter(project=self.project)
        context['quotation_quantity'] = self.quotation_quantity
        context['form'] = QuoteQuantityForm(project=self.project, quote_quantity=self.quotation_quantity)
        return context


class ExportProjectSupplierQuotes(View):
    http_method_names = ['get']
    project = None

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs.pop('project_id'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s.csv' % self.project
        writer = csv.writer(response, csv.excel)
        response.write(u'\ufeff'.encode('utf8'))

        products = SupplierComponent.objects.filter(project_supplier__project=self.project).order_by(
            'project_product_component__project_product__name',
            'project_product_component__mpn',
            'project_supplier__supplier_id'
        )

        headers = [
            'Product', 'Customer Manufacturer', 'Customer MPN', 'Customer QTY', 'Customer UOM', 'Supplier',
            'Supplier Part No', 'Supplier Description', 'Supplier Manufacturer', 'Supplier MPN', 'MOQ',
            'Order Multiples', 'Current Stock', 'Leadtime'
        ]

        for quote_quantity in range(0, NPI_PROJECT_MAX_QUOTATION_QUANTITY):
            headers.append("QTY%s" % (quote_quantity+1))

        writer.writerow([smart_str(header) for header in headers])

        for product in products:
            row = [
                product.project_product_component.project_product.name,
                product.project_product_component.manufacturer,
                product.project_product_component.mpn,
                product.project_product_component.qty,
                product.project_product_component.uom_name,
                product.project_supplier.supplier_name,
                product.product_code,
                product.description,
                product.manufacturer,
                product.mpn,
                product.moq,
                product.order_multiples,
                product.current_stock,
                product.leadtime
            ]
            quotes = SupplierProductQuote.objects.filter(
                product=product
            ).order_by('quantity')[:NPI_PROJECT_MAX_QUOTATION_QUANTITY]

            for quote in quotes:
                row += [quote.price]
            writer.writerow(row)

        return response


def export_to_excel(request, project_id):
    project = Project.objects.get(pk=project_id)
    data = SupplierProductQuote.get_excel_data(QuoteQuantity.objects.filter(project=project), project)
    response = HttpResponse(content_type="application/vnd.ms-excel")
    response['Content-Disposition'] = 'attachment; filename=bom_supplier_info.xls'
    template_workbook = xlrd.open_workbook(SUPPLIER_INFO_TEMPLATE, formatting_info=True)
    template_sheet = template_workbook.sheet_by_index(0)
    workbook = xlwt.Workbook()

    for page in data:
        sheet = workbook.add_sheet('Quantity %s' % page.pop(0), cell_overwrite_ok=True)
        ExcelUtils.copy_row_style(sheet, template_sheet.ncols, 0, 0)
        for i in range(0, template_sheet.ncols):
            ExcelUtils.set_cell_value(sheet, 0, i, ExcelUtils.cell_string_value(template_sheet, 0, i))
            for index, component in enumerate(page[0]):
                ExcelUtils.set_cell_value(sheet, index+1, i, list(component.values())[i])

    workbook.save(response)
    return response


def update_component_quote(request):
    component = get_object_or_404(Component, pk=request.GET.get('component_id'))
    quotation_quantity = get_object_or_404(QuoteQuantity, pk=request.GET.get('quotation_quantity_id'))
    supplier_component = get_object_or_404(SupplierComponent, pk=request.GET.get('supplier_component_id'))
    quotation = SupplierProductQuote.objects.filter(
        product=supplier_component, quote_quantity=quotation_quantity
    ).first()
    quotation.select()

    updated_quote = component.selected_quote(quotation_quantity)
    current_stock = ''
    if updated_quote.product.current_stock:
        current_stock = '%g' % updated_quote.product.current_stock

    leadtime = ''
    if updated_quote.product.leadtime:
        leadtime = '%g' % updated_quote.product.leadtime

    response = {
        'component_id': component.id,
        'price': "%g" % updated_quote.price,
        'total_price': "%g" % updated_quote.total_price,
        'multiple_qty': "%g" % updated_quote.product_order_multiple_quantity,
        'multiple_price': "%g" % updated_quote.order_multiple_quantity_price,
        'multiple_total_price': "%g" % updated_quote.order_multiple_total_price,
        'order_multiple': '%g' % updated_quote.product.order_multiples,
        'moq': '%g' % updated_quote.product.moq,
        'current_stock': current_stock,
        'leadtime': leadtime,
        'cost_each': "%.2f" % quotation_quantity.cost_each,
        'cost_each_multiples': "%.2f" % quotation_quantity.order_multiple_cost_each,
        'uom': updated_quote.product.uom_name_func,
        'bom_qty': updated_quote.product_quantity,
    }

    return JsonResponse(response)


class ExportToOpenERP(FormView, NpiContextMixin):
    project = False
    quote_quantity = False
    form_class = ExportSupplierInformationToOpenErpForm
    template_name = 'npi/supplier_pricing/export.html'

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('npi:viewProject', kwargs={'pk': self.project.id})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.project
        kwargs['quote_quantity'] = self.quote_quantity
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        self.quote_quantity = request.GET.get('quote_quantity')
        self.project = get_object_or_404(Project, pk=kwargs.pop('project_id'))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        return context

    def get_title(self):
        return '%s Quote Quantity Submission' % self.project


class SupplierComponentAlternativesDatatable(BaseDatatableView):
    model = SupplierComponent
    project = None

    columns = [
        'component.mpn', 'component.manufacturer', 'project_supplier.supplier_name', 'product_code',
        'mpn', 'manufacturer', 'state'
    ]
    order_columns = [
        'component.mpn', 'component.manufacturer', 'project_supplier.supplier_name', 'product_code',
        'mpn', 'manufacturer', 'state'
    ]

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs.pop('project_id'))
        return super().dispatch(request, *args, **kwargs)

    def get_initial_queryset(self):
        return super().get_initial_queryset().filter(
            component__project=self.project,
            alternative=True,
            project_supplier__enabled=True
        )


class SupplierComponentAlternativeEdit(NpiContextMixin, FormView):
    form_class = SupplierComponentAlternativeForm
    title = "Editing Supplier Alternatives State"
    project = None
    template_name = 'npi/supplier_info/alternatives.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.project
        return kwargs

    def get_success_url(self):
        return reverse('npi:viewSupplierInfo', kwargs={'pk': self.project.id})

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=self.kwargs.pop('project_id'))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        return context


def supplier_api_pricing(request, project_supplier_id):
    project_supplier = get_object_or_404(ProjectSupplier, pk=project_supplier_id)
    project_supplier.api_call()
    return HttpResponseRedirect(reverse('npi:viewSupplierInfo', kwargs={'pk': project_supplier.project_id}))
