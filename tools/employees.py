from langchain_core.tools import tool
from werkzeug.security import generate_password_hash

from tools.db import get_connection


@tool
def add_employee(details: dict) -> dict:
    """Add a new employee to the Employee Table.

    details keys: name, user_id, password, email, phone, designation,
    salary, user_row_num, permanent_address, temporary_address.
    emp_id and status auto-generated.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT MAX(CAST(SUBSTRING(emp_id, 5) AS UNSIGNED)) AS m FROM employees WHERE emp_id LIKE 'EMP\\_%'"
            )
            n = (cur.fetchone()['m'] or 0) + 1
            emp_id = f'EMP_{n}'
            raw_password = details.get("password")
            password_hash = generate_password_hash(raw_password) if raw_password else None
            cur.execute(
                "INSERT INTO employees (emp_id, name, user_id, password, email, phone,"
                " designation, salary, user_row_num, permanent_address, temporary_address, status)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (emp_id, details.get("name"), details.get("user_id"),
                 password_hash, details.get("email"),
                 details.get("phone"), details.get("designation"),
                 details.get("salary"), details.get("user_row_num", ""),
                 details.get("permanent_address"),
                 details.get("temporary_address"), 0)
            )
            cur.execute('SELECT * FROM employees WHERE emp_id=%s', (emp_id,))
            return cur.fetchone()


@tool
def update_employee(row_num: int, details: dict) -> str:
    """Update an existing employee by spreadsheet row number.

    details keys (any subset): name, user_id, password, email, phone,
    designation, salary, permanent_address, temporary_address.
    """
    col_map = {
        "name": "name",
        "user_id": "user_id",
        "password": "password",
        "email": "email",
        "phone": "phone",
        "designation": "designation",
        "salary": "salary",
        "permanent_address": "permanent_address",
        "temporary_address": "temporary_address",
    }
    fields, vals = [], []
    for key, col in col_map.items():
        if key in details and details[key] is not None:
            if key == "password":
                if not details[key]:
                    continue
                vals.append(generate_password_hash(details[key]))
            else:
                vals.append(details[key])
            fields.append(f'`{col}`=%s')
    if fields:
        vals.append(row_num)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE employees SET {', '.join(fields)} WHERE row_num=%s",
                    tuple(vals)
                )
    return f"Employee at row {row_num} updated."


@tool
def get_employee_by_row_num(row_num: int) -> list:
    """Get an employee's row by spreadsheet row number."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM employees WHERE row_num=%s', (row_num,))
            row = cur.fetchone()
    if row:
        cols = ['row_num', 'emp_id', 'name', 'user_id', 'password', 'email',
                'phone', 'designation', 'salary', 'user_row_num',
                'permanent_address', 'temporary_address', 'status']
        return [row[c] for c in cols]
    return []


@tool
def get_employee_by_id(emp_id: str) -> dict | None:
    """Find an employee by their emp_id (e.g. EMP_1). Returns the employee."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM employees WHERE emp_id=%s AND status=0', (emp_id,))
            return cur.fetchone()


@tool
def get_all_employees() -> list[dict]:
    """Get all non-deleted employees."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM employees WHERE status=0 ORDER BY row_num')
            return cur.fetchall()


@tool
def delete_employee(row_num: int) -> str:
    """Soft-delete an employee by setting status to 1.

    Call this only AFTER the user has confirmed the deletion.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE employees SET status=1 WHERE row_num=%s', (row_num,))
    return f"Employee at row {row_num} deleted."
