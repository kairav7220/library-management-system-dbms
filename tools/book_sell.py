from datetime import datetime

from langchain_core.tools import tool

from tools.db import get_connection


@tool
def book_sell(details: dict) -> dict:
    """Record a book sale to a member.

    details keys: order_date, book_id, book_name, book_price, mem_id.
    order_id and timestamp auto-generated.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT MAX(CAST(SUBSTRING(order_id, 7) AS UNSIGNED)) AS m FROM book_sell WHERE order_id LIKE 'ORDER\\_%'"
            )
            n = (cur.fetchone()['m'] or 0) + 1
            order_id = f'ORDER_{n}'
            cur.execute(
                "INSERT INTO book_sell (order_id, order_date, timestamp, book_id,"
                " book_name, book_price, mem_id)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (order_id, details.get("order_date"),
                 datetime.now().strftime("%d-%b-%Y %I:%M:%S %p"),
                 details.get("book_id"), details.get("book_name"),
                 details.get("book_price"), details.get("mem_id"))
            )
            cur.execute('SELECT * FROM book_sell WHERE order_id=%s', (order_id,))
            return cur.fetchone()


@tool
def update_book_sell(row_num: int, details: dict) -> str:
    """Update an existing book sale by spreadsheet row number.

    details keys (any subset): order_date, book_id, book_name, book_price,
    mem_id.
    """
    col_map = {
        "order_date": "order_date",
        "book_id": "book_id",
        "book_name": "book_name",
        "book_price": "book_price",
        "mem_id": "mem_id",
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
                    f"UPDATE book_sell SET {', '.join(fields)} WHERE row_num=%s",
                    tuple(vals)
                )
    return f"Book sell order at row {row_num} updated."


@tool
def get_all_book_sells() -> list[dict]:
    """Get all book sale records."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM book_sell ORDER BY row_num')
            return cur.fetchall()
