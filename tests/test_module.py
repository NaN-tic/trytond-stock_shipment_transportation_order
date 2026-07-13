
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

import datetime
from decimal import Decimal

from trytond.modules.company.tests import CompanyTestMixin
from trytond.modules.company.tests import create_company, set_company
from trytond.pool import Pool
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.transaction import Transaction


class StockShipmentTransportationOrderTestCase(CompanyTestMixin, ModuleTestCase):
    'Test StockShipmentTransportationOrder module'
    module = 'stock_shipment_transportation_order'

    @with_transaction()
    def test_transportation_order_report_execute(self):
        pool = Pool()
        Carrier = pool.get('carrier')
        Party = pool.get('party.party')
        Product = pool.get('product.product')
        ProductTemplate = pool.get('product.template')
        TransportOrder = pool.get('stock.transportation_order')
        Report = pool.get('stock.transportation_order.jreport', type='report')
        Uom = pool.get('product.uom')

        company = create_company()
        with set_company(company):
            unit, = Uom.search([('name', '=', 'Unit')], limit=1)
            carrier_party, = Party.create([{
                        'name': 'MRW',
                        }])
            product_template, = ProductTemplate.create([{
                        'name': 'Carrier Service',
                        'type': 'service',
                        'default_uom': unit.id,
                        }])
            product, = Product.create([{
                        'template': product_template.id,
                        }])
            carrier, = Carrier.create([{
                        'party': carrier_party.id,
                        'carrier_product': product.id,
                        }])
            order, = TransportOrder.create([{
                        'company': company.id,
                        'carrier': carrier.id,
                        'order_date': datetime.date.today(),
                        }])

            ext, content, _, _ = Report.execute([order.id], {})
            self.assertEqual(ext, 'pdf')
            self.assertTrue(content)
            self.assertTrue(content.startswith(b'%PDF'))

    @with_transaction()
    def test_transportation_order_supplier_summary(self):
        pool = Pool()
        Carrier = pool.get('carrier')
        Location = pool.get('stock.location')
        Party = pool.get('party.party')
        Product = pool.get('product.product')
        ProductTemplate = pool.get('product.template')
        Move = pool.get('stock.move')
        ShipmentIn = pool.get('stock.shipment.in')
        TransportOrder = pool.get('stock.transportation_order')
        Uom = pool.get('product.uom')

        company = create_company()
        with set_company(company):
            unit, = Uom.search([('name', '=', 'Unit')], limit=1)
            carrier_party, = Party.create([{
                        'name': 'Carrier',
                        }])
            product_template, = ProductTemplate.create([{
                        'name': 'Carrier Service',
                        'type': 'service',
                        'default_uom': unit.id,
                        }])
            product, = Product.create([{
                        'template': product_template.id,
                        }])
            carrier, = Carrier.create([{
                        'party': carrier_party.id,
                        'carrier_product': product.id,
                        }])
            stock_template, = ProductTemplate.create([{
                        'name': 'Stock Product',
                        'type': 'goods',
                        'default_uom': unit.id,
                        }])
            stock_product, = Product.create([{
                        'template': stock_template.id,
                        }])
            supplier, = Party.create([{
                        'name': 'Supplier',
                        }])
            warehouse = self.create_warehouse(Location, company, '1')
            order, = TransportOrder.create([{
                        'carrier': carrier.id,
                        'company': company.id,
                        'order_date': datetime.date.today(),
                        }])
            shipment, = ShipmentIn.create([{
                        'company': company.id,
                        'supplier': supplier.id,
                        'warehouse': warehouse.id,
                        'warehouse_input': warehouse.input_location.id,
                        'warehouse_storage': warehouse.storage_location.id,
                        }])
            move, = Move.create([{
                        'company': company.id,
                        'from_location': shipment.supplier_location.id,
                        'to_location': warehouse.input_location.id,
                        'product': stock_product.id,
                        'unit': unit.id,
                        'quantity': 1,
                        'unit_price': Decimal('1'),
                        'currency': company.currency.id,
                        'shipment': 'stock.shipment.in,%s' % shipment.id,
                        'transportation_order': order.id,
                        }])

            order = TransportOrder(order.id)
            self.assertEqual(order.party_summary, supplier.rec_name)
            self.assertEqual(order.supplier_moves, (move,))

    @staticmethod
    def create_warehouse(Location, company, suffix):
        with Transaction().set_context({
                    'company': company.id,
                    'companies': [company.id],
                    }):
            storage = Location(
                name='Storage %s' % suffix,
                type='storage',
                code='STO%s' % suffix,
                )
            storage.save()
            warehouse = Location(
                name='Warehouse %s' % suffix,
                code='WH%s' % suffix,
                type='warehouse',
                input_location=storage,
                output_location=storage,
                storage_location=storage)
            warehouse.save()
            return warehouse


del ModuleTestCase
