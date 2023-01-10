from odoo import fields, models, api
import logging
import pprint
import json

_logger = logging.getLogger("prestashop")


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    prestashop_attribute_value_id = fields.Char("Prestashop Attribute ID")


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    prestashop_attribute_id = fields.Char("Prestashop Attribute ID")

    def create_attribute_value(self, attribute_associations=False, prestashop_store_id=False, warehouse_id=False,
                               product_operation_attribute_id=False):
        if attribute_associations:
            for attribute_association in attribute_associations:
                attribute_association_id = attribute_association.get('id')
                api_operation = "http://%s@%s/api/product_option_values/?output_format=JSON&display=full&filter[id]=[%s]" % (
                    prestashop_store_id and prestashop_store_id.prestashop_api_key,
                    prestashop_store_id and prestashop_store_id.prestashop_api_url, attribute_association_id)
                try:
                    response_status, response_data = prestashop_store_id.send_get_request_from_odoo_to_prestashop(
                        api_operation)
                    if isinstance(response_data, str):
                        response_data = eval(response_data)
                    product_value_options = response_data.get('product_option_values')
                    if product_value_options:
                        _logger.info("prestashop Get Product Response : {0}".format(response_data))
                        for product_value_option in product_value_options:
                            prestashop_attribute_value_id = product_value_option.get('id')
                            if isinstance(product_value_options, list):
                                attribute_name = product_value_option.get('name')[0].get('value')
                            else:
                                attribute_name = product_value_option.get('name')
                            attribute_value_id = self.env['product.attribute.value'].search(
                                [('prestashop_attribute_value_id', '=', prestashop_attribute_value_id)])
                            if not attribute_value_id:
                                attribute_value_id = self.env['product.attribute.value'].create({
                                    'name': attribute_name,
                                    'attribute_id': self.id,
                                    'prestashop_attribute_value_id': prestashop_attribute_value_id
                                })
                                process_message = "%s : Attribute Value Created!" % (attribute_name)
                                prestashop_store_id.create_prestashop_operation_detail('product_attribute', 'import',
                                                                                       pprint.pformat(api_operation),
                                                                                       pprint.pformat(
                                                                                           product_value_option),
                                                                                       product_operation_attribute_id,
                                                                                       False, process_message)

                            else:
                                attribute_value_id.attribute_id = self.id
                                process_message = "%s : Already Exist In Odoo!" % (attribute_name)
                                prestashop_store_id.create_prestashop_operation_detail('product_attribute', 'import',
                                                                                       pprint.pformat(api_operation),
                                                                                       pprint.pformat(
                                                                                           product_value_option),
                                                                                       product_operation_attribute_id,
                                                                                       True, process_message)
                        product_operation_attribute_id and product_operation_attribute_id.write(
                            {'prestashop_message': "Process Completed"})
                        _logger.info("Import Product Process Completed ")
                    else:
                        _logger.info(
                            "[ERROR] Attribute Value {}".format(response_data))
                        process_message = "[ERROR] Attribute Value {0}".format(response_data)
                        prestashop_store_id.create_prestashop_operation_detail('product_attribute', 'import',
                                                                               pprint.pformat(api_operation),
                                                                               pprint.pformat(response_data),
                                                                               product_operation_attribute_id, True,
                                                                               process_message)
                except Exception as e:
                    product_process_message = "Process Is Not Completed Yet! %s" % (e)
                    _logger.info("Getting an Error In Import Product Attribute Response {}".format(e))
                    process_message = "[Exception] Import Product Attribute {}".format(e)
                    prestashop_store_id.create_prestashop_operation_detail('product_attribute', 'import',
                                                                           pprint.pformat(api_operation),
                                                                           pprint.pformat(response_data),
                                                                           product_operation_attribute_id,
                                                                           True, process_message)
                product_operation_attribute_id and product_operation_attribute_id.write(
                    {'prestashop_message': "Process Completed Successfully"})
                self._cr.commit()

    def prestashop_to_odoo_import_product_attribute(self, warehouse_id=False, prestashop_store_id=False):
        req_data = False
        product_process_message = "Process Completed Successfully!"
        product_operation_attribute_id = self.env['prestashop.operation']
        if not product_operation_attribute_id:
            product_operation_attribute_id = prestashop_store_id.create_prestashop_operation('product_attribute',
                                                                                             'import',
                                                                                             prestashop_store_id,
                                                                                             'Processing...')
        self._cr.commit()
        try:
            api_operation = "http://%s@%s/api/product_options/?output_format=JSON&display=full" % (
                prestashop_store_id and prestashop_store_id.prestashop_api_key,
                prestashop_store_id and prestashop_store_id.prestashop_api_url)

            response_status, response_data = prestashop_store_id.send_get_request_from_odoo_to_prestashop(api_operation)
            product_options = response_data.get('product_options')
            if product_options:
                _logger.info("prestashop Get Product Response : {0}".format(response_data))
                for product_option in product_options:
                    group_type = product_option.get('group_type')
                    prestashop_attribute_id = product_option.get('id')

                    if product_option.get('name') and isinstance(product_option.get('name'), list):
                        attribute_name = product_option.get('name')[0].get('value')
                    else:
                        attribute_name = product_option.get('name')
                    attribute_associations = product_option.get('associations') and product_option.get(
                        'associations').get('product_option_values')
                    attribute_id = self.search([('prestashop_attribute_id', '=', prestashop_attribute_id)])

                    # create attribute
                    if not attribute_id:
                        attribute_id = self.create({'name': attribute_name, 'display_type': group_type,
                                                    'prestashop_attribute_id': prestashop_attribute_id})
                        process_message = "%s : Attribute Created!" % (attribute_name)
                        prestashop_store_id.create_prestashop_operation_detail('product_attribute', 'import',
                                                                               api_operation,
                                                                               product_option,
                                                                               product_operation_attribute_id,
                                                                               False, process_message)
                    # update attribute
                    else:
                        process_message = "%s : Attribute already available in odoo!" % (attribute_name)
                        prestashop_store_id.create_prestashop_operation_detail('product_attribute', 'import',
                                                                               api_operation,
                                                                               product_option,
                                                                               product_operation_attribute_id,
                                                                               True, process_message)
                    # create attribute value
                    if attribute_id:
                        attribute_id.create_attribute_value(attribute_associations, prestashop_store_id, warehouse_id,
                                                            product_operation_attribute_id)
                product_operation_attribute_id and product_operation_attribute_id.write(
                    {'prestashop_message': "Process Completed Successfully"})
                _logger.info("Import Product Process Completed ")
            else:
                _logger.info("Getting an Error In Import Product Response {}".format(response_data))
                response_data = response_data.content
                process_message = "Getting an Error In Import Product Attribute Response".format(response_data)
                prestashop_store_id.create_prestashop_operation_detail('product_attribute', 'import', req_data,
                                                                       response_data,
                                                                       product_operation_attribute_id, True,
                                                                       process_message)
        except Exception as e:
            product_process_message = "Process Is Not Completed Yet! %s" % (e)
            _logger.info("Getting an Error In Import Product Attribute Response {}".format(e))
            process_message = "Getting an Error In Import Product Attribute Response {}".format(e)
            prestashop_store_id.create_prestashop_operation_detail('product_attribute', 'import', response_data,
                                                                   product_process_message,
                                                                   product_operation_attribute_id, True,
                                                                   process_message)
        product_operation_attribute_id and product_operation_attribute_id.write(
            {'prestashop_message': product_process_message})
        self._cr.commit()
