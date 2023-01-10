from odoo import models, fields, api
from odoo.exceptions import ValidationError
import xml.etree.ElementTree as etree
import requests
import base64


class prestashopProductDetail(models.Model):
    _name = "prestashop.product.detail"

    product_id = fields.Many2one("product.product", "Product")
    prestashop_store_id = fields.Many2one('prestashop.store.details', string="prestashop Store")
    prestashop_product_id = fields.Char("Prestashop Product ID")
    product_combination_id = fields.Char("Prestashop Product Combination ID")
    product_stock_id = fields.Char("Prestashop Product Stock ID")
    qty_available_in_odoo = fields.Float(string="Quantity In Odoo", related='product_id.qty_available')
    product_tmpl_id = fields.Many2one(string="Product Template", related='product_id.product_tmpl_id')
    qty_available_in_prestashop = fields.Float(string="Quantity In Prestashop", default=0.0)

    def auto_export_stock_from_odoo_to_prestashop(self):
        product_detail_ids = self.search([])
        product_detail_ids = product_detail_ids.filtered(
            lambda line_item: line_item.qty_available_in_odoo != line_item.qty_available_in_prestashop)
        operation_id = self.env['prestashop.operation']
        for product_detail_id in product_detail_ids:
            if not operation_id:
                operation_id = product_detail_id.prestashop_store_id.create_prestashop_operation('stock', 'update',
                                                                                product_detail_id.prestashop_store_id, False)
            product_detail_id.export_product_qty_in_prestashop(operation_id)
            self._cr.commit()
        operation_id.write({'prestashop_message': "Process Completed Successfully!"})

    def export_product_qty_in_prestashop(self, operation_id=False):
        operation_id = self.env['prestashop.operation']

        if not operation_id:
            operation_id = self.prestashop_store_id.create_prestashop_operation('stock', 'update',
                                                                                self.prestashop_store_id, False)
        service_root = etree.Element("prestashop")

        request = etree.SubElement(service_root, "stock_available")

        etree.SubElement(request, "id").text = "%s" % (self.product_stock_id)
        etree.SubElement(request, "id_product").text = "%s" % (self.prestashop_product_id)
        etree.SubElement(request, "id_product_attribute").text = "%s" % (self.product_combination_id)
        etree.SubElement(request, "id_shop").text = "1"
        etree.SubElement(request, "quantity").text = "%s" % (int(self.qty_available_in_odoo))
        etree.SubElement(request, "depends_on_stock").text = "0"
        etree.SubElement(request, "out_of_stock").text = "0"
        data = "%s" % (self.prestashop_store_id.prestashop_api_key)
        encode_data = base64.b64encode(data.encode("utf-8"))
        authrization_data = "Basic %s" % (encode_data.decode("utf-8"))
        headers = {"Content-Type": "application/xml", "Authorization": "%s" % authrization_data}
        url = "https://%s@%s/api/stock_availables/?output_format=JSON&resource=stock_availables" % (
            self.prestashop_store_id and self.prestashop_store_id.prestashop_api_key,
            self.prestashop_store_id and self.prestashop_store_id.prestashop_api_url)
        try:
            xml = etree.tostring(service_root)
            response_body = requests.request('PUT', url=url, data=xml, headers=headers)
            if response_body.status_code == 200:
                response_body = response_body.json()
                if int(response_body.get('stock_available').get('quantity')) == int(self.qty_available_in_odoo):
                    update_stock = "%s : %s : %s Stock Updated Successfully" % (
                    self.prestashop_store_id.name, self.product_id.name, self.qty_available_in_odoo)
                    self.prestashop_store_id.create_prestashop_operation_detail('stock', 'update',
                                                                                url,
                                                                                response_body,
                                                                                operation_id,
                                                                                update_stock)
                    self.qty_available_in_prestashop = self.qty_available_in_odoo

            else:
                update_stock = "%s : %s : %s Stock Is Not Updated!!" % (
                    self.prestashop_store_id.name, self.product_id.name, self.qty_available_in_odoo)
                self.prestashop_store_id.create_prestashop_operation_detail('stock', 'update',
                                                                            url,
                                                                            response_body.text,
                                                                            operation_id,
                                                                            True, update_stock)

                raise Warning("%s : %s" % (update_stock, response_body.text))
        except Exception as e:
            update_stock = "%s : %s : %s Stock Is Not Updated!!" % (
                self.prestashop_store_id.name, self.product_id.name, self.qty_available_in_odoo)
            self.prestashop_store_id.create_prestashop_operation_detail('stock', 'update',
                                                                        False,
                                                                        e,
                                                                        operation_id,
                                                                        True, update_stock)
            raise ValidationError(e)
