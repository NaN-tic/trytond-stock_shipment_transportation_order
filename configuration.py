# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.model import fields
from trytond.pyson import Eval, Id
from trytond.pool import PoolMeta, Pool
from trytond.modules.stock.configuration import default_func

transportation_order_sequence_field = fields.Many2One(
    'ir.sequence', "Transportation Order Sequence", required=True,
    domain=[
        ('company', 'in',
            [Eval('context', {}).get('company', -1), None]),
        ('sequence_type', '=', Id('stock_shipment_transportation_order',
                'sequence_type_transportation_order')),
        ],
    help="Used to generate the number given to transportation orders.")


class Configuration(metaclass=PoolMeta):
    __name__ = 'stock.configuration'
    transportation_order_sequence = fields.MultiValue(
        transportation_order_sequence_field)

    @classmethod
    def multivalue_model(cls, field):
        if field == 'transportation_order_sequence':
            return Pool().get('stock.configuration.sequence')
        return super(Configuration, cls).multivalue_model(field)

    default_transportation_order_sequence = \
        default_func('transportation_order_sequence')


class ConfigurationSequence(metaclass=PoolMeta):
    __name__ = 'stock.configuration.sequence'
    transportation_order_sequence = transportation_order_sequence_field

    @classmethod
    def default_transportation_order_sequence(cls):
        pool = Pool()
        ModelData = pool.get('ir.model.data')
        try:
            return ModelData.get_id('stock_shipment_transportation_order',
                'sequence_transportation_order')
        except KeyError:
            return None
