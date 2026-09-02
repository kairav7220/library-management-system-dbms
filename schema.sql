-- ============================================================
-- Library Management System - MySQL Schema and Sample Data
-- DBMS Assignment
-- ============================================================

CREATE DATABASE IF NOT EXISTS library_db;
USE library_db;

-- ============================================================
-- 1. USERS
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    row_num INT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(20) UNIQUE NOT NULL,
    user_type VARCHAR(50),
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(150),
    phone VARCHAR(15),
    status TINYINT DEFAULT 0
);

INSERT INTO users (user_id, user_type, username, password, email, phone, status) VALUES
('USER_1','Admin','admin','admin123','admin@library.com','9876543210',0),
('USER_2','Employee','priya_emp','pass123','priya@library.com','9876543211',0),
('USER_3','Employee','rahul_emp','pass123','rahul@library.com','9876543212',0),
('USER_4','Member','amit_mem','pass123','amit@gmail.com','9876543213',0),
('USER_5','Member','sneha_mem','pass123','sneha@gmail.com','9876543214',0),
('USER_6','Member','rohit_mem','pass123','rohit@gmail.com','9876543215',0),
('USER_7','Member','priya_mem','pass123','priya.s@gmail.com','9876543216',0);

-- ============================================================
-- 2. BOOK CATEGORY
-- ============================================================
CREATE TABLE IF NOT EXISTS book_category (
    row_num INT PRIMARY KEY AUTO_INCREMENT,
    cat_id VARCHAR(20) UNIQUE NOT NULL,
    cat_name VARCHAR(100) NOT NULL,
    description TEXT,
    book_names TEXT,
    status TINYINT DEFAULT 0
);

INSERT INTO book_category (cat_id, cat_name, description, book_names, status) VALUES
('CAT_1','Fiction','Novels and literary works across genres','To Kill a Mockingbird, 1984, Pride and Prejudice, The Great Gatsby, The Alchemist, Interpreter of Maladies, The God of Small Things, Midnight Children, Five Point Someone, The Immortals of Meluha, Life of Pi',0),
('CAT_2','Fantasy','Imaginary worlds and magical adventures','The Hobbit, Harry Potter and the Philosopher Stone',0),
('CAT_3','Non-Fiction','Factual books on self-improvement, finance, history','Atomic Habits, Rich Dad Poor Dad, Think and Grow Rich, The Psychology of Money, Sapiens',0),
('CAT_4','Science','Scientific literature and discoveries','A Brief History of Time, The Origin of Species, Dune',0);

-- ============================================================
-- 3. BOOK GENRE
-- ============================================================
CREATE TABLE IF NOT EXISTS book_genre (
    row_num INT PRIMARY KEY AUTO_INCREMENT,
    genre_id VARCHAR(20) UNIQUE NOT NULL,
    genre_title VARCHAR(100) NOT NULL,
    book_names TEXT,
    status TINYINT DEFAULT 0
);

INSERT INTO book_genre (genre_id, genre_title, book_names, status) VALUES
('GENRE_1','Classic','To Kill a Mockingbird, 1984, The Great Gatsby, Pride and Prejudice',0),
('GENRE_2','Dystopian','1984',0),
('GENRE_3','Romance','Pride and Prejudice',0),
('GENRE_4','Adventure','The Hobbit, Life of Pi',0),
('GENRE_5','Young Adult','Harry Potter and the Philosopher Stone',0),
('GENRE_6','Philosophy','The Alchemist',0),
('GENRE_7','Self-Help','Atomic Habits',0),
('GENRE_8','Finance','Rich Dad Poor Dad, Think and Grow Rich, The Psychology of Money',0),
('GENRE_9','History','Sapiens',0),
('GENRE_10','Physics','A Brief History of Time',0),
('GENRE_11','Biology','The Origin of Species',0),
('GENRE_12','Short Stories','Interpreter of Maladies',0),
('GENRE_13','Literary','The God of Small Things',0),
('GENRE_14','Magical Realism','Midnight Children',0),
('GENRE_15','Contemporary','Five Point Someone',0),
('GENRE_16','Mythology','The Immortals of Meluha',0),
('GENRE_17','Sci-Fi','Dune',0);

-- ============================================================
-- 4. BOOKS
-- ============================================================
CREATE TABLE IF NOT EXISTS books (
    row_num INT PRIMARY KEY AUTO_INCREMENT,
    book_id VARCHAR(20) UNIQUE NOT NULL,
    book_name VARCHAR(255) NOT NULL,
    book_author VARCHAR(255),
    book_price DECIMAL(10,2),
    book_cat VARCHAR(100),
    book_genre VARCHAR(100),
    edition VARCHAR(50),
    publication VARCHAR(255),
    status TINYINT DEFAULT 0
);

INSERT INTO books (book_id, book_name, book_author, book_price, book_cat, book_genre, edition, publication, status) VALUES
('BOOK_1','To Kill a Mockingbird','Harper Lee',350,'Fiction','Classic','1st','J.B. Lippincott',0),
('BOOK_2','1984','George Orwell',299,'Fiction','Dystopian','1st','Secker & Warburg',0),
('BOOK_3','Pride and Prejudice','Jane Austen',250,'Fiction','Romance','Revised','Penguin Classics',0),
('BOOK_4','The Great Gatsby','F. Scott Fitzgerald',320,'Fiction','Classic','1st','Scribner',0),
('BOOK_5','The Hobbit','J.R.R. Tolkien',399,'Fantasy','Adventure','1st','George Allen & Unwin',0),
('BOOK_6','Harry Potter and the Philosopher Stone','J.K. Rowling',450,'Fantasy','Young Adult','1st','Bloomsbury',0),
('BOOK_7','The Alchemist','Paulo Coelho',280,'Fiction','Philosophy','1st','HarperOne',0),
('BOOK_8','Atomic Habits','James Clear',550,'Non-Fiction','Self-Help','1st','Avery',0),
('BOOK_9','Rich Dad Poor Dad','Robert Kiyosaki',400,'Non-Fiction','Finance','1st','Plata Publishing',0),
('BOOK_10','Think and Grow Rich','Napoleon Hill',350,'Non-Fiction','Finance','Revised','Self-Publishing',0),
('BOOK_11','The Psychology of Money','Morgan Housel',499,'Non-Fiction','Finance','1st','Harriman House',0),
('BOOK_12','Sapiens','Yuval Noah Harari',599,'Non-Fiction','History','1st','Harper',0),
('BOOK_13','A Brief History of Time','Stephen Hawking',450,'Science','Physics','1st','Bantam Books',0),
('BOOK_14','The Origin of Species','Charles Darwin',380,'Science','Biology','1st','John Murray',0),
('BOOK_15','Interpreter of Maladies','Jhumpa Lahiri',300,'Fiction','Short Stories','1st','Houghton Mifflin',0),
('BOOK_16','The God of Small Things','Arundhati Roy',350,'Fiction','Literary','1st','IndiaInk',0),
('BOOK_17','Midnight Children','Salman Rushdie',420,'Fiction','Magical Realism','1st','Jonathan Cape',0),
('BOOK_18','Five Point Someone','Chetan Bhagat',250,'Fiction','Contemporary','1st','Rupa Publications',0),
('BOOK_19','The Immortals of Meluha','Amish Tripathi',399,'Fiction','Mythology','1st','Westland',0),
('BOOK_20','Life of Pi','Yann Martel',370,'Fiction','Adventure','1st','Knopf Canada',0),
('BOOK_21','Dune','Frank Herbert',499,'Science','Sci-Fi','1st','Chilton Books',0);

-- ============================================================
-- 5. MEMBERS
-- ============================================================
CREATE TABLE IF NOT EXISTS members (
    row_num INT PRIMARY KEY AUTO_INCREMENT,
    mem_id VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    user_id VARCHAR(20),
    password VARCHAR(255),
    email VARCHAR(150),
    phone VARCHAR(15),
    user_row_num VARCHAR(20),
    permanent_address TEXT,
    temporary_address TEXT,
    status TINYINT DEFAULT 0
);

INSERT INTO members (mem_id, name, user_id, password, email, phone, user_row_num, permanent_address, temporary_address, status) VALUES
('MEM_1','Amit Sharma','USER_4','pass123','amit@gmail.com','9876543213',5,'Sector 17, Chandigarh','Sector 12, Kharar',0),
('MEM_2','Sneha Verma','USER_5','pass123','sneha@gmail.com','9876543214',6,'Mohali Phase 7','Sector 22, Chandigarh',0),
('MEM_3','Rohit Gupta','USER_6','pass123','rohit@gmail.com','9876543215',7,'Phase 5, Mohali','Sector 34, Chandigarh',0),
('MEM_4','Priya Singh','USER_7','pass123','priya.s@gmail.com','9876543216',8,'Zirakpur','Sector 11, Panchkula',0);

-- ============================================================
-- 6. EMPLOYEES
-- ============================================================
CREATE TABLE IF NOT EXISTS employees (
    row_num INT PRIMARY KEY AUTO_INCREMENT,
    emp_id VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    user_id VARCHAR(20),
    password VARCHAR(255),
    email VARCHAR(150),
    phone VARCHAR(15),
    designation VARCHAR(100),
    salary DECIMAL(10,2),
    user_row_num VARCHAR(20),
    permanent_address TEXT,
    temporary_address TEXT,
    status TINYINT DEFAULT 0
);

INSERT INTO employees (emp_id, name, user_id, password, email, phone, designation, salary, user_row_num, permanent_address, temporary_address, status) VALUES
('EMP_1','Priya Mehta','USER_2','pass123','priya@library.com','9876543211','Head Librarian',35000,3,'Phase 3, Mohali','Sector 20, Chandigarh',0),
('EMP_2','Rahul Kapoor','USER_3','pass123','rahul@library.com','9876543212','Assistant Librarian',25000,4,'Phase 5, Mohali','Sector 15, Panchkula',0);

-- ============================================================
-- 7. BOOK ISSUES
-- ============================================================
CREATE TABLE IF NOT EXISTS book_issues (
    row_num INT PRIMARY KEY AUTO_INCREMENT,
    transaction_id VARCHAR(20) UNIQUE NOT NULL,
    transaction_date VARCHAR(50),
    timestamp VARCHAR(50),
    book_id VARCHAR(20),
    issued_date VARCHAR(50),
    issued_to VARCHAR(20),
    recieved_by VARCHAR(20),
    returned_date VARCHAR(50)
);

INSERT INTO book_issues (transaction_id, transaction_date, timestamp, book_id, issued_date, issued_to, recieved_by, returned_date) VALUES
('TXN_1','2026-01-20','2026-01-20 11:00:00','BOOK_1','2026-01-20','MEM_1','EMP_1',NULL),
('TXN_2','2026-02-10','2026-02-10 14:30:00','BOOK_4','2026-02-10','MEM_2','EMP_1',NULL),
('TXN_3','2026-03-05','2026-03-05 09:15:00','BOOK_6','2026-03-05','MEM_3','EMP_2',NULL),
('TXN_4','2026-04-18','2026-04-18 10:45:00','BOOK_8','2026-04-18','MEM_4','EMP_2','2026-05-02'),
('TXN_5','2026-05-22','2026-05-22 15:00:00','BOOK_13','2026-05-22','MEM_1','EMP_1',NULL),
('TXN_6','2026-06-30','2026-06-30 11:30:00','BOOK_15','2026-06-30','MEM_2','EMP_2',NULL);

-- ============================================================
-- 8. SUBSCRIPTIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS subscriptions (
    row_num INT PRIMARY KEY AUTO_INCREMENT,
    transaction_id VARCHAR(20) UNIQUE NOT NULL,
    transaction_date VARCHAR(50),
    timestamp VARCHAR(50),
    plan_mode VARCHAR(50),
    mem_id VARCHAR(20),
    mem_subscription_amount DECIMAL(10,2),
    plan_type VARCHAR(50),
    plan_start VARCHAR(50),
    plan_end VARCHAR(50),
    subscription_status TINYINT DEFAULT 0
);

INSERT INTO subscriptions (transaction_id, transaction_date, timestamp, plan_mode, mem_id, mem_subscription_amount, plan_type, plan_start, plan_end, subscription_status) VALUES
('TXN_1','2026-01-15','2026-01-15 10:30:00','Online','MEM_1',500,'Monthly','2026-01-15','2026-02-15',0),
('TXN_2','2026-02-01','2026-02-01 11:00:00','Offline','MEM_2',1500,'Yearly','2026-02-01','2027-02-01',0),
('TXN_3','2026-03-10','2026-03-10 09:45:00','Online','MEM_3',500,'Monthly','2026-03-10','2026-04-10',0),
('TXN_4','2026-04-05','2026-04-05 14:20:00','Online','MEM_4',750,'Quarterly','2026-04-05','2026-07-05',0);

-- ============================================================
-- 9. PAYMENTS
-- ============================================================
CREATE TABLE IF NOT EXISTS payments (
    row_num INT PRIMARY KEY AUTO_INCREMENT,
    transaction_id VARCHAR(20) UNIQUE NOT NULL,
    transaction_date VARCHAR(50),
    timestamp VARCHAR(50),
    payment_amount DECIMAL(10,2),
    payment_type VARCHAR(50),
    payment_mode VARCHAR(50),
    payment_status VARCHAR(50),
    paid_by VARCHAR(20),
    recieved_by VARCHAR(20),
    user_row_num VARCHAR(20)
);

INSERT INTO payments (transaction_id, transaction_date, timestamp, payment_amount, payment_type, payment_mode, payment_status, paid_by, recieved_by, user_row_num) VALUES
('TXN_1','2026-01-15','10:30:00',500,'Subscription','UPI','Completed','MEM_1','EMP_1',5),
('TXN_2','2026-02-01','11:00:00',1500,'Subscription','Cash','Completed','MEM_2','EMP_1',6),
('TXN_3','2026-03-10','09:45:00',500,'Subscription','Card','Completed','MEM_3','EMP_2',7),
('TXN_4','2026-04-05','14:20:00',750,'Subscription','UPI','Completed','MEM_4','EMP_2',8),
('TXN_5','2026-05-20','16:10:00',450,'Book Purchase','UPI','Completed','MEM_1','EMP_1',5),
('TXN_6','2026-06-12','12:00:00',399,'Book Purchase','Cash','Completed','MEM_2','EMP_2',6);

-- ============================================================
-- 10. BOOK SELL
-- ============================================================
CREATE TABLE IF NOT EXISTS book_sell (
    row_num INT PRIMARY KEY AUTO_INCREMENT,
    order_id VARCHAR(20) UNIQUE NOT NULL,
    order_date VARCHAR(50),
    timestamp VARCHAR(50),
    book_id VARCHAR(20),
    book_name VARCHAR(255),
    book_price DECIMAL(10,2),
    mem_id VARCHAR(20)
);

INSERT INTO book_sell (order_id, order_date, timestamp, book_id, book_name, book_price, mem_id) VALUES
('ORDER_1','2026-01-10','2026-01-10 10:00:00','BOOK_8','The Alchemist',280,'MEM_1'),
('ORDER_2','2026-02-14','2026-02-14 12:30:00','BOOK_9','Atomic Habits',550,'MEM_2'),
('ORDER_3','2026-03-20','2026-03-20 14:00:00','BOOK_11','Think and Grow Rich',350,'MEM_3'),
('ORDER_4','2026-04-25','2026-04-25 11:15:00','BOOK_17','The God of Small Things',350,'MEM_4'),
('ORDER_5','2026-05-18','2026-05-18 16:45:00','BOOK_20','The Immortals of Meluha',399,'MEM_1');

-- ============================================================
-- 11. LOGS (login/logout audit)
-- ============================================================
CREATE TABLE IF NOT EXISTS logs (
    row_num INT PRIMARY KEY AUTO_INCREMENT,
    timestamp VARCHAR(50),
    action VARCHAR(255)
);

-- ============================================================
-- 12. CUSTOMERS
-- ============================================================
CREATE TABLE IF NOT EXISTS customers (
    row_num INT PRIMARY KEY AUTO_INCREMENT,
    cust_id VARCHAR(20),
    name VARCHAR(100),
    username VARCHAR(100),
    password VARCHAR(255)
);

