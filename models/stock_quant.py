# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError 

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    inventory_quantity_auto_apply = fields.Float(
        help = 'TEST',
        groups='sale_consignment_app.group_sale_consignment_quants'
    )
    stored_inventory_quantity = fields.Float(
        string='Stored Inventory Quantity',
        store=True,
        compute='_compute_stored_inventory_quantity',
        digits='Product Unit of Measure',
        help='Campo almacenado que refleja el valor de inventory_quantity_auto_apply'
    )

    @api.depends('inventory_quantity_auto_apply')
    def _compute_stored_inventory_quantity(self):
        for record in self:
            record.stored_inventory_quantity = record.inventory_quantity_auto_apply