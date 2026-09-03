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

def next_genre_id():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(CAST(SUBSTRING(genre_id, 7) AS UNSIGNED)) AS m FROM book_genre WHERE genre_id LIKE 'GENRE\\_%'")
            n = (cur.fetchone()['m'] or 0) + 1
    return f'GENRE_{n}'

def add_genre(genre_title, book_names):
    genre_id = next_genre_id()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO book_genre (genre_id, genre_title, book_names, status)"
                " VALUES (%s,%s,%s,%s)",
                (genre_id, genre_title, book_names, 0)
            )
    return genre_id

def update_genre(row_num, *, genre_title=None, book_names=None):
    fields, vals = [], []
    for col, v in (('genre_title', genre_title), ('book_names', book_names)):
        if v is not None:
            fields.append(f'`{col}`=%s')
            vals.append(v)
    if not fields:
        return row_num
    vals.append(row_num)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE book_genre SET {', '.join(fields)} WHERE row_num = %s",
                tuple(vals)
            )
    return row_num

def get_genre_by_row_num(row_num):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM book_genre WHERE row_num=%s', (row_num,))
            return cur.fetchone()

def get_all_genres():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM book_genre WHERE status=0 ORDER BY row_num')
            return cur.fetchall()

def delete_genre(row_num):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE book_genre SET status=1 WHERE row_num=%s', (row_num,))
    return row_num

if __name__ == '__main__':
    print(add_genre('Science Fiction', 'Dune, Neuromancer, Foundation'))
    print(get_genre_by_row_num(2))
    print(get_all_genres())
    print(delete_genre(2))
