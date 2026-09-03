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

def next_cat_id():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(CAST(SUBSTRING(cat_id, 5) AS UNSIGNED)) AS m FROM book_category WHERE cat_id LIKE 'CAT\\_%'")
            n = (cur.fetchone()['m'] or 0) + 1
    return f'CAT_{n}'

def add_category(cat_name, description, book_names):
    cat_id = next_cat_id()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO book_category (cat_id, cat_name, description, book_names, status)"
                " VALUES (%s,%s,%s,%s,%s)",
                (cat_id, cat_name, description, book_names, 0)
            )
    return cat_id

def update_category(row_num, *, cat_name=None, description=None, book_names=None):
    fields, vals = [], []
    for col, v in (('cat_name', cat_name), ('description', description),
                   ('book_names', book_names)):
        if v is not None:
            fields.append(f'`{col}`=%s')
            vals.append(v)
    if not fields:
        return row_num
    vals.append(row_num)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE book_category SET {', '.join(fields)} WHERE row_num = %s",
                tuple(vals)
            )
    return row_num

def get_category_by_row_num(row_num):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM book_category WHERE row_num=%s', (row_num,))
            return cur.fetchone()

def get_all_categories():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM book_category WHERE status=0 ORDER BY row_num')
            return cur.fetchall()

def get_books_by_category(cat_name):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT book_names FROM book_category WHERE cat_name=%s AND status=0", (cat_name,))
            row = cur.fetchone()
            if row:
                books = row['book_names'].split(', ') if row['book_names'] else []
                print(f'{cat_name}: {books}')
                return books
            else:
                print(f'Category {cat_name} not found')
                return []

def delete_category(row_num):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE book_category SET status=1 WHERE row_num=%s', (row_num,))
    return row_num

if __name__ == '__main__':
    print(add_category('Science Fiction', 'Futuristic and imaginative science-based stories', 'Dune, Neuromancer, Snow Crash'))
    print(get_category_by_row_num(2))
    print(get_all_categories())
    print(get_books_by_category('Science Fiction'))
    print(delete_category(2))
