from flask import Flask, render_template, request, redirect, url_for
import pymysql

app = Flask(__name__)

# Функция для подключения к базе данных MySQL
def get_db_connection():
    connection = pymysql.connect(
        host='localhost',
        user='library_user',
        password='password123',
        database='library_db',
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

# 1. Главная страница (Каталог книг с выводом из БД и формой добавления)
@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # Обработка добавления новой книги через форму
        if request.method == 'POST':
            title = request.form['title']
            author = request.form['author']
            year = request.form['year']
            cursor.execute(
                "INSERT INTO books (title, author, year, status) VALUES (%s, %s, %s, 'в наличии')",
                (title, author, year)
            )
            conn.commit()
            return redirect(url_for('index'))
        
        # Получение списка всех книг из базы данных
        cursor.execute("SELECT * FROM books")
        books = cursor.fetchall()
    conn.close()
    return render_template('index.html', books=books)

# 2. Страница авторизации
@app.route('/login')
def login():
    return render_template('login.html')

# 3. Панель сотрудника (Управление выдачей)
@app.route('/librarian', methods=['GET', 'POST'])
def librarian():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        if request.method == 'POST':
            ticket = request.form['ticket_number']
            book_id = request.form['book_id']
            # Находим читателя по номеру билета
            cursor.execute("SELECT id FROM readers WHERE ticket_number = %s", (ticket,))
            reader = cursor.fetchone()
            
            if reader:
                reader_id = reader['id']
                # Фиксируем выдачу книги в таблице loans
                cursor.execute(
                    "INSERT INTO loans (book_id, reader_id, issue_date, due_date) VALUES (%s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY))",
                    (book_id, reader_id)
                )
                # Меняем статус книги на 'выдана'
                cursor.execute("UPDATE books SET status = 'выдана' WHERE id = %s", (book_id,))
                conn.commit()
        
        # Получаем список активных выдач для отображения
        cursor.execute("""
            SELECT loans.id, books.title, readers.full_name, loans.issue_date, loans.due_date 
            FROM loans 
            JOIN books ON loans.book_id = books.id 
            JOIN readers ON loans.reader_id = readers.id 
            WHERE loans.return_date IS NULL
        """)
        active_loans = cursor.fetchall()
    conn.close()
    return render_template('librarian.html', loans=active_loans)

# 4. Личный кабинет читателя
@app.route('/reader')
def reader():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # Для примера выведем читателя с id = 1
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
    app.run(debug=True)
