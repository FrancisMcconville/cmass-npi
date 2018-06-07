from django import template
from npi.models import SupplierProductQuote

register = template.Library()


@register.filter(name='cheapest_supplier_quote')
def cheapest_supplier_quote(component, quotation_quantity):
    return component.cheapest_supplier_quote(quotation_quantity)


@register.filter(name='component_supplier_quote')
def component_supplier_quote(component_supplier, quotation_quantity):
    component, supplier_id = component_supplier
    return SupplierProductQuote.objects.filter(
        quote_quantity=quotation_quantity, 
        product__project_supplier_id=supplier_id,
        product__component=component
    ).first()


@register.filter(name='cheapest_supplier_quote_moq')
def cheapest_supplier_quote_moq(component, quotation_quantity):
    return component.cheapest_supplier_quote_moq(quotation_quantity)


@register.filter(name='selected_supplier_quote')
def selected_supplier_quote(component, quotation_quantity):
    return component.selected_quote(quotation_quantity)


@register.filter(name='edit_selected_quote')
def edit_selected_quote(component, quotation_quantity):
    return component.edit_selected_quote(quotation_quantity)


@register.filter(name='supplier_component_state')
def supplier_component_state(supplier_component):
    return supplier_component.STATES[supplier_component.state]
