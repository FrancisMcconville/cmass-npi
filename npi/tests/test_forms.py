from django.test import TestCase
from django.forms import ValidationError
from npi.forms import SupplierInformationUploadForm, CreateProjectForm, ExportSupplierInformationToOpenErpForm, BomUploadForm
from npi.forms import SpreadsheetParser, ExportBomToOpenErpForm
from npi.models import Project, ProjectSupplier, Component, QuoteQuantity, SupplierComponent
from metrics.models import ProductUom
from django.core.files.uploadedfile import SimpleUploadedFile


# class TestSpreadsheetParser(TestCase):
#     fixtures = ['metrics/fixtures/metrics.erp.yaml', 'npi/fixtures/npi.supplier_upload_to_complete.json']
#     multi_db = True
#
#     spreadsheet_directory = 'npi/tests/spreadsheets/project/'
#     spreadsheet_invalid_format = 'invalid_format.ods'
#     spreadsheet_no_parents_sheet = 'no_parents_sheet.xls'
#     spreadsheet_no_components_sheet = 'no_components_sheet.xls'
#     spreadsheet_invalid_parent_headers = 'invalid_parent_headers.xls'
#     spreadsheet_invalid_components_headers = 'invalid_component_headers.xls'
#     spreadsheet_test_data = 'test_data.xls'
#
#     class TestSpreadsheetParserChild(SpreadsheetParser):
#         WORKBOOK_PARENT_SHEET = 'Parents'
#         WORKBOOK_COMPONENTS_SHEET = 'Components'
#         sheet_details = {
#             WORKBOOK_PARENT_SHEET: {'header_row': 5, 'headers': ['parent', 'description', 'uom', 'product quantity']},
#             WORKBOOK_COMPONENTS_SHEET: {'header_row': 0, 'headers': ['parent', 'designators', 'manufacturer', 'mpn']}
#         }
#
#     @classmethod
#     def get_spreadsheet(cls, spreadsheet):
#         return SimpleUploadedFile(
#             'testing_spreadsheet.xml',
#             open('%s%s' % (cls.spreadsheet_directory, spreadsheet), 'rb').read()
#         )
#
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         cls.spreadsheet_parser = cls.TestSpreadsheetParserChild()
#
#     def tearDown(self):
#         self.spreadsheet_parser.spreadsheet_validation_errors = {}
#
#     def test_raise_spreadsheet_validation_error_without_errors(self):
#         pass
#
#     def test_raise_spreadsheet_validation_error_with_errors(self):
#         pass
#
#     def test_raise_spreadsheet_validation_error_with_error_title(self):
#         pass
#
#     def test_validate_column_required_adds_error_when_no_value(self):
#         pass
#
#     def test_validate_column_required_when_valid(self):
#         pass
#
#     def test_validate_uom_when_uom_is_invalid(self):
#         pass
#
#     def test_validate_uom_when_valid(self):
#         pass
#
#     def test_validate_quantity_no_value(self):
#         pass
#
#     def test_validate_quantity_non_numeric_value(self):
#         pass
#
#     def test_validate_quantity_valid_value(self):
#         pass


# class TestSupplierInformationUploadFormStateComplete(TestCase):
#     fixtures = ['metrics/fixtures/metrics.erp.yaml', 'npi/fixtures/npi.supplier_upload_to_complete.json']
#     multi_db = True
#
#     def setUp(self):
#         super().setUpClass()
#         self.project = Project.objects.filter(name='CM00100').first()
#         self.form = SupplierInformationUploadForm(project=self.project)
#
#     def test_save_project_supplier_info_state_rfq_when_pending_uploads(self):
#         spreadsheet = open('npi/tests/spreadsheets/TEST_CM00100_Digi-Key_RFQ.xls', 'rb')
#         spreadsheet = SimpleUploadedFile('testing_spreadsheet.xml', spreadsheet.read())
#         farnell = ProjectSupplier.objects.filter(supplier_name='Farnell UK').first()
#         farnell.uploaded = False
#         farnell.save()
#         self.form.project_supplier = ProjectSupplier.objects.filter(supplier_name='Digi-Key').first()
#         self.form.cleaned_data = {'spreadsheet': spreadsheet}
#         self.form.clean_spreadsheet()
#         self.form.save()
#         self.assertEqual(self.project.supplier_info_state, 'rfq')
#
#     def test_save_project_supplier_info_state_complete_when_all_uploads_complete(self):
#         spreadsheet = open('npi/tests/spreadsheets/TEST_CM00100_Digi-Key_RFQ.xls', 'rb')
#         spreadsheet = SimpleUploadedFile('testing_spreadsheet.xml', spreadsheet.read())
#         farnell = ProjectSupplier.objects.filter(supplier_name='Farnell UK').first()
#         farnell.uploaded = True
#         farnell.save()
#         self.form.project_supplier = ProjectSupplier.objects.filter(supplier_name='Digi-Key').first()
#         self.form.cleaned_data = {'spreadsheet': spreadsheet}
#         self.form.clean_spreadsheet()
#         self.form.save()
#         self.assertEqual(Project.objects.filter(name=self.project.name).first().supplier_info_state, 'complete')


# class TestSupplierInformationUploadForm(TestCase):
#     fixtures = ['metrics/fixtures/metrics.erp.yaml', 'npi/fixtures/npi.json']
#     multi_db = True
#
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         cls.project = Project.objects.all().first()
#         cls.project_supplier = ProjectSupplier.objects.filter(project=cls.project).first()
#
#         spreadsheet = open('npi/tests/spreadsheets/TEST_CM00100_Digi-Key_RFQ.xls', 'rb')
#         cls.spreadsheet = SimpleUploadedFile('testing_spreadsheet.xml', spreadsheet.read())
#         cls.form = SupplierInformationUploadForm(project=cls.project, data={}, files={'spreadsheet': cls.spreadsheet})
#
#     def tearDown(self):
#         self.form.SPREADSHEET_ERRORS = []
#         self.form.SPREADSHEET_LINE_ERRORS = {}
#         self.form.parsed_data = []
#
#     def test_spreadsheet_parse_data(self):
#         self.parsed_data = self.form.parse_spreadsheet_data(self.spreadsheet)
#
#     # def test_spreadsheet_add_line_number(self):
#     #     error_1 = "ERROR 1"
#     #     error_2 = "ERROR 2"
#     #
#     #     self.form.spreadsheet_add_line_error(1, error_1)
#     #     self.assertEqual([error_1], self.form.SPREADSHEET_LINE_ERRORS[1])
#     #
#     #     self.form.spreadsheet_add_line_error(2, error_1)
#     #     self.form.spreadsheet_add_line_error(2, error_2)
#     #     self.assertEqual([error_1, error_2], self.form.SPREADSHEET_LINE_ERRORS[2])
#     #
#     #     self.form.spreadsheet_add_line_error(3, error_1)
#     #     self.form.spreadsheet_add_line_error(3, error_1)
#     #     self.assertEqual([error_1, error_1], self.form.SPREADSHEET_LINE_ERRORS[3])
#
#     def test_clean_spreadsheet_raises_validation_error_when_spreadsheet_line_errors(self):
#         from django.forms import ValidationError
#         self.form.SPREADSHEET_LINE_ERRORS = {1: ['Error on line 1']}
#         self.form.cleaned_data = {'spreadsheet': self.spreadsheet}
#         with self.assertRaises(ValidationError):
#             self.form.clean_spreadsheet()
#
#     def test_spreadsheet_clean_customer_mpn_manufacturer_unrelated_manufacturer_invalid(self):
#         data = [{'customer_manufacturer': '', 'customer_mpn': 'test'}]
#         self.form.spreadsheet_clean_customer_mpn_manufacturer(data)
#         expected_error_message = \
#             "Component with Manufacturer '%(manufacturer)s' and MPN '%(mpn)s' is not part of " \
#             "the customers BOM for %(project)s" % {
#                 'mpn': data[0]['customer_mpn'],
#                 'manufacturer': data[0]['customer_manufacturer'],
#                 'project': self.form.project
#             }
#         self.assertIn(0, self.form.SPREADSHEET_LINE_ERRORS)
#         self.assertIn(expected_error_message, self.form.SPREADSHEET_LINE_ERRORS[0])
#
#     def test_spreadsheet_clean_customer_mpn_manufacturer_unrelated_mpn_invalid(self):
#         data = [{'customer_manufacturer': 'test', 'customer_mpn': ''}]
#         self.form.spreadsheet_clean_customer_mpn_manufacturer(data)
#         expected_error_message = \
#             "Component with Manufacturer '%(manufacturer)s' and MPN '%(mpn)s' is not part of " \
#             "the customers BOM for %(project)s" % {
#                 'mpn': data[0]['customer_mpn'],
#                 'manufacturer': data[0]['customer_manufacturer'],
#                 'project': self.form.project
#             }
#         self.assertIn(0, self.form.SPREADSHEET_LINE_ERRORS)
#         self.assertIn(expected_error_message, self.form.SPREADSHEET_LINE_ERRORS[0])
#
#     def test_spreadsheet_clean_customer_mpn_manufacturer_valid_mpn_updates_data(self):
#         component = Component(
#             project=self.project,
#             mpn='TEST_MPN',
#             manufacturer="TEST_MANUFACTURER",
#             uom_id=1,
#             description='TEST'
#         )
#         component.save()
#         data = [{'customer_manufacturer': component.manufacturer, 'customer_mpn': component.mpn}]
#         self.form.spreadsheet_clean_customer_mpn_manufacturer(data)
#         self.assertIn('component', data[0])
#         self.assertEqual(data[0]['component'], component)
#
#     def test_spreadsheet_clean_product_optional_when_row_blank(self):
#         false_row = {}
#         for attribute in self.form.WORKBOOK_COLUMN_MAPPING:
#             false_row[attribute] = ''
#         data = [false_row]
#         self.form.spreadsheet_clean_product(data)
#         self.assertNotIn(0, self.form.SPREADSHEET_LINE_ERRORS)
#
#     def test_spreadsheet_clean_product_required_when_row_not_blank(self):
#         false_row = {}
#         for attribute in self.form.WORKBOOK_COLUMN_MAPPING:
#             false_row[attribute] = 'TEST'
#         false_row['product'] = ''
#         data = [false_row]
#         self.form.spreadsheet_clean_product(data)
#         expected_error_message = "Product is required unless all other columns in this row are blank"
#         self.assertIn(expected_error_message, self.form.SPREADSHEET_LINE_ERRORS[0])
#
#     def test_spreadsheet_clean_product_unique(self):
#         test_product = {'product': 'TEST'}
#         data = [test_product, test_product]
#         self.form.spreadsheet_clean_product(data)
#         expected_error_message = "Product %(product)s is a duplicate of line %(line)s" % {
#             'product': data[1]['product'], 'line': 1  # Line 1 rather than 0 as errors must be human readable
#         }
#         self.assertIn(1, self.form.SPREADSHEET_LINE_ERRORS)
#         self.assertIn(expected_error_message, self.form.SPREADSHEET_LINE_ERRORS[1])
#
#     def test_spreadsheet_clean_description_required_when_product_provided(self):
#         self.form.spreadsheet_clean_description([{'product': 'TEST', 'description': ''}])
#         self.assertIn(0, self.form.SPREADSHEET_LINE_ERRORS)
#         self.assertIn("Description is required", self.form.SPREADSHEET_LINE_ERRORS[0])
#
#     def test_spreadsheet_clean_description_optional_when_product_not_provided(self):
#         self.form.spreadsheet_clean_description([{'product': '', 'description': ''}])
#         self.assertNotIn(0, self.form.SPREADSHEET_LINE_ERRORS)
#
#     def test_spreadsheet_clean_supplier_manufacturer_required_if_manufacturer(self):
#         self.form.spreadsheet_clean_supplier_manufacturer([{'manufacturer': '', 'mpn': 'test'}])
#         expected_error_message = "Manufacturer required"
#         self.assertIn(0, self.form.SPREADSHEET_LINE_ERRORS)
#         self.assertIn(expected_error_message, self.form.SPREADSHEET_LINE_ERRORS[0])
#
#     def test_spreadsheet_clean_supplier_mpn_required_if_manufacturer(self):
#         self.form.spreadsheet_clean_supplier_mpn([{'manufacturer': 'test', 'mpn': ''}])
#         expected_error_message = "MPN required"
#         self.assertIn(0, self.form.SPREADSHEET_LINE_ERRORS)
#         self.assertIn(expected_error_message, self.form.SPREADSHEET_LINE_ERRORS[0])
#
#     def test_spreadsheet_clean_supplier_mpn_manufacturer_combo_unique(self):
#         test_mpn_manufacturer_combo = {'manufacturer': 'TEST_MANUFACTURER', 'mpn': 'TEST_MPN'}
#         data = [test_mpn_manufacturer_combo, test_mpn_manufacturer_combo]
#         self.form.spreadsheet_clean_supplier_mpn(data)
#         expected_error_message = "Supplier Manufacturer / MPN is a duplicate of line %(line)s" % {'line': 1}
#         self.assertIn(1, self.form.SPREADSHEET_LINE_ERRORS)
#         self.assertIn(expected_error_message, self.form.SPREADSHEET_LINE_ERRORS[1])
#
#     def test_spreadsheet_clean_uom_required_when_product_provided(self):
#         data = [{'product': 'TEST', 'uom': ''}]
#         self.form.spreadsheet_clean_uom(data)
#         expected_error_message = "UOM required"
#         self.assertIn(0, self.form.SPREADSHEET_LINE_ERRORS)
#         self.assertIn(expected_error_message, self.form.SPREADSHEET_LINE_ERRORS[0])
#
#     def test_spreadsheet_clean_uom_optional_when_product_not_provided(self):
#         data = [{'product': '', 'uom': ''}]
#         self.form.spreadsheet_clean_uom(data)
#         self.assertNotIn(0, self.form.SPREADSHEET_LINE_ERRORS)
#
#     def test_spreadsheet_clean_uom_invalid_when_not_on_openerp(self):
#         data = [{'product': 'TEST', 'uom': '####'}]
#         self.form.spreadsheet_clean_uom(data)
#         expected_error_message = "UOM '%s' Not on OpenERP" % data[0]['uom']
#         self.assertIn(0, self.form.SPREADSHEET_LINE_ERRORS)
#         self.assertIn(expected_error_message, self.form.SPREADSHEET_LINE_ERRORS[0])
#
#     def test_spreadsheet_clean_uom_valid_adds_uom_id_to_data(self):
#         uom = ProductUom.objects.all().first()
#         data = [{'product': 'TEST', 'uom': uom.name}]
#         self.form.spreadsheet_clean_uom(data)
#         self.assertNotIn(0, self.form.SPREADSHEET_LINE_ERRORS)
#         self.assertEqual(data[0]['uom_id'], uom.id)
#
#     def test_spreadsheet_clean_uom_invalid_when_not_same_family_as_project_product_component_uom_id(self):
#         # TODO
#         pass
#
#     def test_spreadsheet_clean_prices_required_when_product_provided(self):
#         data = [{'product': 'TEST', 'prices': {}}, {'product': '', 'prices': {}}]
#         expected_error_message = "Prices are required"
#         self.form.spreadsheet_clean_prices(data)
#         self.assertNotIn(1, self.form.SPREADSHEET_LINE_ERRORS)
#         self.assertIn(0, self.form.SPREADSHEET_LINE_ERRORS)
#         self.assertIn(expected_error_message, self.form.SPREADSHEET_LINE_ERRORS[0])
#
#     def test_spreadsheet_clean_prices_invalid_if_not_numeric(self):
#         invalid_value = 'a'
#
#         prices = {'0': '0', '1': '0.1', '2': '0.2', '3': '0.3', '4': invalid_value}
#         data = [{'product': 'TEST', 'prices': prices}]
#         expected_error_message = "Prices %(prices)s contains non-numeric value '%(value)s'" % {
#             'prices': prices.values(), 'value': invalid_value
#         }
#
#         self.form.spreadsheet_clean_prices(data)
#         self.assertIn(0, self.form.SPREADSHEET_LINE_ERRORS)
#         self.assertIn(expected_error_message, self.form.SPREADSHEET_LINE_ERRORS[0])
#
#     def test_spreadsheet_clean_moq(self):
#         bad_moq = 'abc'
#         data = [
#             {'product': '', 'moq': ''},
#             {'product': 'TEST', 'moq': '111'},
#             {'product': 'TEST', 'moq': bad_moq},
#             {'product': 'TEST', 'moq': ''}
#         ]
#         self.form.spreadsheet_clean_moq(data)
#         self.assertNotIn(0, self.form.SPREADSHEET_LINE_ERRORS)
#         self.assertNotIn(1, self.form.SPREADSHEET_LINE_ERRORS)
#         self.assertIn(2, self.form.SPREADSHEET_LINE_ERRORS)  # MOQ must be numeric
#         self.assertIn(3, self.form.SPREADSHEET_LINE_ERRORS)  # MOQ is required
#
#     def test_spreadsheet_clean_order_multiples(self):
#         non_numeric_value = '12a'
#         data = [
#             {'product': 'TEST', 'order_multiples': non_numeric_value},
#             {'product': 'TEST', 'order_multiples': ''},
#             {'product': '', 'order_multiples': ''},
#             {'product': 'TEST', 'order_multiples': '1'},
#         ]
#         self.form.spreadsheet_clean_order_multiples(data)
#         self.assertNotIn(2, self.form.SPREADSHEET_LINE_ERRORS)
#         self.assertNotIn(3, self.form.SPREADSHEET_LINE_ERRORS)
#         self.assertIn(0, self.form.SPREADSHEET_LINE_ERRORS)  # MOQ must be numeric
#         self.assertIn(1, self.form.SPREADSHEET_LINE_ERRORS)  # MOQ is required
#
#     # def test_spreadsheet_clean_current_stock_numeric_value_valid(self):
#     #     value = '123.122'
#     #     data = [{'current_stock': value}]
#     #     self.form.spreadsheet_clean_current_stock(data)
#     #     self.assertNotIn(0, self.form.SPREADSHEET_LINE_ERRORS)
#
#     # def test_spreadsheet_clean_current_stock_null_value_valid(self):
#     #     value = ''
#     #     data = [{'current_stock': value}]
#     #     self.form.spreadsheet_clean_current_stock(data)
#     #     self.assertNotIn(0, self.form.SPREADSHEET_LINE_ERRORS)
#
#     # def test_spreadsheet_clean_current_stock_non_numeric_value_invalid(self):
#     #     value = 'asdasd'
#     #     data = [{'current_stock': value}]
#     #     self.form.spreadsheet_clean_current_stock(data)
#     #     self.assertIn(0, self.form.SPREADSHEET_LINE_ERRORS)
#
#     def test_spreadsheet_clean_leadtime_numeric_value(self):
#         value = ' 123.12'
#         data = [{'leadtime': value}]
#         self.form.spreadsheet_clean_leadtime(data)
#         self.assertNotIn(0, self.form.SPREADSHEET_LINE_ERRORS)
#
#     def test_spreadsheet_clean_leadtime_non_numeric_value_invalid(self):
#         value = ' abcd'
#         data = [{'leadtime': value}]
#         self.form.spreadsheet_clean_leadtime(data)
#         self.assertIn(0, self.form.SPREADSHEET_LINE_ERRORS)
#
#     def test_spreadsheet_clean_leadtime_null_value_valid(self):
#         value = ''
#         data = [{'leadtime': value}]
#         self.form.spreadsheet_clean_leadtime(data)
#         self.assertNotIn(0, self.form.SPREADSHEET_LINE_ERRORS)
#
#     def test_validate_optional_numeric_value_null_value(self):
#         column = 'test'
#         data = [{column: ''}]
#         self.form._validate_optional_numeric_value(data, column, 'Test')
#         self.assertNotIn(0, self.form.SPREADSHEET_LINE_ERRORS)
#
#     def test_validate_optional_numeric_value_numeric_value(self):
#         column = 'test'
#         data = [{column: '123.123 '}]
#         self.form._validate_optional_numeric_value(data, column, 'Test')
#         self.assertNotIn(0, self.form.SPREADSHEET_LINE_ERRORS)
#
#     def test_validate_optional_numeric_value_non_numeric_value(self):
#         column = 'test'
#         data = [{column: 'abc '}]
#         self.form._validate_optional_numeric_value(data, column, 'Test')
#         self.assertIn(0, self.form.SPREADSHEET_LINE_ERRORS)
#
#     def test_save(self):
#         self.form.is_valid()
#         self.form.project_supplier = self.project_supplier
#         created_records = self.form.save()
#         self.assertIsNotNone(created_records)
#         self.assertEqual(self.form.project_supplier.uploaded, True)


# class TestProjectForm(TestCase):
#     fixtures = ['metrics/fixtures/metrics.erp.yaml', 'npi/fixtures/npi.json']
#     multi_db = True
#
#     spreadsheet_directory = 'npi/tests/spreadsheets/project/'
#     spreadsheet_invalid_format = 'invalid_format.ods'
#     spreadsheet_no_parents_sheet = 'no_parents_sheet.xls'
#     spreadsheet_no_components_sheet = 'no_components_sheet.xls'
#     spreadsheet_invalid_parent_headers = 'invalid_parent_headers.xls'
#     spreadsheet_invalid_components_headers = 'invalid_component_headers.xls'
#     spreadsheet_test_data = 'test_data.xls'
#     form_class = CreateProjectForm
#
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         cls.form = CreateProjectForm(
#             data={'web_pricing': 'yes'}, files={'spreadsheet': cls.get_spreadsheet(cls.spreadsheet_test_data)}
#         )
#
#     def setUp(self):
#         super().setUp()
#         self.form.load_workbook(self.get_spreadsheet(self.spreadsheet_test_data))
#
#     def tearDown(self):
#         self.form.spreadsheet_validation_errors = {}
#
#     @classmethod
#     def get_spreadsheet(cls, spreadsheet):
#         return SimpleUploadedFile(
#             'testing_spreadsheet.xml',
#             open('%s%s' % (cls.spreadsheet_directory, spreadsheet), 'rb').read()
#         )
#
#     def test_load_workbook_invalid_file_format(self):
#         with self.assertRaisesRegexp(ValidationError, 'not supported'):
#             self.form.load_workbook(self.get_spreadsheet(self.spreadsheet_invalid_format))
#
#     def test_load_workbook_no_parents_sheet(self):
#         with self.assertRaisesRegexp(ValidationError, '%s Sheet missing' % self.form.WORKBOOK_PARENT_SHEET):
#             self.form.load_workbook(self.get_spreadsheet(self.spreadsheet_no_parents_sheet))
#
#     def test_load_workbook_no_components_sheet(self):
#         with self.assertRaisesRegexp(ValidationError, '%s Sheet missing' % self.form.WORKBOOK_COMPONENTS_SHEET):
#             self.form.load_workbook(self.get_spreadsheet(self.spreadsheet_no_components_sheet))
#
#     def test_load_workbook_invalid_parents_headers(self):
#         with self.assertRaisesRegexp(ValidationError, 'Parents headers invalid'):
#             self.form.load_workbook(self.get_spreadsheet(self.spreadsheet_invalid_parent_headers))
#
#     def test_load_workbook_invalid_components_headers(self):
#         with self.assertRaisesRegexp(ValidationError, 'Components headers invalid'):
#             self.form.load_workbook(self.get_spreadsheet(self.spreadsheet_invalid_components_headers))
#
#     def test_load_workbook_valid(self):
#         self.form.load_workbook(self.get_spreadsheet(self.spreadsheet_test_data))
#
#     def test_validate_quotation_quantities_too_many_quantities(self):
#         self.form.NPI_PROJECT_MAX_QUOTATION_QUANTITY = 5
#         self.form.parsed_data['quotation_quantities'] = '1,2,3,4,5,6'
#         self.form.validate_quotation_quantities()
#         self.assertIn(1, self.form.spreadsheet_validation_errors)
#         self.assertRegexpMatches(self.form.spreadsheet_validation_errors[1][0], 'Too many Quotation Quantities' )
#
#     def test_validate_quotation_quantities_non_numeric(self):
#         self.form.NPI_PROJECT_MAX_QUOTATION_QUANTITY = 5
#         self.form.parsed_data['quotation_quantities'] = '1,2,3,a,5'
#         self.form.validate_quotation_quantities()
#         self.assertIn(1, self.form.spreadsheet_validation_errors)
#         self.assertRegexpMatches(self.form.spreadsheet_validation_errors[1][0], "contains non-numeric")
#
#     def test_validate_quotation_quantities_required(self):
#         self.form.parsed_data['quotation_quantities'] = ""
#         self.form.validate_quotation_quantities()
#         self.assertIn(1, self.form.spreadsheet_validation_errors)
#         self.assertRegexpMatches(self.form.spreadsheet_validation_errors[1][0], "Quotation Quantities not provided")
#
#     def test_validate_quotation_quantities_valid(self):
#         """must set form.spreadsheet_quotation_quantities when valid"""
#         self.form.NPI_PROJECT_MAX_QUOTATION_QUANTITY = 5
#         self.form.parsed_data['quotation_quantities'] = "1,2,3,4,5"
#         self.form.validate_quotation_quantities()
#         self.assertEquals(self.form.spreadsheet_validation_errors, {})
#
#     def test_validate_parent_procure_method_invalid(self):
#         parents_data = self.form.parsed_data[self.form.WORKBOOK_PARENT_SHEET]
#         invalid_procure_method = 'buy_to_order'
#         test_data = parents_data[0]
#         test_data['procure method'] = invalid_procure_method
#         self.form.parsed_data[self.form.WORKBOOK_PARENT_SHEET] = [test_data]
#
#         with self.assertRaisesRegexp(ValidationError, "Procure Method '%s'" % invalid_procure_method):
#             self.form.clean_workbook_parents()
#
#     def test_validate_parent_procure_method_empty(self):
#         self.form.parsed_data[self.form.WORKBOOK_PARENT_SHEET] = [{'procure method': ''}]
#         self.form.validate_parent_procure_method()
#         self.assertNotIn(0, self.form.spreadsheet_validation_errors)
#
#     def test_validate_hscomcode_less_than_10(self):
#         invalid_data = '001234556'
#         self.form.parsed_data[self.form.WORKBOOK_PARENT_SHEET] = [{'hscomcode': invalid_data}]
#         self.form.validate_hscomcode()
#         self.assertIn(0, self.form.spreadsheet_validation_errors)
#         self.assertIn("Hscomcode '%s' must be 10 digits" % invalid_data, self.form.spreadsheet_validation_errors[0])
#
#     def test_validate_hscomcode_more_than_10(self):
#         invalid_data = '001234556789012'
#         self.form.parsed_data[self.form.WORKBOOK_PARENT_SHEET] = [{'hscomcode': invalid_data}]
#         self.form.validate_hscomcode()
#         self.assertIn(0, self.form.spreadsheet_validation_errors)
#         self.assertIn("Hscomcode '%s' must be 10 digits" % invalid_data, self.form.spreadsheet_validation_errors[0])
#
#     def test_validate_hscomcode_non_numeric(self):
#         invalid_data = '123456789a'
#         self.form.parsed_data[self.form.WORKBOOK_PARENT_SHEET] = [{'hscomcode': invalid_data}]
#         self.form.validate_hscomcode()
#         self.assertIn(0, self.form.spreadsheet_validation_errors)
#         self.assertIn("Hscomcode '%s' must be 10 digits" % invalid_data, self.form.spreadsheet_validation_errors[0])
#
#     def test_validate_hscomcode_empty(self):
#         data = ''
#         self.form.parsed_data[self.form.WORKBOOK_PARENT_SHEET] = [{'hscomcode': data}]
#         self.form.validate_hscomcode()
#         self.assertEquals(self.form.spreadsheet_validation_errors, {})
#
#     def test_validate_hscomcode_valid(self):
#         valid_data = '1234567890'
#         self.form.parsed_data[self.form.WORKBOOK_PARENT_SHEET] = [{'hscomcode': valid_data}]
#         self.assertEquals(self.form.spreadsheet_validation_errors, {})
#
#
#
#     #
#     # def test_validate_components_parent(self):
#     #     """Component parents must exist in parsed data to be valid"""
#     #     valid_parent = 'test_parent'
#     #     invalid_parent = 'invalid_parent'
#     #     self.form.spreadsheet_parsed_data = {valid_parent}
#     #
#     #     test_data = [{'parent': valid_parent}, {'parent': invalid_parent}, {'parent': ''}]
#     #
#     #     self.form.validate_components_parent(test_data)
#     #     self.assertNotIn(1, self.form.spreadsheet_validation_errors)
#     #     self.assertIn(2, self.form.spreadsheet_validation_errors)
#     #     self.assertIn(
#     #         "Parent '%(parent)s' is not defined in %(sheet)s sheet" % {
#     #             'parent': invalid_parent, 'sheet': self.form.WORKBOOK_PARENT_SHEET
#     #         },
#     #         self.form.spreadsheet_validation_errors[2]
#     #     )
#     #     self.assertIn(3, self.form.spreadsheet_validation_errors)
#     #     self.assertIn("Parent is required", self.form.spreadsheet_validation_errors[3])
#     #
#     # def test_validate_components_uom(self):
#     #     """UoM must exist on OpenERP. On Returning, valid rows will have uom_id key added"""
#     #     valid_uom_record = ProductUom.objects.first()
#     #     invalid_uom = 'invalid_uom'
#     #
#     #     data = [{'uom': valid_uom_record.name}, {'uom': invalid_uom}, {'uom': ''}]
#     #     self.form.validate_components_uom(data)
#     #
#     #     expected_missing_openerp_message = "UOM '%s' Doesn't exist on OpenERP" % invalid_uom
#     #     self.assertNotIn(1, self.form.spreadsheet_validation_errors)
#     #     self.assertIn('uom_id', data[0])
#     #     self.assertIn(2, self.form.spreadsheet_validation_errors)
#     #     self.assertIn(expected_missing_openerp_message, self.form.spreadsheet_validation_errors[2])
#     #     self.assertIn(3, self.form.spreadsheet_validation_errors)
#     #     self.assertIn("UOM is required", self.form.spreadsheet_validation_errors[3])
#     #
#     # def test_validate_components_qty(self):
#     #     invalid_qty = 'abc'
#     #     data = [{'qty': '1'}, {'qty': ''}, {'qty': invalid_qty}]
#     #     expected_invalid_qty_error_message = "Quantity '%s' is not a number" % invalid_qty
#     #     self.form.validate_components_qty(data)
#     #     self.assertNotIn(1, self.form.spreadsheet_validation_errors)
#     #     self.assertIn(2, self.form.spreadsheet_validation_errors)
#     #     self.assertIn("Quantity is required", self.form.spreadsheet_validation_errors[2])
#     #     self.assertIn(3, self.form.spreadsheet_validation_errors)
#     #     self.assertIn(expected_invalid_qty_error_message, self.form.spreadsheet_validation_errors[3])
#     #
#     # def test_validate_column_required(self):
#     #     column = 'test'
#     #     data = [{column: ''}, {column: 'valid'}]
#     #     expected_error_message = '%s is required' % column
#     #     self.form.validate_column_required(data, column, expected_error_message)
#     #     self.assertIn(1, self.form.spreadsheet_validation_errors)
#     #     self.assertIn(expected_error_message, self.form.spreadsheet_validation_errors[1])
#     #     self.assertNotIn(2, self.form.spreadsheet_validation_errors)
#     #
#     # def test_validate_components_msl_optional(self):
#     #     data = [{'msl': ''}]
#     #     self.form.validate_components_msl(data)
#     #     self.assertNotIn(1, self.form.spreadsheet_validation_errors)
#     #
#     # def test_validate_components_between_1_and_6(self):
#     #     data = [{'msl': '1'}, {'msl': '6'}, {'msl': '0'}, {'msl': '-1'}, {'msl': '07'}]
#     #     self.form.validate_components_msl(data)
#     #     self.assertNotIn(1, self.form.spreadsheet_validation_errors)
#     #     self.assertNotIn(2, self.form.spreadsheet_validation_errors)
#     #     self.assertIn(3, self.form.spreadsheet_validation_errors)
#     #     self.assertIn(4, self.form.spreadsheet_validation_errors)
#     #     self.assertIn(5, self.form.spreadsheet_validation_errors)
#     #
#     # def test_validate_components_non_numeric(self):
#     #     data = [{'msl': 'abc'}]
#     #     self.form.validate_components_msl(data)
#     #     self.assertIn(1, self.form.spreadsheet_validation_errors)


class SpreadsheetLoader(object):
    spreadsheet_directory = 'static/npi/spreadsheets/'

    def get_spreadsheet(self, spreadsheet):
        return SimpleUploadedFile(
            'testing_spreadsheet.xml', open('%s%s' % (self.spreadsheet_directory, spreadsheet), 'rb').read()
        )


# class TestExportSupplierInformationToOpenErpForm(TestCase):
#     fixtures = ['npi/fixtures/npi.supplier_info_complete.json']
#
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         cls.quotation_quantity = QuoteQuantity.objects.first()
#         cls.form = ExportSupplierInformationToOpenErpForm(
#             project=cls.quotation_quantity.project,
#             data={'quote_quantity': cls.quotation_quantity}
#         )
#
#     def test_save(self):
#         cleaned_data = {
#             'quote_quantity': self.quotation_quantity,
#             'username': 'stockadmin',
#             'password': 'c0MDFiMmQzODBhMT'
#         }
#         self.form.cleaned_data = cleaned_data
#         self.form.save()


# class TestBomUploadForm(SpreadsheetLoader, TestCase):
#     fixtures = ['metrics/fixtures/metrics.erp.yaml', 'npi/fixtures/npi.json']
#     multi_db = True
#
#     spreadsheet_directory = 'npi/tests/spreadsheets/bom_upload/'
#     spreadsheet_invalid_format = 'invalid_format.ods'
#     spreadsheet_no_parents_sheet = 'no_parents_sheet.xls'
#     spreadsheet_no_components_sheet = 'no_components_sheet.xls'
#     spreadsheet_invalid_parent_headers = 'invalid_parent_headers.xls'
#     spreadsheet_invalid_components_headers = 'invalid_component_headers.xls'
#     spreadsheet_test_data = 'test_data.xls'
#     form_class = BomUploadForm
#
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         cls.project = Project.objects.all().first()
#
#     def test_load_workbook_invalid_file_format(self):
#         form = self.form_class(self.project)
#         with self.assertRaisesRegexp(ValidationError, 'not supported'):
#             form.load_workbook(self.get_spreadsheet(self.spreadsheet_invalid_format))
#
#     def test_load_workbook_no_parents_sheet(self):
#         form = self.form_class(self.project)
#         with self.assertRaisesRegexp(ValidationError, '%s Sheet missing' % form.SPREADSHEET_PARENT_SHEET):
#             form.load_workbook(self.get_spreadsheet(self.spreadsheet_no_parents_sheet))
#
#     def test_load_workbook_no_components_sheet(self):
#         form = self.form_class(self.project)
#         with self.assertRaisesRegexp(ValidationError, '%s Sheet missing' % form.SPREADSHEET_COMPONENT_SHEET):
#             form.load_workbook(self.get_spreadsheet(self.spreadsheet_no_components_sheet))
#
#     def test_load_workbook_invalid_parents_headers(self):
#         form = self.form_class(self.project)
#         with self.assertRaisesRegexp(ValidationError, 'Parents headers invalid'):
#             form.load_workbook(self.get_spreadsheet(self.spreadsheet_invalid_parent_headers))
#
#     def test_load_workbook_invalid_components_headers(self):
#         form = self.form_class(self.project)
#         with self.assertRaisesRegexp(ValidationError, 'Components headers invalid'):
#             form.load_workbook(self.get_spreadsheet(self.spreadsheet_invalid_components_headers))


# class TestExportBomToOpenErpForm(TestCase):
#     fixtures = ['npi/fixtures/npi.supplier_info_and_xy_completed.json']
#
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         cls.form = ExportBomToOpenErpForm(Project.objects.get(pk=1))
#
#     def test_save(self):
#         self.form.cleaned_data = {'username': 'stockadmin', 'password': 'c0MDFiMmQzODBhMT'}
#         self.form.connect()
#         self.form.save()
