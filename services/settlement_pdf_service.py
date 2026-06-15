from reportlab.platypus import *
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from pypdf import PdfReader, PdfWriter
import os
import uuid


def generate_settlement_pdf(
    settlement,
    expenses,
    files
):

    os.makedirs("pdfs", exist_ok=True)

    filename = f"settlement_{uuid.uuid4()}.pdf"

    filepath = os.path.join(
        "pdfs",
        filename
    )

    doc = SimpleDocTemplate(filepath)

    styles = getSampleStyleSheet()

    elements = []

    # =========================================
    # CALCULATE TOTALS
    # =========================================

    travelling_total = 0
    conveyance_total = 0
    food_total = 0
    hotel_total = 0
    others_total = 0
    office_total = 0

    for row in expenses:

        amount = float(row['amount'] or 0)

        if row['expense_type'] == 'Travelling':
            travelling_total += amount

        elif row['expense_type'] == 'Conveyance':
            conveyance_total += amount

        elif row['expense_type'] == 'Food':
            food_total += amount

        elif row['expense_type'] == 'Hotel':
            hotel_total += amount

        elif row['expense_type'] == 'Others':
            others_total += amount

        elif row['expense_type'] == 'Office':
            office_total += amount

    total_expense = (
        travelling_total
        + conveyance_total
        + food_total
        + hotel_total
        + others_total
        + office_total
    )

    advance = float(
        settlement['advance_received'] or 0
    )

    due_amount = total_expense - advance

    # =========================================
    # PAGE 1
    # =========================================

    elements.append(
        Paragraph(
            "TRAVEL SETTLEMENT FORM",
            styles['Title']
        )
    )

    elements.append(
        Spacer(1, 15)
    )

    summary_data = [

        ["Employee Name", settlement['emp_name']],

        ["Designation", settlement['designation'] or ""] ,

        ["Posting Place", settlement['posting_place'] or ""] ,

        ["Place Of Visit", settlement['place_of_visit'] or ""] ,

        ["Project Code", settlement['project_code'] or ""] ,

        ["Project Reference",
         settlement['project_reference'] or ""],

        ["Departure Date",
         str(settlement['departure_date'])],

        ["Arrival Date",
         str(settlement['arrival_date'])]

    ]

    summary_table = Table(
        summary_data,
        colWidths=[180, 280]
    )

    summary_table.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),1,colors.black),
        ('BACKGROUND',
         (0,0),
         (-1,0),
         colors.HexColor('#C7E6F1')),
        ('BACKGROUND',
         (0,0),
         (0,-1),
         colors.HexColor('#C7E6F1')),
    ('FONTNAME',
     (0,0),
     (0,-1),
     'Helvetica-Bold'),
]))

    elements.append(summary_table)

    elements.append(
        Spacer(1, 20)
    )

    totals_data = [

        ["Expense Detail", "Amount"],

        ["Travelling Expenses",
         f"{travelling_total:.2f}"],

        ["Conveyance Expenses",
         f"{conveyance_total:.2f}"],

        ["Food Expenses",
         f"{food_total:.2f}"],

        ["Hotel Expenses",
         f"{hotel_total:.2f}"],

        ["Other Expenses",
         f"{others_total:.2f}"],

        ["Office Expenses",
         f"{office_total:.2f}"],

        ["Total Expense",
         f"{total_expense:.2f}"],

        ["Advance Received",
         f"{advance:.2f}"],

        ["Due Amount",
         f"{due_amount:.2f}"]

    ]

    totals_table = Table(
        totals_data,
        colWidths=[250,150]
    )

    totals_table.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),1,colors.black),
        ('BACKGROUND',
         (0,0),
         (-1,0),
         colors.HexColor('#C7E6F1')),
        ('FONTNAME',
         (0,0),
         (-1,0),
         'Helvetica-Bold'),
        ('BACKGROUND',
         (0,7),
         (-1,9),
         colors.HexColor('#EAF6FB')),
]))

    elements.append(totals_table)

    elements.append(PageBreak())

    # =========================================
    # PAGE 2
    # =========================================

    elements.append(
        Paragraph(
            "CLAIM BREAKUP",
            styles['Title']
        )
    )

    categories = [

        'Travelling',
        'Conveyance',
        'Food',
        'Hotel',
        'Others',
        'Office'

    ]

    for category in categories:

        rows = []

        for row in expenses:

            if row['expense_type'] == category:

                rows.append(row)

        if not rows:
            continue

        elements.append(
            Spacer(1,12)
        )

        elements.append(
            Paragraph(
                category + " Expenses",
                styles['Heading2']
            )
        )

        table_data = [[

            "Date",
            "Particulars",
            "Mode",
            "Bill No",
            "Amount"

        ]]

        category_total = 0

        for row in rows:

            amount = float(
                row['amount'] or 0
            )

            category_total += amount

            table_data.append([

                str(row['expense_date']),

                row['particulars'] or "",

                row['mode'] or "",

                row['bill_no'] or "",

                f"{amount:.2f}"

            ])

        table_data.append([

            "",
            "",
            "",
            "Total",
            f"{category_total:.2f}"

        ])

        table = Table(
            table_data,
            colWidths=[
                70,
                180,
                80,
                80,
                80
            ]
        )

        table.setStyle(TableStyle([

            ('GRID',
             (0,0),
             (-1,-1),
             1,
             colors.black),

            ('BACKGROUND',
             (0,0),
             (-1,0),
             colors.HexColor('#C7E6F1')),
            ('FONTNAME',
             (0,0),
             (-1,0),
             'Helvetica-Bold'),

            ('BACKGROUND',
             (0,-1),
             (-1,-1),
             colors.whitesmoke)

        ]))

        elements.append(table)

    # =========================================
    # BILL ATTACHMENTS
    # =========================================

    for file in files:

        path = os.path.join(
            "uploads",
            file['stored_filename']
        )

        if not os.path.exists(path):
            continue

        ext = path.lower()

        if ext.endswith(
            ('.jpg', '.jpeg', '.png')
        ):

            elements.append(
                PageBreak()
            )

            elements.append(
                Paragraph(
                    "Bill Attachment",
                    styles['Heading1']
                )
            )

            elements.append(
                Paragraph(
                    file['original_filename'],
                    styles['Heading3']
                )
            )

            img = Image(path)
            img.drawWidth = 450
            img.drawHeight = 550

            elements.append(img)

    doc.build(elements)
    # =========================================
    # MERGE GENERATED PDF + UPLOADED PDF FILES
    # =========================================
    writer = PdfWriter()
    # Add generated settlement PDF pages
    generated_pdf = PdfReader(filepath)
    for page in generated_pdf.pages:
        writer.add_page(page)
    # Add uploaded PDF bills
    for file in files:
        path = os.path.join(
            "uploads",
            file['stored_filename']
        )
        if (
            os.path.exists(path)
            and path.lower().endswith(".pdf")
        ):
            try:
                uploaded_pdf = PdfReader(path)
                for page in uploaded_pdf.pages:
                    writer.add_page(page)
            except Exception as e:
                print(
                    "PDF merge failed:",
                    path,
                    str(e)
                )
    # Save final merged PDF
    with open(filepath, "wb") as output_file:
        writer.write(output_file)
    return filename