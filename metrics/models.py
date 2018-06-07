# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals

from django.db import models, connections
from django.db.models import Q


def suppress_zero(number):
    if number == 0 or number == '0':
        return ''
    else:
        return "%g" % number


class ProductProduct(models.Model):
    ean13 = models.CharField(max_length=13, blank=True, null=True)
    price_extra = models.DecimalField(max_digits=1000, decimal_places=10, blank=True, null=True)
    default_code = models.CharField(max_length=64, blank=True, null=True)
    name_template = models.CharField(max_length=128, blank=True, null=True)
    active = models.NullBooleanField()
    variants = models.CharField(max_length=64, blank=True, null=True)
    product_tmpl = models.ForeignKey('ProductTemplate' )
    price_margin = models.DecimalField(max_digits=1000, decimal_places=10, blank=True, null=True)
    track_production = models.NullBooleanField()
    valuation = models.CharField(max_length=16)
    track_outgoing = models.NullBooleanField()
    track_incoming = models.NullBooleanField()
    color = models.IntegerField(blank=True, null=True)
    image = models.BinaryField(blank=True, null=True)
    auto_pick = models.NullBooleanField()
    image_medium = models.BinaryField(blank=True, null=True)
    image_small = models.BinaryField(blank=True, null=True)
    hold_flag = models.NullBooleanField()
    eccn = models.CharField(max_length=10, blank=True, null=True)
    need_tech_validation = models.NullBooleanField()
    cmcomcode = models.CharField(max_length=10, blank=True, null=True)
    hold_reason = models.CharField(max_length=30, blank=True, null=True)
    pick_lead_time = models.IntegerField()
    hscomcode = models.CharField(max_length=10)
    opera_code = models.IntegerField(blank=True, null=True)

    def qty_available(self):
        qty = 0
        for child in StockMove.positive_stock_moves(self).filter(state='done'):
            qty += ProductUom.quantity_as_product_uom(
                product_uom=self.product_tmpl.uom,
                reference_uom=child.product_uom,
                qty=child.product_qty
            )
        for child in StockMove.negative_stock_moves(self).filter(state='done'):
            qty -= ProductUom.quantity_as_product_uom(
                product_uom=self.product_tmpl.uom,
                reference_uom=child.product_uom,
                qty=child.product_qty
            )

        return qty

    def virtual_quantity(self):
        qty = 0
        for child in StockMove.positive_stock_moves(self):
            qty += ProductUom.quantity_as_product_uom(
                product_uom=self.product_tmpl.uom,
                reference_uom=child.product_uom,
                qty=child.product_qty
            )
        for child in StockMove.negative_stock_moves(self):
            qty -= ProductUom.quantity_as_product_uom(
                product_uom=self.product_tmpl.uom,
                reference_uom=child.product_uom,
                qty=child.product_qty
            )

        return qty

    def incoming_quantity(self):
        qty = 0
        for child in StockMove.positive_stock_moves(self).exclude(state='done'):
            qty += ProductUom.quantity_as_product_uom(
                product_uom=self.product_tmpl.uom,
                reference_uom=child.product_uom,
                qty=child.product_qty
            )

        return qty

    def outgoing_quantity(self):
        qty = 0
        for child in StockMove.positive_stock_moves(self).exclude(state='done'):
            qty += ProductUom.quantity_as_product_uom(
                product_uom=self.product_tmpl.uom,
                reference_uom=child.product_uom,
                qty=child.product_qty
            )

        return qty

    def __str__(self):
        return self.default_code

    class Meta:
        managed = False
        db_table = 'product_product'
        ordering = ['default_code']


class ProductTemplate(models.Model):
    warranty = models.FloatField(blank=True, null=True)
    supply_method = models.CharField(max_length=16)
    list_price = models.DecimalField(max_digits=1000, decimal_places=10, blank=True, null=True)
    standard_price = models.DecimalField(max_digits=1000, decimal_places=10, blank=True, null=True)
    mes_type = models.CharField(max_length=16, blank=True, null=True)
    uom = models.ForeignKey('ProductUom' , verbose_name='UOM')
    description_purchase = models.TextField(blank=True, null=True)
    uos_coeff = models.DecimalField(max_digits=1000, decimal_places=10, blank=True, null=True)
    purchase_ok = models.NullBooleanField()
    product_manager = models.ForeignKey('ResUsers' , db_column='product_manager', blank=True, null=True)
    company = models.ForeignKey('ResCompany' , blank=True, null=True)
    name = models.CharField(max_length=128, verbose_name='Description')
    state = models.CharField(max_length=16, blank=True, null=True)
    loc_rack = models.CharField(max_length=16, blank=True, null=True)
    type = models.CharField(max_length=16)
    description = models.TextField(blank=True, null=True)
    volume = models.FloatField(blank=True, null=True)
    loc_row = models.CharField(max_length=16, blank=True, null=True)
    description_sale = models.TextField(blank=True, null=True)
    procure_method = models.CharField(max_length=16)
    cost_method = models.CharField(max_length=16)
    rental = models.NullBooleanField()
    sale_ok = models.NullBooleanField()
    sale_delay = models.FloatField(blank=True, null=True)
    loc_case = models.CharField(max_length=16, blank=True, null=True)
    produce_delay = models.FloatField(blank=True, null=True)
    categ = models.ForeignKey('ProductCategory' )
    weight = models.DecimalField(max_digits=1000, decimal_places=10, blank=True, null=True)
    weight_net = models.DecimalField(max_digits=1000, decimal_places=10, blank=True, null=True)
    moisture_sensitivity = models.CharField(max_length=1)
    feeder_type = models.CharField(max_length=16, blank=True, null=True)
    cycle_class = models.CharField(max_length=1, blank=True, null=True)
    programmable_ic = models.NullBooleanField()
    pcba_part_type = models.CharField(max_length=32, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        managed = False
        db_table = 'product_template'


class ProductCategory(models.Model):
    parent = models.ForeignKey('self', blank=True, null=True)
    name = models.CharField(max_length=64)
    sequence = models.IntegerField(blank=True, null=True)
    type = models.CharField(max_length=16, blank=True, null=True)
    parent_left = models.IntegerField(blank=True, null=True)
    parent_right = models.IntegerField(blank=True, null=True)
    opera_code = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'product_category'


class ProductUom(models.Model):
    uom_type = models.CharField(max_length=16)
    category = models.ForeignKey('ProductUomCateg')
    name = models.CharField(max_length=64)
    rounding = models.DecimalField(max_digits=1000, decimal_places=10)
    factor = models.DecimalField(max_digits=1000, decimal_places=10)
    active = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'product_uom'

    @staticmethod
    def quantity_as_product_uom(product_uom, reference_uom, qty):
        """
        :param product_uom:
        :param reference_uom:
        :param qty:
        :return:
        """
        return (qty / reference_uom.factor) * product_uom.factor

    def __str__(self):
        return self.name


class ProductUomCateg(models.Model):
    name = models.CharField(max_length=64)

    class Meta:
        managed = False
        db_table = 'product_uom_categ'

    def __str__(self):
        return self.name


class ResUsers(models.Model):
    name = models.CharField(max_length=64, blank=True, null=True)
    active = models.NullBooleanField()
    login = models.CharField(unique=True, max_length=64)
    email = models.CharField(max_length=64, blank=True, null=True)
    context_tz = models.CharField(max_length=64, blank=True, null=True)
    signature = models.TextField(blank=True, null=True)
    context_lang = models.CharField(max_length=64, blank=True, null=True)
    company = models.ForeignKey('ResCompany' )
    menu_id = models.IntegerField(blank=True, null=True)
    address = models.ForeignKey('ResPartner' , blank=True, null=True, related_name='res_users_address')
    menu_tips = models.NullBooleanField()
    date = models.DateTimeField(blank=True, null=True)
    action_id = models.IntegerField(blank=True, null=True)
    default_section = models.ForeignKey('CrmCaseSection' , blank=True, null=True)
    screen_pop = models.NullBooleanField()
    partner = models.ForeignKey('ResPartner' , related_name='res_users_partner')
    email_from = models.CharField(max_length=255, blank=True, null=True)
    login_date = models.DateField(blank=True, null=True)
    password_crypt = models.CharField(max_length=255, blank=True, null=True)
    share = models.NullBooleanField()
    password = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'res_users'

    def __str__(self):
        return self.login


class ResPartner(models.Model):
    comment = models.TextField(blank=True, null=True)
    ean13 = models.CharField(max_length=13, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    active = models.NullBooleanField()
    lang = models.CharField(max_length=5, blank=True, null=True)
    customer = models.NullBooleanField()
    credit_limit = models.FloatField(blank=True, null=True)
    user = models.ForeignKey('ResUsers' , blank=True, null=True)
    name = models.CharField(max_length=128)
    title = models.ForeignKey('ResPartnerTitle' , db_column='title', blank=True, null=True)
    company = models.ForeignKey('ResCompany' , blank=True, null=True)
    parent = models.ForeignKey('self' , blank=True, null=True)
    employee = models.NullBooleanField()
    supplier = models.NullBooleanField()
    ref = models.CharField(max_length=64, blank=True, null=True)
    vat = models.CharField(max_length=32, blank=True, null=True)
    last_reconciliation_date = models.DateTimeField(blank=True, null=True)
    debit_limit = models.FloatField(blank=True, null=True)
    section = models.ForeignKey('CrmCaseSection' , blank=True, null=True)
    vat_subjected = models.NullBooleanField()
    color = models.IntegerField(blank=True, null=True)
    opt_out = models.NullBooleanField()
    is_company = models.NullBooleanField()
    birthdate = models.CharField(max_length=64, blank=True, null=True)
    city = models.CharField(max_length=128, blank=True, null=True)
    street = models.CharField(max_length=128, blank=True, null=True)
    street2 = models.CharField(max_length=128, blank=True, null=True)
    type = models.CharField(max_length=255, blank=True, null=True)
    fax = models.CharField(max_length=64, blank=True, null=True)
    function = models.CharField(max_length=128, blank=True, null=True)
    mobile = models.CharField(max_length=64, blank=True, null=True)
    phone = models.CharField(max_length=64, blank=True, null=True)
    zip = models.CharField(max_length=24, blank=True, null=True)
    country = models.ForeignKey('ResCountry' , blank=True, null=True)
    state = models.ForeignKey('ResCountryState' , blank=True, null=True)
    tz = models.CharField(max_length=64, blank=True, null=True)
    email = models.CharField(max_length=240, blank=True, null=True)
    image = models.BinaryField(blank=True, null=True)
    image_small = models.BinaryField(blank=True, null=True)
    image_medium = models.BinaryField(blank=True, null=True)
    use_parent_address = models.NullBooleanField()
    website = models.CharField(max_length=64, blank=True, null=True)
    notification_email_send = models.CharField(max_length=255)
    signup_type = models.CharField(max_length=255, blank=True, null=True)
    signup_expiration = models.DateTimeField(blank=True, null=True)
    signup_token = models.CharField(max_length=255, blank=True, null=True)
    display_name = models.CharField(max_length=255, blank=True, null=True)
    customer_account_no = models.CharField(max_length=16, blank=True, null=True)
    export_license = models.CharField(max_length=64, blank=True, null=True)
    attn_to = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        managed = False
        db_table = 'res_partner'


class ResPartnerTitle(models.Model):
    domain = models.CharField(max_length=24)
    name = models.CharField(max_length=46)
    shortcut = models.CharField(max_length=16, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'res_partner_title'


class ResCurrency(models.Model):
    name = models.CharField(max_length=32)
    rounding = models.DecimalField(max_digits=1000, decimal_places=10, blank=True, null=True)
    company = models.ForeignKey('ResCompany' , blank=True, null=True)
    active = models.NullBooleanField()
    base = models.NullBooleanField()
    date = models.DateField(blank=True, null=True)
    accuracy = models.IntegerField(blank=True, null=True)
    position = models.CharField(max_length=255, blank=True, null=True)
    symbol = models.CharField(max_length=4, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'res_currency'


class ResCountry(models.Model):
    code = models.CharField(unique=True, max_length=2, blank=True, null=True)
    name = models.CharField(unique=True, max_length=64)
    address_format = models.TextField(blank=True, null=True)
    currency = models.ForeignKey('ResCurrency' , blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'res_country'


class ResCountryState(models.Model):
    code = models.CharField(max_length=3)
    country = models.ForeignKey('ResCountry' )
    name = models.CharField(max_length=64)

    class Meta:
        managed = False
        db_table = 'res_country_state'


class CrmCaseSection(models.Model):
    working_hours = models.DecimalField(max_digits=1000, decimal_places=10, blank=True, null=True)
    name = models.CharField(max_length=64)
    user = models.ForeignKey('ResUsers' , blank=True, null=True)
    change_responsible = models.NullBooleanField()
    note = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self' , blank=True, null=True)
    code = models.CharField(unique=True, max_length=8, blank=True, null=True)
    complete_name = models.CharField(max_length=256, blank=True, null=True)
    reply_to = models.CharField(max_length=64, blank=True, null=True)
    active = models.NullBooleanField()
    allow_unlink = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'crm_case_section'


class AccountAccount(models.Model):
    parent_left = models.IntegerField(blank=True, null=True)
    parent_right = models.IntegerField(blank=True, null=True)
    code = models.CharField(max_length=64)
    reconcile = models.NullBooleanField()
    currency = models.ForeignKey('ResCurrency' , blank=True, null=True)
    user_type = models.ForeignKey('AccountAccountType' , db_column='user_type')
    active = models.NullBooleanField()
    level = models.IntegerField(blank=True, null=True)
    company = models.ForeignKey('ResCompany' )
    shortcut = models.CharField(max_length=12, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self' , blank=True, null=True)
    currency_mode = models.CharField(max_length=16)
    type = models.CharField(max_length=16)
    name = models.CharField(max_length=256)

    class Meta:
        managed = False
        db_table = 'account_account'
        unique_together = (('code', 'company'),)


class AccountAccountType(models.Model):
    note = models.TextField(blank=True, null=True)
    close_method = models.CharField(max_length=16)
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=64)
    sign = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'account_account_type'


class ResCompany(models.Model):
    parent = models.ForeignKey('self' , blank=True, null=True)
    rml_footer1 = models.CharField(max_length=200, blank=True, null=True)
    rml_header = models.TextField()
    currency = models.ForeignKey('ResCurrency' )
    rml_header3 = models.TextField()
    partner = models.ForeignKey('ResPartner' )
    account_no = models.CharField(max_length=64, blank=True, null=True)
    overdue_msg = models.TextField(blank=True, null=True)
    schedule_range = models.FloatField()
    security_lead = models.FloatField()
    project_time_mode = models.ForeignKey('ProductUom' , blank=True, null=True)
    income_currency_exchange_account = models.ForeignKey('AccountAccount' , blank=True, null=True, related_name='res_company_income_currency_exchange_account')
    expense_currency_exchange_account = models.ForeignKey('AccountAccount' , blank=True, null=True, related_name='res_company_expense_currency_exchange_account')
    paper_format = models.CharField(max_length=255)
    company_registry = models.CharField(max_length=64, blank=True, null=True)
    name = models.CharField(unique=True, max_length=128)
    paypal_account = models.CharField(max_length=128, blank=True, null=True)
    vat_check_vies = models.NullBooleanField()
    po_lead = models.FloatField()
    manufacturing_lead = models.FloatField()
    old_partner_id = models.IntegerField(blank=True, null=True)
    rml_footer = models.TextField(blank=True, null=True)
    logo_web = models.BinaryField(blank=True, null=True)
    custom_footer = models.NullBooleanField()
    expects_chart_of_accounts = models.NullBooleanField()
    tax_calculation_rounding_method = models.CharField(max_length=255, blank=True, null=True)
    rml_header2 = models.TextField()
    rml_header1 = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'res_company'


class PurchaseOrder(models.Model):
    origin = models.CharField(max_length=64, blank=True, null=True)
    date_order = models.DateField()
    partner = models.ForeignKey('ResPartner' , related_name='purchase_order_partner')
    dest_address = models.ForeignKey('ResPartner' , blank=True, null=True, related_name='purchase_order_dest_address')
    amount_untaxed = models.DecimalField(max_digits=1000, decimal_places=10, blank=True, null=True)
    location = models.ForeignKey('StockLocation' )
    company = models.ForeignKey('ResCompany' )
    amount_tax = models.DecimalField(max_digits=1000, decimal_places=10, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    pricelist = models.ForeignKey('ProductPricelist' )
    warehouse = models.ForeignKey('StockWarehouse' , blank=True, null=True)
    partner_ref = models.CharField(max_length=64, blank=True, null=True)
    date_approve = models.DateField(blank=True, null=True)
    amount_total = models.DecimalField(max_digits=1000, decimal_places=10, blank=True, null=True)
    name = models.CharField(max_length=64)
    notes = models.TextField(blank=True, null=True)
    invoice_method = models.CharField(max_length=255)
    shipped = models.NullBooleanField()
    validator = models.ForeignKey('ResUsers' , db_column='validator', blank=True, null=True)
    minimum_planned_date = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'purchase_order'
        unique_together = (('name', 'company'),)


class PurchaseOrderLine(models.Model):
    product_uom = models.ForeignKey('ProductUom' , db_column='product_uom')
    order = models.ForeignKey('PurchaseOrder' )
    price_unit = models.DecimalField(max_digits=1000, decimal_places=10)
    move_dest = models.ForeignKey('StockMove' , blank=True, null=True)
    product_qty = models.DecimalField(max_digits=1000, decimal_places=10)
    partner = models.ForeignKey('ResPartner' , blank=True, null=True)
    invoiced = models.NullBooleanField()
    name = models.TextField()
    date_planned = models.DateField()
    company = models.ForeignKey('ResCompany' , blank=True, null=True)
    state = models.CharField(max_length=255)
    product = models.ForeignKey('ProductProduct' , blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'purchase_order_line'


class SaleOrder(models.Model):
    origin = models.CharField(max_length=64, blank=True, null=True)
    order_policy = models.CharField(max_length=255)
    client_order_ref = models.CharField(max_length=64, blank=True, null=True)
    date_order = models.DateField()
    partner = models.ForeignKey('ResPartner' , related_name='sale_order_partner')
    note = models.TextField(blank=True, null=True)
    user = models.ForeignKey('ResUsers' , blank=True, null=True)
    company = models.ForeignKey('ResCompany' , blank=True, null=True)
    amount_tax = models.DecimalField(max_digits=1000, decimal_places=10, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    pricelist = models.ForeignKey('ProductPricelist' )
    partner_invoice = models.ForeignKey('ResPartner' , related_name='sale_order_partner_invoice')
    amount_untaxed = models.DecimalField(max_digits=1000, decimal_places=10, blank=True, null=True)
    date_confirm = models.DateField(blank=True, null=True)
    amount_total = models.DecimalField(max_digits=1000, decimal_places=10, blank=True, null=True)
    name = models.CharField(max_length=64)
    partner_shipping = models.ForeignKey('ResPartner' , related_name='sale_order_partner_shipping')
    invoice_quantity = models.CharField(max_length=255)
    section = models.ForeignKey('CrmCaseSection' , blank=True, null=True)
    picking_policy = models.CharField(max_length=255)
    incoterm = models.ForeignKey('StockIncoterms' , db_column='incoterm', blank=True, null=True)
    shipped = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'sale_order'
        unique_together = (('name', 'company'),)


class SaleOrderLine(models.Model):
    product_uos_qty = models.DecimalField(max_digits=1000, decimal_places=10, blank=True, null=True)
    product_uom = models.ForeignKey('ProductUom' , db_column='product_uom', related_name='sale_order_line_product_uom')
    sequence = models.IntegerField(blank=True, null=True)
    order = models.ForeignKey('SaleOrder' )
    price_unit = models.DecimalField(max_digits=1000, decimal_places=10)
    product_uom_qty = models.DecimalField(max_digits=1000, decimal_places=10)
    discount = models.DecimalField(max_digits=1000, decimal_places=10, blank=True, null=True)
    product_uos = models.ForeignKey('ProductUom' , db_column='product_uos', blank=True, null=True, related_name='sale_order_line_product_uos')
    name = models.TextField()
    company = models.ForeignKey('ResCompany' , blank=True, null=True)
    salesman = models.ForeignKey('ResUsers' , blank=True, null=True)
    state = models.CharField(max_length=255)
    product = models.ForeignKey('ProductProduct' , blank=True, null=True)
    order_partner = models.ForeignKey('ResPartner' , blank=True, null=True, related_name='sale_order_line_order_partner')
    th_weight = models.FloatField(blank=True, null=True)
    invoiced = models.NullBooleanField()
    type = models.CharField(max_length=255)
    address_allotment = models.ForeignKey('ResPartner' , blank=True, null=True, related_name='sale_order_line_address_allotment')
    procurement = models.ForeignKey('ProcurementOrder' , blank=True, null=True)
    delay = models.FloatField()

    class Meta:
        managed = False
        db_table = 'sale_order_line'


class ProcurementOrder(models.Model):
    origin = models.CharField(max_length=64, blank=True, null=True)
    product_uom = models.ForeignKey('ProductUom' , db_column='product_uom', related_name='procurement_order_product_uom')
    product_uos_qty = models.FloatField(blank=True, null=True)
    procure_method = models.CharField(max_length=255)
    product_qty = models.DecimalField(max_digits=1000, decimal_places=10)
    product_uos = models.ForeignKey('ProductUom' , db_column='product_uos', blank=True, null=True, related_name='procurement_order_product_uos')
    message = models.CharField(max_length=124, blank=True, null=True)
    location = models.ForeignKey('StockLocation' )
    move = models.ForeignKey('StockMove' , blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    name = models.TextField()
    date_planned = models.DateTimeField()
    close_move = models.NullBooleanField()
    company = models.ForeignKey('ResCompany' )
    date_close = models.DateTimeField(blank=True, null=True)
    priority = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    product = models.ForeignKey('ProductProduct' )
    purchase = models.ForeignKey('PurchaseOrder' , blank=True, null=True)
    production = models.ForeignKey('MrpProduction' , blank=True, null=True)
    bom = models.ForeignKey('MrpBom' , blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'procurement_order'


class ProductPricelist(models.Model):
    currency = models.ForeignKey('ResCurrency' )
    name = models.CharField(max_length=64)
    active = models.NullBooleanField()
    type = models.CharField(max_length=255)
    company = models.ForeignKey('ResCompany' , blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'product_pricelist'


class MrpProduction(models.Model):
    origin = models.CharField(max_length=64, blank=True, null=True)
    product_uom = models.ForeignKey('ProductUom' , db_column='product_uom', related_name='mrp_production_product_uom')
    product_uos_qty = models.FloatField(blank=True, null=True)
    product_qty = models.DecimalField(max_digits=1000, decimal_places=10)
    product_uos = models.ForeignKey('ProductUom' , db_column='product_uos', blank=True, null=True, related_name='mrp_production_product_uos')
    user = models.ForeignKey('ResUsers' , blank=True, null=True)
    location_src = models.ForeignKey('StockLocation' , related_name='mrp_production_location_src')
    cycle_total = models.DecimalField(max_digits=1000, decimal_places=10, blank=True, null=True)
    date_start = models.DateTimeField(blank=True, null=True)
    company = models.ForeignKey('ResCompany' )
    priority = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    bom = models.ForeignKey('MrpBom' , blank=True, null=True)
    date_finished = models.DateTimeField(blank=True, null=True)
    name = models.CharField(max_length=64)
    product = models.ForeignKey('ProductProduct' )
    date_planned = models.DateTimeField()
    move_prod = models.ForeignKey('StockMove' , blank=True, null=True)
    routing = models.ForeignKey('MrpRouting' , blank=True, null=True)
    hour_total = models.DecimalField(max_digits=1000, decimal_places=10, blank=True, null=True)
    location_dest = models.ForeignKey('StockLocation' , related_name='mrp_production_location_dest')
    picking = models.ForeignKey('StockPicking' , blank=True, null=True)

    def __str__(self):
        return "%(name)s - %(product)s - %(product_qty)g" % {
            'name': self.name, 'product': self.product, 'product_qty': self.product_qty
        }

    class Meta:
        managed = False
        db_table = 'mrp_production'
        unique_together = (('name', 'company'),)


class MrpBom(models.Model):
    date_stop = models.DateField(blank=True, null=True)
    code = models.CharField(max_length=16, blank=True, null=True)
    product_uom = models.ForeignKey('ProductUom' , db_column='product_uom', related_name='bom_product_uom')
    product_uos_qty = models.FloatField(blank=True, null=True)
    date_start = models.DateField(blank=True, null=True)
    product_qty = models.DecimalField(max_digits=1000, decimal_places=10)
    product_uos = models.ForeignKey('ProductUom' , db_column='product_uos', blank=True, null=True, related_name='bom_product_uos')
    product_efficiency = models.FloatField()
    active = models.NullBooleanField()
    product_rounding = models.FloatField(blank=True, null=True)
    name = models.CharField(max_length=64, blank=True, null=True)
    sequence = models.IntegerField(blank=True, null=True)
    company = models.ForeignKey('ResCompany' )
    routing = models.ForeignKey('MrpRouting' , blank=True, null=True)
    product = models.ForeignKey('ProductProduct' )
    bom = models.ForeignKey('self' , blank=True, null=True)
    position = models.CharField(max_length=64, blank=True, null=True)
    type = models.CharField(max_length=255)

    @staticmethod
    def get_all_bom_product_ids(parent_id):
        cursor = connections['erp'].cursor()

        def get_child_product_ids(parent_ids):
            cursor.execute("""
            SELECT product_id FROM mrp_bom WHERE bom_id IN (
                SELECT id FROM mrp_bom WHERE bom_id IS NULL AND product_id = ANY(%(parent_ids)s)
            )
            """, {'parent_ids': parent_ids})
            return [x[0] for x in cursor.fetchall()]

        product_ids = []

        children = get_child_product_ids([parent_id])
        while children:
            product_ids += children
            children = get_child_product_ids(children)
        return product_ids

    class Meta:
        managed = False
        db_table = 'mrp_bom'


class MrpRouting(models.Model):
    note = models.TextField(blank=True, null=True)
    code = models.CharField(max_length=8, blank=True, null=True)
    name = models.CharField(max_length=64)
    active = models.NullBooleanField()
    location = models.ForeignKey('StockLocation' , blank=True, null=True)
    company = models.ForeignKey('ResCompany' , blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'mrp_routing'


class StockPicking(models.Model):
    origin = models.CharField(max_length=64, blank=True, null=True)
    date_done = models.DateTimeField(blank=True, null=True)
    min_date = models.DateTimeField(blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    partner = models.ForeignKey('ResPartner' , blank=True, null=True)
    backorder = models.ForeignKey('self' , blank=True, null=True)
    name = models.CharField(max_length=64, blank=True, null=True)
    location = models.ForeignKey('StockLocation' , blank=True, null=True, related_name='stock_picking_location')
    move_type = models.CharField(max_length=255)
    company = models.ForeignKey('ResCompany' )
    invoice_state = models.CharField(max_length=255)
    note = models.TextField(blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    location_dest = models.ForeignKey('StockLocation' , blank=True, null=True, related_name='stock_picking_location_dest')
    max_date = models.DateTimeField(blank=True, null=True)
    auto_picking = models.NullBooleanField()
    type = models.CharField(max_length=255)
    purchase = models.ForeignKey('PurchaseOrder' , blank=True, null=True)
    sale = models.ForeignKey('SaleOrder' , blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'stock_picking'
        unique_together = (('name', 'company'),)


class StockMove(models.Model):
    origin = models.CharField(max_length=64, blank=True, null=True)
    product_uos_qty = models.DecimalField(max_digits=1000, decimal_places=10, blank=True, null=True)
    date_expected = models.DateTimeField()
    product_uom = models.ForeignKey('ProductUom' , db_column='product_uom', related_name='stock_move_product_uom')
    price_unit = models.DecimalField(max_digits=1000, decimal_places=10, blank=True, null=True)
    date = models.DateTimeField()
    move_dest = models.ForeignKey('self' , blank=True, null=True)
    product_qty = models.DecimalField(max_digits=1000, decimal_places=10)
    product_uos = models.ForeignKey('ProductUom' , db_column='product_uos', blank=True, null=True, related_name='stock_move_product_uos')
    partner = models.ForeignKey('ResPartner' , blank=True, null=True)
    name = models.CharField(max_length=255)
    note = models.TextField(blank=True, null=True)
    product = models.ForeignKey('ProductProduct' )
    auto_validate = models.NullBooleanField()
    price_currency = models.ForeignKey('ResCurrency' , blank=True, null=True)
    location = models.ForeignKey('StockLocation' , related_name='stock_move_location')
    company = models.ForeignKey('ResCompany' )
    picking = models.ForeignKey('StockPicking' , blank=True, null=True)
    priority = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    location_dest = models.ForeignKey('StockLocation' , related_name='stock_move_location_dest')
    purchase_line = models.ForeignKey('PurchaseOrderLine' , blank=True, null=True)
    sale_line = models.ForeignKey('SaleOrderLine' , blank=True, null=True)
    production = models.ForeignKey('MrpProduction' , blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'stock_move'

    @staticmethod
    def positive_stock_moves(product_product):
        stockable_locations = StockLocation.stockable_locations()
        return StockMove.objects.filter(product=product_product).exclude(location__in=stockable_locations).filter(location_dest__in=stockable_locations).exclude(state='cancel')


    @staticmethod
    def negative_stock_moves(product_product):
        stockable_locations = StockLocation.stockable_locations()
        return StockMove.objects.filter(product=product_product).filter(location__in=stockable_locations).exclude(location_dest__in=stockable_locations).exclude(state='cancel')


class StockLocation(models.Model):
    parent_left = models.IntegerField(blank=True, null=True)
    parent_right = models.IntegerField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    chained_delay = models.IntegerField(blank=True, null=True)
    chained_company = models.ForeignKey('ResCompany' , blank=True, null=True, related_name='stock_location_chained_company')
    active = models.NullBooleanField()
    posz = models.IntegerField(blank=True, null=True)
    posx = models.IntegerField(blank=True, null=True)
    posy = models.IntegerField(blank=True, null=True)
    valuation_in_account = models.ForeignKey('AccountAccount' , blank=True, null=True, related_name='stock_location_valuation_in_account')
    partner = models.ForeignKey('ResPartner' , blank=True, null=True)
    icon = models.CharField(max_length=64, blank=True, null=True)
    valuation_out_account = models.ForeignKey('AccountAccount' , blank=True, null=True, related_name='stock_location_valuation_out_account')
    scrap_location = models.NullBooleanField()
    name = models.CharField(max_length=64)
    chained_location = models.ForeignKey('self' , blank=True, null=True, related_name='stock_location_chained_location')
    chained_picking_type = models.CharField(max_length=255, blank=True, null=True)
    company = models.ForeignKey('ResCompany' , blank=True, null=True, related_name='stock_location_company')
    chained_auto_packing = models.CharField(max_length=255)
    complete_name = models.CharField(max_length=256, blank=True, null=True)
    usage = models.CharField(max_length=255)
    location = models.ForeignKey('self' , blank=True, null=True, related_name='stock_location_location')
    chained_location_type = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    @staticmethod
    def stockable_locations():
        return StockLocation.objects.filter(id__in=StockLocation.stockable_location_ids())

    @staticmethod
    def stockable_location_ids():
        cursor = connections['erp'].cursor()
        try:
            stock = StockLocation.objects.get(name="Stock")
        except:
            return
        cursor.execute("""
        SELECT id FROM stock_location 
        WHERE (parent_left BETWEEN %(parent_left)s AND %(parent_right)s) 
        OR id = %(parent_id)s
        OR name = 'MMRB'
        """, {'parent_left': stock.parent_left, 'parent_right': stock.parent_right, 'parent_id': stock.id})
        ids = [record[0] for record in cursor.fetchall()]
        return ids

    @staticmethod
    def api_count_locations():
        stock = StockLocation.objects.get(name="Stock")
        locations = StockLocation.objects.filter(
            Q(parent_left__range=(stock.parent_left, stock.parent_right)) |
            Q(name="MMRB")
        ).order_by('name')
        unused_locations = locations.exclude(id__in=StockMove.objects.values('location').distinct())
        unused_locations = unused_locations.exclude(id__in=StockMove.objects.values('location_dest').distinct())
        locations = locations.exclude(id__in=[location.id for location in unused_locations])
        return locations

    @staticmethod
    def test_count_locations():
        return StockLocation.objects.filter(name__istartswith="MP")

    class Meta:
        managed = False
        db_table = 'stock_location'


class StockWarehouse(models.Model):
    lot_input = models.ForeignKey('StockLocation' , related_name='stock_warehouse_lot_input')
    lot_output = models.ForeignKey('StockLocation' , related_name='stock_warehouse_lot_output')
    name = models.CharField(max_length=128)
    lot_stock = models.ForeignKey('StockLocation' , related_name='stock_warehouse_lot_stock')
    partner = models.ForeignKey('ResPartner' , blank=True, null=True)
    company = models.ForeignKey('ResCompany' )

    class Meta:
        managed = False
        db_table = 'stock_warehouse'


class StockIncoterms(models.Model):
    active = models.NullBooleanField()
    code = models.CharField(max_length=3)
    name = models.CharField(max_length=64)

    class Meta:
        managed = False
        db_table = 'stock_incoterms'


class ProductSupplierinfo(models.Model):
    name = models.ForeignKey('ResPartner', models.DO_NOTHING, db_column='name')
    sequence = models.IntegerField(blank=True, null=True)
    company = models.ForeignKey('ResCompany', models.DO_NOTHING, blank=True, null=True)
    qty = models.DecimalField(max_digits=1000, decimal_places=6, blank=True, null=True)
    delay = models.IntegerField(null=True, blank=True)
    min_qty = models.FloatField(null=True, blank=True)
    product_code = models.CharField(max_length=64, blank=True, null=True)
    product_name = models.CharField(max_length=128, blank=True, null=True)
    product = models.ForeignKey(ProductProduct)
    manufacturer_name = models.CharField(max_length=64, blank=True, null=True)
    manufacturer_part_no = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'product_supplierinfo'
