from langchain_core.tools import tool

from tools.db import get_connection


@tool
def add_member(details: dict) -> dict:
    """Add a new member to the Member Table.

    details keys: name, user_id, password, email, phone, user_row_num,
    permanent_address, temporary_address. mem_id and status auto-generated.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT MAX(CAST(SUBSTRING(mem_id, 5) AS UNSIGNED)) AS m FROM members WHERE mem_id LIKE 'MEM\\_%'"
            )
            n = (cur.fetchone()['m'] or 0) + 1
            mem_id = f'MEM_{n}'
            cur.execute(
                'INSERT INTO members (mem_id, name, user_id, password, email, phone,'
                ' user_row_num, permanent_address, temporary_address, status)'
                ' VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (mem_id, details.get('name'), details.get('user_id'),
                 details.get('password'), details.get('email'),
                 details.get('phone'), details.get('user_row_num', ''),
                 details.get('permanent_address'),
                 details.get('temporary_address'), 0)
            )
            cur.execute('SELECT * FROM members WHERE mem_id=%s', (mem_id,))
            return cur.fetchone()


@tool
def update_member(row_num: int, details: dict) -> str:
    """Update an existing member by spreadsheet row number.

    details keys (any subset): name, user_id, password, email, phone,
    permanent_address, temporary_address.
    """
    col_map = {
        'name': 'name',
        'user_id': 'user_id',
        'password': 'password',
        'email': 'email',
        'phone': 'phone',
        'permanent_address': 'permanent_address',
        'temporary_address': 'temporary_address',
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
                    f"UPDATE members SET {', '.join(fields)} WHERE row_num=%s",
                    tuple(vals)
                )
    return f'Member at row {row_num} updated.'


@tool
def get_member_by_row_num(row_num: int) -> list:
    """Get a member's row by spreadsheet row number."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM members WHERE row_num=%s', (row_num,))
            row = cur.fetchone()
    if row:
        cols = ['row_num', 'mem_id', 'name', 'user_id', 'password', 'email',
                'phone', 'user_row_num', 'permanent_address',
                'temporary_address', 'status']
        return [row[c] for c in cols]
    return []


@tool
def get_member_by_id(mem_id: str) -> dict | None:
    """Find a member by their mem_id (e.g. MEM_1). Returns the member."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM members WHERE mem_id=%s AND status=0', (mem_id,))
            return cur.fetchone()


@tool
def get_all_members() -> list[dict]:
    """Get all non-deleted members."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM members WHERE status=0 ORDER BY row_num')
            return cur.fetchall()


@tool
def delete_member(row_num: int) -> str:
    """Soft-delete a member by setting status to 1.

    Call this only AFTER the user has confirmed the deletion.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE members SET status=1 WHERE row_num=%s', (row_num,))
    return f"Member at row {row_num} deleted."
