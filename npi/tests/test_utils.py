from django.db import connections
from django.test import TestCase
from npi.utils import ExcelUtils, SupplierRfqSpreadsheetGenerator
from npi.models import Component, Project, ProjectSupplier, SupplierComponent
import xlrd


class TestExcelUtils(TestCase):

    def test_get_cell_string_value_float(self):
        value = float(5.6)
        self.assertEquals('5.6', ExcelUtils._sanitize_float_to_string(value))

    def test_get_cell_string_value_ignore_redundant_zeros_past_decimal_point(self):
        value = float(1000000.0)
        self.assertEquals('1000000', ExcelUtils._sanitize_float_to_string(value))

    def test_get_cell_string_value_ignores_leading_redundant_zeros_if_decimal_place(self):
        value = float(056810.101)
        self.assertEquals('56810.101', ExcelUtils._sanitize_float_to_string(value))

    def test_get_cell_string_value_round_to_6_decimal_places(self):
        value = float(1.333333333333333333333333333)
        self.assertEquals('1.333333', ExcelUtils._sanitize_float_to_string(value))

    def test_get_cell_string_value_large_number_with_more_than_6_decimal_places(self):
        value = float(1010101010.33333333)
        self.assertEquals('1010101010.333333', ExcelUtils._sanitize_float_to_string(value))

    def test_get_cell_string_value_large_number(self):
        value = float(10101010101010.0)
        self.assertEquals('10101010101010', ExcelUtils._sanitize_float_to_string(value))


class TestSupplierRfqSpreadsheetGenerator(TestCase):
    fixtures = ['npi/fixtures/npi.projects_shared_components_and_suppliers.json']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cursor = connections['default'].cursor()

        cls.generator_class = SupplierRfqSpreadsheetGenerator
        cls.component_mpn = '09.03201.02'
        cls.component_manufacturer = 'EOZ'
        cls.draft_project = Project.objects.get(name='CM001031')
        cls.uploaded_project = Project.objects.get(name='CM001030')
        cls.supplier_id = 420

        cls.supplier = ProjectSupplier.objects.filter(
            project__name=cls.draft_project.name,
            supplier_id=cls.supplier_id
        ).first()
        cls.component = Component.objects.filter(
            project=cls.draft_project, mpn=cls.component_mpn, manufacturer=cls.component_manufacturer
        ).first()

    def test_get_existing_supplier_info_returns_most_recent_supplierinfo(self):
        expected_product_code = 'MOST_RECENT_SUPPLIERINFO'

        SupplierComponent.objects.create(
            project_supplier=self.supplier, component=self.component, product_code=expected_product_code,
            description='test', manufacturer='test', mpn='test', uom_id=1, uom_name='PCE',
            moq=1, order_multiples=1
        )
        self.supplier.upload()

        instance = self.generator_class(self.supplier)
        supplierinfo_key = '%s%s' % (self.component_manufacturer, self.component_mpn)
        most_recent_supplierinfo = instance._get_existing_supplier_info()[supplierinfo_key]

        self.assertEquals(len(most_recent_supplierinfo), 1)
        self.assertEquals(most_recent_supplierinfo[0]['product_code'], expected_product_code)

    def test_get_existing_supplier_info_returns_non_reject_alternatives(self):
        number_alternatives = 3
        for i in range(0, number_alternatives):
            SupplierComponent.objects.create(
                project_supplier=self.supplier, component=self.component, product_code='Alternative %s' % i,
                description='test', manufacturer='test', mpn='test', uom_id=1, uom_name='PCE',
                moq=1, order_multiples=1
            )

        reject_code = 'Reject'
        reject = SupplierComponent.objects.create(
            project_supplier=self.supplier, component=self.component, product_code=reject_code,
            description='test', manufacturer='test', mpn='test', uom_id=1, uom_name='PCE',
            moq=1, order_multiples=1
        )
        self.supplier.upload()
        reject.wkf_rejected()

        instance = self.generator_class(self.supplier)
        supplierinfo_key = '%s%s' % (self.component_manufacturer, self.component_mpn)
        result = instance._get_existing_supplier_info()[supplierinfo_key]

        for supplierinfo in result:
            self.assertFalse(supplierinfo['product_code'] == reject_code)

        self.assertEquals(len(result), number_alternatives)

    def test_initialize_data_opens_template_successfully(self):
        instance = self.generator_class(self.supplier)
        instance._initialize_data()
        self.assertTrue(instance.template_sheet)

    def test_get_spreadsheet_returns_spreadsheet_with_all_components(self):
        instance = self.generator_class(self.supplier)
        components = set(
            ["%s%s" % (x.manufacturer, x.mpn) for x in Component.objects.filter(project=self.supplier.project)]
        )
        self.assertTrue(components)

        workbook = instance.get_spreadsheet()
        workbook.seek(0)
        workbook = xlrd.open_workbook(file_contents=workbook.read(), formatting_info=True)
        sheet = workbook.sheet_by_index(0)

        for row in range(instance.first_component_row, sheet.nrows):
            manufacturer = ExcelUtils.cell_string_value(sheet, row, instance.component_column_mapping['manufacturer'])
            mpn = ExcelUtils.cell_string_value(sheet, row, instance.component_column_mapping['mpn'])
            components.discard("%s%s" % (manufacturer, mpn))

        self.assertFalse(components)






