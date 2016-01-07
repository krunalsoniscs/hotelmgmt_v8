# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
from openerp import models
from openerp.report import report_sxw


class folio_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(folio_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({'time': time,
                                  'get_data': self.get_data,
                                  'get_Total': self.getTotal,
                                  'get_total': self.gettotal,
                                  })
        self.net_total = 0.0

    def get_data(self, date_start, date_end):
        folio_obj = self.pool.get('hotel.folio')
        tids = folio_obj.search(self.cr, self.uid,
                                [('checkin_date', '>=', date_start),
                                 ('checkout_date', '<=', date_end)])
        res = folio_obj.browse(self.cr, self.uid, tids)
        return res

    def gettotal(self, total):
        self.net_total += float(total)
        return total

    def getTotal(self):
        return self.net_total


class report_lunchorder(models.AbstractModel):
    _name = 'report.hotel.report_hotel_folio'
    _inherit = 'report.abstract_report'
    _template = 'hotel.report_hotel_folio'
    _wrapped_report_class = folio_report
