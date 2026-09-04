-- ============================================================
-- Library Management System - DBMS Demo Queries
-- Covers: Searching, JOINs, Aggregates, Transactions, Ordering
-- ============================================================

USE library_db;

-- ============================================================
-- A. SEARCHING (SELECT with WHERE and LIKE)
-- ============================================================

-- Search books by title containing 'The'
SELECT book_id, book_name, book_author, book_price FROM books
WHERE book_name LIKE '%The%';

-- Search members by name containing 'a'
SELECT mem_id, name, email, phone FROM members
WHERE name LIKE '%a%';

-- Search expensive books (price > 400)
SELECT book_name, book_price FROM books
WHERE book_price > 400;

-- Books in Fiction category
SELECT book_name, book_cat FROM books
WHERE book_cat = 'Fiction';

-- ============================================================
-- B. JOIN QUERIES
-- ============================================================

-- Books issued to members (3-table JOIN)
SELECT bi.transaction_id, b.book_name, m.name AS member_name, bi.issued_date
FROM book_issues bi
JOIN books b ON bi.book_id = b.book_id
JOIN members m ON bi.issued_to = m.mem_id;

-- Payments received by employees (LEFT JOIN: auto-created sale payments
-- have recieved_by NULL, so an INNER JOIN would hide them)
SELECT p.transaction_id, p.payment_amount, p.payment_mode, m.name AS paid_by, e.name AS received_by
FROM payments p
JOIN members m ON p.paid_by = m.mem_id
LEFT JOIN employees e ON p.recieved_by = e.emp_id;

-- Books sold to members
SELECT s.order_id, s.book_name, s.book_price, m.name AS buyer
FROM book_sell s
JOIN members m ON s.mem_id = m.mem_id;

-- ============================================================
-- C. AGGREGATE QUERIES
-- ============================================================

-- Count books per category
SELECT book_cat, COUNT(*) AS total_books FROM books GROUP BY book_cat;

-- Total money collected per payment mode
SELECT payment_mode, SUM(payment_amount) AS total FROM payments GROUP BY payment_mode;

-- Max, min, avg book price
SELECT MAX(book_price) AS max_price, MIN(book_price) AS min_price,
       AVG(book_price) AS avg_price FROM books;

-- ============================================================
-- D. TRANSACTIONS
-- NOTE: demo IDs (TXN_7, TXN_8, ORDER_6) assume a fresh seed
-- (reset_db.py). Change them if you re-run this file twice.
-- ============================================================

-- Transaction 1: Sell a book (mirrors the app's add_book_sell flow:
-- sale row + matching payment row succeed or fail together)
START TRANSACTION;
INSERT INTO book_sell (order_id, order_date, timestamp, book_id, book_name, book_price, mem_id)
VALUES ('ORDER_6', CURDATE(), NOW(), 'BOOK_7', 'The Alchemist', 280, 'MEM_2');
INSERT INTO payments (transaction_id, transaction_date, timestamp, payment_amount, payment_type, payment_mode, payment_status, paid_by, recieved_by)
VALUES ('TXN_7', CURDATE(), NOW(), 280, 'Book Purchase', 'Cash', 'Completed', 'MEM_2', NULL);
COMMIT;

-- Transaction 2: Issue a book to a member (recieved_by/returned_date stay
-- NULL until the book is returned; issuing must NOT flip books.status,
-- since status=1 means soft-deleted/hidden from the catalog)
START TRANSACTION;
INSERT INTO book_issues (transaction_id, transaction_date, timestamp, book_id, issued_date, issued_to, recieved_by, returned_date)
VALUES ('TXN_7', CURDATE(), NOW(), 'BOOK_5', CURDATE(), 'MEM_3', NULL, NULL);
COMMIT;

-- Transaction 3: With ROLLBACK on failure (nothing persists)
START TRANSACTION;
INSERT INTO book_sell (order_id, order_date, timestamp, book_id, book_name, book_price, mem_id)
VALUES ('ORDER_7', CURDATE(), NOW(), 'BOOK_14', 'The Origin of Species', 380, 'MEM_4');
ROLLBACK;  -- undo: ORDER_7 never appears in book_sell

-- ============================================================
-- F. REFERENTIAL INTEGRITY (foreign keys)
-- Each of these MUST FAIL with error 1452 (foreign key constraint).
-- That rejection is the demo: the DB protects itself.
-- ============================================================

-- Sell to a member that does not exist -> rejected (fk_sell_member)
-- INSERT INTO book_sell (order_id, order_date, timestamp, book_id, book_name, book_price, mem_id)
-- VALUES ('ORDER_X', CURDATE(), NOW(), 'BOOK_1', 'To Kill a Mockingbird', 350, 'MEM_999');

-- Issue a book that does not exist -> rejected (fk_issues_book)
-- INSERT INTO book_issues (transaction_id, transaction_date, timestamp, book_id, issued_date, issued_to, recieved_by, returned_date)
-- VALUES ('TXN_X', CURDATE(), NOW(), 'BOOK_999', CURDATE(), 'MEM_1', NULL, NULL);

-- Record a payment received by an employee that does not exist -> rejected (fk_pay_employee)
-- INSERT INTO payments (transaction_id, transaction_date, timestamp, payment_amount, payment_type, payment_mode, payment_status, paid_by, recieved_by)
-- VALUES ('TXN_X', CURDATE(), NOW(), 100, 'Subscription', 'Cash', 'Completed', 'MEM_1', 'EMP_999');

-- ============================================================
-- E. ORDERING AND LIMIT
-- ============================================================

-- Top 5 most expensive books
SELECT book_name, book_price FROM books ORDER BY book_price DESC LIMIT 5;

-- Recent book issues by timestamp
SELECT * FROM book_issues ORDER BY timestamp DESC;

-- Books in alphabetical order
SELECT book_name, book_author FROM books ORDER BY book_name ASC;
