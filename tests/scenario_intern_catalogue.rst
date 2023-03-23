=========================
Intern Catalogue Scenario
=========================

Imports::

    >>> from decimal import Decimal
    >>> from proteus import Model, Wizard
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company

Install intern_catalogue::

    >>> config = activate_modules('intern_catalogue')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> template = ProductTemplate()
    >>> template.name = 'Product1'
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.list_price = Decimal('20')
    >>> template.save()
    >>> product1, = template.products
    >>> template = ProductTemplate()
    >>> template.name = 'Product2'
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.list_price = Decimal('20')
    >>> template.save()
    >>> product2, = template.products
    >>> template = ProductTemplate()
    >>> template.name = 'Product3'
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.list_price = Decimal('20')
    >>> template.save()
    >>> product3, = template.products

Get stock locations::

    >>> Location = Model.get('stock.location')
    >>> storage_loc, = Location.find([('code', '=', 'STO')])
    >>> storage_loc2 = Location(Location.copy([storage_loc.id], config.context)[0])

Create catalogue::

    >>> Catalogue = Model.get('stock.location.catalogue')
    >>> CatalogueLine = Model.get('stock.location.catalogue.line')
    >>> catalogue = Catalogue()
    >>> catalogue.name = 'DEMO'
    >>> catalogue.location = storage_loc
    >>> catalogue_line = CatalogueLine()
    >>> catalogue.lines.append(catalogue_line)
    >>> catalogue_line.product = product1
    >>> catalogue_line.max_quantity = 12
    >>> catalogue_line = CatalogueLine()
    >>> catalogue.lines.append(catalogue_line)
    >>> catalogue_line.product = product2
    >>> catalogue_line.max_quantity = 5
    >>> catalogue_line = CatalogueLine()
    >>> catalogue.lines.append(catalogue_line)
    >>> catalogue_line.product = product3
    >>> catalogue_line.max_quantity = 15
    >>> catalogue.save()

Create Shipment Internal::

    >>> ShipmentInternal = Model.get('stock.shipment.internal')
    >>> shipment_internal = ShipmentInternal()
    >>> shipment_internal.from_location = storage_loc
    >>> shipment_internal.to_location = storage_loc2
    >>> shipment_internal.company = company
    >>> shipment_internal.catalogues.append(catalogue)
    >>> shipment_internal.click('create_lines')
    >>> line1, line2, _ = shipment_internal.catalog_lines
    >>> line1.quantity = 5
    >>> line1.save()
    >>> line2.quantity = 3
    >>> line2.save()
    >>> shipment_internal.click('create_moves')
    >>> len(shipment_internal.moves) == 2
    True
    >>> move1, move2 = shipment_internal.moves
    >>> move2.quantity == line2.quantity
    True
    >>> move2.product == line2.product
    True
    >>> move1.quantity == line1.quantity
    True
    >>> move1.product == line1.product
    True
