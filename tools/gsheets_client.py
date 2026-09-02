"""MySQL-backed gsheets_client replacement (DBMS version).

Keeps the same public API as the original Google Sheets client so the
agent tools (tools/*.py) and other callers work unmodified. All data
operations now go through the MySQL relational database.
"""

import sys
import os

# Ensure the repo root is importable (tools/ is a subdirectory).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mysql_client import (  # noqa: E402
    get_worksheet,
    get_headers,
    get_all_records,
    next_row,
    MySQLWorksheet,
)

__all__ = [
    "get_worksheet",
    "get_headers",
    "get_all_records",
    "next_row",
    "MySQLWorksheet",
]
