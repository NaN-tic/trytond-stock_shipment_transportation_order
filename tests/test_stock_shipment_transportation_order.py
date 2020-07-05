# This file is part stock_shipment_transportation_order module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import unittest


from trytond.tests.test_tryton import ModuleTestCase
from trytond.tests.test_tryton import suite as test_suite


class TransportOrderTestCase(ModuleTestCase):
    'Test Stock Shipment Transportation Order module'
    module = 'stock_shipment_transportation_order'


def suite():
    suite = test_suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
            TransportOrderTestCase))
    return suite
