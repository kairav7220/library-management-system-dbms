from langchain_core.tools import tool

from tools.db import get_connection


@tool
def add_book_genre(details: dict) -> dict:
    """Add a new book genre.

    details keys: genre_title, book_names (comma-separated list).
    ID and status are auto-generated.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT MAX(CAST(SUBSTRING(genre_id, 7) AS UNSIGNED)) AS m FROM book_genre WHERE genre_id LIKE 'GENRE\\_%'"
            )
            n = (cur.fetchone()['m'] or 0) + 1
            genre_id = f'GENRE_{n}'
            cur.execute(
                "INSERT INTO book_genre (genre_id, genre_title, book_names, status)"
                " VALUES (%s,%s,%s,%s)",
                (genre_id, details.get("genre_title"), details.get("book_names"), 0)
            )
            cur.execute('SELECT * FROM book_genre WHERE genre_id=%s', (genre_id,))
            return cur.fetchone()


@tool
def update_book_genre(row_num: int, details: dict) -> str:
    """Update an existing genre by spreadsheet row number.

    details keys (any subset): genre_title, book_names.
    """
    col_map = {
        "genre_title": "genre_title",
        "book_names": "book_names",
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
                    f"UPDATE book_genre SET {', '.join(fields)} WHERE row_num=%s",
                    tuple(vals)
                )
    return f"Genre at row {row_num} updated."


@tool
def get_book_genre_by_row_num(row_num: int) -> list:
    """Get a genre's row by spreadsheet row number."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM book_genre WHERE row_num=%s', (row_num,))
            row = cur.fetchone()
    if row:
        cols = ['row_num', 'genre_id', 'genre_title', 'book_names', 'status']
        return [row[c] for c in cols]
    return []


@tool
def get_all_book_genres() -> list[dict]:
    """Get all non-deleted book genres."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM book_genre WHERE status=0 ORDER BY row_num')
            return cur.fetchall()


@tool
def delete_book_genre(row_num: int) -> str:
    """Soft-delete a genre by setting status to 1.

    Call this only AFTER the user has confirmed the deletion.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE book_genre SET status=1 WHERE row_num=%s', (row_num,))
    return f"Genre at row {row_num} deleted."
