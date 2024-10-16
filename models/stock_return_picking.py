from odoo import api, models, fields, _
from odoo.exceptions import UserError


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.onchange('product_return_moves')
    def _onchange_product_return_moves(self):
        picking_id = self.env.context.get('active_id')
        if picking_id:
            picking = self.env['stock.picking'].browse(picking_id)
            if picking.origin and 'SC-' in picking.origin:
                
                consignment_orders = self.env['consignment.order'].search([('name', '=', picking.origin)])
                
                if not consignment_orders:
                    raise UserError(_("No se encontraron pedidos de consignación que coincidan con el origen del picking."))

                for consignment_order in consignment_orders:
                    for consignment_line in consignment_order.line_ids:
                        for return_move in self.product_return_moves:
                            if return_move.product_id == consignment_line.product_id:
                                return_move.quantity = consignment_line.remain_qty