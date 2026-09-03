from langchain_core.tools import tool

from tools.db import get_connection


def _reindex_after():
    """Rebuild the semantic book index (pgvector) after a write.
    Best-effort: never fails the underlying write if indexing hiccups."""
    try:
        from rag.embedder import index_all

        index_all()
    except Exception as e:
        print(f"[tools/book.py] reindex failed: {e}")


@tool
def add_book(details: dict) -> dict:
    """Add a new book to the Book Table.

    details keys: book_name, book_author, book_price, book_cat,
    book_genre, edition, publication. IDs and status are auto-generated.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT MAX(CAST(SUBSTRING(book_id, 6) AS UNSIGNED)) AS m FROM books WHERE book_id LIKE 'BOOK\\_%'"
            )
            n = (cur.fetchone()['m'] or 0) + 1
            book_id = f'BOOK_{n}'
            cur.execute(
                'INSERT INTO books (book_id, book_name, book_author, book_price,'
                ' book_cat, book_genre, edition, publication, status)'
                ' VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (book_id, details.get('book_name'), details.get('book_author'),
                 details.get('book_price'), details.get('book_cat'),
                 details.get('book_genre'), details.get('edition'),
                 details.get('publication'), 0)
            )
            cur.execute('SELECT * FROM books WHERE book_id=%s', (book_id,))
            row = cur.fetchone()
    _reindex_after()
    return row


@tool
def update_book(row_num: int, details: dict) -> str:
    """Update an existing book by its spreadsheet row number.

    details keys (any subset): book_name, book_author, book_price, book_cat,
    book_genre, edition, publication.
    """
    col_map = {
        'book_name': 'book_name',
        'book_author': 'book_author',
        'book_price': 'book_price',
        'book_cat': 'book_cat',
        'book_genre': 'book_genre',
        'edition': 'edition',
        'publication': 'publication',
    }
    fields, vals = [], []
    for key, col in col_map.items():
        if key in details and details[key] is not None:
            fields.append(f'`{col}`=%s')
            vals.append(details[key])
    if fields:
        vals.append(row_num)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE books SET {', '.join(fields)} WHERE row_num=%s",
                    tuple(vals)
                )
    _reindex_after()
    return f'Book at row {row_num} updated.'


@tool
def get_book_by_row_num(row_num: int) -> list:
    """Get a book's row by its spreadsheet row number."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM books WHERE row_num=%s', (row_num,))
            row = cur.fetchone()
    if row:
        cols = ['row_num', 'book_id', 'book_name', 'book_author', 'book_price',
                'book_cat', 'book_genre', 'edition', 'publication', 'status']
        return [row[c] for c in cols]
    return []


@tool
def get_all_books() -> list[dict]:
    """Get all non-deleted books from the Book Table."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM books WHERE status=0 ORDER BY row_num')
            return cur.fetchall()


@tool
def delete_book(row_num: int) -> str:
    """Soft-delete a book by setting its status to 1 (hides from catalog).

    Call this only AFTER the user has confirmed the deletion.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE books SET status=1 WHERE row_num=%s', (row_num,))
    _reindex_after()
    return f'Book at row {row_num} deleted.'