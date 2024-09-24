# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SaleOrderInherit(models.Model):
    _inherit = "res.partner"

    is_consignment = fields.Boolean(string='Is Consignment')
    partner_type = fields.Selection([('customer', 'customer'),('vendor', 'vendor')])
