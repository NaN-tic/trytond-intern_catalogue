# This file is part intern_catalogue module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import shipment

module = 'intern_catalogue'

def register():
    Pool.register(
        shipment.ShipmentCatalogues,
        shipment.ShipmentInternalCatalogLine,
        shipment.ShipmentInternal,
        module=module, type_='model')
