from cmass_django_generics.views import CmassDeleteView
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import reverse, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView, DetailView
from cmass_django_datatables_view.base_datatable_view import BaseDatatableView
from npi.views import NpiContextMixin
from npi.forms import CreateProjectForm, ProjectBomUpdateForm, ProjectForm
from npi.models import Project, Component, Parent, ParentComponent


def get_project_template(request):
    path = 'static/npi/excel_templates/project_template.xlsx'
    data = open(path, "rb")
    response = HttpResponse(data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=NPI_Project_Template.xlsx'
    return response


class CreateProject(NpiContextMixin, FormView):
    title = 'Create Project'
    template_name = 'npi/project/create.html'
    form_class = CreateProjectForm

    def form_valid(self, form):
        project = form.save()
        return HttpResponseRedirect(reverse('npi:viewProject', kwargs={'pk': project.id}))

    def get_navigation_buttons(self):
        return [
            {'id': 'template', 'class': 'btn btn-success', 'link': reverse('npi:getProjectTemplate'),
             'text': 'Excel Template'}
        ]


class ListProject(NpiContextMixin, TemplateView):
    title = 'Projects'
    template_name = 'npi/project/list.html'

    def get_navigation_buttons(self):
        return [
            {'id': 'createButton', 'class': 'btn btn-primary', 'link': reverse('npi:createProject'), 'text': 'Create'},
            {'id': 'template', 'class': 'btn btn-success', 'link': reverse('npi:getProjectTemplate'),
             'text': 'Excel Template'}
        ]


class EditProject(NpiContextMixin, FormView):
    template_name = 'npi/project/edit.html'
    form_class = ProjectForm
    project = None

    def get_title(self):
        return "Edit %s" % self.project

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.project
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        return context

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs.pop('project_id', None))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        project = form.save()
        return HttpResponseRedirect(reverse('npi:viewProject', kwargs={'pk': project.id}))


class ViewProject(NpiContextMixin, DetailView):
    template_name = 'npi/project/view.html'
    model = Project

    def get_title(self):
        return "Project %s" % self.get_object()

    def get_navigation_buttons(self):
        return [
            {
                'id': 'editButton',
                'class': 'btn btn-primary',
                'link': reverse('npi:editProject', kwargs={'project_id': self.get_object().pk}),
                'text': 'Edit'
            },
            {
                'id': 'updateButton',
                'class': 'btn btn-warning',
                'link': reverse('npi:updateProjectBom', kwargs={'pk': self.get_object().pk}),
                'text': 'Update Bom'
            },
            {
                'id': 'deleteButton',
                'class': 'btn btn-danger ajax-view-link',
                'link': reverse('npi:deleteProject', kwargs={'pk': self.get_object().pk}),
                'text': 'Delete'
            },
        ]


class ProjectDatatable(BaseDatatableView):
    model = Project
    columns = [
        'name', 'customer_name', 'description', 'products', 'supplier_info_state_string',
        'bom_state_string', 'create_date'
    ]
    order_columns = [
        'name', 'customer_name', 'description', 'products', 'supplier_info_state_string',
        'bom_state_string', 'create_date'
    ]
    calculated_columns = ['customer_name', 'products', 'bom_state_string', 'supplier_info_state_string']

    def render_name(self, record):
        return "<a href=%(url)s>%(name)s</a>" % {
            'url': reverse('npi:viewProject', kwargs={'pk': record.id},),
            'name': record.name
        }

    def render_create_date(self, record):
        return record.create_date.strftime('%Y-%m-%d')

    def order_customer_name(self, queryset, reverse=False):
        return sorted(list(queryset), key=lambda x: x.customer_name, reverse=reverse)

    def order_products(self, queryset, reverse=False):
        return sorted(list(queryset), key=lambda x: x.products, reverse=reverse)

    def order_supplier_info_state_string(self, queryset, reverse=False):
        return sorted(list(queryset), key=lambda x: x.supplier_info_state_string, reverse=reverse)

    def order_bom_state_string(self, queryset, reverse=False):
        return sorted(list(queryset), key=lambda x: x.bom_state_string, reverse=reverse)


class ProjectProductComponentDatatable(BaseDatatableView):
    model = ParentComponent
    columns = [
        'component.product_code', 'parent.name', 'parent.description', 'parent.quantity', 'parent.routing_name',
        'component.mpn', 'component.manufacturer', 'component.description', 'quantity', 'component.uom_name',
        'component.number_of_suppliers_quoted'
    ]
    order_columns = [
        'component.product_code', 'parent.name', 'parent.description', 'parent.quantity', 'parent.routing_name',
        'component.mpn', 'component.manufacturer', 'component.description', 'quantity', 'component.uom_name',
        'component.number_of_suppliers_quoted'
    ]
    filter_icontains = ['component.description']
    calculated_columns = ['component.uom_name', 'component.number_of_suppliers_quoted']

    def get_initial_queryset(self):
        qs = super().get_initial_queryset()
        if self._querydict.get('project_id'):
            qs = qs.filter(parent__project_id=self._querydict.get('project_id'))
        return qs.order_by('parent__name', 'component__manufacturer', 'component__mpn')

    def render_component__product_code(self, record):
        if record.product_code:
            return "<a href='http://%(url)s:8069/?db=cmasscrm#" \
                   "id=%(product_id)s&view_type=form&model=product.product&menu_id=564&action=122' target='_blank'>" \
                   " %(product_code)s </a>" % {
                        'product_id': record.product_id, 'product_code': record.product_code,
                        'url': settings.OPENERP_URL
                   }
        return ""

    def render_parent__name(self, record):
        value = record.name
        if record.product_id:
            value = "<a href='http://%(url)s:8069/?db=%(db)s#" \
                    "id=%(product_id)s&view_type=form&model=product.product&menu_id=564&action=122' target='_blank'>" \
                    " %(product_code)s </a>" % {
                        'product_id': record.product_id,
                        'product_code': value,
                        'url': settings.OPENERP_URL,
                        'db': settings.OPENERP_DATABASE
                    }
        return value

    def order_component__uom_name(self, queryset, reverse=False):
        return sorted(list(queryset), key=lambda x: x.component.uom_name, reverse=reverse)

    def order_number_of_suppliers_quoted(self, queryset, reverse=False):
        return sorted(list(queryset), key=lambda x: x.number_of_suppliers_quoted, reverse=reverse)


class DeleteProject(NpiContextMixin, CmassDeleteView):
    model = Project
    success_url = reverse_lazy('npi:listProjects')
    template_name = 'npi/project/delete.html'
    modal_id = 'deleteProject'

    def get_post_url(self):
        return reverse('npi:deleteProject', kwargs={'pk': self.get_object().id})

    def get_title(self):
        return 'Deleting %s' % self.get_object()

    def get_cancel_url(self):
        return reverse('npi:viewProject', kwargs={'pk': self.get_object().id})


class UpdateProjectBom(NpiContextMixin, FormView):
    form_class = ProjectBomUpdateForm
    template_name = 'npi/project/update.html'
    project = None

    def get_title(self):
        return "%s Update BOM" % self.project

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(reverse('npi:viewProject', kwargs={'pk': self.project.id}))

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs.pop('pk'))
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.project
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        return context
