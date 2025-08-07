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
    consignment_id = fields.Many2one(
        comodel_name='consignment.order',
        help='Field used for linking the picking RETURN to a consignment order',
    )

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