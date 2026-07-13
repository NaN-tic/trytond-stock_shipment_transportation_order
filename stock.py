# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from decimal import Decimal
from dominate.tags import div, h1, header as header_tag, img, table, tbody, td, th, thead, tr
from dominate.util import raw
from trytond.model import ModelView, ModelSQL, fields, Workflow
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Eval
from trytond.transaction import Transaction
from trytond.modules.html_report.dominate_report import DominateReport
from trytond.modules.html_report.i18n import _

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
        })
    order_date = fields.Date('Date',
        states={
            'required': Eval('state') == 'done',
            'readonly': Eval('state') != 'draft',
        })
    company = fields.Many2One('company.company', 'Company', required=True)
    shipments_out = fields.One2Many('stock.shipment.out', 'transportation_order',
        'Customer Shipments', states=_STATES)
    supplier_moves = fields.One2Many('stock.move', 'transportation_order',
        'Supplier Moves', domain=[
            ('shipment', 'ilike', 'stock.shipment.in,%'),
            ], states=_STATES)
    party_summary = fields.Function(fields.Char('Party Summary'),
        'get_party_summary')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ], 'State', required=True, readonly=True)
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

    def get_rec_name(self, name):
        items = []
        if self.number:
            items.append(self.number)
        else:
            party_summary = self.get_party_summary(name)
            if party_summary:
                items.append(party_summary)
            if self.order_date:
                items.append(str(self.order_date))
        if not items:
            items.append('(%s)' % self.id)
        return ' '.join(items)

    def get_party_summary(self, name):
        parties = {
            shipment.customer.rec_name
            for shipment in self.shipments_out
            if shipment.customer
            }
        parties.update(
            move.shipment.supplier.rec_name
            for move in self.supplier_moves
            if move.shipment and move.shipment.supplier)
        return ', '.join(sorted(parties))

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


class StockMove(metaclass=PoolMeta):
    __name__ = 'stock.move'
    transportation_order = fields.Many2One('stock.transportation_order',
        'Transportation Order')


class TransportOrderReport(DominateReport):
    __name__ = 'stock.transportation_order.jreport'
    _single = True

    @classmethod
    def language(cls, records):
        return Transaction().language or 'en'

    @classmethod
    def _render_weight(cls, shipment):
        weight = shipment.raw.weight if hasattr(shipment.raw, 'weight') else None
        if weight not in (None, '', 0):
            return shipment.render.weight
        weight_lines = (shipment.raw.weight_lines
            if hasattr(shipment.raw, 'weight_lines') else None)
        if weight_lines not in (None, ''):
            return shipment.render.weight_lines
        return '0.00'

    @classmethod
    def header(cls, action, data, records):
        record, = records
        company = record.company
        header = div()
        with header:
            with header_tag(id='header'):
                with table():
                    with tr():
                        with td(style='width: 30%;'):
                            if company.render.logo:
                                img(cls='logo', src=company.render.logo)
                        with td():
                            h1(_('TRANSPORTATION ORDER'), cls='title')
                with table():
                    with tr():
                        td('%s:' % cls.label('stock.transportation_order', 'carrier'),
                            cls='thick no-wrap', style='width: 15%;')
                        td(record.carrier.party.render.name if record.raw.carrier else '',
                            style='width: 35%;')
                        td(_('Nº'), cls='thick no-wrap', style='width: 10%;')
                        td(record.render.number if record.raw.number else '',
                            style='width: 15%;')
                        td(_('DATE'), cls='thick no-wrap', style='width: 10%;')
                        td(record.render.order_date if record.raw.order_date else '',
                            style='width: 15%;')
        return header

    @classmethod
    def body(cls, action, data, records):
        record, = records
        if record.supplier_moves and not record.shipments_out:
            body = div()
            with body:
                lines_table = table()
                with lines_table:
                    with thead():
                        with tr(cls='table-header'):
                            th(_('Supplier'), cls='text-left')
                            th(_('Product'), cls='text-left')
                            th(_('Quantity'), cls='text-right')
                    with tbody():
                        for move in record.supplier_moves:
                            with tr():
                                td(move.shipment.supplier.render.rec_name
                                    if (move.raw.shipment
                                        and move.shipment.raw.supplier) else '')
                                td(move.product.render.rec_name
                                    if move.raw.product else '')
                                td(move.render.quantity, cls='text-right')
            return body

        show_packages = any(
            hasattr(shipment.raw, 'number_packages')
            for shipment in record.shipments_out)
        show_total_packages = (
            hasattr(record.raw, 'total_packages')
            and record.raw.total_packages is not None)
        show_total_weight = (
            hasattr(record.raw, 'total_weight')
            and record.raw.total_weight is not None)

        body = div()
        with body:
            lines_table = table()
            with lines_table:
                with thead():
                    with tr(cls='table-header'):
                        th(_('Customer Code'), cls='text-left')
                        th(_('Customer and Address'), cls='text-left')
                        th(_('Nº'), cls='text-left')
                        if show_packages:
                            th(_('Packages'), cls='text-right')
                        th(_('Weight'), cls='text-right')
                with tbody():
                    for shipment in record.shipments_out:
                        customer_code = (
                            shipment.customer.render.code
                            if shipment.raw.customer
                            and shipment.customer.raw.code
                            else '')
                        customer_name = (
                            shipment.customer.render.full_name
                            if shipment.raw.customer
                            and shipment.customer.raw.full_name
                            else (shipment.customer.render.rec_name
                                if shipment.raw.customer else ''))
                        address = (
                            shipment.delivery_address.render.full_address
                            if shipment.raw.delivery_address else '')
                        with tr():
                            td(customer_code)
                            with td():
                                if customer_name:
                                    div(customer_name, cls='thick')
                                if address:
                                    raw(address.replace('\n', '<br/>'))
                            td(shipment.render.number if shipment.raw.number else '')
                            if show_packages:
                                td(shipment.render.number_packages
                                    if (hasattr(shipment.raw, 'number_packages')
                                        and shipment.raw.number_packages is not None)
                                    else '',
                                    cls='text-right')
                            td(cls._render_weight(shipment), cls='text-right')
                    if show_total_packages or show_total_weight:
                        with tr(cls='table-total'):
                            td('')
                            td('')
                            td(_('Total') if show_total_packages else '',
                                cls='thick')
                            if show_packages:
                                td(record.render.total_packages
                                    if show_total_packages else '',
                                    cls='text-right')
                            td(record.render.total_weight
                                if show_total_weight else '',
                                cls='text-right')
        return body
