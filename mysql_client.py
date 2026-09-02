"""
MySQL client for Library Management System (DBMS version).

Replaces the Google Sheets (gspread) data layer with a real MySQL
relational database. Provides a gspread-compatible worksheet shim so
the existing FLASK routes and tools keep working with minimal changes.

Tables are mapped to MySQL as follows (same column order as the
original sheets):

    User Table       -> users
    Book Table       -> books
    Book Category    -> book_category
    Book Genre       -> book_genre
    Member Table     -> members
    Employee Table   -> employees
    Subscription Tab -> subscriptions
    Payment Table    -> payments
    Book Sell        -> book_sell
    Book Issue       -> book_issues
"""

import os

import pymysql
from dotenv import load_dotenv

load_dotenv()

# Table name -> (MySQL table, exact column list in sheet order)
# The first column on every sheet is the auto-increment row_num used
# by the web UI as the "sheet row" identifier.
TABLES = {
    'User Table': (
        'users',
        ['row_num', 'user_id', 'user_type', 'username', 'password',
         'email', 'phone', 'status'],
    ),
    'Book Table': (
        'books',
        ['row_num', 'book_id', 'book_name', 'book_author', 'book_price',
         'book_cat', 'book_genre', 'edition', 'publication', 'status'],
    ),
    'Book Category': (
        'book_category',
        ['row_num', 'cat_id', 'cat_name', 'description', 'book_names', 'status'],
    ),
    'Book Genre': (
        'book_genre',
        ['row_num', 'genre_id', 'genre_title', 'book_names', 'status'],
    ),
    'Member Table': (
        'members',
        ['row_num', 'mem_id', 'name', 'user_id', 'password', 'email',
         'phone', 'user_row_num', 'permanent_address', 'temporary_address',
         'status'],
    ),
    'Employee Table': (
        'employees',
        ['row_num', 'emp_id', 'name', 'user_id', 'password', 'email',
         'phone', 'designation', 'salary', 'user_row_num',
         'permanent_address', 'temporary_address', 'status'],
    ),
    'Subscription Table': (
        'subscriptions',
        ['row_num', 'transaction_id', 'transaction_date', 'timestamp',
         'plan_mode', 'mem_id', 'mem_subscription_amount', 'plan_type',
         'plan_start', 'plan_end', 'subscription_status'],
    ),
    'Payment Table': (
        'payments',
        ['row_num', 'transaction_id', 'transaction_date', 'timestamp',
         'payment_amount', 'payment_type', 'payment_mode', 'payment_status',
         'paid_by', 'recieved_by', 'user_row_num'],
    ),
    'Book Sell': (
        'book_sell',
        ['row_num', 'order_id', 'order_date', 'timestamp', 'book_id',
         'book_name', 'book_price', 'mem_id'],
    ),
    'Book Issue': (
        'book_issues',
        ['row_num', 'transaction_id', 'transaction_date', 'timestamp',
         "book_id", "issued_date", "issued_to", "recieved_by", "returned_date"],
    ),
    'Logs': (
        'logs',
        ['row_num', 'timestamp', 'action'],
    ),
    'Customer Table': (
        'customers',
        ['row_num', 'cust_id', 'name', 'username', 'password'],
    ),
}

# Column index (1-based) of the soft-delete "status" flag, or None
# for tables that have no status column.
STATUS_COL = {
    'User Table': 8,
    'Book Table': 10,
    'Book Category': 6,
    'Book Genre': 5,
    'Member Table': 11,
    'Employee Table': 13,
    "Subscription Table": 11,
    "Payment Table": None,
    "Book Sell": None,
    "Book Issue": None,
}


def get_connection():
    """Return a new MySQL connection from environment variables."""
    return pymysql.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', 'root'),
        database=os.getenv('MYSQL_DB', 'library_db'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


class MySQLWorksheet:
    """Drop-in shim mimicking a single gspread worksheet backed by MySQL."""

    def __init__(self, sheet_name: str):
        if sheet_name not in TABLES:
            raise ValueError(f"Unknown sheet '{sheet_name}'. Valid: {list(TABLES)}")
        self.sheet_name = sheet_name
        self.table, self.columns = TABLES[sheet_name]
        self._col_list = '', ''.join(self.columns)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _fetch_all_rows(self):
        """Return all rows as a list of lists, in sheet column order,
        excluding the MySQL auto-increment row_num only if present."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(f'SELECT * FROM `{self.table}` ORDER BY row_num')
                rows = cur.fetchall()
            # Convert dicts -> ordered lists
            return [
                [r.get(col) for col in self.columns]
                for r in rows
            ]
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # gspread-compatible API
    # ------------------------------------------------------------------
    def get_all_values(self) -> list[list]:
        """Return all rows as a list of lists (with a leading header row)."""
        data = self._fetch_all_rows()
        return [self.columns] + data

    def row_values(self, row: int) -> list:
        """Return the values of a single row (1-based, matching gspread)."""
        rows = self._fetch_all_rows()
        if 1 <= row <= len(rows):
            return rows[row - 1]
        return []

    def get(self, a1_range: str) -> list[list]:
        """Return a rectangular block of values. Supports 'A2:J10' style.
        Only the row range is honored (columns are assumed full table)."""
        n_rows = len(self._fetch_all_rows())
        # parse "A1:J5" -> last row number (strip letters)
        import re
        m = re.search(r':([A-Z]+)(\d+)', a1_range)
        end = int(m.group(2)) if m else n_rows
        start = 1
        # parse start? gspread uses 'A{row}:J{row}' -> single row
        ms = re.match(r'([A-Z]+)(\d+):', a1_range)
        if ms:
            start = int(ms.group(2))
        rows = self._fetch_all_rows()
        return rows[start - 1:end]

    def update(self, values: list[list], a1_range: str = None,
               value_input_option: str = None) -> None:
        """Append a new row (first element of values) or update rows in range."""
        # Determine if we are appending or a range is given
        if values and len(values) >= 1:
            row_data = values[0]
            # Row 0 is always the incrementing id, which we auto-generate;
            # strip any '=ROW()' sentinel
            cleaned = [
                None if (isinstance(v, str) and v.startswith('=')) else v
                for v in row_data
            ]
            self._insert_row(cleaned)

    def _insert_row(self, values: list) -> None:
        """Insert a row. values is the full 1-indexed column data."""
        # Build INSERT. Skip the row_num (auto) column.
        cols = self.columns[1:]  # skip row_num
        vals = values[1:] if len(values) > 1 else []
        # Pad/truncate to match cols
        padded = (vals + [None] * len(cols))[:len(cols)]
        col_names = ', '.join(f'`{c}`' for c in cols)
        ph = ', '.join(['%s'] * len(cols))
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f'INSERT INTO `{self.table}` ({col_names}) VALUES ({ph})',
                    padded,
                )
            conn.commit()
        finally:
            conn.close()

    def update_cell(self, row: int, col: int, value) -> None:
        """Update a single cell by 1-based row and column number."""
        col_name = self.columns[col - 1]
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f'UPDATE `{self.table}` SET `{col_name}`=%s '
                    f'WHERE row_num=%s',
                    (value, row),
                )
            conn.commit()
        finally:
            conn.close()

    def update_acell(self, a1: str, value) -> None:
        """Update a single cell by A1 notation, e.g. 'E2'."""
        import re
        m = re.match(r'([A-Z]+)(\d+)', a1)
        if not m:
            raise ValueError(f'Invalid A1 reference: {a1}')
        col = col_to_num(m.group(1))
        row = int(m.group(2))
        self.update_cell(row, col, value)

    def append_row(self, values: list, value_input_option=None) -> None:
        """Append a new row (used by legacy login.py)."""
        self._insert_row(values)


def col_to_num(col_str: str) -> int:
    """Convert spreadsheet column letters to a number: A=1, Z=26, AA=27."""
    num = 0
    for ch in col_str.upper():
        num = num * 26 + (ord(ch) - ord('A') + 1)
    return num


def rowcol_to_a1(row: int, col: int) -> str:
    """Convert a (row, col) pair to A1 notation, e.g. (2, 5) -> 'E2'.
    Compatible with gspread.utils.rowcol_to_a1."""
    col_str = ""
    while col > 0:
        col, rem = divmod(col - 1, 26)
        col_str = chr(ord('A') + rem) + col_str
    return f"{col_str}{row}"


def num_to_col_letter(*args, **kwargs):
    """gspread helper used by some legacy scripts."""
    raise NotImplementedError("num_to_col_letter not needed")


# --------------------------------------------------------------------
# Public helpers used by tools/*.py (replaces tools/gsheets_client.py)
# --------------------------------------------------------------------
def get_worksheet(sheet_name: str) -> MySQLWorksheet:
    return MySQLWorksheet(sheet_name)


def get_headers(sheet_name: str) -> list[str]:
    return list(TABLES[sheet_name][1])


def get_all_records(sheet_name: str) -> list[dict]:
    """Return non-deleted records as dicts keyed by column name."""
    ws = MySQLWorksheet(sheet_name)
    rows = ws._fetch_all_rows()
    status_col = STATUS_COL.get(sheet_name)
    records = []
    for i, row in enumerate(rows, start=1):
        if status_col is not None:
            # row is a list of values; status_col is 1-based
            idx = status_col - 1
            if idx < len(row) and str(row[idx]) == '1':
                continue
        rec = {name: row[pos] for pos, name in enumerate(TABLES[sheet_name][1])}
        rec['_sheet_row'] = i
        records.append(rec)
    return records


def next_row(sheet_name: str) -> int:
    return len(MySQLWorksheet(sheet_name)._fetch_all_rows()) + 1
