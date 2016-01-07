# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Hotel Management',
    'version': '9.0.0.0.07',
    'author': 'Serpent Consulting Services Pvt. Ltd., OpenERP SA',
    'category': 'Generic Modules/Hotel Management',
    'website': 'http://www.serpentcs.com',
    'depends': ['product_uos', 'sale_stock', 'point_of_sale', 'report'],
    'demo': [
            'data/hotel_data.xml',
     ],
    'data': [
            'security/hotel_security.xml',
            'security/ir.model.access.csv',
            'views/hotel_sequence.xml',
            'views/hotel_report.xml',
            'views/report_hotel_management.xml',
            'views/hotel_view.xml',
            'wizard/hotel_wizard.xml',
            'views/templates.xml'
    ],
    'description': '''
    Module for Hotel/Resort/Property management. You can manage:
    * Configure Property
    * Hotel Configuration
    * Check In, Check out
    * Manage Folio
    * Payment

    Different reports are also provided, mainly for hotel statistics.
    ''',
    'auto_install': False,
    'installable': True
}
