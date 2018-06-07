from .utils import SupplierRfqSpreadsheetGenerator, SupplierRfqExistingSpreadsheetGenerator
from collections import OrderedDict
from copy import copy
from cmass_django_generics.models import StatefulModel
from django.db import models, transaction, connections
from django.shortcuts import reverse
from django.utils import timezone
from django.utils.html import format_html
from math import ceil
from metrics.models import ProductUom
from metrics.utils import dictfetchall
from six import with_metaclass
from threading import Thread, Lock


PROJECT_SUPPLIER_INFO_STATES = {
    'draft': 'Not Started',
    'rfq': 'Awaiting Upload',
    'complete': 'Quoted',
    'uploaded': 'Uploaded'
}
PROJECT_BOM_STATES = {
    'draft': 'Awaiting X/Y Data',
    'ready': 'Ready to Upload',
    'uploaded': 'Uploaded'
}


class WorkflowInvalidActionException(Exception):
    pass


class SupplierInfoWorkflow(models.Model):
    SUPPLIER_INFO_STATES = PROJECT_SUPPLIER_INFO_STATES.copy()
    SUPPLIER_INFO_STATE_ACTIONS = {
        'draft': ['create'],
        'rfq': ['edit', 'export', 'upload', 'alternatives', 'clear'],
        'complete': ['edit', 'export', 'upload', 'alternatives', 'review', 'clear'],
        'uploaded': ['review']
    }
    SUPPLIER_INFO_STATE_PROGRESSION = {
        'draft': ['rfq'],
        'rfq': ['complete', 'draft'],
        'complete': ['draft', 'uploaded', 'rfq'],
        'uploaded': ['rfq']
    }

    @property
    def supplier_info_actions(self):
        return {
            'create': {
                'url': reverse('npi:createSupplierInfo', kwargs={'project_id': self.id}),
                'text': 'Create', 'button-class': 'btn btn-primary'
            },
            'export': {
                'url': reverse('npi:exportSupplierInfo', kwargs={'project_id': self.id}),
                'text': 'Excel', 'button-class': 'btn btn-success'
            },
            'edit': {
                'url': reverse('npi:editSupplierInfo', kwargs={'project_id': self.id}),
                'text': 'Suppliers', 'button-class': 'btn btn-default'
            },
            'upload': {
                'url': reverse('npi:uploadSupplierInfo', kwargs={'project_id': self.id}),
                'text': 'Upload', 'button-class': 'btn btn-primary'
            },
            'clear': {
                'url': reverse('npi:cleanProject', kwargs={'pk': self.id}),
                'text': 'Clear', 'button-class': 'btn btn-danger ajax-view-link'
            },
            'review': {
                'url': reverse('npi:viewSupplierInfoQuotes', kwargs={'project_id': self.id}),
                'text': 'Review', 'button-class': 'btn btn-primary'
            },
            'alternatives': {
                'url': reverse('npi:editSupplierComponentAlternatives', kwargs={'project_id': self.id}),
                'text': 'Alternatives', 'button-class': 'btn btn-default'
            }
        }

    @property
    def supplier_info_state_string(self):
        return self.SUPPLIER_INFO_STATES[self.supplier_info_state]

    @property
    def supplier_info_ready_to_complete(self):
        quotes = SupplierProductQuote.objects.filter(
            product__in=SupplierComponent.active_components.filter(component__project=self)
        )
        quoted_component_ids = [quote.product.component.id for quote in quotes]
        components_without_quotes = Component.objects.filter(project=self).exclude(id__in=quoted_component_ids)
        if not components_without_quotes:
            return True
        return False

    def wkf_supplier_info_draft(self):
        self._supplier_info_workflow_push('draft')

    def wkf_supplier_info_rfq(self):
        self._supplier_info_workflow_push('rfq')

    def wkf_supplier_info_complete(self):
        if self.supplier_info_state == 'complete':
            if not self.supplier_info_ready_to_complete:
                return self.wkf_supplier_info_rfq()
        elif self.supplier_info_ready_to_complete:
            self._supplier_info_workflow_push('complete')

    def wkf_supplier_info_uploaded(self):
        self._supplier_info_workflow_push('uploaded')

    def _supplier_info_workflow_push(self, state):
        if self.supplier_info_state == state:
            return True

        if state not in self.SUPPLIER_INFO_STATE_PROGRESSION[self.supplier_info_state]:
            raise WorkflowInvalidActionException(
                "Can't move supplier_info_state to '%(target)s' while in '%(state)s' state" % {
                    'target': state, 'state': self.supplier_info_state
                }
            )
        self.supplier_info_state = state
        self.save()
        return True

    def supplier_info_action_buttons(self):
        buttons = ''
        for action in self.supplier_info_actions_available():
            buttons += "<a href='%(url)s' class='%(button-class)s'>%(text)s</a>\n" % action
        return format_html(buttons)

    def supplier_info_actions_available(self):
        actions = []
        for action in self.SUPPLIER_INFO_STATE_ACTIONS[self.supplier_info_state]:
            actions.append(self.supplier_info_actions[action])
        return actions

    supplier_info_state = models.CharField(
        verbose_name='Supplier Information State',
        choices=[(state, PROJECT_SUPPLIER_INFO_STATES[state]) for state in PROJECT_SUPPLIER_INFO_STATES],
        default='draft',
        max_length=16
    )

    class Meta:
        abstract = True


class BomWorkflow(models.Model):
    BOM_STATES = PROJECT_BOM_STATES.copy()
    BOM_STATE_ACTIONS = {
        'draft': ['upload'],
        'ready': ['upload', 'export'],
        'uploaded': ['upload', 'export']
    }
    BOM_STATE_PROGRESSION = {
        'draft': ['ready'],
        'ready': ['uploaded'],
        'uploaded': []
    }
    bom_state = models.CharField(
        choices=[(x, PROJECT_BOM_STATES[x]) for x in PROJECT_BOM_STATES],
        verbose_name='State',
        default='draft',
        max_length=16
    )

    @property
    def bom_state_actions(self):
        return self.BOM_STATE_ACTIONS

    @property
    def bom_actions(self):
        return {
            'upload': {
                'url': reverse('npi:uploadBom', kwargs={'project_id': self.id}),
                'text': 'Upload', 'button-class': 'btn btn-default'
            },
            'clear': {
                'url': '#',
                'text': 'Clear', 'button-class': 'btn btn-danger ajax-view-link'
            },
            'export': {
                'url': reverse('npi:exportBomToOpenERP', kwargs={'project_id': self.id}),
                'text': 'Export', 'button-class': 'btn btn-primary'
            }
        }

    @property
    def bom_state_string(self):
        return self.BOM_STATES.get(self.bom_state)

    def bom_action_buttons(self):
        buttons = ''
        for action in self.bom_actions_available():
            buttons += "<a href='%(url)s' class='%(button-class)s'>%(text)s</a>\n" % action
        return format_html(buttons)

    def bom_actions_available(self):
        actions = []
        for action in self.bom_state_actions[self.bom_state]:
            actions.append(self.bom_actions[action])
        return actions

    def wkf_bom_ready(self):
        self._bom_workflow_push('ready')

    def wkf_bom_uploaded(self):
        self._bom_workflow_push('uploaded')

    def _bom_workflow_push(self, state):
        if self.bom_state == state:
            return True

        if state not in self.BOM_STATE_PROGRESSION[self.bom_state]:
            raise WorkflowInvalidActionException(
                "Can't move bom_state to '%(target)s' while in '%(state)s' state" % {
                    'target': state, 'state': self.bom_state
                }
            )
        self.bom_state = state
        self.save()
        return True

    class Meta:
        abstract = True


class Project(SupplierInfoWorkflow, BomWorkflow, models.Model):
    name = models.CharField(verbose_name='Reference', max_length=16, unique=True)
    description = models.CharField(verbose_name='Description', max_length=255, null=True)
    web_pricing = models.BooleanField(default=False)
    customer_id = models.IntegerField()
    customer_name = models.CharField(verbose_name='Customer', max_length=64)
    create_date = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.pk:
            self.create_date = timezone.now()
            self.name = self._next_name()
        super().save(*args, **kwargs)

    @staticmethod
    def _next_name():
        with transaction.atomic():
            last_project = Project.objects.all().order_by('-id').first()
            if not last_project:
                last_project_id = 1030
            else:
                last_project_id = last_project.id + 1030

            return "CM%06d" % last_project_id

    @property
    def products(self):
        products = ""
        for parent in Parent.objects.filter(project=self).order_by('name'):
            products += "%s, " % parent
        return products[:-2]

    @property
    def quotation_quantities(self):
        string = ''
        for quantity in QuoteQuantity.objects.filter(project=self).order_by('quantity'):
            string += "%g, " % quantity.quantity
        return string[:-2]

    @property
    def bom_state_actions(self):
        actions = copy(super().bom_state_actions)
        if self.supplier_info_state != 'uploaded':
            for state in actions:
                actions[state] = [x for x in actions[state] if x != 'export']
        return actions

    @property
    def bom_state_string(self):
        if self.bom_state == 'ready' and self.supplier_info_state != 'uploaded':
            return "Bom Loaded, Awaiting Supplier Info upload"
        return super().bom_state_string

    def _bom_workflow_push(self, state):
        with transaction.atomic():
            result = super()._bom_workflow_push(state)
        if state == 'uploaded' and self.supplier_info_state != 'uploaded':
            raise WorkflowInvalidActionException("Cant export bom before supplier info has been exported")
        return result

    def component_mpn_vs_supplier_order_code_missmatch(self):
        """
        Check if OpenERP has records where product_supplierinfo.product_code matches supplier_component.product_code
        but the product_supplierinfo.mpn doesn't match the supplier_component.mpn
        :return:
        """
        active_components = SupplierComponent.active_components.filter(project_supplier__project=self)

        cursor = connections['erp'].cursor()
        cursor.execute("""
        SELECT product_code AS order_code, manufacturer_part_no AS mpn, name AS supplier_id
        FROM product_supplierinfo
        WHERE product_code = ANY (%(order_codes)s)        
        """, {
            'mpns': [x.mpn for x in active_components],
            'order_codes': [x.product_code for x in active_components]
        })
        existing_order_codes = {}

        for result in dictfetchall(cursor):
            order_codes = existing_order_codes.get(result['supplier_id'], {})
            mpns = order_codes.get(result['order_code'], set())
            mpns.add(result['mpn'])
            order_codes[result['order_code']] = mpns
            existing_order_codes[result['supplier_id']] = order_codes

        for supplier_id in set([x.project_supplier.supplier_id for x in active_components.all()]):
            x = existing_order_codes.get(supplier_id)
            if x:
                print("%s: %s" % (supplier_id, x))
            # Don't create a new product with a duplicate supplierinfo_product_code
            # Check if the product will be created - Does it matter if im using an existing product?


        print("\n")

        return bool(existing_order_codes)

    def __str__(self):
        return self.name


class QuoteQuantity(models.Model):
    quantity = models.FloatField(verbose_name='Quantity')
    project = models.ForeignKey(Project)

    @property
    def order_multiple_cost_total(self):
        cost = 0
        for component in Component.objects.filter(project=self.project):
            cost += component.selected_quote(self).order_multiple_total_price
        return cost

    @property
    def order_multiple_cost_each(self):
        return self.order_multiple_cost_total / self.quantity

    @property
    def cost_total(self):
        cost = 0
        for component in Component.objects.filter(project=self.project):
            cost += component.selected_quote(self).total_price
        return cost

    @property
    def cost_each(self):
        return self.cost_total / self.quantity

    def export_data_for_openerp(self):
        data = {}
        for parent in Parent.objects.filter(project=self.project):
            parents = data.get('parents', dict())
            parents.update({
                str(parent.id): {
                    'product_details': parent.export_as_openerp_product_product(),
                    'orderpoint': parent.export_as_openerp_orderpoint(),
                    'children': {
                        str(child.component.id): {'qty': child.quantity, 'uom_id': child.component.uom_id}
                        for child in ParentComponent.objects.filter(parent=parent)
                    },
                    'bom_details': parent.export_as_openerp_parent_bom()
                }
            })
            data['parents'] = parents

        for component in Component.objects.filter(project=self.project):
            components = data.get('components', dict())
            components.update({
                str(component.id): {
                    'mpn': component.mpn, 'manufacturer': component.manufacturer,
                    'product_details': component.export_component_as_openerp_product_product(self),
                    'orderpoint': component.export_component_orderpoint_as_openerp_product_product(self)
                }
            })

            supplier_info = {}

            # Get selected supplierinfo and set it to sequence 10
            selected_supplierinfo = component.selected_quote(self).product
            supplier_info.update(SupplierComponent.openerp_product_supplierinfo_dictionary(selected_supplierinfo, 10))
            supplier_info[str(selected_supplierinfo.id)]['product_supplierinfo']['sequence'] = 10

            # All other supplierinfo records to be sequence 20
            for product in SupplierComponent.objects.filter(component=component).exclude(id=selected_supplierinfo.id):
                supplier_info.update(SupplierComponent.openerp_product_supplierinfo_dictionary(product, 20))

            components[str(component.id)]['supplier_info'] = supplier_info
            data['components'] = components
        return data

    def save(self, *args, **kwargs):
        if self.quantity <= 0:
            raise ValueError("Quantity '%s' is invalid! Must be > 0" % self.quantity)
        return super().save(*args, **kwargs)

    def __str__(self):
        return "%g" % self.quantity


class Parent(models.Model):
    project = models.ForeignKey(Project)
    name = models.CharField(verbose_name='Parent Product', max_length=64)
    description = models.TextField(verbose_name='Description')
    quantity = models.FloatField(verbose_name='Quantity')
    uom_id = models.IntegerField()
    uom_name = models.CharField(max_length=16)
    procure_method = models.CharField(
        max_length=16,
        default='make_to_order',
        choices=[('make_to_order', 'Make To Order'), ('make_to_stock', 'Make To Stock')]
    )
    routing_name = models.CharField(max_length=16)
    routing_id = models.IntegerField()
    hscomcode = models.CharField(default='0000000000', max_length=10)
    eccn = models.CharField(default='ECL99', max_length=16)
    product_id = models.IntegerField(null=True)
    bom_uploaded = models.BooleanField(default=False)

    def export_as_openerp_product_product(self):
        return {
            'default_code': self.name,
            'name': "%(mpn)s %(description)s" % {'mpn': self.name, 'description': self.description},
            'description': "%(mpn)s %(description)s" % {'mpn': self.name, 'description': self.description},
            'description_purchase': "%(mpn)s %(description)s" % {'mpn': self.name, 'description': self.description},
            'description_sale': self.description,
            'procure_method': self.procure_method,
            'supply_method': 'produce',
            'type': 'product',
            'sale_ok': True,
            'purchase_ok': False,
            'state': 'sellable',
            'uom_id': self.uom_id,
            'uom_po_id': self.uom_id,
            'standard_price': 0,
            'cost_method': 'average',
            'hscomcode': self.hscomcode or '0000000000',
            'eccn': self.eccn or 'ECL99',
            'moisture_sensitivity': '1'
        }

    def export_as_openerp_orderpoint(self):
        return {
            'warehouse_id': 1,
            'location_id': 12,
            'product_min_qty': 0,
            'product_max_qty': 0,
            'qty_multiple': 1,
            'product_uom': self.uom_id
        }

    def export_as_openerp_parent_bom(self):
        return {
            'name': self.name,
            'code': self.name,
            'type': 'normal',
            'product_qty': self.quantity,
            'product_uom': self.uom_id,
            'product_efficiency': 1,
            'routing_id': self.routing_id
        }

    def __str__(self):
        return self.name


class Component(models.Model):
    project = models.ForeignKey(Project)
    mpn = models.CharField(verbose_name='MPN', max_length=64)
    manufacturer = models.CharField(verbose_name="Manufacturer", max_length=64)
    uom_id = models.IntegerField(verbose_name='Unit Of Measure ID')
    uom_name = models.CharField(verbose_name='UOM', max_length=16)
    description = models.TextField(verbose_name="Description")
    msl = models.IntegerField(verbose_name='Moisture Sensitivity Level', null=True, blank=True)
    product_id = models.IntegerField(null=True)
    product_code = models.CharField(verbose_name="Product Code", max_length=200, null=True)

    @property
    def number_of_suppliers_quoted(self):
        return len(SupplierComponent.objects.filter(component=self))

    @property
    def quantity(self):
        quantity = 0
        for record in ParentComponent.objects.filter(component=self):
            quantity += record.real_quantity
        return quantity

    @property
    def awaiting_alternative_approval(self):
        if SupplierComponent.objects.filter(component=self, project_supplier__enabled=True, state='pending'):
            return True
        return False

    def _will_generate_new_openerp_product_product(self):
        if self.product_id:
            return False

        mpns = [x.mpn for x in SupplierComponent.objects.filter(component=self)]

        if not mpns:
            return False
        cursor = connections['erp'].cursor()
        cursor.execute("""SELECT count(id) FROM product_supplierinfo WHERE manufacturer_part_no = ANY(%s)""", (mpns,))
        matching



    def selected_quote(self, quotation_quantity):
        """
        Return the price of the selected supplier or the cheapest price
        May return None
        """
        selected_quote = SupplierProductQuote.objects.filter(
            product__component=self, quote_quantity=quotation_quantity, selected=True
        ).first()
        if selected_quote:
            return selected_quote
        return self.default_quote(quotation_quantity)

    def default_quote(self, quotation_quantity):
        """Default to cheapest price as per DJess"""
        return self.cheapest_supplier_quote(quotation_quantity)

    def selected_quote_price(self, quotation_quantity):
        selected_quote = self.selected_quote(quotation_quantity)
        if not selected_quote:
            raise ValueError("Component pk:'%s' has no quotes" % self.pk)
        return selected_quote.price * selected_quote.order_multiple_quantity_price

    def edit_selected_quote(self, quotation_quantity):
        from django.template.loader import render_to_string
        from npi.forms import SelectSupplierComponentForm

        if self.project.supplier_info_state == 'uploaded':
            return str(self.selected_quote(quotation_quantity).product)

        return render_to_string(
            'npi/supplier_pricing/edit.html',
            {'form': SelectSupplierComponentForm(component=self, quote_quantity=quotation_quantity)}
        )

    def cheapest_supplier_quote(self, quotation_quantity):
        return SupplierProductQuote.objects.filter(
            quote_quantity=quotation_quantity, product__in=SupplierComponent.active_components.filter(component=self)
        ).order_by('price').first()

    def cheapest_supplier_quote_moq(self, quotation_quantity):
        quotes = SupplierProductQuote.objects.filter(
            quote_quantity=quotation_quantity, product__in=SupplierComponent.active_components.filter(component=self)
        )
        cheapest = None
        if quotes:
            cheapest = min(quotes, key=lambda x: x.order_multiple_quantity_price)
        return cheapest

    def export_component_as_openerp_product_product(self, quotation_quantity):
        selected_quote = self.selected_quote(quotation_quantity)
        return {
            'name': "%(mpn)s %(description)s" % {'mpn': self.mpn, 'description': self.description},
            'description': "%(mpn)s %(description)s" % {'mpn': self.mpn, 'description': self.description},
            'description_purchase': "%(mpn)s %(description)s" % {'mpn': self.mpn, 'description': self.description},
            'description_sale': self.description,
            'type': 'product',
            'sale_ok': False,
            'state': 'sellable',
            'uom_id': self.uom_id,
            'uom_po_id': selected_quote.product.uom_id,
            'standard_price': 0,
            'cost_method': 'average',
            'hscomcode': '0000000000',
            'eccn': 'ECL99',
            'moisture_sensitivity': '1'
        }

    def export_component_orderpoint_as_openerp_product_product(self, quotation_quantity):
        multiple = self.selected_quote(quotation_quantity).product.order_multiples
        return {
            'warehouse_id': 1,
            'location_id': 12,
            'product_min_qty': 0,
            'product_max_qty': 0,
            'qty_multiple': multiple if multiple > 0 else 1,
            'product_uom': self.uom_id
        }

    def __str__(self):
        return "%s %s" % (self.manufacturer, self.mpn)


class Designator(models.Model):
    designator = models.CharField(max_length=16)
    component = models.ForeignKey(Component)

    class Meta:
        unique_together = ('designator', 'component')


class ParentComponent(models.Model):
    parent = models.ForeignKey(Parent)
    component = models.ForeignKey(Component)
    quantity = models.FloatField()

    @property
    def real_quantity(self):
        return self.quantity * self.parent.quantity


class ProjectSupplierApiWorkflow(with_metaclass(StatefulModel, models.Model)):
    @property
    def verbose_api_state(self):
        return self.API_STATES[self.api_state]

    api_state_progression = {
        'pending': ['error', 'finished', 'finished_with_errors'],
        'ready': ['pending'],
        'finished': [],
        'finished_with_errors': ['pending'],
        'error': [],
        'inactive': []
    }

    @property
    def api_state_actions(self):
        return {
            'pending': [],
            'ready': [],
            'finished': [],
            'finished_with_errors': [],
            'error': [],
            'inactive': []
        }

    def api_workflow_push(self, state):
        with transaction.atomic():
            if state not in self.api_state_progression.get(self.api_state, {}):
                raise WorkflowInvalidActionException("Can't progress from '%(state)s' to '%(target)s' state" % {
                    'state': self.api_state, 'target': state
                })

            func = getattr(self, 'wkf_api_%s' % state, None)
            if func:
                return func()
            self.api_state = state
            self.save()

    @property
    def api_actions(self):
        return {
            'price': {
                'url': reverse('npi:getSupplierPricingApi', kwargs={'project_supplier_id': self.id}),
                'css_class': 'btn btn-default', 'text': 'API Price',
            },
            'retry': {
                'url': reverse('npi:getSupplierPricingApi', kwargs={'project_supplier_id': self.id}),
                'css_class': 'btn btn-default', 'text': 'Retry %s errors' % len(self.failed_api_calls)
            }
        }

    @property
    def failed_api_calls(self):
        return []

    def wkf_api_pending(self):
        self.api_state = 'pending'
        self.save()

    def wkf_api_finished(self):
        self.api_state = 'finished'
        self.save()

    def wkf_api_error(self):
        self.api_state = 'error'
        self.save()

    def wkf_api_finished_with_errors(self):
        self.wkf_api_finished()
        self.api_state = 'finished_with_errors'
        self.save()

    class Meta:
        _states = {
            'pending': 'In-Progress',
            'ready': 'Ready',
            'finished': 'Complete',
            'finished_with_errors': 'Completed with Errors',
            'error': 'Error!',
            'inactive': ''
        }
        _state_prefix = 'api'
        _state_verbose = 'Api State'
        _state_default = 'ready'
        abstract = True


class ProjectSupplier(ProjectSupplierApiWorkflow):
    project = models.ForeignKey(Project)
    supplier_id = models.IntegerField()
    supplier_name = models.CharField(max_length=128)
    uploaded = models.BooleanField(default=False)
    upload_date = models.DateTimeField(null=True)
    enabled = models.BooleanField(default=True)

    class Meta:
        unique_together = ('project', 'supplier_id')

    def _api_state_default(self):
        if self.api_class:
            return 'ready'
        return 'inactive'

    def save(self, *args, **kwargs):
        if not self.pk:
            self.api_state = self._api_state_default()
        return super().save(*args, **kwargs)

    @property
    def api_class(self):
        from npi.product_api.api import SUPPLIER_MAP
        return SUPPLIER_MAP.get(self.supplier_id)

    @property
    def failed_api_calls(self):
        return SupplierApiFailedSearch.objects.filter(project_supplier=self)

    @property
    def api_state_actions(self):
        return {
            'pending': [],
            'ready': ['price'] if self.api_class and not self.uploaded else [],
            'finished': [],
            'finished_with_errors': ['retry'],
            'error': [],
            'inactive': []
        }

    def api_call(self):
        thread = Thread(target=self.api_class(self).update_supplier_info)
        thread.daemon = True
        thread.start()

    def wkf_api_finished(self):
        result = super().wkf_api_finished()
        self.upload()
        self.project.wkf_supplier_info_complete()
        return result

    def upload(self):
        self.uploaded = True
        self.upload_date = timezone.now()
        self.save()

    @property
    def excel_button(self):
        button = ''
        if self.uploaded:
            button = "<a href='%(url)s' class='%(button-class)s'>%(text)s</a>" % {
                'url': reverse('npi:exportSupplierInfoExistingExcel', kwargs={'project_supplier_id': self.id}),
                'button-class': 'btn btn-success',
                'text': 'Excel',
            }
        return format_html(button)

    @property
    def state(self):
        if self.uploaded:
            return "Uploaded"
        return "Pending"

    def generate_rfq_spreadsheet(self):
        return SupplierRfqSpreadsheetGenerator(self).get_spreadsheet()

    def generate_existing_spreadsheet(self):
        return SupplierRfqExistingSpreadsheetGenerator(self).get_spreadsheet()

    def __str__(self):
        return self.supplier_name


SUPPLIER_COMPONENT_STATES = {'normal': 'Accepted', 'reject': 'Rejected', 'pending': 'Pending'}


class SupplierComponentManagerActiveComponents(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(state='normal', project_supplier__enabled=True)


class SupplierComponent(models.Model):
    STATES = SUPPLIER_COMPONENT_STATES.copy()

    @property
    def uom_name_func(self):
        uom = ProductUom.objects.filter(id=self.uom_id).first()
        if uom:
            return uom.name
        return "ERROR"

    component = models.ForeignKey(Component)
    project_supplier = models.ForeignKey(ProjectSupplier)
    product_code = models.CharField(max_length=64)
    description = models.TextField()
    manufacturer = models.CharField(max_length=64, null=True)
    mpn = models.CharField(max_length=64, null=True)
    uom_id = models.IntegerField()
    uom_name = models.CharField(verbose_name='UOM', max_length=16)
    moq = models.FloatField()
    order_multiples = models.FloatField()
    current_stock = models.FloatField(null=True)
    leadtime = models.IntegerField(null=True)
    sequence = models.IntegerField(default=10)
    alternative = models.BooleanField(default=False)
    state = models.CharField(
        verbose_name='State',
        choices=[(state, SUPPLIER_COMPONENT_STATES[state]) for state in SUPPLIER_COMPONENT_STATES],
        default='normal',
        max_length=16
    )
    objects = models.Manager()
    active_components = SupplierComponentManagerActiveComponents()

    def wkf_normal(self):
        with transaction.atomic():
            self.state = 'normal'
            self.save()
            self.component.project.wkf_supplier_info_complete()

    def wkf_rejected(self):
        with transaction.atomic():
            self.state = 'reject'
            self.save()
            self.component.project.wkf_supplier_info_complete()

    def wkf_pending(self):
        with transaction.atomic():
            self.state = 'pending'
            self.save()
            self.component.project.wkf_supplier_info_complete()

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.mpn.lower() != self.component.mpn.lower() or \
                    self.manufacturer.lower() != self.component.manufacturer.lower():
                self.state = 'pending'
                self.alternative = True

        return super().save(*args, **kwargs)

    def openerp_product_supplierinfo_dictionary(self, sequence):
        return {
            str(self.id): {
                'product_supplierinfo': {
                    'sequence': sequence,
                    'delay': self.leadtime or 0,
                    'min_qty': self.moq,
                    'product_code': self.product_code,
                    'product_name': self.description,
                    'manufacturer_name': self.manufacturer,
                    'manufacturer_part_no': self.mpn,
                    'name': self.project_supplier.supplier_id
                },
                'pricelist_partnerinfo': SupplierProductQuote.openerp_pricelist_partnerinfo_dictionary(self)
            }
        }

    def __str__(self):
        return "%s: %s" % (self.project_supplier, self.product_code)


class SupplierApiDailyUsage(models.Model):
    supplier_id = models.IntegerField()
    request_count = models.IntegerField(default=0)
    date = models.DateField(default=timezone.now)

    mutex = Lock()

    class Meta:
        unique_together = ('supplier_id', 'date')

    @classmethod
    def inc(cls, supplier_id):
        with cls.mutex:
            record, created = SupplierApiDailyUsage.objects.get_or_create(supplier_id=supplier_id, date=timezone.now().date())
            record.request_count += 1
            record.save()


class SupplierApiFailedSearch(models.Model):
    project_supplier = models.ForeignKey(ProjectSupplier)
    component = models.ForeignKey(Component)


class SupplierProductQuote(models.Model):
    product = models.ForeignKey(SupplierComponent)
    quote_quantity = models.ForeignKey(QuoteQuantity)
    price = models.FloatField()
    selected = models.BooleanField(default=False)

    @property
    def product_quantity(self):
        product_quantity = self.product.component.quantity

        if self.product.uom_id != self.product.component.uom_id:
            component_uom = ProductUom.objects.get(id=self.product.component.uom_id)
            component_factor = float(1 / component_uom.factor) if component_uom.uom_type == 'smaller'\
                else float(component_uom.factor)

            # convert to reference unit
            reference_unit = component_factor * product_quantity

            supplier_product_uom = ProductUom.objects.get(id=self.product.uom_id)
            supplier_factor = float(1 / supplier_product_uom.factor) if supplier_product_uom.uom_type == 'bigger' \
                else float(supplier_product_uom.factor)

            target_unit = reference_unit * supplier_factor
            product_quantity = target_unit
        return product_quantity * self.quote_quantity.quantity

    @property
    def total_price(self):
        return self.price * self.product_quantity

    @property
    def product_order_multiple_quantity(self):
        """"Using the Order Multiples, work out the actual quantity of products which will be purchased"""
        quantity = self.product_quantity
        multiple = self.product.order_multiples

        # Hack to prevent division by 0
        if multiple in [0, 1]:
            return quantity
        if self.product.order_multiples < 0:
            raise ValueError(
                "SupplierProductQuote pk:'%(pk)s' multiple:'%(multiple)s"
                " Can't calculate negative order multiple" % {
                    'pk': self.pk, 'multiple': self.product.order_multiples
                }
            )
        return ceil(quantity/multiple) * multiple

    @property
    def order_multiple_quantity_price(self):
        """Price of the actual order when considering order multiples"""
        return (self.price * self.product_order_multiple_quantity) / self.product_quantity

    @property
    def order_multiple_total_price(self):
        return self.product_order_multiple_quantity * self.price

    def select(self):
        if not SupplierComponent.active_components.filter(id=self.product.id).first():
            raise ValueError("Supplier component '%s' is not active." % self.product)

        quotes = SupplierProductQuote.objects.filter(
            product__component=self.product.component,
            quote_quantity=self.quote_quantity
        ).exclude(pk=self.pk)

        with transaction.atomic():
            for quote in quotes:
                quote.selected = False
                quote.save()

            self.selected = True
            self.save()

    @staticmethod
    def get_excel_data(quantities, project):
        return [
            [quantity, [OrderedDict([
                ('manufacturer', x.product.component.manufacturer),
                ('mpn', x.product.component.mpn),
                ('description', x.product.description),
                ('cheapest_product', str(x.product.component.cheapest_supplier_quote(quantity).product)),
                ('cheapest_price', x.product.component.cheapest_supplier_quote(quantity).price),
                ('cheapest_multiple_product', str(x.product.component.cheapest_supplier_quote_moq(quantity).product)),
                ('cheapest_multiple_price', x.product.component.cheapest_supplier_quote_moq(quantity).price),
                ('preferred_supplier_product', x.product.component.edit_selected_quote(quantity)),
                ('uom', x.product.component.uom_name),
                ('bom_qty', x.product_quantity),
                ('price', x.price),
                ('total_cost', x.total_price),
                ('purchase_quantity', x.product_order_multiple_quantity),
                ('purchase_cost', x.order_multiple_quantity_price),
                ('total_purchase_cost', x.order_multiple_total_price),
                ('multiples', x.product.order_multiples),
                ('moq', x.product.moq),
                ('current_stock', x.product.current_stock),
                ('leadtime', x.product.leadtime),
                ('selected', 'True' if x == x.product.component.selected_quote(quantity) else 'False'),
                ('supplier_quote_id', x.id),
                ('supplier', str(x.product.project_supplier)),
                ('supplier_product_code', x.product.product_code)
                ]) for x in SupplierProductQuote.objects.filter(quote_quantity=quantity).filter(
                    product__component__project=project).order_by('product__component')
            ]] for quantity in quantities]

    @staticmethod
    def openerp_pricelist_partnerinfo_dictionary(supplier_component):
        """
        outputs all quotes related to a supplier_component in a format suitable for uploading to OpenERP
        If there are no quotes for Quantity 1, the highest price will be linked to quantity 1
        :return {
            SupplierProductQuote.id {
                min_quantity: float(), price: float()
            }
        }
        """
        pricelist = {}
        has_qty_1 = False

        quotes = SupplierProductQuote.objects.filter(product=supplier_component).order_by('-price')

        for quote in quotes:
            if quote.product_quantity <= 1:
                has_qty_1 = True

            pricelist.update({
                str(quote.id): {
                    'min_quantity': quote.product_quantity,
                    'price': quote.price
                }
            })
        if pricelist and not has_qty_1:
            pricelist.update({
                '0': {
                    'min_quantity': 1,
                    'price': quotes.first().price
                }
            })
        return pricelist

    def __str__(self):
        return "%s: %s" % (self.quote_quantity.quantity, self.price)


class BomParent(models.Model):
    project = models.ForeignKey(Project)
    product_code = models.CharField(max_length=64)
    description = models.CharField(max_length=128)
    quantity = models.FloatField()
    uom_id = models.IntegerField()
    uom_name = models.CharField(max_length=16)
    routing_name = models.CharField(max_length=16)
    routing_id = models.IntegerField()
    procure_method = models.CharField(
        max_length=16,
        choices=[('make_to_order', 'Make to Order'), ('make_to_stock', 'Make to Stock')]
    )

    def get_descendant_parents(self):
        result = []
        children = BomChildParent.objects.filter(parent=self)
        while children:
            products = [x.product for x in children]
            result.extend(products)
            children = BomChildParent.objects.filter(parent__in=products)
        return result

    @staticmethod
    def top_level_products(project):
        """BomParents which are never referenced as children"""
        return BomParent.objects.filter(project=project).exclude(
            id__in=[x.product.id for x in BomChildParent.objects.filter(product__project=project)]
        )

    @staticmethod
    def export_bom_openerp(project):
        res = {
            'bom_parents': {},
            'bom_child_parents': {},
            'bom_components': {},
        }

        top_level_products = [x.product_code for x in BomParent.top_level_products(project)]

        for parent in BomParent.objects.filter(project=project):
            res['bom_parents'][str(parent.id)] = {
                'product':  {
                    'default_code': parent.product_code,
                    'name': parent.description,
                    'description': parent.description,
                    'description_purchase': parent.description,
                    'description_sale': parent.description,
                    'procure_method': parent.procure_method,
                    'supply_method': 'produce',
                    'type': 'product',
                    'sale_ok': parent.product_code in top_level_products,
                    'purchase_ok': False,
                    'state': 'sellable',
                    'uom_id': parent.uom_id,
                    'uom_po_id': parent.uom_id,
                    'standard_price': 0,
                    'cost_method': 'average',
                    'hscomcode': '0000000000',
                    'eccn': 'ECL99',
                    'moisture_sensitivity': '1'
                },
                'bom': {
                    'name': parent.product_code,
                    'code': parent.product_code,
                    'type': 'normal',
                    'product_qty': parent.quantity,
                    'product_uom': parent.uom_id,
                    'product_efficiency': 1,
                    'routing_id': parent.routing_id,
                }
            }

        for bom_child_parent in BomChildParent.objects.filter(product__project=project):
            res['bom_child_parents'][str(bom_child_parent.id)] = {
                'product': str(bom_child_parent.product.id),
                'parent': str(bom_child_parent.parent.id),
                'product_qty': bom_child_parent.quantity,
                'product_uom': bom_child_parent.uom_id,
                'type': bom_child_parent.bom_type
            }

        for component in BomComponent.objects.filter(parent__project=project):
            res['bom_components'][str(component.id)] = {
                'product_id': component.component.product_id,
                'product_qty': component.quantity,
                'product_uom': component.uom_id,
                'parent': str(component.parent.id)
            }
        return res

    def get_bom_type(self):
        return getattr(BomChildParent.objects.filter(parent=self).first(), 'bom_type', None)

    @staticmethod
    def get_bom_data(parent, bom_list=None, layer=1):
        bom_list = bom_list or list()
        bom_list.append({
            'product': parent.product.product_code,
            'description': parent.product.description,
            'bom_type': parent.bom_type,
            'procure_method': parent.product.procure_method,
            'uom': parent.uom_name,
            'quantity': parent.quantity,
            'layer': layer,
            'routing_name': parent.product.routing_name,
            'is_parent': "parent-child"
        })
        for component in BomComponent.objects.filter(parent=parent.product):
            bom_list.append({
                'product': component.component.product_code,
                'description': component.component.description,
                'bom_type': '',
                'procurement_type': component.parent.procure_method,
                'uom': component.uom_name,
                'quantity': component.quantity,
                'mpn': component.component.mpn,
                'manufacturer': component.component.manufacturer,
                'layer': layer + 1,
                'is_parent': "child"
            })
        for child_parent in BomChildParent.objects.filter(parent=parent.product):
            BomParent.get_bom_data(child_parent, bom_list, layer + 1)
        return bom_list

    @staticmethod
    def get_bom_structure(project):
        bom_list = []
        for parent in BomParent.objects.filter(project=project).exclude(
                id__in=[x.product.id for x in BomChildParent.objects.filter(product__project=project.id)]
        ):
            bom_list.append({
                'product': parent.product_code,
                'description': parent.description,
                'bom_type': parent.get_bom_type(),
                'procure_method': parent.procure_method,
                'uom': parent.uom_name,
                'quantity': parent.quantity,
                'layer': 1,
                'routing_name': parent.routing_name,
                'is_parent': "parent"
            })
            for child_parent in BomChildParent.objects.filter(parent=parent):
                bom_list.extend(BomParent.get_bom_data(parent=child_parent, layer=2))

        return bom_list


class BomChildParent(models.Model):
    product = models.ForeignKey(BomParent, related_name='product')
    parent = models.ForeignKey(BomParent, related_name='parent')
    quantity = models.FloatField()
    uom_id = models.IntegerField()
    uom_name = models.CharField(max_length=16)
    bom_type = models.CharField(max_length=16, choices=[('phantom', 'phantom'), ('normal', 'normal')])


class BomComponent(models.Model):
    parent = models.ForeignKey(BomParent, null=True, blank=True)
    component = models.ForeignKey(Component)
    quantity = models.FloatField()
    uom_id = models.IntegerField()
    uom_name = models.CharField(max_length=16)

