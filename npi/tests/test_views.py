from django.test import TestCase
from npi.models import Project
from django.shortcuts import reverse
from django.test import RequestFactory
from django.views.generic import TemplateView
from npi.views import NpiContextMixin
from npi.model_views.project_views import DeleteProject
from npi.model_views.supplier_views import EditProjectSupplier, CleanProjectSupplier


class TestNpiContextMixin(TestCase):
    class DummyView(NpiContextMixin, TemplateView):
        template_name = 'npi/npi_navigation.html'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.view = cls.DummyView()

    def test_get_context_no_args(self):
        context = self.view.get_context_data()
        self.assertEqual(context['navigation_template'], 'npi/npi_navigation.html')


class TestDeleteProject(TestCase):
    fixtures = ['metrics/fixtures/metrics.erp.yaml', 'npi/fixtures/npi.json']
    multi_db = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.request_factory = RequestFactory()

    def test_get_title(self):
        view = DeleteProject()
        view.kwargs = {'pk': 1}
        self.assertEqual(view.get_title(), 'Deleting %s' % Project.objects.get(pk=1))

    def test_get_context_data(self):
        pk = 1
        view = DeleteProject()
        view.object = Project.objects.get(pk=pk)
        view.kwargs = {'pk': pk}
        self.assertIn('post_url', view.get_context_data())
        self.assertEqual(view.get_context_data()['post_url'], reverse('npi:deleteProject', kwargs={'pk': pk}))


# class TestEditProjectSuppliers(TestCase):
#     fixtures = ['metrics/fixtures/metrics.erp.yaml', 'npi/fixtures/npi.yaml']
#     multi_db = True
#
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         cls.request_factory = RequestFactory()
#
#     def test_get_title(self):
#         view = EditProjectSupplier()
#         view.kwargs = {'pk': 1}
#         view.object = Project.objects.get(pk=view.kwargs['pk'])
#         self.assertEqual(view.get_title(), '%s Edit Supplier Information' % Project.objects.get(pk=1))
#
#     def test_get_context_data(self):
#         pk = 1
#         view = EditProjectSupplier()
#         view.object = Project.objects.get(pk=pk)
#         self.assertIn('formset', view.get_context_data())
#         self.assertEqual(view.get_context_data()['project'], view.object)