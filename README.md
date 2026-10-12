# Lab 2: Login & To-Do Application

## 1. Team
| Name | ID 
| Aly Badawy | 2304123 
| Joumana Mohamed | 2304067

## 2. Technology
- Back end: Python 3 + Flask, PyMySQL (plain SQL with `%s` parameters, no ORM), bcrypt, python-dotenv
- Front end: HTML (Jinja templates), CSS (own stylesheet, responsive, light animations), JavaScript (validation, delete confirmation, dark mode)
- Database: MySQL 8, database `registration` (tables `users`, `todos`)

## 3. How to run it (from an empty machine)
1. Install Python 3.10+ and MySQL 8.
2. Clone this repository and open a terminal in its folder.
3. Create a virtual environment and install the packages:
   ```
   python -m venv venv
   venv\Scripts\activate        (Windows)   or   source venv/bin/activate   (Linux/Mac)
   pip install -r requirements.txt
   ```
4. Build the database: run `database/schema.sql` in MySQL (for example `mysql -u root -p < database/schema.sql`).
5. Copy `.env.example` to `.env` and put your real MySQL password and a random `SECRET_KEY`.
6. Start the server: `python app.py`
7. Open http://127.0.0.1:5000

## 4. Features
R1 register (duplicate e-mail check, auto login) · R2 login/logout with one generic error · R3 private list (redirect to login) ·
R4 add · R5 edit title · R6 mark done / not done · R7 delete with "are you sure?" · R8 validation in the browser and on the server with the exact messages ·
R9 bcrypt hashes, only the given queries with parameters, `user_id` from the session · R10 responsive, consistent UI with an empty state.
counter of open to-dos; filter (All / Open / Done); search box; optional due date per to-do (overdue ones are marked); dark mode (remembered in the browser).

## 5. Screenshots
Put them in `screenshots/` and link them here: register page with errors, login page, list with some to-dos (one done), phone-sized window.

## 6. Answers
**(a)** `AND user_id = ?` makes the statement touch only rows that belong to the logged-in user. The to-do id comes from the browser, so anyone can send another user's id. Without the condition, any logged-in user could edit or delete other people's to-dos.

**(b)** MySQL rejects the insert with a foreign-key error (error 1452). This is **referential integrity**: a foreign key value must exist as a primary key value in the referenced table (`users.user_id`).

**(c)** If the database leaks, plain passwords would be exposed (and people reuse passwords). A bcrypt hash is one-way, salted (equal passwords give different hashes) and slow on purpose, so it is very hard to reverse. At login the library compares the typed password with the hash.

**(d)** `NOT NULL` only forbids NULL. An empty text `''` (or spaces) is a value, so MySQL accepts it. Only our own check (in JavaScript and on the server) can refuse an empty name.
