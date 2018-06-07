from .models import Project, Parent, Component, ParentComponent, Designator
from .models import ProjectSupplier, SupplierComponent, SupplierProductQuote, QuoteQuantity
from .models import BomParent, BomChildParent, BomComponent
from .utils import NPI_PROJECT_MAX_QUOTATION_QUANTITY, ExcelUtils
from cmass_django_generics.forms import FormInlineModelFormset
from metrics.models import ResPartner, ProductUom, ProductProduct, MrpRouting
from metrics.utils import OpenerpXmlrpc
from dal import autocomplete
from django.db import transaction
from django.forms import *
from django.shortcuts import reverse
import re
import xlrd


class SpreadsheetParser(object):
    sheet_details = {}
    parsed_data = {}
    cleaned_spreadsheet_data = {}

    def __init__(self, *args, **kwargs):
        self.sheet_details = self.get_sheet_details()
        self.spreadsheet_validation_errors = {}
        super().__init__(*args, **kwargs)

    def get_sheet_details(self):
        return self.sheet_details

    def open_workbook(self, spreadsheet_file):
        try:
            spreadsheet_file.seek(0)
            return xlrd.open_workbook(file_contents=spreadsheet_file.read())
        except xlrd.XLRDError as e:
            raise ValidationError(e)

    def open_sheets(self, spreadsheet):
        sheets = {}
        for sheet_name in self.sheet_details:
            if sheet_name not in spreadsheet.sheet_names():
                raise ValidationError("%s Sheet missing'" % sheet_name)
            sheets[sheet_name] = {'sheet': spreadsheet.sheet_by_name(sheet_name)}
        return sheets

    def get_sheet_header_columns(self, sheets):
        """
        Adds headers key to sheets
        headers is a dictionary of {'column_name': column_index}

        May raise Validation Error of headers
         defined in self.sheet_details[sheet_name]['headers'] are not found on the sheet

        :param sheets: dictionary of {'sheet_name': {'sheet': xlrd.Sheet}}
        :return: updated sheets dictionary with headers key
        """
        for sheet_name in sheets:
            sheet = sheets[sheet_name]['sheet']
            headers = {header.lower(): None for header in self.sheet_details[sheet_name]['headers']}

            for index, column in enumerate(sheet.row(self.sheet_details[sheet_name]['header_row'])):
                column = column.value.strip().lower()
                if column in headers:
                    headers[column] = index
            missing_headers = {k: v for k, v in headers.items() if v is None}
            if missing_headers:
                raise ValidationError("%(sheet)s headers invalid: %(headers)s missing" % {
                    'sheet': sheet_name, 'headers': list(missing_headers.keys())
                })
            sheets[sheet_name]['headers'] = headers
        return sheets

    def get_sheet_data(self, sheets):
        """
        :param sheets: dictionary of {'sheet_name': {'sheet': xlrd.Sheet, 'headers': {'column_name': column_index}} }
        """
        data = {}
        for sheet_name in sheets:
            data[sheet_name] = []
            sheet = sheets[sheet_name]['sheet']
            headers = sheets[sheet_name]['headers']

            for row in range(self.sheet_details[sheet_name]['header_row']+1, sheet.nrows):
                row_data = {}
                for header, col in headers.items():
                    row_data[header] = ExcelUtils.cell_string_value(sheet, row, col)
                data[sheet_name].append(row_data)
        return data

    def load_workbook(self, spreadsheet_file):
        spreadsheet = self.open_workbook(spreadsheet_file)
        sheets = self.open_sheets(spreadsheet)
        sheets = self.get_sheet_header_columns(sheets)
        self.parsed_data = self.get_sheet_data(sheets)

    def raise_spreadsheet_validation_error(self, error_title=None, line_number_increment=0):
        if self.spreadsheet_validation_errors:
            errors = []
            if error_title:
                errors.append(ValidationError("%s" % error_title))

            for line_number in sorted(self.spreadsheet_validation_errors.keys()):
                error = "Line %s: " % (line_number + line_number_increment)
                for text in self.spreadsheet_validation_errors[line_number]:
                    error += "%s, " % text
                errors.append(ValidationError(error[:-2]))

            raise ValidationError(errors)

    def add_spreadsheet_validation_error(self, validation_line_number, validation_error):
        validation_errors = self.spreadsheet_validation_errors.get(validation_line_number, [])
        validation_errors.append(validation_error)
        self.spreadsheet_validation_errors[validation_line_number] = validation_errors

    def validate_column_required(self, data, column, error_message):
        for line_number, component in enumerate(data):
            if not component.get(column):
                self.add_spreadsheet_validation_error(line_number, error_message)

    def validate_column_required_unique(self, data, column, verbose_column_name):
        existing_values = set()
        for line_number, row in enumerate(data):
            value = row.get(column)
            if not value:
                self.add_spreadsheet_validation_error(line_number, "%s is required" % verbose_column_name)
            elif value in existing_values:
                self.add_spreadsheet_validation_error(line_number, "%s is a duplicated value" % verbose_column_name)
            else:
                existing_values.add(value)

    def validate_uom(self, data, column):
        uoms = [component[column] for component in data]
        system_uom_mapping = {x.name: x.id for x in ProductUom.objects.filter(name__in=uoms)}

        for line_number, row in enumerate(data):
            uom = row[column]
            if not uom:
                self.add_spreadsheet_validation_error(line_number, 'UOM is required')
            else:
                if uom not in system_uom_mapping:
                    self.add_spreadsheet_validation_error(line_number, "UOM '%s' Doesn't exist on OpenERP" % uom)
                else:
                    row['%s_uom_id' % column] = system_uom_mapping[uom]

    def validate_quantity(self, data, column):
        for line_number, row in enumerate(data):
            quantity = row[column]
            if not quantity:
                self.add_spreadsheet_validation_error(line_number, "Quantity is required")
            else:
                try:
                    float(quantity)
                except ValueError:
                    self.add_spreadsheet_validation_error(line_number, "Quantity '%s' is not a number" % quantity)

    def validate_routing(self, data, column):
        routings = {x.code: x.id for x in MrpRouting.objects.filter(code__in=[x[column] for x in data])}
        for line_number, row in enumerate(data):
            routing = row.get(column)
            row['%s_id' % column] = routings.get(routing, None)
            if not routing:
                self.add_spreadsheet_validation_error(line_number, "Routing is required")
            elif routing not in routings:
                self.add_spreadsheet_validation_error(line_number, "Routing '%s' was not found on OpenERP" % routing)


class ProjectForm(Form):
    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        if self.project:
            kwargs['initial'].update({
                'customer': ResPartner.objects.filter(id=self.project.customer_id).first(),
                'web_pricing': 'yes' if self.project.web_pricing else 'no',
                'description': self.project.description
            })
        super().__init__(*args, **kwargs)

    customer = ModelChoiceField(
        queryset=ResPartner.objects.filter(customer=True, active=True, parent__isnull=True),
        label='Customer',
        help_text='Customer the project is for. '
                  'Customer may need to be created on OpenERP if they do not appear in the drop down',
        widget=autocomplete.Select2(url='npi:autocompleteCustomer', attrs={'class': 'form-control'})
    )
    web_pricing = CharField(
        label='Web Pricing',
        help_text='When checked, purchasing will price this BoM using web pricing',
        widget=Select(choices=[(None, '----'), ('yes', 'Yes'), ('no', 'No')], attrs={'class': 'form-control'})
    )
    description = CharField(
        label='Description', help_text='Short text describing the project being quoted', required=False,
        widget=TextInput(attrs={'class': 'form-control'})
    )

    def clean_web_pricing(self):
        if self.cleaned_data['web_pricing'] == 'yes':
            return True
        return False

    def save(self):
        project = self.project or Project()
        project.customer_id = self.cleaned_data['customer'].id
        project.customer_name = self.cleaned_data['customer'].name
        project.web_pricing = self.cleaned_data['web_pricing']
        project.description = self.cleaned_data['description']
        project.save()
        return project


class ProjectBomForm(SpreadsheetParser, Form):
    WORKBOOK_PARENT_SHEET = 'Parents'
    WORKBOOK_COMPONENTS_SHEET = 'Components'
    sheet_details = {
        WORKBOOK_PARENT_SHEET: {'header_row': 2, 'quantity_cell': {'col': 1, 'row': 0}, 'headers': [
            'parent', 'description', 'uom', 'product quantity', 'procure method', 'hscomcode', 'eccn', 'routing'],
                                },
        WORKBOOK_COMPONENTS_SHEET: {'header_row': 0, 'headers': [
            'parent', 'designators', 'manufacturer', 'mpn', 'description', 'qty', 'uom', 'msl']
                                    }
    }
    HSCOMCODE_PATTERN = re.compile('^\d{10}$')
    MSL_VALUES = ['1', '2', '3', '4', '5', '6']
    spreadsheet = FileField(label='Customer Data Spreadsheet')

    def get_sheet_data(self, sheets):
        data = super().get_sheet_data(sheets)
        parent_sheet = sheets[self.WORKBOOK_PARENT_SHEET]['sheet']
        cell = self.sheet_details[self.WORKBOOK_PARENT_SHEET]['quantity_cell']
        data['quotation_quantities'] = ExcelUtils.cell_string_value(parent_sheet, **cell)
        return data

    def clean_spreadsheet(self):
        self.load_workbook(self.cleaned_data['spreadsheet'])
        self.clean_workbook_parents()
        self.clean_workbook_components()
        return self.cleaned_data['spreadsheet']

    def clean_workbook_parents(self):
        self.validate_quotation_quantities()
        data = self.parsed_data[self.WORKBOOK_PARENT_SHEET]
        self.validate_column_required(data, 'parent', 'Parent is required')
        self.validate_column_required(data, 'description', 'Description is required')
        self.validate_uom(self.parsed_data[self.WORKBOOK_PARENT_SHEET], 'uom')
        self.validate_quantity(data, 'product quantity')
        self.validate_parent_procure_method()
        self.validate_hscomcode()
        self.validate_eccn()
        self.validate_routing(data, 'routing')
        self.raise_spreadsheet_validation_error(
            "%s Sheet" % self.WORKBOOK_PARENT_SHEET,
            self.sheet_details[self.WORKBOOK_PARENT_SHEET]['header_row'] + 1
        )

        result = {}
        for parent in self.parsed_data[self.WORKBOOK_PARENT_SHEET]:
            result[parent['parent']] = {
                'name': parent['parent'],
                'description': parent['description'],
                'quantity': parent['product quantity'],
                'procure_method': parent['procure method'],
                'uom_id': parent['uom_uom_id'],
                'uom_name': parent['uom'],
                'hscomcode': parent['hscomcode'],
                'eccn': parent['eccn'],
                'routing_name': parent['routing'],
                'routing_id': parent['routing_id'],
                'children': []
            }
        self.cleaned_spreadsheet_data = result

    def clean_workbook_components(self):
        components_data = self.parsed_data[self.WORKBOOK_COMPONENTS_SHEET]
        self.validate_components_parent()
        self.validate_components_designators()
        self.validate_column_required(components_data, 'manufacturer', 'Manufacturer is required')
        self.validate_column_required(components_data, 'mpn', 'MPN is required')
        self.validate_column_required(components_data, 'description', 'Description is required')
        self.validate_quantity(components_data, 'qty')
        self.validate_uom(components_data, 'uom')
        self.validate_components_msl()
        self.raise_spreadsheet_validation_error(
            "%s Sheet" % self.WORKBOOK_COMPONENTS_SHEET,
            self.sheet_details[self.WORKBOOK_COMPONENTS_SHEET]['header_row'] + 1
        )

        for component in components_data:
            self.cleaned_spreadsheet_data[component['parent']]['children'].append({
                'mpn': component['mpn'],
                'manufacturer': component['manufacturer'],
                'uom_id': component['uom_uom_id'],
                'uom_name': component['uom'],
                'description': component['description'],
                'msl': component['msl'] or None,
                'designators': component['designators'],
                'qty': component['qty']
            })

        self.validate_all_parents_have_children()

    def validate_quotation_quantities(self):
        """Ensure self.parsed_data['quotation_quantities'] is numeric"""
        quantities = self.parsed_data['quotation_quantities']
        if not quantities:
            self.add_spreadsheet_validation_error(1, 'Quotation Quantities not provided')
            return

        result_quantities = []
        try:
            result_quantities = [int(quantities)]
        except ValueError:
            quantities_string = [x.strip() for x in quantities.split(',')]

            if len(quantities_string) > NPI_PROJECT_MAX_QUOTATION_QUANTITY:
                self.add_spreadsheet_validation_error(
                    1, "Too many Quotation Quantities, %(qty)s submitted while maximum is %(max)s" % {
                        'qty': len(quantities_string), 'max': NPI_PROJECT_MAX_QUOTATION_QUANTITY
                    }
                )
            for quantity in quantities_string:
                try:
                    result_quantities.append(int(quantity))
                except ValueError:
                    self.add_spreadsheet_validation_error(
                        1, "Quotation Quantities '%(quantities)s contains non-numeric value '%(value)s'" % {
                            'value': quantity, 'quantities': quantities
                        }
                    )
                    return

        self.spreadsheet_quotation_quantities = result_quantities

    def validate_parent_procure_method(self):
        """may be [None, 'make_to_order', 'make_to_stock']"""
        for line_number, row in enumerate(self.parsed_data[self.WORKBOOK_PARENT_SHEET]):
            procure_method = row['procure method']
            if procure_method not in ['', 'make_to_order', 'make_to_stock']:
                self.add_spreadsheet_validation_error(
                    line_number,
                    "Procure Method '%s' does not match 'make_to_order' or 'make_to_stock'" % procure_method
                )

    def validate_hscomcode(self):
        """May be None or 10 digit number"""
        for line_number, row in enumerate(self.parsed_data[self.WORKBOOK_PARENT_SHEET]):
            hscomcode = row['hscomcode']
            if hscomcode and not self.HSCOMCODE_PATTERN.match(hscomcode):
                self.add_spreadsheet_validation_error(line_number, "Hscomcode '%s' must be 10 digits" % hscomcode)

    def validate_eccn(self):
        """Cant be longer than 16"""
        for line_number, row in enumerate(self.parsed_data[self.WORKBOOK_PARENT_SHEET]):
            eccn = row['eccn']
            if len(eccn) > 16:
                self.add_spreadsheet_validation_error(line_number, "ECCN '%s' must be less than 16 characters" % eccn)

    def validate_components_parent(self):
        for line_number, component in enumerate(self.parsed_data[self.WORKBOOK_COMPONENTS_SHEET]):
            if not component['parent']:
                self.add_spreadsheet_validation_error(line_number, 'Parent is required')
            else:
                if component['parent'] not in self.cleaned_spreadsheet_data:
                    self.add_spreadsheet_validation_error(
                        line_number, 'Parent \'%(parent)s\' is not defined in %(sheet)s sheet' % {
                            'parent': component['parent'], 'sheet': self.WORKBOOK_PARENT_SHEET
                        }
                    )

    def validate_components_msl(self):
        for line_number, component in enumerate(self.parsed_data[self.WORKBOOK_COMPONENTS_SHEET]):
            if component['msl']:
                if component['msl'] not in self.MSL_VALUES:
                    self.add_spreadsheet_validation_error(
                        line_number, 'MSL is not one of valid values: %s' % self.MSL_VALUES
                    )

    def validate_components_designators(self):
        """Optional but must be unique"""
        designators = set()
        for line_number, component in enumerate(self.parsed_data[self.WORKBOOK_COMPONENTS_SHEET]):
            if component['designators']:
                duplicates = []
                component['designators'] = [designator.strip() for designator in component['designators'].split(',')]
                for designator in component['designators']:
                    if designator in designators:
                        duplicates.append(designator)
                    designators.add(designator)
                if duplicates:
                    self.add_spreadsheet_validation_error(line_number, 'Duplicate Designator found: %s' % duplicates)

    def validate_all_parents_have_children(self):
        invalid_parents = []
        for parent in self.cleaned_spreadsheet_data.values():
            if not parent['children']:
                invalid_parents.append(parent['name'])
        if invalid_parents:
            raise ValidationError("Parents declared without any children: %s" % invalid_parents)


class CreateProjectForm(ProjectForm, ProjectBomForm):

    def save(self):
        with transaction.atomic():
            project = super().save()

            for quote_quantity in self.spreadsheet_quotation_quantities:
                QuoteQuantity.objects.create(project=project, quantity=quote_quantity)

            for parent in self.cleaned_spreadsheet_data.values():
                components = parent.pop('children')
                parent = Parent.objects.create(project=project, **parent)

                for component_kwargs in components:
                    designators = component_kwargs.pop('designators', [])
                    component_quantity = component_kwargs.pop('qty')

                    component = Component.objects.filter(
                        project=project, mpn=component_kwargs['mpn'], manufacturer=component_kwargs['manufacturer']
                    ).first()
                    if not component:
                        component = Component.objects.create(project=project, **component_kwargs)

                    parent_component = ParentComponent.objects.filter(parent=parent, component=component).first()
                    if not parent_component:
                        parent_component = ParentComponent(parent=parent, component=component, quantity=0)
                    parent_component.quantity += float(component_quantity)
                    parent_component.save()

                    for designator in designators:
                        Designator.objects.create(designator=designator, component=component)
        return project


class ProjectBomUpdateForm(ProjectBomForm):
    def __init__(self, project, *args, **kwargs):
        self.project = project
        super().__init__(*args, **kwargs)

    def save(self):
        with transaction.atomic():
            Parent.objects.filter(project=self.project).delete()
            Component.objects.filter(project=self.project).delete()
            QuoteQuantity.objects.filter(project=self.project).delete()
            BomParent.objects.filter(project=self.project).delete()
            self.project.bom_state = 'draft'
            self.project.save()

            suppliers = ProjectSupplier.objects.filter(project=self.project)
            if suppliers:
                self.project.wkf_supplier_info_rfq()
                for supplier in suppliers:
                    supplier.uploaded = False
                    supplier.save()

            for quote_quantity in self.spreadsheet_quotation_quantities:
                QuoteQuantity.objects.create(project=self.project, quantity=quote_quantity)

            for parent in self.cleaned_spreadsheet_data.values():
                components = parent.pop('children')
                parent = Parent.objects.create(project=self.project, **parent)

                for component_kwargs in components:
                    designators = component_kwargs.pop('designators', [])
                    component_quantity = component_kwargs.pop('qty')

                    component = Component.objects.filter(
                        project=self.project,
                        mpn=component_kwargs['mpn'],
                        manufacturer=component_kwargs['manufacturer']
                    ).first()
                    if not component:
                        component = Component.objects.create(project=self.project, **component_kwargs)

                    parent_component = ParentComponent.objects.filter(parent=parent, component=component).first()
                    if not parent_component:
                        parent_component = ParentComponent(parent=parent, component=component, quantity=0)
                    parent_component.quantity += float(component_quantity)
                    parent_component.save()

                    for designator in designators:
                        Designator.objects.create(designator=designator, component=component)


class CreateProjectSupplierForm(FormInlineModelFormset):
    FORMSET_MODEL = ProjectSupplier
    FORMSET_FACTORY_KWARGS = {'extra': False, 'min_num': 1}

    def __init__(self, project, *args, **kwargs):
        self.project = project
        self.save_workflow = project.wkf_supplier_info_rfq
        super().__init__(*args, **kwargs)

    @classmethod
    def get_formset_form(cls):
        return cls.FormsetForm

    @classmethod
    def get_formset_kwargs(cls):
        kwargs = super().get_formset_kwargs()
        kwargs['min_num'] = 1
        return kwargs

    def get_formset_queryset(self):
        return ProjectSupplier.objects.filter(project=self.project)

    def formset_save(self):
        with transaction.atomic():
            saved_ids = []
            for form in self.formset:
                supplier = form.save(self.project)
                saved_ids.append(supplier.id)
            self.get_formset_queryset().exclude(id__in=saved_ids).delete()

            if self.save_workflow:
                self.save_workflow()

    class FormsetForm(ModelForm):
        supplier = None
        supplier_id = ModelChoiceField(
            queryset=ResPartner.objects.filter(supplier=True, active=True),
            label='Supplier',
            widget=autocomplete.Select2(url='npi:autocompleteSupplier', attrs={'class': 'form-control'}),
        )

        def __init__(self, *args, **kwargs):
            kwargs['empty_permitted'] = False
            super().__init__(*args, **kwargs)

        def clean_supplier_id(self):
            self.supplier = self.cleaned_data['supplier_id']
            return self.cleaned_data['supplier_id'].id

        def save(self, project):
            self.instance.supplier_id = self.supplier.id
            self.instance.supplier_name = self.supplier.name
            self.instance.project = project
            self.instance.save()
            return self.instance

        class Meta:
            model = ProjectSupplier
            fields = ['supplier_id']


class EditProjectSupplierForm(CreateProjectSupplierForm):
    enabled = True

    def __init__(self, project, *args, **kwargs):
        super().__init__(project, *args, **kwargs)
        self.save_workflow = None

    def save(self):
        with transaction.atomic():
            super().save()
            self.project.refresh_from_db()
            if self.project.supplier_info_state == 'complete' and not self.project.supplier_info_ready_to_complete:
                self.project.wkf_supplier_info_rfq()

    class FormsetForm(CreateProjectSupplierForm.get_formset_form()):
        no_remove = True

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if not self.instance.uploaded:
                self.no_remove = False

        class Meta(CreateProjectSupplierForm.get_formset_form().Meta):
            fields = ['supplier_id', 'enabled']


class SupplierInformationUploadForm(SpreadsheetParser, Form):
    sheet = 'Purchasing'
    sheet_details = {
        sheet: {
            'supplier_id_cell': {'col': 7, 'row': 0},
            'header_row': 2,
            'headers': [
                'manufacturer', 'mpn', 'uom', 'rfq qty 1', 'rfq qty 2', 'rfq qty 3', 'rfq qty 4', 'rfq qty 5',
                'supplier part number', 'supplier description', 'supplier manufacturer', 'supplier mpn', 'supplier uom',
                'price qty 1', 'price qty 2', 'price qty 3', 'price qty 4', 'price qty 5', 'min order qty',
                'order multiples', 'current stock', 'leadtime'
            ]
        },
    }

    spreadsheet = FileField(label='Supplier Information Spreadsheet')

    def __init__(self, project, *args, **kwargs):
        self.project = project
        self.project_supplier = None

        components = {}
        for component in Component.objects.filter(project=self.project):
            manufacturer = components.get(component.manufacturer, {})
            manufacturer[component.mpn] = component
            components[component.manufacturer] = manufacturer
        self.components = components
        self.quotation_quantities = sorted(
            list(QuoteQuantity.objects.filter(project=project).order_by('quantity')),
            key=lambda x: x.quantity
        )
        self.required_price_columns = {}

        for quantity, quotation_quantity in enumerate(self.quotation_quantities):
            self.required_price_columns['price qty %s' % (quantity + 1)] = quotation_quantity

        super().__init__(*args, **kwargs)

    def get_sheet_data(self, sheets):
        data = super().get_sheet_data(sheets)
        cell_kwargs = self.sheet_details[self.sheet]['supplier_id_cell']
        cell_kwargs['sheet'] = sheets[self.sheet]['sheet']
        data['supplier_id'] = ExcelUtils.cell_string_value(**cell_kwargs)
        return data

    def clean_spreadsheet(self):
        self.load_workbook(self.cleaned_data['spreadsheet'])
        data = self.parsed_data[self.sheet]
        self.validate_supplier_id(self.parsed_data['supplier_id'])
        self.validate_customer_product(data)
        self.validate_supplier_part_number(data)
        self.validate_supplier_description(data)
        self.validate_supplier_component(data)
        self.validate_supplier_uom(data)
        self.validate_price_quantities(data)
        self.validate_moq(data)
        self.validate_order_multiples(data)
        self.validate_current_stock(data)
        self.validate_leadtime(data)
        self.raise_spreadsheet_validation_error(line_number_increment=self.sheet_details[self.sheet]['header_row']+2)

        self.cleaned_spreadsheet_data = []
        for row in data:
            if not row['supplier part number']:
                continue

            supplier_quotes = []
            for quote in row['prices']:
                supplier_quotes.append({'quote_quantity': quote['qty'], 'price': quote['price']})

            self.cleaned_spreadsheet_data.append({
                'component': row['component'],
                'project_supplier_id': self.project_supplier.id,
                'product_code': row['supplier part number'],
                'description': row['supplier description'],
                'manufacturer': row['supplier manufacturer'],
                'mpn': row['supplier mpn'],
                'uom_id': row['uom_id'],
                'uom_name': row['supplier uom'],
                'moq': row['min order qty'],
                'order_multiples': row['order multiples'],
                'current_stock': row['current stock'] or None,
                'leadtime': row['leadtime'] or None,
                'supplier_quotes': supplier_quotes
            })

    def save(self):
        created_supplier_products = []
        with transaction.atomic():

            SupplierComponent.objects.filter(project_supplier=self.project_supplier).delete()
            self.project.wkf_supplier_info_rfq()

            for component in self.cleaned_spreadsheet_data:
                quotes = component.pop('supplier_quotes')
                supplier_component = SupplierComponent.objects.create(**component)
                for quote in quotes:
                    quote['product'] = supplier_component
                    SupplierProductQuote.objects.create(**quote)
                created_supplier_products.append(supplier_component)

            self.project_supplier.upload()

            if self.project.supplier_info_ready_to_complete:
                self.project.wkf_supplier_info_complete()
        return created_supplier_products

    def validate_supplier_id(self, supplier_id):
        try:
            supplier_id = int(supplier_id)
        except ValueError:
            raise ValidationError("Supplier ID '%s' is not a number" % supplier_id)
        self.project_supplier = ProjectSupplier.objects.filter(project=self.project, supplier_id=supplier_id).first()
        if not self.project_supplier:
            raise ValidationError(
                "Project '%(project)s' has no supplier with id '%(supplier)s'" % {
                    'project': self.project, 'supplier': supplier_id
                })

    def validate_customer_product(self, data):
        for line_number, row in enumerate(data):
            if row['supplier part number']:
                if row['manufacturer'] not in self.components or row['mpn'] not in self.components[row['manufacturer']]:
                    self.add_spreadsheet_validation_error(
                        line_number,
                        "Component '%(manufacturer)s' '%(mpn)s' not part of %(project)s BOM" % {
                            'manufacturer': row['manufacturer'],
                            'mpn': row['mpn'],
                            'project': self.project
                        }
                    )
                else:
                    row['component'] = self.components[row['manufacturer']][row['mpn']]

    def validate_supplier_part_number(self, data):
        part_numbers = {}
        headers = self.sheet_details[self.sheet]['headers']
        ignore_headers = [
            'supplier part number', 'manufacturer', 'mpn', 'uom', 'rfq qty 1',
            'rfq qty 2', 'rfq qty 3', 'rfq qty 4', 'rfq qty 5'
        ]
        required_empty_headers = [x for x in headers if x not in ignore_headers]

        for line_number, row in enumerate(data):
            part_number = row['supplier part number']
            # supplier part number is required if any other field is provided
            if not part_number:
                for column in required_empty_headers:
                    if row[column]:
                        self.add_spreadsheet_validation_error(
                            line_number,
                            "Supplier Part Number is required"
                        )
                    break
            else:
                if part_number in part_numbers:
                    self.add_spreadsheet_validation_error(
                        line_number,
                        "Supplier Part Number '%s' is a duplicate of line %s" % (
                            part_number, part_numbers[part_number])
                    )
                else:
                    part_numbers[part_number] = line_number + self.sheet_details[self.sheet]['header_row'] + 2

    def validate_supplier_description(self, data):
        for line_number, row in enumerate(data):
            if row['supplier part number'] and not row['supplier description']:
                self.add_spreadsheet_validation_error(line_number, 'Supplier Description is required')

    def validate_supplier_component(self, data):
        for line_number, row in enumerate(data):
            supplier_part = row['supplier part number']
            manufacturer = row['supplier manufacturer'].lower()
            mpn = row['supplier mpn'].lower()

            if not supplier_part and not manufacturer and not mpn:
                continue
            if not manufacturer:
                self.add_spreadsheet_validation_error(line_number, "Supplier Manufacturer is required")
            if not mpn:
                self.add_spreadsheet_validation_error(line_number, "Supplier MPN is required")

    def validate_supplier_uom(self, data):
        uoms = {x.name: x for x in ProductUom.objects.filter(name__in=[x['supplier uom'] for x in data])}

        for line_number, row in enumerate(data):

            if row['supplier part number']:
                uom = row['supplier uom']
                if not uom:
                    self.add_spreadsheet_validation_error(line_number, "Supplier UoM is required")
                elif uom not in uoms:
                    self.add_spreadsheet_validation_error(
                        line_number, "Supplier UoM '%s' doesn't exist on OpenERP" % row['supplier uom']
                    )
                else:
                    row['uom_id'] = uoms[uom].id

    def validate_price_quantities(self, data):
        for line_number, row in enumerate(data):
            if row['supplier part number']:
                row['prices'] = []
                for column in self.required_price_columns:
                    if not row[column]:
                        self.add_spreadsheet_validation_error(line_number, "%s is required" % column)
                    else:
                        try:
                            price = float(row[column])
                            row['prices'].append({'price': price, 'qty': self.required_price_columns[column]})
                        except ValueError:
                            self.add_spreadsheet_validation_error(
                                line_number,
                                "%(column)s '%(value)s' is not a number" % {'column': column, 'value': row[column]}
                            )

    def validate_moq(self, data):
        self._validate_lines(
            data, self._row_number_required_if_supplier_part_number,
            {'column': 'min order qty', 'verbose_column': 'Min Order Qty'}
        )

    def validate_order_multiples(self, data):
        self._validate_lines(
            data, self._row_number_required_if_supplier_part_number,
            {'column': 'order multiples', 'verbose_column': 'Order Multiples'}
        )

    def validate_current_stock(self, data):
        self._validate_lines(
            data, self._row_number_optional, {'column': 'current stock', 'verbose_column': 'Current Stock'}
        )

    def validate_leadtime(self, data):
        self._validate_lines(data, self._row_number_optional, {'column': 'leadtime', 'verbose_column': 'Leadtime'})

    def _validate_lines(self, data, line_function, line_kwargs=None):
        line_kwargs = line_kwargs or {}
        for line_number, row in enumerate(data):
            line_kwargs.update({'line_number': line_number, 'row': row})
            line_function(**line_kwargs)

    def _row_number_required_if_supplier_part_number(self, row, line_number, column, verbose_column):
        if row['supplier part number']:
            if not row[column]:
                self.add_spreadsheet_validation_error(line_number, '%s is required' % verbose_column)
            else:
                try:
                    float(row[column])
                except ValueError:
                    self.add_spreadsheet_validation_error(
                        line_number, "%s '%s' is not a number" % (verbose_column, row[column])
                    )

    def _row_number_optional(self, row, line_number, column, verbose_column):
        if row[column]:
            try:
                float(row[column])
            except ValueError:
                self.add_spreadsheet_validation_error(
                    line_number,
                    "%(column)s '%(value)s' is not a number" % {'column': verbose_column, 'value': row[column]}
                )


class QuoteQuantityForm(Form):
    def __init__(self, project, quote_quantity, *args, **kwargs):
        initial = kwargs.get('initial', {})
        initial.update({'quote_quantity': quote_quantity})
        kwargs['initial'] = initial

        super().__init__(*args, **kwargs)
        self.fields['quote_quantity'].widget = autocomplete.ModelSelect2(
            url=reverse('npi:autocompleteQuoteQuantity', kwargs={'project_id': project.id}),
            attrs={'class': 'form-control'}
        )
        self.fields['quote_quantity'].queryset = QuoteQuantity.objects.filter(project=project)

    quote_quantity = ModelChoiceField(QuoteQuantity.objects.none())


class SelectSupplierComponentForm(Form):
    def __init__(self, component, quote_quantity, *args, **kwargs):
        initial = kwargs.get('initial', {})
        initial['supplier_component'] = component.selected_quote(quote_quantity).product
        kwargs['initial'] = initial

        super().__init__(*args, **kwargs)
        self.fields['supplier_component'].widget = autocomplete.ModelSelect2(
            url=reverse('npi:autocompleteSupplierComponent', kwargs={'component_id': component.id}),
            attrs={'class': 'form-control update-component-quote'}
        )
        self.fields['supplier_component'].queryset = SupplierComponent.objects.filter(component=component)

    supplier_component = ModelChoiceField(SupplierComponent.objects.none())


class ExportSupplierInformationToOpenErpForm(Form, OpenerpXmlrpc):
    def __init__(self, project, quote_quantity=None, *args, **kwargs):
        if quote_quantity:
            initial = kwargs.get('initial', {})
            initial.update({'quote_quantity': quote_quantity})
            kwargs['initial'] = initial

        super().__init__(*args, **kwargs)
        self.fields['quote_quantity'].widget = autocomplete.ModelSelect2(
            url=reverse('npi:autocompleteQuoteQuantity', kwargs={'project_id': project.id}),
            attrs={'class': 'form-control'},
        )
        self.fields['quote_quantity'].queryset = QuoteQuantity.objects.filter(project=project)

    quote_quantity = ModelChoiceField(
        queryset=QuoteQuantity.objects.all(),
        label='Quotation Quantity',
    )

    username = CharField(
        help_text="OpenERP Username",
        max_length=50,
        widget=TextInput(attrs={'class': 'form-control'})
    )

    password = CharField(
        help_text="OpenERP Password",
        max_length=50,
        widget=PasswordInput(attrs={'class': 'form-control'})
    )

    def connect(self):
        self._CONNECTION_ARGS['username'] = self.cleaned_data['username']
        self._CONNECTION_ARGS['password'] = self.cleaned_data['password']
        return super().connect()

    def is_valid(self):
        is_valid = super().is_valid()
        if is_valid:
            try:
                self.connect()
            except Exception:
                self.add_error('username', 'OpenERP Username or Password is incorrect')
                is_valid = False
        return is_valid

    def save(self):
        self.connect()
        with transaction.atomic():
            self.cleaned_data['quote_quantity'].project.wkf_supplier_info_uploaded()

            result = self.openerp_execute(
                'product.supplierinfo',
                'npi_bulk_upload',
                self.cleaned_data['quote_quantity'].export_data_for_openerp()
            )

            created_product_ids = result['component_product_ids']
            created_products = {
                x.id: x.default_code for x in ProductProduct.objects.filter(id__in=created_product_ids.values())
            }
            for component in Component.objects.filter(id__in=created_product_ids.keys()):
                component.product_id = created_product_ids[str(component.id)]
                component.product_code = created_products[component.product_id]
                component.save()

            created_parent_ids = result['parent_product_ids']
            for parent in Parent.objects.filter(id__in=created_parent_ids.keys()):
                parent.product_id = created_parent_ids[str(parent.id)]
                parent.save()

        return True


class SupplierComponentAlternativeForm(FormInlineModelFormset):
    FORMSET_MODEL = SupplierComponent
    FORMSET_FACTORY_KWARGS = {'extra': False}

    def __init__(self, project, *args, **kwargs):
        self.project = project
        super().__init__(*args, **kwargs)

    @classmethod
    def get_formset_form(cls):
        return cls.FormsetForm

    def get_formset_queryset(self):
        return SupplierComponent.objects.filter(
            component__project=self.project, alternative=True, project_supplier__enabled=True
        ).order_by('component__manufacturer', 'component__mpn')

    class FormsetForm(ModelForm):
        @property
        def workflow_functions(self):
            return {
                'normal': self.instance.wkf_normal,
                'reject': self.instance.wkf_rejected,
                'pending': self.instance.wkf_pending
            }

        def save(self, *args, **kwargs):
            workflow_function = self.workflow_functions.get(self.cleaned_data['state'])
            if workflow_function:
                workflow_function()
            self.instance.save()

        class Meta:
            model = SupplierComponent
            fields = ['state']


class BomUploadForm(SpreadsheetParser, Form):
    SPREADSHEET_PARENT_SHEET = 'Parents'
    SPREADSHEET_COMPONENT_SHEET = 'Components'
    procurement_types = ['make_to_order', 'make_to_stock']
    bom_types = ['phantom', 'normal']

    def __init__(self, project, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        self.sheet_details = {
            self.SPREADSHEET_PARENT_SHEET: {
                'header_row': 0,
                'headers': [
                    'Parent Code', 'Description', 'Layer', 'Parent Produced Quantity', 'Parent Produced UOM',
                    'Procurement Type', 'Routing', 'Bom Type', 'Bom Parent', 'Customer Parent'
                ]
            },
            self.SPREADSHEET_COMPONENT_SHEET: {
                'header_row': 0, 'headers': ['Designator', 'Layer', 'UOM', 'Quantity']
            }
        }
        self.designators_missing_from_bom = []

    ignore_missing_designator_warnings = ChoiceField(
        choices=[('no', 'No'), ('yes', 'Yes')],
        label='Ignore Missing Designator Warnings',
        help_text="Uploaded bom may be missing designators from customer bom",
        widget=Select(attrs={'class': 'form-control'})
    )
    spreadsheet = FileField(label='Supplier Information Spreadsheet')

    def clean_ignore_missing_designator_warnings(self):
        if self.cleaned_data['ignore_missing_designator_warnings'] == 'yes':
            return True
        return False

    def clean_spreadsheet(self):
        self.load_workbook(self.cleaned_data['spreadsheet'])
        self.validate_parent_sheet()
        self.validate_component_sheet()

    def clean(self):
        if not self.cleaned_data['ignore_missing_designator_warnings'] and self.designators_missing_from_bom:
            errors = []
            for designator in self.designators_missing_from_bom:
                errors.append("Designator '%s' is defined on customer bom but missing on the x/y data" % designator)
            self.add_error('spreadsheet', ValidationError(errors))
        return super().clean()

    def get_sheet_data(self, sheets):
        parsed_data = super().get_sheet_data(sheets)
        parent_data = parsed_data[self.SPREADSHEET_PARENT_SHEET]
        has_customer_parent = False
        for row in parent_data:
            if row['customer parent']:
                has_customer_parent = True
                break
        if not has_customer_parent:
            raise ValidationError(
                "%s Sheet must contain one line with a Customer Parent" % self.SPREADSHEET_PARENT_SHEET
            )
        return parsed_data

    def validate_parent_sheet(self):
        data = self.parsed_data[self.SPREADSHEET_PARENT_SHEET]
        # TODO Parent code can't match a Parent object
        self.validate_column_required_unique(data, 'parent code', 'Parent Code')
        self.validate_column_required(data, 'description', 'Description is required')
        self.validate_column_required_unique(data, 'layer', 'Layer')
        self.validate_quantity(data, 'parent produced quantity')
        self.validate_uom(data, 'parent produced uom')
        self.validate_procurement_type()
        self.validate_routing(data, 'routing')
        self.validate_bom_type()
        self.validate_bom_parent()
        self.raise_spreadsheet_validation_error(
            '%s Sheet' % self.SPREADSHEET_PARENT_SHEET,
            line_number_increment=self.sheet_details[self.SPREADSHEET_PARENT_SHEET]['header_row'] + 2
        )

        self.cleaned_parents = {}
        self.cleaned_child_parents = []
        self.layers = {}

        self.customer_parents = set([x['customer parent'] for x in data if x['customer parent']])

        for parent in self.customer_parents:
            parent_object = Parent.objects.filter(project=self.project, name=parent).first()
            self.cleaned_parents.update({
                parent: {
                    'product_code': parent,
                    'description': parent_object.description,
                    'quantity': parent_object.quantity,
                    'uom_id': parent_object.uom_id,
                    'uom_name': parent_object.uom_name,
                    'procure_method': parent_object.procure_method,
                    'routing_name': parent_object.routing_name,
                    'routing_id': parent_object.routing_id
                }
            })

        for parent in data:
            self.layers.update({parent['layer']: parent['parent code']})
            self.cleaned_parents.update({
                parent['parent code']: {
                    'product_code': parent['parent code'],
                    'description': parent['description'],
                    'quantity': parent['parent produced quantity'],
                    'uom_id': parent['parent produced uom_uom_id'],
                    'uom_name': parent['parent produced uom'],
                    'procure_method': parent['procurement type'],
                    'routing_name': parent['routing'],
                    'routing_id': parent['routing_id']
                }
            })

            self.cleaned_child_parents.append({
                'product_code': parent['parent code'],
                'parent_code': parent['bom parent'] or parent['customer parent'],
                'quantity': parent['parent produced quantity'],
                'uom_id': parent['parent produced uom_uom_id'],
                'uom_name': parent['parent produced uom'],
                'bom_type': parent['bom type']
            })

    def validate_component_sheet(self):
        data = self.parsed_data[self.SPREADSHEET_COMPONENT_SHEET]
        self.validate_designator()
        self.validate_layer()
        self.validate_quantity(data, 'quantity')
        self.validate_uom(data, 'uom')
        self.raise_spreadsheet_validation_error(
            '%s Sheet' % self.SPREADSHEET_COMPONENT_SHEET,
            line_number_increment=self.sheet_details[self.SPREADSHEET_COMPONENT_SHEET]['header_row'] + 2
        )

        self.cleaned_components_data = {}
        for row in data:
            layer = row['layer']
            parent = self.layers[layer]
            layer_components = self.cleaned_components_data.get(parent, [])
            layer_components.append({
                'component': row['component'],
                'quantity': row['quantity'],
                'uom_id': row['uom_uom_id'],
                'uom_name': row['uom']
            })
            self.cleaned_components_data[parent] = layer_components

    def validate_procurement_type(self):
        for line_number, row in enumerate(self.parsed_data[self.SPREADSHEET_PARENT_SHEET]):
            value = row.get('procurement type')
            if not value:
                self.add_spreadsheet_validation_error(line_number, "Procurement Type is required")
            elif value.strip().lower() not in self.procurement_types:
                self.add_spreadsheet_validation_error(
                    line_number, "Procurement Type '%s' is not in %s" % (value, self.procurement_types)
                )

    def validate_bom_type(self):
        for line_number, row in enumerate(self.parsed_data[self.SPREADSHEET_PARENT_SHEET]):
            value = row.get('bom type')
            if not value:
                self.add_spreadsheet_validation_error(line_number, "BOM Type is required")
            elif value.strip().lower() not in self.bom_types:
                self.add_spreadsheet_validation_error(
                    line_number, "BOM Type '%s' is not in %s" % (value, self.bom_types)
                )

    def validate_bom_parent(self):
        data = self.parsed_data[self.SPREADSHEET_PARENT_SHEET]
        customer_parents = {parent.name: parent for parent in Parent.objects.filter(project=self.project)}
        bom_parents = [x['parent code'] for x in data]

        for line_number, row in enumerate(data):
            bom_parent = row.get('bom parent')
            customer_parent = row.get('customer parent')

            if not bom_parent and not customer_parent:
                self.add_spreadsheet_validation_error(line_number, 'No Parent provided')

            elif bom_parent and customer_parent:
                self.add_spreadsheet_validation_error(line_number, "Cant have both a BoM Parent and a Customer Parent")

            elif customer_parent:
                if customer_parent not in customer_parents:
                    self.add_spreadsheet_validation_error(
                        line_number, "Customer Parent '%s' doesn't exist for this project" % customer_parent
                    )
                else:
                    row['customer parent record'] = customer_parents[customer_parent]

            elif bom_parent:
                if bom_parent == row['parent code']:
                    self.add_spreadsheet_validation_error(
                        line_number, "BOM Parent '%s' is a reference to itself" % bom_parent
                    )
                elif bom_parent not in bom_parents:
                    self.add_spreadsheet_validation_error(
                        line_number, "BOM Parent '%s' does not reference a Parent Code on this spreadsheet" % bom_parent
                    )

    def validate_designator(self):
        data = self.parsed_data[self.SPREADSHEET_COMPONENT_SHEET]
        designators = set()
        project_designators = {
            x.designator: x.component for x in Designator.objects.filter(component__project=self.project)
        }

        for line_number, row in enumerate(data):
            designator = row['designator']

            if not designator:
                self.add_spreadsheet_validation_error(line_number, 'Designator is required')
                continue
            if designator in designators:
                self.add_spreadsheet_validation_error(line_number, "Designator '%s' is duplicated" % designator)
            elif designator not in project_designators:
                self.add_spreadsheet_validation_error(
                    line_number, "Designator '%s' is not on the Customer BOM" % designator
                )
            else:
                row['component'] = project_designators[designator]
                project_designators.pop(designator)
            designators.add(designator)
        self.designators_missing_from_bom = project_designators.keys()

    def validate_layer(self):
        for line_number, row in enumerate(self.parsed_data[self.SPREADSHEET_COMPONENT_SHEET]):
            if row['layer'] not in self.layers:
                self.add_spreadsheet_validation_error(
                    line_number,
                    "Layer '%s' does not exist on the '%s' Sheet" % (row['layer'], self.SPREADSHEET_PARENT_SHEET)
                )

    def save(self):
        with transaction.atomic():
            # Delete existing boms for the uploaded customer parents
            existing_parents = BomParent.objects.filter(project=self.project, product_code__in=self.customer_parents)
            for parent in existing_parents:
                for child in parent.get_descendant_parents():
                    child.delete()
                parent.delete()

            created_bom_parents = {}
            for parent in self.cleaned_parents:
                parent_data = self.cleaned_parents[parent]
                parent_data['project'] = self.project

                bom_parent = BomParent.objects.create(**parent_data)
                created_bom_parents[bom_parent.product_code] = bom_parent.id

                for child in self.cleaned_components_data.get(parent_data['product_code'], []):
                    existing_child = BomComponent.objects.filter(
                        parent=bom_parent, component=child['component']
                    ).first()

                    if existing_child:
                        existing_child.quantity += float(child['quantity'])
                        existing_child.save()
                    else:
                        child['parent'] = bom_parent
                        BomComponent.objects.create(**child)

            for parent in self.cleaned_child_parents:
                product_code = parent.pop('product_code')
                parent_code = parent.pop('parent_code')
                parent.update({
                    'product_id': created_bom_parents[product_code],
                    'parent_id': created_bom_parents[parent_code],
                })
                BomChildParent.objects.create(**parent)

            for parent in Parent.objects.filter(name__in=self.customer_parents):
                parent.bom_uploaded = True
                parent.save()

            self.project.wkf_bom_ready()
        return self.project


class ExportBomToOpenErpForm(Form, OpenerpXmlrpc):
    def __init__(self, project, *args, **kwargs):
        self.project = project
        super().__init__(*args, **kwargs)

    username = CharField(
        help_text="OpenERP Username",
        max_length=50,
        widget=TextInput(attrs={'class': 'form-control'})
    )

    password = CharField(
        help_text="OpenERP Password",
        max_length=50,
        widget=PasswordInput(attrs={'class': 'form-control'})
    )

    def connect(self):
        self._CONNECTION_ARGS['username'] = self.cleaned_data['username']
        self._CONNECTION_ARGS['password'] = self.cleaned_data['password']
        return super().connect()

    def is_valid(self):
        is_valid = super().is_valid()
        if is_valid:
            try:
                self.connect()
            except Exception:
                self.add_error('username', 'OpenERP Username or Password is incorrect')
                is_valid = False
        return is_valid

    def save(self):
        with transaction.atomic():
            self.project.wkf_bom_uploaded()
            self.openerp_execute(
                'mrp.bom',
                'load_npi_bom',
                BomParent.export_bom_openerp(self.project)
            )

