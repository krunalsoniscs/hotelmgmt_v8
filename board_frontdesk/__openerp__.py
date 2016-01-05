# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Board for Hotel FrontDesk",
    "version": "9.0.0.0.01",
    "author": "Serpent Consulting Services Pvt Ltd",
    "website": "http://www.serpentcs.com",
    "category": "Board/Hotel FrontDesk",
    "depends": [
        "board",
        "report_hotel_restaurant",
        "hotel_pos_restaurant"
        ],
    "data": [
        "views/board_frontdesk_view.xml"
    ],
    "description": """
This module implements a dashboard for hotel FrontDesk that includes:
    * Calendar view of Today's Check-In and Check-Out
    * Calendar view of Weekly Check-In and Check-Out
    * Calendar view of Monthly Check-In and Check-Out
    """,
    "active": False,
    "installable": True,
}
