# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Hotel Reservation Management",
    "version": "9.0.0.0.03",
    "author": "Serpent Consulting Services Pvt. Ltd., OpenERP SA",
    "category": "Generic Modules/Hotel Reservation",
    "website": "http://www.serpentcs.com",
    "depends": ["hotel", "stock", 'mail'],
    "demo": [
        "views/hotel_reservation_data.xml",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/hotel_reservation_wizard.xml",
        "report/hotel_reservation_report.xml",
        "views/hotel_reservation_sequence.xml",
        "views/hotel_reservation_workflow.xml",
        "views/hotel_reservation_view.xml",
        "views/hotel_scheduler.xml",
        "views/report_checkin.xml",
        "views/report_checkout.xml",
        "views/max_room.xml",
        "views/room_res.xml",
        "views/room_summ_view.xml",
        "views/email_temp_view.xml",
        "views/templates.xml"
    ],
    "description": """
    Module for Hotel/Resort/Property management. You can manage:
    * Guest Reservation
    * Group Reservartion
      Different reports are also provided, mainly for hotel statistics.
    """,
    'qweb': ['static/src/xml/hotel_room_summary.xml'],
    'installable': True,
    'auto_install': False,
}
