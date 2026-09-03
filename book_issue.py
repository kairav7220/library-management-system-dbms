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
            cur.execute("SELECT MAX(CAST(SUBSTRING(transaction_id, 5) AS UNSIGNED)) AS m FROM book_issues WHERE transaction_id LIKE 'TXN\\_%'")
            n = (cur.fetchone()['m'] or 0) + 1
    return f'TXN_{n}'

def book_issue(transaction_date, book_id, issued_date, issued_to):
    transaction_id = next_txn_id()
    timestamp = datetime.now().strftime('%d-%m-%Y %I:%M:%S %p')
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO book_issues (transaction_id, transaction_date, timestamp, book_id,"
                " issued_date, issued_to, recieved_by, returned_date)"
                " VALUES (%s,%s,%s,%s,%s,%s,NULL,NULL)",
                (transaction_id, transaction_date, timestamp, book_id,
                 issued_date, issued_to)
            )
    return transaction_id

def book_return(row_num, recieved_by, returned_date):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'UPDATE book_issues SET recieved_by=%s, returned_date=%s WHERE row_num=%s',
                (recieved_by, returned_date, row_num)
            )
    return row_num

def get_issue_return_by_row(row_num):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM book_issues WHERE row_num=%s', (row_num,))
            return cur.fetchone()

def get_all_issues_returns():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM book_issues ORDER BY row_num')
            return cur.fetchall()

if __name__ == '__main__':
    print(book_issue('25-Jan-2026', 'BOOK_1', '25-Jan-2026', 'MEM_1'))
    print(book_return(2, 'EMP_1', '26-Feb-2026'))
    print(get_issue_return_by_row(2))
    print(get_all_issues_returns())
