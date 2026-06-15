import logging
from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    session,
    abort
)

from database.db import get_db_connection
from utils.decorators import login_required

analytics_routes = Blueprint(
    'analytics_routes',
    __name__
)
# =========================================
# ANALYTICS
# =========================================

@analytics_routes.route('/analytics')
@login_required
def analytics():

    if session.get('role') not in ['admin', 'ceo']:
        abort(403)

    db, cursor = get_db_connection()

    try:

        # TOTAL REQUESTS

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM travel_requests
        """)

        total_requests = cursor.fetchone()['total']

        # APPROVED REQUESTS

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM travel_requests
            WHERE status='Approved'
        """)

        approved_requests = cursor.fetchone()['total']

        # PENDING REQUESTS

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM travel_requests
            WHERE status='Pending'
        """)

        pending_requests = cursor.fetchone()['total']

        cursor.execute("""
            SELECT DISTINCT emp_name
            FROM travel_requests
            ORDER BY emp_name
        """)

        employees = cursor.fetchall()
        return render_template(
            'analytics.html',
            total_requests=total_requests,
            approved_requests=approved_requests,
            pending_requests=pending_requests,
            employees=employees
        )

    finally:

        cursor.close()
        db.close()

@analytics_routes.route('/analytics-data')
@login_required
def analytics_data():

    if session.get('role') not in ['admin', 'ceo']:
        return jsonify({"error": "Access Denied"})

    db, cursor = get_db_connection()

    try:

        # =========================================
        # FILTER VALUES
        # =========================================

        employee = request.args.get('employee', 'ALL')
        purpose = request.args.get('purpose', 'ALL')

        chart_type = request.args.get('chart_type', 'monthly')

        pie_filter = request.args.get('pie_filter', '')

        line_chart_type = request.args.get(
            'line_chart_type',
            'monthly'
        )

        # =========================================
        # WHERE CONDITIONS
        # =========================================

        conditions = ["status='Approved'"]

        values = []

        if employee != "ALL":

            conditions.append("emp_name=%s")

            values.append(employee)

        if purpose != "ALL":

            conditions.append("purpose=%s")

            values.append(purpose)

        where_clause = " AND ".join(conditions)

        # =========================================
        # BAR CHART
        # =========================================

        if chart_type == "yearly":
            cursor.execute(f"""
                SELECT
                    YEAR(request_date) AS label,
                    COUNT(*) AS total
                FROM travel_requests
                WHERE {where_clause}
                GROUP BY YEAR(request_date)
                ORDER BY YEAR(request_date)
            """, values)

        else:

            cursor.execute(f"""
                SELECT
                    MONTH(request_date) AS month_number,
                    MONTHNAME(request_date) AS label,
                    COUNT(*) AS total
                FROM travel_requests
                WHERE {where_clause}
                GROUP BY
                    MONTH(request_date),
                    MONTHNAME(request_date)
                ORDER BY month_number
            """, values)

        bar_data = cursor.fetchall()

        # =========================================
        # PIE CHART
        # =========================================

        pie_conditions = conditions.copy()

        pie_values = values.copy()

        if chart_type == "yearly" and pie_filter:

            pie_conditions.append("YEAR(request_date)=%s")

            pie_values.append(pie_filter)

        elif chart_type == "monthly" and pie_filter:

            pie_conditions.append("MONTHNAME(request_date)=%s")

            pie_values.append(pie_filter)

        pie_where = " AND ".join(pie_conditions)

        cursor.execute(f"""
            SELECT
                site_name,
                COUNT(*) AS total
            FROM travel_requests
            WHERE {pie_where}
            GROUP BY site_name
            ORDER BY total DESC
        """, pie_values)

        pie_data = cursor.fetchall()

        # =========================================
        # LINE CHART
        # =========================================

        if line_chart_type == "yearly":

            cursor.execute(f"""
                SELECT
                    YEAR(request_date) AS label,
                    COUNT(*) AS total
                FROM travel_requests
                WHERE {where_clause}
                GROUP BY YEAR(request_date)
                ORDER BY YEAR(request_date)
            """, values)

        else:

            cursor.execute(f"""
                SELECT
                    MONTH(request_date) AS month_number,
                    MONTHNAME(request_date) AS label,
                    COUNT(*) AS total
                FROM travel_requests
                WHERE {where_clause}
                GROUP BY
                    MONTH(request_date),
                    MONTHNAME(request_date)
                ORDER BY month_number
            """, values)

        line_data = cursor.fetchall()

        # =========================================
        # EMPLOYEE PURPOSE COUNTS
        # =========================================

        purpose_conditions = conditions.copy()

        purpose_values = values.copy()

        cursor.execute(f"""
            SELECT
                purpose,
                COUNT(*) AS total
            FROM travel_requests
            WHERE {' AND '.join(purpose_conditions)}
            GROUP BY purpose
            ORDER BY purpose
        """, purpose_values)

        purpose_data = cursor.fetchall()

        employee_purpose_counts = {}

        for row in purpose_data:
            employee_purpose_counts[row['purpose']] = row['total']

        # =========================================
        # SITE COUNTS
        # =========================================

        site_conditions = conditions.copy()

        site_values = values.copy()
        cursor.execute(f"""
            SELECT
                site_name,
                COUNT(*) AS total
            FROM travel_requests
            WHERE {' AND '.join(site_conditions)}
            GROUP BY site_name
            ORDER BY total DESC
        """, site_values)

        site_data = cursor.fetchall()

        site_counts = {}

        for row in site_data:
            site_counts[row['site_name']] = row['total']

        # =========================================
        # RETURN JSON
        # =========================================

        return jsonify({

            "bar_labels":
                [row['label'] for row in bar_data],

            "bar_values":
                [row['total'] for row in bar_data],

            "pie_labels":
                [row['site_name'] for row in pie_data],

            "pie_values":
                [row['total'] for row in pie_data],

            "line_labels":
                [row['label'] for row in line_data],

            "line_values":
                [row['total'] for row in line_data],

            "employee_purpose_counts":
                employee_purpose_counts,

            "site_counts":
                site_counts

        })
    except Exception as e:

        logging.error(f"ANALYTICS ERROR: {str(e)}")

        return jsonify({
            "error": "Something went wrong"
        })
    finally:
        cursor.close()
        db.close()
