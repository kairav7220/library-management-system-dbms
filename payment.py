import os, pymysql
from datetime import datetime
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

def next_txn_id():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(CAST(SUBSTRING(transaction_id, 5) AS UNSIGNED)) AS m FROM payments WHERE transaction_id LIKE 'TXN\\_%'")
            n = (cur.fetchone()['m'] or 0) + 1
    return f'TXN_{n}'

def add_payment(transaction_date, payment_amount, payment_type, payment_mode,
                payment_status, paid_by, recieved_by, user_row_num):
    transaction_id = next_txn_id()
    timestamp = datetime.now().strftime('%I:%M:%S %p')
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO payments (transaction_id, transaction_date, timestamp, payment_amount,"
                " payment_type, payment_mode, payment_status, paid_by, recieved_by, user_row_num)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (transaction_id, transaction_date, timestamp, payment_amount,
                 payment_type, payment_mode, payment_status, paid_by,
                 recieved_by, user_row_num)
            )
    return transaction_id

def get_payment_by_row_num(row_num):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM payments WHERE row_num=%s', (row_num,))
            return cur.fetchone()

def get_all_payments():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM payments ORDER BY row_num')
            return cur.fetchall()

if __name__ == '__main__':
    print(add_payment('22-Jan-2026', 200, 'Subscription', 'Cash',
                      'Accepted', 'MEM_1', 'EMP_1', 2))
    print(get_payment_by_row_num(2))
    print(get_all_payments())
