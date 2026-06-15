import os
import logging

from flask import (
    Blueprint,
    redirect,
    session,
    abort
)
from flask_mail import Message

from database.db import get_db_connection
from utils.decorators import login_required
from extensions import mail
approval_routes = Blueprint(
    'approval_routes',
    __name__
)
# =========================================
# APPROVE REQUEST
# =========================================

@approval_routes.route('/approve-request/<int:request_id>')
@login_required
def approve_request(request_id):

    db, cursor = get_db_connection()

    try:

        # =========================================
        # ADMIN APPROVAL
        # =========================================

        if session.get('role') == 'admin':

            cursor.execute("""
                UPDATE travel_requests
                SET
                    admin_approval='Approved',
                    status='Pending'
                WHERE id=%s
            """, (request_id,))

            db.commit()

        # =========================================
        # CEO APPROVAL
        # =========================================

        elif session.get('role') == 'ceo':

            cursor.execute("""
                UPDATE travel_requests
                SET
                    ceo_approval='Approved',
                    status='Approved'
                WHERE id=%s
            """, (request_id,))

            db.commit()

            # =========================================
            # FETCH TRAVEL REQUEST
            # =========================================

            cursor.execute("""
                SELECT *
                FROM travel_requests
                WHERE id=%s
            """, (request_id,))

            travel = cursor.fetchone()

            # =========================================
            # FETCH EMPLOYEE EMAIL
            # =========================================

            cursor.execute("""
                SELECT *
                FROM users
                WHERE emp_id=%s
            """, (travel['emp_id'],))

            employee = cursor.fetchone()

            if not employee:
                return "Employee email not found"

            employee_email = employee['email']

            # =========================================
            # FETCH ADMIN EMAIL
            # =========================================

            cursor.execute("""
                SELECT *
                FROM users
                WHERE role='admin'
                LIMIT 1
            """)

            admin = cursor.fetchone()

            admin_email = admin['email']

            # =========================================
            # FETCH ACCOUNTS EMAIL
            # =========================================

            cursor.execute("""
                SELECT *
                FROM users
                WHERE role='accounts'
                LIMIT 1
            """)

            accounts = cursor.fetchone()

            accounts_email = None

            if accounts:

                accounts_email = accounts['email']

            # =========================================
            # CEO EMAIL
            # =========================================

            ceo_email = session['email']

            # =========================================
            # CREATE RECIPIENTS
            # =========================================

            recipients = [
                employee_email,
                admin_email,
                ceo_email
            ]

            if accounts_email:

                recipients.append(accounts_email)

            # =========================================
            # CREATE EMAIL
            # =========================================

            msg = Message(

            subject=f"Travel Request - {travel['emp_name']}",

            recipients=recipients

            )

            msg.body = f"""
Travel Request Approved

Employee:
{travel['emp_name']}

Project:
{travel['project_name']}

Site:
{travel['site_name']}

Purpose:
{travel['purpose']}

Status:
Approved
"""

            # =========================================
            # ATTACH PDF
            # =========================================

            pdf_path = os.path.join(
                'pdfs',
                travel['pdf_file']
            )

            if os.path.exists(pdf_path):
                with open(pdf_path, 'rb') as pdf:
                    msg.attach(
                        filename=travel['pdf_file'],
                        content_type='application/pdf',
                        data=pdf.read()
                    )
            # =========================================
            # SEND EMAIL
            # =========================================

            try:

                mail.send(msg)

                logging.info("APPROVAL EMAIL SENT SUCCESSFULLY")

            except Exception as e:

                logging.error(f"APPROVAL EMAIL ERROR: {str(e)}")

        else:

            abort(403)

        return redirect('/history')

    finally:

        cursor.close()
        db.close()
# =========================================
# DECLINE REQUEST
# =========================================

@approval_routes.route('/decline-request/<int:request_id>')
@login_required
def decline_request(request_id):

    db, cursor = get_db_connection()

    try:

        # =========================================
        # ADMIN DECLINE
        # =========================================

        if session.get('role') == 'admin':

            cursor.execute("""
                UPDATE travel_requests
                SET
                    admin_approval='Declined',
                    status='Declined'
                WHERE id=%s
            """, (request_id,))

        # =========================================
        # CEO DECLINE
        # =========================================

        elif session.get('role') == 'ceo':

            cursor.execute("""
                UPDATE travel_requests
                SET
                    ceo_approval='Declined',
                    status='Declined'
                WHERE id=%s
            """, (request_id,))

        else:

            abort(403)

        db.commit()

        # =========================================
        # FETCH TRAVEL REQUEST
        # =========================================

        cursor.execute("""
            SELECT *
            FROM travel_requests
            WHERE id=%s
        """, (request_id,))

        travel = cursor.fetchone()

        # =========================================
        # FETCH EMPLOYEE EMAIL
        # =========================================

        cursor.execute("""
            SELECT *
            FROM users
            WHERE emp_id=%s
        """, (travel['emp_id'],))

        employee = cursor.fetchone()

        employee_email = employee['email']

        # =========================================
        # WHO DECLINED
        # =========================================

        declined_by = session['emp_name'].title()

        # =========================================
        # EMAIL
        # =========================================

        msg = Message(

            subject=f"Travel Request Declined - {travel['emp_name']}",

            recipients=[employee_email]

        )

        msg.body = f"""
Your travel request has been DECLINED.

Declined By:
{declined_by}

Project:
{travel['project_name']}

Site:
{travel['site_name']}

Purpose:
{travel['purpose']}
"""

        # =========================================
        # ATTACH PDF
        # =========================================

        pdf_path = os.path.join(
            'pdfs',
            travel['pdf_file']
        )

        if os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as pdf:
                msg.attach(
                    filename=travel['pdf_file'],
                    content_type='application/pdf',
                    data=pdf.read()
                )
        # =========================================
        # SEND MAIL
        # =========================================

        try:

            mail.send(msg)

            logging.info("DECLINE EMAIL SENT SUCCESSFULLY")

        except Exception as e:

            logging.error(f"DECLINE EMAIL ERROR: {str(e)}")

        return redirect('/history')

    finally:

        cursor.close()
        db.close()
# =========================================
# QUERY REQUEST
# =========================================

@approval_routes.route('/query/<int:id>')
@login_required
def query_request(id):

    if session.get('role') not in ['admin', 'ceo']:
        abort(403)

    db, cursor = get_db_connection()

    try:

        query_person = session['emp_name'].title()

        # =========================================
        # ADMIN QUERY
        # =========================================

        if session.get('role') == 'admin':

            status_text = f"{query_person} Query"

            cursor.execute("""
                UPDATE travel_requests
                SET
                    status=%s,
                    admin_approval='Query'
                WHERE id=%s
            """, (
                status_text,
                id
            ))

        # =========================================
        # CEO QUERY
        # =========================================

        elif session.get('role') == 'ceo':

            status_text = f"{query_person} Query"

            cursor.execute("""
                UPDATE travel_requests
                SET
                    status=%s,
                    ceo_approval='Query'
                WHERE id=%s
            """, (
                status_text,
                id
            ))

        db.commit()

        # =========================================
        # FETCH TRAVEL REQUEST
        # =========================================

        cursor.execute("""
            SELECT *
            FROM travel_requests
            WHERE id=%s
        """, (id,))

        travel = cursor.fetchone()

        # =========================================
        # FETCH EMPLOYEE EMAIL
        # =========================================

        cursor.execute("""
            SELECT *
            FROM users
            WHERE emp_id=%s
        """, (travel['emp_id'],))

        employee = cursor.fetchone()

        employee_email = employee['email']

        # =========================================
        # EMAIL MESSAGE
        # =========================================

        msg = Message(

            subject=f"Travel Request Query - {travel['emp_name']}",

            recipients=[employee_email]

        )
        msg.body = f"""
Your travel request has been marked as QUERY.

Query Raised By:
{query_person}

Project:
{travel['project_name']}

Site:
{travel['site_name']}

Purpose:
{travel['purpose']}

Please contact the above person for clarification.
"""

        # =========================================
        # ATTACH PDF
        # =========================================

        pdf_path = os.path.join(
            'pdfs',
            travel['pdf_file']
        )

        if os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as pdf:
                msg.attach(
                    filename=travel['pdf_file'],
                    content_type='application/pdf',
                    data=pdf.read()
                )

        # =========================================
        # SEND EMAIL
        # =========================================

        try:

            mail.send(msg)

            logging.info("QUERY EMAIL SENT SUCCESSFULLY")

        except Exception as e:

            logging.error(f"QUERY EMAIL ERROR: {str(e)}")

        return redirect('/history')

    finally:

        cursor.close()
        db.close()
# =========================================
# QUERY PAGE
# =========================================

@approval_routes.route('/query-page/<int:id>')
@login_required
def query_page(id):

    if session.get('role') not in ['admin', 'ceo']:
        abort(403)

    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            SELECT *
            FROM travel_requests
            WHERE id=%s
        """, (id,))

        request_data = cursor.fetchone()

        if not request_data:
            abort(404)

        return render_template(
            'query_page.html',
            request_data=request_data
        )

    finally:

        cursor.close()
        db.close()