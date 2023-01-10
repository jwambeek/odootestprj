from odoo import fields, models
import logging


_logger = logging.getLogger("prestashop")


class PrestashopStockInventory(models.Model):
    _inherit = "stock.quant"

    def prestashop_to_odoo_import_stock_inventory(self, warehouse_id=False, prestashop_store_id=False):
        product_process_message = "Process Completed Successfully!"
        self._cr.commit()
        product_detail_ids = self.env['prestashop.product.detail'].search([('id', 'in', (2462,2463))])
        product_operation_id = prestashop_store_id.create_prestashop_operation('stock', 'import',
                                                                               prestashop_store_id,
                                                                               'Processing...')
        try:
            product_ids = []
            for product_detail_id in product_detail_ids:
                _logger.info("Product detail id {}".format(product_detail_id.id))
                if product_detail_id.product_combination_id:
                    api_operation = "http://%s@%s/api/stock_availables/?output_format=JSON&filter[id_product_attribute]=[%s]&display=full" % (
                        prestashop_store_id and prestashop_store_id.prestashop_api_key,
                        prestashop_store_id and prestashop_store_id.prestashop_api_url,
                        product_detail_id.product_combination_id)
                else:
                    api_operation = "http://%s@%s/api/stock_availables/?output_format=JSON&filter[id_product]=[%s]&display=full" % (
                        prestashop_store_id and prestashop_store_id.prestashop_api_key,
                        prestashop_store_id and prestashop_store_id.prestashop_api_url,
                        product_detail_id.prestashop_product_id)
                response_status, response_data = prestashop_store_id.send_get_request_from_odoo_to_prestashop(
                    api_operation)
                if isinstance(response_data, str):
                    response_data = eval(response_data)
                product_stock_inventory = response_data.get('stock_availables')
                if product_stock_inventory:
                    _logger.info("prestashop Get Product Response : {0}".format(response_data))
                    for stock_inventory in product_stock_inventory:
                        quantity = "{}".format(stock_inventory.get('quantity'))
                        if product_detail_id and product_detail_id.product_id.id:
                            product_ids.append(product_detail_id and product_detail_id.product_id.id)
                        else:
                            continue

                        quant_vals = {'product_tmpl_id': product_detail_id.product_id.product_tmpl_id.id,
                                      'location_id': prestashop_store_id.warehouse_id.lot_stock_id.id,
                                      'inventory_quantity': quantity,
                                      'product_id': product_detail_id and product_detail_id.product_id.id,
                                      'quantity': quantity}
                        self.env['stock.quant'].sudo().create(quant_vals)
                        message = "%s [Quantity %s]" % (
                        prestashop_store_id and product_detail_id.product_id.name, quantity)
                        prestashop_store_id.create_prestashop_operation_detail('stock', 'import',
                                                                               api_operation,
                                                                               response_data,
                                                                               product_operation_id,
                                                                               False,
                                                                               message)
                else:
                    process_message = "Import Product Stock Failed %s" % (
                                product_detail_id and product_detail_id.product_id.name)
                    prestashop_store_id.create_prestashop_operation_detail('stock', 'import',
                                                                           api_operation,
                                                                           response_data,
                                                                           product_operation_id,
                                                                           True,
                                                                           process_message)
        except Exception as e:
            _logger.info("Getting an Error In Import Product Stock Response {}".format(e))
            process_message = "Getting an Error In Import Product Stock Response {}".format(e)
            prestashop_store_id.create_prestashop_operation_detail('stock', 'import',
                                                                   api_operation,
                                                                   response_data,
                                                                   product_operation_id,
                                                                   True,
                                                                   process_message)

        product_operation_id and product_operation_id.write({'prestashop_message': product_process_message})
        self._cr.commit()
