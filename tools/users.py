from langchain_core.tools import tool

from tools.db import get_connection


@tool
def add_user(user_data: list) -> dict:
    """Add a new user to the User Table.

    user_data is a list in order:
    [user_type, username, password, email, phone].
    row_num, user_id and status are auto-generated.
    """
    user_type, username, password, email, phone = user_data
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT MAX(CAST(SUBSTRING(user_id, 6) AS UNSIGNED)) AS m FROM users WHERE user_id LIKE 'USER\\_%'"
            )
            n = (cur.fetchone()['m'] or 0) + 1
            user_id = f'USER_{n}'
            cur.execute(
                "INSERT INTO users (user_id, user_type, username, password, email, phone, status)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (user_id, user_type, username, password, email, phone, 0)
            )
            cur.execute('SELECT * FROM users WHERE user_id=%s', (user_id,))
            return cur.fetchone()


@tool
def get_user_by_id(user_id: str) -> dict | None:
    """Find an active user by their user_id (e.g. USER_1). Returns the user."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM users WHERE user_id=%s AND status=0', (user_id,))
            return cur.fetchone()


@tool
def get_all_users() -> list[dict]:
    """Get all active users from the User Table."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM users WHERE status=0 ORDER BY row_num')
            return cur.fetchall()


@tool
def delete_user(row_num: int) -> str:
    """Soft-delete a user by setting status to 1.

    Call this only AFTER the user has confirmed the deletion.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE users SET status=1 WHERE row_num=%s', (row_num,))
    return f"User at row {row_num} deleted."
