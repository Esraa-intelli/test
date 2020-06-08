# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class OvertimeSetting(models.Model):
    _name = 'overtime.setting'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(default='Overtime Setting', string='Reference',readonly=1)
    normal_hours = fields.Float(string='Normal Hours', default=1.5, required=True, track_visibility='onchange')
    holiday_hours = fields.Float(string='Holiday Hours', default=2, required=True, track_visibility='onchange')
    days_employee = fields.Integer(string='Divide Employee Salary By', default=240, track_visibility='onchange')
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Overtime Setting Already Exists !"),
    ]


class PayrollCalculation(models.Model):
    _name = 'payroll.calculation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(default='Payroll Calculation', string='Reference',readonly=1)
    employee_basic = fields.Float(string='Basic', default=48, track_visibility='onchange')
    cola = fields.Float(string=' Cola', default=20, track_visibility='onchange')
    housing = fields.Float(string=' Housing', default=14, track_visibility='onchange')
    transportation = fields.Float(string='Transportation', default=18, track_visibility='onchange')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Payroll Calculation Setting Already Exists !"),
    ]
