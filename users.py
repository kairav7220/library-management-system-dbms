import os, pymysql
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
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

def next_user_id():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(CAST(SUBSTRING(user_id, 6) AS UNSIGNED)) AS m FROM users WHERE user_id LIKE 'USER\\_%'")
            row = cur.fetchone()
            n = (row['m'] or 0) + 1
    return f'USER_{n}'

def add_user(user_type, username, password, email, phone):
    user_id = next_user_id()
    password_hash = generate_password_hash(password) if password else None
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO users (user_id, user_type, username, password, email, phone, status) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (user_id, user_type, username, password_hash, email, phone, 0)
            )
    return user_id

def get_user_by_id(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM users WHERE user_id=%s AND status=0', (user_id,))
            return cur.fetchone()

def get_all_users():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM users WHERE status=0 ORDER BY row_num')
            return cur.fetchall()

def delete_user(row_num):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE users SET status=1 WHERE row_num=%s', (row_num,))
    return row_num

if __name__ == '__main__':
    print(add_user('member', 'john', 'pass123', 'john@test.com', 9876543210))
    print(get_user_by_id('USER_1'))
    print(get_all_users())
    print(delete_user(3))