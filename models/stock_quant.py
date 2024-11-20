# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError 

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    inventory_quantity_auto_apply = fields.Float(
        help = 'TEST',
        groups='sale_consignment_app.group_sale_consignment_quants'
    )