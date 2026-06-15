from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from database.db import get_db_connection

auth = Blueprint('auth', __name__)
# =========================================
# LOGIN
# =========================================

@auth.route('/login', methods=['GET', 'POST'])
def login():

    db, cursor = get_db_connection()

    try:

        if request.method == 'POST':

            username = request.form['username']
            password = request.form['password']

            cursor.execute("""
                SELECT *
                FROM users
                WHERE username=%s
            """, (username,))

            user = cursor.fetchone()

            if user and check_password_hash(user['password'], password):

                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                session['emp_name'] = user['emp_name']
                session['emp_id'] = user['emp_id']
                session['email'] = user['email']

                return redirect('/')

            return "Invalid Login"

        return render_template('login.html')

    finally:

        cursor.close()
        db.close()
# =========================================
# SIGNUP
# =========================================

@auth.route('/signup', methods=['GET', 'POST'])
def signup():

    db, cursor = get_db_connection()

    try:

        if request.method == 'POST':

            # FORM DATA

            emp_name = request.form['emp_name']

            username = request.form['username']

            password = request.form['password']

            hashed_password = generate_password_hash(password)

            email = request.form['email']

            # FETCH EMPLOYEE DETAILS FROM DATABASE

            cursor.execute("""
                SELECT *
                FROM employees
                WHERE UPPER(emp_name)=UPPER(%s)
            """, (emp_name,))

            employee = cursor.fetchone()

            # IF EMPLOYEE NOT FOUND

            if not employee:

                return "Employee not found in database"

            # FETCH EMPLOYEE ID

            emp_id = employee['emp_id']

            # CHECK IF EMPLOYEE ALREADY REGISTERED

            cursor.execute("""
                SELECT *
                FROM users
                WHERE emp_id=%s
            """, (emp_id,))

            existing_employee = cursor.fetchone()

            if existing_employee:

                return "Employee already registered"

            # CHECK EXISTING USERNAME

            cursor.execute("""
                SELECT *
                FROM users
                WHERE username=%s
            """, (username,))

            existing_user = cursor.fetchone()

            if existing_user:

                return "Username already exists"
            cursor.execute("""
                SELECT *
                FROM users
                WHERE email=%s
            """, (email,))

            existing_email = cursor.fetchone()

            if existing_email:
                return "Email already exists"
            # INSERT USER

            cursor.execute("""
                INSERT INTO users
                (
                    emp_id,
                    emp_name,
                    username,
                    password,
                    role,
                    email
                )
                VALUES
                (%s,%s,%s,%s,%s,%s)
            """, (
                emp_id,
                emp_name,
                username,
                hashed_password,
                'employee',
                email
            ))

            db.commit()

            return redirect('/login')

        return render_template('signup.html')

    finally:

        cursor.close()
        db.close()

# =========================================
# LOGOUT
# =========================================

@auth.route('/logout')
def logout():

    session.clear()

    return redirect('/login')


