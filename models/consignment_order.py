# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError 
import logging
_logger = logging.getLogger(__name__)

class StockQuant(models.Model):
    _inherit = 'stock.quant'

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

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_consignment = fields.Boolean()

class ConsignmentOrder(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Consignment Order'
    _name = 'consignment.order'

    name = fields.Char(string='Nombre', tracking=True)
    date = fields.Date('Fecha', tracking=True, required=True)
    partner_id = fields.Many2one('res.partner', string='Cliente', tracking=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Almacen', tracking=True)
    sale_order_ids = fields.Many2many('sale.order', 'rel_consignment_sale', 'consignment_order_id', 'sale_order_id',
                                      string='Ordenes', tracking=True, copy="False")
    user_id = fields.Many2one('res.users', string='Responsable', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string='Compañia', store=True, readonly=True,
                                 default=lambda self: self.env.user.company_id)
    state = fields.Selection([('quotation', 'Quotation'), ('waiting', 'Waiting Approval'), ('approved', 'Approved'),
                              ('consignment', 'Consignment'), ('sale', 'Sale Order'), ('done', 'Done'),
                              ('cancel', 'Cancel')], default='quotation', tracking=True)

    line_ids = fields.One2many('consignment.order.line', 'consignment_order_id', string="Líneas")

    no_of_pick = fields.Float(string='No of Pick', compute='compute_no_of_move')
    no_of_return = fields.Float(string='No of Pick', compute='compute_no_of_move')
    no_of_move = fields.Float(string='No of Move', compute='compute_no_of_move')
    no_of_move_line = fields.Float(string='No of Move Line', compute='compute_no_of_move')
    no_of_so = fields.Float(string='No of Move Line', compute='compute_no_of_move')
    is_so_create = fields.Boolean(string="Is Sale Order Created")
    route_id = fields.Many2one('stock.route', 'Ruta', required=True, ondelete='cascade')
    #location_id = fields.Many2one('stock.location', 'Ubicación de origen', required=True)
    #location_dest_id = fields.Many2one('stock.location', 'Ubicación de destino', required=True)

    sale_order_id = fields.Many2one(
        'sale.order', 
        string='Orden existente', 
        domain="[('state', 'in', ['draft','sent'])]",
        tracking=True)
    
    all_remain_qty_is_zero = fields.Boolean(
        compute='_compute_all_remain_qty_is_zero'
    )

    _sql_constraints = [
        ('unique_sale_order', 'unique(sale_order_id)', 'La orden de venta ya está asignada a otra orden de consignación.')
    ]

    @api.constrains('sale_order_id')
    def _check_unique_sale_order(self):
        for record in self:
            if record.sale_order_id:
                existing = self.search([
                    ('sale_order_id', '=', record.sale_order_id.id),
                    ('id', '!=', record.id)
                ], limit=1)
                if existing:
                    raise ValidationError("Esta orden de venta ya está asignada a otra orden de consignación.")

    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        if self.sale_order_id:

            self.partner_id = self.sale_order_id.partner_id.id

            self.sale_order_id.is_locked_by_consignment = True 

            # Limpiar líneas existentes
            self.line_ids = [(5, 0, 0)]

            lines = []
            for line in self.sale_order_id.order_line:
                lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'quantity': line.product_uom_qty,
                    #'product_price': line.price_unit,
                }))

            self.line_ids = lines

    def action_cancel(self):
        for rec in self:
            # if rec.sale_order_id:
            #     rec.sale_order_id.action_cancel()
            rec.state = 'cancel'
            rec.action_create_return()
    
    def action_create_return(self):
        for rec in self:
            # if rec.state not in ['approved']:
            #     raise UserError(_('No se puede crear una devolución desde el estado actual de la orden de consignación.'))

            picking_ids = self.env['stock.picking'].search([
                ('origin', '=', rec.name),
                ('state', 'in', ['done']) 
            ])
            for picking in picking_ids.filtered(lambda p: p.state == 'done'):
                ctx = dict(self._context or {})
                ctx.update({
                    'active_model': 'stock.picking',
                    'active_ids': [picking.id],
                    'active_id': picking.id,
                })

                product_returns = []
                to_return = rec.get_unsold_products(picking_ids, rec.sale_order_ids.filtered(lambda so: so.state == 'sale'))
                for move in to_return:
                    product_returns.append((0, 0, {
                        'product_id': move.product_id.id,
                        'quantity': move.quantity,
                        'move_id': move.id,
                    }))

                wizard_values = {
                    'picking_id': picking.id,
                    'location_id': picking.location_id.id,
                    'product_return_moves': product_returns,
                }
                wizard = self.env['stock.return.picking'].with_context(ctx).create(wizard_values)
                new_picking = wizard.create_returns()
                #new_picking.consignment_id = rec.id
    
    def get_unsold_products(self, picking_ids, sale_order_ids):
        self.ensure_one()
        original_lines = picking_ids[0].move_ids_without_package
        so_lines = sale_order_ids.mapped('picking_ids.move_ids_without_package')
        for line in so_lines:
            product_lines = original_lines.filtered(lambda m: m.product_id == line.product_id)
            if product_lines:
                product_lines.quantity -= line.quantity
        return original_lines.filtered(lambda m: m.quantity > 0)
                
        


    def action_done(self):
        for rec in self:
            rec.state = 'done'

    def action_return(self):
        for rec in self:

            stock_picking = self.env['stock.picking'].search([
                ('origin', '=', rec.name),
                ('state', '!=', 'cancel')
            ], limit=1)

            if stock_picking:
                ctx = dict(self._context or {})
                ctx.update({
                    'active_model': 'stock.picking',
                    'active_ids': [stock_picking.id],
                    'active_id': stock_picking.id,
                })

                product_returns = []
                for move in stock_picking.move_ids_without_package:
                    product_returns.append((0, 0, {
                        'product_id': move.product_id.id,
                        'quantity': move.quantity,
                        'move_id': move.id,
                    }))

                wizard_values = {
                    'picking_id': stock_picking.id,
                    'location_id': stock_picking.location_id.id,
                    'product_return_moves': product_returns,
                }
                wizard = self.env['stock.return.picking'].with_context(ctx).create(wizard_values)

                new_picking = wizard.create_returns()

                new_picking_id = new_picking.get('res_id')
                if new_picking_id:
                    created_picking = self.env['stock.picking'].browse(new_picking_id)
                    if created_picking.state == 'assigned':
                        for mv in created_picking.move_ids_without_package:
                            mv.quantity = mv.product_uom_qty
                        created_picking.button_validate()
                    created_picking.origin = stock_picking.origin
                #rec.state = 'done'
        return True

    def action_create_sale_order(self):
        view = self.env.ref('sale_consignment_app.create_sale_order_wizard_form_view')

        return {
            'name': _('Create Sale Order Wizard'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'create.sale.order.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'flags': {'form': {'action_buttons': True}},
            'context': dict(
                self.env.context,
            ),
        }

    def compute_no_of_move(self):
        for rec in self:
            pick_ids = rec.env['stock.picking'].search([('origin', '=', self.name)])
            return_ids = rec.env['stock.picking'].search([('consignment_id', '=', self.id)])
            move_ids = rec.env['stock.move'].search([('origin', '=', self.name)])
            move_line_ids = rec.env['stock.move.line'].search([('origin', '=', self.name)])
            sale_order_id = rec.env['sale.order'].search([('consignment_order_id', '=', self.id)])
            rec.no_of_pick = len(pick_ids)
            rec.no_of_return = len(return_ids)
            rec.no_of_move = len(move_ids)
            rec.no_of_move_line = len(move_line_ids)
            rec.no_of_so = len(sale_order_id)

    def action_view_sale_order(self):
        xml_id = 'sale.view_order_tree'
        tree_view_id = self.env.ref(xml_id).id
        xml_id = 'sale.view_order_form'
        form_view_id = self.env.ref(xml_id).id
        return {
            'name': _('Sale Order'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'res_model': 'sale.order',
            'domain': [('consignment_order_id', '=', self.id)],
            'context': {'create': 0, 'edit': 0},
            'type': 'ir.actions.act_window',
        }

    def action_view_stock_picking(self):
        xml_id = 'stock.vpicktree'
        tree_view_id = self.env.ref(xml_id).id
        xml_id = 'stock.view_picking_form'
        form_view_id = self.env.ref(xml_id).id
        return {
            'name': _('Transferencias'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'res_model': 'stock.picking',
            'domain': [('origin', '=', self.name)],
            'context': {'create': 0, 'edit': 0},
            'type': 'ir.actions.act_window',
        }
    def action_view_return(self):
        return

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('consignment.order') or 'New'
        return super(ConsignmentOrder, self).create(vals)

    def action_waiting_approval(self):
        self.state = 'waiting'

    def action_approval(self):

        if self.sale_order_id:
            self.sale_order_id.action_cancel()

        pick_vals = self._prepare_picking()
        stock_picking = self.env['stock.picking'].create(pick_vals)
        if stock_picking:
            self._prepare_picking_lines(stock_picking)
            #stock_picking.action_confirm()

        self.state = 'approved'

    def action_confirm(self):
        for rec in self:
            rec.state = 'consignment'

            stock_picking = self.env['stock.picking'].search([
                ('origin', '=', rec.name),
                ('state', 'in', ['draft','waiting','confirmed','assigned']) 
            ], limit=1)

            if stock_picking:
                #stock_picking.button_validate()

                raise UserError("No se ha validado la transferencia que ingresa el producto a la ubicación de consignación, vefique en inventario antes de confirmar.")

                """
                stock_picking_to_delete = self.env['stock.picking'].search([
                    ('origin', 'like', 'SC-'),
                    ('state', '=', 'assigned'),
                    ('origin', '=', stock_picking.origin)
                ], limit=1)

                if stock_picking_to_delete:
                    stock_picking_to_delete.unlink()
                """

    def _prepare_picking(self):

        picking_type = self.env['stock.picking.type'].search([
            ('warehouse_id', '=', self.warehouse_id.id),
            ('code', '=', 'internal')
        ], limit=1)

        if not picking_type:
            raise ValidationError(_("No se encontró ningún tipo de picking con los criterios especificados."))

        return {
            'partner_id': self.partner_id.id,
            'picking_type_id': picking_type.id,
            'location_id': self.route_id.rule_ids[:1].location_src_id.id,
            'location_dest_id': self.route_id.rule_ids[:1].location_dest_id.id,
            'origin': self.name,
            'company_id': self.company_id.id,
            'move_type': 'direct',
            'state': 'draft',
            'scheduled_date': self.date,
            'is_consignment': True,
        }

    def _prepare_picking_lines(self, stock_picking):
        move_lines = []
        for line_id in self.line_ids:

            #Buscar ubicaciones con stock
            """
            quant_domain = [
                ('product_id', '=', line_id.product_id.id),
                ('location_id', 'child_of', stock_picking.location_id.id),
                ('inventory_quantity_auto_apply', '>=', line_id.quantity)
            ]
            """
            quant_domain = [
                ('product_id', '=', line_id.product_id.id),
                ('location_id', 'child_of', stock_picking.location_id.id),
                ('stored_inventory_quantity', '>=', line_id.quantity),
                ('on_hand', '=', True),
                ('location_id.usage', '=', 'internal')
            ]
            #stock_quant = self.env['stock.quant'].search(quant_domain, limit=1)

            stock_quants = self.env['stock.quant'].search(quant_domain)
            stock_quants = sorted(stock_quants, key=lambda q: len(q.location_id.child_ids))
            stock_quant = stock_quants[0] if stock_quants else None

            if stock_quant:
                location_temp = stock_quant.location_id.id
            else:
                location_temp = stock_picking.location_id.id

            if line_id.show_details:
                for line_lot in line_id.consignment_lot_ids:
                    move_lines.append((0, 0, {
                        'picking_id': stock_picking.id,
                        'product_id': line_lot.product_id.id,
                        'product_uom_qty': line_lot.quantity,
                        'product_uom': line_lot.uom_id.id,
                        'location_id': stock_picking.location_id.id,
                        'location_dest_id': stock_picking.location_dest_id.id,
                        'name': self.name,
                    }))
            else:
                move_lines.append((0, 0, {
                    'picking_id': stock_picking.id,
                    'product_id': line_id.product_id.id,
                    #'product_uom_qty': line_id.quantity,
                    'product_uom_qty': line_id.quantity,
                    'quantity': line_id.quantity,
                    'product_uom': line_id.product_id.uom_id.id,
                    #'product_uom_id': line_id.product_id.uom_id.id,
                    #'location_id': stock_picking.location_id.id,
                    'location_id': location_temp,
                    'location_dest_id': stock_picking.location_dest_id.id,
                    'name': self.name,
                }))
        
        #stock_picking.write({'move_line_ids': move_lines})
        stock_picking.write({'move_ids_without_package': move_lines})

    @api.depends('line_ids')
    def _compute_all_remain_qty_is_zero(self):
        for rec in self:
            rec.all_remain_qty_is_zero = True
            for line_id in rec.line_ids:
                if line_id.remain_qty != 0:
                    rec.all_remain_qty_is_zero = False

class ConsignmentOrderLine(models.Model):
    _name = "consignment.order.line"
    _rec_name = 'product_id'

    consignment_order_id = fields.Many2one('consignment.order', 'Orden de consignacion')
    product_tmpl_id = fields.Many2one('product.template', 'Product', related='product_id.product_tmpl_id', store=True)
    product_id = fields.Many2one('product.product', 'Product')
    stock_move_id = fields.Many2one('stock.move', 'Stock Move')
    quantity = fields.Float(string="Demand")
    sale_qty = fields.Float(string="Sale Quantity")
    remain_qty = fields.Float(string="Remaining Qty", compute='compute_remaining_qty')
    qty_on_hand = fields.Float(string="Available Qty", related='product_id.qty_available', store=True)
    consignment_lot_ids = fields.One2many('consignment.order.lot', 'consignment_order_line_id', string="Lines",
                                          )
    show_details = fields.Boolean(string='Show Lot Details', compute='compute_show_details')

    state = fields.Selection([('quotation', 'Quotation'), ('waiting', 'Waiting Approval'), ('approved', 'Approved'),
                              ('consignment', 'Consignment'), ('sale', 'Sale Order'), ('done', 'Done'),
                              ('cancel', 'Cancel')], default='quotation', related='consignment_order_id.state',
                             store=True)

    product_price = fields.Float(string="Precio Lista", readonly=True)
    quantity_delivery = fields.Float(string="Cantidad entregada", compute="_compute_quantity_delivery", readonly=True)
    price_invoiced = fields.Float(string="Facturado", compute="_compute_price_invoiced", readonly=True)

    @api.depends('product_id')
    def compute_show_details(self):
        for rec in self:
            if rec.product_id.tracking == 'none':
                rec.show_details = False
            else:
                rec.show_details = True

    @api.depends('quantity', 'sale_qty')
    def compute_remaining_qty(self):
        for rec in self:
            rec.remain_qty = rec.quantity - rec.sale_qty

    def action_show_details(self):
        self.ensure_one()

        view = self.env.ref('sale_consignment_app.consignment_order_line_view_form')

        return {
            'name': _('Lot/Serial Number Detailed'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'consignment.order.line',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': dict(
                self.env.context,
            ),
        }

    @api.model
    def create(self, vals):
        if vals.get('product_id') and vals.get('consignment_order_id'):
            product = self.env['product.product'].browse(vals['product_id'])
            consignment_order = self.env['consignment.order'].browse(vals['consignment_order_id'])
            partner = consignment_order.partner_id

            if not partner:
                raise UserError(_("No se encontró un contacto válido para la orden de consignación."))
            if consignment_order.company_id.add_price_discount:
                return super(ConsignmentOrderLine, self).create(vals)

            vals['product_price'] = self._get_product_price(product, partner)

        return super(ConsignmentOrderLine, self).create(vals)

    def _get_product_price(self, product, partner):
        company = self.env.company
        pricelist = partner.property_product_pricelist

        if not pricelist:
            return product.with_company(company).lst_price

        try:
            price = pricelist._get_product_price(
                product, 
                quantity=1.0, 
                partner=partner, 
                date=fields.Date.today(), 
                uom_id=product.uom_id
            )
        except Exception as e:
            # Si hay algún error al obtener el precio de la tarifa, se usa el precio de lista
            self.env.cr.rollback()
            price = product.with_company(company).lst_price

        # Asegurarse de que el precio esté en la moneda de la compañía
        if pricelist.currency_id != company.currency_id:
            price = pricelist.currency_id._convert(
                price, 
                company.currency_id, 
                company, 
                fields.Date.today()
            )

        return price

    @api.depends('consignment_order_id')
    def _compute_quantity_delivery(self):
        for line in self:
            total_quantity = 0.0

            stock_pickings = self.env['stock.picking'].search([
                ('origin', '=', line.consignment_order_id.name),
                ('state', '=', 'done')
            ])

            for picking in stock_pickings:
                for move in picking.move_ids_without_package:
                    if move.product_id == line.product_id:
                        total_quantity += move.quantity

            line.quantity_delivery = total_quantity

    @api.depends('consignment_order_id')
    def _compute_price_invoiced(self):
        for line in self:
            total_invoiced = 0.0

            for k in line.consignment_order_id.sale_order_ids:
                for move in k.invoice_ids:
                    for j in move.invoice_line_ids:
                        if j.product_id == line.product_id:
                            total_invoiced += j.price_total

            """
            sale_order = self.env['sale.order'].search([
                ('origin', '=', line.consignment_order_id.name),
                ('state', '=', 'sale')
            ])

            if sale_order:
                for so in sale_order:

                    account_move = self.env['account.move'].search([
                        ('invoice_origin', '=', so.name),
                        ('state', '=', 'posted')
                    ])

                    if account_move:
                        for move in account_move:
                            for i in move.invoice_line_ids:
                                if i.product_id == line.product_id:
                                    total_invoiced += i.price_total
            """

            line.price_invoiced = total_invoiced

class ConsignmentOrderLot(models.Model):
    _name = "consignment.order.lot"
    _rec_name = 'product_id'

    consignment_order_line_id = fields.Many2one('consignment.order.line', 'Consignment Order')
    product_id = fields.Many2one('product.product', 'Product', related='consignment_order_line_id.product_id',
                                 store=True)
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    lot_id = fields.Many2one('stock.lot', 'Lot/Serial No')
    quantity = fields.Float(string="Quantity")
    qty_on_hand = fields.Float(string="Sale Quantity")

    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.uom_id = rec.product_id.uom_id