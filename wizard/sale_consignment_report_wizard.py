from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class saleConsignmentWizard(models.TransientModel):
    _name = 'sale.consignment.report.wizard'
    _description = "Sale Consignment Report Wizard"

    consignment_order_id = fields.Many2one('consignment.order', 'Consignment Order')
    report_type = fields.Selection([('sale', 'Consignment Sale Order Report'), ('details', 'Sale Consignment Order Report')],
                                   default='sale', string="Print Report for")
    date_from = fields.Date('Start Date')
    date_to = fields.Date('End Date')
    product_ids = fields.Many2many('product.product', 'rel_product_sale_report_wizard', 'wizard_id', 'product_id',
                                   string="Product")
    partner_ids = fields.Many2many('res.partner', 'rel_partner_sale_report_wizard', 'wizard_id', 'partner_id',
                                   string="Customer")
    sale_order_line_ids = fields.Many2many('sale.order.line', 'rel_sale_order_line_sale_report_wizard', 'wizard_id',
                                           'sale_order_line_id',
                                           string="Sale Order line")

    def action_print_report(self):
        return self.env.ref('sale_consignment_app.action_sale_consignment_report').report_action(self)

    @api.onchange('date_from', 'date_to', 'product_ids', 'partner_ids')
    def onchange_consignment_account(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                if rec.date_from > rec.date_to:
                    raise ValidationError(
                        _('Date From should be less then Date to'))
                if rec.product_ids and rec.partner_ids:
                    sale_order_line_ids = rec.env['sale.order.line'].search(
                        [('product_id', '=', rec.product_ids.ids),
                         ('order_id.partner_id', '=', rec.partner_ids.ids),
                         ('order_id.sale_consignment', '=', True),
                         ('order_id.date_order', '>', rec.date_from),
                         ('order_id.date_order', '<', rec.date_to)])
                elif rec.product_ids:
                    sale_order_line_ids = rec.env['sale.order.line'].search(
                        [('product_id', '=', rec.product_ids.ids),
                         ('order_id.sale_consignment', '=', True),
                         ('order_id.date_order', '>', rec.date_from),
                         ('order_id.date_order', '<', rec.date_to)])

                elif rec.partner_ids:
                    sale_order_line_ids = rec.env['sale.order.line'].search(
                        [('order_id.partner_id', '=', rec.partner_ids.ids),
                         ('order_id.sale_consignment', '=', True),
                         ('order_id.date_order', '>', rec.date_from),
                         ('order_id.date_order', '<', rec.date_to)])

                else:
                    sale_order_line_ids = rec.env['sale.order.line'].search(
                        [('order_id.sale_consignment', '=', True),
                         ('order_id.date_order', '>', rec.date_from),
                         ('order_id.date_order', '<', rec.date_to)])

                rec.sale_order_line_ids = [(6, 0, sale_order_line_ids.ids)]
