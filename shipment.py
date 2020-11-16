# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import PoolMeta, Pool
from trytond.model import fields, ModelSQL, ModelView
from trytond.rpc import RPC
from trytond.pyson import Eval, If
from trytond.transaction import Transaction
from trytond.i18n import gettext
from trytond.exceptions import UserError

__all__ = ['ShipmentCatalogues', 'ShipmentInternalCatalogLine',
    'ShipmentInternal']


class ShipmentCatalogues(ModelSQL):
    'Shipment Internal - Stock Location Catalogue'
    __name__ = 'stock.shipment.internal-stock.location.catalogue'
    shipment = fields.Many2One('stock.shipment.internal', 'Shipment')
    catalogue = fields.Many2One('stock.location.catalogue', 'Catalogue')


class ShipmentInternalCatalogLine(ModelSQL, ModelView):
    'Lines from the catalogs entered by the user in the app'
    __name__ = 'stock.shipment.internal.catalog_line'
    catalogue = fields.Many2One('stock.location.catalogue', 'Catalogue')
    internal_shipment = fields.Many2One('stock.shipment.internal', 'Shipment',
        required=True, ondelete="CASCADE")
    product = fields.Many2One('product.product', 'Product', required=True)
    quantity = fields.Float('Quantity', required=True,
        digits=(16, Eval('unit_digits', 2)), depends=['unit_digits'])
    max_quantity = fields.Float('Max Quantity', required=True, readonly=True,
        digits=(16, Eval('unit_digits', 2)), depends=['unit_digits'])
    served_quantity = fields.Function(fields.Float('Served Quantity',
        readonly=True, digits=(16, Eval('unit_digits', 2)),
        depends=['unit_digits']), 'on_change_with_served_quantity')
    unit_digits = fields.Function(fields.Integer('Unit Digits'),
        'on_change_with_unit_digits')

    @staticmethod
    def default_quantity():
        return 0

    @fields.depends('internal_shipment', '_parent_internal_shipment.moves')
    def on_change_with_served_quantity(self, name=None):
        if not self.internal_shipment:
            return 0
        for move in self.internal_shipment.moves:
            if move.product == self.product:
                return int(move.quantity)
        return 0

    @fields.depends('product')
    def on_change_with_unit_digits(self, name=None):
        if self.product:
            return self.product.default_uom.digits
        return 2

    @classmethod
    def validate(cls, lines):
        for line in lines:
            line.check_validate_max_quantity()

    def check_validate_max_quantity(self):
        if self.quantity > self.max_quantity:
            raise UserError(gettext('intern_catalogue.msg_error_quantity_product',
                    product=self.product.rec_name,
                    amount=self.max_quantity))


class ShipmentInternal(metaclass=PoolMeta):
    __name__ = 'stock.shipment.internal'
    employee = fields.Many2One('company.employee', 'Employee',
        help='Employee that made the request')
    catalogues = fields.Many2Many(
        'stock.shipment.internal-stock.location.catalogue',
        'shipment', 'catalogue', 'Catalogues')
    catalog_lines = fields.One2Many('stock.shipment.internal.catalog_line',
        'internal_shipment', 'Catalog Lines', help='Lines entered by the user',
        )

    @classmethod
    def __setup__(cls):
        super(ShipmentInternal, cls).__setup__()
        cls.__rpc__.update({
            'app_create_lines': RPC(readonly=False),
            'app_create_moves': RPC(readonly=False),
            })
        cls._buttons.update({
            'create_lines': {
                'invisible': Eval('catalog_lines'),
                },
            'create_moves': {
                'invisible': (~Eval('catalog_lines') | Eval('moves') |
                    (Eval('state') != 'draft')),
                },
            })
        # replace from_location in moves domain
        cls.moves.domain = [
            If(Eval('state') == 'draft', [
                    ('to_location', '=', Eval('to_location')),
                    ],
                If(~Eval('transit_location'),
                    [
                        ('to_location', 'child_of',
                            [Eval('to_location', -1)], 'parent'),
                        ],
                    ['OR',
                        [
                            ('to_location', '=', Eval('transit_location')),
                            ],
                        [
                            ('to_location', 'child_of',
                                [Eval('to_location', -1)], 'parent'),
                            ],
                        ])),
            ('company', '=', Eval('company')),
            ]
        cls.outgoing_moves.domain = [
            If(~Eval('transit_location'),
                ('to_location', 'child_of', [Eval('to_location', -1)],
                    'parent'),
                ('to_location', '=', Eval('transit_location')))
            ]
        cls.incoming_moves.domain = [
            ('to_location', 'child_of', [Eval('to_location', -1)],
                'parent'),
            ]

    @classmethod
    def default_from_location(cls):
        return Transaction().context.get('catalogue_from_location')

    @classmethod
    def default_to_location(cls):
        return Transaction().context.get('catalogue_to_location')

    @classmethod
    def app_create_lines(cls, shipment_ids):
        shipments = cls.browse(shipment_ids)
        cls.create_lines(shipments)

    @classmethod
    @ModelView.button
    def create_lines(cls, shipments):
        CatalogLine = Pool().get('stock.shipment.internal.catalog_line')

        to_create = []
        for shipment in shipments:
            for catalogue in shipment.catalogues:
                for catalog_line in catalogue.lines:
                    new_line = CatalogLine()
                    new_line.internal_shipment = shipment
                    new_line.product = catalog_line.product
                    new_line.max_quantity = catalog_line.max_quantity
                    new_line.catalogue = catalogue
                    to_create.append(new_line)
        if to_create:
            CatalogLine.create([x._save_values for x in to_create])

    @classmethod
    def app_create_moves(cls, shipment_ids):
        shipments = cls.browse(shipment_ids)
        cls.create_moves(shipments)

    @classmethod
    @ModelView.button
    def create_moves(cls, shipments):
        Move = Pool().get('stock.move')

        to_create = []
        to_delete = []
        same_from_to_locations = set()
        for shipment in shipments:
            if shipment.state != 'draft':
                continue
            to_delete.append(shipment)
            move_lines_with_quantity = [line for line in shipment.catalog_lines
                if line.quantity > 0]
            for line in move_lines_with_quantity:
                move = Move()
                move.shipment = shipment
                move.company = shipment.company
                move.from_location = line.catalogue.location
                move.to_location = shipment.to_location
                if move.from_location == move.to_location:
                    same_from_to_locations.add(move.from_location.rec_name)
                    break
                move.product = line.product
                move.on_change_product()
                move.quantity = line.quantity
                to_create.append(move)
        if same_from_to_locations:
            raise UserError(gettext('intern_catalogue.msg_same_from_to_locations',
                    locations=','.join(list(same_from_to_locations))))

        if to_delete:
            Move.draft([m for s in to_delete for m in s.moves])
            Move.delete([m for s in to_delete for m in s.moves
                    if m.state in ('draft', 'cancel')])

        if to_create:
            Move.create([x._save_values for x in to_create])

    @classmethod
    def draft(cls, shipments):
        super(ShipmentInternal, cls).draft(shipments)
        # remove and create new moves from catalog lines
        cls.create_moves(shipments)
