# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from decimal import Decimal
from trytond.model import ModelView, ModelSQL, fields, Workflow
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Eval
from trytond.transaction import Transaction
from trytond.modules.jasper_reports.jasper import JasperReport

_STATES = {
    'readonly': Eval('state') != 'draft',
}
_DEPENDS = ['state']


class TransportOrder(Workflow, ModelSQL, ModelView):
    'Transportation Order'
    __name__ = 'stock.transportation_order'
    _rec_name = 'number'

    number = fields.Char('Number', readonly=True)
    carrier = fields.Many2One('carrier', 'Carrier', required=True,
        states={
            'required': Eval('state') == 'done',
            'readonly': Eval('state') != 'draft',
        },
        depends=_DEPENDS)
    incoterm = fields.Many2One('incoterm', 'Incoterm',
        states={
            'required': Eval('state') == 'done',
            'readonly': Eval('state') != 'draft',
        },
        depends=_DEPENDS)
    order_date = fields.Date('Date',
        states={
            'required': Eval('state') == 'done',
            'readonly': Eval('state') != 'draft',
        },
        depends=_DEPENDS)
    company = fields.Many2One('company.company', 'Company', required=True)
    shipments_out = fields.One2Many('stock.shipment.out', 'transportation_order',
        'Customer Shipments', states=_STATES, depends=_DEPENDS)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ], 'State', required=True, readonly=True, select=True)
    total_packages = fields.Function(fields.Integer('Total of Packages'),
        'get_total_packages')
    total_weight = fields.Function(fields.Numeric('Total Weight', digits=(16, 4)),
        'get_total_weight')


    @classmethod
    def __setup__(cls):
        super(TransportOrder, cls).__setup__()
        cls._transitions |= set((
                ('draft', 'done'),
                ('done', 'draft'),
                ))
        cls._buttons.update({
                'draft': {
                    'readonly': Eval('state') != 'done',
                    'depends': ['state'],
                    },
                'done': {
                    'readonly': Eval('state') != 'draft',
                    'depends': ['state'],
                    },
                })

    @staticmethod
    def default_order_date():
        Date = Pool().get('ir.date')
        return Date.today()

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_state():
        return 'draft'

    @classmethod
    def set_number(cls, transportation_orders):
        'Fill the number field with the transportation orders sequence'
        pool = Pool()
        Config = pool.get('stock.configuration')

        config = Config(1)
        to_write = []
        for order in transportation_orders:
            if order.number or not config.transportation_order_sequence:
                continue
            number = config.transportation_order_sequence.get()
            to_write.extend(([order], {
                        'number': number,
                        }))
        if to_write:
            cls.write(*to_write)

    @classmethod
    @ModelView.button
    @Workflow.transition('done')
    def done(cls, transportation_orders):
        cls.set_number(transportation_orders)

    @classmethod
    @ModelView.button
    @Workflow.transition('draft')
    def draft(cls, transportation_orders):
        pass

    def get_total_weight(self, name):
        total = Decimal(0)
        for shipment in self.shipments_out:
            if not hasattr(shipment, 'weight_lines'):
                return
            if shipment.weight_lines:
                total += Decimal(shipment.weight_lines)
        return Decimal(total)

    def get_total_packages(self, name):
        packages = 0
        for shipment in self.shipments_out:
            if not hasattr(shipment, 'number_packages'):
                return
            if shipment.number_packages:
                packages += shipment.number_packages
        return packages


class StockShipmentOut(metaclass=PoolMeta):
    __name__ = 'stock.shipment.out'
    transportation_order = fields.Many2One('stock.transportation_order',
        'Transportation Order')

class TransportOrderReport(JasperReport):
    __name__ = 'stock.transportation_order.jreport'
