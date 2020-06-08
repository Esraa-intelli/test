from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.osv import expression


class HrDepartment(models.Model):
    _inherit = 'hr.department'
    analytic_debit_account_id = fields.Many2one('account.analytic.account', string="Department Analytic Account")


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    code = fields.Char(string='ID No.', required=True,index=True,)
    hiring_date = fields.Date(string="Hiring  Date")
    age = fields.Char(compute='_calculate_age', string='Age')

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name.split(' ')[0] + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        employee_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(employee_ids).name_get()

    @api.depends('birthday')
    def _calculate_age(self):
        str_now = datetime.now().date()
        age = ''
        employee_years = 0
        for employee in self:
            if employee.birthday:
                date_start = datetime.strptime(str(employee.birthday), '%Y-%m-%d').date()
                total_days = (str_now - date_start).days
                employee_years = int(total_days / 365)
                remaining_days = total_days - 365 * employee_years
                employee_months = int(12 * remaining_days / 365)
                employee_days = int(0.5 + remaining_days - 365 * employee_months / 12)
                age = str(employee_years) + ' Year(s) ' + str(employee_months) + ' Month(s) ' + str(
                    employee_days) + ' day(s)'
            employee.age = age
            employee.age_in_years = employee_years





