CREATE DATABASE IF NOT EXISTS library_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE library_db;

-- 1. Таблица читателей
CREATE TABLE readers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_number VARCHAR(50) NOT NULL UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    address TEXT
);

-- 2. Таблица книг
CREATE TABLE books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(250) NOT NULL,
    author VARCHAR(150) NOT NULL,
    year INT NOT NULL,
    status ENUM('в наличии', 'выдана') DEFAULT 'в наличии'
);

-- 3. Таблица пользователей (авторизация)
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('reader', 'librarian') NOT NULL,
    reader_id INT NULL,
    FOREIGN KEY (reader_id) REFERENCES readers(id) ON DELETE SET NULL
);

-- 4. Таблица выдачи книг (абонемент)
CREATE TABLE loans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    reader_id INT NOT NULL,
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    return_date DATE NULL,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY (reader_id) REFERENCES readers(id) ON DELETE CASCADE
);