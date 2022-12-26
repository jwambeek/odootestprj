from odoo import models, fields, api, _


class DBSchenker(models.Model):
    _inherit = 'stock.picking'
    db_schenker_shipment_id = fields.Char(string="DB Schenker Shipment Id",copy=False,
                                     help="DB Schenker Shipment Id Number")
    db_schenker_book_shipment_id = fields.Char(string="DB Schenker Book Shipment Id", copy=False,
                                          help="DB Schenker Book Shipment Id Number")
    number_of_labels = fields.Integer(string="Number Of Labels", default=1, copy=False,
                                      help="Enter Number Of Labels You Want")



