from django_tables2 import *
from .models import ProjectSupplier, SupplierComponent, Component, Parent
from django.utils.html import format_html
from metrics.table_columns import NumericColumn


class ProjectSupplierInformationTable(Table):
    verbose_api_state = Column(verbose_name="API State")
    api_button = Column(verbose_name="", accessor='id')

    def render_api_button(self, value, record):
        buttons = ""
        for action in record.api_state_actions.get(record.api_state, []):
            buttons += '<a href="%(url)s" class="%(css_class)s">%(text)s</a>' % record.api_actions.get(action)
        return format_html(buttons)

    class Meta:
        model = ProjectSupplier
        fields = ['supplier_name', 'state', 'upload_date', 'enabled', 'verbose_api_state', 'excel_button']
        sequence = [
            'supplier_name', 'state', 'upload_date', 'enabled', 'api_button', 'verbose_api_state', 'excel_button'
        ]
        orderable = False
        attrs = {'class': 'table table-striped table-condensed table-hover table-bordered dataTable'}


class ComponentsWithoutQuotesTable(Table):
    awaiting_alternative_approval = BooleanColumn(accessor='awaiting_alternative_approval')

    class Meta:
        model = Component
        fields = ['manufacturer', 'mpn', 'description']
        orderable = False
        attrs = {'class': 'table table-striped table-condensed table-hover table-bordered product-dataTable'}


class BomTable(Table):

    class Meta:
        model = Parent
        fields = ['name', 'description', 'bom_uploaded']
        orderable = False
        attrs = {'class': 'table table-striped table-condensed table-hover table-bordered product-dataTable'}


class BomStructureTable(Table):
    class Meta:
        orderable = False
        attrs = {'class': 'table table-striped table-condensed table-hover table-bordered dataTable'}
        row_attrs = {
            'class': lambda record: "%(is_parent)s" % record,
            'layer': lambda record: record['layer'],
            'collapsed': 'true',
            'collapsedBelow': 'true',
            'parentCollapse': 'true',
            'style': lambda record: 'display: none' if not record['is_parent'] == 'parent' else '',
        }

    layer = Column(verbose_name='Product')
    bom_type = Column(verbose_name='Bom Type')
    procure_method = Column(verbose_name='Procurement Type')
    uom = Column(verbose_name='UOM')
    quantity = NumericColumn(verbose_name='Quantity')
    routing_name = Column(verbose_name='Routing Name')

    def render_layer(self, value, record):
        buffer = "&nbsp;&nbsp;&nbsp;&nbsp;"
        buffer_span = "<span class='bom-buffer'>%s</span>" % buffer * (value - 1)

        args = {
            'buffer': buffer_span,
            'product': "[%(product)s] %(mpn)s %(manufacturer)s (%(description)s)" % {
                'product': record['product'],
                'manufacturer': record.get('manufacturer', ''),
                'mpn': record.get('mpn', ''),
                'description': record['description']
            }
        }

        if record.get('bom_type', None):
            # on click parent row, update .bom-parent class to be 'bom-parent glyphicon glyphicon-triangle-bottom',
            # collapse all children
            return format_html(
                "<b>%(buffer)s <span class='bom-parent glyphicon glyphicon-triangle-right'></span> "
                "%(product)s </b>" % args
            )
        return format_html("%(buffer)s %(product)s" % args)

    def render_routing_name(self, value, record):
        if not record['is_parent'] == 'child':
            return value
        return ''

    def render_procure_method(self, value, record):
        if not record['is_parent'] == 'child':
            return value
        return ''
