# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Hotel Reservation Management - Reporting",
    "version": "9.0.0.0.03",
    "author": "Serpent Consulting Services Pvt. Ltd., OpenERP SA",
    "website": "http://www.serpentcs.com",
    "depends": ["hotel_reservation"],
    "category": "Generic Modules/Hotel Reservation",
    "data": [
        "security/ir.model.access.csv",
        "views/report_hotel_reservation_view.xml",
    ],
    "description": """
    Module shows the status of room reservation
     * Current status of reserved room
     * List status of room as draft or done state
    """,
    'installable': True,
    'auto_install': False,
}
