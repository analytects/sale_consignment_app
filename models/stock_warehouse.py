# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class StockWarehouseInherit(models.Model):
    _inherit = "stock.warehouse"

    consignment_location_id = fields.Many2one('stock.location', string='Consignment Location')
    is_consignment_warehouse = fields.Boolean(
        string='Is Consignment Warehouse'
    )
