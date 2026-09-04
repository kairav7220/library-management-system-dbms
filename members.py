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

def next_mem_id():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(CAST(SUBSTRING(mem_id, 5) AS UNSIGNED)) AS m FROM members WHERE mem_id LIKE 'MEM\\_%'")
            n = (cur.fetchone()['m'] or 0) + 1
    return f'MEM_{n}'

def add_member(name, user_id, password, email, phone, user_row_num,
               permanent_address, temporary_address):
    mem_id = next_mem_id()
    password_hash = generate_password_hash(password) if password else None
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO members (mem_id, name, user_id, password, email, phone,"
                " user_row_num, permanent_address, temporary_address, status)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (mem_id, name, user_id, password_hash, email, phone, user_row_num,
                 permanent_address, temporary_address, 0)
            )
    return mem_id

def update_member(row_num, *, name=None, user_id=None, password=None, email=None,
                  phone=None, user_row_num=None, permanent_address=None,
                  temporary_address=None):
    if password:
        password = generate_password_hash(password)
    fields, vals = [], []
    for col, v in (('name', name), ('user_id', user_id), ('password', password),
                   ('email', email), ('phone', phone), ('user_row_num', user_row_num),
                   ('permanent_address', permanent_address),
                   ('temporary_address', temporary_address)):
        if v is not None:
            fields.append(f'`{col}`=%s')
            vals.append(v)
    if not fields:
        return row_num
    vals.append(row_num)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE members SET {', '.join(fields)} WHERE row_num = %s",
                tuple(vals)
            )
    return row_num

def get_member_by_row_num(row_num):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM members WHERE row_num=%s', (row_num,))
            return cur.fetchone()

def get_all_members():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM members WHERE status=0 ORDER BY row_num')
            return cur.fetchall()

def delete_member(row_num):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE members SET status=1 WHERE row_num=%s', (row_num,))
    return row_num

if __name__ == '__main__':
    print(add_member('ajay', 'USER_1', 'user123', 'user@test.com', 9876543210,
                     2, 'abc', 'abcd'))
    print(get_member_by_row_num(2))
    print(get_all_members())
    print(delete_member(2))
