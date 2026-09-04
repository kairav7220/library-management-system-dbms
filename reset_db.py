"""Drop and rebuild the library database from schema.sql.

WARNING: This DELETES all rows and recreates every table with fresh seed
data. Intended as an admin / deploy-time reset only.

Usage:
    python reset_db.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pymysql
from dotenv import load_dotenv

from tools.db import get_connection

load_dotenv()

TABLES = [
    'book_sell',
    'book_issues',
    'payments',
    'subscriptions',
    'members',
    'employees',
    'books',
    'users',
    'book_category',
    'book_genre',
    'logs',
    'customers',
]


def main():
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')
    if not os.path.exists(schema_path):
        print(f'schema.sql not found: {schema_path}')
        sys.exit(1)

    print('Dropping all tables (reverse dependency order)...')
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SET FOREIGN_KEY_CHECKS = 0')
            for table in TABLES:
                try:
                    cur.execute(f'DROP TABLE IF EXISTS `{table}`')
                    print(f'  dropped {table}')
                except Exception as exc:
                    print(f'  !! failed to drop {table}: {exc}')
            cur.execute('SET FOREIGN_KEY_CHECKS = 1')
    finally:
        conn.close()

    print('Re-creating schema and seed data from schema.sql...')
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            statements = []
            current = []
            with open(schema_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('--') or not line.strip():
                        continue
                    current.append(line)
                    if line.rstrip().endswith(';'):
                        statements.append(''.join(current))
                        current = []
            if current:
                statements.append(''.join(current))

            for stmt in statements:
                try:
                    cur.execute(stmt)
                except Exception as exc:
                    print(f'  FAILED statement: {exc}')
                    print(f'  -> {stmt[:200]}...')
    finally:
        conn.close()

    print('Done. Database rebuilt from schema.sql.')


if __name__ == '__main__':
    main()
