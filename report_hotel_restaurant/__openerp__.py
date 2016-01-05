# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Restaurant Management - Reporting",
    "version": "9.0.0.0.03",
    "author": "Serpent Consulting Services Pvt. Ltd., OpenERP SA",
    "website": "http://www.serpentcs.com, http://www.openerp.com",
    "depends": ["hotel_restaurant", "report_hotel_reservation"],
    "category": "Generic Modules/Hotel Restaurant",
    "data": [
        "security/ir.model.access.csv",
        "views/report_hotel_restaurant_view.xml",
    ],
    "description": """
    Module shows the status of restaurant reservation
     * Current status of reserved tables
     * List status of tables as draft or done state
    """,
    'installable': True,
    'auto_install': False,
}

