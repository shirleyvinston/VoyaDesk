import os
from services.fraud_service import analyze_settlement
from services.settlement_pdf_service import generate_settlement_pdf
from flask import session
from flask import send_file
from werkzeug.utils import secure_filename
from flask import (
Blueprint,
render_template,
request,
redirect,
abort
)

from database.db import get_db_connection
from utils.decorators import login_required

settlement_routes = Blueprint(
'settlement_routes',
__name__
)
# =========================================
# SETTLEMENT PAGE
# =========================================
@settlement_routes.route('/settlements')
@login_required
def settlements():

    db, cursor = get_db_connection()

    try:
        emp_id = session['emp_id']
        cursor.execute("""
            SELECT *
            FROM travel_requests
            WHERE emp_id=%s
            AND status='Approved'
            AND settlement_status IN ('Pending','Draft')
            ORDER BY id DESC
        """, (emp_id,))

        requests_data = cursor.fetchall()

        return render_template(
            'settlement.html',
            requests_data=requests_data
        )

    finally:
        cursor.close()
        db.close()
# =========================================
# CREATE SETTLEMENT PAGE
# =========================================
@settlement_routes.route(
    '/create-settlement/<int:request_id>',
    methods=['GET', 'POST']
)
@login_required
def create_settlement(request_id):
    db, cursor = get_db_connection()
    try:
        cursor.execute("""
            SELECT
                tr.*,
                u.designation,
                u.posted_at
            FROM travel_requests tr
            JOIN users u
            ON tr.emp_id = u.emp_id
            WHERE tr.id=%s
        """, (request_id,))
        request_data = cursor.fetchone()
        if request.method == 'POST':
            designation = request_data['designation']
            posting_place = request_data['posted_at']
            project_reference = request.form.get(
                'project_reference'
            )
            arrival_date = request.form.get(
                'arrival_date'
            )
            expense_incurred = 0
            due_amount = 0
            cursor.execute("""
                SELECT id
                FROM travel_settlements
                WHERE request_id=%s
                LIMIT 1
            """, (request_id,))
            existing = cursor.fetchone()
            if existing:
                cursor.execute("""
                    UPDATE travel_settlements
                    SET
                        designation=%s,
                        posting_place=%s,
                        project_reference=%s,
                        arrival_date=%s
                    WHERE id=%s
                """, (
                    designation,
                    posting_place,
                    project_reference,
                    arrival_date,
                    existing['id']
                ))
                db.commit()
                cursor.execute("""
                    UPDATE travel_requests
                    SET settlement_status='Draft'
                    WHERE id=%s
                """, (request_id,))
                db.commit()
                return redirect(
                    f"/claim-breakup/{existing['id']}"
                )
            cursor.execute("""
                INSERT INTO travel_settlements
                (
                    request_id,
                    emp_name,
                    designation,
                    posting_place,
                    place_of_visit,
                    project_code,
                    project_reference,
                    departure_date,
                    arrival_date,
                    advance_received,
                    expense_incurred,
                    due_amount
                )
                VALUES
                (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                request_id,
                request_data['emp_name'],
                designation,
                posting_place,
                request_data['site_name'],
                request_data['project_name'],
                project_reference,
                request_data['departure_date'],
                arrival_date,
                request_data['amount_requested'],
                expense_incurred,
                due_amount
            ))
            db.commit()
            settlement_id = cursor.lastrowid
            cursor.execute("""
                UPDATE travel_requests
                SET settlement_status='Draft'
                WHERE id=%s
            """, (request_id,))
            db.commit()
            return redirect(
                f"/claim-breakup/{settlement_id}"
            )
        if not request_data:
            abort(404)
        cursor.execute("""
            SELECT *
            FROM travel_settlements
            WHERE request_id=%s
            ORDER BY expense_incurred DESC, id DESC
            LIMIT 1
        """,(request_id,))
        settlement = cursor.fetchone()
        print("Loaded settlement:", settlement)
        return render_template(
            'create_settlement.html',
            request_data=request_data,
            settlement=settlement
        )
    finally:
        cursor.close()
        db.close()
@settlement_routes.route(
    '/claim-breakup/<int:settlement_id>',
    methods=['GET', 'POST']
)
@login_required
def claim_breakup(settlement_id):
    db, cursor = get_db_connection()
    try:
        cursor.execute("""
            SELECT *
            FROM travel_settlements
            WHERE id=%s
        """, (settlement_id,))
        settlement = cursor.fetchone()
        # =========================================
        # LOAD FILES FOR DISPLAY
        # =========================================
        cursor.execute("""
            SELECT *
            FROM settlement_files
            WHERE settlement_id=%s
        """,(settlement_id,))
        uploaded_files = cursor.fetchall()
        if request.method == 'POST':
            print("POST RECEIVED")
            print(request.form)
            action = request.form.get("action")
            if action == "upload":
                files = request.files.getlist(
                    "expense_files"
                )
                for file in files:
                    if file.filename:
                        filename = (
                            str(settlement_id)
                            + "_"
                            + secure_filename(file.filename)
                        )
                        os.makedirs(
                            "uploads",
                            exist_ok=True
                        )
                        save_path = os.path.join(
                            "uploads",
                            filename
                        )
                        file.save(save_path)
                        cursor.execute("""
                            INSERT INTO settlement_files
                            (
                                settlement_id,
                                original_filename,
                                stored_filename,
                                file_type,
                                file_size
                            )
                            VALUES
                            (%s,%s,%s,%s,%s)
                        """,(
                            settlement_id,
                            file.filename,
                            filename,
                            file.content_type,
                            os.path.getsize(save_path)
                        ))
                cursor.execute("""
                    SELECT request_id
                    FROM travel_settlements
                    WHERE id=%s
                """,(settlement_id,))
                data = cursor.fetchone()
                cursor.execute("""
                    UPDATE travel_requests
                    SET settlement_status='Draft'
                    WHERE id=%s
                """, (data['request_id'],))
                db.commit()
                cursor.execute("""
                    SELECT *
                    FROM settlement_files
                    WHERE settlement_id=%s
                """,(settlement_id,))
                uploaded_files = cursor.fetchall()
                return redirect(
                    f"/claim-breakup/{settlement_id}"
                )
            cursor.execute("""
                DELETE FROM settlement_expenses
                WHERE settlement_id=%s
            """,(settlement_id,))
            travel_dates = request.form.getlist(
                'travel_date[]'
            )
            travel_amounts = request.form.getlist(
                'travel_amount[]'
            )
            travel_particulars = request.form.getlist(
                'travel_particular[]'
            )
            travel_modes = request.form.getlist(
                'travel_mode[]'
            )
            travel_bills = request.form.getlist(
                'travel_bill[]'
            )
            for i in range(len(travel_amounts)):
                if travel_amounts[i]:
                    cursor.execute("""
                        INSERT INTO settlement_expenses
                        (
                            settlement_id,
                            expense_type,
                            expense_date,
                            particulars,
                            mode,
                            bill_no,
                            amount
                        )
                        VALUES
                        (%s,%s,%s,%s,%s,%s,%s)
                    """, (
                        settlement_id,
                        'Travelling',
                        travel_dates[i],
                        travel_particulars[i],
                        travel_modes[i],
                        travel_bills[i],
                        travel_amounts[i]
                    ))
            convey_dates = request.form.getlist('convey_date[]')
            convey_amounts = request.form.getlist('convey_amount[]')
            convey_particulars = request.form.getlist('convey_particular[]')
            convey_modes = request.form.getlist('convey_mode[]')
            convey_bills = request.form.getlist('convey_bill[]')
            for i in range(len(convey_amounts)):
                if convey_amounts[i]:
                    cursor.execute("""
                        INSERT INTO settlement_expenses
                        (
                            settlement_id,
                            expense_type,
                            expense_date,
                            particulars,
                            mode,
                            bill_no,
                            amount
                        ) 
                        VALUES
                        (%s,%s,%s,%s,%s,%s,%s)
                    """,(
                        settlement_id,
                        'Conveyance',
                        convey_dates[i],
                        convey_particulars[i],
                        convey_modes[i],
                        convey_bills[i],
                        convey_amounts[i]
                    ))
            food_dates = request.form.getlist('food_date[]')
            food_amounts = request.form.getlist('food_amount[]')
            food_particulars = request.form.getlist('food_particular[]')
            food_bills = request.form.getlist('food_bill[]')
            for i in range(len(food_amounts)):
                if food_amounts[i]:
                    cursor.execute("""
                        INSERT INTO settlement_expenses
                        (
                            settlement_id,
                            expense_type,
                            expense_date,
                            particulars,
                            bill_no,
                            amount
                        )
                        VALUES
                        (%s,%s,%s,%s,%s,%s)
                    """,(
                        settlement_id,
                        'Food',
                        food_dates[i],
                        food_particulars[i],
                        food_bills[i],
                        food_amounts[i]
                    ))
            hotel_dates = request.form.getlist('hotel_date[]')
            hotel_amounts = request.form.getlist('hotel_amount[]')
            hotel_particulars = request.form.getlist('hotel_particular[]')
            hotel_bills = request.form.getlist('hotel_bill[]')
            for i in range(len(hotel_amounts)):
                if hotel_amounts[i]:
                    cursor.execute("""
                        INSERT INTO settlement_expenses
                        (
                            settlement_id,
                            expense_type,
                            expense_date,
                            particulars,
                            bill_no,
                            amount
                        )
                        VALUES
                        (%s,%s,%s,%s,%s,%s)
                    """,(
                        settlement_id,
                        'Hotel',
                        hotel_dates[i],
                        hotel_particulars[i],
                        hotel_bills[i],
                        hotel_amounts[i]
                    ))
            other_dates = request.form.getlist('other_date[]')
            other_amounts = request.form.getlist('other_amount[]')
            other_particulars = request.form.getlist('other_particular[]')
            other_bills = request.form.getlist('other_bill[]')
            for i in range(len(other_amounts)):
                if other_amounts[i]:
                    cursor.execute("""
                        INSERT INTO settlement_expenses
                        (
                            settlement_id,
                            expense_type,
                            expense_date,
                            particulars,
                            bill_no,
                            amount
                        )
                        VALUES
                        (%s,%s,%s,%s,%s,%s)
                    """,(
                        settlement_id,
                        'Others',
                        other_dates[i],
                        other_particulars[i],
                        other_bills[i],
                        other_amounts[i]
                    ))
            office_dates = request.form.getlist('office_date[]')
            office_amounts = request.form.getlist('office_amount[]')
            office_particulars = request.form.getlist('office_particular[]')
            office_bills = request.form.getlist('office_bill[]')
            for i in range(len(office_amounts)):
                if office_amounts[i]:
                    cursor.execute("""
                        INSERT INTO settlement_expenses
                        (
                            settlement_id,
                            expense_type,
                            expense_date,
                            particulars,
                            bill_no,
                            amount
                        )
                        VALUES
                        (%s,%s,%s,%s,%s,%s)
                    """,(
                        settlement_id,
                        'Office',
                        office_dates[i],
                        office_particulars[i],
                        office_bills[i],
                        office_amounts[i]
                    ))
            travel_total = sum(
                float(x or 0)
                for x in travel_amounts
            )
            conveyance_total = sum(
                float(x or 0)
                for x in convey_amounts
            )
            food_total = sum(
                float(x or 0)
                for x in food_amounts
            )
            hotel_total = sum(
                float(x or 0)
                for x in hotel_amounts
            )
            others_total = sum(
                float(x or 0)
                for x in other_amounts
            )
            office_total = sum(
                float(x or 0)
                for x in office_amounts
            )
            # =========================================
            # CALCULATE TOTAL EXPENSE
            # =========================================
            cursor.execute("""
                SELECT
                SUM(amount) AS total
                FROM settlement_expenses
                WHERE settlement_id=%s
            """, (settlement_id,))
            result = cursor.fetchone()
            expense_incurred = (
                result['total'] or 0
            )
            # =========================================
            # CALCULATE DUE AMOUNT
            # =========================================
            advance = (
                settlement['advance_received']
            )
            due_amount = (
                expense_incurred - advance
            )
            # =========================================
            # UPDATE SETTLEMENT
            # =========================================
            cursor.execute("""
                UPDATE travel_settlements
                SET
                    travelling_total=%s,
                    conveyance_total=%s,
                    food_total=%s,
                    hotel_total=%s,
                    others_total=%s,
                    office_total=%s,
                    expense_incurred=%s,
                    due_amount=%s
                WHERE id=%s
            """,(
                travel_total,
                conveyance_total,
                food_total,
                hotel_total,
                others_total,
                office_total,
                expense_incurred,
                due_amount,
                settlement_id
            ))
            # =========================================
            # SAVE UPLOADED FILES
            # =========================================
            allowed_extensions = (
                '.pdf',
                '.jpg',
                '.jpeg',
                '.png',
                '.doc',
                '.docx',
                '.xls',
                '.xlsx'
            )
            files = request.files.getlist(
                'expense_files'
            )
            for file in files:
                if (
                    file.filename and
                    file.filename.lower().endswith(
                        allowed_extensions
                    )
                ):
                    filename = (
                        str(settlement_id)
                        + "_"
                        + secure_filename(file.filename)
                    )
                    os.makedirs(
                        "uploads",
                        exist_ok=True
                    )
                    save_path = os.path.join(
                        'uploads',
                        filename
                    )
                    file.save(save_path)
                    cursor.execute("""
                        INSERT INTO settlement_files
                        (
                            settlement_id,
                            original_filename,
                            stored_filename,
                            file_type,
                            file_size
                        )
                        VALUES
                        (%s,%s,%s,%s,%s)
                    """,(
                        settlement_id,
                        file.filename,
                        filename,
                        file.content_type,
                        os.path.getsize(save_path)
                    ))
            db.commit()
            cursor.execute("""
                SELECT request_id
                FROM travel_settlements
                WHERE id=%s
            """,(settlement_id,))
            data = cursor.fetchone()
            cursor.execute("""
                UPDATE travel_requests
                SET settlement_status='Draft'
                WHERE id=%s
            """, (data['request_id'],))
            db.commit()
            return redirect(
                f"/create-settlement/{data['request_id']}"
            )
        cursor.execute("""
            SELECT request_id
            FROM travel_settlements
            WHERE id=%s
        """,(settlement_id,))
        data = cursor.fetchone()
        # Travelling
        cursor.execute("""
            SELECT *
            FROM settlement_expenses
            WHERE settlement_id=%s
            AND expense_type='Travelling'
        """,(settlement_id,))
        travel_expenses = cursor.fetchall()
        # Conveyance
        cursor.execute("""
            SELECT *
            FROM settlement_expenses
            WHERE settlement_id=%s
            AND expense_type='Conveyance'
        """,(settlement_id,))
        convey_expenses = cursor.fetchall()
        # Food
        cursor.execute("""
            SELECT *
            FROM settlement_expenses
            WHERE settlement_id=%s
            AND expense_type='Food'
        """,(settlement_id,))
        food_expenses = cursor.fetchall()
        # Hotel
        cursor.execute("""
            SELECT *
            FROM settlement_expenses
            WHERE settlement_id=%s
            AND expense_type='Hotel'
        """,(settlement_id,))
        hotel_expenses = cursor.fetchall()
        # Others
        cursor.execute("""
            SELECT *
            FROM settlement_expenses
            WHERE settlement_id=%s
            AND expense_type='Others'
        """,(settlement_id,))
        other_expenses = cursor.fetchall()
        # Office
        cursor.execute("""
            SELECT *
            FROM settlement_expenses
            WHERE settlement_id=%s
            AND expense_type='Office'
        """,(settlement_id,))
        office_expenses = cursor.fetchall()
        print("Settlement ID:", settlement_id)
        print("Travel:", travel_expenses)
        print("Convey:", convey_expenses)
        print("Food:", food_expenses)
        print("Hotel:", hotel_expenses)
        print("Other:", other_expenses)
        print("Office:", office_expenses)
        return render_template(
            'claim_breakup.html',
            settlement=settlement,
            uploaded_files=uploaded_files,
            request_id=data['request_id'],
            travel_expenses=travel_expenses,
            convey_expenses=convey_expenses,
            food_expenses=food_expenses,
            hotel_expenses=hotel_expenses,
            other_expenses=other_expenses,
            office_expenses=office_expenses
        )
    finally:
        cursor.close()
        db.close()
@settlement_routes.route(
    '/view-file/<int:file_id>'
)
@login_required
def view_file(file_id):

    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            SELECT *
            FROM settlement_files
            WHERE id=%s
        """,(file_id,))

        file = cursor.fetchone()

        path = os.path.join(
            'uploads',
            file['stored_filename']
        )

        return send_file(path)
 
    finally:

        cursor.close()
        db.close()
@settlement_routes.route(
    '/delete-settlement-file/<int:file_id>',
    methods=['POST']
)
@login_required
def delete_file(file_id):

    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            SELECT *
            FROM settlement_files
            WHERE id=%s
        """,(file_id,))

        file = cursor.fetchone()

        settlement_id = file['settlement_id']

        path = os.path.join(
            'uploads',
            file['stored_filename']
        )

        if os.path.exists(path):

            os.remove(path)

        cursor.execute("""
            DELETE FROM settlement_files
            WHERE id=%s
        """,(file_id,))

        db.commit()

        return redirect(
            f"/claim-breakup/{settlement_id}"
        )

    finally:

        cursor.close()
        db.close()
@settlement_routes.route(
    '/submit-settlement/<int:request_id>',
    methods=['POST']
)
@login_required
def submit_settlement(request_id):

    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            SELECT *
            FROM travel_settlements
            WHERE request_id=%s
        """,(request_id,))
        settlement = cursor.fetchone()
        
        cursor.execute("""
            SELECT *
            FROM settlement_expenses
            WHERE settlement_id=%s
        """,(settlement['id'],))
        expenses = cursor.fetchall()
        fraud_result = analyze_settlement(
            settlement,
            expenses
        )
        print("FRAUD RESULT =", fraud_result)
        cursor.execute("""
            SELECT *
            FROM settlement_files
            WHERE settlement_id=%s
        """,(settlement['id'],))
        files = cursor.fetchall()
        print("SETTLEMENT =", settlement)
        print("EXPENSE COUNT =", len(expenses))
        print("FILE COUNT =", len(files))
        pdf_file = generate_settlement_pdf(
            settlement,
            expenses,
            files
        )
        print("PDF FILE =", pdf_file)
        cursor.execute("""
            UPDATE travel_settlements
            SET settlement_pdf=%s
            WHERE id=%s
        """,(
            pdf_file,
            settlement['id']
        ))
        print("UPDATED DATABASE")
        cursor.execute("""
            UPDATE travel_requests
            SET settlement_status='Submitted'
            WHERE id=%s
        """, (request_id,))
        cursor.execute("""
            SELECT id
            FROM fraud_analysis
            WHERE request_id=%s
        """,(request_id,))
        existing = cursor.fetchone()
        if existing:
            cursor.execute("""
                UPDATE fraud_analysis
                SET
                    fraud_score=%s,
                    risk_level=%s,
                    recommendation=%s,
                    remarks=%s
                WHERE request_id=%s
            """,(
                fraud_result['score'],
                fraud_result['risk'],
                fraud_result['recommendation'],
                fraud_result['remarks'],
                request_id
            ))
        else:
            cursor.execute("""
                INSERT INTO fraud_analysis
                (
                    request_id,
                    fraud_score,
                    risk_level,
                    recommendation,
                    remarks
                )
                VALUES
                (%s,%s,%s,%s,%s)
            """,(
                request_id,
                fraud_result['score'],
                fraud_result['risk'],
                fraud_result['recommendation'],
                fraud_result['remarks']
            ))
        db.commit()
        return redirect('/settlements')
    finally:

        cursor.close()
        db.close()
@settlement_routes.route('/submitted-settlements')
@login_required
def submitted_settlements():
    employee = request.args.get('employee', '')
    project = request.args.get('project', '')
    if session.get('role') != 'accounts':
        abort(403)

    db, cursor = get_db_connection()

    try:

        employee = request.args.get(
            'employee',
            ''
        )

        project = request.args.get(
            'project',
            ''
        )
        site = request.args.get(
            'site',
            ''
        )
        query = """
            SELECT
                tr.*,
                ts.id AS settlement_id,
                ts.settlement_pdf,
                fa.fraud_score,
                fa.risk_level,
                fa.recommendation
            FROM travel_requests tr
            LEFT JOIN travel_settlements ts
                ON tr.id = ts.request_id
            LEFT JOIN fraud_analysis fa
                ON tr.id = fa.request_id
            WHERE tr.settlement_status='Submitted'
        """
        params = []

        if employee:

            query += """
                AND tr.emp_name LIKE %s
            """

            params.append(
                f"%{employee}%"
            )

        if project:

            query += """
                AND tr.project_name LIKE %s
            """

            params.append(
                f"%{project}%"
            )
        if site:
            query += """
                AND tr.site_name LIKE %s
            """
            params.append(
                f"%{site}%"
            )
        query += """
            ORDER BY tr.id DESC
        """
        cursor.execute(
            query,
            tuple(params)
        )
        requests_data = cursor.fetchall()
        cursor.execute("""
            SELECT DISTINCT emp_name
            FROM travel_requests
            WHERE settlement_status='Submitted'
            ORDER BY emp_name
        """)
        employees = cursor.fetchall()
        cursor.execute("""
            SELECT DISTINCT project_name
            FROM travel_requests
            WHERE settlement_status='Submitted'
            ORDER BY project_name
        """)
        projects = cursor.fetchall()
        cursor.execute("""
            SELECT DISTINCT site_name
            FROM travel_requests
            WHERE settlement_status='Submitted'
            ORDER BY site_name
        """)
        sites = cursor.fetchall()
        return render_template(
            'submitted_settlements.html',
            requests_data=requests_data,
            employees=employees,
            projects=projects,
            sites=sites
        )
    finally:

        cursor.close()
        db.close()
@settlement_routes.route(
    '/download-settlement-pdf/<int:request_id>'
)
@login_required
def download_settlement_pdf(request_id):

    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            SELECT settlement_pdf
            FROM travel_settlements
            WHERE request_id=%s
        """,(request_id,))

        data = cursor.fetchone()

        if not data:
            abort(404)

        return send_file(
            os.path.join(
                'pdfs',
                data['settlement_pdf']
            ),
            as_attachment=True
        )

    finally:

        cursor.close()
        db.close()
@settlement_routes.route(
    '/approve-settlement/<int:request_id>'
)
@login_required
def approve_settlement(request_id):

    if session.get('role') != 'accounts':
        abort(403)

    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            UPDATE travel_requests
            SET settlement_status='Draft'
            WHERE id=%s
        """, (request_id,))

        db.commit()

        return redirect('/submitted-settlements')

    finally:

        cursor.close()
        db.close()
@settlement_routes.route(
    '/decline-settlement/<int:request_id>'
)
@login_required
def decline_settlement(request_id):

    if session.get('role') != 'accounts':
        abort(403)

    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            UPDATE travel_requests
            SET settlement_status='Pending'
            WHERE id=%s
        """, (request_id,))
        cursor.execute("""
            DELETE FROM fraud_analysis
            WHERE request_id=%s
        """,(request_id,))
        db.commit()

        return redirect('/submitted-settlements')

    finally:

        cursor.close()
        db.close()