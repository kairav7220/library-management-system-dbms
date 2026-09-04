import os, pymysql
from datetime import datetime
from dotenv import load_dotenv
from werkzeug.security import check_password_hash
load_dotenv()

def get_connection():
    host = os.getenv('MYSQL_HOST', 'localhost')
    ssl = {'ssl': {}} if 'tidbcloud' in host else None
    conn = pymysql.connect(
        host=host,
        port=int(os.getenv('MYSQL_PORT', '3306')),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', 'root'),
        database=os.getenv('MYSQL_DB', 'library_db'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        ssl=ssl
    )
    return conn

def login(username, password):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM users WHERE username=%s AND status=0', (username,))
            user = cur.fetchone()
    if user and check_password_hash(user['password'], password):
        print('Successful Login!')
        log_action(f'{username} has logged in')
        return True
    else:
        print('Login failed!')
        return False

def logout(username):
    log_action(f'{username} has logged out')

def log_action(action):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO logs (timestamp, action) VALUES (%s, %s)',
                (datetime.now().strftime('%d-%m-%Y %I:%M:%S %p'), action)
            )

if __name__ == '__main__':
    print(login('admin', 'admin123'))
    print(logout('admin'))
