from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError, UserError
import logging
import json
import requests
import binascii

_logger = logging.getLogger("DB Schenker")


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[("dbschenker", "DBSchenker")],
                                     ondelete={'dbschenker': 'set default'})
    incoterm_codes = fields.Selection([('CIP', 'Carriage and Insurance Paid to'),
                                       ('CPT', 'Carriage Paid to'),
                                       ('DAF', 'Delivered at Frontier'),
                                       ('DAP', 'Delivered At Place'),
                                       ('DPU', 'Delivered at Place Unloaded'),
                                       ('DDP', 'Delivered, Duty paid'),
                                       ('EXW', 'Ex Works'),
                                       ('FCA', 'Free Carrier'),
                                       ('P', 'Charges paid'),
                                       ('D', 'Charges owed')
                                       ], string="Incoterm Codes",
                                      help="This Is Incoterm Codes. This Is Provided By DBSchenker")
    Product_codes = fields.Selection([('01', '01-SYSTEM France'),
                                      ('08', '08-PALLET France'),
                                      ('10', '10-WECARE France'),
                                      ('12', '12-PREMIUM 13 France'),
                                      ('13', '13-PREMIUM France'),
                                      ('18', '18-PALLET PREMIUM France'),
                                      ('21', '21-PHARMA+ SYSTEM France'),
                                      ('22', '22-PHARMA+ PREMIUM 13 France'),
                                      ('23', '23-PHARMA+ PREMIUM France'),
                                      ('24', '24-PHARMA+ PALLET France'),
                                      ('30', '30-EXPRESS France'),
                                      ('60', '60-SYSTEM Export'),
                                      ('62', '62-PREMIUM 13 Export'),
                                      ('63', '63-PREMIUM Export'),
                                      ('64', '64-FIX DAY Export'),
                                      ('66', '66-PREMIUM 10 Export'),
                                      ('80', '80-DIRECT France'),
                                      ('81', '81-DIRECT Export'),
                                      ], string="Product Codes",
                                     help="This Is Product Codes. This Is Provided By DBSchenker")
    package_type = fields.Selection([('CT', 'Carton'),
                                     ('EP', 'Euro pallet'),
                                     ('PE', 'One-way pallet')], string="Package Type",
                                    help="This Is Package Type. This Is Provided By DBSchenker")
    label_format = fields.Selection([('A4', 'A4'),
                                     ('A6', 'A6')])

    def dbschenker_rate_shipment(self, orders):
        "This Method Is Used For Get Rate"
        return {'success': True, 'price': 0.0, 'error_message': False, 'warning_message': False}

    def dbschenker_request_method(self, pickings):
        "This Method Is Used For Making Shipping Request Data"
        sender_address = pickings.picking_type_id.warehouse_id.partner_id
        receiver_address = pickings.partner_id
        payload = {
            "consolidation": "CONSIGNOR_REFERENCE",
            "delivery": {
                "incoterm": self.incoterm_codes or "",
                "product": self.Product_codes or ""
            },
            "handling": {
                "total_handling_units": str(pickings.number_of_labels),
                "type": self.package_type or "",
                "weight":
                    [
                        {
                            "type": "GROSS_WEIGHT",
                            "unit": "KGM",
                            "value": str(pickings.shipping_weight / pickings.number_of_labels)
                        }
                    ]
            },
            "invoicing": {
                "account_number": str(self.company_id.db_schenker_account_number)
            },
            "labels": {
                "language": "PDF",
                "format":self.label_format
            },
            "partners": [
                {
                    "identity":
                        {
                            "address": [
                                sender_address.street or ""
                            ],
                            "city": sender_address.city or "",
                            "country_code": "FR",
                            "name": [
                                sender_address.name or ""
                            ],
                            "postal_code": sender_address.zip or ""
                        },
                    "role": "CONSIGNOR"
                },
                {
                    "identity":
                        {
                            "address": [
                                receiver_address.street or ""
                            ],
                            "city": receiver_address.city or "",
                            "country_code": "FR",
                            "name": [
                                receiver_address.name or ""
                            ],
                            "postal_code": receiver_address.zip or ""
                        },
                    "role": "CONSIGNEE"
                }
            ],
            "references": [
                {
                    "type": "CONSIGNOR",
                    "value": str(pickings.origin)
                }
            ]
        }
        data = json.dumps(payload)
        return data

    def dbschenker_send_shipping(self, pickings):
        """This Method Is Used For Send The Data To Shipper"""
        response = []
        try:

            headers = {
                'Content-Type': 'application/json',
                'Authorization': "Bearer %s" % self.company_id.db_schenker_access_token
            }
            api_url = "%s/shipments/" % self.company_id.db_schenker_api_url
            request_data = self.dbschenker_request_method(pickings)
            _logger.info("Shipment Request Data %s" % request_data)
            response_data = requests.request(method="POST", url=api_url, headers=headers, data=request_data)
            _logger.info(response_data)
            if response_data.status_code in [200, 201]:
                response_body = response_data.json()
                _logger.info("Response Of Shipment %s " % response_body)
                if not response_body.get('request_id'):
                    raise ValidationError("Shipment Id not found in response %s" % (response_body))
                pickings.db_schenker_shipment_id = response_body.get('request_id')
                pickings.carrier_tracking_ref = response_body.get('shipment') and response_body.get('shipment').get(
                    'stt')
                loading_shipment_api_url = "%s/loadings/STT/%s" % (self.company_id.db_schenker_api_url,pickings.carrier_tracking_ref)
                response_data_loading_shipment = requests.request(method="POST", url=loading_shipment_api_url, headers=headers)
                if response_data_loading_shipment.status_code in [200,201]:
                    pickings.db_schenker_book_shipment_id= response_data_loading_shipment.text
                else:
                    _logger.info(response_data_loading_shipment.text)
                label_url = response_body.get('shipment') and response_body.get('shipment').get('labels')[0]
                binary_data = binascii.a2b_base64(
                    str(label_url))
                logmessage = ("<b>Tracking Number:</b> %s") % (pickings.carrier_tracking_ref)
                pickings.message_post(body=logmessage,
                                      attachments=[("%s.pdf" % (pickings.db_schenker_shipment_id), binary_data)])
                shipping_data = {'exact_price': 0.0, 'tracking_number': pickings.carrier_tracking_ref}
                response += [shipping_data]
                return response
            else:
                raise ValidationError(
                    "getting Some Error From {0} \n Response Data {1}".format(api_url, response_data.text))
        except Exception as e:
            raise ValidationError(e)

    def dbschenker_cancel_shipment(self, picking):
        """This Method Used For Cancel The Shipment"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': "Bearer %s" % self.company_id.db_schenker_access_token
            }

            api_url = "%s/shipments/STT/%s" % (self.company_id and self.company_id.db_schenker_api_url,
                                    picking.carrier_tracking_ref)
            response_body = requests.request(method="DELETE", url=api_url, headers=headers)
            _logger.info("Response Of Cancel Shipment %s " % response_body)
            if response_body.status_code == 200:
                return True
            else:
                raise ValidationError(response_body.text)
        except Exception as e:
            raise ValidationError(e)

    def dbschenker_get_tracking_link(self, picking):
        """This Method Is Used For Track The Shippment"""
        return "%s%s&refType=Stt"% ("https://eschenker.dbschenker.com/app/tracking-public/?refNumber=",
        picking.carrier_tracking_ref)

