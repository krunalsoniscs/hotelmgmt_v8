# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Hotel POS Restaurant Management",
    "version": "9.0.0.0.03",
    "author": "Serpent Consulting Services Pvt. Ltd., OpenERP SA",
    "category": "Generic Modules/Hotel Restaurant Management",
    "website": "http://www.serpentcs.com",
    "depends": ["pos_restaurant", "hotel"],
    "demo": ["views/hotel_pos_data.xml"],
    "data": ["security/ir.model.access.csv",
             "views/pos_restaurent_view.xml",
             "views/hotel_pos_report.xml",
             "views/report_pos_management.xml",
             "wizard/hotel_pos_wizard.xml"],
    "description": """
    Module for POS management.
     """,
    "auto_install": False,
    "installable": True
}
