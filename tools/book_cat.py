from langchain_core.tools import tool

from tools.db import get_connection


@tool
def add_category(details: dict) -> dict:
    """Add a new book category.

    details keys: cat_name, description, book_names (comma-separated list).
    ID and status are auto-generated.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT MAX(CAST(SUBSTRING(cat_id, 5) AS UNSIGNED)) AS m FROM book_category WHERE cat_id LIKE 'CAT\\_%'"
            )
            n = (cur.fetchone()['m'] or 0) + 1
            cat_id = f'CAT_{n}'
            cur.execute(
                'INSERT INTO book_category (cat_id, cat_name, description, book_names, status)'
                ' VALUES (%s,%s,%s,%s,%s)',
                (cat_id, details.get('cat_name'), details.get('description'),
                 details.get('book_names'), 0)
            )
            cur.execute('SELECT * FROM book_category WHERE cat_id=%s', (cat_id,))
            return cur.fetchone()


@tool
def update_category(row_num: int, details: dict) -> str:
    """Update an existing category by spreadsheet row number.

    details keys (any subset): cat_name, description, book_names.
    """
    col_map = {
        'cat_name': 'cat_name',
        'description': 'description',
        'book_names': 'book_names',
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
                    f"UPDATE book_category SET {', '.join(fields)} WHERE row_num=%s",
                    tuple(vals)
                )
    return f'Category at row {row_num} updated.'


@tool
def get_category_by_row_num(row_num: int) -> list:
    """Get a category's row by spreadsheet row number."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM book_category WHERE row_num=%s', (row_num,))
            row = cur.fetchone()
    if row:
        cols = ['row_num', 'cat_id', 'cat_name', 'description', 'book_names', 'status']
        return [row[c] for c in cols]
    return []


@tool
def get_all_categories() -> list[dict]:
    """Get all non-deleted book categories."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM book_category WHERE status=0 ORDER BY row_num')
            return cur.fetchall()


@tool
def get_books_by_category(cat_name: str) -> list:
    """Get the list of book names belonging to a category by name."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT book_names FROM book_category WHERE cat_name=%s AND status=0', (cat_name,))
            row = cur.fetchone()
    if row and row['book_names']:
        return row['book_names'].split(', ')
    return []


@tool
def delete_category(row_num: int) -> str:
    """Soft-delete a category by setting status to 1.

    Call this only AFTER the user has confirmed the deletion.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE book_category SET status=1 WHERE row_num=%s', (row_num,))
    return f'Category at row {row_num} deleted.'
