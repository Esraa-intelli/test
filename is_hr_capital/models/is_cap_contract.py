# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrContract(models.Model):
    _inherit = 'hr.contract'

    def get_default_currency(self):
        for rec in self:
            rec.currency_id = rec.company_id.currency_id.id

    wage = fields.Monetary(string='Gross Salary',track_visibility='onchange')
    currency_id = fields.Many2one(string="Currency", default=get_default_currency, readonly=False)
    basic = fields.Monetary(string='Basic Salary',track_visibility='onchange')
    cola_allowance = fields.Monetary(string='Cola',track_visibility='onchange')
    housing_allowance = fields.Monetary(string='Housing Allowance', track_visibility='onchange')
    transportation_allowance = fields.Monetary(string='Transportation Allowance', track_visibility='onchange')

    income_tax = fields.Boolean(string='Personal Income Tax', default=True)
    social_insurance = fields.Boolean(string='Social Insurance', default=False)
    social_insurance_type = fields.Selection([('amount', 'Fixed Amount'), ('percentage', 'Percentage 8%'),
                                    ], string='Social Insurance Type', track_visibility='onchange')
    insurance_amount = fields.Monetary(string='Insurance Amount',track_visibility='onchange')
    medical_deduction = fields.Monetary(string='Medical Deduction', track_visibility='onchange')
    phone = fields.Monetary(string='Phone', default=True)

    @api.onchange('wage')
    def compute_basic(self):
        for rec in self:
            if rec.wage > 0:
                num = self.env['payroll.calculation'].search([], order='id DESC', limit=1).employee_basic
                rec.basic = rec.wage * num / 100
                num = self.env['payroll.calculation'].search([], order='id DESC', limit=1).cola
                rec.cola_allowance = rec.wage * num / 100
                num = self.env['payroll.calculation'].search([], order='id DESC', limit=1).housing
                rec.housing_allowance = rec.wage * num / 100
                num = self.env['payroll.calculation'].search([], order='id DESC', limit=1).transportation
                rec.transportation_allowance = rec.wage * num / 100
            else:
                rec.basic = 0
                rec.cola_allowance = 0
                rec.housing_allowance = 0
                rec.transportation_allowance = 0






