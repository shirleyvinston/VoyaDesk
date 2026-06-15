import os
import logging
from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    session,
)
from database.db import get_db_connection
from utils.decorators import login_required
from routes.auth_routes import auth
from routes.dashboard_routes import dashboard
from routes.settings_routes import settings_routes
from routes.request_routes import request_routes
from routes.approval_routes import approval_routes
from routes.analytics_routes import analytics_routes
from routes.settlement_routes import settlement_routes
# =========================================
# FLASK APP
# =========================================

app = Flask(__name__)
app.register_blueprint(auth)
app.register_blueprint(dashboard)
app.register_blueprint(settings_routes)
app.register_blueprint(request_routes)
app.register_blueprint(approval_routes)
app.register_blueprint(analytics_routes)
app.register_blueprint(settlement_routes)
from extensions import mail
load_dotenv()
if not os.getenv("SECRET_KEY"):
    raise ValueError("SECRET_KEY not found in .env")
if not os.getenv("MAIL_USERNAME"):
    raise ValueError("MAIL_USERNAME not found")

if not os.getenv("MAIL_PASSWORD"):
    raise ValueError("MAIL_PASSWORD not found")
app.secret_key = os.getenv("SECRET_KEY")
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_USERNAME")
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

mail.init_app(app)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

# =========================================
# PDF FOLDER
# =========================================

if not os.path.exists("pdfs"):
    os.makedirs("pdfs")
if not os.path.exists("uploads"):
    os.makedirs("uploads")
# =========================================
# NEW REQUEST
# =========================================

@app.route('/new-request')
@login_required
def new_request():

    db, cursor = get_db_connection()

    try:

        cursor.execute("""
            SELECT *
            FROM substations
            ORDER BY substation_name
        """)

        sites = cursor.fetchall()

        cursor.execute("""
            SELECT *
            FROM projects
            ORDER BY project_name
        """)

        projects = cursor.fetchall()

        employee_data = {
            "emp_id": session['emp_id'],
            "emp_name": session['emp_name']
        }

        return render_template(
            'new_request.html',
            sites=sites,
            projects=projects,
            employee_data=employee_data
        )

    finally:

        cursor.close()
        db.close()
# =========================================
# RUN APP
# =========================================

if __name__ == '__main__':
    app.run(debug=True)