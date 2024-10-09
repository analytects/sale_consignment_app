# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_consignment = fields.Boolean()

class ConsignmentOrder(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Consignment Order'
    _name = 'consignment.order'

    name = fields.Char(string='Name', tracking=True)
    date = fields.Date('Date', tracking=True, required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', tracking=True)
    sale_order_ids = fields.Many2many('sale.order', 'rel_consignment_sale', 'consignment_order_id', 'sale_order_id',
                                      string='Sale Order', tracking=True, copy="False")
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string='Company', store=True, readonly=True,
                                 default=lambda self: self.env.user.company_id)
    state = fields.Selection([('quotation', 'Quotation'), ('waiting', 'Waiting Approval'), ('approved', 'Approved'),
                              ('consignment', 'Consignment'), ('sale', 'Sale Order'), ('done', 'Done'),
                              ('cancel', 'Cancel')], default='quotation', tracking=True)

    line_ids = fields.One2many('consignment.order.line', 'consignment_order_id', string="Lines")

    no_of_pick = fields.Float(string='No of Pick', compute='compute_no_of_move')
    no_of_move = fields.Float(string='No of Move', compute='compute_no_of_move')
    no_of_move_line = fields.Float(string='No of Move Line', compute='compute_no_of_move')
    no_of_so = fields.Float(string='No of Move Line', compute='compute_no_of_move')
    is_so_create = fields.Boolean(string="Is Sale Order Created")
    route_id = fields.Many2one('stock.route', 'Route', required=True, ondelete='cascade')
    #location_id = fields.Many2one('stock.location', 'Ubicación de origen', required=True)
    #location_dest_id = fields.Many2one('stock.location', 'Ubicación de destino', required=True)

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    """
    def action_done(self):
        for rec in self:
            rec.state = 'done'
            for line_id in rec.line_ids:
                line_id.stock_move_id._do_unreserve()
                line_id.stock_move_id._action_done()
    """

    def action_done(self):
        for rec in self:
            rec.state = 'done'

    """
    def action_return(self):
        for rec in self:
            for line_id in rec.line_ids:
                move_vals = self._prepare_return_move(line_id)
                stock_move = self.env['stock.move'].create(move_vals)
                if stock_move:

                    stock_move._action_confirm()
                    stock_move._do_unreserve()
                    stock_move._action_assign()
                    stock_move._action_done()

                    line_id.stock_move_id._do_unreserve()
                    line_id.stock_move_id._action_done()
                    rec.state = 'done'

    def _prepare_return_move(self, line_id):
        #location_id = self.warehouse_id.consignment_location_id.id
        #location_dest_id = self.env.ref('stock.stock_location_stock').id
        
        #location_id = self.location_dest_id.id
        #location_dest_id = self.location_id.id

        first_rule = self.route_id.rule_ids[:1]

        if not first_rule:
            raise ValidationError(_("No se encontró ninguna regla en la ruta seleccionada."))

        location_id = first_rule.location_dest_id.id
        location_dest_id = first_rule.location_src_id.id

        move_lines = []
        if line_id.show_details:
            for line_lot in line_id.consignment_lot_ids:
                qty = line_lot.quantity - line_lot.qty_on_hand
                vals = {
                    'product_id': line_id.product_id.id,
                    'lot_id': line_lot.lot_id.id,
                    'quantity': qty,  # bypass reservation here
                    'product_uom_id': line_lot.uom_id.id,
                    'quantity': qty,
                    'origin': self.name,
                    'reference': self.name,
                    'location_id': location_id,
                    'location_dest_id': location_dest_id,
                    'owner_id': self.partner_id.id,
                }
                move_lines.append((0, 0, vals))
        else:
            qty = line_id.quantity - line_id.sale_qty
            vals = {
                'product_id': line_id.product_id.id,
                'quantity': qty,  # bypass reservation here
                'product_uom_id': line_id.product_id.uom_id.id,
                'quantity': qty,
                'origin': self.name,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'owner_id': self.partner_id.id,
                'reference': self.name,
            }
            move_lines.append((0, 0, vals))
        qty = line_id.quantity - line_id.sale_qty
        move_vals = {
            'product_id': line_id.product_id.id,
            'product_uom': line_id.product_id.uom_id.id,
            'quantity': qty,
            'date': self.date,
            'name': self.name,
            'origin': self.name,
            'move_line_ids': move_lines,
            'reference': self.name,
            'company_id': self.company_id.id,
            'restrict_partner_id': self.partner_id.id,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
        }
        return move_vals
    """

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
            'target': 'current',
            'flags': {'form': {'action_buttons': True}},
            'context': dict(
                self.env.context,
            ),
        }

    #Método de momento no se usa ya que se cambio la logica para crear un pick directamente
    """
    def action_unreserved(self):
        for line_id in self.line_ids:
            line_id.stock_move_id._do_unreserve()
            line_id.stock_move_id.state = 'draft'
            line_id.stock_move_id.name = ''
            line_id.stock_move_id.origin = ''
            line_id.stock_move_id.reference = ''
            line_id.stock_move_id = False
            line_id.stock_move_id.state = 'approved'
        self.state = 'approved'
    """

    def compute_no_of_move(self):
        for rec in self:
            pick_ids = rec.env['stock.picking'].search([('origin', '=', self.name)])
            move_ids = rec.env['stock.move'].search([('origin', '=', self.name)])
            move_line_ids = rec.env['stock.move.line'].search([('origin', '=', self.name)])
            sale_order_id = rec.env['sale.order'].search([('consignment_order_id', '=', self.id)])
            rec.no_of_pick = len(pick_ids)
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

    """
    def action_view_stock_move_line(self):
        xml_id = 'stock.view_move_line_tree'
        tree_view_id = self.env.ref(xml_id).id
        xml_id = 'stock.view_move_line_form'
        form_view_id = self.env.ref(xml_id).id
        return {
            'name': _('Traceability'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'res_model': 'stock.move.line',
            'domain': [('origin', '=', self.name)],
            'context': {'create': 0, 'edit': 0},
            'type': 'ir.actions.act_window',
        }

    def action_view_stock_move(self):
        xml_id = 'stock.view_move_tree'
        tree_view_id = self.env.ref(xml_id).id
        xml_id = 'stock.view_move_form'
        form_view_id = self.env.ref(xml_id).id
        return {
            'name': _('Stock Move'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'res_model': 'stock.move',
            'domain': [('origin', '=', self.name)],
            'context': {'create': 0, 'edit': 0},
            'type': 'ir.actions.act_window',
        }
    """

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

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('consignment.order') or 'New'
        return super(ConsignmentOrder, self).create(vals)

    def action_waiting_approval(self):
        self.state = 'waiting'

    def action_approval(self):

        pick_vals = self._prepare_picking()
        stock_picking = self.env['stock.picking'].create(pick_vals)
        if stock_picking:
            self._prepare_picking_lines(stock_picking)
            #stock_picking.action_confirm()

        self.state = 'approved'

    """
    def action_confirm(self):
        for line_id in self.line_ids:
            move_vals = self._prepare_move(line_id)
            stock_move = self.env['stock.move'].create(move_vals)
            if stock_move:
                line_id.stock_move_id = stock_move
                stock_move._action_confirm()
        self.state = 'consignment'
    

    def _prepare_move(self, line_id):
        #location_id = self.env.ref('stock.stock_location_stock').id
        #location_dest_id = self.warehouse_id.consignment_location_id.id or self.warehouse_id.id

        #location_id = self.location_id.id
        #location_dest_id = self.location_dest_id.id

        first_rule = self.route_id.rule_ids[:1]

        if not first_rule:
            raise ValidationError(_("No se encontró ninguna regla en la ruta seleccionada."))

        location_id = first_rule.location_src_id.id
        location_dest_id = first_rule.location_dest_id.id

        move_lines = []
        if line_id.show_details:
            for line_lot in line_id.consignment_lot_ids:
                vals = {
                    'product_id': line_id.product_id.id,
                    'lot_id': line_lot.lot_id.id,
                    'quantity': line_lot.quantity,  # bypass reservation here
                    'product_uom_id': line_lot.uom_id.id,
                    'quantity': line_lot.quantity,
                    'origin': self.name,
                    'reference': self.name,
                    'location_id': location_id,
                    'location_dest_id': location_dest_id,
                    'owner_id': self.partner_id.id,
                }
                move_lines.append((0, 0, vals))
        else:
            vals = {
                'product_id': line_id.product_id.id,
                'quantity': line_id.quantity,  # bypass reservation here
                'product_uom_id': line_id.product_id.uom_id.id,
                'quantity': line_id.quantity,
                'origin': self.name,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'owner_id': self.partner_id.id,
                'reference': self.name,
            }
            move_lines.append((0, 0, vals))

        move_vals = {
            'product_id': line_id.product_id.id,
            'product_uom': line_id.product_id.uom_id.id,
            'product_uom_qty': line_id.quantity,
            'date': self.date,
            'name': self.name,
            'origin': self.name,
            'move_line_ids': move_lines,
            'reference': self.name,
            'company_id': self.company_id.id,
            'restrict_partner_id': self.partner_id.id,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
        }
        return move_vals
    
    """

    def action_confirm(self):
        """
        pick_vals = self._prepare_picking()
        stock_picking = self.env['stock.picking'].create(pick_vals)
        if stock_picking:
            self._prepare_picking_lines(stock_picking)
            stock_picking.action_confirm()
        """
        for rec in self:
            rec.state = 'consignment'

            stock_picking = self.env['stock.picking'].search([
                ('origin', '=', rec.name),
                ('state', '!=', 'done') 
            ], limit=1)

            if stock_picking:
                #stock_picking.button_validate()

                raise UserError("No se ha validado la transferencia que ingresa el producto a la ubicación de consignación, vefique en inventario antes de confirmar.")

                stock_picking_to_delete = self.env['stock.picking'].search([
                    ('origin', 'like', 'SC-'),
                    ('state', '=', 'assigned'),
                    ('origin', '=', stock_picking.origin)
                ], limit=1)

                if stock_picking_to_delete:
                    stock_picking_to_delete.unlink()

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
                    'location_id': stock_picking.location_id.id,
                    'location_dest_id': stock_picking.location_dest_id.id,
                    'name': self.name,
                }))
        
        #stock_picking.write({'move_line_ids': move_lines})
        stock_picking.write({'move_ids_without_package': move_lines})

class ConsignmentOrderLine(models.Model):
    _name = "consignment.order.line"
    _rec_name = 'product_id'

    consignment_order_id = fields.Many2one('consignment.order', 'Consignment Order')
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

    """
    @api.model
    def create(self, vals):
        if vals.get('product_id'):
            product = self.env['product.product'].browse(vals['product_id'])
            vals['product_price'] = product.lst_price
        return super(ConsignmentOrderLine, self).create(vals)
    """

    """
    @api.model
    def create(self, vals):
        if vals.get('product_id'):
            product = self.env['product.product'].browse(vals['product_id'])
            consignment_order = self.env['consignment.order'].browse(vals.get('consignment_order_id'))

            if not consignment_order:
                raise ValidationError(_("No se encontró una orden de consignación válida."))

            partner = consignment_order.partner_id

            if partner.property_product_pricelist:
                pricelist = partner.property_product_pricelist
                # Con _get_product_price se obtiene el precio de la tarifa
                price = pricelist._get_product_price(product, 1.0, partner)
                vals['product_price'] = price
            else:
                vals['product_price'] = product.lst_price

        return super(ConsignmentOrderLine, self).create(vals)
    """

    @api.model
    def create(self, vals):
        if vals.get('product_id') and vals.get('consignment_order_id'):
            product = self.env['product.product'].browse(vals['product_id'])
            consignment_order = self.env['consignment.order'].browse(vals['consignment_order_id'])
            partner = consignment_order.partner_id

            if not partner:
                raise UserError(_("No se encontró un contacto válido para la orden de consignación."))

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

#ANADIR FUNCIONALIDAD AL BUSCAR VARIANTES
class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if name:
            products = self.search([('default_code', operator, name)] + args, limit=limit)
            if products:
                product_tmpl_ids = products.mapped('product_tmpl_id')
                variants = self.search([('product_tmpl_id', 'in', product_tmpl_ids.ids)], limit=limit)
                return variants.name_get()
        return super(ProductProduct, self).name_search(name, args=args, operator=operator, limit=limit)
