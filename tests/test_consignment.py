from odoo import Command, fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestConsignment(TransactionCase):

    def test_approval_creates_internal_transfer(self):
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)
        warehouse.int_type_id.active = True
        destination = self.env['stock.location'].create({
            'name': 'Consignment Test Location',
            'usage': 'internal',
            'location_id': warehouse.view_location_id.id,
        })
        route = self.env['stock.route'].create({'name': 'Consignment Test Route'})
        self.env['stock.rule'].create({
            'name': 'Consignment Test Rule',
            'route_id': route.id,
            'location_src_id': warehouse.lot_stock_id.id,
            'location_dest_id': destination.id,
            'picking_type_id': warehouse.int_type_id.id,
        })
        product = self.env['product.product'].create({
            'name': 'Consignment Test Product',
            'type': 'consu',
            'is_storable': True,
            'standard_price': 5,
            'list_price': 10,
        })
        self.env['stock.quant']._update_available_quantity(product, warehouse.lot_stock_id, 5)
        order = self.env['consignment.order'].create({
            'date': fields.Date.today(),
            'partner_id': self.env.company.partner_id.id,
            'warehouse_id': warehouse.id,
            'route_id': route.id,
            'line_ids': [Command.create({'product_id': product.id, 'quantity': 3})],
        })
        order.action_approval()
        picking = self.env['stock.picking'].search([('origin', '=', order.name)])
        self.assertEqual(order.state, 'approved')
        self.assertEqual(len(picking), 1)
        self.assertEqual(picking.move_ids.product_uom_qty, 3)
        self.assertEqual(picking.location_dest_id, destination)