from django.test import TestCase
from npi.models import *
from npi.product_api.api import FarnellAPI
from unittest.mock import patch


class MockResponse(object):
    status_code = 200
    json_response = None

    def json(self, **kwargs):
        if not self.json_response:
            raise ValueError('Mock Error')
        return self.json_response

    def __str__(self):
        return "Response %s " % self.status_code

    @classmethod
    def mock_patch_request_get(cls):
        def mock_request(url):
            return cls()
        return mock_request


class TestFarnellAPI(TestCase):
    fixtures = ['npi/fixtures/npi.json']

    class MockFarnellSuccessResponse(MockResponse):
        json_response = {
            'manufacturerPartNumberSearchReturn': {
                'numberOfResults': 2,
                'products': [
                    {
                        'countryOfOrigin': 'FR', 'translatedMinimumOrderQuality': 1,
                        'displayName': 'EOZ - 09.03201.02 - SWITCH, SPST-CO, 0.5A, 12V, PCB, RED',
                        'prices': [
                            {'to': 49, 'from': 1, 'cost': 1.01},
                            {'to': 99, 'from': 50, 'cost': 0.961},
                            {'to': 499, 'from': 100, 'cost': 0.912},
                            {'to': 999, 'from': 500, 'cost': 0.808},
                            {'to': 1000000000, 'from': 1000, 'cost': 0.708}
                        ],
                        'vendorId': '73751',
                        'image': {'baseName': '/42724587.jpg', 'vrntPath': 'farnell/'},
                        'stock': {
                            'level': 17701,
                            'leastLeadTime': 70,
                            'nominatedWarehouseDetails': None,
                            'shipsFromMultipleWarehouses': True,
                            'breakdown': [
                                {'lead': 0, 'region': 'US', 'inv': 0, 'warehouse': 'P1'},
                                {'lead': 0, 'region': 'Liege', 'inv': 5649, 'warehouse': 'LG1'},
                                {'lead': 70, 'region': 'UK', 'inv': 12052, 'warehouse': 'GB1'}
                            ],
                            'regionalBreakdown': [
                                {'level': 5649, 'status': 1, 'shipsFromMultipleWarehouses': True, 'warehouse': 'Liege',
                                 'leastLeadTime': 0},
                                {'level': 0, 'status': 0, 'shipsFromMultipleWarehouses': True, 'warehouse': 'US',
                                 'leastLeadTime': 0},
                                {'level': 12052, 'status': 1, 'shipsFromMultipleWarehouses': True, 'warehouse': 'UK',
                                 'leastLeadTime': 70}
                            ],
                            'status': 1
                        },
                        'comingSoon': False,
                        'unitOfMeasure': 'EACH',
                        'inv': 17701,
                        'brandName': 'EOZ',
                        'isSpecialOrder': False,
                        'datasheets': [{'url': 'http://www.farnell.com/datasheets/2010029.pdf', 'type': 'T',
                                        'description': 'Technical Data Sheet'}],
                        'reeling': False,
                        'attributes': [
                            {'attributeLabel': ' Contact Configuration', 'attributeValue': 'SPDT'},
                            {'attributeLabel': ' Switch Operation', 'attributeValue': 'On'},
                            {'attributeLabel': ' Switch Mounting', 'attributeValue': 'Through Hole'},
                            {'attributeLabel': ' Product Range', 'attributeValue': '1K2 Series'},
                            {'attributeLabel': ' Contact Current Max', 'attributeUnit': 'mA', 'attributeValue': '500'},
                            {'attributeLabel': ' Contact Voltage AC Max', 'attributeValue': '-'},
                            {'attributeLabel': ' Contact Voltage DC Max', 'attributeUnit': 'V', 'attributeValue': '24'},
                            {'attributeLabel': ' Orientation',
                             'attributeUnit': '-pole change-over PCB Slide Switch with maintained action.</span></div><div class="features-and-benefits-list"><ul class="features-and-benefits-list-list"><li class="features-and-benefits-list-item">SPST Contact Configuration</li><li class="features-and-benefits-list-item">Plastic Red Flush Slider</li><li class="features-and-benefits-list-item">Gold-plated Contact</li></ul></div><div class="features-and-benefits-applications"><ul class="features-and-benefits-value"><li class="features-and-benefits-list-item">Industrial</li></ul></div></div>',
                             'attributeValue': 'Vertical<!--FANDB--><div class="features-and-benefits-container"><div class="features-and-benefits-description"><span class="features-benefits-value">The 09.03201.02 is a 1'}
                        ],
                        'sku': '1608080',
                        'isAwaitingRelease': False,
                        'vendorName': 'EOZ',
                        'discountReason': 0,
                        'vatHandlingCode': 'SLST',
                        'brandId': '1010745',
                        'productStatus': 'defaultStatus',
                        'rohsStatusCode': 'YES',
                        'commodityClassCode': '081036000',
                        'translatedManufacturerPartNumber': '09.03201.02',
                        'id': 'pf_UK1_1608080_0',
                        'packSize': 1,
                        'releaseStatusCode': -1
                    },
                    {
                        'countryOfOrigin': 'FR',
                        'translatedMinimumOrderQuality': 1,
                        'displayName': 'EAO - 09.03201.02 - SLIDE SWITCH, SPDT-CO, 0.5A, 24VDC',
                        'prices': [
                            {'to': 24, 'from': 1, 'cost': 2.99},
                            {'to': 49, 'from': 25, 'cost': 1.68},
                            {'to': 249, 'from': 50, 'cost': 1.49},
                            {'to': 499, 'from': 250, 'cost': 1.25},
                            {'to': 1000000000, 'from': 500, 'cost': 1.12}
                        ],
                        'vendorId': '80133',
                        'image': {'baseName': '/2787231-40.jpg', 'vrntPath': 'farnell/'},
                        'stock': {
                            'level': 611,
                            'leastLeadTime': 35,
                            'nominatedWarehouseDetails': None,
                            'shipsFromMultipleWarehouses': True,
                            'breakdown': [
                                {'lead': 0, 'region': 'Liege', 'inv': 225, 'warehouse': 'LG1'},
                                {'lead': 35, 'region': 'UK', 'inv': 386, 'warehouse': 'GB1'}
                            ],
                            'regionalBreakdown': [
                                {'level': 225, 'status': 1, 'shipsFromMultipleWarehouses': True, 'warehouse': 'Liege',
                                 'leastLeadTime': 0},
                                {'level': 386, 'status': 1, 'shipsFromMultipleWarehouses': True, 'warehouse': 'UK',
                                 'leastLeadTime': 35}
                            ],
                            'status': 1
                        },
                        'comingSoon': False,
                        'unitOfMeasure': 'EACH',
                        'inv': 611,
                        'brandName': 'EAO',
                        'isSpecialOrder': False,
                        'datasheets': [
                            {
                                'url': 'http://www.farnell.com/datasheets/2010029.pdf',
                                'type': 'T',
                                'description': 'Technical Data Sheet'
                            }
                        ],
                        'reeling': False,
                        'attributes': [
                            {'attributeLabel': ' Contact Configuration', 'attributeValue': 'SPDT-CO'},
                            {'attributeLabel': ' Switch Operation', 'attributeValue': 'On-On'},
                            {'attributeLabel': ' Switch Mounting', 'attributeValue': 'Through Hole'},
                            {'attributeLabel': ' Product Range', 'attributeValue': '1K2 Series'},
                            {'attributeLabel': ' Contact Current Max', 'attributeUnit': 'mA', 'attributeValue': '500'},
                            {'attributeLabel': ' Contact Voltage AC Max', 'attributeValue': '-'},
                            {'attributeLabel': ' Contact Voltage DC Max', 'attributeUnit': 'V', 'attributeValue': '24'},
                            {'attributeLabel': ' Orientation', 'attributeValue': 'Vertical'},
                            {'attributeLabel': ' SVHC',
                             'attributeUnit': ')<!--FANDB--><div class="features-and-benefits-container"></div>',
                             'attributeValue': 'No SVHC (07-Jul-2017'}
                        ],
                        'sku': '2787231',
                        'isAwaitingRelease': False,
                        'vendorName': 'EAO',
                        'discountReason': 0,
                        'vatHandlingCode': 'SLST',
                        'brandId': '1000296',
                        'productStatus': 'defaultStatus',
                        'rohsStatusCode': 'YES',
                        'commodityClassCode': '081036000',
                        'translatedManufacturerPartNumber': '09.03201.02',
                        'id': 'pf_UK1_2787231_0',
                        'packSize': 1,
                        'releaseStatusCode': -1
                    }
                ]
            }
        }

    class MockFarnellNotFoundResponse(MockResponse):
        json_response = {
            'Fault': {
                'Code': {'Value': 'soapenv:Receiver'}, 'Reason': {'Text': {'lang': 'en-US'}},
                'Detail': {
                    'searchException': {
                        'exceptionString': 'Could Not Query for the Keyword',
                        'exceptionCode': '200003'
                    }
                }
            }
        }

    class MockFarnellRateLimitExceeded(MockResponse):
        status_code = 403
        json_response = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project_supplier = ProjectSupplier.objects.first()

        FarnellAPI.RATE_LIMIT = 64

    def setUp(self):
        self.project_supplier.api_state = 'ready'
        self.project_supplier.save()
        self.api = FarnellAPI(project_supplier=self.project_supplier)

    # def test_valid_response_no_results(self):
    #     self.assertTrue(self.api._valid_response(self.MockFarnellNotFoundResponse()))

    def test_parse_response_data_contains_correct_keys(self):
        expected_keys = [
            'product_code', 'description', 'manufacturer', 'mpn', 'uom_id',
            'uom_name', 'moq', 'order_multiples', 'current_stock', 'leadtime'
        ]
        products = self.api._parse_response(self.MockFarnellSuccessResponse())
        self.assertTrue(len(products))
        for product in products:
            for key in expected_keys:
                self.assertTrue(product.get(key))

    def test_parse_response_no_results(self):
        parsed_response = self.api._parse_response(self.MockFarnellNotFoundResponse())
        self.assertEqual([], parsed_response)

    def test_parse_response_moq(self):
        response = self.MockFarnellSuccessResponse()
        for product in response.json_response['manufacturerPartNumberSearchReturn']['products']:
            product['prices'] = [
                {'from': 150, 'to': 300, 'cost': 1.15},
                {'from': 301, 'to': 10000, 'cost': 1},
            ]

        parsed_response = self.api._parse_response(response)
        for product in parsed_response:
            self.assertEqual(product['moq'], 150)

    def test_parse_response_uom_id_found(self):
        pass

    def test_parse_response_uom_id_not_found(self):
        pass

    def test_parse_response_ignore_reel(self):
        pass

    @patch('npi.product_api.api.requests.get', MockFarnellSuccessResponse.mock_patch_request_get())
    def test_add_response(self):
        self.api.update_supplier_info()

    @patch('npi.product_api.api.requests.get', MockFarnellRateLimitExceeded.mock_patch_request_get())
    def test_failed_searches(self):
        self.api.update_supplier_info()
        self.assertTrue(self.api._failed_searches)


    # @patch('npi.product_api.api.requests.get', mock_request_get)
    # def test_get_json_data_retry_after_403(self):
    #     components = list(Component.objects.filter(project=self.project)[:5])
    #     component = components[0]
    #     component.mpn = self.MPN_403
    #     component.save()
    #     self.api.get_data(components=components)
    #
    # @patch('npi.product_api.api.requests.get', mock_request_get)
    # def test_get_json_data_retry_after_500_with_json(self):
    #     components = list(Component.objects.filter(project=self.project)[:5])
    #     component = components[0]
    #     component.mpn = self.MPN_JSON_500
    #     component.save()
    #     self.api.get_data(components=components)
    #
    # @patch('npi.product_api.api.requests.get', mock_request_get)
    # def test_get_json_data_server_down(self):
    #     components = list(Component.objects.filter(project=self.project)[:5])
    #     component = components[0]
    #     component.mpn = self.MPN_SERVER_FAILURE
    #     component.save()
    #     with self.assertRaises(ValueError):
    #         self.api.get_data(components=components)


    # def test_farnell_get_request_url(self):
    #     result = 'https://api.element14.com/catalog/products?term=manuPartNum:C0603C104K5RACTU&storeInfo.id=uk.farnel' \
    #              'l.com&resultsSettings.offset=0&resultsSettings.numberOfResults=1&resultsSettings.refinements.filt' \
    #              'ers=&resultsSettings.responseGroup=large&callInfo.responseDataFormat=JSON&callInfo.apiKey=%s' % \
    #              FarnellApiData.API_KEY
    #     self.assertEqual(result, FarnellApiData.get_request_url('C0603C104K5RACTU'))
    #
    # def test_save_records(self):
    #     data = [{
    #         'component': Component.objects.get(mpn='C0603C104K5RACTU'),
    #         'mpn': 'C0603C104K5RACTU',
    #         'manufacturer': 'manuf1',
    #         'uom': FarnellApiData.uom_conversion.get('TC', 'TC'),
    #         'description': 'product_description',
    #         'product_code': 'MC0603B104K500CT',
    #         'order_multiples': '1',
    #         'current_stock': '432',
    #         'leadtime': '41',
    #         'prices': [{'break': '1', 'cost': '0.293', 'limit': '10'}, {'break': '11', 'cost': '0.214', 'limit': '200'}]
    #     }]
    #     records = FarnellApiData.save_records(data, self.project)
    #     print(records[0])
