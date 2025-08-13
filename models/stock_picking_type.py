# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    is_consignment_type = fields.Boolean(
        string='Is Consignment Operation Type',
        default=False
    )