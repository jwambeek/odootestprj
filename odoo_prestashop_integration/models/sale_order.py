from odoo import fields, models, api
import logging
import pprint
_logger = logging.getLogger("prestashop")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    prestashop_order_id = fields.Char("prestashop Order ID", copy=False)
    prestashop_reference = fields.Char("prestashop Reference", copy=False)
    prestashop_order_imported = fields.Boolean(default=False, string="prestashop Order ID", copy=False)
    prestashop_store_id = fields.Many2one('prestashop.store.details', string="Prestashop Store")

    def create_sales_order_from_prestashop(self, vals):
        sale_order = self.env['sale.order']
        order_vals = {
            'company_id': vals.get('company_id'),
            'partner_id': vals.get('partner_id'),
            'partner_invoice_id': vals.get('partner_invoice_id'),
            'partner_shipping_id': vals.get('partner_shipping_id'),
            'warehouse_id': vals.get('warehouse_id'),
        }
        new_record = sale_order.new(order_vals)
        new_record.onchange_partner_id()
        order_vals = sale_order._convert_to_write({name: new_record[name] for name in new_record._cache})
        new_record = sale_order.new(order_vals)
        new_record.onchange_partner_shipping_id()
        order_vals = sale_order._convert_to_write({name: new_record[name] for name in new_record._cache})
        order_vals.update({
            'company_id': vals.get('company_id'),
            'picking_policy': 'direct',
            'partner_invoice_id': vals.get('partner_invoice_id'),
            'partner_shipping_id': vals.get('partner_shipping_id'),
            'partner_id': vals.get('partner_id'),
            'date_order': vals.get('date_order', ''),
            'state': 'draft',
            'carrier_id': vals.get('carrier_id', '')
        })
        return order_vals

    def create_sale_order_line_from_prestashop(self, vals):
        sale_order_line = self.env['sale.order.line']
        order_line = {
            'order_id': vals.get('order_id'),
            'product_id': vals.get('product_id', ''),
            'company_id': vals.get('company_id', ''),
            'name': vals.get('description'),
            'product_uom': vals.get('product_uom')
        }
        new_order_line = sale_order_line.new(order_line)
        new_order_line.product_id_change()
        order_line = sale_order_line._convert_to_write({name: new_order_line[name] for name in new_order_line._cache})
        order_line.update({
            'order_id': vals.get('order_id'),
            'product_uom_qty': vals.get('order_qty', 0.0),
            'price_unit': vals.get('price_unit', 0.0),
            'discount': vals.get('discount', 0.0),
            'state': 'draft',
        })
        return order_line

    def prestashop_to_odoo_import_orders(self, warehouse_id=False, prestashop_store_id=False):
        req_data = False
        order_id = self.env['sale.order']
        order_process_message = "Process Completed Successfully!"
        order_operation_id = self.env['prestashop.operation']
        if not order_operation_id:
            order_operation_id = prestashop_store_id.create_prestashop_operation('order', 'import', prestashop_store_id,
                                                                                 'Processing...')
        self._cr.commit()
        try:
            if prestashop_store_id.import_single_data:
                order_api_operation = "http://%s@%s/api/orders/?output_format=JSON&resource=orders&filter[id]=[%s]&display=full" % (
                    prestashop_store_id and prestashop_store_id.prestashop_api_key,
                    prestashop_store_id and prestashop_store_id.prestashop_api_url, prestashop_store_id.prestashop_single_data_id,)
            else:
                order_api_operation = "http://%s@%s/api/orders/?output_format=JSON&resource=orders&filter[id]=[%s,%s]&display=full" % (
                    prestashop_store_id and prestashop_store_id.prestashop_api_key,
                    prestashop_store_id and prestashop_store_id.prestashop_api_url, prestashop_store_id.start_range,
                    prestashop_store_id.end_range)
            order_response_status, order_response_data = prestashop_store_id.send_get_request_from_odoo_to_prestashop(
                order_api_operation)

            _logger.info("prestashop Get Order Response : {0}".format(order_response_data))
            if order_response_status:
                orders = order_response_data and order_response_data.get('orders')
                for order in orders:
                    try:
                        o_id = order.get('id')
                        country_id = self.env['res.country']
                        state_id = self.env['res.country.state']
                        res_partner_id = self.env['res.partner']
                        address1 = ""
                        phone = ""
                        city = ""
                        postcode = ""
                        order_existing_id = self.env['sale.order'].search(
                            [('prestashop_order_id', '=', o_id)], limit=1)
                        if not order_existing_id:
                            reference = order.get('reference')
                            date_add = order.get("date_add")

                            # Identify customer address
                            address_value = order.get('id_address_delivery')
                            address_api_operation = "http://%s@%s/api/addresses/?output_format=JSON&resource=addresses&filter[id]=[%s]&display=full" % (
                                prestashop_store_id and prestashop_store_id.prestashop_api_key,
                                prestashop_store_id and prestashop_store_id.prestashop_api_url, address_value)
                            address_response_status, address_response_data = prestashop_store_id.send_get_request_from_odoo_to_prestashop(
                                address_api_operation)
                            if isinstance(address_response_data, str):
                                address_response_data = eval(address_response_data)
                            address_preastashop_response_data = address_response_data.get('addresses')
                            if address_preastashop_response_data:
                                for address_data in address_preastashop_response_data:
                                    address1 = address_data.get('address1')
                                    postcode = address_data.get('postcode')
                                    phone = address_data.get('phone')
                                    city = address_data.get('city')
                                    # state and country identify
                                    id_country = address_data.get('id_country')
                                    id_state = address_data.get('id_state')
                                    country_api_operation = "http://%s@%s/api/countries/?output_format=JSON&resource=countries&filter[id]=[%s]&display=full" % (
                                        prestashop_store_id and prestashop_store_id.prestashop_api_key,
                                        prestashop_store_id and prestashop_store_id.prestashop_api_url, id_country)
                                    country_response_status, country_response_data = prestashop_store_id.send_get_request_from_odoo_to_prestashop(
                                        country_api_operation)
                                    if isinstance(country_response_data, str):
                                        country_response_data = eval(country_response_data)
                                    country_list = country_response_data.get('countries')
                                    if country_list:
                                        for country_dict in country_list:
                                            country_code = country_dict.get('iso_code')
                                            country_id = country_id.search(
                                                [('code', '=', country_code)],
                                                limit=1)
                                    state_api_operation = "http://%s@%s/api/states/?output_format=JSON&resource=states&filter[id]=[%s]&display=full" % (
                                        prestashop_store_id and prestashop_store_id.prestashop_api_key,
                                        prestashop_store_id and prestashop_store_id.prestashop_api_url, id_state)
                                    state_response_status, state_response_data = prestashop_store_id.send_get_request_from_odoo_to_prestashop(
                                        state_api_operation)
                                    if isinstance(state_response_data, str):
                                        state_response_data = eval(state_response_data)
                                    state_list = state_response_data.get('states')
                                    if state_list:
                                        for state_dict in state_list:
                                            state_code = state_dict.get('iso_code')
                                            state_id = state_id.search([('code', '=', state_code)], limit=1)

                            # Found Customer
                            id_customer = order.get('id_customer')
                            res_partner_id = res_partner_id.search([('prestashop_customer_id', '=', id_customer)], limit=1)
                            if not res_partner_id:
                                customer_api_operation = "http://%s@%s/api/customers/?output_format=JSON&resource=customers&filter[id]=[%s]&display=full" % (
                                    prestashop_store_id and prestashop_store_id.prestashop_api_key,
                                    prestashop_store_id and prestashop_store_id.prestashop_api_url, id_customer)
                                customer_response_status, customer_response_data = prestashop_store_id.send_get_request_from_odoo_to_prestashop(
                                    customer_api_operation)
                                if isinstance(customer_response_data, str):
                                    customer_response_data =  eval(customer_response_data)
                                customer_data = customer_response_data.get('customers')
                                if customer_data:
                                    for customer_dict in customer_data:
                                        lastname = customer_dict.get('lastname')
                                        firstname = customer_dict.get('firstname')
                                        email = customer_dict.get('email')
                                        customer_name = "%s %s" % (firstname, lastname)
                                        partner_vals = {
                                            'name': customer_name,
                                            'phone': phone,
                                            'email': email,
                                            'street': address1,
                                            'city': city,
                                            'zip': postcode,
                                            'country_id': country_id and country_id.id,
                                            'state_id': state_id and state_id.id,
                                            'prestashop_customer_id': id_customer,
                                            'prestashop_customer_url': customer_api_operation
                                        }
                                        res_partner_id = self.env['res.partner'].create(partner_vals)
                                        res_partner_id.prestashop_store_id = prestashop_store_id and prestashop_store_id.id
                                        _logger.info("Customer Created : {0}".format(res_partner_id.name))
                                        customer_message = "%s Customer Created" % (res_partner_id.name)
                                        self.prestashop_store_id.create_prestashop_operation_detail('order', 'import',
                                                                                                    customer_api_operation,
                                                                                                    customer_response_data,
                                                                                                    order_operation_id,
                                                                                                    False, customer_message)

                            if res_partner_id:
                                vals = {
                                    'name': "%s_%s" % (o_id, reference),
                                    'type': 'delivery',
                                    'parent_id': res_partner_id.id
                                }

                                vals.update({'partner_id': res_partner_id.id,
                                             'partner_invoice_id': res_partner_id.id,
                                             'partner_shipping_id': res_partner_id.id,
                                             'date_order': date_add,
                                             'carrier_id': '',
                                             'company_id': self.env.user.company_id.id,
                                             'warehouse_id': warehouse_id.id,
                                             'carrierCode': '',
                                             'serviceCode': '',
                                             })
                                order_vals = self.create_sales_order_from_prestashop(vals)
                                order_vals.update({'prestashop_order_id': o_id, 'prestashop_reference': reference,
                                                   'prestashop_order_imported': True})

                                try:
                                    order_id = self.env['sale.order'].create(order_vals)
                                    order_id.prestashop_store_id = prestashop_store_id and prestashop_store_id.id
                                    order_message = "{} : Order Created".format(order_id.name)
                                    self.prestashop_store_id.create_prestashop_operation_detail('order', 'import',
                                                                                                order_api_operation,
                                                                                                order_vals,
                                                                                                order_operation_id,
                                                                                                False,
                                                                                                order_message)

                                except Exception as e:
                                    process_message = "Getting an Error In Create Order procecss {}".format(e)
                                    self.prestashop_store_id.create_prestashop_operation_detail('order', 'import', '', '',
                                                                                                order_operation_id,
                                                                                                True,
                                                                                                process_message)

                            # Order Line Creation Part
                            order_rows = order.get('associations') and order.get('associations').get('order_rows')
                            if order_rows and order_id:
                                if isinstance(order_rows, dict):
                                    order_rows = [order_rows]
                                for order_row in order_rows:
                                    p_id = order_row.get('product_id')
                                    product_attribute_id = order_row.get('product_attribute_id',False)
                                    product_price = order_row.get('product_price')
                                    product_quantity = order_row.get('product_quantity')
                                    product_name = order_row.get('product_name')
                                    if product_attribute_id:
                                        product_detail_id = self.env['prestashop.product.detail'].search(
                                            [('product_combination_id', '=', product_attribute_id),
                                             ('prestashop_store_id', '=', prestashop_store_id.id)], limit=1)
                                        product_id = product_detail_id and product_detail_id.product_id
                                        # product_id = self.env['product.product'].search([('id', '=', '2029')])
                                    if not product_id:
                                        product_detail_id = self.env['prestashop.product.detail'].search(
                                            [('prestashop_product_id', '=', p_id),
                                             ('prestashop_store_id', '=', prestashop_store_id.id)], limit=1)
                                        product_id = product_detail_id and product_detail_id.product_id
                                        # product_id = self.env['product.product'].search([('id', '=', '2029')])

                                    if product_id:
                                        order_line_vals = {'product_id': product_id.id, 'price_unit': product_price,
                                                           'order_qty': product_quantity,
                                                           'order_id': order_id and order_id.id,
                                                           'description': product_name,
                                                           'company_id': self.env.user.company_id.id}
                                        order_line = self.create_sale_order_line_from_prestashop(order_line_vals)
                                        order_line = self.env['sale.order.line'].create(order_line)
                                        _logger.info("Sale Order line Created : {}".format(
                                            order_line and order_line.product_id and order_line.product_id.name))
                                        response_msg = "Sale Order line Created For Order  : {0}".format(
                                            order_id.name)
                                        self.prestashop_store_id.create_prestashop_operation_detail('order', 'import', '',
                                                                                                    pprint.pformat(order_row),
                                                                                                    order_operation_id,
                                                                                                    False, response_msg)
                                    else:
                                        response_msg = "Product Is Not Available In Odoo  : {0} : {1} : {2}".format(
                                            product_name, o_id, reference)
                                        self.prestashop_store_id.create_prestashop_operation_detail('order', 'import', '',
                                                                                                    pprint.pformat(order_row),
                                                                                                    order_operation_id,
                                                                                                    True, response_msg)

                        else:
                            _logger.info("%s : %s : Order Already Exist in Odoo" % (
                            order_existing_id and order_existing_id.name, o_id))
                            order_message = "%s : %s : Order Already Exist in Odoo" % (
                            order_existing_id and order_existing_id.name, o_id)
                            self.prestashop_store_id.create_prestashop_operation_detail('order', 'import',
                                                                                        order_api_operation,
                                                                                        order, order_operation_id,
                                                                                        True, order_message)

                        self._cr.commit()
                        order_operation_id and order_operation_id.write(
                            {'prestashop_message': order_process_message})
                        _logger.info("Import Product Process Completed ")
                    except Exception as e:
                        _logger.info("Getting an Error In Import Order Response {}".format(e))
                        process_message = "Getting An Error In Import Order Response".format(e)
                        self.prestashop_store_id.create_prestashop_operation_detail('order', 'import', '', '',
                                                                                    order_operation_id, True,
                                                                                    process_message)
            else:
                process_message = "[Error] order data not found in response "
                self.prestashop_store_id.create_prestashop_operation_detail('order', 'import', order_api_operation,
                                                                            order_response_data, order_operation_id,
                                                                            True, process_message)
        except Exception as e:
            _logger.info("Getting an Error In Import Order Response {}".format(e))
            process_message = "Getting an Error In Import Order Response {}".format(e)
            self.prestashop_store_id.create_prestashop_operation_detail('order', 'import', order_response_data,
                                                                        process_message, order_operation_id,
                                                                        True, process_message)
        order_operation_id and order_operation_id.write({'prestashop_message': order_process_message})
        self._cr.commit()
