# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError 

class StockMove(models.Model):
    _inherit = 'stock.move'

    is_consignment = fields.Boolean(
        string="Es Consignación",
        related='picking_id.is_consignment',
        store=True
    )

class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_consignment = fields.Boolean(string='Is Consignment')

    """
    def button_validate(self):
        res = super(StockPicking, self).button_validate()

        stock_picking_to_delete = self.env['stock.picking'].search([
            ('origin', 'like', 'SC-'),
            ('state', '=', 'assigned'),
            ('origin', '=', self.origin)
        ], limit=1)

        if stock_picking_to_delete:
            stock_picking_to_delete.unlink()

        return res
    """
    @api.model_create_multi
    def create(self, vals):
        res = super(StockPicking, self).create(vals)
        for val in vals:
            if 'origin' in val:
                so_id = self.env['sale.order'].search([
                    ('company_id', '=', val['company_id']),
                    ('name', '=', val['origin']),
                ], limit=1)
                if so_id.consignment_order_id:
                    raise UserError(so_id)
        return res