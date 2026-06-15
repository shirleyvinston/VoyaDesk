import os
import uuid
import logging
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    send_from_directory,
    abort
)
from werkzeug.utils import secure_filename
from database.db import get_db_connection
from utils.decorators import login_required
from services.pdf_services import generate_pdf

request_routes = Blueprint(
    'request_routes',
    __name__
)
ALLOWED_EXTENSIONS = {
    'png',
    'jpg',
    'jpeg',
    'pdf',
    'xlsx',
    'docx'
}

def allowed_file(filename):

    return (
        '.' in filename
        and
        filename.rsplit('.', 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )
# =========================================
# SUBMIT REQUEST
# =========================================

@request_routes.route('/submit', methods=['POST'])
@login_required
def submit():
    db, cursor = get_db_connection()
    try:

        # =========================================
        # FORM DATA
        # =========================================

        emp_id = session['emp_id']
        emp_name = session['emp_name']

        project_name = request.form.get('project_name')
        site_name = request.form.get('site_name')

        if site_name == "CUSTOM":
            site_name = request.form.get('custom_site')
            if not site_name:
                return "Please enter custom site name"

        request_date = request.form.get('request_date')
        departure_date = request.form.get('departure_date')
        return_date = request.form.get('return_date')

        total_days = request.form.get('total_days')

        period_name = request.form.get('period_name')
        quarter = request.form.get('quarter_name')

        purpose = request.form.get('purpose')
        reason_text = request.form.get('reason_text')

        amount_requested = request.form.get('amount_requested')

        # =========================================
        # GET SUBSTATION ID
        # =========================================

        cursor.execute("""
            SELECT id
            FROM substations
            WHERE substation_name=%s
        """, (site_name,))

        substation = cursor.fetchone()
        if substation:
            substation_id = substation['id']
        else:
            cursor.execute("""
                INSERT INTO substations
                (
                    substation_name,
                    region_id
                )
                VALUES(%s,%s)
            """, (
                site_name,
                1
            ))
            db.commit()
            substation_id = cursor.lastrowid

        # =========================================
        # GENERATED LINK
        # =========================================
        if purpose == "CAMC":
            purpose_code = "CAMC"

        elif purpose == "Downcall":
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM travel_requests
                WHERE emp_id=%s
                AND purpose='Downcall'
                AND period_name=%s
            """, (
                emp_id,
                period_name
            ))
            downcall_count = cursor.fetchone()['total'] + 1

            purpose_code = f"D{downcall_count}"

        elif purpose == "Installation":
            purpose_code = "INST"

        elif purpose == "Maintenance":
            purpose_code = "MAIN"
        else:
            purpose_code = purpose

        generated_link = (
            f"{project_name}/"
            f"{period_name}/"
            f"{site_name}/"
            f"{purpose_code}/"
            f"{quarter}"
        )
        pdf_data = {

            "emp_id": emp_id,
            "emp_name": emp_name,

            "project_name": project_name,
            "site_name": site_name,

            "request_date": request_date,
            "departure_date": departure_date,
            "return_date": return_date,

            "total_days": total_days,

            "period_name": period_name,
            "quarter": quarter,

            "purpose": purpose,
            "reason_text": reason_text,

            "amount_requested": amount_requested,

            "generated_link": generated_link,

            "request_form": request.form

        }

        pdf_filename = generate_pdf(pdf_data)
        # =========================================
        # INSERT DATABASE
        # =========================================

        cursor.execute("""
            INSERT INTO travel_requests
            (
                       emp_id,
                       emp_name,
                       project_name,
                       site_name,
                       substation_id,
                       request_date,
                       departure_date,
                       return_date,
                       total_days,
                       period_name,
                       quarter,
                       purpose,
                       reason_text,
                       amount_requested,
                       generated_link,
                       pdf_file,
                       status,
                       admin_approval,
                       ceo_approval
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (

            emp_id,
            emp_name,
            project_name,
            site_name,
            substation_id,
            request_date,
            departure_date,
            return_date,
            total_days,
            period_name,
            quarter,
            purpose,
            reason_text,
            amount_requested,
            generated_link,
            pdf_filename,
            'Pending',
            'Pending',
            'Pending'

        ))
        request_id = cursor.lastrowid
        # =========================================
        # SAVE TRAVEL EXPENSES
        # =========================================

        travel_dates = request.form.getlist('travel_date[]')
        travel_froms = request.form.getlist('travel_from[]')
        travel_tos = request.form.getlist('travel_to[]')
        travel_modes = request.form.getlist('travel_mode[]')
        travel_persons = request.form.getlist('travel_persons[]')
        travel_amounts = request.form.getlist('travel_amount[]')

        for i in range(len(travel_dates)):
            if not travel_dates[i]:
                continue

            cursor.execute("""
                INSERT INTO travel_expenses
                (
                    request_id,
                    travel_date,
                    travel_from,
                    travel_to,
                    travel_mode,
                    travel_persons,
                    travel_amount
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (

                request_id,
                travel_dates[i],
                travel_froms[i],
                travel_tos[i],
                travel_modes[i],
                travel_persons[i],
                travel_amounts[i]

            ))
        # =========================================
        # SAVE ACCOMMODATION EXPENSES
        # =========================================

        acc_froms = request.form.getlist('acc_from[]')
        acc_tos = request.form.getlist('acc_to[]')
        acc_stays = request.form.getlist('acc_stay[]')
        acc_persons = request.form.getlist('acc_persons[]')
        acc_days = request.form.getlist('acc_days[]')
        acc_initials = request.form.getlist('acc_initial[]')
        acc_amounts = request.form.getlist('acc_amount[]')

        for i in range(len(acc_froms)):
            if not acc_froms[i]:
                continue

            cursor.execute("""
                INSERT INTO accommodation_expenses
                (
                    request_id,
                    acc_from,
                    acc_to,
                    stay_at,
                    persons,
                    total_days,
                    initial_amount,
                    total_amount
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                request_id,
                acc_froms[i],
                acc_tos[i],
                acc_stays[i],
                acc_persons[i],
                acc_days[i],
                acc_initials[i],
                acc_amounts[i]

            ))
        # =========================================
        # SAVE BOARDING EXPENSES
        # =========================================

        board_froms = request.form.getlist('boarding_from[]')
        board_tos = request.form.getlist('boarding_to[]')
        board_days = request.form.getlist('boarding_days[]')
        board_initials = request.form.getlist('boarding_initial[]')
        board_amounts = request.form.getlist('boarding_amount[]')

        for i in range(len(board_froms)):
            if not board_froms[i]:
                continue
            cursor.execute("""
                INSERT INTO boarding_expenses
                (
                    request_id,
                    board_from,
                    board_to,
                    total_days,
                    initial_amount,
                    total_amount
                )
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (
                request_id,
                board_froms[i],
                board_tos[i],
                board_days[i],
                board_initials[i],
                board_amounts[i]
            ))
        # =========================================
        # SAVE CONVEYANCE EXPENSES
        # =========================================
        conv_froms = request.form.getlist('conveyance_from[]')
        conv_tos = request.form.getlist('conveyance_to[]')
        conv_days = request.form.getlist('conveyance_days[]')
        conv_initials = request.form.getlist('conveyance_initial[]')
        conv_amounts = request.form.getlist('conveyance_amount[]')
        for i in range(len(conv_froms)):
            if not conv_froms[i]:
                continue
            cursor.execute("""
                INSERT INTO conveyance_expenses
                (
                    request_id,
                    conv_from,
                    conv_to,
                    total_days,
                    initial_amount,
                    total_amount
                )
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (
                request_id,
                conv_froms[i],
                conv_tos[i],
                conv_days[i],
                conv_initials[i],
                conv_amounts[i]
            )) 
        # =========================================
        # SAVE PER DIEM EXPENSES
        # =========================================

        pd_froms = request.form.getlist('perdiem_from[]')
        pd_tos = request.form.getlist('perdiem_to[]')
        pd_days = request.form.getlist('perdiem_days[]')
        pd_persons = request.form.getlist('perdiem_persons[]')
        pd_initials = request.form.getlist('perdiem_initial[]')
        pd_amounts = request.form.getlist('perdiem_amount[]')

        for i in range(len(pd_froms)):
            if not pd_froms[i]:
                continue
            cursor.execute("""
                INSERT INTO per_diem_expenses
                (
                    request_id,
                    pd_from,
                    pd_to,
                    total_days,
                    persons,
                    initial_amount,
                    total_amount
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (
                request_id,
                pd_froms[i],
                pd_tos[i],
                pd_days[i],
                pd_persons[i],
                pd_initials[i],
                pd_amounts[i]
            ))
        db.commit()

        return render_template(
            'submitted.html',
            generated_link=generated_link
        )

    except Exception as e:
        db.rollback()
        logging.error(f"SUBMIT ERROR: {str(e)}")
        return "Something went wrong"
    finally:
        cursor.close()
        db.close()

# =========================================
# PROFILE
# =========================================

@request_routes.route('/profile')
@login_required
def profile():
    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            SELECT *
            FROM travel_requests
            WHERE emp_name=%s
            ORDER BY id DESC
        """, (session['emp_name'],))

        requests_data = cursor.fetchall()

        return render_template(
            'profile.html',
            requests_data=requests_data
        )

    finally:

        cursor.close()
        db.close()


# =========================================
# HISTORY
# =========================================

@request_routes.route('/history')
@login_required
def history():

    db, cursor = get_db_connection()

    try:

        # ADMIN CAN SEE EMPLOYEE REQUESTS

        if session.get('role') == 'admin':

            cursor.execute("""
                SELECT *
                FROM travel_requests
                WHERE admin_approval IN ('Pending', 'Query')
                ORDER BY id DESC
            """)

        # CEO CAN SEE ONLY ADMIN APPROVED

        elif session.get('role') == 'ceo':

            cursor.execute("""
                SELECT *
                FROM travel_requests
                WHERE admin_approval='Approved'
                AND ceo_approval IN ('Pending', 'Query')
                ORDER BY id DESC
            """)

        else:

            abort(403)

        requests_data = cursor.fetchall()

        return render_template(
            'history.html',
            requests_data=requests_data
        )

    finally:

        cursor.close()
        db.close()
# =========================================
# DOWNLOAD PDF
# =========================================

@request_routes.route('/download-pdf/<path:filename>')
@login_required
def download_pdf(filename):
    return send_from_directory(
        'pdfs',
        filename,
        as_attachment=True
    )
# =========================================
# DOWNLOAD ATTACHMENT
# =========================================

@request_routes.route('/download-file/<path:filename>')
@login_required
def download_file(filename):

    return send_from_directory(
        'uploads',
        filename,
        as_attachment=True
    )
# =========================================
# UPLOAD FILES PAGE
# =========================================

@request_routes.route('/upload-files/<int:request_id>')
@login_required
def upload_files_page(request_id):

    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            SELECT *
            FROM travel_requests
            WHERE id=%s
        """, (request_id,))

        request_data = cursor.fetchone()
        if not request_data:
            abort(404)
        # =========================================
        # ALLOW FILES ONLY FOR APPROVED REQUESTS
        # =========================================
        if request_data['status'] != 'Approved':
            return "Files can only be uploaded after approval"
        cursor.execute("""
            SELECT *
            FROM expense_files
            WHERE request_id=%s
            ORDER BY uploaded_at DESC
        """, (request_id,))

        files = cursor.fetchall()

        return render_template(
            'upload_files.html',
            request_data=request_data,
            files=files
        )

    finally:

        cursor.close()
        db.close()
# =========================================
# SAVE FILES
# =========================================

@request_routes.route(
    '/save-files/<int:request_id>',
    methods=['POST']
)
@login_required
def save_files(request_id):

    db, cursor = get_db_connection()

    try:

        uploaded_files = request.files.getlist('expense_files')
        cursor.execute("""
            SELECT *
            FROM travel_requests
            WHERE id=%s
        """, (request_id,))

        request_data = cursor.fetchone()

        if not request_data:
            abort(404)
        if request_data['status'] != 'Approved':
            return "Files can only be uploaded after approval"

        for file in uploaded_files:

            if file and file.filename:
                if not allowed_file(file.filename):
                    return """Allowed file types: png, jpg, jpeg, pdf, xlsx, docx"""
                filename = secure_filename(file.filename)
                stored_filename = (
                    f"{request_id}_{uuid.uuid4()}_{filename}"
                )

                file_path = os.path.join(
                    'uploads',
                    stored_filename
                )

                file.save(file_path)

                cursor.execute("""
                    INSERT INTO expense_files
                    (
                        request_id,
                        original_filename,
                        stored_filename
                    )
                    VALUES (%s,%s,%s)
                """, (
                    request_id,
                    filename,
                    stored_filename
                ))

        db.commit()

        return redirect(f'/upload-files/{request_id}')

    finally:

        cursor.close()
        db.close()
# =========================================
# DELETE FILE
# =========================================

@request_routes.route('/delete-file/<int:file_id>')
@login_required
def delete_file(file_id):

    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            SELECT *
            FROM expense_files
            WHERE id=%s
        """, (file_id,))

        file_data = cursor.fetchone()

        if not file_data:
            abort(404)

        # =========================================
        # FETCH REQUEST
        # =========================================

        cursor.execute("""
            SELECT *
            FROM travel_requests
            WHERE id=%s
        """, (file_data['request_id'],))

        request_data = cursor.fetchone()

        # =========================================
        # DELETE PHYSICAL FILE
        # =========================================

        file_path = os.path.join(
            'uploads',
            file_data['stored_filename']
        )

        if os.path.exists(file_path):
            os.remove(file_path)

        # =========================================
        # DELETE DATABASE ROW
        # =========================================

        cursor.execute("""
            DELETE FROM expense_files
            WHERE id=%s
        """, (file_id,))

        db.commit()

        return redirect(
            f"/upload-files/{file_data['request_id']}"
        )
    except Exception as e:
        db.rollback()
        logging.error(f"UPLOAD ERROR: {str(e)}")
        return f"Upload failed: {str(e)}"
    finally:

        cursor.close()
        db.close()