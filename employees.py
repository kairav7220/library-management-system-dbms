import os, pymysql
from dotenv import load_dotenv
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

def next_emp_id():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(CAST(SUBSTRING(emp_id, 5) AS UNSIGNED)) AS m FROM employees WHERE emp_id LIKE 'EMP\\_%'")
            n = (cur.fetchone()['m'] or 0) + 1
    return f'EMP_{n}'

def add_employee(name, user_id, password, email, phone, designation,
                 salary, user_row_num, permanent_address, temporary_address):
    emp_id = next_emp_id()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO employees (emp_id, name, user_id, password, email, phone,"
                " designation, salary, user_row_num, permanent_address, temporary_address, status)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (emp_id, name, user_id, password, email, phone, designation,
                 salary, user_row_num, permanent_address, temporary_address, 0)
            )
    return emp_id

def update_employee(row_num, *, name=None, user_id=None, password=None, email=None,
                    phone=None, designation=None, salary=None, user_row_num=None,
                    permanent_address=None, temporary_address=None):
    fields, vals = [], []
    for col, v in (('name', name), ('user_id', user_id), ('password', password),
                   ('email', email), ('phone', phone), ('designation', designation),
                   ('salary', salary), ('user_row_num', user_row_num),
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
                f"UPDATE employees SET {', '.join(fields)} WHERE row_num = %s",
                tuple(vals)
            )
    return row_num

def get_employee_by_row_num(row_num):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM employees WHERE row_num=%s', (row_num,))
            return cur.fetchone()

def get_all_employees():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM employees WHERE status=0 ORDER BY row_num')
            return cur.fetchall()

def delete_employee(row_num):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE employees SET status=1 WHERE row_num=%s', (row_num,))
    return row_num

if __name__ == '__main__':
    print(add_employee('raju', 'USER_6', 'emp123', 'emp@test.com', 9876543210,
                       'librarian', 10000, 2, 'werw', 'rtw'))
    print(get_employee_by_row_num(2))
    print(get_all_employees())
    print(delete_employee(2))
