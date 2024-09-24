# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProductTemplateInherit(models.Model):
    _inherit = "product.template"

    is_consignment = fields.Boolean(string='Is Consignment')
