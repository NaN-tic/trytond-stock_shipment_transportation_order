# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import configuration
from . import stock


def register():
    Pool.register(
        configuration.Configuration,
        configuration.ConfigurationSequence,
        stock.TransportOrder,
        stock.StockShipmentOut,
        module='stock_shipment_transportation_order', type_='model')
    Pool.register(
        stock.TransportOrderReport,
        module='stock_shipment_transportation_order', type_='report')
