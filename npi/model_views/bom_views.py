from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import reverse, get_object_or_404
from django.views.generic import DetailView, FormView
from npi.forms import BomUploadForm, ExportBomToOpenErpForm
from npi.models import Project, Parent, BomChildParent, BomComponent, BomParent
from npi.tables import BomTable, BomStructureTable
from npi.views import NpiContextMixin


def get_bom_template(request):
    path = 'static/npi/excel_templates/bom_template.xls'
    data = open(path, "rb")
    response = HttpResponse(data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=NPI_Bom_Template.xls'
    return response


class ViewBom(NpiContextMixin, DetailView):
    template_name = 'npi/bom/view.html'
    title = 'Bill Of Material Information'
    model = Project

    def get_navigation_buttons(self):
        buttons = self.get_object().bom_actions_available()
        for button in buttons:
            button.update({'class': button['button-class'], 'link': button['url']})
        buttons.insert(
            0, {
                'id': 'template', 'class': 'btn btn-success',
                'link': reverse('npi:getBomTemplate'), 'text': 'Excel Template'
            }
        )
        return buttons

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        context['project'] = self.get_object()
        context['parents_table'] = BomTable(Parent.objects.filter(project=self.get_object()).order_by('name'))
        if project.bom_state != "draft":
            context['bom_table'] = BomStructureTable(data=BomParent.get_bom_structure(project=project))
        return context


class UploadBom(NpiContextMixin, FormView):
    title = 'Upload BoM'
    template_name = 'npi/bom/upload.html'
    form_class = BomUploadForm
    project = None

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=self.kwargs.pop('project_id'))
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.project
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        context['parents_table'] = BomTable(Parent.objects.filter(project=self.project).order_by('name'))
        return context

    def form_valid(self, form):
        project = form.save()
        return HttpResponseRedirect(reverse('npi:viewBom', kwargs={'pk': project.id}))


class ExportToOpenERP(NpiContextMixin, FormView):
    project = False
    form_class = ExportBomToOpenErpForm
    template_name = 'npi/bom/export.html'

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('npi:viewProject', kwargs={'pk': self.project.id})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.project
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs.pop('project_id'))
        return super().dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        if self.project.bom_state == 'uploaded':
            return HttpResponseRedirect(self.get_success_url())
        return super().get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        return context

    def get_title(self):
        return '%s BOM Export' % self.project

