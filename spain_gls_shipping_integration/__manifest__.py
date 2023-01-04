# -*- coding: utf-8 -*-
{   
    'name': 'GLS Spain Shipping Integration',
    'category': 'Website',
    'author': "Vraja Technologies",
    'version': '15.0.19.11.2021',
    'summary': """""",
    'description': """Using GLS Easily manage Shipping Operation in odoo.Export Order While Validate Delivery Order.Import Tracking From GLS to odoo.Generate Label in odoo.We also Provide the gls,envia,fedex shipping integration.""",
        'depends': ['delivery'],
    'data': [
        'views/res_company.xml',
        'views/delivery_carrier_view.xml',],
    'images': ['static/description/GLS_Cover_Image.png'],
    'maintainer': 'Vraja Technologies',
    'website':'https://www.vrajatechnologies.com',
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'live_test_url': 'https://www.vrajatechnologies.com/contactus',
    'price': '321',
    'currency': 'EUR',
    'license': 'OPL-1',
}
#initial version
#15.0.24.11.2020
#15.0.19.10.2021 change in tracking method link