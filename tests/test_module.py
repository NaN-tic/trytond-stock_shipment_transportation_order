
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

import datetime

from trytond.modules.company.tests import CompanyTestMixin
from trytond.modules.company.tests import create_company, set_company
from trytond.pool import Pool
from trytond.tests.test_tryton import ModuleTestCase, with_transaction


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


del ModuleTestCase
