import requests
import threading
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from django.db import transaction
from METRICS_PROJECT.settings import API_MAX_WORKERS
from npi.models import QuoteQuantity, SupplierApiDailyUsage, SupplierComponent, SupplierProductQuote
from npi.models import SupplierApiFailedSearch
from queue import Queue
from zeep import Client

ApiThreadPool = ThreadPoolExecutor(max_workers=API_MAX_WORKERS)


class SupplierAPI(ABC, object):
    """
    request_queue is a static queue of all requests
    _worker thread pools request_queue, sleeps until requests are added
    instance updates request_queue with a request per component in instance.project_supplier.project.component_set
    _worker thread calls _api_request for each request in request_queue
    _api_request calls instance.add_response() for each response
    instance.add_response() decrements instance.pending_requests
    instance is woken when pending_requests = 0
    """
    PERIOD = 1
    SUPPLIER_ID = None
    API_KEY = ''
    DAILY_LIMIT = 0
    RATE_LIMIT = 0

    _request_count = 0
    _request_queue = Queue()
    _request_rate_limit_lock = None  # Semaphore(RATE_LIMIT) set by _request_worker
    _response_count = 0
    _worker_progress_mutex = threading.Lock()
    _worker_creation_lock = threading.Lock()
    _worker = None

    def __new__(cls, *args, **kwargs):
        cls._start_request_worker()
        return super().__new__(cls)

    def __init__(self, project_supplier, *args, **kwargs):
        self.project_supplier = project_supplier
        self._await_response = threading.Semaphore(0)  # Lock to sleep current thread while it waits for responses
        self._pending_requests = 0  # Number of requests on self.requests queue
        self._failed_searches = []
        self._parsed_data = {}
        super().__init__(*args, **kwargs)

    def __str__(self):
        return "%s: %s" % (self.project_supplier.project, self.project_supplier)

    @classmethod
    def _start_request_worker(cls):
        """Create a new worker thread if there isn't one already running"""
        with cls._worker_creation_lock:
            if not cls._worker:
                cls._worker = threading.Thread(target=cls._request_worker)
                cls._worker.daemon = True
                cls._worker.start()

    @classmethod
    def _progress_request_worker(cls):
        with cls._worker_progress_mutex:
            cls._response_count += 1
            if cls._request_queue.empty() and cls._request_count == cls._response_count:
                with cls._worker_creation_lock:
                    cls._response_count = 0
                    cls._request_count = 0
                    cls._worker = None
                    return

            if cls._response_count % cls.RATE_LIMIT == 0:
                time.sleep(cls.PERIOD)

                for x in range(0, cls.RATE_LIMIT):
                    cls._request_rate_limit_lock.release()

    @classmethod
    def _request_worker(cls):
        """pools request_queue for added requests"""
        cls._request_rate_limit_lock = threading.Semaphore(cls.RATE_LIMIT)
        while True:
            component, instance = cls._request_queue.get()
            with cls._worker_progress_mutex:
                cls._request_count += 1
            ApiThreadPool.submit(cls._request, component, instance)

    @classmethod
    def _request(cls, component, instance):
        """
        :param component: npi.models.Component
        :param instance: SupplierAPI instance to return the response to
        """
        cls._request_rate_limit_lock.acquire()
        response = cls._send_api_request(component)

        try:
            SupplierApiDailyUsage.inc(instance.project_supplier.supplier_id)
        except:
            pass

        if cls._valid_response(response, component, instance):
            response = cls._parse_response(response)
        else:
            response = []

        instance.add_response({component: response})
        cls._progress_request_worker()

    @classmethod
    @abstractmethod
    def _send_api_request(cls, component):
        pass

    @classmethod
    @abstractmethod
    def _valid_response(cls, response, component, instance):
        """
        Verify response data is valid
        :param response: result returned from request.get()
        :returns True if valid, else False
        """
        pass

    @classmethod
    @abstractmethod
    def _parse_response(cls, response):
        """
        :returns list(
            dict(
                product_code=string(),
                description=string(),
                manufacturer=string(),
                mpn=string(),
                uom_id=int(),
                uom_name=string(),
                moq=float(), # Minimum order quantity
                order_multiples=float(),
                leadtime=int(), # Number of days
                prices=list(
                    dict(
                        break=int() # price_range_start,
                        limit=int() # price_range_max,
                        cost=float()
                    )
                )
            )
        )
        """
        pass

    def _add_request(self, component):
        """Add request to request_queue"""
        self._pending_requests += 1
        self._request_queue.put((component, self))

    def add_failed_search(self, component):
        self._failed_searches.append(component)

    def _get_components(self, retry=False):
        """:returns list of npi.models.Component to be searched for"""
        if retry:
            return [x.component for x in self.project_supplier.failed_api_calls]
        return self.project_supplier.project.component_set.all()

    def _search(self, retry=False):
        """Adds components to request_queue and waits for response"""
        for component in self._get_components(retry):
            self._add_request(component)
        self._await_response.acquire()

    def _save_records(self):
        """Write self.parsed_data to database"""
        with transaction.atomic():
            SupplierApiFailedSearch.objects.filter(project_supplier=self.project_supplier).delete()
            quote_quantities = QuoteQuantity.objects.filter(project=self.project_supplier.project)

            for component, results in self._parsed_data.items():
                for product_details in results:
                    prices = product_details.pop('prices')
                    product_details.update({'component': component, 'project_supplier': self.project_supplier})
                    supplier_component, created = SupplierComponent.objects.get_or_create(**product_details)

                    for quantity in quote_quantities:
                        SupplierProductQuote.objects.get_or_create(
                            product=supplier_component,
                            quote_quantity=quantity,
                            price=self._get_price(prices, quantity)
                        )

            state = 'finished'
            if self._failed_searches:
                state = 'finished_with_errors'
                for component in self._failed_searches:
                    SupplierApiFailedSearch.objects.create(project_supplier=self.project_supplier, component=component)
            self.project_supplier.api_workflow_push(state)

    @staticmethod
    def _get_price(price_list, quantity):
        for price in sorted(price_list, key=lambda x: x['limit']):
            if quantity.quantity < price['limit']:
                return price['cost']

        # quantity is larger than all limits, use largest limit cost
        return max(price_list, key=lambda x: x['limit'])['cost']

    def update_supplier_info(self):
        """Search API for SupplierComponents and write results to database"""
        retry = self.project_supplier.api_state == 'finished_with_errors'
        self.project_supplier.api_workflow_push('pending')
        try:
            self._search(retry)
            self._save_records()
        except Exception as e:
            self.project_supplier.api_workflow_push('error')

    def add_response(self, response):
        """Receive response from request_worker"""
        self._pending_requests -= 1
        self._parsed_data.update(response)
        if self._pending_requests == 0:
            self._await_response.release()


class FarnellAPI(SupplierAPI):
    RATE_LIMIT = 2
    PERIOD = 1
    SUPPLIER_ID = 420
    API_KEY = 'gfa2g5wnnxjzs9uk9p94h49v'
    REQUEST_URL = \
        u'https://api.element14.com/catalog/products?' \
        u'term=manuPartNum:%s' \
        u'&storeInfo.id=uk.farnell.com' \
        u'&resultsSettings.offset=0' \
        u'&resultsSettings.numberOfResults=1' \
        u'&resultsSettings.refinements.filters=inStock' \
        u'&resultsSettings.responseGroup=large' \
        u'&callInfo.responseDataFormat=JSON' \
        u'&callInfo.apiKey=' + API_KEY

    uom_conversion = {
        'TC': {'id': 1, 'name': 'PCE'},
        'EACH': {'id': 1, 'name': 'PCE'},
        'TR': {'id': 1, 'name': 'PCE'},
        'REEL': {'id': 1, 'name': 'PCE'},
        'PACK': {'id': 1, 'name': 'PCE'}
    }

    @classmethod
    def _send_api_request(cls, component):
        try:
            return requests.get(cls.REQUEST_URL % component.mpn)
        except:
            return

    @classmethod
    def _valid_response(cls, response, component, instance):
        valid_error_codes = ['200001', '200002', '200003', '200004']
        try:
            json = response.json()
            if 'Fault' in json:
                detail = json['Fault'].get('Detail', {})
                exception = detail.get('searchException', {})
                error_code = exception.get('exceptionCode', None)

                if error_code not in valid_error_codes:
                    instance.add_failed_search(component)
                    return False

            return True
        except Exception:
            instance.add_failed_search(component)
            return False

    @classmethod
    def _parse_response(cls, response):
        data = response.json()
        result = data.get('manufacturerPartNumberSearchReturn', {})
        products = result.get('products', [])
        parsed_data = []
        for product in products:
            if product['reeling']:
                continue
            parsed_data.append({
                'product_code': product['sku'],
                'description': product['displayName'],
                'manufacturer': product['vendorName'],
                'mpn': product['translatedManufacturerPartNumber'],
                'uom_id': cls.uom_conversion[product['unitOfMeasure']]['id'],  # May fail
                'uom_name': cls.uom_conversion[product['unitOfMeasure']]['name'],
                'moq': min([price['from'] for price in product['prices']]),
                'order_multiples': product['translatedMinimumOrderQuality'],
                'current_stock': product['inv'],
                'leadtime': product['stock']['leastLeadTime'],
                'prices': [
                    {'break': price['from'], 'cost': price['cost'], 'limit': price['to']} for price in product['prices']
                ],
            })

        return parsed_data

    @staticmethod
    def _get_price(price_list, quantity):
        # Farnell partner pricing is always lowest price
        return min(price_list, key=lambda x: x['cost'])['cost']


# class MouserAPI(SupplierAPI):
#     API_KEY = '9f9a1bdd-5689-43a2-b922-9fa1ac5eb77c'
#     SUPPLIER_ID = 448
#     RATE_LIMIT = 2
#
#     def __new__(cls, *args, **kwargs):
#         cls._client = Client(wsdl='https://api.mouser.com/service/searchapi.asmx?wsdl')
#         cls._header = cls._client.get_element('ns0:MouserHeader')(AccountInfo=cls.API_KEY)
#         return super().__new__(cls, *args, **kwargs)
#
#     @classmethod
#     def _parse_response(cls, response):
#         return_data = []
#         parts = response.get('Parts')
#         parts = parts or {}
#
#         for product in parts.get('MouserPart', []):
#             return_data.append({
#                 'product_code': product['MouserPartNumber'],
#                 'description': product['Description'],
#                 'manufacturer': product['Manufacturer'],
#                 'mpn': product['ManufacturerPartNumber'],
#                 'uom_id': 1,
#                 'uom_name': 'PCE',
#                 'moq': product['Min'],
#                 'order_multiples': product['Mult'],
#                 'current_stock': None,
#                 'leadtime': product['LeadTime'],
#                 'prices': [
#                     {'break': price['from'], 'cost': price['cost'], 'limit': price['to']} for price in product['prices']
#                 ],
#             })
#         return return_data
#
#     @classmethod
#     def _api_send_request(cls, component):
#         return cls._client.service.SearchByPartNumber(
#             _soapheaders=[cls._header],
#             mouserPartNumber=component.mpn,
#             partSearchOptions=1
#         )
#
#     @classmethod
#     def _valid_response(cls, response):
#         return True
#
#     @staticmethod
#     def get_price(price_list, quantity):
#         for price in reversed(price_list):
#             if price['break'] <= quantity:
#                 return price['cost'][1:]


SUPPLIER_MAP = {
    420: FarnellAPI,
    # 448: MouserAPI
}

