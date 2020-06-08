# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (c) 2005-2006 Axelor SARL. (http://www.axelor.com)

import logging

from datetime import datetime, time
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.addons.resource.models.resource import HOURS_PER_DAY
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.translate import _
from odoo.tools.float_utils import float_round


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    allocation_ids = fields.One2many('hr.leave.allocation', 'employee_id', string="Annual", index=True)
    # outstanding_balance = fields.Float('Outstanding balance', compute='_compute_outstanding_balance')
    #
    # @api.depands('allocation_ids')
    # def _compute_outstanding_balance(self):
    #     for rec in self:
            

class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    is_annual = fields.Boolean('Is Annual Leave')

    # time_type = fields.Selection([('annual','Annual Leave'),('other','Other Leave')],string='Kind Of Leave')


class HolidaysAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    have_outstanding = fields.Boolean('Have Outstanding balance')
    outstanding_balance = fields.Integer('Outstanding balance')
    activity_id = fields.Many2one('mail.activity', string='Activity')

    @api.onchange('allocation_type')
    def _onchange_allocation_type(self):
        if self.holiday_status_id.is_annual and self.allocation_type == 'accrual':
            self.number_of_days = 0

    @api.model
    def _update_annual_leave_accrual(self):
        """
            Method called by the cron task in order to increment the number_of_days when
            necessary.
        """
        today = fields.Date.from_string(fields.Date.today())

        holidays = self.search(
            [('allocation_type', '=', 'accrual'), ('employee_id.active', '=', True), ('state', '=', 'validate'),
             ('holiday_type', '=', 'employee'),('holiday_status_id.is_annual','=',True),
             '|', ('date_to', '=', False), ('date_to', '>', fields.Datetime.now()),
             '|', ('nextcall', '=', False), ('nextcall', '<=', today)])

        for holiday in holidays:
            print('hallo',holiday.employee_id.remaining_leaves)
            values = {}
            if holiday.employee_id.hiring_date.year == today.year:
                year = today.year + 1
            else:
                year = today.year
            remaining_leaves = holiday.employee_id.remaining_leaves
            hiring_date = fields.Date.from_string(holiday.employee_id.hiring_date)
            outstanding_date = hiring_date.replace(year=year)
            if int(outstanding_date.day) > 15 :
                notify_date = outstanding_date.replace(day=int(outstanding_date.day)-15)
            else:
                if outstanding_date.month-1 ==0:
                    month = 12
                    not_year = outstanding_date.year - 1
                else:
                    month = outstanding_date.month-1
                    not_year = outstanding_date.year
                notify_date = outstanding_date.replace(day=30 - (15 - int(outstanding_date.day)) , month= month ,year=not_year )
            if today == notify_date:
                # get manager
                group_manager = self.env.ref('hr.group_hr_manager').id
                # first of all get users
                self.env.cr.execute(
                    '''SELECT uid FROM res_groups_users_rel WHERE gid = %s order by uid''' % (group_manager))

                # schedule activity for user(s) to approve
                for fm in list(filter(lambda x: (
                        self.env['res.users'].sudo().search([('id', '=', x)])),
                                      self.env.cr.fetchall())):
                    if fm[0] == holiday.employee_id.leave_manager_id.id:

                        holiday.activity_id.unlink()
                        vals = {
                            'activity_type_id': self.env['mail.activity.type'].sudo().search(
                                [('name', 'like', 'Annual Leave')],
                                limit=1).id,
                            'res_id': holiday.id,
                            'res_model_id': self.env['ir.model'].sudo().search([('model', 'like', 'hr.leave.allocation')],
                                                                               limit=1).id,
                            'user_id': fm[0] or 1,
                            'summary': holiday.employee_id.name + ' Will Have Annual Leave After 15 Day ',
                        }
                        # add lines
                        holiday.activity_id = self.env['mail.activity'].sudo().create(vals)

            if today == outstanding_date:
                values = {
                    'name': str(holiday.name) +''+ str(year ),
                    'holiday_type': 'employee',
                    'holiday_status_id': holiday.holiday_status_id.id,
                    'notes': holiday.notes,
                    'number_of_days': holiday.number_per_interval,
                    'parent_id': holiday.id,
                    'employee_id': holiday.employee_id.id,
                    'allocation_type': 'regular',
                    'outstanding_balance': remaining_leaves,
                    # 'date_to': holiday.date_to,
                    # 'interval_unit': self.interval_unit,
                    # 'interval_number': self.interval_number,
                    # 'number_per_interval': self.number_per_interval,
                    # 'unit_per_interval': self.unit_per_interval,
                }

                self.env['hr.leave.allocation'].create(values)
                nextcall = hiring_date.replace(year = outstanding_date.year+1)
                values['nextcall'] = nextcall
                holiday.write(values)

    @api.model
    def _update_accrual(self):
        """
            Method called by the cron task in order to increment the number_of_days when
            necessary.
        """
        today = fields.Date.from_string(fields.Date.today())
        holidays = self.search([('allocation_type', '=', 'accrual'), ('employee_id.active', '=', True), ('state', '=', 'validate'),
                                ('holiday_type', '=', 'employee'),('holiday_status_id.is_annual','!=',True),
                                '|', ('date_to', '=', False), ('date_to', '>', fields.Datetime.now()),
                                '|', ('nextcall', '=', False), ('nextcall', '<=', today)])

        for holiday in holidays:
            values = {}
            delta = relativedelta(days=0)

            if holiday.interval_unit == 'weeks':
                delta = relativedelta(weeks=holiday.interval_number)
            if holiday.interval_unit == 'months':
                delta = relativedelta(months=holiday.interval_number)
            if holiday.interval_unit == 'years':
                delta = relativedelta(years=holiday.interval_number)
            values['nextcall'] = (holiday.nextcall if holiday.nextcall else today) + delta

            period_start = datetime.combine(today, time(0, 0, 0)) - delta
            period_end = datetime.combine(today, time(0, 0, 0))

            # We have to check when the employee has been created
            # in order to not allocate him/her too much leaves
            start_date = holiday.employee_id._get_date_start_work()
            # If employee is created after the period, we cancel the computation
            if period_end <= start_date:
                holiday.write(values)
                continue

            # If employee created during the period, taking the date at which he has been created
            if period_start <= start_date:
                period_start = start_date

            worked = holiday.employee_id._get_work_days_data(period_start, period_end, domain=[('holiday_id.holiday_status_id.unpaid', '=', True), ('time_type', '=', 'leave')])['days']
            left = holiday.employee_id._get_leave_days_data(period_start, period_end, domain=[('holiday_id.holiday_status_id.unpaid', '=', True), ('time_type', '=', 'leave')])['days']
            prorata = worked / (left + worked) if worked else 0

            days_to_give = holiday.number_per_interval
            if holiday.unit_per_interval == 'hours':
                # As we encode everything in days in the database we need to convert
                # the number of hours into days for this we use the
                # mean number of hours set on the employee's calendar
                days_to_give = days_to_give / (holiday.employee_id.resource_calendar_id.hours_per_day or HOURS_PER_DAY)

            values['number_of_days'] = holiday.number_of_days + days_to_give * prorata
            if holiday.accrual_limit > 0:
                values['number_of_days'] = min(values['number_of_days'], holiday.accrual_limit)

            holiday.write(values)



