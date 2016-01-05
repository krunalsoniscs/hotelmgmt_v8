# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import models, fields

AVAILABLE_STATES = [
    ('draft', 'Draft'),
    ('confirm', 'Confirm'),
    ('done', 'Done')]


class report_hotel_reservation_status(models.Model):

    _name = "report.hotel.reservation.status"
    _description = "Reservation By State"
    _auto = False

    reservation_no = fields.Char('Reservation No', size=64, readonly=True)
    nbr = fields.Integer('Reservation', readonly=True)
    state = fields.Selection(AVAILABLE_STATES, 'State', size=16,
                             readonly=True)

    def init(self, cr):
        """
        This method is for initialization for report hotel reservation
        status Module.
        @param self: The object pointer
        @param cr: database cursor
        """
        cr.execute("""
            create or replace view report_hotel_reservation_status as (
                select
                    min(c.id) as id,
                    c.reservation_no,
                    c.state,
                    count(*) as nbr
                from
                    hotel_reservation c
                group by c.state,c.reservation_no
            )""")
