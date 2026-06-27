import os
from werkzeug.utils import secure_filename
from flask import Blueprint
from flask import request
from flask import jsonify
from flask import send_file
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    create_refresh_token
)
from schemas.request_schema import TravelRequestSchema
from werkzeug.security import check_password_hash

from database.db import get_db_connection

api_routes = Blueprint(
    "api_routes",
    __name__,
    url_prefix="/api/v1"
)

@api_routes.route(
    "/refresh",
    methods=["POST"]
)
@jwt_required(refresh=True)
def refresh():

    user_id = get_jwt_identity()

    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            SELECT *
            FROM users
            WHERE id=%s
        """, (user_id,))

        user = cursor.fetchone()

        access_token = create_access_token(
            identity=str(user["id"]),
            additional_claims={
                "emp_id": user["emp_id"],
                "role": user["role"]
            }
        )

        return jsonify({
            "access_token": access_token
        })

    finally:
        cursor.close()
        db.close()
# =========================================
# API LOGIN
# =========================================

@api_routes.route(
    "/login",
    methods=["POST"]
)
def api_login():
    """
Login API
---
tags:
  - Authentication
parameters:
  - in: body
    name: body
    required: true
    schema:
      properties:
        username:
          type: string
        password:
          type: string
responses:
  200:
    description: Login successful
"""

    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            SELECT *
            FROM users
            WHERE username=%s
        """, (username,))

        user = cursor.fetchone()

        if not user:

            return jsonify({
                "error": "Invalid username"
            }), 401

        if not check_password_hash(
            user["password"],
            password
        ):

            return jsonify({
                "error": "Invalid password"
            }), 401

        access_token = create_access_token(
        identity=str(user["id"]),
        additional_claims={
            "emp_id": user["emp_id"],
            "role": user["role"]
        }
    )
        refresh_token = create_refresh_token(
        identity=str(user["id"])
        )

        return jsonify({

            "access_token": access_token,
            "refresh_token": refresh_token,
            "username": user["username"],
            "role": user["role"],
            "emp_id": user["emp_id"]

        })

    finally:

        cursor.close()
        db.close()


# =========================================
# API REQUESTS
# =========================================

@api_routes.route("/requests")
@jwt_required()
def get_requests():
    """
    Get Travel Requests
    ---
    tags:
      - Requests

    security:
      - Bearer: []

    parameters:
      - name: page
        in: query
        type: integer

      - name: per_page
        in: query
        type: integer

    responses:
      200:
        description: List of travel requests
    """

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))

    offset = (page - 1) * per_page

    claims = get_jwt()
    role = claims["role"]
    emp_id = claims["emp_id"]

    db, cursor = get_db_connection()

    try:

        if role in ["admin", "ceo"]:

            cursor.execute("""
                SELECT *
                FROM travel_requests
                ORDER BY id DESC
                LIMIT %s OFFSET %s
            """, (per_page, offset))

        else:

            cursor.execute("""
                SELECT *
                FROM travel_requests
                WHERE emp_id=%s
                ORDER BY id DESC
                LIMIT %s OFFSET %s
            """, (
                emp_id,
                per_page,
                offset
            ))

        requests = cursor.fetchall()

        return jsonify({
            "page": page,
            "per_page": per_page,
            "data": requests
        })

    finally:
        cursor.close()
        db.close()

@api_routes.route("/analytics")
@jwt_required()
def analytics():
    """
Analytics Dashboard
---
tags:
  - Analytics

security:
  - Bearer: []

responses:
  200:
    description: Dashboard analytics
"""
    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            SELECT COUNT(*) total
            FROM travel_requests
        """)

        total = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) approved
            FROM travel_requests
            WHERE status='Approved'
        """)

        approved = cursor.fetchone()["approved"]

        cursor.execute("""
            SELECT COUNT(*) pending
            FROM travel_requests
            WHERE status='Pending'
        """)

        pending = cursor.fetchone()["pending"]

        cursor.execute("""
            SELECT IFNULL(SUM(amount_requested),0) total_amount
            FROM travel_requests
        """)

        amount = cursor.fetchone()["total_amount"]

        return jsonify({
            "total_requests": total,
            "approved_requests": approved,
            "pending_requests": pending,
            "total_amount": amount
        })

    finally:

        cursor.close()
        db.close()
# =========================================
# CREATE REQUEST API
# =========================================

@api_routes.route(
    "/requests",
    methods=["POST"]
)
@jwt_required()
def create_request():
    """
Create Travel Request
---
tags:
  - Requests

security:
  - Bearer: []

parameters:
  - in: body
    name: body
    schema:
      properties:

        project_name:
          type: string

        site_name:
          type: string

        request_date:
          type: string

        departure_date:
          type: string

        return_date:
          type: string

        total_days:
          type: integer

        amount_requested:
          type: number

responses:
  200:
    description: Request created
"""
    claims = get_jwt()

    emp_id = claims["emp_id"]

    db, cursor = get_db_connection()

    try:

        data = request.get_json()
        schema = TravelRequestSchema()
        errors = schema.validate(data)
        if errors:
            return jsonify({
                "success": False,
                "errors": errors
            }), 400
        project_name = data["project_name"]
        site_name = data["site_name"]
        request_date = data["request_date"]
        departure_date = data["departure_date"]
        return_date = data["return_date"]
        total_days = data["total_days"]
        period_name = data["period_name"]
        quarter = data["quarter"]
        purpose = data["purpose"]
        reason_text = data["reason_text"]
        amount_requested = data["amount_requested"]
        generated_link = (
            f"{project_name}/"
            f"{period_name}/"
            f"{site_name}/"
            f"{purpose}/"
            f"{quarter}"
        )

        cursor.execute("""
            SELECT emp_name
            FROM users
            WHERE emp_id=%s
        """, (emp_id,))

        employee = cursor.fetchone()

        emp_name = employee["emp_name"]

        cursor.execute("""
            INSERT INTO travel_requests
            (
                emp_id,
                emp_name,
                project_name,
                site_name,
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
                status,
                admin_approval,
                ceo_approval
            )
            VALUES
            (
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                'Pending',
                'Pending',
                'Pending'
            )
        """, (
            emp_id,
            emp_name,
            project_name,
            site_name,
            request_date,
            departure_date,
            return_date,
            total_days,
            period_name,
            quarter,
            purpose,
            reason_text,
            amount_requested,
            generated_link
        ))

        db.commit()

        return jsonify({
            "message": "Request created",
            "request_id": cursor.lastrowid
        })

    finally:

        cursor.close()
        db.close()
@api_routes.route(
    "/request/<int:request_id>"
)
@jwt_required()
def request_details(request_id):
    """
    Request Details
    ---
    tags:
      - Requests

    security:
      - Bearer: []

    parameters:
      - name: request_id
        in: path
        type: integer
        required: true

    responses:
      200:
        description: Request details
      404:
        description: Request not found
    """
    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            SELECT *
            FROM travel_requests
            WHERE id=%s
        """, (request_id,))

        request_data = cursor.fetchone()
        if not request_data:
            return jsonify({
                "error": "Request not found"
            }), 404
        claims = get_jwt()
        role = claims["role"]
        emp_id = claims["emp_id"]
        if role not in ["admin", "ceo", "accounts"]:
            if request_data["emp_id"] != emp_id:
                return jsonify({
                    "error": "Access denied"
                }), 403
        return jsonify(request_data)
    finally:

        cursor.close()
        db.close()
# =========================================
# APPROVE REQUEST
# =========================================
@api_routes.route(
    "/approve-request/<int:request_id>",
    methods=["POST"]
)
@jwt_required()
def api_approve_request(request_id):
    """
    Approve Travel Request
    ---
    tags:
      - Approvals

    security:
      - Bearer: []

    parameters:
      - name: request_id
        in: path
        type: integer
        required: true

    responses:
      200:
        description: Request approved
    """
    claims = get_jwt()

    role = claims["role"]

    db, cursor = get_db_connection()

    try:

        # Fetch request first
        cursor.execute("""
            SELECT *
            FROM travel_requests
            WHERE id=%s
        """, (request_id,))

        travel = cursor.fetchone()

        if not travel:

            return jsonify({
                "error": "Request not found"
            }), 404

        # ADMIN APPROVAL
        if role == "admin":

            cursor.execute("""
                UPDATE travel_requests
                SET
                    admin_approval='Approved',
                    status='Pending'
                WHERE id=%s
            """, (request_id,))

        # CEO APPROVAL
        elif role == "ceo":

            # ADD THIS BLOCK HERE
            if travel["admin_approval"] != "Approved":

                return jsonify({
                    "error": "Admin approval required first"
                }), 400

            cursor.execute("""
                UPDATE travel_requests
                SET
                    ceo_approval='Approved',
                    status='Approved'
                WHERE id=%s
            """, (request_id,))

        else:

            return jsonify({
                "error": "Unauthorized"
            }), 403

        db.commit()

        return jsonify({
            "message": "Request approved"
        })

    finally:

        cursor.close()
        db.close()
# =========================================
# GET SETTLEMENTS
# =========================================

@api_routes.route("/settlements")
@jwt_required()
def get_settlements():
    """
    Get Settlements
    ---
    tags:
      - Settlements

    security:
      - Bearer: []

    responses:
      200:
        description: List of settlements
    """
    claims = get_jwt()

    emp_id = claims["emp_id"]

    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            SELECT *
            FROM travel_requests
            WHERE emp_id=%s
            AND status='Approved'
            AND settlement_status IN ('Pending','Draft')
            ORDER BY id DESC
        """, (emp_id,))

        data = cursor.fetchall()

        return jsonify(data)

    finally:

        cursor.close()
        db.close()
# =========================================
# CREATE SETTLEMENT API
# =========================================

@api_routes.route(
    "/create-settlement/<int:request_id>",
    methods=["POST"]
)
@jwt_required()
def api_create_settlement(request_id):
    """
    Create Settlement
    ---
    tags:
      - Settlements

    security:
      - Bearer: []

    parameters:
      - name: request_id
        in: path
        type: integer
        required: true

      - in: body
        name: body
        schema:
          properties:
            project_reference:
              type: string
            arrival_date:
              type: string

    responses:
      200:
        description: Settlement created
    """
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

        if not request_data:

            return jsonify({
                "error": "Request not found"
            }), 404

        data = request.get_json()

        project_reference = data["project_reference"]
        arrival_date = data["arrival_date"]
        cursor.execute("""
            SELECT id
            FROM travel_settlements
            WHERE request_id=%s
        """, (request_id,))
        existing = cursor.fetchone()
        if existing:
            return jsonify({
                "error": "Settlement already exists"
            }), 400
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
            (
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
            )
        """, (

            request_id,
            request_data["emp_name"],
            request_data["designation"],
            request_data["posted_at"],
            request_data["site_name"],
            request_data["project_name"],
            project_reference,
            request_data["departure_date"],
            arrival_date,
            request_data["amount_requested"],
            0,
            0
        ))

        settlement_id = cursor.lastrowid

        cursor.execute("""
            UPDATE travel_requests
            SET settlement_status='Draft'
            WHERE id=%s
        """, (request_id,))

        db.commit()

        return jsonify({
            "message": "Settlement created",
            "settlement_id": settlement_id
        })

    finally:

        cursor.close()
        db.close()
# =========================================
# SETTLEMENT DETAILS API
# =========================================

@api_routes.route(
    "/settlement/<int:settlement_id>"
)
@jwt_required()
def settlement_details(settlement_id):

    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            SELECT *
            FROM travel_settlements
            WHERE id=%s
        """, (settlement_id,))

        settlement = cursor.fetchone()
        if not settlement:
            return jsonify({
                "error": "Settlement not found"
            }), 404
        cursor.execute("""
            SELECT emp_id
            FROM travel_requests
            WHERE id=%s
        """, (settlement["request_id"],))
        owner = cursor.fetchone()
        claims = get_jwt()
        role = claims["role"]
        emp_id = claims["emp_id"]
        if role not in ["admin", "ceo", "accounts"]:
            if owner["emp_id"] != emp_id:
                return jsonify({
                    "error": "Access denied"
                }), 403
        cursor.execute("""
            SELECT *
            FROM settlement_expenses
            WHERE settlement_id=%s
        """, (settlement_id,))

        expenses = cursor.fetchall()

        cursor.execute("""
            SELECT *
            FROM settlement_files
            WHERE settlement_id=%s
        """, (settlement_id,))

        files = cursor.fetchall()

        return jsonify({
            "settlement": settlement,
            "expenses": expenses,
            "files": files
        })

    finally:

        cursor.close()
        db.close()
@api_routes.route(
    "/add-expense/<int:settlement_id>",
    methods=["POST"]
)
@jwt_required()
def add_expense(settlement_id):
    """
    Add Expense
    ---
    tags:
      - Expenses

    security:
      - Bearer: []

    parameters:
      - name: settlement_id
        in: path
        type: integer
        required: true

      - in: body
        name: body
        schema:
          properties:
            expense_type:
              type: string
            amount:
              type: number

    responses:
      200:
        description: Expense added
    """
    db, cursor = get_db_connection()

    try:

        data = request.get_json()

        expense_type = data["expense_type"]
        expense_date = data["expense_date"]
        particulars = data["particulars"]
        mode = data["mode"]
        bill_no = data["bill_no"]
        amount = data["amount"]
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
            (
                %s,%s,%s,%s,%s,%s,%s
            )
        """, (
            settlement_id,
            expense_type,
            expense_date,
            particulars,
            mode,
            bill_no,
            amount
        ))
        # ==========================
        # HOTEL TOTAL
        # ==========================
        cursor.execute("""
            SELECT IFNULL(SUM(amount),0) total
            FROM settlement_expenses
            WHERE settlement_id=%s
            AND expense_type='Hotel'
        """, (settlement_id,))
        hotel_total = cursor.fetchone()["total"]
        # ==========================
        # FOOD TOTAL
        # ==========================
        cursor.execute("""
            SELECT IFNULL(SUM(amount),0) total
            FROM settlement_expenses
            WHERE settlement_id=%s
            AND expense_type='Food'
        """, (settlement_id,))
        food_total = cursor.fetchone()["total"]
        # ==========================
        # TRAVELLING TOTAL
        # ==========================
        cursor.execute("""
            SELECT IFNULL(SUM(amount),0) total
            FROM settlement_expenses
            WHERE settlement_id=%s
            AND expense_type='Travelling'
        """, (settlement_id,))
        travelling_total = cursor.fetchone()["total"]
        # ==========================
        # CONVEYANCE TOTAL
        # ==========================
        cursor.execute("""
            SELECT IFNULL(SUM(amount),0) total
            FROM settlement_expenses
            WHERE settlement_id=%s
            AND expense_type='Conveyance'
        """, (settlement_id,))
        conveyance_total = cursor.fetchone()["total"]
        # ==========================
        # OTHERS TOTAL
        # ==========================
        cursor.execute("""
            SELECT IFNULL(SUM(amount),0) total
            FROM settlement_expenses
            WHERE settlement_id=%s
            AND expense_type='Others'
        """, (settlement_id,))
        others_total = cursor.fetchone()["total"]
        # ==========================
        # OFFICE TOTAL
        # ==========================
        cursor.execute("""
            SELECT IFNULL(SUM(amount),0) total
            FROM settlement_expenses
            WHERE settlement_id=%s
            AND expense_type='Office'
        """, (settlement_id,))
        office_total = cursor.fetchone()["total"]
        # ==========================
        # GRAND TOTAL
        # ==========================
        total_expenses = (
            hotel_total +
            food_total +
            travelling_total +
            conveyance_total +
            others_total +
            office_total
        )
        # ==========================
        # ADVANCE RECEIVED
        # ==========================
        cursor.execute("""
            SELECT advance_received
            FROM travel_settlements
            WHERE id=%s
        """, (settlement_id,))
        advance = cursor.fetchone()["advance_received"]
        due_amount = total_expenses - advance
        # ==========================
        # UPDATE SETTLEMENT
        # ==========================
        cursor.execute("""
            UPDATE travel_settlements
            SET
                hotel_total=%s,
                food_total=%s,
                travelling_total=%s,
                conveyance_total=%s,
                others_total=%s,
                office_total=%s,
                total_expenses=%s,
                expense_incurred=%s,
                due_amount=%s
            WHERE id=%s
        """, (
            hotel_total,
            food_total,
            travelling_total,
            conveyance_total,
            others_total,
            office_total,
            total_expenses,
            total_expenses,
            due_amount,
            settlement_id
        ))
        db.commit()
        return jsonify({
            "message": "Expense added"
        })

    finally:

        cursor.close()
        db.close()
@api_routes.route(
    "/upload-bill/<int:settlement_id>",
    methods=["POST"]
)
@jwt_required()
def upload_bill(settlement_id):

    db, cursor = get_db_connection()

    try:

        if "file" not in request.files:

            return jsonify({
                "error": "No file uploaded"
            }), 400

        file = request.files["file"]

        filename = secure_filename(
            file.filename
        )

        upload_folder = "uploads"

        os.makedirs(
            upload_folder,
            exist_ok=True
        )

        filepath = os.path.join(
            upload_folder,
            filename
        )

        file.save(filepath)

        file_type = file.content_type

        file_size = os.path.getsize(
            filepath
        )

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
            (
                %s,%s,%s,%s,%s
            )
        """, (
            settlement_id,
            filename,
            filepath,
            file_type,
            file_size
        ))

        db.commit()

        return jsonify({
            "message": "File uploaded successfully"
        })

    finally:

        cursor.close()
        db.close()
@api_routes.route(
    "/submit-settlement/<int:request_id>",
    methods=["POST"]
)
@jwt_required()
def api_submit_settlement(request_id):

    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            UPDATE travel_requests
            SET settlement_status='Submitted'
            WHERE id=%s
        """, (request_id,))

        db.commit()

        return jsonify({
            "message": "Settlement submitted"
        })

    finally:

        cursor.close()
        db.close()
# =========================================
# SUBMITTED SETTLEMENTS
# =========================================

@api_routes.route(
    "/submitted-settlements"
)
@jwt_required()
def submitted_settlements():

    claims = get_jwt()

    role = claims["role"]

    if role != "accounts":

        return jsonify({
            "error": "Accounts access only"
        }), 403

    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            SELECT *
            FROM travel_requests
            WHERE settlement_status='Submitted'
            ORDER BY id DESC
        """)

        data = cursor.fetchall()

        return jsonify(data)

    finally:

        cursor.close()
        db.close()
# =========================================
# APPROVE SETTLEMENT
# =========================================

@api_routes.route(
    "/approve-settlement/<int:request_id>",
    methods=["POST"]
)
@jwt_required()
def approve_settlement(request_id):

    claims = get_jwt()

    if claims["role"] != "accounts":

        return jsonify({
            "error": "Accounts access only"
        }), 403

    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            UPDATE travel_requests
            SET
                settlement_status='Approved',
                settlement_approved_by=%s,
                settlement_approved_date=NOW()
            WHERE id=%s
        """, (
            claims["emp_id"],
            request_id
        ))

        db.commit()

        return jsonify({
            "message": "Settlement approved"
        })

    finally:

        cursor.close()
        db.close()
# =========================================
# REJECT SETTLEMENT
# =========================================

@api_routes.route(
    "/reject-settlement/<int:request_id>",
    methods=["POST"]
)
@jwt_required()
def reject_settlement(request_id):

    claims = get_jwt()

    if claims["role"] != "accounts":

        return jsonify({
            "error": "Accounts access only"
        }), 403

    db, cursor = get_db_connection()

    try:

        data = request.get_json()
        reason = data["reason"]
        cursor.execute("""
            UPDATE travel_requests
            SET
                settlement_status='Rejected',
                settlement_rejection_reason=%s
            WHERE id=%s
        """, (
            reason,
            request_id
        ))
        db.commit()

        return jsonify({
            "message": "Settlement rejected"
        })

    finally:

        cursor.close()
        db.close()
# =========================================
# MY DASHBOARD
# =========================================

@api_routes.route("/my-dashboard")
@jwt_required()
def my_dashboard():
    """
    My Dashboard
    ---
    tags:
      - Dashboard

    security:
      - Bearer: []

    responses:
      200:
        description: Employee dashboard statistics
    """
    claims = get_jwt()

    emp_id = claims["emp_id"]

    db, cursor = get_db_connection()

    try:

        # Pending Requests

        cursor.execute("""
            SELECT COUNT(*) count
            FROM travel_requests
            WHERE emp_id=%s
            AND status='Pending'
        """, (emp_id,))

        pending_requests = cursor.fetchone()["count"]

        # Approved Requests

        cursor.execute("""
            SELECT COUNT(*) count
            FROM travel_requests
            WHERE emp_id=%s
            AND status='Approved'
        """, (emp_id,))

        approved_requests = cursor.fetchone()["count"]

        # Draft Settlements

        cursor.execute("""
            SELECT COUNT(*) count
            FROM travel_requests
            WHERE emp_id=%s
            AND settlement_status='Draft'
        """, (emp_id,))

        draft_settlements = cursor.fetchone()["count"]

        # Submitted Settlements

        cursor.execute("""
            SELECT COUNT(*) count
            FROM travel_requests
            WHERE emp_id=%s
            AND settlement_status='Submitted'
        """, (emp_id,))

        submitted_settlements = cursor.fetchone()["count"]

        # Approved Settlements

        cursor.execute("""
            SELECT COUNT(*) count
            FROM travel_requests
            WHERE emp_id=%s
            AND settlement_status='Approved'
        """, (emp_id,))

        approved_settlements = cursor.fetchone()["count"]

        return jsonify({

            "pending_requests": pending_requests,

            "approved_requests": approved_requests,

            "draft_settlements": draft_settlements,

            "submitted_settlements": submitted_settlements,

            "approved_settlements": approved_settlements

        })

    finally:

        cursor.close()
        db.close()
@api_routes.route(
    "/files/<int:settlement_id>"
)
@jwt_required()
def get_files(settlement_id):

    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            SELECT *
            FROM settlement_files
            WHERE settlement_id=%s
            ORDER BY uploaded_at DESC
        """, (settlement_id,))

        files = cursor.fetchall()

        return jsonify(files)

    finally:

        cursor.close()
        db.close()
@api_routes.route(
    "/download-file/<int:file_id>"
)
@jwt_required()
def download_file(file_id):

    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            SELECT *
            FROM settlement_files
            WHERE id=%s
        """, (file_id,))

        file = cursor.fetchone()

        if not file:

            return jsonify({
                "error": "File not found"
            }), 404

        return send_file(
            file["stored_filename"],
            as_attachment=True
        )

    finally:

        cursor.close()
        db.close()
@api_routes.route(
    "/delete-file/<int:file_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_file(file_id):

    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            SELECT *
            FROM settlement_files
            WHERE id=%s
        """, (file_id,))

        file = cursor.fetchone()

        if not file:

            return jsonify({
                "error": "File not found"
            }), 404

        if os.path.exists(
            file["stored_filename"]
        ):
            os.remove(
                file["stored_filename"]
            )

        cursor.execute("""
            DELETE FROM settlement_files
            WHERE id=%s
        """, (file_id,))

        db.commit()

        return jsonify({
            "message": "File deleted"
        })

    finally:

        cursor.close()
        db.close()
@api_routes.route(
    "/settlement-summary/<int:settlement_id>"
)
@jwt_required()
def settlement_summary(settlement_id):
    """
    Settlement Summary
    ---
    tags:
      - Settlements

    security:
      - Bearer: []

    parameters:
      - name: settlement_id
        in: path
        type: integer
        required: true

    responses:
      200:
        description: Settlement summary
    """
    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            SELECT *
            FROM travel_settlements
            WHERE id=%s
        """, (settlement_id,))

        settlement = cursor.fetchone()

        cursor.execute("""
            SELECT *
            FROM settlement_expenses
            WHERE settlement_id=%s
        """, (settlement_id,))

        expenses = cursor.fetchall()

        cursor.execute("""
            SELECT *
            FROM settlement_files
            WHERE settlement_id=%s
        """, (settlement_id,))

        files = cursor.fetchall()

        return jsonify({
            "settlement": settlement,
            "expenses": expenses,
            "files": files
        })

    finally:

        cursor.close()
        db.close()