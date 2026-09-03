import os

import pymysql
from dotenv import load_dotenv

load_dotenv()


def get_connection(autocommit=True):
    """Open a PyMySQL connection.

    autocommit=False returns a connection whose writes you must explicitly
    commit() or rollback() — used for multi-statement transactions.
    """
    host = os.getenv('MYSQL_HOST', 'localhost')
    ssl = {'ssl': {}} if 'tidbcloud' in host else None
    return pymysql.connect(
        host=host,
        port=int(os.getenv('MYSQL_PORT', '3306')),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', 'root'),
        database=os.getenv('MYSQL_DB', 'library_db'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=autocommit,
        ssl=ssl,
    )
