from flask import (
    Blueprint,
    render_template,
    abort
)
from flask import request, redirect
from database.db import get_db_connection
from utils.decorators import login_required

dashboard = Blueprint('dashboard', __name__)
# =========================================
# DASHBOARD
# ========================================

@dashboard.route('/')
@login_required
def index():

    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            SELECT *
            FROM regions
            ORDER BY region_name
        """)

        regions = cursor.fetchall()

        return render_template(
            'index.html',
            regions=regions
        )

    finally:

        cursor.close()
        db.close()


# =========================================
# REGION PAGE
# =========================================

@dashboard.route('/region/<int:region_id>')
@login_required
def region(region_id):

    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            SELECT *
            FROM regions
            WHERE id=%s
        """, (region_id,))

        region = cursor.fetchone()
        if not region:
            abort(404)
        cursor.execute("""
            SELECT *
            FROM substations
            WHERE region_id=%s
            ORDER BY substation_name
        """, (region_id,))

        substations = cursor.fetchall()

        return render_template(
            'region.html',
            region=region,
            substations=substations
        )

    finally:

        cursor.close()
        db.close()
# =========================================
# SUBSTATION PAGE
# =========================================

@dashboard.route('/substation/<int:substation_id>')
@login_required
def substation(substation_id):

    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            SELECT *
            FROM substations
            WHERE id=%s
        """, (substation_id,))

        substation = cursor.fetchone()
        if not substation:
            abort(404)
        cursor.execute("""
            SELECT *
            FROM travel_requests
            WHERE substation_id=%s
            ORDER BY id DESC
        """, (substation_id,))

        requests_data = cursor.fetchall()

        return render_template(
            'site_requests.html',
            substation=substation,
            requests_data=requests_data
        )

    finally:

        cursor.close()
        db.close()
@dashboard.route(
    '/update-comments/<int:request_id>',
    methods=['POST']
)
@login_required
def update_comments(request_id):

    comments = request.form.get('comments')

    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            UPDATE travel_requests
            SET comments=%s
            WHERE id=%s
        """, (
            comments,
            request_id
        ))

        db.commit()

        return redirect(
            request.referrer or '/'
        )

    finally:

        cursor.close()
        db.close()
