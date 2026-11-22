import sqlite3
from pathlib import Path
from datetime import date

DB_PATH = Path(__file__).resolve().with_name("library.db")


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            book_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS issue_records (
            issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            issue_date TEXT NOT NULL,
            return_date TEXT,
            status TEXT NOT NULL DEFAULT 'Issued',
            FOREIGN KEY (book_id) REFERENCES books(book_id),
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)

    conn.commit()
    conn.close()


# ---------------- BOOK OPERATIONS ----------------

def add_book(title, author, category, quantity):
    conn = connect_db()
    try:
        conn.execute(
            """INSERT INTO books (title, author, category, quantity)
               VALUES (?, ?, ?, ?)""",
            (title, author, category, quantity)
        )
        conn.commit()
    finally:
        conn.close()


def get_all_books():
    conn = connect_db()
    try:
        return conn.execute(
            """SELECT book_id, title, author, category, quantity
               FROM books ORDER BY book_id"""
        ).fetchall()
    finally:
        conn.close()


def search_books(keyword):
    conn = connect_db()
    try:
        pattern = f"%{keyword}%"
        return conn.execute(
            """SELECT book_id, title, author, category, quantity
               FROM books
               WHERE title LIKE ? OR author LIKE ? OR category LIKE ?
               ORDER BY book_id""",
            (pattern, pattern, pattern)
        ).fetchall()
    finally:
        conn.close()


def update_book(book_id, title, author, category, quantity):
    conn = connect_db()
    try:
        cursor = conn.execute(
            """UPDATE books
               SET title = ?, author = ?, category = ?, quantity = ?
               WHERE book_id = ?""",
            (title, author, category, quantity, book_id)
        )
        if cursor.rowcount == 0:
            raise ValueError("Book was not found.")
        conn.commit()
    finally:
        conn.close()


def delete_book(book_id):
    conn = connect_db()
    try:
        active = conn.execute(
            """SELECT COUNT(*) FROM issue_records
               WHERE book_id = ? AND status = 'Issued'""",
            (book_id,)
        ).fetchone()[0]

        if active:
            raise ValueError(
                "This book has an active issue record. Return it before deleting."
            )

        conn.execute("DELETE FROM issue_records WHERE book_id = ?", (book_id,))
        cursor = conn.execute("DELETE FROM books WHERE book_id = ?", (book_id,))
        if cursor.rowcount == 0:
            raise ValueError("Book was not found.")
        conn.commit()
    finally:
        conn.close()


# ---------------- STUDENT OPERATIONS ----------------

def add_student(name, email):
    conn = connect_db()
    try:
        conn.execute(
            "INSERT INTO students (name, email) VALUES (?, ?)",
            (name, email)
        )
        conn.commit()
    finally:
        conn.close()


def get_all_students():
    conn = connect_db()
    try:
        return conn.execute(
            """SELECT student_id, name, email
               FROM students ORDER BY student_id"""
        ).fetchall()
    finally:
        conn.close()


# ---------------- ISSUE / RETURN OPERATIONS ----------------

def issue_book(book_id, student_id):
    conn = connect_db()
    try:
        cursor = conn.cursor()

        book = cursor.execute(
            "SELECT quantity FROM books WHERE book_id = ?",
            (book_id,)
        ).fetchone()

        if book is None:
            raise ValueError("Selected book does not exist.")

        student = cursor.execute(
            "SELECT student_id FROM students WHERE student_id = ?",
            (student_id,)
        ).fetchone()

        if student is None:
            raise ValueError("Selected student does not exist.")

        if book[0] <= 0:
            raise ValueError("This book is currently unavailable.")

        cursor.execute(
            "UPDATE books SET quantity = quantity - 1 WHERE book_id = ?",
            (book_id,)
        )

        cursor.execute(
            """INSERT INTO issue_records
               (book_id, student_id, issue_date, return_date, status)
               VALUES (?, ?, ?, NULL, 'Issued')""",
            (book_id, student_id, date.today().isoformat())
        )

        issue_id = cursor.lastrowid
        conn.commit()
        return issue_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def return_book(issue_id):
    conn = connect_db()
    try:
        cursor = conn.cursor()

        record = cursor.execute(
            """SELECT book_id, status FROM issue_records
               WHERE issue_id = ?""",
            (issue_id,)
        ).fetchone()

        if record is None:
            raise ValueError("Issue record was not found.")

        book_id, status = record

        if status == "Returned":
            raise ValueError("This book has already been returned.")

        cursor.execute(
            """UPDATE issue_records
               SET status = 'Returned', return_date = ?
               WHERE issue_id = ?""",
            (date.today().isoformat(), issue_id)
        )

        cursor.execute(
            "UPDATE books SET quantity = quantity + 1 WHERE book_id = ?",
            (book_id,)
        )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_issued_books():
    conn = connect_db()
    try:
        return conn.execute(
            """SELECT
                   ir.issue_id,
                   b.title,
                   s.name,
                   ir.issue_date,
                   COALESCE(ir.return_date, ''),
                   ir.status
               FROM issue_records ir
               JOIN books b ON b.book_id = ir.book_id
               JOIN students s ON s.student_id = ir.student_id
               ORDER BY ir.issue_id DESC"""
        ).fetchall()
    finally:
        conn.close()
