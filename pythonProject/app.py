from flask import Flask, render_template, request, redirect, session, flash, url_for
from database import create_tables, add_user, login_user, apply_leave, view_leaves, update_leave_status, get_leave_balance
from helpers import get_user_by_id, get_db_connection  # Ensure correct import of get_db_connection
import pyodbc

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Secret key for session management

# Ensure tables are created on startup
create_tables()

@app.route('/')
def index():
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(f"Attempting login with username: {username}, password: {password}")

        user = login_user(username, password)
        if user:
            session['user'] = user
            flash('Logged in successfully!', 'success')
            if user['role'] == 'admin':
                return redirect('/admin_dashboard')
            return redirect('/user_dashboard')

        flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        employee_id = request.form['employee_id']
        mobile_number = request.form['mobile_number']
        add_user(username, password, role, employee_id, mobile_number)
        flash('Registered successfully! You can now log in.', 'success')
        return redirect('/login')
    return render_template('register.html')


@app.route('/user_dashboard', methods=['GET', 'POST'])
def user_dashboard():
    if 'user' not in session:
        return redirect('/login')

    user_id = session['user']['id']

    if request.method == 'POST':
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')
        leave_type = request.form.get('leave_type')
        apply_leave(user_id, from_date, to_date, leave_type)

    leaves = view_leaves('user', user_id)
    return render_template('user_dashboard.html', leaves=leaves)


@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'user' not in session or session['user']['role'] != 'admin':
        return redirect('/login')

    if request.method == 'POST':
        leave_id = request.form['leave_id']
        status = request.form['status']
        update_leave_status(leave_id, status)

    leaves = view_leaves('admin')
    return render_template('admin_dashboard.html', leaves=leaves)


@app.route('/employee/leave_balance', methods=['GET'])
def view_leave_balance():
    if 'user' not in session:
        return redirect('/login')

    user_id = session['user']['id']
    year = request.args.get('year', default=2024, type=int)  # Get year from query string (default to 2024)

    leave_balance = get_leave_balance(user_id, year)

    if leave_balance:
        return render_template('employee_leave_balance.html', leave_balance=leave_balance)
    else:
        flash('No leave balance found for the specified year.', 'danger')
        return redirect('/user_dashboard')  # Redirect to user dashboard if not found


@app.route('/admin/update_leave/<int:user_id>', methods=['GET', 'POST'])
def admin_update_leave(user_id):
    if request.method == 'GET':
        # Fetch user data
        user = get_user_by_id(user_id)
        if user:
            return render_template('update_leave.html', user=user)
        else:
            return "User not found", 404

    if request.method == 'POST':
        # Handle the form submission and update the leave record
        updated_leave = request.form.get('leave')  # Using .get() to avoid KeyError if 'leave' is not present
        if updated_leave is not None:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE Users SET leave_days = ? WHERE id = ?', (updated_leave, user_id))
            conn.commit()
            conn.close()
            flash('Leave days updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Leave days field is required.', 'danger')
            return redirect(url_for('admin_update_leave', user_id=user_id))

    return render_template('update_leave.html', user=get_user_by_id(user_id))


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)
