from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
DB_NAME = 'library.db'

# Функция для подключения к SQLite с возвратом результатов в виде словарей
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# Инициализация базы данных при первом запуске
def init_db():
    conn = get_db_connection()
    with open('database_sqlite.sql', 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    # Добавим тестового читателя, если таблица пустая
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM readers")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO readers (ticket_number, full_name, phone, address) VALUES ('С-1042', 'Алексей Иванов', '+375291234567', 'г. Гродно, ул. Советская, 15')")
        cursor.execute("INSERT INTO books (title, author, year, status) VALUES ('Чистый код', 'Роберт Мартин', 2018, 'в наличии')")
        conn.commit()
    conn.close()

# 1. Главная страница (Каталог + Валидация добавления книги)
@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db_connection()
    error = None
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        year_str = request.form.get('year', '').strip()
        
        # Валидация ввода
        if not title or not author or not year_str:
            error = "Все поля формы должны быть заполнены!"
        else:
            try:
                year = int(year_str)
                current_year = datetime.now().year
                if year < 1400 or year > current_year:
                    raise ValueError()
                
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO books (title, author, year, status) VALUES (?, ?, ?, 'в наличии')",
                    (title, author, year)
                )
                conn.commit()
                conn.close()
                return redirect(url_for('index'))
            except ValueError:
                error = f"Некорректный год издания! Введите число от 1400 до {current_year}."

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    conn.close()
    
    return render_template('index.html', books=books, error=error)

# 2. Страница авторизации
@app.route('/login')
def login():
    return render_template('login.html')

# 3. Панель сотрудника (Выдача литературы с валидацией)
@app.route('/librarian', methods=['GET', 'POST'])
def librarian():
    conn = get_db_connection()
    error = None
    success = None
    
    if request.method == 'POST':
        ticket = request.form.get('ticket_number', '').strip()
        book_id_str = request.form.get('book_id', '').strip()
        
        if not ticket or not book_id_str:
            error = "Необходимо указать номер читательского билета и ID книги!"
        else:
            try:
                book_id = int(book_id_str)
                cursor = conn.cursor()
                
                # Проверяем существование читателя
                cursor.execute("SELECT id FROM readers WHERE ticket_number = ?", (ticket,))
                reader = cursor.fetchone()
                if not reader:
                    raise ValueError("Читатель с таким номером билета не найден в базе!")
                
                reader_id = reader['id']
                
                # Проверяем статус книги
                cursor.execute("SELECT status FROM books WHERE id = ?", (book_id,))
                book = cursor.fetchone()
                if not book:
                    raise ValueError("Книга с указанным ID не найдена!")
                if book['status'] == 'выдана':
                    raise ValueError("Эта книга уже находится на руках у другого читателя!")
                
                # Оформляем выдачу
                issue_date = datetime.now().strftime('%Y-%m-%d')
                due_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                
                cursor.execute(
                    "INSERT INTO loans (book_id, reader_id, issue_date, due_date) VALUES (?, ?, ?, ?)",
                    (book_id, reader_id, issue_date, due_date)
                )
                cursor.execute("UPDATE books SET status = 'выдана' WHERE id = ?", (book_id,))
                conn.commit()
                success = "Книга успешно выдана читателю!"
                
            except ValueError as e:
                error = str(e)

    cursor = conn.cursor()
    cursor.execute("""
        SELECT loans.id, books.title, readers.full_name, loans.issue_date, loans.due_date 
        FROM loans 
        JOIN books ON loans.book_id = books.id 
        JOIN readers ON loans.reader_id = readers.id 
        WHERE loans.return_date IS NULL
    """)
    active_loans = cursor.fetchall()
    conn.close()
    
    return render_template('librarian.html', loans=active_loans, error=error, success=success)

# 4. Личный кабинет читателя
@app.route('/reader')
def reader():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Для демонстрации берем читателя с id = 1
    cursor.execute("SELECT * FROM readers WHERE id = 1")
    current_reader = cursor.fetchone()
    
    cursor.execute("""
        SELECT books.title, books.author, loans.issue_date, loans.due_date 
        FROM loans 
        JOIN books ON loans.book_id = books.id 
        WHERE loans.reader_id = 1 AND loans.return_date IS NULL
    """)
    my_books = cursor.fetchall()
    conn.close()
    
    return render_template('reader.html', reader=current_reader, my_books=my_books)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
