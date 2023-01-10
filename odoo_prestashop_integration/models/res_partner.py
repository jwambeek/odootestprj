from odoo import fields, models, api

class CustomResPartner(models.Model):
    _inherit = "res.partner"

    prestashop_customer_url = fields.Char(string="Prestashop Customer Url")
    prestashop_customer_id = fields.Char(string="prestashop Customer")
    prestashop_store_id = fields.Many2one('prestashop.store.details', string="Prestashop Store")
