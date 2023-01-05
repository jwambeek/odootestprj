# -*- coding: utf-8 -*-

{   
    'name': 'CORREOS Express Integration for Spain',
    'summary': """""",

    'description': """

Features
--------

Our Odoo to CORREOS EXPRESS Shipping Integration will help you to connect your Odoo with CORREOS EXPRESS (www.correosexpress.es).

You will be able to automatically submit order information from stock picking and get Shipping label and
Order Tracking number.

NOTICE: this module does NOT connect with Correos (www.correos.com). Please check our other modules.

We also have integrations with: Correos, DHL Parcel, DHL Express, Fedex, UPS, GLS (ASM), USPS, Stamps.com, 

Shipstation, Bigcommerce, Easyship, Amazon shipping, Sendcloud, eBay, Shopify.
        """,

    'category': 'Stock',
    'author': "Vraja Technologies",
    'version': '15.0.28.10.2021',
    'depends': ['delivery'],
    'live_test_url': 'https://www.vrajatechnologies.com/contactus',
    'data': [
            'views/res_company.xml',
        'views/delivery_carrier_view.xml',
        'views/stock_picking_view.xml',
             ],
    'images': ['static/description/correos_express.png'],

    'maintainer': 'Vraja Technologies',
    'website':'https://www.vrajatechnologies.com',
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': '321',
    'currency': 'EUR',
    'license': 'OPL-1',
}
# version changelog
# 14.0.18.06.2021 Add receiver email address
# 15.0.28.10.2021 Migrate From version 14