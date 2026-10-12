import os
from datetime import date
from functools import wraps

import bcrypt
import pymysql
from dotenv import load_dotenv
from flask import Flask, g, redirect, render_template, request, session, url_for

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-only-secret")


# ---------- database helpers ----------
def get_db():
    """One MySQL connection per request, closed automatically at the end."""
    if "db" not in g:
        g.db = pymysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "aly3573332"),
            database=os.getenv("DB_NAME", "registration"),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:  # R3: private pages
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


# ---------- validation (same rules as static/app.js) ----------
def check_title(title):
    if not title:
        return ["Title is required"]
    if len(title) > 200:
        return ["Title is too long (200 characters at most)"]
    return []


def check_register(name, email, password, confirm):
    errors = []
    if not name:
        errors.append("Name is required")
    if not email:
        errors.append("Email is required")
    if not password:
        errors.append("Password is required")
    if not confirm:
        errors.append("Confirm password is required")
    if password and confirm and password != confirm:
        errors.append("Passwords do not match")
    return errors


# ---------- auth ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("index"))
    if request.method == "GET":
        return render_template("register.html", errors=[], form={})

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")
    form = {"name": name, "email": email}

    errors = check_register(name, email, password, confirm)
    if errors:  # R8: show the page again, do not touch the database
        return render_template("register.html", errors=errors, form=form)

    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s)",
                (email, name, pw_hash),
            )
            new_id = cur.lastrowid
        db.commit()
    except pymysql.err.IntegrityError as e:
        db.rollback()
        if e.args[0] == 1062:  # duplicate e-mail (UNIQUE)
            return render_template("register.html", errors=["Email Already Exists"], form=form)
        raise

    session["user_id"] = new_id
    session["name"] = name
    return redirect(url_for("index"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))
    if request.method == "GET":
        return render_template("login.html", errors=[], form={})

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    form = {"email": email}

    errors = []
    if not email:
        errors.append("Email is required")
    if not password:
        errors.append("Password is required")
    if errors:
        return render_template("login.html", errors=errors, form=form)

    with get_db().cursor() as cur:
        cur.execute(
            "SELECT user_id, name, password_hash FROM users WHERE email = %s", (email,)
        )
        user = cur.fetchone()

    ok = user is not None and bcrypt.checkpw(
        password.encode("utf-8"), user["password_hash"].encode("utf-8")
    )
    if not ok:  # same message for wrong e-mail and wrong password (R2)
        return render_template("login.html", errors=["Invalid email or password"], form=form)

    session["user_id"] = user["user_id"]
    session["name"] = user["name"]
    return redirect(url_for("index"))


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- to-do list ----------
def parse_due(raw):
    """BONUS: optional due date. Returns (date or None, list of errors)."""
    raw = (raw or "").strip()
    if not raw:
        return None, []
    try:
        return date.fromisoformat(raw), []
    except ValueError:
        return None, ["Due date is invalid"]


def build_list_query(flt, q):
    """BONUS: filter (all/open/done) + search. SQL pieces are fixed strings written here;
    the user's text only travels as a parameter."""
    sql = ("SELECT todo_id, title, is_done, created_at, due_date FROM todos "
           "WHERE user_id = %s")
    params = [session["user_id"]]
    if flt == "open":
        sql += " AND is_done = 0"
    elif flt == "done":
        sql += " AND is_done = 1"
    if q:
        safe = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        sql += " AND title LIKE %s"
        params.append("%" + safe + "%")
    sql += " ORDER BY todo_id DESC"
    return sql, params


def render_list(add_errors=None, add_title="", add_due="",
                edit_id=None, edit_errors=None, edit_title="", edit_due=""):
    current = session.get("filter", "all")
    q = session.get("q", "")
    sql, params = build_list_query(current, q)
    with get_db().cursor() as cur:
        cur.execute(sql, params)
        todos = cur.fetchall()
        # BONUS: how many to-dos are still open
        cur.execute(
            "SELECT COUNT(*) AS open_count FROM todos WHERE user_id = %s AND is_done = 0",
            (session["user_id"],),
        )
        open_count = cur.fetchone()["open_count"]
    return render_template(
        "todos.html",
        todos=todos,
        name=session["name"],
        open_count=open_count,
        current=current,
        q=q,
        today=date.today(),
        add_errors=add_errors or [],
        add_title=add_title,
        add_due=add_due,
        edit_id=edit_id,
        edit_errors=edit_errors or [],
        edit_title=edit_title,
        edit_due=edit_due,
    )


@app.route("/")
@login_required
def index():
    # remember filter and search in the session so they survive add/edit/delete
    if request.args.get("filter") in ("all", "open", "done"):
        session["filter"] = request.args["filter"]
    if "q" in request.args:
        session["q"] = request.args["q"].strip()[:100]
    return render_list()


@app.route("/add", methods=["POST"])
@login_required
def add():
    title = request.form.get("title", "").strip()
    due_raw = request.form.get("due_date", "")
    due, due_errors = parse_due(due_raw)
    errors = check_title(title) + due_errors
    if errors:
        return render_list(add_errors=errors, add_title=title, add_due=due_raw)
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO todos (user_id, title, due_date) VALUES (%s, %s, %s)",
            (session["user_id"], title, due),
        )
    db.commit()
    return redirect(url_for("index"))


@app.route("/edit/<int:todo_id>", methods=["POST"])
@login_required
def edit(todo_id):
    title = request.form.get("title", "").strip()
    due_raw = request.form.get("due_date", "")
    due, due_errors = parse_due(due_raw)
    errors = check_title(title) + due_errors
    if errors:
        return render_list(edit_id=todo_id, edit_errors=errors,
                           edit_title=title, edit_due=due_raw)
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "UPDATE todos SET title = %s, due_date = %s WHERE todo_id = %s AND user_id = %s",
            (title, due, todo_id, session["user_id"]),
        )
    db.commit()
    return redirect(url_for("index"))


@app.route("/toggle/<int:todo_id>", methods=["POST"])
@login_required
def toggle(todo_id):
    is_done = 1 if request.form.get("is_done") == "1" else 0
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "UPDATE todos SET is_done = %s WHERE todo_id = %s AND user_id = %s",
            (is_done, todo_id, session["user_id"]),
        )
    db.commit()
    return redirect(url_for("index"))


@app.route("/delete/<int:todo_id>", methods=["POST"])
@login_required
def delete(todo_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "DELETE FROM todos WHERE todo_id = %s AND user_id = %s",
            (todo_id, session["user_id"]),
        )
    db.commit()
    return redirect(url_for("index"))


@app.errorhandler(404)
def not_found(_e):
    return render_template("error.html", message="Page not found"), 404


@app.errorhandler(500)
def server_error(_e):
    return render_template("error.html", message="Something went wrong. Please try again."), 500


if __name__ == "__main__":
    app.run(debug=False)
