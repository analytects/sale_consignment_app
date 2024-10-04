# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_consignment = fields.Boolean(string='Is Consignment')

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