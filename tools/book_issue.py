from datetime import datetime

from langchain_core.tools import tool

from tools.db import get_connection


@tool
def book_issue(details: dict) -> dict:
    """Issue a book to a member.

    details keys: book_id, mem_id (the member ID), issued_date,
    transaction_date (optional, defaults to today), recieved_by (optional,
    employee ID).
    transaction_id and timestamp are auto-generated.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT MAX(CAST(SUBSTRING(transaction_id, 5) AS UNSIGNED)) AS m FROM book_issues WHERE transaction_id LIKE 'TXN\\_%'"
            )
            n = (cur.fetchone()['m'] or 0) + 1
            transaction_id = f'TXN_{n}'
            cur.execute(
                "INSERT INTO book_issues (transaction_id, transaction_date, timestamp, book_id,"
                " issued_date, issued_to, recieved_by, returned_date)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (transaction_id,
                 details.get("transaction_date") or datetime.now().strftime("%d-%b-%Y"),
                 datetime.now().strftime("%d-%b-%Y %I:%M:%S %p"),
                 details.get("book_id"), details.get("issued_date"),
                 details.get("mem_id"), details.get("recieved_by", ""),
                 details.get("returned_date", ""))
            )
            cur.execute('SELECT * FROM book_issues WHERE transaction_id=%s', (transaction_id,))
            return cur.fetchone()


@tool
def book_return(row_num: int, details: dict) -> str:
    """Process a book return.

    details keys: recieved_by (employee ID), returned_date.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'UPDATE book_issues SET recieved_by=%s, returned_date=%s WHERE row_num=%s',
                (details.get("recieved_by"), details.get("returned_date"), row_num)
            )
    return f"Book issue at row {row_num} marked as returned."


@tool
def get_issue_by_row_num(row_num: int) -> list:
    """Get a book issue/return row by spreadsheet row number."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM book_issues WHERE row_num=%s', (row_num,))
            row = cur.fetchone()
    if row:
        cols = ['row_num', 'transaction_id', 'transaction_date', 'timestamp',
                'book_id', 'issued_date', 'issued_to', 'recieved_by',
                'returned_date']
        return [row[c] for c in cols]
    return []


@tool
def get_all_issues() -> list[dict]:
    """Get all book issue records."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM book_issues ORDER BY row_num')
            return cur.fetchall()
