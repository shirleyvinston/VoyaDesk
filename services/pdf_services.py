import os
import re

from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors


def generate_pdf(data):

    # =========================================
    # BASIC DATA
    # =========================================

    emp_name = data['emp_name']
    emp_id = data['emp_id']

    project_name = data['project_name']
    site_name = data['site_name']

    request_date = data['request_date']
    departure_date = data['departure_date']
    return_date = data['return_date']

    total_days = data['total_days']

    period_name = data['period_name']
    quarter = data['quarter']

    purpose = data['purpose']
    reason_text = data['reason_text']

    amount_requested = data['amount_requested']

    generated_link = data['generated_link']

    request_form = data['request_form']

    # =========================================
    # FILE NAME
    # =========================================

    safe_filename = (
        generated_link.replace('/', '_')
        + f"_{emp_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    )

    safe_filename = re.sub(
        r'[^A-Za-z0-9_-]',
        '_',
        safe_filename
    )

    pdf_filename = safe_filename + ".pdf"

    pdf_path = os.path.join(
        "pdfs",
        pdf_filename
    )

    # =========================================
    # PDF DOCUMENT
    # =========================================

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter
    )

    styles = getSampleStyleSheet()

    elements = []

    # =========================================
    # TITLE
    # =========================================

    title = Paragraph(
        "<b>Travel Expense Claim Sheet</b>",
        styles['Title']
    )

    elements.append(title)

    elements.append(Spacer(1, 20))

    # =========================================
    # DETAILS TABLE
    # =========================================

    details = [

        ['Employee Name', emp_name],
        ['Employee ID', emp_id],
        ['Project', project_name],
        ['Site', site_name],
        ['Request Date', request_date],
        ['Departure Date', departure_date],
        ['Return Date', return_date],
        ['Total Days', total_days],
        ['Period', period_name],
        ['Quarter', quarter],
        ['Purpose', purpose],
        ['Reason', reason_text]

    ]

    details_table = Table(
        details,
        colWidths=[200, 300]
    )

    details_table.setStyle(TableStyle([

        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10)

    ]))

    elements.append(details_table)

    elements.append(Spacer(1, 20))

    # =========================================
    # TRAVEL TABLE
    # =========================================

    travel_data = [[
        'Date',
        'From',
        'To',
        'Mode',
        'Persons',
        'Amount'
    ]]

    travel_dates = request_form.getlist('travel_date[]')
    travel_froms = request_form.getlist('travel_from[]')
    travel_tos = request_form.getlist('travel_to[]')
    travel_modes = request_form.getlist('travel_mode[]')
    travel_persons = request_form.getlist('travel_persons[]')
    travel_amounts = request_form.getlist('travel_amount[]')

    for i in range(len(travel_dates)):

        if not travel_dates[i]:
            continue

        travel_data.append([

            travel_dates[i],
            travel_froms[i],
            travel_tos[i],
            travel_modes[i],
            travel_persons[i],
            travel_amounts[i]

        ])

    elements.append(
        Paragraph(
            "<b>Travelling Expenses</b>",
            styles['Heading2']
        )
    )

    travel_table = Table(travel_data)

    travel_table.setStyle(TableStyle([

        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 9)

    ]))

    elements.append(travel_table)

    elements.append(Spacer(1, 20))

    # =========================================
    # ACCOMMODATION TABLE
    # =========================================

    acc_data = [[
        'From',
        'To',
        'Stay At',
        'Persons',
        'Total Days',
        'Initial Amount',
        'Total Amount'
    ]]

    acc_froms = request_form.getlist('acc_from[]')
    acc_tos = request_form.getlist('acc_to[]')
    acc_stays = request_form.getlist('acc_stay[]')
    acc_persons = request_form.getlist('acc_persons[]')
    acc_days = request_form.getlist('acc_days[]')
    acc_initials = request_form.getlist('acc_initial[]')
    acc_amounts = request_form.getlist('acc_amount[]')

    for i in range(len(acc_froms)):

        if not acc_froms[i]:
            continue

        acc_data.append([

            acc_froms[i],
            acc_tos[i],
            acc_stays[i],
            acc_persons[i],
            acc_days[i],
            acc_initials[i],
            acc_amounts[i]

        ])

    elements.append(
        Paragraph(
            "<b>Accommodation Expenses</b>",
            styles['Heading2']
        )
    )

    acc_table = Table(acc_data)

    acc_table.setStyle(TableStyle([

        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 9)

    ]))

    elements.append(acc_table)

    elements.append(Spacer(1, 20))

    # =========================================
    # BOARDING TABLE
    # =========================================

    boarding_data = [[
        'From',
        'To',
        'Total Days',
        'Initial Amount',
        'Total Amount'
    ]]

    board_froms = request_form.getlist('boarding_from[]')
    board_tos = request_form.getlist('boarding_to[]')
    board_days = request_form.getlist('boarding_days[]')
    board_initials = request_form.getlist('boarding_initial[]')
    board_amounts = request_form.getlist('boarding_amount[]')

    for i in range(len(board_froms)):

        if not board_froms[i]:
            continue

        boarding_data.append([

            board_froms[i],
            board_tos[i],
            board_days[i],
            board_initials[i],
            board_amounts[i]

        ])

    elements.append(
        Paragraph(
            "<b>Boarding Expenses</b>",
            styles['Heading2']
        )
    )

    boarding_table = Table(boarding_data)

    boarding_table.setStyle(TableStyle([

        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 9)

    ]))

    elements.append(boarding_table)

    elements.append(Spacer(1, 20))

    # =========================================
    # CONVEYANCE TABLE
    # =========================================

    conveyance_data = [[
        'From',
        'To',
        'Total Days',
        'Initial Amount',
        'Total Amount'
    ]]

    conv_froms = request_form.getlist('conveyance_from[]')
    conv_tos = request_form.getlist('conveyance_to[]')
    conv_days = request_form.getlist('conveyance_days[]')
    conv_initials = request_form.getlist('conveyance_initial[]')
    conv_amounts = request_form.getlist('conveyance_amount[]')

    for i in range(len(conv_froms)):

        if not conv_froms[i]:
            continue

        conveyance_data.append([

            conv_froms[i],
            conv_tos[i],
            conv_days[i],
            conv_initials[i],
            conv_amounts[i]

        ])

    elements.append(
        Paragraph(
            "<b>Conveyance Expenses</b>",
            styles['Heading2']
        )
    )

    conveyance_table = Table(conveyance_data)

    conveyance_table.setStyle(TableStyle([

        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 9)

    ]))

    elements.append(conveyance_table)

    elements.append(Spacer(1, 20))

    # =========================================
    # PER DIEM TABLE
    # =========================================

    per_diem_data = [[
        'From',
        'To',
        'Total Days',
        'Persons',
        'Initial Amount',
        'Total Amount'
    ]]

    pd_froms = request_form.getlist('perdiem_from[]')
    pd_tos = request_form.getlist('perdiem_to[]')
    pd_days = request_form.getlist('perdiem_days[]')
    pd_persons = request_form.getlist('perdiem_persons[]')
    pd_initials = request_form.getlist('perdiem_initial[]')
    pd_amounts = request_form.getlist('perdiem_amount[]')

    for i in range(len(pd_froms)):

        if not pd_froms[i]:
            continue

        per_diem_data.append([

            pd_froms[i],
            pd_tos[i],
            pd_days[i],
            pd_persons[i],
            pd_initials[i],
            pd_amounts[i]

        ])

    elements.append(
        Paragraph(
            "<b>Per Diem Expenses</b>",
            styles['Heading2']
        )
    )

    pd_table = Table(per_diem_data)

    pd_table.setStyle(TableStyle([

        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 9)

    ]))

    elements.append(pd_table)

    elements.append(Spacer(1, 20))

    # =========================================
    # FINAL AMOUNT
    # =========================================

    final_table = Table([

        ['TOTAL AMOUNT REQUESTED', f'₹ {amount_requested}']

    ], colWidths=[300, 200])

    final_table.setStyle(TableStyle([

        ('BACKGROUND', (0, 0), (-1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12)

    ]))

    elements.append(final_table)

    # =========================================
    # BUILD PDF
    # =========================================

    doc.build(elements)

    return pdf_filename