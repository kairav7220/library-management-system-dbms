from flask import Flask, jsonify, render_template, request, redirect, url_for, Response, session, flash, abort
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
import json
from datetime import datetime
from dotenv import load_dotenv
import os

from functools import wraps

import pymysql

from tools.db import get_connection


EMAIL_RE = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'


def _error_message(exc):
    if isinstance(exc, pymysql.err.IntegrityError):
        err = str(exc).lower()
        if 'duplicate' in err:
            return 'That value already exists.'
        if 'cannot be null' in err or 'not null' in err:
            return 'A required field is missing.'
        return 'That would conflict with existing data.'
    return f'Something went wrong: {exc}'


def _check_email(field_name, value):
    return '' if _is_email(value) else f'{field_name} must be a valid email address.'


def _check_money(field_name, value):
    if value is None or str(value).strip() == '':
        return ''
    try:
        num = float(value)
    except (TypeError, ValueError):
        return f'{field_name} must be a number.'
    if num < 0:
        return f'{field_name} cannot be negative.'
    return ''


def _require(field_name, value):
    if value is None or str(value).strip() == '':
        return f'{field_name} is required.'
    return ''


def _is_email(value):
    import re
    if not value:
        return True
    return re.match(EMAIL_RE, str(value).strip()) is not None


def _first_error(errors):
    for msg in errors:
        if msg:
            return msg
    return None


def _id_list(table, id_col, label_col):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f'SELECT `{id_col}`, `{label_col}` FROM `{table}` ORDER BY `{id_col}`')
            rows = cur.fetchall()
    return [{'id': r[id_col], 'label': f'{r[id_col]} — {r[label_col]}'} for r in rows]


def _book_list():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT book_id, book_name, book_price FROM books ORDER BY book_id')
            rows = cur.fetchall()
    return [{'id': r['book_id'], 'label': f'{r["book_id"]} — {r["book_name"]}',
             'name': r['book_name'], 'price': str(r['book_price'] or '')} for r in rows]


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
csrf = CSRFProtect(app)


# Column order (matches the original sheet layout / templates).
USER_COLS = ['row_num', 'user_id', 'user_type', 'username', 'password', 'email', 'phone', 'status']
BOOK_COLS = ['row_num', 'book_id', 'book_name', 'book_author', 'book_price', 'book_cat', 'book_genre',
             'edition', 'publication', 'status']
CAT_COLS = ['row_num', 'cat_id', 'cat_name', 'description', 'book_names', 'status']
GENRE_COLS = ['row_num', 'genre_id', 'genre_title', 'book_names', 'status']
MEMBER_COLS = ['row_num', 'mem_id', 'name', 'user_id', 'password', 'email', 'phone', 'user_row_num',
               'permanent_address', 'temporary_address', 'status']
EMPLOYEE_COLS = ['row_num', 'emp_id', 'name', 'user_id', 'password', 'email', 'phone', 'designation',
                 'salary', 'user_row_num', 'permanent_address', 'temporary_address', 'status']
SUBSCRIPTION_COLS = ['row_num', 'transaction_id', 'transaction_date', 'timestamp', 'plan_mode', 'mem_id',
                     'mem_subscription_amount', 'plan_type', 'plan_start', 'plan_end', 'subscription_status']
PAYMENT_COLS = ['row_num', 'transaction_id', 'transaction_date', 'timestamp', 'payment_amount', 'payment_type',
                'payment_mode', 'payment_status', 'paid_by', 'recieved_by', 'user_row_num']
SELL_COLS = ['row_num', 'order_id', 'order_date', 'timestamp', 'book_id', 'book_name', 'book_price', 'mem_id']
ISSUE_COLS = ['row_num', 'transaction_id', 'transaction_date', 'timestamp', 'book_id', 'issued_date',
              'issued_to', 'recieved_by', 'returned_date']
LOG_COLS = ['row_num', 'timestamp', 'action']


def _to_list(row: dict, cols: list) -> list:
    return [row.get(c) for c in cols]


def _next_id(table: str, id_col: str, prefix: str) -> str:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT MAX(CAST(SUBSTRING(`{id_col}`, %s) AS UNSIGNED)) AS m "
                f"FROM `{table}` WHERE `{id_col}` LIKE CONCAT(%s, '\\_%%')",
                (len(prefix) + 2, prefix),
            )
            n = (cur.fetchone()['m'] or 0) + 1
    return f'{prefix}_{n}'


def _next_txn(table: str) -> str:
    return _next_id(table, 'transaction_id', 'TXN')


def _log_action(action: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO logs (timestamp, action) VALUES (%s, %s)',
                (datetime.now().strftime('%d-%b-%Y %I:%M:%S %p'), action),
            )


def _name_map(table: str, id_col: str, name_col: str) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f'SELECT `{id_col}`, `{name_col}` FROM `{table}`')
            return {row[id_col]: row[name_col] for row in cur.fetchall() if row[id_col]}


def _fetch(table: str, cols: list, status_col: str = None) -> tuple:
    """Return (headers, rows) where rows is [{data: [...], sheet_row: id}]."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f'SELECT * FROM `{table}` ORDER BY row_num')
            rows = cur.fetchall()
    headers = cols
    out = []
    for r in rows:
        if status_col is not None and str(r.get(status_col)) == '1':
            continue
        out.append({'data': _to_list(r, cols), 'sheet_row': r['row_num']})
    return headers, out


# ─── Auth ───────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        if session.get('user_type') != 'Admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated

@app.context_processor
def inject_current_user():
    return {'current_user': session.get('username'), 'current_user_type': session.get('user_type')}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT * FROM users WHERE username=%s',
                    (username,),
                )
                user = cur.fetchone()
        if user and check_password_hash(user['password'], password):
            session['username'] = user['username']
            session['user_type'] = user.get('user_type') or ''
            session['user_id'] = user.get('user_id') or ''
            _log_action(f'{username} logged in')
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('index'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    username = session.get('username')
    if username:
        _log_action(f'{username} logged out')
        session.clear()
        flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/logs')
@admin_required
def logs():
    headers, rows = _fetch('logs', LOG_COLS)
    return render_template('logs.html', headers=headers, rows=rows)

@app.before_request
def require_login():
    if request.endpoint in ('static', 'login'):
        return
    if 'username' not in session:
        flash('Please log in to continue.', 'warning')
        return redirect(url_for('login'))

# ─── Users ───────────────────────────────────────────────

@app.route('/')
@app.route('/users')
def index():
    headers, rows = _fetch('users', USER_COLS, status_col='status')
    return render_template('index.html', headers=headers, rows=rows)

@app.route('/list')
def get_all_users():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM users ORDER BY row_num')
            rows = cur.fetchall()
    sheet_data = [USER_COLS] + [_to_list(r, USER_COLS) for r in rows]
    return jsonify({'sheet_data': sheet_data})

@app.route('/users/add', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        user_type = request.form.get('user_type')
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        phone = request.form.get('phone')
        err = _first_error([
            _require('User type', user_type),
            _require('Username', username),
            _require('Password', password),
            _check_email('Email', email),
        ])
        if err:
            flash(f'Could not add user: {err}', 'error')
            return render_template('add_user.html')
        try:
            user_id = _next_id('users', 'user_id', 'USER')
            password_hash = generate_password_hash(password)
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        'INSERT INTO users (user_id, user_type, username, password, email, phone, status)'
                        ' VALUES (%s,%s,%s,%s,%s,%s,0)',
                        (user_id, user_type, username, password_hash, email, phone),
                    )
            flash('User added.', 'success')
            return redirect(url_for('index'))
        except Exception as exc:
            flash(f'Could not add user: {_error_message(exc)}', 'error')
    return render_template('add_user.html')

@app.route('/users/edit/<int:row_num>', methods=['GET', 'POST'])
def update_user(row_num):
    if request.method == 'POST':
        password = request.form.get('password')
        phone = request.form.get('phone')
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    if password:
                        cur.execute(
                            'UPDATE users SET password=%s, phone=%s WHERE row_num=%s',
                            (generate_password_hash(password), phone, row_num),
                        )
                    else:
                        cur.execute(
                            'UPDATE users SET phone=%s WHERE row_num=%s',
                            (phone, row_num),
                        )
            flash('User updated.', 'success')
            return redirect(url_for('index'))
        except Exception as exc:
            flash(f'Could not update user: {_error_message(exc)}', 'error')

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM users WHERE row_num=%s', (row_num,))
            row = cur.fetchone()
    user_row = _to_list(row, USER_COLS) if row else []
    return render_template('form.html', user=user_row, row_num=row_num)

@app.route('/users/delete/<int:row_num>', methods=['POST'])
def delete_user(row_num):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('UPDATE users SET status=1 WHERE row_num=%s', (row_num,))
        flash('User deleted.', 'success')
    except Exception as exc:
        flash(f'Could not delete user: {_error_message(exc)}', 'error')
    return redirect(url_for('index'))

# ─── Books ───────────────────────────────────────────────

@app.route('/books')
def books():
    headers, rows = _fetch('books', BOOK_COLS, status_col='status')
    return render_template('books.html', headers=headers, rows=rows)

@app.route('/books/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        book_name = request.form.get('book_name')
        book_author = request.form.get('book_author')
        book_price = request.form.get('book_price')
        book_cat = request.form.get('book_cat')
        book_genre = request.form.get('book_genre')
        edition = request.form.get('edition')
        publication = request.form.get('publication')
        book_id = _next_id('books', 'book_id', 'BOOK')
        err = _first_error([
            _require('Book name', book_name),
            _require('Book author', book_author),
            _check_money('Price', book_price),
        ])
        if err:
            flash(f'Could not add book: {err}', 'error')
            return render_template('add_book.html')
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        'INSERT INTO books (book_id, book_name, book_author, book_price, book_cat,'
                        ' book_genre, edition, publication, status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,0)',
                        (book_id, book_name, book_author, book_price, book_cat, book_genre, edition, publication),
                    )
            flash('Book added.', 'success')
            return redirect(url_for('books'))
        except Exception as exc:
            flash(f'Could not add book: {_error_message(exc)}', 'error')
    return render_template('add_book.html')

@app.route('/books/edit/<int:row_num>', methods=['GET', 'POST'])
def edit_book(row_num):
    if request.method == 'POST':
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        'UPDATE books SET book_name=%s, book_author=%s, book_price=%s, book_cat=%s,'
                        ' book_genre=%s, edition=%s, publication=%s WHERE row_num=%s',
                        (request.form.get('book_name'), request.form.get('book_author'),
                         request.form.get('book_price'), request.form.get('book_cat'),
                         request.form.get('book_genre'), request.form.get('edition'),
                         request.form.get('publication'), row_num),
                    )
            flash('Book updated.', 'success')
            return redirect(url_for('books'))
        except Exception as exc:
            flash(f'Could not update book: {_error_message(exc)}', 'error')

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM books WHERE row_num=%s', (row_num,))
            row = cur.fetchone()
    book_row = _to_list(row, BOOK_COLS) if row else []
    return render_template('edit_book.html', book=book_row, row_num=row_num)

@app.route('/books/delete/<int:row_num>', methods=['POST'])
def delete_book(row_num):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('UPDATE books SET status=1 WHERE row_num=%s', (row_num,))
        flash('Book deleted.', 'success')
    except Exception as exc:
        flash(f'Could not delete book: {_error_message(exc)}', 'error')
    return redirect(url_for('books'))

# ─── Book Category ───────────────────────────────────────────────

@app.route('/book_cat')
def book_category():
    headers, rows = _fetch('book_category', CAT_COLS, status_col='status')
    return render_template('book_category.html', headers=headers, rows=rows)

@app.route('/book_cat/add', methods=['GET', 'POST'])
def add_book_category():
    if request.method == 'POST':
        cat_name = request.form.get('cat_name')
        description = request.form.get('description')
        book_names = request.form.get('book_names')
        cat_id = _next_id('book_category', 'cat_id', 'CAT')
        err = _first_error([_require('Category name', cat_name)])
        if err:
            flash(f'Could not add category: {err}', 'error')
            return render_template('add_book_category.html')
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        'INSERT INTO book_category (cat_id, cat_name, description, book_names, status)'
                        ' VALUES (%s,%s,%s,%s,0)',
                        (cat_id, cat_name, description, book_names),
                    )
            flash('Category added.', 'success')
            return redirect(url_for('book_category'))
        except Exception as exc:
            flash(f'Could not add category: {_error_message(exc)}', 'error')
    return render_template('add_book_category.html')

@app.route('/book_cat/edit/<int:row_num>', methods=['GET', 'POST'])
def edit_book_category(row_num):
    if request.method == 'POST':
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        'UPDATE book_category SET cat_name=%s, description=%s, book_names=%s WHERE row_num=%s',
                        (request.form.get('cat_name'), request.form.get('description'),
                         request.form.get('book_names'), row_num),
                    )
            flash('Category updated.', 'success')
            return redirect(url_for('book_category'))
        except Exception as exc:
            flash(f'Could not update category: {_error_message(exc)}', 'error')

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM book_category WHERE row_num=%s', (row_num,))
            row = cur.fetchone()
    book_cat_row = _to_list(row, CAT_COLS) if row else []
    return render_template('edit_book_category.html', book_cat=book_cat_row, row_num=row_num)

@app.route('/book_cat/delete/<int:row_num>', methods=['POST'])
def delete_book_category(row_num):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('UPDATE book_category SET status=1 WHERE row_num=%s', (row_num,))
        flash('Category deleted.', 'success')
    except Exception as exc:
        flash(f'Could not delete category: {_error_message(exc)}', 'error')
    return redirect(url_for('book_category'))

# ─── Book Genre ───────────────────────────────────────────────

@app.route('/book_genre')
def book_genre():
    headers, rows = _fetch('book_genre', GENRE_COLS, status_col='status')
    return render_template('book_genre.html', headers=headers, rows=rows)

@app.route('/book_genre/add', methods=['GET', 'POST'])
def add_book_genre():
    if request.method == 'POST':
        genre_title = request.form.get('genre_title')
        book_names = request.form.get('book_names')
        genre_id = _next_id('book_genre', 'genre_id', 'GENRE')
        err = _first_error([_require('Genre title', genre_title)])
        if err:
            flash(f'Could not add genre: {err}', 'error')
            return render_template('add_book_genre.html')
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        'INSERT INTO book_genre (genre_id, genre_title, book_names, status)'
                        ' VALUES (%s,%s,%s,0)',
                        (genre_id, genre_title, book_names),
                    )
            flash('Genre added.', 'success')
            return redirect(url_for('book_genre'))
        except Exception as exc:
            flash(f'Could not add genre: {_error_message(exc)}', 'error')
    return render_template('add_book_genre.html')

@app.route('/book_genre/edit/<int:row_num>', methods=['GET', 'POST'])
def edit_book_genre(row_num):
    if request.method == 'POST':
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        'UPDATE book_genre SET genre_title=%s, book_names=%s WHERE row_num=%s',
                        (request.form.get('genre_title'), request.form.get('book_names'), row_num),
                    )
            flash('Genre updated.', 'success')
            return redirect(url_for('book_genre'))
        except Exception as exc:
            flash(f'Could not update genre: {_error_message(exc)}', 'error')

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM book_genre WHERE row_num=%s', (row_num,))
            row = cur.fetchone()
    genre_row = _to_list(row, GENRE_COLS) if row else []
    return render_template('edit_book_genre.html', genre=genre_row, row_num=row_num)

@app.route('/book_genre/delete/<int:row_num>', methods=['POST'])
def delete_book_genre(row_num):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('UPDATE book_genre SET status=1 WHERE row_num=%s', (row_num,))
        flash('Genre deleted.', 'success')
    except Exception as exc:
        flash(f'Could not delete genre: {_error_message(exc)}', 'error')
    return redirect(url_for('book_genre'))

# ─── Members ───────────────────────────────────────────────

@app.route('/members')
def members():
    headers, rows = _fetch('members', MEMBER_COLS, status_col='status')
    return render_template('members.html', headers=headers, rows=rows)

@app.route('/members/add', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        email = request.form.get('email')
        phone = request.form.get('phone')
        permanent_address = request.form.get('permanent_address')
        temporary_address = request.form.get('temporary_address')
        mem_id = _next_id('members', 'mem_id', 'MEM')
        err = _first_error([
            _require('Name', name),
            _check_email('Email', email),
        ])
        if err:
            flash(f'Could not add member: {err}', 'error')
            return render_template('add_member.html')
        try:
            password_hash = generate_password_hash(password) if password else None
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        'INSERT INTO members (mem_id, name, user_id, password, email, phone, user_row_num,'
                        ' permanent_address, temporary_address, status) VALUES (%s,%s,NULL,%s,%s,%s,%s,%s,%s,0)',
                        (mem_id, name, password_hash, email, phone, '', permanent_address, temporary_address),
                    )
            flash('Member added.', 'success')
            return redirect(url_for('members'))
        except Exception as exc:
            flash(f'Could not add member: {_error_message(exc)}', 'error')
    return render_template('add_member.html')

@app.route('/members/edit/<int:row_num>', methods=['GET', 'POST'])
def edit_member(row_num):
    if request.method == 'POST':
        try:
            password = request.form.get('password')
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            permanent_address = request.form.get('permanent_address')
            temporary_address = request.form.get('temporary_address')
            with get_connection() as conn:
                with conn.cursor() as cur:
                    if password:
                        cur.execute(
                            'UPDATE members SET name=%s, password=%s, email=%s, phone=%s,'
                            ' permanent_address=%s, temporary_address=%s WHERE row_num=%s',
                            (name, generate_password_hash(password),
                             email, phone,
                             permanent_address, temporary_address, row_num),
                        )
                    else:
                        cur.execute(
                            'UPDATE members SET name=%s, email=%s, phone=%s,'
                            ' permanent_address=%s, temporary_address=%s WHERE row_num=%s',
                            (name, email, phone,
                             permanent_address, temporary_address, row_num),
                        )
            flash('Member updated.', 'success')
            return redirect(url_for('members'))
        except Exception as exc:
            flash(f'Could not update member: {_error_message(exc)}', 'error')

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM members WHERE row_num=%s', (row_num,))
            row = cur.fetchone()
    member_row = _to_list(row, MEMBER_COLS) if row else []
    return render_template('edit_member.html', member=member_row, row_num=row_num)

@app.route('/members/delete/<int:row_num>', methods=['POST'])
def delete_member(row_num):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('UPDATE members SET status=1 WHERE row_num=%s', (row_num,))
        flash('Member deleted.', 'success')
    except Exception as exc:
        flash(f'Could not delete member: {_error_message(exc)}', 'error')
    return redirect(url_for('members'))

# ─── Employees ───────────────────────────────────────────────

@app.route('/employees')
def employees():
    headers, rows = _fetch('employees', EMPLOYEE_COLS, status_col='status')
    return render_template('employees.html', headers=headers, rows=rows)

@app.route('/employees/add', methods=['GET', 'POST'])
def add_employee():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        email = request.form.get('email')
        phone = request.form.get('phone')
        designation = request.form.get('designation')
        salary = request.form.get('salary')
        permanent_address = request.form.get('permanent_address')
        temporary_address = request.form.get('temporary_address')
        emp_id = _next_id('employees', 'emp_id', 'EMP')
        err = _first_error([
            _require('Name', name),
            _check_email('Email', email),
            _check_money('Salary', salary),
        ])
        if err:
            flash(f'Could not add employee: {err}', 'error')
            return render_template('add_employee.html')
        try:
            password_hash = generate_password_hash(password) if password else None
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        'INSERT INTO employees (emp_id, name, user_id, password, email, phone, designation,'
                        ' salary, user_row_num, permanent_address, temporary_address, status)'
                        ' VALUES (%s,%s,NULL,%s,%s,%s,%s,%s,%s,%s,%s,0)',
                        (emp_id, name, password_hash, email, phone, designation, salary, '',
                         permanent_address, temporary_address),
                    )
            flash('Employee added.', 'success')
            return redirect(url_for('employees'))
        except Exception as exc:
            flash(f'Could not add employee: {_error_message(exc)}', 'error')
    return render_template('add_employee.html')

@app.route('/employees/edit/<int:row_num>', methods=['GET', 'POST'])
def edit_employee(row_num):
    if request.method == 'POST':
        try:
            password = request.form.get('password')
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            designation = request.form.get('designation')
            salary = request.form.get('salary')
            permanent_address = request.form.get('permanent_address')
            temporary_address = request.form.get('temporary_address')
            with get_connection() as conn:
                with conn.cursor() as cur:
                    if password:
                        cur.execute(
                            'UPDATE employees SET name=%s, password=%s, email=%s, phone=%s,'
                            ' designation=%s, salary=%s, permanent_address=%s, temporary_address=%s WHERE row_num=%s',
                            (name, generate_password_hash(password),
                             email, phone, designation,
                             salary, permanent_address,
                             temporary_address, row_num),
                        )
                    else:
                        cur.execute(
                            'UPDATE employees SET name=%s, email=%s, phone=%s,'
                            ' designation=%s, salary=%s, permanent_address=%s, temporary_address=%s WHERE row_num=%s',
                            (name, email, phone, designation,
                             salary, permanent_address,
                             temporary_address, row_num),
                        )
            flash('Employee updated.', 'success')
            return redirect(url_for('employees'))
        except Exception as exc:
            flash(f'Could not update employee: {_error_message(exc)}', 'error')

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM employees WHERE row_num=%s', (row_num,))
            row = cur.fetchone()
    emp_row = _to_list(row, EMPLOYEE_COLS) if row else []
    return render_template('edit_employee.html', employee=emp_row, row_num=row_num)

@app.route('/employees/delete/<int:row_num>', methods=['POST'])
def delete_employee(row_num):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('UPDATE employees SET status=1 WHERE row_num=%s', (row_num,))
        flash('Employee deleted.', 'success')
    except Exception as exc:
        flash(f'Could not delete employee: {_error_message(exc)}', 'error')
    return redirect(url_for('employees'))

# ─── Subscriptions ───────────────────────────────────────────────

@app.route('/subscriptions')
def subscriptions():
    headers, rows = _fetch('subscriptions', SUBSCRIPTION_COLS, status_col='subscription_status')
    member_names = _name_map('members', 'mem_id', 'name')
    return render_template('subscriptions.html', headers=headers, rows=rows, member_names=member_names)

@app.route('/subscriptions/add', methods=['GET', 'POST'])
def add_subscription():
    if request.method == 'POST':
        plan_mode = request.form.get('plan_mode')
        mem_id = request.form.get('mem_id')
        mem_subscription_amount = request.form.get('mem_subscription_amount')
        plan_type = request.form.get('plan_type')
        plan_start = request.form.get('plan_start')
        plan_end = request.form.get('plan_end')
        txn = _next_txn('subscriptions')
        err = _first_error([
            _require('Member', mem_id),
            _require('Plan mode', plan_mode),
            _check_money('Amount', mem_subscription_amount),
        ])
        if err:
            flash(f'Could not add subscription: {err}', 'error')
            return render_template('add_subscription.html')
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        'INSERT INTO subscriptions (transaction_id, transaction_date, timestamp, plan_mode,'
                        ' mem_id, mem_subscription_amount, plan_type, plan_start, plan_end, subscription_status)'
                        ' VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,0)',
                        (txn, datetime.now().strftime('%d-%b-%Y'), datetime.now().strftime('%I:%M:%S %p'),
                         plan_mode, mem_id, mem_subscription_amount, plan_type, plan_start, plan_end),
                    )
            flash('Subscription added.', 'success')
            return redirect(url_for('subscriptions'))
        except Exception as exc:
            flash(f'Could not add subscription: {_error_message(exc)}', 'error')
    members_dd = _id_list('members', 'mem_id', 'name')
    return render_template('add_subscription.html', members=members_dd)

@app.route('/subscriptions/edit/<int:row_num>', methods=['GET', 'POST'])
def edit_subscription(row_num):
    if request.method == 'POST':
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        'UPDATE subscriptions SET transaction_date=%s, timestamp=%s, plan_mode=%s, mem_id=%s,'
                        ' mem_subscription_amount=%s, plan_type=%s, plan_start=%s, plan_end=%s,'
                        ' subscription_status=%s WHERE row_num=%s',
                        (request.form.get('transaction_date'), request.form.get('timestamp'),
                         request.form.get('plan_mode'), request.form.get('mem_id'),
                         request.form.get('mem_subscription_amount'), request.form.get('plan_type'),
                         request.form.get('plan_start'), request.form.get('plan_end'),
                         request.form.get('subscription_status'), row_num),
                    )
            flash('Subscription updated.', 'success')
            return redirect(url_for('subscriptions'))
        except Exception as exc:
            flash(f'Could not update subscription: {_error_message(exc)}', 'error')

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM subscriptions WHERE row_num=%s', (row_num,))
            row = cur.fetchone()
    sub_row = _to_list(row, SUBSCRIPTION_COLS) if row else []
    members_dd = _id_list('members', 'mem_id', 'name')
    return render_template('edit_subscription.html', subscription=sub_row, row_num=row_num,
                           members=members_dd)

@app.route('/subscriptions/delete/<int:row_num>', methods=['POST'])
def delete_subscription(row_num):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('UPDATE subscriptions SET subscription_status=1 WHERE row_num=%s', (row_num,))
        flash('Subscription deleted.', 'success')
    except Exception as exc:
        flash(f'Could not delete subscription: {_error_message(exc)}', 'error')
    return redirect(url_for('subscriptions'))

# ─── Payments ───────────────────────────────────────────────

@app.route('/payments')
def payments():
    headers, rows = _fetch('payments', PAYMENT_COLS)
    member_names = _name_map('members', 'mem_id', 'name')
    employee_names = _name_map('employees', 'emp_id', 'name')
    return render_template('payments.html', headers=headers, rows=rows,
                           member_names=member_names, employee_names=employee_names)

@app.route('/payments/add', methods=['GET', 'POST'])
def add_payment():
    if request.method == 'POST':
        payment_amount = request.form.get('payment_amount')
        payment_type = request.form.get('payment_type')
        payment_mode = request.form.get('payment_mode')
        payment_status = request.form.get('payment_status')
        paid_by = request.form.get('paid_by')
        recieved_by = request.form.get('recieved_by')
        txn = _next_txn('payments')
        err = _first_error([
            _check_money('Amount', payment_amount),
            _require('Amount', payment_amount),
        ])
        if err:
            flash(f'Could not add payment: {err}', 'error')
            return render_template('add_payment.html')
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        'INSERT INTO payments (transaction_id, transaction_date, timestamp, payment_amount,'
                        ' payment_type, payment_mode, payment_status, paid_by, recieved_by, user_row_num)'
                        ' VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                        (txn, datetime.now().strftime('%d-%b-%Y'), datetime.now().strftime('%I:%M:%S %p'),
                         payment_amount, payment_type, payment_mode, payment_status, paid_by, recieved_by, ''),
                    )
            flash('Payment added.', 'success')
            return redirect(url_for('payments'))
        except Exception as exc:
            flash(f'Could not add payment: {_error_message(exc)}', 'error')
    members_dd = _id_list('members', 'mem_id', 'name')
    employees_dd = _id_list('employees', 'emp_id', 'name')
    return render_template('add_payment.html', members=members_dd, employees=employees_dd)

# ─── Book Sells ───────────────────────────────────────────────

@app.route('/book_sell')
def book_sell():
    headers, rows = _fetch('book_sell', SELL_COLS)
    member_names = _name_map('members', 'mem_id', 'name')
    return render_template('book_sell.html', headers=headers, rows=rows, member_names=member_names)

@app.route('/book_sell/add', methods=['GET', 'POST'])
def add_book_sell():
    if request.method == 'POST':
        order_date = request.form.get('order_date')
        book_id = request.form.get('book_id')
        book_name = request.form.get('book_name')
        book_price = request.form.get('book_price')
        mem_id = request.form.get('mem_id')
        order_id = _next_id('book_sell', 'order_id', 'ORDER')
        err = _first_error([
            _require('Book', book_id),
            _require('Book name', book_name),
            _require('Member', mem_id),
            _check_money('Price', book_price),
        ])
        if err:
            flash(f'Could not add sell record: {err}', 'error')
            return render_template('add_book_sell.html')
        try:
            conn = get_connection(autocommit=False)
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        'INSERT INTO book_sell (order_id, order_date, timestamp, book_id, book_name,'
                        ' book_price, mem_id) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                        (order_id, order_date, datetime.now().strftime('%d-%m-%Y %I:%M:%S %p'),
                         book_id, book_name, book_price, mem_id),
                    )
                    cur.execute(
                        'INSERT INTO payments (transaction_id, transaction_date, timestamp,'
                        ' payment_amount, payment_type, payment_mode, payment_status, paid_by,'
                        ' recieved_by) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                        (_next_id('payments', 'transaction_id', 'TXN'),
                         order_date, datetime.now().strftime('%H:%M:%S'),
                         book_price, 'Book Purchase', 'Cash', 'Completed', mem_id, None),
                    )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
            flash('Sell record added.', 'success')
            return redirect(url_for('book_sell'))
        except Exception as exc:
            flash(f'Could not add sell record: {_error_message(exc)}', 'error')
    books_dd = _book_list()
    members_dd = _id_list('members', 'mem_id', 'name')
    return render_template('add_book_sell.html', books=books_dd, members=members_dd)

@app.route('/book_sell/edit/<int:row_num>', methods=['GET', 'POST'])
def edit_book_sell(row_num):
    if request.method == 'POST':
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        'UPDATE book_sell SET order_date=%s, book_id=%s, book_name=%s, book_price=%s,'
                        ' mem_id=%s WHERE row_num=%s',
                        (request.form.get('order_date'), request.form.get('book_id'),
                         request.form.get('book_name'), request.form.get('book_price'),
                         request.form.get('mem_id'), row_num),
                    )
            flash('Sell record updated.', 'success')
            return redirect(url_for('book_sell'))
        except Exception as exc:
            flash(f'Could not update sell record: {_error_message(exc)}', 'error')

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM book_sell WHERE row_num=%s', (row_num,))
            row = cur.fetchone()
    sell_row = _to_list(row, SELL_COLS) if row else []
    books_dd = _book_list()
    members_dd = _id_list('members', 'mem_id', 'name')
    return render_template('edit_book_sell.html', sell=sell_row, row_num=row_num,
                           books=books_dd, members=members_dd)

# ─── Book Issues ───────────────────────────────────────────────

@app.route('/book_issue')
def book_issue():
    headers, rows = _fetch('book_issues', ISSUE_COLS)
    member_names = _name_map('members', 'mem_id', 'name')
    employee_names = _name_map('employees', 'emp_id', 'name')
    book_names = _name_map('books', 'book_id', 'book_name')
    return render_template('book_issue.html', headers=headers, rows=rows,
                           member_names=member_names, employee_names=employee_names,
                           book_names=book_names)

@app.route('/book_issue/add', methods=['GET', 'POST'])
def add_book_issue():
    if request.method == 'POST':
        transaction_date = request.form.get('transaction_date')
        book_id = request.form.get('book_id')
        issued_date = request.form.get('issued_date')
        issued_to = request.form.get('issued_to')
        txn = _next_txn('book_issues')
        err = _first_error([
            _require('Book', book_id),
            _require('Issued to', issued_to),
            _require('Issue date', issued_date),
        ])
        if err:
            flash(f'Could not add issue: {err}', 'error')
            return render_template('add_book_issue.html')
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        'INSERT INTO book_issues (transaction_id, transaction_date, timestamp, book_id,'
                        ' issued_date, issued_to, recieved_by, returned_date) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
                        (txn, transaction_date, datetime.now().strftime('%d-%m-%Y %I:%M:%S %p'),
                         book_id, issued_date, issued_to, None, None),
                    )
            flash('Book issued.', 'success')
            return redirect(url_for('book_issue'))
        except Exception as exc:
            flash(f'Could not add issue: {_error_message(exc)}', 'error')
    books_dd = _book_list()
    members_dd = _id_list('members', 'mem_id', 'name')
    employees_dd = _id_list('employees', 'emp_id', 'name')
    return render_template('add_book_issue.html', books=books_dd, members=members_dd, employees=employees_dd)

@app.route('/book_issue/return/<int:row_num>', methods=['GET', 'POST'])
def return_book_issue(row_num):
    if request.method == 'POST':
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        'UPDATE book_issues SET recieved_by=%s, returned_date=%s WHERE row_num=%s',
                        (request.form.get('recieved_by'), request.form.get('returned_date'), row_num),
                    )
            flash('Book returned.', 'success')
            return redirect(url_for('book_issue'))
        except Exception as exc:
            flash(f'Could not return book: {_error_message(exc)}', 'error')
    return render_template('return_book_issue.html', row_num=row_num,
                           employees=_id_list('employees', 'emp_id', 'name'))

# ─── AI Assistant (multi-agent) ──────────────────────────

from graph.orchestrator import build_graph, build_classifier
from graph.memory import load_history, append_turn, get_session_turns, list_sessions, delete_session
from tools.llm import get_llm

_llm = None
_graph = None


def _get_llm():
    global _llm
    if _llm is None:
        _llm = get_llm()
    return _llm


def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph(llm=_get_llm(), classifier=build_classifier(_get_llm()))
    return _graph


@app.route('/chat/history', methods=['GET'])
def chat_history():
    session_id = request.args.get('session_id') or 'default'
    turns = get_session_turns(session_id)
    return jsonify({'session_id': session_id, 'turns': turns})


@app.route('/chat/sessions', methods=['GET'])
def chat_sessions():
    sessions = list_sessions(limit=25)
    return jsonify({'sessions': sessions})


@app.route('/chat/sessions/<session_id>', methods=['DELETE'])
def chat_session_delete(session_id):
    deleted = delete_session(session_id)
    return jsonify({'deleted': deleted, 'session_id': session_id})


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json(force=True, silent=True) or {}
    user_message = (data.get('message') or '').strip()
    session_id = data.get('session_id') or 'default'
    if not user_message:
        return jsonify({'response': 'Please type a message.'})

    history = load_history(session_id)
    messages = history + [{'role': 'user', 'content': user_message}]
    result = _get_graph().invoke({'messages': messages, 'session_id': session_id})

    response = None
    agent_name = None
    for m in result['messages']:
        if m.type == 'ai' and m.content:
            response = m.content
            agent_name = m.name
    response = response or 'I could not process that request.'

    append_turn(session_id, user_message, agent_name, response, [])
    return jsonify({'response': response, 'agent': agent_name})


@app.route('/chat/stream', methods=['POST'])
def chat_stream():
    """SSE streaming endpoint. Emits JSON events:
    {"type": "delta", "text": "..."} per token, then {"type": "done",
    "response": "...", "agent": "..."}."""
    data = request.get_json(force=True, silent=True) or {}
    user_message = (data.get('message') or '').strip()
    session_id = data.get('session_id') or 'default'
    if not user_message:
        return jsonify({'response': 'Please type a message.'})

    history = load_history(session_id)
    messages = history + [{'role': 'user', 'content': user_message}]

    def generate():
        try:
            buf = []
            agent_name = None
            for mode, event in _get_graph().stream(
                {'messages': messages, 'session_id': session_id},
                stream_mode=['custom', 'updates'],
            ):
                if mode == 'custom':
                    if isinstance(event, dict) and event.get('delta'):
                        buf.append(event['delta'])
                        yield 'data: ' + json.dumps({'type': 'delta', 'text': event['delta']}) + '\n\n'
                elif mode == 'updates':
                    for node, update in event.items():
                        if isinstance(update, dict):
                            if update.get('next'):
                                agent_name = update['next']
            response = ''.join(buf) or 'I could not process that request.'
            append_turn(session_id, user_message, agent_name, response, [])
            yield 'data: ' + json.dumps({'type': 'done', 'response': response, 'agent': agent_name}) + '\n\n'
        except Exception as exc:
            yield 'data: ' + json.dumps({'type': 'error', 'message': str(exc)}) + '\n\n'

    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

if __name__ == '__main__':
    app.run(debug=True)
