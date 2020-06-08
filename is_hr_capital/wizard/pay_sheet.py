# -*- coding: utf-8 -*-
###########

from odoo import api, fields, models, _
import xlsxwriter
import base64
import datetime
from io import StringIO, BytesIO
from datetime import *
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from dateutil import relativedelta


class WizardPayslip(models.Model):
    _name = 'wizard.paysheet'
    _description = 'Print Payslip'

    # payslip_report = fields.Binary(string='s')
    # payslip_report_name = fields.Char(string='Payslip Name', default='Pay sheet Report.xls')
    from_date = fields.Date(string='Date From', required=True)
    # default=time.strftime('%Y-%m-01'))
    to_date = fields.Date(string='Date To', required=True,
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          )
    name = fields.Char(string="Payslip")

    def print_report(self):
        for report in self:
            from_date = report.from_date
            to_date = report.to_date
            if self.from_date > self.to_date:
                raise UserError(_("You must be enter start date less than end date !"))
            report.name = 'Pay Sheet From ' + str(from_date) + ' To ' + str(to_date)
            report_title = 'Salaries From ' + str(from_date) + ' To ' + str(to_date)
            file_name = _('Pay Sheet.xlsx')
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            excel_sheet = workbook.add_worksheet('Pay Sheet')
            header_format = workbook.add_format(
                {'bold': True, 'font_color': 'white', 'bg_color': '#808080', 'border': 1})
            header_format_sequence = workbook.add_format(
                {'bold': False, 'font_color': 'black', 'bg_color': 'white', 'border': 1})
            format = workbook.add_format({'bold': False, 'font_color': 'black', 'bg_color': 'white', 'border': 1})
            title_format = workbook.add_format({'bold': True, 'font_color': 'black', 'bg_color': 'white'})
            title_format.set_align('center')
            format.set_align('center')
            header_format_sequence.set_align('center')
            header_format.set_align('center')
            header_format.set_text_wrap()
            excel_sheet.set_row(5, 20)
            excel_sheet.set_column('F:U', 20, )
            format.set_text_wrap()
            format.set_num_format('#,##0.00')
            format_details = workbook.add_format()
            format_details.set_num_format('#,##0.00')
            sequence_id = 0
            col = 0
            row = 5
            first_row = 7
            excel_sheet.write(row, col, '#', header_format)
            col += 1
            excel_sheet.write(row, col, 'code', header_format)
            col += 1
            excel_sheet.write(row, col, 'Name', header_format)
            col += 1
            excel_sheet.write(row, col, 'Department', header_format)
            col += 1
            excel_sheet.write(row, col, 'Job  Title ', header_format)
            col += 1
            excel_sheet.write(row, col, 'Basic 45% ', header_format)
            col += 1
            excel_sheet.write(row, col, 'COLA 20%', header_format)
            col += 1
            excel_sheet.write(row, col, 'Transport 18%', header_format)
            col += 1
            excel_sheet.write(row, col, 'Housing 7%', header_format)
            col += 1
            excel_sheet.write(row, col, 'Social allowance 5%', header_format)
            col += 1
            excel_sheet.write(row, col, 'Acting allowance 5%', header_format)
            col += 1
            excel_sheet.write(row, col, '50 Year Exemption Limit', header_format)
            col += 1
            excel_sheet.write(row, col, 'Gross Salary', header_format)
            col += 1
            excel_sheet.write(row, col, 'Tax', header_format)
            col += 1
            excel_sheet.write(row, col, 'Social Ins.', header_format)
            col += 1
            excel_sheet.write(row, col, 'Delay', header_format)
            col += 1
            excel_sheet.write(row, col, 'Monthly Loan', header_format)
            col += 1
            excel_sheet.write(row, col, 'Long Loan', header_format)
            col += 1
            excel_sheet.write(row, col, 'Other Deduction', header_format)
            col += 1
            excel_sheet.write(row, col, 'Total Deduction', header_format)
            col += 1
            excel_sheet.write(row, col, 'Net Salary', header_format)
            col += 1
            excel_sheet.write(row, col, 'Sig', header_format)
            excel_sheet.set_column(0, 4, 25)
            excel_sheet.set_row(1, 25)
            excel_sheet.merge_range(0, 0, 1, 20, 'MTWA International Investment Co.LTD', title_format)
            excel_sheet.merge_range(2, 0, 3, 20, report_title, title_format)
            excel_sheet.merge_range(3, 0, 4, 20, '', title_format)
            payslip_month_ids = report.env['hr.payslip'].search(
                [('date_to', '<=', to_date), ('date_from', '>=', from_date), ('state', '=', 'done')])
            for payslip_period in payslip_month_ids:
                slip_id = payslip_period.id
                employee = payslip_period.employee_id.id
                employee_id = payslip_period.employee_id.name
                department_id = payslip_period.employee_id.department_id.name
                job_id = payslip_period.employee_id.job_id.name
                employee_code = payslip_period.employee_id.code
                col = 0
                row += 1
                sequence_id += 1
                excel_sheet.write(row, col, sequence_id, header_format_sequence)
                col += 1
                if employee_code:
                    excel_sheet.write(row, col, employee_code, format)
                else:
                    excel_sheet.write(row, col, '', format)
                col += 1
                if employee_id:
                    excel_sheet.write(row, col, employee_id, format)
                else:
                    excel_sheet.write(row, col, '', format)
                col += 1
                if department_id:
                    excel_sheet.write(row, col, department_id, format)
                else:
                    excel_sheet.write(row, col, '', format)
                col += 1
                if job_id:
                    excel_sheet.write(row, col, job_id, format)
                else:
                    excel_sheet.write(row, col, '', format)
                slip_ids = payslip_period.env['hr.payslip.line'].search([('slip_id', '=', slip_id),
                                                                         ('employee_id', '=', employee)])
                basic = 0.0
                cola = 0.0
                unpaid = 0.0
                housing = 0.0
                income_tax = 0.0
                social_alw = 0.0
                long_loan = 0.0
                family_burdens = 0.0
                transport = 0.0
                social_company = 0.0
                tax = 0.0
                gross = 0.0
                representation_alw = 0.0
                social_ins = 0.0
                upper_limit_tax = 0.0
                sh_loan = 0.0
                net = 0.0
                attendance = 0.0
                acting_alw = 0.0
                other_deduction = 0.0
                exemption = 0.0
                for slip_line in slip_ids:
                    category = slip_line.code

                    if category == 'BASIC':
                        basic = slip_line.total
                    if category == 'COLA':
                        cola = slip_line.total
                    if category == 'Unpaid':
                        unpaid = slip_line.total
                    if category == 'HOUSING':
                        housing = slip_line.total
                    if category == 'IncomeTax':
                        income_tax = slip_line.total
                    if category == 'SocialALW':
                        social_alw = slip_line.total
                    if category == 'LOLOAN':
                        long_loan = slip_line.total
                    if category == 'FamilyBurdens':
                        family_burdens = slip_line.total
                    if category == 'TANSPORT':
                        transport = slip_line.amount
                    if category == 'SocialInsComp':
                        social_company = slip_line.total
                    if category == 'TAX':
                        tax = slip_line.total
                    if category == 'GROSS':
                        gross = slip_line.amount
                    if category == 'RepresentationALW':
                        representation_alw = slip_line.total
                    if category == 'SocialIns':
                        social_ins = slip_line.total
                    if category == 'UpperLimitTax':
                        upper_limit_tax = slip_line.total
                    if category == 'SHLOAN':
                        sh_loan = slip_line.total
                    if category == 'NET':
                        net = slip_line.amount
                    if category == 'ATTENDANCE':
                        attendance = slip_line.total
                    if category == 'ActingALW':
                        acting_alw = slip_line.total
                    if category == 'OtherDeduction':
                        other_deduction = slip_line.total
                    if category == 'Exemption':
                        exemption = slip_line.amount
                    col = 5

                    # if basic:
                    excel_sheet.write(row, col, basic, format)
                    col += 1
                    excel_sheet.write(row, col, cola, format)
                    col += 1
                    excel_sheet.write(row, col, transport, format)
                    col += 1
                    excel_sheet.write(row, col, housing, format)
                    col += 1
                    excel_sheet.write(row, col, social_alw, format)
                    col += 1
                    excel_sheet.write(row, col, acting_alw, format)
                    col += 1
                    excel_sheet.write(row, col, exemption, format)
                    col += 1
                    excel_sheet.write(row, col, gross, format)
                    col += 1
                    excel_sheet.write(row, col, tax, format)
                    col += 1
                    excel_sheet.write(row, col, social_ins, format)
                    col += 1
                    excel_sheet.write(row, col, attendance, format)
                    col += 1
                    excel_sheet.write(row, col, sh_loan, format)
                    col += 1
                    excel_sheet.write(row, col, long_loan, format)
                    col += 1
                    excel_sheet.write(row, col, other_deduction, format)
                    col += 1
                    excel_sheet.write_formula(row, col,
                                              'SUM(N' + str(row + 1) + ',O' + str(row + 1) + ',P' + str(row + 1) +
                                              ',Q' + str(row + 1) + ',R' + str(row + 1) + ':S' + str(row + 1) + ')',
                                              format)
                    col += 1
                    excel_sheet.write(row, col, net, format)
                    col += 1
                    excel_sheet.write(row, col, 'Bank', format)
        col = 0
        row += 1
        excel_sheet.merge_range(row, col, row, col + 18, 'Total', header_format)
        excel_sheet.write_formula(row, col + 19, 'SUM(t' + str(first_row) + ':t' + str(row) + ')', header_format)
        excel_sheet.write_formula(row, col + 20, 'SUM(u' + str(first_row) + ':u' + str(row) + ')', header_format)
        excel_sheet.write(row, col + 21, '', header_format)
        workbook.close()
        file_download = base64.b64encode(fp.getvalue())
        fp.close()
        wizardmodel = self.env['payslip.report.excel']
        res_id = wizardmodel.create({'name': file_name, 'file_download': file_download})
        return {
            'name': 'Files to Download',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'payslip.report.excel',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': res_id.id,
        }

    ############################################
class payslip_report_excel(models.TransientModel):
    _name = 'payslip.report.excel'

    name = fields.Char('File Name', size=256, readonly=True)
    file_download = fields.Binary('File to Download', readonly=True)
