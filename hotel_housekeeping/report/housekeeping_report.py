# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
from openerp import models
from openerp.report import report_sxw
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class activity_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(activity_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'get_room_no': self.get_room_no,
            'get_room_activity_detail': self._get_room_activity_detail,
        })

    def _get_room_activity_detail(self, date_start, date_end, room_data):
        activity_detail = []
        house_keep_act_obj = self.pool.get('hotel.housekeeping.activities')
        if room_data:
            activiti_line_ids = (house_keep_act_obj.search
                                 (self.cr, self.uid,
                                  [('clean_start_time', '>=', date_start),
                                   ('clean_end_time', '<=', date_end)]))
            for activity in house_keep_act_obj.browse(self.cr, self.uid,
                                                      activiti_line_ids):
                act_val = {}
                ss_date = datetime.strptime(activity.clean_start_time,
                                            DEFAULT_SERVER_DATETIME_FORMAT)
                ee_date = datetime.strptime(activity.clean_end_time,
                                            DEFAULT_SERVER_DATETIME_FORMAT)
                diff = ee_date - ss_date
                act_val.update({'current_date': activity.today_date,
                                'activity': (activity.activity_name and
                                             activity.activity_name.name
                                             or ''),
                                'login': (activity.housekeeper and
                                          activity.housekeeper.name or ''),
                                'clean_start_time': activity.clean_start_time,
                                'clean_end_time': activity.clean_end_time,
                                'duration': diff})
                activity_detail.append(act_val)
        return activity_detail

    def get_room_no(self, room_no):
        return self.pool.get('hotel.room').browse(self.cr, self.uid,
                                                  room_no).name


class report_lunchorder(models.AbstractModel):

    _name = 'report.hotel_housekeeping.report_housekeeping'
    _inherit = 'report.abstract_report'
    _template = 'hotel_housekeeping.report_housekeeping'
    _wrapped_report_class = activity_report
