from django_tables2 import Column
from django.utils.html import format_html


class NumericColumn(Column):
    def __init__(self, *args, **kwargs):
        attrs = kwargs.get('attrs', {})
        if not attrs.get('td', False):
            attrs['td'] = {}
        attrs['td'].update({'align': 'right'})
        kwargs['attrs'] = attrs
        super().__init__(*args, **kwargs)

    def render(self, value):
        return format_html("%g" % value)


class NumericHideZero(NumericColumn):
    def render(self, value):
        if value == 0:
            return format_html("")
        return super().render(value)


class ProductCodeColumn(Column):
    def render(self, value):
        return format_html(
            "<a href='http://erp.core.cmass-ni.com/cgi-bin/openerp_utils/product_info.cgi?product_id=%(value)s' "
            "target='_blank'>%(value)s</a>" % {'value': value}
        )
