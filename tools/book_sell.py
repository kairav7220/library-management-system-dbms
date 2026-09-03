from datetime import datetime

from langchain_core.tools import tool

from tools.db import get_connection


@tool
def book_sell(details: dict) -> dict:
    """Record a book sale to a member.

    details keys: order_date, book_id, book_name, book_price, mem_id.
    order_id, transaction_id and timestamps are auto-generated.

    Runs the sale insert and its matching payment record in one transaction
    so they succeed or fail together.
    """
    conn = get_connection(autocommit=False)
    try:
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
            cur.execute(
                "SELECT MAX(CAST(SUBSTRING(transaction_id, 5) AS UNSIGNED)) AS m"
                " FROM payments WHERE transaction_id LIKE 'TXN\\_%'"
            )
            txn_n = (cur.fetchone()['m'] or 0) + 1
            transaction_id = f'TXN_{txn_n}'
            cur.execute(
                "INSERT INTO payments (transaction_id, transaction_date, timestamp,"
                " payment_amount, payment_type, payment_mode, payment_status,"
                " paid_by, recieved_by) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (transaction_id, details.get("order_date"),
                 datetime.now().strftime("%I:%M:%S %p"),
                 details.get("book_price"), "Book Purchase", "Cash",
                 "Completed", details.get("mem_id"), None)
            )
            cur.execute('SELECT * FROM book_sell WHERE order_id=%s', (order_id,))
            result = cur.fetchone()
        conn.commit()
        return result
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


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
