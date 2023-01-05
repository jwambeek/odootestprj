# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CorreosExpressTrackingNumber(models.Model):
    _inherit = 'stock.picking'

    correos_express_shipment_number = fields.Char(string="Correos Express Shipment Number", copy=False,help="Shipment number generated once we click on validate button")
