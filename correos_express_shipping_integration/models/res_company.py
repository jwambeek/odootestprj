# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CorreosExpressResCompany(models.Model):
    _inherit = 'res.company'

    correos_express_username = fields.Char(string="Username", help="Your Correos Account Username")
    correos_express_password = fields.Char(string="Password", help="Your Correos Account Password")
    correos_express_customer_code = fields.Char(string="Customer Code", help="Your Correos Account Customer Code")
    correso_express_sender_code = fields.Char(string="Sender Code",help="Sender's Code ( provided by Correos Express)")
    correos_express_api_url = fields.Char(string="API URl")
    correos_express_tracking_url = fields.Char(string="Tracking URL", help="Used For Tracking Shipment")
    use_correos_express_shipping_provider = fields.Boolean(copy=False, string="Are You Using Correos Express?",
                                                 help="If use Correos Express shipping Integration than value set TRUE.",
                                                 default=False)
