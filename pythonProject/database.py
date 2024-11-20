from werkzeug.security import generate_password_hash, check_password_hash
import pyodbc

# Replace with your SQL Server credentials
DATABASE_CONFIG = {
    'server': '103.101.58.125',
    'database': 'LeaveMate',
    'username': 'sa',
    'password': 'sap@123',
    'driver': '{ODBC Driver 17 for SQL Server}'
}


def get_connection():
    connection_string = (
        f"DRIVER={DATABASE_CONFIG['driver']};"
        f"SERVER={DATABASE_CONFIG['server']};"
        f"DATABASE={DATABASE_CONFIG['database']};"
        f"UID={DATABASE_CONFIG['username']};"
        f"PWD={DATABASE_CONFIG['password']}"
    )
    return pyodbc.connect(connection_string)


# Creating tables for users and leaves
def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U')
        CREATE TABLE users (
            id INT IDENTITY(1,1) PRIMARY KEY,
            username NVARCHAR(100) NOT NULL UNIQUE,
            password NVARCHAR(255) NOT NULL,
            role NVARCHAR(50) NOT NULL,
            employee_id NVARCHAR(50) NOT NULL UNIQUE,
            mobile_number NVARCHAR(15) NOT NULL
        )
    ''')

    cursor.execute('''
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='leaves' AND xtype='U')
        CREATE TABLE leaves (
            id INT IDENTITY(1,1) PRIMARY KEY,
            user_id INT NOT NULL,
            from_date DATE NOT NULL,
            to_date DATE NOT NULL,
            leave_type NVARCHAR(50) NOT NULL,
            status NVARCHAR(50) DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()


# Add user with hashed password
def add_user(username, password, role, employee_id, mobile_number):
    conn = get_connection()
    cursor = conn.cursor()

    # Hash the password before storing
    hashed_password = generate_password_hash(password)

    cursor.execute(
        "INSERT INTO users (username, password, role, employee_id, mobile_number) VALUES (?, ?, ?, ?, ?)",
        (username, hashed_password, role, employee_id, mobile_number)
    )
    conn.commit()
    conn.close()


# Login user with password verification
def login_user(username, password):
    """
    Logs in a user by checking the username and password.
    Returns user details if found, else None.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Check if the username exists in the database
    cursor.execute("SELECT id, username, password, role FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    conn.close()

    # Check if the user exists and the password matches
    if user and user.password == password:
        return {'id': user.id, 'username': user.username, 'role': user.role}

    return None

# Apply for leave
def apply_leave(user_id, from_date, to_date, leave_type):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO leaves (user_id, from_date, to_date, leave_type) VALUES (?, ?, ?, ?)",
        (user_id, from_date, to_date, leave_type)
    )
    conn.commit()
    conn.close()


# View leave applications based on role (user or admin)
def view_leaves(role, user_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    if role == 'admin':
        cursor.execute("SELECT * FROM leaves")
    else:
        cursor.execute("SELECT * FROM leaves WHERE user_id = ?", (user_id,))

    leaves = cursor.fetchall()
    conn.close()

    return [
        {
            'id': row[0],
            'user_id': row[1],
            'from_date': row[2],
            'to_date': row[3],
            'leave_type': row[4],
            'status': row[5]
        }
        for row in leaves
    ]


# Update leave status by admin (approve/reject)
def update_leave_status(leave_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE leaves SET status = ? WHERE id = ?",
        (status, leave_id)
    )
    conn.commit()
    conn.close()

def get_leave_balance(user_id, year):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT total_leaves, leaves_taken FROM leave_balances WHERE user_id = ? AND year = ?", (user_id, year))
    balance = cursor.fetchone()
    conn.close()

    if balance:
        return {'total_leaves': balance[0], 'leaves_taken': balance[1], 'remaining_leaves': balance[0] - balance[1]}
    return None

def update_leave_balance(user_id, year, leaves_taken):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT total_leaves, leaves_taken FROM leave_balances WHERE user_id = ? AND year = ?", (user_id, year))
    balance = cursor.fetchone()

    if balance:
        new_leaves_taken = balance[1] + leaves_taken
        cursor.execute("UPDATE leave_balances SET leaves_taken = ? WHERE user_id = ? AND year = ?", (new_leaves_taken, user_id, year))
        conn.commit()
    else:
        # If no record exists for that user in the given year, create one
        cursor.execute("INSERT INTO leave_balances (user_id, year, total_leaves, leaves_taken) VALUES (?, ?, ?, ?)",
                       (user_id, year, 30, leaves_taken))  # Default 30 total leaves
        conn.commit()

    conn.close()
