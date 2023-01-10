{
    'name': 'Prestashop Odoo Integration',
    'category': 'Sales',
    'version': '15.0',
    'summary': """""",
    'description': """ Using Prestashop odoo integration we import Orders,Products,Variant,Category,customer and Inventory.we also providing various apps like magento,bigcommerce,shipstation.""",
    'depends': ['sale_management','sale_stock','product','base'],

    'data': [
        'security/ir.model.access.csv',
        'views/res_partner.xml',
        'views/prestashop_store_details.xml',
        'views/prestashop_operation_details.xml',
        'views/product_category.xml',
        'views/product.xml',
        'views/product_attribute.xml',
        'views/sale_order.xml',
        'data/ir_cron.xml',
        'views/prestashop_product_details.xml'
    ],
    'author': 'Vraja Technologies',
    'images': ['static/description/prestashop.jpg'],
    'maintainer': 'Vraja Technologies',
    'website': 'https://www.vrajatechnologies.com',
    'live_test_url': 'https://www.vrajatechnologies.com/contactus',
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': '204',
    'currency': 'EUR',
    'license': 'OPL-1',

}
