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

def next_order_id():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(CAST(SUBSTRING(order_id, 7) AS UNSIGNED)) AS m FROM book_sell WHERE order_id LIKE 'ORDER\\_%'")
            n = (cur.fetchone()['m'] or 0) + 1
    return f'ORDER_{n}'

def book_order(order_date, book_id, book_name, book_price, mem_id):
    order_id = next_order_id()
    timestamp = datetime.now().strftime('%d-%m-%Y %I:%M:%S %p')
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO book_sell (order_id, order_date, timestamp, book_id, book_name, book_price, mem_id)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (order_id, order_date, timestamp, book_id, book_name, book_price, mem_id)
            )
    return order_id

def update_order(row_num, *, order_date=None, timestamp=None, book_id=None,
                 book_name=None, book_price=None, mem_id=None):
    fields, vals = [], []
    for col, v in (('order_date', order_date), ('timestamp', timestamp),
                   ('book_id', book_id), ('book_name', book_name),
                   ('book_price', book_price), ('mem_id', mem_id)):
        if v is not None:
            fields.append(f'`{col}`=%s')
            vals.append(v)
    if not fields:
        return row_num
    vals.append(row_num)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE book_sell SET {', '.join(fields)} WHERE row_num = %s",
                tuple(vals)
            )
    return row_num

def get_order_by_row_num(row_num):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM book_sell WHERE row_num=%s', (row_num,))
            return cur.fetchone()

def get_all_orders():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM book_sell ORDER BY row_num')
            return cur.fetchall()

if __name__ == '__main__':
    print(book_order('25-Jan-2026', 'BOOK_1', 'Duke', 200, 'MEM_1'))
    print(get_order_by_row_num(2))
    print(get_all_orders())
