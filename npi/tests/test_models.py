from django.test import TestCase
from metrics.utils import copy_record
from npi.models import *
from metrics.models import ProductUomCateg
from unittest import mock


class TestProject(TestCase):
    fixtures = ['metrics/fixtures/metrics.erp.yaml', 'npi/fixtures/npi.json']
    multi_db = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = Project.objects.first()

    def test_supplier_info_actions_keys(self):
        expected_keys = ['create', 'export', 'edit', 'upload', 'clear', 'review', 'alternatives']
        self.assertEquals(sorted(list(self.project.supplier_info_actions.keys())), sorted(expected_keys))

    def test_supplier_info_actions_values(self):
        for action_value in self.project.supplier_info_actions.values():
            self.assertIn('url', action_value)
            self.assertIn('text', action_value)
            self.assertIn('button-class', action_value)

    def test_supplier_info_actions_available_contains_action_for_each_state(self):
        for state in self.project.SUPPLIER_INFO_STATES:
            self.assertIn(state, self.project.SUPPLIER_INFO_STATE_ACTIONS)

    def test_supplier_info_actions_available(self):
        expected_actions = [
            self.project.supplier_info_actions[action]
            for action in self.project.SUPPLIER_INFO_STATE_ACTIONS[self.project.supplier_info_state]
        ]
        self.assertEquals(self.project.supplier_info_actions_available(), expected_actions)

    def test_supplier_info_action_buttons(self):
        from django.utils.safestring import SafeText
        self.assertEquals(type(self.project.supplier_info_action_buttons()), type(SafeText()))

    def test_save_new_record(self):
        new_project = Project(web_pricing=True, customer_id=1, customer_name="Test")
        new_project.save()
        self.assertTrue(new_project.create_date)
        self.assertTrue(new_project.name)

    def test_next_name(self):
        last_project = Project.objects.all().order_by('name').last()
        number = int(last_project.name[2:])
        next_number = number + 1
        expected_name = "CM%06d" % next_number
        self.assertEquals(self.project._next_name(), expected_name)

    def test_first_next_name(self):
        Project.objects.all().delete()
        self.assertEquals(Project._next_name(), 'CM001030')

    def test_quotation_quantites(self):
        QuoteQuantity.objects.filter(project=self.project).delete()
        quantites = [1, 2, 3, 4, 5]
        expected_output = ''
        for quantity in quantites:
            QuoteQuantity(project=self.project, quantity=quantity).save()
            expected_output += '%g, ' % quantity
        expected_output = expected_output[:-2]
        self.assertEquals(self.project.quotation_quantities, expected_output)

    def _complete_project(self):
        supplier = ProjectSupplier.objects.filter(project=self.project).first()
        quotation_quantities = QuoteQuantity.objects.filter(project=self.project)
        for component in Component.objects.filter(project=self.project):
            product = SupplierComponent(
                component=component,
                project_supplier=supplier,
                product_code="test",
                description=component.description,
                manufacturer=component.manufacturer,
                mpn=component.mpn,
                uom_id=component.uom_id,
                uom_name=component.uom_name,
                moq=1,
                order_multiples=1,
            )
            product.save()

            for quote_quantity in quotation_quantities:
                SupplierProductQuote(
                    product=product,
                    quote_quantity=quote_quantity,
                    price=1
                ).save()

    def test_supplier_info_ready_to_complete_true_when_all_products_quoted(self):
        self._complete_project()
        self.assertEquals(self.project.supplier_info_ready_to_complete, True)

    def test_supplier_info_ready_to_complete_false_when_products_without_quotes(self):
        self._complete_project()
        for product in SupplierComponent.objects.filter(component__project=self.project):
            product.state = 'reject'
            product.save()
        self.assertEquals(self.project.supplier_info_ready_to_complete, False)

    def test_supplier_info_workflow_push_raise_exception_when_invalid(self):
        self.project.supplier_info_state = 'draft'
        with self.assertRaises(WorkflowInvalidActionException):
            self.project._supplier_info_workflow_push('uploaded')

    def test_supplier_info_workflow_push_updates_state(self):
        self.project.supplier_info_state = 'draft'
        self.project._supplier_info_workflow_push('rfq')
        self.assertEquals(self.project.supplier_info_state, 'rfq')

    def test_supplier_info_workflow_push_to_existing_state(self):
        self.project.supplier_info_state = 'draft'
        self.assertTrue(self.project._supplier_info_workflow_push('draft'))
        self.assertEquals(self.project.supplier_info_state, 'draft')

    def test_wkf_supplier_info_draft(self):
        self.project.supplier_info_state = 'rfq'
        self.project.wkf_supplier_info_draft()
        self.assertEquals(self.project.supplier_info_state, 'draft')

    def test_wkf_supplier_info_rfq(self):
        self.project.supplier_info_state = 'draft'
        self.project.wkf_supplier_info_rfq()
        self.assertEquals(self.project.supplier_info_state, 'rfq')

    def test_wkf_supplier_info_complete_when_ready_to_complete(self):
        self._complete_project()
        self.project.supplier_info_state = 'rfq'
        self.project.wkf_supplier_info_complete()
        self.assertEquals(self.project.supplier_info_state, 'complete')

    def test_wkf_supplier_info_complete_when_not_ready_to_complete(self):
        self._complete_project()
        for product in SupplierComponent.objects.filter(component__project=self.project):
            product.state = 'reject'
            product.save()
        self.project.supplier_info_state = 'rfq'
        self.project.wkf_supplier_info_complete()
        self.assertEquals(self.project.supplier_info_state, 'rfq')

    def test_wkf_supplier_info_complete_already_completed_but_not_ready_to_complete(self):
        self._complete_project()
        for product in SupplierComponent.objects.filter(component__project=self.project):
            product.state = 'reject'
            product.save()
        self.project.supplier_info_state = 'complete'
        self.project.wkf_supplier_info_complete()
        self.assertEquals(self.project.supplier_info_state, 'rfq')

    def test_wkf_supplier_info_complete_already_completed_ready_to_complete(self):
        self._complete_project()
        self.project.supplier_info_state = 'complete'
        self.project.wkf_supplier_info_complete()
        self.assertEquals(self.project.supplier_info_state, 'complete')

    def test_wkf_supplier_info_uploaded(self):
        self.project.supplier_info_state = 'complete'
        self.project.wkf_supplier_info_uploaded()
        self.assertEquals(self.project.supplier_info_state, 'uploaded')

    def test_supplier_info_state_string(self):
        self.assertEquals(
            self.project.supplier_info_state_string,
            self.project.SUPPLIER_INFO_STATES[self.project.supplier_info_state]
        )

    def test_component_mpn_vs_supplier_order_code_missmatch(self):
        cursor = mock.MagicMock(
            description=(('count',),),
            **{'fetchall.return_value': [('100',)],}

        )
        # with mock.patch('django.db.backends.utils.CursorWrapper', mock.MagicMock(side_effect=lambda x, y: cursor)):
        print(self.project.component_mpn_vs_supplier_order_code_missmatch())


class TestComponent(TestCase):
    fixtures = ['npi/fixtures/npi.supplier_info_complete.json']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.component = Component.objects.first()
        cls.quote_quantity = QuoteQuantity.objects.filter(project=cls.component.project).first()

    def test_cheapest_supplier_quote(self):
        component = Component.objects.first()
        quote_quantity = QuoteQuantity.objects.filter(project=component.project).first()
        supplier_quote = SupplierProductQuote.objects.filter(
            product__component=component, quote_quantity=quote_quantity
        ).order_by('price').first()

        # Subtract 1 from current cheapest record's price to make a new cheapest record
        cheapest_supplier_quote = supplier_quote
        cheapest_supplier_quote.pk = None
        cheapest_supplier_quote.price -= 1
        cheapest_supplier_quote.save()
        self.assertEquals(component.cheapest_supplier_quote(quote_quantity), cheapest_supplier_quote)

    def test_cheapest_supplier_quote_moq(self):
        # self.supplier_component_1 will have cheapest price with
        self.supplier_component_1 = SupplierComponent.objects.filter(component=self.component).first()
        self.supplier_component_2 = self.supplier_component_1
        self.supplier_component_2.pk = None
        self.supplier_component_2.save()
        # TODO

    def test_default_quote(self):
        self.assertEquals(
            self.component.default_quote(self.quote_quantity),
            self.component.cheapest_supplier_quote(self.quote_quantity)
        )

    def test_selected_quote(self):
        quotes = SupplierProductQuote.objects.filter(
            product__component=self.component,
            quote_quantity=self.quote_quantity
        )
        for quote in quotes:
            quote.selected = False

        selected_quote = quotes.first()
        selected_quote.selected = True
        self.assertEquals(self.component.selected_quote(self.quote_quantity), selected_quote)

        selected_quote.selected = False
        self.assertEquals(
            self.component.selected_quote(self.quote_quantity),
            self.component.default_quote(self.quote_quantity)
        )

    def test_selected_quote_price(self):
        selected_quote = self.component.selected_quote(self.quote_quantity)
        expected_value = selected_quote.price * selected_quote.order_multiple_quantity_price
        self.assertEquals(self.component.selected_quote_price(self.quote_quantity), expected_value)

    def test_selected_quote_price_no_quotes(self):
        QuoteQuantity.objects.filter(project__component=self.component).delete()
        with self.assertRaises(ValueError):
            self.component.selected_quote_price(self.quote_quantity)

    def test_number_of_suppliers_quoted(self):
        expected_length = len(SupplierComponent.objects.filter(component=self.component))
        self.assertEquals(self.component.number_of_suppliers_quoted, expected_length)

    def test_awaiting_alternative_approval_when_true(self):
        supplier_component = SupplierComponent.objects.first()
        supplier_component.state = 'pending'
        supplier_component.save()
        self.assertEquals(supplier_component.component.awaiting_alternative_approval, True)

    def test_awaiting_alternative_approval_when_all_supplier_components_normal_state(self):
        supplier_component = SupplierComponent.objects.first()
        for component in SupplierComponent.objects.filter(component=supplier_component.component):
            component.state = 'normal'
            component.save()
        self.assertEquals(supplier_component.component.awaiting_alternative_approval, False)

    def test_awaiting_alternative_approval_when_no_supplier_components(self):
        SupplierComponent.objects.filter(component=self.component).delete()
        self.assertEquals(self.component.awaiting_alternative_approval, False)

    def test_edit_selected_quote_returns_html_select_when_not_uploaded(self):
        self.component.project.supplier_info_state = 'rfq'
        self.component.project.save()
        result = self.component.edit_selected_quote(self.quote_quantity)
        self.assertIn('<select name="supplier_component"', result)

    def test_edit_selected_quote_returns_selected_supplier_component_string_when_uploaded(self):
        self.component.project.supplier_info_state = 'uploaded'
        self.component.project.save()
        expected_result = str(self.component.selected_quote(self.quote_quantity).product)
        self.assertEquals(self.component.edit_selected_quote(self.quote_quantity), expected_result)

    def test_cheapest_supplier_quote_moq_returns_correct_value(self):
        supplier_moq_quotes = SupplierProductQuote.objects.filter(
            product__in=SupplierComponent.active_components.filter(component=self.component),
            quote_quantity=self.quote_quantity
        )
        self.assertEquals(
            min(supplier_moq_quotes, key=lambda x: x.order_multiple_quantity_price),
            self.component.cheapest_supplier_quote_moq(self.quote_quantity)
        )

    def test_cheapest_supplier_quote_moq_returns_none_when_no_quotes(self):
        SupplierProductQuote.objects.all().delete()
        self.assertEquals(None, self.component.cheapest_supplier_quote_moq(self.quote_quantity))

    def test_to_str(self):
        self.assertEquals(str(self.component), "%s %s" % (self.component.manufacturer, self.component.mpn))


class TestSupplierProductQuote(TestCase):
    fixtures = ['metrics/fixtures/metrics.erp.yaml', 'npi/fixtures/npi.json']
    multi_db = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Uom Setup
        pieces_category = ProductUomCateg.objects.get_or_create(name='Pieces')[0]
        lengths_category = ProductUomCateg.objects.get_or_create(name='Length / Distance')[0]
        cls.pce_uom = ProductUom.objects.get_or_create(
            name='PCE', factor=1, category=pieces_category, rounding=1, uom_type='reference'
        )[0]
        cls.box200_uom = ProductUom.objects.get_or_create(
            name='Box200', factor=200, category=pieces_category, rounding=1, uom_type='bigger')[0]
        cls.box1000_uom = ProductUom.objects.get_or_create(
            name='Box1000', factor=1000, category=pieces_category, rounding=1, uom_type='bigger')[0]
        cls.m_uom = ProductUom.objects.get_or_create(
            name='m', factor=1, category=lengths_category, rounding=1, uom_type='reference'
        )[0]
        cls.mm_uom = ProductUom.objects.get_or_create(
            name='mm', factor=1000, category=lengths_category, rounding=0.010, uom_type='smaller'
        )[0]

        # Component setup. Quoting for 10 of Required quantity of 100 for first parent. Not used on any other parents
        cls.supplier_quote = SupplierProductQuote.objects.first()
        cls.component = cls.supplier_quote.product.component
        cls.parent_component = ParentComponent.objects.filter(component=cls.component).first()
        cls.parent_component.quantity = 100
        cls.parent_component.save()
        cls.parent_component.parent.quantity = 1
        cls.parent_component.parent.save()
        cls.supplier_quote.quote_quantity.quantity = 10
        cls.supplier_quote.quote_quantity.save()

        ParentComponent.objects.filter(
            component=cls.parent_component.component
        ).exclude(id=cls.parent_component.id).delete()

    def test_product_quantity_component_uom_smaller_than_supplier_uom(self):
        component = self.supplier_quote.product.component
        component.uom_id = self.mm_uom.id
        component.save()

        self.supplier_quote.product.uom_id = self.m_uom.id
        self.supplier_quote.save()

        # need 1000mm, supplier quote in m  = 1000/1000 = 1
        self.assertEquals(self.supplier_quote.product_quantity, 1)

    def test_product_quantity_component_uom_larger_than_supplier_uom(self):
        component = self.supplier_quote.product.component
        component.uom_id = self.box1000_uom.id
        component.save()

        self.supplier_quote.product.uom_id = self.box200_uom.id
        self.supplier_quote.save()

        # Need 1000 box1000s, supplier quote in box200, need 5000 box200s
        self.assertEquals(self.supplier_quote.product_quantity, 5000)

    def test_product_quantity_component_uom_equal_to_supplier_uom(self):
        self.supplier_quote.product.uom_id = self.pce_uom.id
        self.supplier_quote.save()

        component = self.supplier_quote.product.component
        component.uom_id = self.pce_uom.id
        component.save()

        self.assertEquals(self.supplier_quote.product_quantity, 1000)

    def test_product_order_multiple_quantity_round_quantity_up_to_multiple(self):
        # Multiple is greater than quantity, so must round up to the multiple
        order_multiple = self.supplier_quote.product_quantity + 0.1
        self.supplier_quote.product.order_multiples = order_multiple
        self.assertEquals(self.supplier_quote.product_order_multiple_quantity, order_multiple)

    def test_product_order_multiple_quantity_round_up_multiple_to_meet_quantity(self):
        # multiple is slightly lower than quantity, expected to have to buy two multiples
        order_multiple = self.supplier_quote.product_quantity - 0.1
        self.supplier_quote.product.order_multiples = order_multiple
        self.assertEquals(self.supplier_quote.product_order_multiple_quantity, order_multiple * 2)

    def test_product_order_multiple_quantity_quantity_equals_multiple_returns_quantity(self):
        # Multiple equal to quantity should return quantity
        self.supplier_quote.product.order_multiples = self.supplier_quote.product_quantity
        self.assertEquals(self.supplier_quote.product_order_multiple_quantity, self.supplier_quote.product_quantity)

    def test_product_order_multiple_quantity_negative_multiple_invalid(self):
        # Negative multiples are invalid
        self.supplier_quote.product.order_multiples = -1
        with self.assertRaises(ValueError):
            self.supplier_quote.product_order_multiple_quantity()

    def test_product_order_multiple_quantity_multiple_1_returns_quantity(self):
        # Multiple of 1 should just equal quantity
        self.supplier_quote.product.order_multiples = 1
        self.assertEquals(self.supplier_quote.product_order_multiple_quantity, self.supplier_quote.product_quantity)

    def test_product_order_multiple_quantity_multiple_0_returns_quantity(self):
        # Multiple of 0 should still work as a placeholder value for unknown multiples
        self.supplier_quote.product.order_multiples = 0
        self.assertEquals(self.supplier_quote.product_order_multiple_quantity, self.supplier_quote.product_quantity)

    def test_product_order_multiple_quantity_small_number(self):
        # Floats should calculate correctly
        float_multiple = 0.0000000101
        expected_output = ceil(self.supplier_quote.product_quantity/float_multiple) * float_multiple
        self.supplier_quote.product.order_multiples = float_multiple
        self.assertEquals(self.supplier_quote.product_order_multiple_quantity, expected_output)

    def test_order_multiple_quantity_price(self):
        expected_output = (self.supplier_quote.price * self.supplier_quote.product_order_multiple_quantity)
        expected_output /= self.supplier_quote.product_quantity
        self.assertEquals(self.supplier_quote.order_multiple_quantity_price, expected_output)

    def test_select(self):
        currently_selected_record = copy_record(self.supplier_quote)
        currently_selected_record.selected = True
        self.supplier_quote.select()
        currently_selected_record = SupplierProductQuote.objects.get(pk=currently_selected_record.pk)
        self.assertEquals(currently_selected_record.selected, False)
        self.assertEquals(self.supplier_quote.selected, True)

    def test_select_rejected_alternative(self):
        self.supplier_quote.product.state = 'reject'
        self.supplier_quote.product.alternative = True
        self.supplier_quote.product.save()
        with self.assertRaises(ValueError):
            self.supplier_quote.select()

    def test_select_disabled_supplier(self):
        self.supplier_quote.product.project_supplier.enabled = False
        self.supplier_quote.product.project_supplier.save()
        with self.assertRaises(ValueError):
            self.supplier_quote.select()

    def test_openerp_pricelist_partnerinfo_dictionary_return_empty_dict_when_no_suppliercomponent_quotes(self):
        record = SupplierComponent(
            component=Component.objects.first(),
            project_supplier=ProjectSupplier.objects.first(),
            product_code='TEST',
            description='TEST',
            manufacturer='TEST',
            mpn='TEST',
            uom_id=1,
            uom_name='TEST',
            moq=1,
            order_multiples=1,
            current_stock=1,
            leadtime=1
        )
        record.save()
        self.assertEquals({}, SupplierProductQuote.openerp_pricelist_partnerinfo_dictionary(record))

    def test_openerp_pricelist_partnerinfo_dictionar_with_quantity_1(self):
        component = Component.objects.first()
        quote_quantity_1 = QuoteQuantity.objects.get_or_create(project=component.project, quantity=1)[0]
        supplier_component = SupplierComponent.objects.filter(component=component).first()

        # Set parent quantity to 1
        parent = ParentComponent.objects.filter(component=component).first()
        Parent.objects.all().exclude(id=parent.id).delete()
        parent.quantity = 1
        parent.save()

        # Create quote for quantity 1
        quote = SupplierProductQuote(
            product=supplier_component,
            quote_quantity=quote_quantity_1,
            price=1,
            selected=True
        )
        quote.save()

        # 0 key only present when a record for min quantity 1 had to be inserted
        self.assertNotIn('0', SupplierProductQuote.openerp_pricelist_partnerinfo_dictionary(supplier_component))

    def test_openerp_pricelist_partnerinfo_dictionary_add_quantity_1_when_not_quote_for_quantity_1(self):
        component = Component.objects.first()

        # Deleting QuoteQuantity = 1 will cascade, deleting any SupplierProductQuote for quantity 1
        QuoteQuantity.objects.filter(project=component.project).filter(quantity=1).delete()

        result = SupplierProductQuote.openerp_pricelist_partnerinfo_dictionary(
            SupplierComponent.objects.filter(component=component).first()
        )

        self.assertIn('0', result)
        self.assertEquals(result['0']['min_quantity'], 1)

    def test_openerp_pricelist_partnerinfo_dictionary_quantity_1_price_is_highest_quote_price(self):
        component = Component.objects.first()

        # Deleting QuoteQuantity = 1 will cascade, deleting any SupplierProductQuote for quantity 1
        QuoteQuantity.objects.filter(project=component.project).filter(quantity=1).delete()

        supplier_component = SupplierComponent.objects.filter(component=component).first()
        max_price = SupplierProductQuote.objects.filter(product=supplier_component).order_by('-price').first().price

        result = SupplierProductQuote.openerp_pricelist_partnerinfo_dictionary(supplier_component)
        self.assertEquals(result['0']['price'], max_price)

    def test_to_str(self):
        expected_output = "%s: %s" % (self.supplier_quote.quote_quantity.quantity, self.supplier_quote.price)
        self.assertEquals(str(self.supplier_quote), expected_output)


class TestQuoteQuantity(TestCase):
    fixtures = ['npi/fixtures/npi.json', 'metrics/fixtures/metrics.erp.yaml']
    multi_db = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.record = QuoteQuantity.objects.first()

    def test_cost_total(self):
        expected_cost = 0
        for component in Component.objects.filter(project=self.record.project):
            expected_cost += component.selected_quote(self.record).order_multiple_total_price

        self.assertEquals(self.record.order_multiple_cost_total, expected_cost)

    def test_cost_each(self):
        total_cost = 0
        for component in Component.objects.filter(project=self.record.project):
            total_cost += component.selected_quote(self.record).order_multiple_total_price

        cost_each = total_cost / self.record.quantity
        self.assertEquals(self.record.order_multiple_cost_each, cost_each)

    def test_to_str(self):
        self.assertEquals(str(self.record), "%g" % self.record.quantity)

    def test_save_with_zero_quantity(self):
        with self.assertRaises(ValueError):
            QuoteQuantity(quantity=0, project=Project.objects.first()).save()

    def test_export_data_for_openerp_contains_all_components(self):
        components_ids = [component.id for component in Component.objects.filter(project=self.record.project)]
        result = self.record.export_data_for_openerp()['components']
        for component_id in components_ids:
            self.assertIn(str(component_id), result)

    def test_export_data_for_openerp_selected_supplierinfo_lowest_sequence(self):
        component = Component.objects.filter(project=self.record.project).first()

        result = self.record.export_data_for_openerp()
        sequences = []
        supplier_info = result['components'][str(component.id)]['supplier_info']

        for data in supplier_info.values():
            sequences.append(data['product_supplierinfo']['sequence'])

        min_sequence = min(sequences)
        selected_sequence = result['components'][str(component.id)]['supplier_info']\
            [str(component.selected_quote(self.record).product.id)]['product_supplierinfo']['sequence']

        self.assertEquals(sequences.count(min_sequence), 1)
        self.assertEquals(selected_sequence, min_sequence)


class TestParent(TestCase):
    fixtures = ['npi/fixtures/npi.json']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.record = Parent.objects.first()

    def test_to_str(self):
        self.assertEquals(str(self.record), self.record.name)


class TestSupplierComponent(TestCase):
    fixtures = ['npi/fixtures/npi.json']
    
    def setUp(self):
        self.supplier_component = SupplierComponent.objects.first()

    def test_openerp_product_supplierinfo_dictionary_contains_corret_keys(self):
        supplier_info = SupplierComponent.objects.first()
        result = SupplierComponent.openerp_product_supplierinfo_dictionary(supplier_info, 10)
        self.assertIn('product_supplierinfo', result[str(supplier_info.id)])
        self.assertIn('pricelist_partnerinfo', result[str(supplier_info.id)])

    def test_openerp_product_supplierinfo_sequence(self):
        supplier_info = SupplierComponent.objects.first()
        sequence = 50
        result = SupplierComponent.openerp_product_supplierinfo_dictionary(supplier_info, sequence)
        self.assertEquals(sequence, result[str(supplier_info.id)]['product_supplierinfo']['sequence'])

    def test_save_sets_active_to_false_when_mpn_ne_component__mpn(self):
        customer_mpn = 'CUSTOMER_MPN'
        customer_manufacturer = 'CUSTOMER_MANUFACTURER'
        self.supplier_component.component.mpn = customer_mpn
        self.supplier_component.component.manufacturer = customer_manufacturer
        self.supplier_component.component.save()
        self.supplier_component.mpn = "%s-TEST" % customer_mpn
        self.supplier_component.manufacturer = customer_manufacturer
        self.supplier_component.id = None
        self.supplier_component.save()
        self.assertEquals(self.supplier_component.state, 'pending')
        self.assertEquals(self.supplier_component.alternative, True)

    def test_save_sets_active_to_false_when_mpn_equals_component__mpn(self):
        customer_mpn = 'CUSTOMER_MPN'
        customer_manufacturer = 'CUSTOMER_MANUFACTURER'
        self.supplier_component.component.mpn = customer_mpn
        self.supplier_component.component.manufacturer = customer_manufacturer
        self.supplier_component.component.save()
        self.supplier_component.mpn = customer_mpn
        self.supplier_component.manufacturer = customer_manufacturer
        self.supplier_component.id = None
        self.supplier_component.save()
        self.assertEquals(self.supplier_component.state, 'normal')
        self.assertEquals(self.supplier_component.alternative, False)

    def test_save_sets_active_to_false_when_manufacturer_ne_component__manufacturer(self):
        customer_mpn = 'CUSTOMER_MPN'
        customer_manufacturer = 'CUSTOMER_MANUFACTURER'
        self.supplier_component.component.mpn = customer_mpn
        self.supplier_component.component.manufacturer = customer_manufacturer
        self.supplier_component.component.save()
        self.supplier_component.mpn = customer_mpn
        self.supplier_component.manufacturer = "%s-TEST" % customer_manufacturer
        self.supplier_component.id = None
        self.supplier_component.save()
        self.assertEquals(self.supplier_component.state, 'pending')
        self.assertEquals(self.supplier_component.alternative, True)

    def test_save_sets_active_to_true_when_manufacturer_equals_component__manufacturer(self):
        customer_mpn = 'CUSTOMER_MPN'
        customer_manufacturer = 'CUSTOMER_MANUFACTURER'
        self.supplier_component.component.mpn = customer_mpn
        self.supplier_component.component.manufacturer = customer_manufacturer
        self.supplier_component.component.save()
        self.supplier_component.mpn = customer_mpn
        self.supplier_component.manufacturer = customer_manufacturer
        self.supplier_component.id = None
        self.supplier_component.save()
        self.assertEquals(self.supplier_component.state, 'normal')
        self.assertEquals(self.supplier_component.alternative, False)

    def test_wkf_normal_from_pending(self):
        self.supplier_component.state = 'pending'
        self.supplier_component.wkf_normal()
        self.assertEquals(self.supplier_component.state, 'normal')

    def test_wkf_normal_from_rejected(self):
        self.supplier_component.state = 'reject'
        self.supplier_component.wkf_normal()
        self.assertEquals(self.supplier_component.state, 'normal')

    def test_wkf_rejected_from_pending(self):
        self.supplier_component.state = 'pending'
        self.supplier_component.wkf_rejected()
        self.assertEquals(self.supplier_component.state, 'reject')

    def test_wkf_rejected_from_normal(self):
        self.supplier_component.state = 'normal'
        self.supplier_component.wkf_rejected()
        self.assertEquals(self.supplier_component.state, 'reject')

    def test_wkf_pending_from_rejected(self):
        self.supplier_component.state = 'reject'
        self.supplier_component.wkf_pending()
        self.assertEquals(self.supplier_component.state, 'pending')

    def test_wkf_pending_from_normal(self):
        self.supplier_component.state = 'normal'
        self.supplier_component.wkf_pending()
        self.assertEquals(self.supplier_component.state, 'pending')


class TestProjectSupplier(TestCase):
    fixtures = ['npi/fixtures/npi.supplier_info_complete.json']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.record = ProjectSupplier.objects.first()

    def test_state_uploaded(self):
        self.record.uploaded = True
        self.record.save()
        self.assertEquals(self.record.state, 'Uploaded')

    def test_state_pending(self):
        self.record.uploaded = False
        self.record.save()
        self.assertEquals(self.record.state, 'Pending')

    def test_generate_rfq_spreadsheet(self):
        import xlrd
        file = self.record.generate_rfq_spreadsheet()
        file.seek(0)
        spreadsheet = xlrd.open_workbook(file_contents=file.read(), formatting_info=True)
        self.assertTrue(spreadsheet.sheet_by_index(0))


class TestBomParent(TestCase):
    fixtures = ['npi/fixtures/npi.supplier_info_and_xy_completed.json']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = Project.objects.get(pk=1)

    def test_export_bom_openerp(self):
        data = BomParent.export_bom_openerp(self.project)
        self.assertIn('bom_parents', data)
        self.assertIn('bom_child_parents', data)
        self.assertIn('bom_parents', data)


