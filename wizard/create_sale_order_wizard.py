from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CreateSaleOrderWizard(models.TransientModel):
    _name = 'create.sale.order.wizard'
    _description = "Create Sale Order Wizard"
    _rec_name = 'consignment_order_id'

    consignment_order_id = fields.Many2one('consignment.order', 'Consignment Order')
    line_ids = fields.One2many('create.sale.order.line.wizard', 'wizard_id', string="Lines")

    def action_create_sale_order(self):
        for rec in self:
            # for line_id in rec.line_ids:
            #     if line_id.sale_qty <= 0:
            #         raise ValidationError('Sale quantity must be greater than zero quantity')
            sale_order_id = self.env['sale.order'].create({
                'partner_id': rec.consignment_order_id.partner_id.id,
                'sale_consignment': True,
                'is_consignment': False,
                'consignment_order_id': rec.consignment_order_id.id,
                'warehouse_id': rec.consignment_order_id.so_warehouse_id.id,
                'route_id': rec.consignment_order_id.route_id.id,
                'origin': rec.consignment_order_id.name
            })
            for line_id in rec.line_ids:
                for con_line in rec.consignment_order_id.line_ids.filtered(
                        lambda line: line.product_id == line_id.product_id):
                    con_line.sale_qty += line_id.remain_qty
                    if con_line.sale_qty > con_line.quantity:
                        raise ValidationError('Total Sale Qty Must be Less Then Demand Quantity')
                sale_order_line_id = sale_order_id.order_line.create({'product_id': line_id.product_id.id,
                                                                      'product_uom_qty': line_id.remain_qty,
                                                                      'product_uom': line_id.product_id.uom_id.id,
                                                                      'stock_move_id': line_id.stock_move_id.id,
                                                                      'show_details': line_id.show_details,
                                                                      #'price_unit': line_id.unit_price,
                                                                      'price_unit': line_id.product_price,
                                                                      'order_id': sale_order_id.id,
                                                                      #'route_id': rec.consignment_order_id.route_id.id
                                                                      })
                for lot in line_id.lot_line_ids:
                    for con_line in rec.consignment_order_id.line_ids.filtered(
                            lambda line: line.product_id == line_id.product_id).consignment_lot_ids.filtered(
                        lambda line: line.lot_id == lot.lot_id):
                        con_line.qty_on_hand += lot.quantity
                    sale_order_line_id.order_line_lot_ids.create({'product_id': line_id.product_id.id,
                                                                  'lot_id': lot.lot_id.id,
                                                                  'quantity': lot.quantity,
                                                                  'line_id': sale_order_line_id.id
                                                                  })

            rec.consignment_order_id.sale_order_ids = [(4, sale_order_id.id)]
            rec.consignment_order_id.is_so_create = True
            rec.consignment_order_id.state = 'sale'

        return {
            'view_mode': 'form',
            'res_id': sale_order_id.id,
            'name': 'HR Payroll Report',
            'res_model': 'sale.order',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    @api.model
    def default_get(self, default_fields):
        res = super(CreateSaleOrderWizard, self).default_get(default_fields)
        active = self.env.context.get('active_id')
        consignment_order_id = self.env['consignment.order'].browse(active)
        line_vals = []

        for line_id in consignment_order_id.line_ids:
            lot_vals = []
            for lot in line_id.consignment_lot_ids:
                if lot.product_id == line_id.product_id:
                    l_vals = {
                        'product_id': line_id.product_id.id,
                        'lot_id': lot.lot_id.id,
                    }
                    lot_vals.append((0, 0, l_vals))
            vals = {
                'product_id': line_id.product_id.id,
                'stock_move_id': line_id.stock_move_id.id,
                'unit_price': line_id.product_id.lst_price or 1,
                'quantity': line_id.quantity,
                'remain_qty': line_id.remain_qty,
                'product_price': line_id.product_price,
                'show_details': line_id.show_details,
                'lot_line_ids': lot_vals,
            }

            line_vals.append((0, 0, vals))
        res.update({
            'consignment_order_id': consignment_order_id.id,
            'line_ids': line_vals
        })

        return res


class CreateSaleOrderLineWizard(models.TransientModel):
    _name = 'create.sale.order.line.wizard'
    _description = "Create Sale Order Line Wizard"

    wizard_id = fields.Many2one('create.sale.order.wizard', string='Wizard')
    product_id = fields.Many2one('product.product', 'Product')
    stock_move_id = fields.Many2one('stock.move', 'Stock Move')
    quantity = fields.Float(string="Demand")
    unit_price = fields.Float(string="Unit Price")
    sale_qty = fields.Float(string="Sale Quantity", compute='compute_sale_qty', store=True)
    remain_qty = fields.Float(string="Remaining Qty")
    show_details = fields.Boolean(string='Show Lot Details')
    lot_line_ids = fields.One2many('create.sale.order.lot.wizard', 'line_id')

    product_price = fields.Float(string="Precio Lista", readonly=True)

    @api.depends('lot_line_ids.quantity')
    def compute_sale_qty(self):
        for rec in self:
            if rec.lot_line_ids:
                qty = 0
                for line in rec.lot_line_ids:
                    qty += line.quantity
                rec.sale_qty = qty

    def action_show_details(self):
        self.ensure_one()

        view = self.env.ref('sale_consignment_app.create_sale_order_line_wizard_form_view')

        return {
            'name': _('Lot/Serial Number Detailed'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'create.sale.order.line.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': dict(
                self.env.context,
            ),
        }


class CreateSaleOrderLotWizard(models.TransientModel):
    _name = 'create.sale.order.lot.wizard'
    _description = "Create Sale Order Line Wizard"

    line_id = fields.Many2one('create.sale.order.line.wizard', string='Create Sale Order Line')
    product_id = fields.Many2one('product.product', 'Product', related='line_id.product_id',
                                 store=True)
    lot_id = fields.Many2one('stock.lot', 'Lot/Serial No')
    quantity = fields.Float(string="Quantity")
