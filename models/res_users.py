# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ResUsers(models.Model):
    _inherit = 'res.users'

    default_consignment_warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Almacén de Consignación'
    )
    default_route_id = fields.Many2one(
        comodel_name='stock.route',
        string='Ruta de Consignación'
    )
    default_so_warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Almacén de Venta de consignación'
    )