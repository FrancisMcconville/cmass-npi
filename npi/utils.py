import xlrd
from xlutils.copy import copy
from django.db import connections
from metrics.utils import dictfetchall
from io import BytesIO
import decimal


NPI_PROJECT_MAX_QUOTATION_QUANTITY = 5
RFQ_TEMPLATE = 'static/npi/excel_templates/rfq_template.xls'
SUPPLIER_INFO_TEMPLATE = 'static/npi/excel_templates/supplier_info_template.xls'


class ExcelUtils:
    decimal_context = decimal.Context()
    decimal_context.prec = 20

    # https://stackoverflow.com/a/7686555
    @staticmethod
    def _get_out_cell(sheet, row, col):
        """ HACK: Extract the internal xlwt cell representation. """
        row = sheet._Worksheet__rows.get(row)
        if not row:
            return None

        cell = row._Row__cells.get(col)
        return cell

    @staticmethod
    def set_cell_value(sheet, row, col, value):
        """ Change cell value without changing formatting. """
        previous_cell = ExcelUtils._get_out_cell(sheet, row, col)

        sheet.write(row, col, value)

        if previous_cell:
            new_cell = ExcelUtils._get_out_cell(sheet, row, col)
            if new_cell:
                new_cell.xf_idx = previous_cell.xf_idx

    @staticmethod
    def copy_row_style(sheet, ncols, source_row, destination_row):
        for column in range(0, ncols):
            source_cell = ExcelUtils._get_out_cell(sheet, source_row, column)
            if source_cell:
                sheet.write(destination_row, column, '')
                new_cell = ExcelUtils._get_out_cell(sheet, destination_row, column)
                new_cell.xf_idx = source_cell.xf_idx

    @staticmethod
    def cell_string_value(sheet, row, col):
        value = ExcelUtils._get_cell_value(sheet, row, col).value
        if isinstance(value, float):
            value = ExcelUtils._sanitize_float_to_string(value)
        return value.strip()

    @staticmethod
    def _get_cell_value(sheet, row, col):
        return sheet.cell(row, col)

    @staticmethod
    def _sanitize_float_to_string(value):
        decimal_value = ExcelUtils.decimal_context.create_decimal(repr(value))
        string_value = format(decimal_value, 'f')
        number_of_digits = len(string_value)

        if '.' in string_value:
            number_of_digits -= 1
            number_of_decimal_places = len(string_value.split('.')[1])

            if number_of_decimal_places > 6:
                number_of_digits -= number_of_decimal_places
                number_of_digits += 6

        format_string = '{:.%sg}' % number_of_digits
        return format_string.format(value)


class SupplierRfqSpreadsheetGenerator(object):
    template = 'static/npi/excel_templates/rfq_template.xls'
    output = None
    template_sheet = None
    output_workbook = None
    sheet = None
    components = None
    quote_quantities = None

    first_component_row = 3
    supplier_info_column_mapping = {
        'product_code': 8, 'description': 9, 'manufacturer': 10, 'mpn': 11, 'uom_name': 12,
        'moq': 18, 'order_multiples': 19
    }
    component_column_mapping = {'manufacturer': 0, 'mpn': 1, 'uom_name': 2}
    quote_quantities_column = 3

    def __init__(self, supplier):
        self.supplier = supplier

    def _get_existing_supplier_info(self):
        from npi.models import Component
        cursor = connections['default'].cursor()
        cursor.execute("""
        SELECT
        component_upload_date.component_name,
        supplier_component.mpn,
        supplier_component.manufacturer,
        supplier_component.product_code,
        supplier_component.description,
        supplier_component.uom_name,
        supplier_component.moq,
        supplier_component.order_multiples
        
        -- Select the latest upload date for each component
        FROM (
            SELECT
            component.manufacturer||component.mpn AS component_name,
            max(supplier.upload_date) AS last_upload
            
            FROM npi_component component 
            JOIN npi_suppliercomponent supplier_component ON component.id = supplier_component.component_id
            JOIN npi_projectsupplier supplier ON supplier_component.project_supplier_id = supplier.id
            
            WHERE supplier.supplier_id = %(supplier_id)s
            GROUP BY component_name
        ) AS component_upload_date
        
        -- Join the suppliercomponent ids which were uploaded at the latest date for each component
        JOIN ( 
            SELECT 
            component.manufacturer||component.mpn AS component_name, 
            supplier.upload_date,
            supplier_component.id 
            
            FROM npi_component component
            JOIN npi_suppliercomponent supplier_component ON supplier_component.component_id = component.id
            JOIN npi_projectsupplier supplier ON supplier.id = supplier_component.project_supplier_id
            
            WHERE supplier.supplier_id = %(supplier_id)s
            AND supplier_component.state NOT IN ('reject')
            ORDER BY component.manufacturer
        ) AS latest_supplier_component ON (
            component_upload_date.last_upload = latest_supplier_component.upload_date
            AND latest_supplier_component.component_name = component_upload_date.component_name
        )
        JOIN npi_suppliercomponent supplier_component ON latest_supplier_component.id = supplier_component.id        
        JOIN npi_projectsupplier supplier ON supplier_component.project_supplier_id = supplier.id

        WHERE latest_supplier_component.component_name IN %(component_names)s
        ORDER BY latest_supplier_component.component_name
        """ % {
            'component_names': '(%s)' % ','.join(
                "'%(manufacturer)s%(mpn)s'" % {
                    'manufacturer': x.manufacturer, 'mpn': x.mpn
                } for x in Component.objects.filter(project=self.supplier.project)
            ),
            'supplier_id': self.supplier.supplier_id
        })
        result = {}
        for line in dictfetchall(cursor):
            component_name = line.pop('component_name')
            component_suppliers = result.get(component_name, [])
            component_suppliers.append(line)
            result[component_name] = component_suppliers
        return result

    def _initialize_data(self):
        from npi.models import Component, QuoteQuantity
        template_workbook = xlrd.open_workbook(self.template, formatting_info=True)
        self.output = BytesIO()
        self.template_sheet = template_workbook.sheet_by_index(0)
        self.output_workbook = copy(template_workbook)
        self.sheet = self.output_workbook.get_sheet(0)
        self.components = Component.objects.filter(project=self.supplier.project).order_by('mpn')
        self.quote_quantities = QuoteQuantity.objects.filter(project=self.supplier.project).order_by('quantity')
        self.supplierinfo = self._get_existing_supplier_info()

    def get_spreadsheet(self):
        self._initialize_data()
        self._print_project_details()

        line_number = self.first_component_row
        for component in self.components:
            quantities = [x.quantity * component.quantity for x in self.quote_quantities]
            existing_supplier_records = self.supplierinfo.get("%s%s" % (component.manufacturer, component.mpn), [{}])

            for supplier_info in existing_supplier_records:
                ExcelUtils.copy_row_style(self.sheet, self.template_sheet.ncols, 3, line_number)
                self._print_component_line(component, line_number)
                self._print_component_supplier_info_line(supplier_info, line_number)
                self._print_quantities(quantities, line_number)
                line_number += 1

        self.output_workbook.save(self.output)
        return self.output

    def _print_component_line(self, component, row):
        for attribute in self.component_column_mapping:
            column = self.component_column_mapping[attribute]
            ExcelUtils.set_cell_value(self.sheet, row, column, getattr(component, attribute))

    def _print_component_supplier_info_line(self, supplier_info, row):
        for attribute in self.supplier_info_column_mapping:
            column = self.supplier_info_column_mapping[attribute]
            ExcelUtils.set_cell_value(self.sheet, row, column, supplier_info.get(attribute))

    def _print_project_details(self):
        ExcelUtils.set_cell_value(self.sheet, 0, 1, self.supplier.supplier_name)
        ExcelUtils.set_cell_value(self.sheet, 0, 3, str(self.supplier.project))
        ExcelUtils.set_cell_value(self.sheet, 0, 5, "GBP")
        ExcelUtils.set_cell_value(self.sheet, 0, 7, self.supplier.supplier_id)

    def _print_quantities(self, quantities, row):
        for index, quantity in enumerate(quantities):
            ExcelUtils.set_cell_value(self.sheet, row, index + self.quote_quantities_column, quantity)


class SupplierRfqExistingSpreadsheetGenerator(SupplierRfqSpreadsheetGenerator):
    supplier_info_column_mapping = {
        'product_code': 8, 'description': 9, 'manufacturer': 10, 'mpn': 11, 'uom_name': 12,
        'price_1': 13, 'price_2': 14, 'price_3': 15, 'price_4': 16, 'price_5': 17,
        'moq': 18, 'order_multiples': 19, 'current_stock': 20, 'leadtime': 21
    }

    def _get_existing_supplier_info(self):
        from npi.models import SupplierProductQuote, SupplierComponent
        result = {}
        for product in SupplierComponent.objects.filter(project_supplier=self.supplier):
            details = {
                'manufacturer': product.manufacturer,
                'moq': product.moq,
                'uom_name': product.uom_name,
                'mpn': product.mpn,
                'description': product.description,
                'product_code': product.product_code,
                'order_multiples': product.order_multiples,
                'current_stock': product.current_stock,
                'leadtime': product.leadtime
            }
            for index, quote in enumerate(SupplierProductQuote.objects.filter(product=product).order_by('quote_quantity__quantity')):
                details.update({'price_%s' % str(index+1): quote.price})
            supplier_info = result.get(product.component_id, [])
            supplier_info.append(details)
            result[product.component_id] = supplier_info

        return result

    def get_spreadsheet(self):
        self._initialize_data()
        self._print_project_details()

        line_number = self.first_component_row
        for component in self.components:
            quantities = [x.quantity * component.quantity for x in self.quote_quantities]
            existing_supplier_records = self.supplierinfo.get(component.id, [{}])

            for supplier_info in existing_supplier_records:
                ExcelUtils.copy_row_style(self.sheet, self.template_sheet.ncols, 3, line_number)
                self._print_component_line(component, line_number)
                self._print_component_supplier_info_line(supplier_info, line_number)
                self._print_quantities(quantities, line_number)
                line_number += 1

        self.output_workbook.save(self.output)
        return self.output
