# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
from openerp import models
from openerp.report import report_sxw


class folio_report1(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(folio_report1, self).__init__(cr, uid, name, context)
        self.localcontext.update({'time': time,
                                  'get_data': self.get_data,
                                  'gettotal': self.gettotal,
                                  'getTotal': self.getTotal,
                                  'get_pos': self.get_pos,
                                  })
        self.temp = 0.0

    def get_data(self, date_start, date_end):
        folio_obj = self.pool.get('hotel.folio')
        tids = folio_obj.search(self.cr, self.uid,
                                [('checkin_date', '>=', date_start),
                                 ('checkout_date', '<=', date_end)])
        res = folio_obj.browse(self.cr, self.uid, tids)
        folio_ids = []
        for rec in res:
            if rec.folio_pos_order_ids:
                folio_ids.append(rec)
        return folio_ids

    def get_pos(self, date_start, date_end):
        folio_obj = self.pool.get('hotel.folio')
        tids = folio_obj.search(self.cr, self.uid,
                                [('checkin_date', '>=', date_start),
                                 ('checkout_date', '<=', date_end)])
        res = folio_obj.browse(self.cr, self.uid, tids)
        posorder_ids = []
        for rec in res:
            if rec.folio_pos_order_ids:
                posorder_ids.append(rec.folio_pos_order_ids)
        return posorder_ids

    def gettotal(self, pos_order):
        amount = 0.0
        for x in pos_order:
            amount = amount + float(x.amount_total)
        self.temp = self.temp + amount
        return amount

    def getTotal(self):
        return self.temp


class report_lunchorder1(models.AbstractModel):
    _name = 'report.hotel_pos_restaurant.report_folio_pos'
    _inherit = 'report.abstract_report'
    _template = 'hotel_pos_restaurant.report_folio_pos'
    _wrapped_report_class = folio_report1
