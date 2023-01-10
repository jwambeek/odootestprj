import base64
import pprint
import logging
import datetime
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from requests import request

_logger = logging.getLogger("prestashop")


class prestashopCredentailDetails(models.Model):
    _name = "prestashop.store.details"

    name = fields.Char("Name", required=True, help="prestashop Store Configuration", copy=False)
    prestashop_api_key = fields.Char("Prestashop API Key", required=True, copy=False,
                                     help="Go in the PrestaShop back office, open the “Web service” page under the “Advanced Parameters” menu, and then choose “Yes” for the “Enable PrestaShop Webservice” option.")
    prestashop_api_url = fields.Char(string='Prestashop API URL', default="Your Store URL", copy=False)

    warehouse_id = fields.Many2one("stock.warehouse", "Warehouse")
    start_range = fields.Integer(string="Order ID Starting Range", help="Starting range for order import process",
                                 default=1)
    end_range = fields.Integer(string="Order ID Ending Range", help="Ending range for order import process",
                               default=100)
    import_single_data = fields.Boolean(string='Import Product, Order Using ID')
    prestashop_single_data_id = fields.Integer(string='Prestashop ID')

    # kanban field
    image = fields.Binary(string="Image", help="Select Image.")
    image_medium = fields.Binary(string="Medium Size Image", related="image", store=True, )
    image_small = fields.Binary(string="Large Size Image", related="image", store=True, )
    color = fields.Integer(string='Color Index', help="select color")
    total_customer_count = fields.Integer(string="Count total number of customer", compute='_compute_total_number')
    total_order_count = fields.Integer(string="Count total number of order", compute='_compute_total_number')
    total_product_count = fields.Integer(string="Count total number of product", compute='_compute_total_number')

    _sql_constraints = [
        ('prestashop_name_unique', 'unique(name)', "Instance name already exists !"),
    ]

    # @api.onchange('prestashop_api_url')
    # def onchange_prestashop_api_url(self):
    #     if 'https://' in self.prestashop_api_url:
    #         self.prestashop_api_url = self.prestashop_api_url.replace('https://', '')
    #     elif 'http://' in self.prestashop_api_url:
    #         self.prestashop_api_url = self.prestashop_api_url.replace('http://', '')

    @api.model
    def create(self, vals):
        result = super(prestashopCredentailDetails, self).create(vals)
        return result

    def write(self, vals):
        res = super(prestashopCredentailDetails, self).write(vals)
        return res

    def _compute_total_number(self):
        for market_id in self.search([]):
            market_id.total_product_count = len(
                self.env['product.template'].search([('prestashop_store_id', '=', market_id.id)]))
            market_id.total_order_count = len(
                self.env['sale.order'].search([('prestashop_store_id', '=', market_id.id)]))
            market_id.total_customer_count = len(
                self.env['res.partner'].search([('prestashop_store_id', '=', market_id.id)]))

    def prestashop_open_form_view(self):
        form_id = self.env.ref('odoo_prestashop_integration.view_form_prestashop_store_details')
        action = {
            'name': _('Prestashop Store Configuration'),
            'view_id': False,
            'res_model': 'prestashop.store.details',
            'context': self._context,
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(form_id.id, 'form')],
            'type': 'ir.actions.act_window',
        }
        return action

    def create_prestashop_operation(self, operation, operation_type, prestashop_store_id, log_message):
        vals = {
            'prestashop_operation': operation,
            'prestashop_operation_type': operation_type,
            'prestashop_store_id': prestashop_store_id and prestashop_store_id.id,
            'prestashop_message': log_message,
        }
        operation_id = self.env['prestashop.operation'].create(vals)
        return operation_id

    def create_prestashop_operation_detail(self, operation, operation_type, req_data, response_data, operation_id,
                                           fault_operation=False, process_message=False):
        prestashop_operation_details_obj = self.env['prestashop.operation.details']
        vals = {
            'prestashop_operation': operation,
            'prestashop_operation_type': operation_type,
            'prestashop_request_message': pprint.pformat(req_data),
            'prestashop_response_message': pprint.pformat(response_data),
            'operation_id': operation_id.id,
            'fault_operation': fault_operation,
            'process_message': process_message,
        }
        operation_detail_id = prestashop_operation_details_obj.create(vals)
        return operation_detail_id

    def send_get_request_from_odoo_to_prestashop(self, api_operation=False):
        try:
            _logger.info("Prestashop API Request Data : %s" % (api_operation))
            data = "%s" % (self.prestashop_api_key)
            encode_data = base64.b64encode(data.encode("utf-8"))
            authrization_data = "Basic %s" % (encode_data.decode("utf-8"))
            # headers = {"Authorization": "%s" % authrization_data}
            headers = {"ws_key": "%s" % self.prestashop_api_key}
            response_data = request(method='GET', url=api_operation, params=headers)
            if response_data.status_code in [200, 201]:
                result = response_data.json()
                _logger.info("Prestashop API Response Data : %s" % (result))
                return True, result
            else:
                _logger.info("Prestashop API Response Data : %s" % (response_data.text))
                return False, response_data.text
        except Exception as e:
            _logger.info("Prestashop API Response Data : %s" % (e))
            return False, e

    def import_products_from_prestashop(self):
        product_obj = self.env['product.template']
        product_obj.prestashop_to_odoo_import_product(self.warehouse_id, self)
        return {
            'effect': {
                'fadeout': 'slow',
                'message': "Product Imported Successfully.",
                'img_url': '/web/static/src/img/smile.svg',
                'type': 'rainbow_man',
            }
        }

    def import_product_stock_from_prestashop(self):
        product_stock_obj = self.env['stock.quant']
        product_stock_obj.prestashop_to_odoo_import_stock_inventory(self.warehouse_id, self)
        return {
            'effect': {
                'fadeout': 'slow',
                'message': "Product Imported Successfully.",
                'img_url': '/web/static/src/img/smile.svg',
                'type': 'rainbow_man',
            }
        }

    def import_categories_from_prestashop(self):
        product_category_obj = self.env['product.category']
        product_category_obj.prestashop_to_odoo_import_product_categories(self.warehouse_id, self)
        return {
            'effect': {
                'fadeout': 'slow',
                'message': "Product Categories Imported Successfully.",
                'img_url': '/web/static/src/img/smile.svg',
                'type': 'rainbow_man',
            }
        }

    def import_order_from_prestashop(self):
        sale_order_obj = self.env['sale.order']
        sale_order_obj.prestashop_to_odoo_import_orders(self.warehouse_id, self)
        self.start_range = self.end_range
        self.end_range = self.end_range + 100
        return {
            'effect': {
                'fadeout': 'slow',
                'message': "Order Imported Successfully.",
                'img_url': '/web/static/src/img/smile.svg',
                'type': 'rainbow_man',
            }
        }
    # crone job for import sale order
    def import_order_from_ps_cron_job(self):
        for store in self.search([]):
            store.import_order_from_prestashop()

    def import_product_attribute_from_prestashop(self):
        product_attribute_obj = self.env['product.attribute']
        product_attribute_obj.prestashop_to_odoo_import_product_attribute(self.warehouse_id, self)
        return {
            'effect': {
                'fadeout': 'slow',
                'message': "Product Attribute Imported Successfully.",
                'img_url': '/web/static/src/img/smile.svg',
                'type': 'rainbow_man',
            }
        }

    def action_view_prestashop_categories(self):
        action = self.env.ref('product.product_category_action_form').read()[0]
        action['domain'] = [('prestashop_category_id', '!=', False)]
        return action

    def action_view_prestashop_product(self):
        action = self.env.ref('sale.product_template_action').read()[0]
        action['domain'] = [('prestashop_product', '!=', False)]
        return action

    def action_view_prestashop_product_detail(self):
        action = self.env.ref('product.product_normal_action_sell').read()[0]
        action['domain'] = [('prestashop_mapping_ids', '!=', False)]
        return action

    def action_prestashop_product_detail(self):
        action = self.env.ref('odoo_prestashop_integration.action_prestashop_product_details').read()[0]
        action['domain'] = [('prestashop_store_id', '=', self.id)]
        action['context'] = {'default_prestashop_store_id': self.id}
        return action

    def action_view_prestashop_customers(self):
        action = self.env.ref('base.action_partner_form').read()[0]
        action['domain'] = [('prestashop_store_id', '=', self.id)]
        action['context'] = {'default_prestashop_store_id': self.id}
        return action

    def action_view_prestashop_orders(self):
        action = self.env.ref('sale.action_quotations_with_onboarding').read()[0]
        action['domain'] = [('prestashop_store_id', '=', self.id)]
        action['context'] = {'default_prestashop_store_id': self.id}
        return action

    def action_view_prestashop_message_detail(self):
        action = self.env.ref('odoo_prestashop_integration.action_prestashop_operation').read()[0]
        action['context'] = {'default_prestashop_store_id': self.id}
        return action

    def remove_unnecessary_log_cron(self, obj_id):
        for process in self.env['prestashop.operation'].search(
                [('prestashop_store_id', '=', obj_id), ('create_date', '<', datetime.now() - timedelta(days=3))]):
            self.env['prestashop.operation.details'].search([('operation_id', '=', process.id)]).unlink()
            process.unlink()

    @api.model
    def create(self, vals):
        res = super(prestashopCredentailDetails, self).create(vals_list=vals)
        cron_val = {
            'name': "%s Remove Unnecessary Log " % (vals.get('name')),
            'model_id': self.env.ref('odoo_prestashop_integration.model_prestashop_store_details').id,
            'state': 'code',
            'code': 'model.remove_unnecessary_log_cron({})'.format(res.id),
            'active': True,
            'user_id': self.env.ref('base.user_root').id,
            "interval_number": 3,
            "interval_type": "days",
            "numbercall": -1

        }
        self.env['ir.cron'].create(cron_val)
        return res
