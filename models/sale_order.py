# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SaleOrderInherit(models.Model):
    _inherit = "sale.order"

    is_consignment = fields.Boolean(string='Is Consignment')
    sale_consignment = fields.Boolean(string='Sale Consignment')
    consignment_order_id = fields.Many2one('consignment.order', 'Consignment Order')
    route_id = fields.Many2one('stock.route', 'Route')

    def action_view_stock_move_line(self):
        move_line_ids = self.env['stock.move.line'].search([('origin', '=', self.name)])
        xml_id = 'stock.view_move_line_tree'
        tree_view_id = self.env.ref(xml_id).id
        xml_id = 'stock.view_move_line_form'
        form_view_id = self.env.ref(xml_id).id
        return {
            'name': _('Traceability'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'res_model': 'stock.move.line',
            'domain': [('id', 'in', move_line_ids.ids)],
            'context': {'create': 0, 'edit': 0},
            'type': 'ir.actions.act_window',
        }


class SaleOrderLineInherit(models.Model):
    _inherit = "sale.order.line"

    purchase_order_line_id = fields.Many2one('purchase.order.line', string="Purchase Order Line")
    is_consignment = fields.Boolean(string='Is Consignment', related='order_id.is_consignment', store=True)
    show_details = fields.Boolean(string="Show Lot Details")
    stock_move_id = fields.Many2one('stock.move', 'Stock Move')
    order_line_lot_ids = fields.One2many('sale.order.line.lot', 'line_id')

    def action_show_details(self):
        self.ensure_one()

        view = self.env.ref('sale_consignment_app.sale_consignment_order_line_view_form')

        return {
            'name': _('Lot/Serial Number Detailed'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sale.order.line',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': dict(
                self.env.context,
            ),
        }


class SaleOrderLineLotInherit(models.Model):
    _name = "sale.order.line.lot"
    _description = "Sale Order Line Lot"
    _rec_name = 'line_id'

    line_id = fields.Many2one('sale.order.line', string='Order Line')
    product_id = fields.Many2one('product.product', 'Product', related='line_id.product_id',
                                 store=True)
    lot_id = fields.Many2one('stock.lot', 'Lot/Serial No')
    quantity = fields.Float(string="Quantity")
