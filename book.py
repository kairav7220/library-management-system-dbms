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

def next_book_id():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(CAST(SUBSTRING(book_id, 6) AS UNSIGNED)) AS m FROM books WHERE book_id LIKE 'BOOK\\_%'")
            n = (cur.fetchone()['m'] or 0) + 1
    return f'BOOK_{n}'

def add_book(book_name, book_author, book_price, book_cat, book_genre, edition, publication):
    book_id = next_book_id()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO books (book_id, book_name, book_author, book_price,"
                " book_cat, book_genre, edition, publication, status)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (book_id, book_name, book_author, book_price, book_cat,
                 book_genre, edition, publication, 0)
            )
    return book_id

def update_book(row_num, *, book_name=None, book_author=None, book_price=None,
                book_cat=None, book_genre=None, edition=None, publication=None):
    fields, vals = [], []
    for col, v in (('book_name', book_name), ('book_author', book_author),
                   ('book_price', book_price), ('book_cat', book_cat),
                   ('book_genre', book_genre), ('edition', edition),
                   ('publication', publication)):
        if v is not None:
            fields.append(f'`{col}`=%s')
            vals.append(v)
    if not fields:
        return row_num
    vals.append(row_num)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE books SET {', '.join(fields)} WHERE row_num = %s",
                tuple(vals)
            )
    return row_num

def get_book_by_row_num(row_num):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM books WHERE row_num=%s', (row_num,))
            return cur.fetchone()

def get_all_books():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM books WHERE status=0 ORDER BY row_num')
            return cur.fetchall()

def delete_book(row_num):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE books SET status=1 WHERE row_num=%s', (row_num,))
    return row_num

if __name__ == '__main__':
    print(add_book('Dune', 'Frank Herbert', 19.99, 'Science Fiction', 
    'Science Fiction', 1, 1965))
    print(get_book_by_row_num(2))
    print(get_all_books())
    print(delete_book(2))