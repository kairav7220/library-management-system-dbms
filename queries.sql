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

-- Payments received by employees
SELECT p.transaction_id, p.payment_amount, p.payment_mode, m.name AS paid_by, e.name AS received_by
FROM payments p
JOIN members m ON p.paid_by = m.mem_id
JOIN employees e ON p.recieved_by = e.emp_id;

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
-- ============================================================

-- Transaction 1: Issue a book to a member (atomic operation)
START TRANSACTION;
INSERT INTO book_issues (transaction_id, transaction_date, timestamp, book_id, issued_date, issued_to, recieved_by)
VALUES ('TXN_7', CURDATE(), NOW(), 'BOOK_5', CURDATE(), 'MEM_3', 'EMP_1');
UPDATE books SET status = 1 WHERE book_id = 'BOOK_5';
COMMIT;

-- Transaction 2: Process a subscription payment
START TRANSACTION;
INSERT INTO payments (transaction_id, transaction_date, timestamp, payment_amount, payment_type, payment_mode, payment_status, paid_by, recieved_by)
VALUES ('TXN_8', CURDATE(), NOW(), 500, 'Subscription', 'UPI', 'Completed', 'MEM_3', 'EMP_1');
UPDATE subscriptions SET subscription_status = 1 WHERE mem_id = 'MEM_3';
COMMIT;

-- Transaction 3: With ROLLBACK on failure
START TRANSACTION;
INSERT INTO book_sell (order_id, order_date, timestamp, book_id, book_name, book_price, mem_id)
VALUES ('ORDER_6', CURDATE(), NOW(), 'BOOK_14', 'The Origin of Species', 380, 'MEM_4');
UPDATE books SET status = 0 WHERE book_id = 'BOOK_14';
ROLLBACK;  -- undo if something goes wrong

-- ============================================================
-- E. ORDERING AND LIMIT
-- ============================================================

-- Top 5 most expensive books
SELECT book_name, book_price FROM books ORDER BY book_price DESC LIMIT 5;

-- Recent book issues by timestamp
SELECT * FROM book_issues ORDER BY timestamp DESC;

-- Books in alphabetical order
SELECT book_name, book_author FROM books ORDER BY book_name ASC;
