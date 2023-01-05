# -*- coding: utf-8 -*-
import base64
import requests
import binascii
import logging
import json
from datetime import datetime
from odoo import models, fields, api
from requests.auth import HTTPBasicAuth
from odoo.exceptions import ValidationError

_logger = logging.getLogger("Correos Express")


class CorreosDeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"
    delivery_type = fields.Selection(selection_add=[("correos_express", "Correos Express")],
                                     ondelete={'correos_express': 'set default'})
    correos_express_carriage = fields.Selection([('P', 'Paid P'), ('D', 'Due D')], string="Carriage")
    correos_express_packaging_id = fields.Many2one('stock.package.type', string="Default Package Type")
    correos_express_product_code = fields.Char("Service Code", help="Provided by Correos Express", default="63")

    def correos_express_rate_shipment(self, order):
        return {'success': True, 'price': 0.0, 'error_message': False, 'warning_message': False}

    def get_correos_express_parcels(self, total_weight=False, packages=False):
        number_of_package = 0
        correos_express_parcels = []
        if packages:
            for package in packages:
                number_of_package = number_of_package + 1
                parcel_dict = {
                    "alto": "{}".format(self.correos_express_packaging_id.height or 0.0),
                    "ancho": "{}".format(self.correos_express_packaging_id.width or 0.0),
                    "kilos": "{}".format(package.shipping_weight),
                    "largo": "{}".format(self.correos_express_packaging_id.packaging_length or 0.0),
                    "orden": "{}".format(number_of_package),
                    "volumen": ""
                }
                correos_express_parcels.append(parcel_dict)
        if total_weight:
            number_of_package = number_of_package + 1
            parcel_dict = {
                "alto": "{}".format(self.correos_express_packaging_id.height or 0.0),
                "ancho": "{}".format(self.correos_express_packaging_id.width or 0.0),
                "kilos": "{}".format(total_weight),
                "largo": "{}".format(self.correos_express_packaging_id.packaging_length or 0.0),
                "orden": "{}".format(number_of_package),
                "volumen": ""
            }
            correos_express_parcels.append(parcel_dict)
        return correos_express_parcels

    def corres_label_request_data(self, pickings):
        """ this method return body data of correos label request"""

        sender_id = pickings.picking_type_id and pickings.picking_type_id.warehouse_id and pickings.picking_type_id.warehouse_id.partner_id
        receiver_id = pickings.partner_id

        # check sender Address
        if not sender_id.zip or not sender_id.city or not sender_id.country_id:
            raise ValidationError("Please Define Proper Sender Address!")

        # check Receiver Address
        if not receiver_id.zip or not receiver_id.city or not receiver_id.country_id:
            raise ValidationError("Please Define Proper Recipient Address!")

        customer_code = self.company_id.correos_express_customer_code
        sender_code = self.company_id.correso_express_sender_code
        current_time = datetime.now()
        package_details = pickings.package_ids
        total_bulk_weight = pickings.weight_bulk
        formatted_time = current_time.strftime("%d%m%Y")
        body_data = {
            "solicitante": "{}".format(customer_code),
            "ref": "{}".format(pickings.name),
            "fecha": "{}".format(formatted_time),
            "codRte": "{}".format(sender_code),
            "nomRte": "{}".format(sender_id.name),
            "dirRte": "{}".format(sender_id.street),
            "pobRte": "{}".format(sender_id.city),
            "codPosNacRte": "{}".format(sender_id.zip),
            "nomDest": "{}".format(receiver_id.name),
            "observac": "{}".format(pickings.note or ""),
            "dirDest": "{}".format(receiver_id.street),
            "pobDest": "{}".format(receiver_id.city),
            "codPosNacDest": "{}".format(receiver_id.zip),
            "contacDest": "{}".format(receiver_id.name),
            "telefDest": "{}".format(receiver_id.phone),
            "EmailDest": "{}".format(receiver_id.email or " "),
            "numBultos": "{}".format(len(pickings.package_ids) + (1 if total_bulk_weight else 0)),
            "kilos": "{}".format(pickings.shipping_weight),
            "producto": "{}".format(self.correos_express_product_code),
            "portes": "{}".format(self.correos_express_carriage),
            "listaBultos": self.get_correos_express_parcels(total_bulk_weight or False, package_details),
            "codDirecDestino": "",
            "listaInformacionAdicional": [
                {
                    "tipoEtiqueta": "1",  # for generate base64 label
                    "creaRecogida": "S"  # If "S" (Yes) carrier will come to sender address to pick package
                }
            ]
        }
        return body_data

    @api.model
    def correos_express_send_shipping(self, pickings):
        if not self.company_id:
            raise ValidationError("Company Is Not Selected In Delivery Method!")
        request_data = self.corres_label_request_data(pickings)
        api_url = self.company_id.correos_express_api_url
        username = self.company_id.correos_express_username
        password = self.company_id.correos_express_password
        headers = {"Content-Type": "application/json"}
        try:
            response_data = requests.post(url=api_url, headers=headers,
                                          auth=HTTPBasicAuth(username=username, password=password),
                                          data=json.dumps(request_data))
            if response_data.status_code in [200, 201]:
                tracking_number = []
                _logger.info("Get Successfully Response From {}".format(api_url))
                response_data = response_data.json()
                if not response_data.get('datosResultado'):
                    raise ValidationError(response_data)
                pickings.correos_express_shipment_number = response_data.get('datosResultado')
                for identify_number in response_data.get('listaBultos'):
                    tracking_number.append(identify_number.get('codUnico'))
                _logger.info("Request Data{}".format(request_data))
                _logger.info("Response Data{}".format(response_data))
                for response in response_data.get('etiqueta'):
                    label_data = response.get('etiqueta1')
                    binary_data = binascii.a2b_base64(str(label_data))

                    # attachment_id = self.env['ir.attachment'].create({
                    #     'name': 'Label_%s.pdf' % (pickings.name),
                    #     'datas': binary_data,
                    #     'datas_fname': 'Label_%s.%s' % (pickings.name, "pdf"),
                    #     'res_id': pickings.id,
                    #     'res_model': 'stock.picking',
                    #     'type': 'binary',
                    # })

                    message = (("Label created!<br/> <b>Label Tracking Number : </b>%s<br/>") % (
                        pickings.name))
                    # pickings.message_post(body=message)
                    pickings.message_post(body=message, attachments=[
                        ('Label_%s.pdf' % (pickings.name), base64.b64decode(binary_data))])
                    delivery_price = sum(
                        pickings.sale_id and pickings.sale_id.order_line.filtered(lambda line: line.is_delivery).mapped(
                            'price_unit'))
                return [{
                    'exact_price': delivery_price or 0.0,
                    'tracking_number': ','.join(tracking_number)}]
            else:
                raise ValidationError("Error In Response {}".format(response_data.content))
        except Exception as e:
            raise ValidationError(e)

    def correos_express_get_tracking_link(self, picking):
        tracking_link = self.company_id.correos_tracking_url if self.company_id and self.company_id.correos_tracking_url else "https://s.correosexpress.com/search?s="
        return '{0}{1}'.format(tracking_link, picking.correos_express_shipment_number)

    def correos_express_cancel_shipment(self, picking):
        raise ValidationError("Cancel API is not available!")
