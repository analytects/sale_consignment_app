# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SaleOrderInherit(models.Model):
    _inherit = "sale.order"

    is_consignment = fields.Boolean(string='Is Consignment')
    sale_consignment = fields.Boolean(string='Sale Consignment')
    consignment_order_id = fields.Many2one('consignment.order', 'Consignment Order')
    route_id = fields.Many2one('stock.route', 'Route')

    is_locked_by_consignment = fields.Boolean(
        string="Bloqueado por Consignación", 
        compute="_compute_locked_by_consignment",
        store=True
    )

    is_locked_by_consignment_order = fields.Boolean(
        string="Bloqueado por Consignación", 
        compute="_compute_locked_by_consignment_order",
        store=True
    )

    @api.depends('consignment_order_id')
    def _compute_locked_by_consignment_order(self):
        for order in self:
            order.is_locked_by_consignment_order = bool(order.consignment_order_id)

    @api.depends('consignment_order_ids')
    def _compute_locked_by_consignment(self):
        for order in self:
            order.is_locked_by_consignment = bool(order.consignment_order_ids)

    consignment_order_ids = fields.One2many(
        'consignment.order', 
        'sale_order_id', 
        string='Órdenes de Consignación'
    )

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
    def action_convert_to_consignment(self):
        if not self.partner_id.is_consignment:
            raise UserError(_('Partner "{0}" is not allowed to create consignments'.format(self.partner_id.name)))
        # convert to consignment.order
        lines = []
        for line in self.order_line:
                lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'quantity': line.product_uom_qty,
                    'product_price': line.price_unit_discount if self.company_id.add_price_discount else 0,
                }))
        vals = {
            'date': fields.Date.context_today(self),
            'partner_id': self.partner_id.id,
            'warehouse_id': self.warehouse_id.id,
            'line_ids': lines,
            'route_id': 15,
            'sale_order_id': self.id,
        }
        consignment_id = self.env['consignment.order'].create(vals)
        self.consignment_order_id = consignment_id
        self.is_consignment = True
        self.sale_consignment = True
        self.action_cancel()
        return {
            'name': _('Consignments'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'consignment.order',
            'domain': [('id', '=', consignment_id.id)],
            'type': 'ir.actions.act_window',
        }
    
    def action_confirm(self):
        res = super(SaleOrderInherit, self).action_confirm()
        picking_ids = self.env['stock.picking'].search([
            ('sale_id', '=', self.id),
            ('state', '=', 'assigned'),
            ('sale_id.consignment_order_id', '!=', False)
        ])
        for picking_id in picking_ids:
            if picking_id.state == 'assigned':
                #picking_id.location_id = picking_id.sale_id.consignment_order_id.route_id.rule_ids[:1].location_dest_id.id,
                picking_id.picking_type_id = self.env['stock.picking.type'].search([('is_consignment_type', '=', True)], limit=1).id
                picking_id.button_validate()
        return res

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
