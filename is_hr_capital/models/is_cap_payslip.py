from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from datetime import datetime
import calendar
import time
from odoo.exceptions import UserError, ValidationError


class CapPayslip(models.Model):
    _inherit = "hr.payslip"

    # bank_acct_num = fields.Char(string='Bank Account Number', related='employee_id.bank_account_id', store=True)
    code = fields.Char(string='Code', related='employee_id.code', store=True)

    absent_deduction = fields.Float(string='absent deduction', readonly=True, compute='compute_penalty')
    delay_deduction = fields.Float(string='delay deduction', readonly=True, compute='compute_penalty')

    long_loan = fields.Float(string='Long Loan', readonly=True, compute='get_loan', store=True)
    short_loan = fields.Float(string='Advance Salary', readonly=True, compute='get_short_loan', store=True)
    grants = fields.Float(string='Grants % ')
    worked_days = fields.Float(string='Days', compute='_compute_days', store=True)
    no_of_days = fields.Integer(string='Days', compute='_compute_days', store=True)
    net_salary = fields.Float("Net Salary", compute='get_net_salary', store=True)
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payslip Batches', readonly=True,
                                     copy=False, states={'draft': [('readonly', False)]}, ondelete='cascade')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Rejected'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft',
        help="""* When the payslip is created the status is \'Draft\'
                    \n* If the payslip is confirmed by hr, the status is \'Confirmed\'.
                    \n* If the payslip is under verification, the status is \'Waiting\'.
                    \n* If the payslip is confirmed by account then status is set to \'Done\'.
                    \n* When user cancel payslip the status is \'Rejected\'.""")

    @api.depends('employee_id', 'contract_id')
    def compute_penalty(self):
        for rec in self:
            if rec.employee_id and rec.contract_id:
                employee_salary = rec.employee_id.contract_id.wage
                absent_days = 0
                delay_days = 0
                rec.delay_deduction = 0.0
                rec.absent_deduction = 0.0
                penalty_ids = self.env['hr.emp.penalty'].search(
                    [('employee_id', '=', rec.employee_id.id), ('date', '<=', rec.date_to), ('state','=','done')])
                for pan in penalty_ids:
                    if pan.violation_id.deduction_type == 'day':
                        absent_days += pan.penalty
                    if pan.violation_id.deduction_type == 'hour':
                        delay_days += pan.penalty
                rec.absent_deduction = (employee_salary / 30) * absent_days
                rec.delay_deduction = (employee_salary / 14400) * delay_days
                print('rec.absent_deduction',rec.absent_deduction)
                print('rec.delay_deduction',rec.delay_deduction)

    # @api.depends('employee_id', 'date_from', 'date_to')
    # def compute_installment_ded(self):
    #     for rec in self:
    #         if rec.employee_id:
    #             installemnt_ids = self.env['hr.installment.line'].search(
    #                 [('employee_id', '=', rec.employee_id.id), ('date_to', '>=', rec.date_to)])
    #             for installemnt_id in installemnt_ids:
    #                 # finance = x.env['finance.approval'].search([('grand_id', '=', grand.id)])
    #                 if installemnt_id.state != 'paid':
    #                     payslip_date_to = rec.date_to
    #                     installment_date_to = installemnt_id.date_to
    #                     payslip_date_to = datetime.strptime(str(payslip_date_to), '%Y-%m-%d')
    #                     installment_date_to = datetime.strptime(str(installment_date_to), '%Y-%m-%d')
    #                     grand_month = installment_date_to.month
    #                     payslip_month = payslip_date_to.month
    #                     if grand_month == payslip_month:
    #                         installemnt_id.write({'mod_check': True})
    #                         rec.installment_ded += installemnt_id.deduction_mod
    #                     else:
    #                         rec.installment_ded += installemnt_id.deduction

    @api.depends('employee_id', 'line_ids')
    def get_net_salary(self):
        for rec in self:
            net = 0.00
            total = 0.00
            if rec.line_ids and rec.employee_id:
                payslip_line_ids = self.env['hr.payslip.line'].search([('employee_id', '=', rec.employee_id.id),
                                                                       ('code', '=', 'NET'),
                                                                       ('slip_id', '=', rec.id)])

                for slip in payslip_line_ids:
                    total = slip.total
            rec.net_salary = total

    @api.depends('date_from', 'date_to')
    def _compute_days(self):
        # str_now = datetime.now().date()
        days = 0
        month_range = 1
        for slip in self:
            if slip.date_from and slip.date_to:
                date_from = datetime.strptime(str(slip.date_from), '%Y-%m-%d')
                month_range = calendar.monthrange(date_from.year, date_from.month)[1]
                date_to = datetime.strptime(str(slip.date_to), '%Y-%m-%d')
                days = (date_to - date_from).days + 1
            slip.no_of_days = days
            if month_range > 0:
                worked_days = float(days)/(month_range)
            else:
                raise Warning(_("Please Enter Valid Dates for this payslip "))
            if worked_days > 1.00:
                slip.worked_days = 1
            else:
                slip.worked_days = worked_days

    def action_hr_confirm(self):
        for rec in self:
            rec.compute_sheet()
            rec.state = 'confirm'

    @api.depends('employee_id', 'date_to', 'date_from')
    def compute_unpaid(self):
        for x in self:
            # if x.worked_days_line_ids:
            unpaid_sum = 0.0
            total_unpaid_salary = 0.0
            unpaid_ids = self.env['hr.leave'].search([('employee_id', '=', x.employee_id.id),
                                                      ('date_from', '>=', x.date_from),
                                                      ('date_to', '<=', x.date_to),
                                                      ('holiday_status_id', '=', self.env.ref('hr_holidays.holiday_status_unpaid').id),
                                                      ('state', '=', 'validate')])
            if unpaid_ids:
                for leave in unpaid_ids:
                    # if worked_ids.code == 'Unpaid':
                    unpaid_sum += leave.number_of_days_temp
                employee_salary = x.employee_id.contract_id.wage
                total_unpaid_salary = employee_salary * unpaid_sum / 30
            x.unpaid_leave = total_unpaid_salary

    @api.depends('employee_id', 'date_to', 'date_from')
    def get_loan(self):
        for rec in self:
            if rec.employee_id:
                loan_ids = rec.env['hr.loan.line'].search(
                    [('employee_id', '=', rec.employee_id.id), ('paid', '=', False),
                     ('paid_date', '<=', rec.date_to), ('paid_date', '>=', rec.date_from), ('loan_id.state', '=', 'done')])
                for loan_id in loan_ids:
                        rec.long_loan = loan_id.paid_amount

    @api.depends('employee_id', 'date_to', 'date_from')
    def get_short_loan(self):
        for x in self:
            if x.employee_id:
                amount = 0.00
                loan_ids = x.env['hr.monthlyloan'].search(
                    [('employee_id', '=', x.employee_id.id), ('state', '=', 'done'), ('date', '>=', x.date_from),
                     ('date', '<=', x.date_to)])
                for loan in loan_ids:
                    amount += loan.loan_amount
                x.short_loan = amount

    def action_payslip_done(self):
        for payslip in self:
            if payslip.employee_id:
                payslip_obj = payslip.search(
                    [('employee_id', '=', payslip.employee_id.id), ('name', '=', payslip.name), ('state', '!=', 'done')])
                if payslip_obj:
                    raise Warning(_("This Employee Already Took This Month's Salary!"))
            loan_ids = payslip.env['hr.loan.line'].search(
                [('employee_id', '=', payslip.employee_id.id), ('paid', '=', False)])
            for line in loan_ids:
                if line.paid_date >= payslip.date_from and line.paid_date <= payslip.date_to and line.loan_id.state == 'done':
                    if not line.paid:
                        # line.payroll_id = payslip.id
                        line.action_paid_amount()
                else:
                    line.payroll_id = False

            short_loan_ids = payslip.env['hr.monthlyloan'].search(
                [('employee_id', '=', payslip.employee_id.id), ('state', '=', 'done'),
                 ('date', '>=', payslip.date_from),
                 ('date', '<=', payslip.date_to)])
            for short_loan in short_loan_ids:
                short_loan.action_paid()
        return super(CapPayslip, self).action_payslip_done()

    @api.constrains('name')
    def _no_duplicate_payslips(self):
        for rec in self:
            if self.employee_id:
                payslip_obj = self.search([('employee_id', '=', rec.employee_id.id), ('name', '=', rec.name)])
                if len(payslip_obj) > 1:
                    raise Warning(_("This Employee Already Took his Month's Salary!"))


class CapPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Verify'),
        ('close', 'Done'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')

    grants = fields.Float(string='Grants % ')

    def close_payslip_run(self):
        for slip in self:
            for slip_run in slip.slip_ids:
                slip_run.action_payslip_done()
        return super(CapPayslipRun, self).close_payslip_run()

    def action_hr_confirm(self):
        for slip in self:
            slip.state = 'confirm'
            for slip_run in slip.slip_ids:
                slip_run.action_hr_confirm()

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise Warning(_("Warning! You cannot delete a payslip which is in %s state.") % (rec.state))
        return super(CapPayslipRun, self).unlink()


class WizardPayslipRecompute(models.TransientModel):
    _name = 'wizard.payslip.recompute'

    def action_recompute_payslip(self):
        for rec in self:
            payslip_ids = self.env['hr.payslip'].browse(self.env.context.get('active_ids'))
            for emp in payslip_ids:
                emp.compute_sheet()

