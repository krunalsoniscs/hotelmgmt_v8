# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.exceptions import except_orm, ValidationError, Warning
from dateutil.relativedelta import relativedelta
from openerp import models, fields, api, _
import datetime
import time

def _offset_format_timestamp_extended(src_tstamp_str, src_format, dst_format,
                              ignore_unparsable_time=True, 
                              context=None, reverse=False):
    """
    Convert a source timeStamp string into a destination timeStamp string,
    attempting to apply the
    correct offset if both the server and local timeZone are recognized,or no
    offset at all if they aren't or if tz_offset is false (i.e. assuming they
    are both in the same TZ).

    @param src_tstamp_str: the STR value containing the timeStamp.
    @param src_format: the format to use when parsing the local timeStamp.
    @param dst_format: the format to use when formatting the resulting
     timeStamp.
    @param server_to_client: specify timeZone offset direction (server=src
                             and client=dest if True, or client=src and
                             server=dest if False)
    @param ignore_unparsable_time: if True, return False if src_tstamp_str
                                   cannot be parsed using src_format or
                                   formatted using dst_format.

    @return: destination formatted timestamp, expressed in the destination
             timezone if possible and if tz_offset is true, or src_tstamp_str
             if timezone offset could not be determined.
    """
    if not src_tstamp_str:
        return False
    res = src_tstamp_str
    if src_format and dst_format:
        try:
            # dt_value needs to be a datetime.datetime object\
            # (so notime.struct_time or mx.DateTime.DateTime here!)
            dt_value = datetime.datetime.strptime(src_tstamp_str, src_format)
            if context.get('tz', False):
                try:
                    import pytz
                    src_tz = pytz.timezone(context['tz'])
                    dst_tz = pytz.timezone('UTC')
                    if reverse:
                        src_tz = pytz.timezone('UTC')
                        dst_tz = pytz.timezone(context['tz'])
                    src_dt = src_tz.localize(dt_value, is_dst=True)
                    dt_value = src_dt.astimezone(dst_tz)
                except Exception:
                    pass
            res = dt_value.strftime(dst_format)
        except Exception:
            # Normal ways to end up here are if strptime or strftime failed
            if not ignore_unparsable_time:
                return False
            pass
    return res


class product_product(models.Model):

    @api.model
    def name_search(self, name='', args=None,
                    operator='ilike', limit=100):
        context = dict(self._context) or {}
        args = args or []
        if context.has_key('checkin') and context.has_key('checkout'):
            if not context.get('checkin') or  not context.get('checkout'):
                raise except_orm(_('Warning'),
                                 _('Before choosing a room,\n You have to select \
                                 a Check in date or a Check out date in \
                                 the form.'))
            room_ids = []
            checkin = str(context.get('checkin'))
            checkout = str(context.get('checkout'))
            assigned_room = self.env['hotel.room.reservation.line'].\
                                    search([
                                            ('status', '=', 'confirm'),
                                            '&','|',
                                            ('check_in', '>=',checkin),
                                            ('check_out', '>=',checkin),
                                            '|',
                                            ('check_in', '<=',checkout),
                                            ('check_out', '<=',checkout),
                                           ])
            for room_line in assigned_room:
                if room_line.room_id.product_id.id not in room_ids:
                    room_ids.append(room_line.room_id.product_id.id)
            folio_line_ids = self.env['folio.room.line'].\
                                search([ 
                                   ('status', 'not in', ['done', 'cancel']),
                                   '&','|',
                                   ('check_in','>=', checkin),
                                   ('check_out','>=', checkin),
                                    '|',
                                    ('check_in','<=', checkout),
                                    ('check_out','<=', checkout),
                                   ])
            for folio_line in folio_line_ids:
                if folio_line.room_id.product_id.id not in room_ids:
                    room_ids.append(room_line.room_id.product_id.id)
            if room_ids:
                args.extend([('id', 'not in', room_ids),('is_active_room','=','True')])
        return super(product_product, self).name_search(name=name, args=args,
                                                        operator=operator, limit=limit)
        
    _inherit = "product.product"

class hotel_folio(models.Model):

    _inherit = 'hotel.folio'
    _order = 'reservation_id desc'

    reservation_id = fields.Many2one(comodel_name='hotel.reservation',
                                     string='Reservation Id')

    @api.multi
    def write(self, vals):
        """
        Overrides orm write method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        folio_write = super(hotel_folio, self).write(vals)
        for folio_rec in self:
            if folio_rec.reservation_id:
                reservation_obj = (self.env['hotel.room.reservation.line'
                                            ].search([('reservation_id',
                                                        '=',
                                                        folio_rec.reservation_id.id)]))
                if len(reservation_obj) == 1:
                    for line_id in folio_rec.reservation_id.reservation_line:
                        for room_id in line_id.reserve:
                            vals = {'room_id': room_id.id,
                                    'check_in': folio_rec.checkin_date,
                                    'check_out': folio_rec.checkout_date,
                                    'state': 'assigned',
                                    'reservation_id': folio_rec.reservation_id.id,
                                    }
                            reservation_obj.write(vals)
        return folio_write


class hotel_reservation(models.Model):

    _name = "hotel.reservation"
    _rec_name = "reservation_no"
    _description = "Reservation"
    _order = 'reservation_no desc'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    reservation_no = fields.Char('Reservation No', size=64, readonly=True)
    date_order = fields.Datetime('Date Ordered', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 default=(lambda *a:
                                          time.strftime
                                          (DEFAULT_SERVER_DATETIME_FORMAT)))
    warehouse_id = fields.Many2one('stock.warehouse', 'Hotel', readonly=True,
                                   required=True, default=1,
                                   states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', 'Guest Name', readonly=True,
                                 required=True,
                                 states={'draft': [('readonly', False)]})
    pricelist_id = fields.Many2one('product.pricelist', 'Scheme',
                                   required=True, readonly=True,
                                   states={'draft': [('readonly', False)]},
                                   help="Pricelist for current reservation.")
    partner_invoice_id = fields.Many2one('res.partner', 'Invoice Address',
                                         readonly=True,
                                         states={'draft':
                                                 [('readonly', False)]},
                                         help="Invoice address for "
                                         "current reservation.")
    partner_order_id = fields.Many2one('res.partner', 'Ordering Contact',
                                       readonly=True,
                                       states={'draft':
                                               [('readonly', False)]},
                                       help="The name and address of the "
                                       "contact that requested the order "
                                       "or quotation.")
    partner_shipping_id = fields.Many2one('res.partner', 'Delivery Address',
                                          readonly=True,
                                          states={'draft':
                                                  [('readonly', False)]},
                                          help="Delivery address"
                                          "for current reservation. ")
    checkin = fields.Datetime('Expected-Date-Arrival', required=True,
                              readonly=True,
                              states={'draft': [('readonly', False)]})
    checkout = fields.Datetime('Expected-Date-Departure', required=True,
                               readonly=True,
                               states={'draft': [('readonly', False)]})
    adults = fields.Integer('Adults', size=64, readonly=True,
                            states={'draft': [('readonly', False)]},
                            help='List of adults there in guest list. ')
    children = fields.Integer('Children', size=64, readonly=True,
                              states={'draft': [('readonly', False)]},
                              help='Number of children there in guest list.')
    reservation_line = fields.One2many('hotel_reservation.line', 'line_id',
                                       'Reservation Line',readonly=True,
                                       states={'draft': [('readonly', False)]},
                                       help='Hotel room reservation details.',)
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'),
                              ('cancel', 'Cancel'), ('done', 'Done')],
                             'State', readonly=True,
                             default=lambda *a: 'draft')
    folio_id = fields.Many2many('hotel.folio', 'hotel_folio_reservation_rel',
                                'order_id', 'invoice_id', string='Folio')
    dummy = fields.Datetime('Dummy')
    
    @api.multi
    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        for records in self:
            if records.state not in ['draft']:
                raise Warning("You can delete only Draft Reservation")
        return super(hotel_reservation, self).unlink()

    @api.constrains('reservation_line', 'adults', 'children')
    def check_reservation_rooms(self):
        '''
        This method is used to validate the reservation_line.
        -----------------------------------------------------
        @param self: object pointer
        @return: raise a warning depending on the validation
        '''
        for reservation in self:
            if not reservation.reservation_line:
                raise ValidationError(_('Please Select Rooms \
                For Reservation.'))
            for rec in reservation.reservation_line:
                if not rec.reserve :
                    raise ValidationError(_('Please Select Rooms \
                    For Reservation.'))
                cap = 0
                for room in rec.reserve:
                    cap += room.capacity
                if (self.adults + self.children) > cap:
                        raise ValidationError(_('Room Capacity \
                        Exceeded \n Please Select Rooms According to \
                        Members Accomodation.'))

    @api.model
    def _needaction_count(self, domain=None):
        """
         Show a count of draft state reservations on the menu badge.
         """
        return self.search_count([('state', '=', 'draft')])

    @api.onchange('date_order', 'checkin')
    def on_change_checkin(self):
        '''
        When you change date_order or checkin it will check whether
        Checkin date should be greater than the current date
        ------------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        '''
        if self.date_order and self.checkin and self.checkin < self.date_order:
            raise except_orm(_('Warning'), _('Checkin date should be \
                greater than the current date.'))

    @api.onchange('checkout', 'checkin')
    def on_change_checkout(self):
        '''
        When you change checkout or checkin it will check whether
        Checkout date should be greater than Checkin date
        and update dummy field
        -----------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        '''
        checkout_date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        checkin_date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if not (checkout_date and checkin_date):
            return {'value': {}}
        if self.checkout and self.checkin:
            if self.checkout < self.checkin:
                raise except_orm(_('Warning'), _('Checkout date \
                should be greater than Checkin date.'))
        dat_a = time.strptime(checkout_date,
                              DEFAULT_SERVER_DATETIME_FORMAT)[:5]
        addDays = datetime.datetime(*dat_a) + datetime.timedelta(days=1)
        self.dummy = addDays.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        '''
        When you change partner_id it will update the partner_invoice_id,
        partner_shipping_id and pricelist_id of the hotel reservation as well
        ---------------------------------------------------------------------
        @param self: object pointer
        '''
        self.partner_invoice_id = False
        self.partner_shipping_id = False
        self.partner_order_id = False
        if self.partner_id:
            addr = self.partner_id.address_get(['delivery', 'invoice',
                                                'contact'])
            self.partner_invoice_id = addr['invoice']
            self.partner_order_id = addr['contact']
            self.partner_shipping_id = addr['delivery']
            self.pricelist_id = self.partner_id.property_product_pricelist.id

    @api.multi
    def confirmed_reservation(self):
        """
        This method create a new recordset for hotel room reservation line
        ------------------------------------------------------------------
        @param self: The object pointer
        @return: new record set for hotel room reservation line.
        """
        reservation_line_obj = self.env['hotel.room.reservation.line']
        for reservation in self:
            self._cr.execute("select count(*) from hotel_reservation as hr "
                             "inner join hotel_reservation_line as hrl on \
                             hrl.line_id = hr.id "
                             "inner join hotel_reservation_line_room_rel as \
                             hrlrr on hrlrr.room_id = hrl.id "
                             "where (checkin,checkout) overlaps \
                             ( timestamp %s, timestamp %s ) "
                             "and hr.id <> cast(%s as integer) "
                             "and hr.state = 'confirm' "
                             "and hrlrr.hotel_reservation_line_id in ("
                             "select hrlrr.hotel_reservation_line_id \
                             from hotel_reservation as hr "
                             "inner join hotel_reservation_line as \
                             hrl on hrl.line_id = hr.id "
                             "inner join hotel_reservation_line_room_rel \
                             as hrlrr on hrlrr.room_id = hrl.id "
                             "where hr.id = cast(%s as integer) )",
                             (reservation.checkin, reservation.checkout,
                              str(reservation.id), str(reservation.id)))
            res = self._cr.fetchone()
            roomcount = res and res[0] or 0.0
            if roomcount:
                raise except_orm(_('Warning'), _('You tried to confirm \
                reservation with room those already reserved in this \
                reservation period'))
            self.write({'state': 'confirm'})
            for line_id in reservation.reservation_line:
                for room_id in line_id.reserve:
                    vals = {
                        'room_id': room_id.id,
                        'check_in': reservation.checkin,
                        'check_out': reservation.checkout,
                        'state': 'assigned',
                        'reservation_id': reservation.id,
                        }
                    room_id.write({'isroom': False, 'status': 'occupied'})
                    reservation_line_obj.create(vals)
        return True

    @api.multi
    def cancel_reservation(self):
        """
        This method cancel recordset for hotel room reservation line
        ------------------------------------------------------------------
        @param self: The object pointer
        @return: cancel record set for hotel room reservation line.
        """
        self.write({'state': 'cancel'})
        room_reservation_line = self.env['hotel.room.reservation.line'
                                         ].search([('reservation_id',
                                                    'in',
                                                    self.ids)])
        room_reservation_line.write({'state': 'unassigned'})
        reservation_lines = self.env['hotel_reservation.line'
                                     ].search([('line_id', 'in', self.ids)])
        for reservation_line in reservation_lines:
            reservation_line.reserve.write({'isroom': True,
                                            'status': 'available'})
        return True

    @api.multi
    def send_reservation_maill(self):
        '''
        This function opens a window to compose an email,
        template message loaded by default.
        @param self: object pointer
        '''
        assert len(self._ids) == 1, 'This is for a single id at a time.'
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = (ir_model_data.get_object_reference
                           ('hotel_reservation',
                            'mail_template_hotel_reservation')[1])
        except ValueError:
            template_id = False
        try:
            compose_form_id = (ir_model_data.get_object_reference
                               ('mail',
                                'email_compose_message_wizard_form')[1])
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'hotel.reservation',
            'default_res_id': self._ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'force_send': True,
            'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
            'force_send': True
        }

    @api.model
    def reservation_reminder_24hrs(self):
        """
        This method is for scheduler
        every 1day scheduler will call this method to
        find all tomorrow's reservations.
        ----------------------------------------------
        @param self: The object pointer
        @return: send a mail
        """
        now_str = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        now_date = datetime.datetime.strptime(now_str,
                                              DEFAULT_SERVER_DATETIME_FORMAT)
        ir_model_data = self.env['ir.model.data']
        template_id = (ir_model_data.get_object_reference
                       ('hotel_reservation',
                        'mail_template_reservation_reminder_24hrs')[1])
        template_rec = self.env['mail.template'].browse(template_id)
        last_date = now_date - relativedelta(days=1)
        now_date = datetime.datetime.strftime(now_date,
                                              DEFAULT_SERVER_DATETIME_FORMAT)
        last_date = datetime.datetime.strftime(last_date,
                                              DEFAULT_SERVER_DATETIME_FORMAT)
        args = [('state', '=', 'confirm'),
                        ('checkin', '<=', now_date),
                        ('checkin', '>=', last_date)]
        for travel_rec in self.search(args):
                template_rec.send_mail(travel_rec.id, force_send=True)
        return True

    @api.multi
    def _create_folio(self):
        """
        This method is for create new hotel folio.
        -----------------------------------------
        @param self: The object pointer
        @return: new record set for hotel folio.
        """
        hotel_folio_obj = self.env['hotel.folio']
        room_obj = self.env['hotel.room']
        vals = {}
        for reservation in self:
            folio_lines = []
            checkin_date = reservation['checkin']
            checkout_date = reservation['checkout']
            if not self.checkin < self.checkout:
                raise except_orm(_('Error'),
                                 _('Checkout date should be greater \
                                 than the Checkin date.'))
            duration_vals = (self.onchange_check_dates
                             (checkin_date=checkin_date,
                              checkout_date=checkout_date, duration=False))
            duration = duration_vals.get('duration') or 0.0
            folio_vals = {
                'date_order': reservation.date_order,
                'warehouse_id': reservation.warehouse_id.id,
                'partner_id': reservation.partner_id.id,
                'pricelist_id': reservation.pricelist_id.id,
                'partner_invoice_id': reservation.partner_invoice_id.id,
                'partner_shipping_id': reservation.partner_shipping_id.id,
                'checkin_date': reservation.checkin,
                'checkout_date': reservation.checkout,
                'duration': duration,
                'reservation_id': reservation.id,
                'service_lines': reservation['folio_id']
            }
            date_a = (datetime.datetime
                      (*time.strptime(reservation['checkout'],
                                      DEFAULT_SERVER_DATETIME_FORMAT)[:5]))
            date_b = (datetime.datetime
                      (*time.strptime(reservation['checkin'],
                                      DEFAULT_SERVER_DATETIME_FORMAT)[:5]))
            for line in reservation.reservation_line:
                for r in line.reserve:
                    folio_lines.append((0, 0, {
                        'checkin_date': checkin_date,
                        'checkout_date': checkout_date,
                        'product_id': r.product_id and r.product_id.id,
                        'name': reservation['reservation_no'],
                        'product_uom': r['uom_id'].id,
                        'price_unit': r['lst_price'],
                        'product_uom_qty': ((date_a - date_b).days) + 1
                    }))
                    r.write({'status': 'occupied', 'isroom': False})
            folio_vals.update({'room_lines': folio_lines})
            folio = hotel_folio_obj.create(folio_vals)
            self._cr.execute('insert into hotel_folio_reservation_rel'
                             '(order_id, invoice_id) values (%s,%s)',
                             (reservation.id, folio.id)
                             )
            for line in reservation.reservation_line:
                for r in line.reserve:
                    vals = {'room_id': r.id,
                        'check_in': checkin_date,
                        'check_out': checkout_date,
                        'folio_id':folio.id,
                        }
                    self.env['folio.room.line'].create(vals)
            reservation.write({'state': 'done'})
        return True

    @api.multi
    def onchange_check_dates(self, checkin_date=False, checkout_date=False,
                             duration=False):
        '''
        This mathod gives the duration between check in checkout if
        customer will leave only for some hour it would be considers
        as a whole day. If customer will checkin checkout for more or equal
        hours, which configured in company as additional hours than it would
        be consider as full days
        --------------------------------------------------------------------
        @param self: object pointer
        @return: Duration and checkout_date
        '''
        value = {}
        configured_addition_hours = 0
        company_ids = self.env['res.company'].search([])
        if company_ids.ids:
            configured_addition_hours = company_ids[0].additional_hours
        duration = 0
        if checkin_date and checkout_date:
            chkin_dt = (datetime.datetime.strptime
                        (checkin_date, DEFAULT_SERVER_DATETIME_FORMAT))
            chkout_dt = (datetime.datetime.strptime
                         (checkout_date, DEFAULT_SERVER_DATETIME_FORMAT))
            duration_day = chkout_dt - chkin_dt
            duration = duration_day.days + 1
            if configured_addition_hours > 0:
                additional_hours = abs((duration_day.seconds / 60) / 60)
                if additional_hours >= configured_addition_hours:
                    duration += 1
        value.update({'duration': duration})
        return value

    @api.model
    def create(self, vals):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        if not vals:
            vals = {}
        if self._context is None:
            self._context = {}
        vals['reservation_no'] = self.env['ir.sequence'
                                          ].next_by_code('hotel.reservation'
                                                         ) or 'New'
        return super(hotel_reservation, self).create(vals)


class hotel_reservation_line(models.Model):

    _name = "hotel_reservation.line"
    _description = "Reservation Line"

    name = fields.Char('Name', size=64)
    line_id = fields.Many2one('hotel.reservation')
    reserve = fields.Many2many('hotel.room',
                               'hotel_reservation_line_room_rel',
                               'room_id', 'hotel_reservation_line_id',
                               domain="[('isroom','=',True),\
                               ('categ_id','=',categ_id)]")
    categ_id = fields.Many2one('product.category', 'Room Type',
                               domain="[('isroomtype','=',True)]",
                               change_default=True)

    @api.onchange('categ_id')
    def on_change_categ(self):
        '''
        When you change categ_id it check checkin and checkout are
        filled or not if not then raise warning
        -----------------------------------------------------------
        @param self: object pointer
        '''
        if not self.line_id.checkin or not self.line_id.checkout:
            raise except_orm(_('Warning'),
                             _('Before choosing a room,\n You have to select \
                             a Check in date or a Check out date in \
                             the reservation form.'))
        if not self.categ_id:
            return {'domain': {'reserve': [('id', 'in', [])]}}
        room_ids = []
        assigned_room = self.env['hotel.room.reservation.line'].\
                search([
                        ('status', '=', 'confirm'),
                        ('room_id.categ_id', '=', self.categ_id.id),
                        '&','|',
                        ('check_in', '>=',self.line_id.checkin),
                        ('check_out', '>=',self.line_id.checkin),
                        '|',
                        ('check_in', '<=',self.line_id.checkout),
                        ('check_out', '<=',self.line_id.checkout),
                       ])
        folio_line_ids = self.env['folio.room.line'].\
                        search([ 
                               ('status', 'not in', ['done', 'cancel']),
                               ('room_id.categ_id', '=', self.categ_id.id),
                               '&','|',
                                ('check_in', '>=',self.line_id.checkin),
                                ('check_out', '>=',self.line_id.checkin),
                                '|',
                                ('check_in', '<=',self.line_id.checkout),
                                ('check_out', '<=',self.line_id.checkout),
                               ])
        room_ids.extend([room.room_id.id for room in assigned_room])
        room_ids.extend([room.room_id.id for room in folio_line_ids])
        room_ids = list(set(room_ids))
        domain = {'reserve': [('id', 'not in', room_ids),('categ_id', '=', self.categ_id.id)]}
        return {'domain': domain}

    @api.multi
    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        reservation_line_obj = self.env['hotel.room.reservation.line']
        for reserv_rec in self:
            for rec in reserv_rec.reserve:
                hres_arg = [('room_id', '=', rec.id),
                            ('reservation_id', '=', reserv_rec.line_id.id)]
                myobj = reservation_line_obj.search(hres_arg)
                if myobj.ids:
                    rec.write({'isroom': True, 'status': 'available'})
                    myobj.unlink()
        return super(hotel_reservation_line, self).unlink()


class hotel_room_reservation_line(models.Model):

    _name = 'hotel.room.reservation.line'
    _description = 'Hotel Room Reservation'
    _rec_name = 'room_id'

    room_id = fields.Many2one(comodel_name='hotel.room', string='Room id')
    check_in = fields.Datetime('Check In Date', required=True)
    check_out = fields.Datetime('Check Out Date', required=True)
    state = fields.Selection([('assigned', 'Assigned'),
                              ('unassigned', 'Unassigned')], 'Room Status')
    reservation_id = fields.Many2one('hotel.reservation',
                                     string='Reservation')
    status = fields.Selection(string='state', related='reservation_id.state')

hotel_room_reservation_line()


class hotel_room(models.Model):

    _inherit = 'hotel.room'
    _description = 'Hotel Room'

    room_reservation_line_ids = fields.One2many('hotel.room.reservation.line',
                                                'room_id',
                                                string='Room Reserv Line')

    @api.model
    def cron_room_line(self):
        """
        This method is for scheduler
        every 1min scheduler will call this method and check Status of
        room is occupied or available
        --------------------------------------------------------------
        @param self: The object pointer
        @return: update status of hotel room reservation line
        """
        now = datetime.datetime.now()
        curr_date = now.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        for room in self.search([]):
            reserv_line_ids = [reservation_line.ids for
                               reservation_line in
                               room.room_reservation_line_ids]
            reserv_args = [('id', 'in', reserv_line_ids),
                           ('check_in', '<=', curr_date),
                           ('check_out', '>=', curr_date)]
            reservation_line_ids = self.env['hotel.room.reservation.line'
                                            ].search(reserv_args)
            rooms_ids = [room_line.ids for room_line in room.room_line_ids]
            rom_args = [('id', 'in', rooms_ids),
                        ('check_in', '<=', curr_date),
                        ('check_out', '>=', curr_date)]
            room_line_ids = self.env['folio.room.line'].search(rom_args)
            status = {'isroom': True, 'color': 5}
            if reservation_line_ids.ids:
                status = {'isroom': False, 'color': 2}
            room.write(status)
            if room_line_ids.ids:
                status = {'isroom': False, 'color': 2}
            room.write(status)
            if reservation_line_ids.ids and room_line_ids.ids:
                raise except_orm(_('Wrong Entry'),
                                 _('Please Check Rooms Status \
                                 for %s.' % (room.name)))
        return True


class room_reservation_summary(models.Model):

    _name = 'room.reservation.summary'
    _description = 'Room reservation summary'

    date_from = fields.Datetime('Date From')
    date_to = fields.Datetime('Date To')
    summary_header = fields.Text('Summary Header')
    room_summary = fields.Text('Room Summary')

    @api.model
    def default_get(self, fields):
        """
        To get default values for the object.
        @param self: The object pointer.
        @param fields: List of fields for which we want default values
        @return: A dictionary which of fields with values.
        """
        context = self._context
        if context is None:
            context = {}
        res = super(room_reservation_summary, self).default_get(fields)
        if not self.date_from and not self.date_to:
            date_today = datetime.datetime.today()
            first_day = datetime.datetime(date_today.year,
                                          date_today.month, 1, 0, 0, 0)
            first_temp_day = first_day + relativedelta(months=1)
            last_temp_day = first_temp_day - relativedelta(days=1)
            last_day = datetime.datetime(last_temp_day.year,
                                         last_temp_day.month,
                                         last_temp_day.day, 23, 59, 59)
            first_day = _offset_format_timestamp_extended(str(first_day), \
                        DEFAULT_SERVER_DATETIME_FORMAT,
                        DEFAULT_SERVER_DATETIME_FORMAT,
                        context=context)
            last_day = _offset_format_timestamp_extended(str(last_day), \
                        DEFAULT_SERVER_DATETIME_FORMAT,
                        DEFAULT_SERVER_DATETIME_FORMAT,
                        context=context)
            res.update({
                        'date_from': first_day, 
                        'date_to': last_day
                        })
        return res

    @api.multi
    def room_reservation(self):
        '''
        @param self: object pointer
        '''
        if self._context is None:
            self._context = {}
        model_data_ids = self.env['ir.model.data'
                                  ].search([('model', '=', 'ir.ui.view'),
                                            ('name',
                                             '=',
                                             'view_hotel_reservation_form')])
        resource_id = model_data_ids.read(fields=['res_id'])[0]['res_id']
        return {'name': _('Reconcile Write-Off'),
                'context': self._context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'hotel.reservation',
                'views': [(resource_id, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'new',
                }

    @api.onchange('date_from', 'date_to')
    def get_room_summary(self):
        '''
        @param self: object pointer
         '''
        context = self._context
        if context is None:
            context = {}
        res = {}
        all_detail = []
        room_obj = self.env['hotel.room']
        reservation_line_obj = self.env['hotel.room.reservation.line']
        date_range_list = []
        main_header = []
        summary_header_list = ['Rooms']
        date_from = _offset_format_timestamp_extended(str(self.date_from), \
                        DEFAULT_SERVER_DATETIME_FORMAT,
                        DEFAULT_SERVER_DATETIME_FORMAT,
                        context=context, reverse=True)
        date_to = _offset_format_timestamp_extended(str(self.date_to), \
                        DEFAULT_SERVER_DATETIME_FORMAT,
                        DEFAULT_SERVER_DATETIME_FORMAT,
                        context=context, reverse=True)
        if date_from and date_to:
            if date_from > date_to:
                raise except_orm(_('User Error!'),
                                 _('Please Check Time period Date \
                                 From can\'t be greater than Date To !'))
            d_frm_obj = (datetime.datetime.strptime
                         (date_from, DEFAULT_SERVER_DATETIME_FORMAT))
            d_to_obj = (datetime.datetime.strptime
                        (date_to, DEFAULT_SERVER_DATETIME_FORMAT))
            temp_date = d_frm_obj
            while(temp_date.date() <= d_to_obj.date()):
                val = ''
                val = (str(temp_date.strftime("%a")) + ' ' +
                       str(temp_date.strftime("%b")) + ' ' +
                       str(temp_date.strftime("%d")))
                summary_header_list.append(val)
                date_range_list.append(temp_date.strftime
                                       (DEFAULT_SERVER_DATETIME_FORMAT))
                temp_date = temp_date + datetime.timedelta(days=1)
            all_detail.append(summary_header_list)
            room_ids = room_obj.search([])
            all_room_detail = []
            for room in room_ids:
                room_detail = {}
                room_list_stats = []
                room_detail.update({'name': room.name or ''})
                
                if not room.room_reservation_line_ids:
                    for chk_date in date_range_list:
                        
                        room_list_stats.append({'state': 'Free',
                                                'date': chk_date,
                                                'room_id': room.id,
                                                })
                else:
                    for chk_date in date_range_list:
                        for room_res_line in room.room_reservation_line_ids:
                            reservline_ids = [i.ids for i in
                                              room.room_reservation_line_ids]
                            reservline_ids = (reservation_line_obj.search
                                              ([('id', 'in', reservline_ids),
                                                ('check_in', '<=', chk_date),
                                                ('check_out', '>=', chk_date),
                                                ('status','!=','cancel')
                                                ]))
                            if reservline_ids:
                                room_list_stats.append({'state': 'Reserved',
                                                        'date': chk_date,
                                                        'room_id': room.id})
                                break
                            else:
                                room_list_stats.append({'state': 'Free',
                                                        'date': chk_date,
                                                        'room_id': room.id})
                                break
                room_detail.update({'value': room_list_stats})
                all_room_detail.append(room_detail)
            main_header.append({'header': summary_header_list})
            self.summary_header = str(main_header)
            self.room_summary = str(all_room_detail)
        return res


class quick_room_reservation(models.TransientModel):
    _name = 'quick.room.reservation'
    _description = 'Quick Room Reservation'

    partner_id = fields.Many2one('res.partner', string="Customer",
                                 required=True)
    check_in = fields.Datetime('Check In', required=True)
    check_out = fields.Datetime('Check Out', required=True)
    room_id = fields.Many2one('hotel.room', 'Room', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Hotel', required=True)
    pricelist_id = fields.Many2one('product.pricelist', 'pricelist',
                                   required=True)
    partner_invoice_id = fields.Many2one('res.partner', 'Invoice Address',
                                         required=True)
    partner_order_id = fields.Many2one('res.partner', 'Ordering Contact',
                                       required=True)
    partner_shipping_id = fields.Many2one('res.partner', 'Delivery Address',
                                          required=True)
    adults = fields.Integer('Adults',
                            help='List of adults there in guest list. ')
    children = fields.Integer('Children',
                              help='Number of children there in guest list.')

    @api.onchange('check_out', 'check_in')
    def on_change_check_out(self):
        '''
        When you change checkout or checkin it will check whether
        Checkout date should be greater than Checkin date
        and update dummy field
        -----------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        '''
        if self.check_out and self.check_in:
            if self.check_out < self.check_in:
                raise except_orm(_('Warning'),
                                 _('Checkout date should be greater \
                                 than Checkin date.'))

    @api.onchange('partner_id')
    def onchange_partner_id_res(self):
        '''
        When you change partner_id it will update the partner_invoice_id,
        partner_shipping_id and pricelist_id of the hotel reservation as well
        ---------------------------------------------------------------------
        @param self: object pointer
        '''
        if not self.partner_id:
            self.partner_invoice_id = False
            self.partner_shipping_id = False
            self.partner_order_id = False
        else:
            addr = self.partner_id.address_get(['delivery', 'invoice',
                                                'contact'])
            self.partner_invoice_id = addr['invoice']
            self.partner_order_id = addr['contact']
            self.partner_shipping_id = addr['delivery']
            self.pricelist_id = self.partner_id.property_product_pricelist.id

    @api.model
    def default_get(self, fields):
        """
        To get default values for the object.
        @param self: The object pointer.
        @param fields: List of fields for which we want default values
        @return: A dictionary which of fields with values.
        """
        if self._context is None:
            self._context = {}
        res = super(quick_room_reservation, self).default_get(fields)
        if self._context:
            keys = self._context.keys()
            if 'date' in keys:
                temp_date = _offset_format_timestamp_extended(\
                        str(self._context['date']), 
                        DEFAULT_SERVER_DATETIME_FORMAT,
                        DEFAULT_SERVER_DATETIME_FORMAT,
                        context=self._context,)
                
                res.update({'check_in': temp_date})
            if 'room_id' in keys:
                roomid = self._context['room_id']
                res.update({'room_id': int(roomid)})
        return res

    @api.multi
    def room_reserve(self):
        """
        This method create a new record for hotel.reservation
        -----------------------------------------------------
        @param self: The object pointer
        @return: new record set for hotel reservation.
        """
        hotel_res_obj = self.env['hotel.reservation']
        for res in self:
            (hotel_res_obj.create
             ({'partner_id': res.partner_id.id,
               'partner_invoice_id': res.partner_invoice_id.id,
               'partner_order_id': res.partner_order_id.id,
               'partner_shipping_id': res.partner_shipping_id.id,
               'checkin': res.check_in,
               'checkout': res.check_out,
               'warehouse_id': res.warehouse_id.id,
               'pricelist_id': res.pricelist_id.id,
               'adults': res.adults,
               'children': res.children,
               'reservation_line': [(0, 0,
                                     {
                                      'categ_id': res.room_id.categ_id.id, 
                                      'reserve': [(6, 0, [res.room_id.id])],
                                      'name': (res.room_id and
                                               res.room_id.name or '')
                                      })]
               }))
        return True
