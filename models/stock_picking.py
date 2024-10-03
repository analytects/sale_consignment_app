# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_consignment = fields.Boolean(string='Is Consignment')
