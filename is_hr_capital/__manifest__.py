# -*- coding: utf-8 -*-
{
    'name': "Capital HR Custmization",

    'summary': """
       Loans,Payroll,Overtime,Leave Customization""",

    'description': """ This Module contains customization of loan in including all types,payroll , Leave and overtime 
                        management.                
    """,

    'author': "IntelliSoft Software",
    'website': "http://www.intellisoft.sd",
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_attendance', 'hr_contract', 'hr_payroll', 'hr_holidays', 'hr_recruitment', 'survey', 'hr_payroll_account' , 'account'],

    # always loaded
    'data': [
        'data/is_cap_sequence.xml',
        'data/is_cap_payroll_structure.xml',
        'security/is_hr_cap_security.xml',
        'security/ir.model.access.csv',

        'views/is_cap_employee_view.xml',
        'views/is_cap_config_view.xml',
        'views/is_cap_contract_view.xml',
        'views/is_cap_loan_view.xml',
        'views/is_cap_long_loan_view.xml',
        'views/is_cap_overtime_view.xml',
        'views/is_cap_penalty_view.xml',
        'views/is_cap_trip.xml',
        'views/is_cap_payslip_view.xml',
        'views/is_cap_leave_views.xml',

        'wizard/wizard_overtime_view.xml',
    ],
    'application': True,
}
