from datetime import datetime

from langchain_core.tools import tool

from tools.db import get_connection


@tool
def add_subscription(details: dict) -> dict:
    """Add a new subscription plan for a member.

    details keys: plan_mode (online/offline), mem_id, mem_subscription_amount,
    plan_type (Annual/Monthly), plan_start, plan_end.
    transaction_id, dates and timestamp auto-generated.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT MAX(CAST(SUBSTRING(transaction_id, 5) AS UNSIGNED)) AS m FROM subscriptions WHERE transaction_id LIKE 'TXN\\_%'"
            )
            n = (cur.fetchone()['m'] or 0) + 1
            transaction_id = f'TXN_{n}'
            cur.execute(
                "INSERT INTO subscriptions (transaction_id, transaction_date, timestamp, plan_mode,"
                " mem_id, mem_subscription_amount, plan_type, plan_start, plan_end, subscription_status)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (transaction_id, datetime.now().strftime("%d-%b-%Y"),
                 datetime.now().strftime("%I:%M:%S %p"),
                 details.get("plan_mode"), details.get("mem_id"),
                 details.get("mem_subscription_amount"), details.get("plan_type"),
                 details.get("plan_start"), details.get("plan_end"), 0)
            )
            cur.execute('SELECT * FROM subscriptions WHERE transaction_id=%s', (transaction_id,))
            return cur.fetchone()


@tool
def update_subscription(row_num: int, details: dict) -> str:
    """Update an existing subscription by spreadsheet row number.

    details keys (any subset): plan_mode, mem_id, mem_subscription_amount,
    plan_type, plan_start, plan_end, subscription_status.
    """
    col_map = {
        "plan_mode": "plan_mode",
        "mem_id": "mem_id",
        "mem_subscription_amount": "mem_subscription_amount",
        "plan_type": "plan_type",
        "plan_start": "plan_start",
        "plan_end": "plan_end",
        "subscription_status": "subscription_status",
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
                    f"UPDATE subscriptions SET {', '.join(fields)} WHERE row_num=%s",
                    tuple(vals)
                )
    return f"Subscription at row {row_num} updated."


@tool
def get_subscription_by_row_num(row_num: int) -> list:
    """Get a subscription row by spreadsheet row number."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM subscriptions WHERE row_num=%s', (row_num,))
            row = cur.fetchone()
    if row:
        cols = ['row_num', 'transaction_id', 'transaction_date', 'timestamp',
                'plan_mode', 'mem_id', 'mem_subscription_amount', 'plan_type',
                'plan_start', 'plan_end', 'subscription_status']
        return [row[c] for c in cols]
    return []


@tool
def get_all_subscriptions() -> list[dict]:
    """Get all non-deleted subscriptions."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM subscriptions WHERE subscription_status=0 ORDER BY row_num')
            return cur.fetchall()


@tool
def delete_subscription(row_num: int) -> str:
    """Soft-delete a subscription by setting status to 1.

    Call this only AFTER the user has confirmed the deletion.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE subscriptions SET subscription_status=1 WHERE row_num=%s', (row_num,))
    return f"Subscription at row {row_num} deleted."
