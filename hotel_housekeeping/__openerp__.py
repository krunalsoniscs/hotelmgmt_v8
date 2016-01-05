# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Hotel Housekeeping Management",
    "version": "9.0.0.0.02",
    "author": "Serpent Consulting Services Pvt. Ltd., OpenERP SA",
    "category": "Generic Modules/Hotel Housekeeping",
    "website": "http://www.serpentcs.com",
    "depends": ["hotel"],
    "demo": [
        "views/hotel_housekeeping_data.xml",
    ],
    "data": [
        "security/ir.model.access.csv",
        "report/hotel_housekeeping_report.xml",
        "views/activity_detail.xml",
        "wizard/hotel_housekeeping_wizard.xml",
        "views/hotel_housekeeping_workflow.xml",
        "views/hotel_housekeeping_view.xml",
    ],
    "description": """
    Module for Hotel/Hotel Housekeeping. You can manage:
    * Housekeeping process
    * Housekeeping history room wise

      Different reports are also provided, mainly for hotel statistics.
    """,
    'installable': True,
    'auto_install': False,
}
