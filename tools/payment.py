from datetime import datetime

from langchain_core.tools import tool

from tools.db import get_connection


@tool
def add_payment(details: dict) -> dict:
    """Add a new payment record.

    details keys: payment_amount, payment_type, payment_mode, payment_status,
    paid_by (member ID), recieved_by (employee ID), user_row_num.
    transaction_id, dates and timestamp auto-generated.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT MAX(CAST(SUBSTRING(transaction_id, 5) AS UNSIGNED)) AS m FROM payments WHERE transaction_id LIKE 'TXN\\_%'"
            )
            n = (cur.fetchone()['m'] or 0) + 1
            transaction_id = f'TXN_{n}'
            cur.execute(
                "INSERT INTO payments (transaction_id, transaction_date, timestamp, payment_amount,"
                " payment_type, payment_mode, payment_status, paid_by, recieved_by, user_row_num)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (transaction_id, datetime.now().strftime("%d-%b-%Y"),
                 datetime.now().strftime("%I:%M:%S %p"),
                 details.get("payment_amount"), details.get("payment_type"),
                 details.get("payment_mode"), details.get("payment_status"),
                 details.get("paid_by"), details.get("recieved_by"),
                 details.get("user_row_num", ""))
            )
            cur.execute('SELECT * FROM payments WHERE transaction_id=%s', (transaction_id,))
            return cur.fetchone()


@tool
def get_payment_by_row_num(row_num: int) -> list:
    """Get a payment row by spreadsheet row number."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM payments WHERE row_num=%s', (row_num,))
            row = cur.fetchone()
    if row:
        cols = ['row_num', 'transaction_id', 'transaction_date', 'timestamp',
                'payment_amount', 'payment_type', 'payment_mode',
                'payment_status', 'paid_by', 'recieved_by', 'user_row_num']
        return [row[c] for c in cols]
    return []


@tool
def get_all_payments() -> list[dict]:
    """Get all payment records."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM payments ORDER BY row_num')
            return cur.fetchall()
