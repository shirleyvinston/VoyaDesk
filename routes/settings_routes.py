from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    abort
)

from database.db import get_db_connection
from utils.decorators import login_required

settings_routes = Blueprint(
    'settings_routes',
    __name__
)

# =====================================
# SETTINGS PAGE
# =====================================

@settings_routes.route('/settings')
@login_required
def settings():

    if session.get('role') not in ['admin', 'ceo']:
        abort(403)

    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            SELECT *
            FROM regions
            ORDER BY region_name
        """)
        regions = cursor.fetchall()

        cursor.execute("""
            SELECT *
            FROM projects
            ORDER BY project_name
        """)
        projects = cursor.fetchall()

        cursor.execute("""
            SELECT *
            FROM substations
            ORDER BY substation_name
        """)
        substations = cursor.fetchall()

        cursor.execute("""
            SELECT *
            FROM users
            ORDER BY emp_name
        """)
        employees = cursor.fetchall()

        return render_template(
            'settings.html',
            regions=regions,
            projects=projects,
            substations=substations,
            employees=employees
        )

    finally:

        cursor.close()
        db.close()


# =========================================
# ADD REGION
# =========================================

@settings_routes.route('/add-region', methods=['POST'])
@login_required
def add_region():

    if session.get('role') not in ['admin', 'ceo']:
        abort(403)

    db, cursor = get_db_connection()

    try:

        region_name = request.form['region_name']

        cursor.execute("""
            INSERT INTO regions(region_name)
            VALUES(%s)
        """, (region_name,))

        db.commit()

        return redirect('/settings')

    finally:

        cursor.close()
        db.close()


# =========================================
# ADD PROJECT
# =========================================

@settings_routes.route('/add-project', methods=['POST'])
@login_required
def add_project():

    if session.get('role') not in ['admin', 'ceo']:
        abort(403)

    db, cursor = get_db_connection()

    try:

        project_name = request.form['project_name']

        cursor.execute("""
            INSERT INTO projects(project_name)
            VALUES(%s)
        """, (project_name,))

        db.commit()

        return redirect('/settings')

    finally:

        cursor.close()
        db.close()


# =========================================
# ADD SITE
# =========================================

@settings_routes.route('/add-site', methods=['POST'])
@login_required
def add_site():

    if session.get('role') not in ['admin', 'ceo']:
        abort(403)

    db, cursor = get_db_connection()

    try:

        site_name = request.form['site_name']

        region_id = request.form['region_id']

        cursor.execute("""
            INSERT INTO substations
            (
                substation_name,
                region_id
            )
            VALUES(%s,%s)
        """, (
            site_name,
            region_id
        ))

        db.commit()

        return redirect('/settings')

    finally:

        cursor.close()
        db.close()


# =========================================
# ADD EMPLOYEE
# =========================================

@settings_routes.route('/add-employee', methods=['POST'])
@login_required
def add_employee():

    if session.get('role') not in ['admin', 'ceo']:
        abort(403)

    db, cursor = get_db_connection()

    try:

        emp_id = request.form['emp_id']
        emp_name = request.form['emp_name']

        cursor.execute("""
            INSERT INTO employees
            (
                emp_id,
                emp_name
            )
            VALUES(%s,%s)
        """, (
            emp_id,
            emp_name
        ))

        db.commit()

        return redirect('/settings')

    finally:

        cursor.close()
        db.close()