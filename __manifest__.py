{
    'name': 'Advance Consignment Management | Sale Consignment | Purchase Consignment | Sale Consignment Order | Consignment Inventory Management | Purchase Consignment Order',
    "author": "Edge Technologies",
    'version': '17.0.1.0',
    'live_test_url': "https://youtu.be/KdYBp1OwSag",
    "images":['static/description/main_screenshot.png'],
    'summary': 'Create consignment order consignment sale order consignment purchase order consignment sales consignment purchase consignment customer consignment vendor consignment delivery consignment stock consignment management process consignment purchase report',
    'description': "Sale Consignment App",
    "license" : "OPL-1",
    'depends': [
        'stock','sale_management','account'
    ],
    'data': [
            'security/consignment_security.xml',
            'security/ir.model.access.csv',
            'data/sequence.xml',
            'data/paperformat.xml',
            'report/report.xml',
            'views/stock_warehouse.xml',
            'views/consignment_order.xml',
            'views/product.xml',
            'views/res_partner.xml',
            'views/sale_order.xml',
            'wizard/create_sale_order_wizard_view.xml',
            'wizard/sale_consignment_report_wizard_view.xml',
            'report/sale_consignment_report.xml',


    ],
    'demo': [ ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 18,
    'currency': "EUR",
    'category': 'Sales',
}
