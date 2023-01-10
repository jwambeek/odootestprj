from odoo import models, fields, api
import datetime


class prestashopOperation(models.Model):
    _name = "prestashop.operation"
    _order = 'id desc'
    _inherit = ['mail.thread']

    name = fields.Char("Name")
    prestashop_operation = fields.Selection([('account', 'Account'),
                                             ('product', 'Product'),
                                             ('customer', 'Customer'),
                                             ('product_attribute', 'Product Attribute'),
                                             ('product_variant', 'Product Variant'),
                                             ('order', 'Order'),
                                             ('product_category', 'Product Category'),
                                             ('stock', 'Stock')
                                             ], string="prestashop Operation")
    prestashop_operation_type = fields.Selection([('export', 'Export'),
                                                  ('import', 'Import'),
                                                  ('update', 'Update'),
                                                  ('delete', 'Cancel / Delete')], string="prestashop Operation Type")
    company_id = fields.Many2one("res.company", "Company")
    operation_ids = fields.One2many("prestashop.operation.details", "operation_id", string="Operation")
    prestashop_store_id = fields.Many2one('prestashop.store.details', string="prestashop Configuration")
    prestashop_message = fields.Char("Message")

    @api.model
    def create(self, vals):
        sequence = self.env.ref("odoo_prestashop_integration.seq_prestashop_operation_detail")
        name = sequence and sequence.next_by_id() or '/'
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        if type(vals) == dict:
            vals.update({'name': name, 'company_id': company_id})
        return super(prestashopOperation, self).create(vals)


class prestashopOperationDetail(models.Model):
    _name = "prestashop.operation.details"
    _rec_name = 'operation_id'
    _order = 'id desc'

    operation_id = fields.Many2one("prestashop.operation", string="prestashop Operation")
    prestashop_operation = fields.Selection([('account', 'Account'),
                                             ('product', 'Product'),
                                             ('customer', 'Customer'),
                                             ('product_attribute', 'Product Attribute'),
                                             ('product_variant', 'Product Variant'),
                                             ('order', 'Order'),
                                             ('product_category', 'Product Category'),
                                             ('stock', 'Stock')
                                             ], string="Operation")
    prestashop_operation_type = fields.Selection([('export', 'Export'),
                                                  ('import', 'Import'),
                                                  ('update', 'Update'),
                                                  ('delete', 'Cancel / Delete')], string="prestashop operation Type")

    company_id = fields.Many2one("res.company", "Company")
    prestashop_request_message = fields.Text("Request Message", copy=False)
    prestashop_response_message = fields.Text("Response Message", copy=False)
    fault_operation = fields.Boolean("Fault Operation", default=False)
    process_message = fields.Char("Message")

    @api.model
    def create(self, vals):
        if type(vals) == dict:
            operation_id = vals.get('operation_id')
            operation = operation_id and self.env['prestashop.operation'].browse(operation_id) or False
            company_id = operation and operation.company_id.id or self.env.user.company_id.id
            vals.update({'company_id': company_id})
        return super(prestashopOperationDetail, self).create(vals)
