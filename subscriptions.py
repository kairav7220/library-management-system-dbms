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
            cur.execute("SELECT MAX(CAST(SUBSTRING(transaction_id, 5) AS UNSIGNED)) AS m FROM subscriptions WHERE transaction_id LIKE 'TXN\\_%'")
            n = (cur.fetchone()['m'] or 0) + 1
    return f'TXN_{n}'

def add_plan(transaction_date, plan_mode, mem_id, mem_subscription_amount,
             plan_type, plan_start, plan_end):
    transaction_id = next_txn_id()
    timestamp = datetime.now().strftime('%I:%M:%S %p')
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO subscriptions (transaction_id, transaction_date, timestamp, plan_mode,"
                " mem_id, mem_subscription_amount, plan_type, plan_start, plan_end, subscription_status)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (transaction_id, transaction_date, timestamp, plan_mode,
                 mem_id, mem_subscription_amount, plan_type, plan_start,
                 plan_end, 0)
            )
    return transaction_id

def update_plan(row_num, *, transaction_date=None, timestamp=None, plan_mode=None,
                mem_id=None, mem_subscription_amount=None, plan_type=None,
                plan_start=None, plan_end=None):
    fields, vals = [], []
    for col, v in (('transaction_date', transaction_date), ('timestamp', timestamp),
                   ('plan_mode', plan_mode), ('mem_id', mem_id),
                   ('mem_subscription_amount', mem_subscription_amount),
                   ('plan_type', plan_type), ('plan_start', plan_start),
                   ('plan_end', plan_end)):
        if v is not None:
            fields.append(f'`{col}`=%s')
            vals.append(v)
    if not fields:
        return row_num
    vals.append(row_num)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE subscriptions SET {', '.join(fields)} WHERE row_num = %s",
                tuple(vals)
            )
    return row_num

def get_subscription_by_row_num(row_num):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM subscriptions WHERE row_num=%s', (row_num,))
            return cur.fetchone()

def get_all_subscriptions():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM subscriptions WHERE subscription_status=0 ORDER BY row_num')
            return cur.fetchall()

def delete_subscription(row_num):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE subscriptions SET subscription_status=1 WHERE row_num=%s', (row_num,))
    return row_num

if __name__ == '__main__':
    print(add_plan('22-Jan-2026', 'online', 'MEM_1', 200, 'Annual',
                   '22-Jan-2026', '21-Jan-2027'))
    print(get_subscription_by_row_num(2))
    print(get_all_subscriptions())
    print(delete_subscription(2))
