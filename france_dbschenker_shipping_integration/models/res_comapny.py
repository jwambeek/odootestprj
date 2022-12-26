from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    is_use_db_schenker_shipping_provider = fields.Boolean(string="IS USE DB SCHENKER SHIPPING PROVIDER",
                                                          help="True when we need to use DB SCHENKER shipping provider",
                                                          default=False, copy=False)

    db_schenker_api_url = fields.Char(string="DB SCHENKER API  URL", help="please enter DB SCHENKER API URL",
                                      default="https://services.schenkerfrance.fr/gateway-fat/edi/api/v1")
    db_schenker_account_number = fields.Char(string="DB SCHENKER ACCOUNT NUMBER",
                                             help="please enter DB SCHENKER ACCOUNT NUMBER")
    db_schenker_access_token = fields.Char(string="DB SCHENKER ACCESS TOKEN")
