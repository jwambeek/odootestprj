# -*- coding: utf-8 -*-pack
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{

    # App information
    'name': 'France DB Schenker Shipping Integration',
    'category': 'Website',
    'version': '14.0.26.10.21',
    'summary': 'We Provide Odoo Services',
    'license': 'OPL-1',

    # Dependencies
    'depends': ['delivery'],

    # Views
    'data': ['views/res_comapny.xml',
             'views/delivery_carrier.xml',
             'views/stock_picking.xml'],

    # Odoo Store Specificpatient_name
    'images': ['static/description/cover.jpg'],

    # Author
    'author': 'Vraja Technologies',
    'website': 'https://www.vrajatechnologies.com',
    'maintainer': 'Vraja Technologies',

    # Technical
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'live_test_url': 'https://www.vrajatechnologies.com/contactus',
    'price': '321',
    'currency': 'EUR',
    "cloc_exclude": [
        "./**/*",
    ]
}

#Devloped and Tested By Mithilesh Lathiya
#Version Log = Module Created AT 26.10.21(15.0.26.10.21)(Mithilesh Lathiya)

