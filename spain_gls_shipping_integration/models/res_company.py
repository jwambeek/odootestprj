from odoo import models, fields,     api


class GLSResCompany(models.Model):
    _inherit = 'res.company'

    spain_gls_userid = fields.Char(string="GLS UserId", help="Your GlS UserId")
    spain_gls_api_url = fields.Char(string="GLS URL", help="ENTER YOUR GLS API URl")

    use_spain_gls_parcel_service = fields.Boolean(copy=False, string="Are You Using GLS?",
                                                  help="If use GLS Parcel Service than value set TRUE.",
                                                  default=False)
