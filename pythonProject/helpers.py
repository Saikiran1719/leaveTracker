import pyodbc

def get_db_connection():
    server = '103.101.58.125'
    database = 'LeaveMate'
    username = 'sa'
    password = 'sap@123'
    conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                          f'SERVER={server};'
                          f'DATABASE={database};'
                          f'UID={username};'
                          f'PWD={password}')
    return conn


def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return {'id': user[0], 'username': user[1], 'role': user[2],
                'leave_days': user[3]}  # Adjust according to your DB schema
    return None