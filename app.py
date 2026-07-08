import os
import re
import sqlite3
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, g, abort, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

DB_PATH = os.environ.get("DB_PATH", "data/app.db")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme")

SCHEMA = """
CREATE TABLE IF NOT EXISTS people (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL,
    sender_name TEXT,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (person_id) REFERENCES people (id)
);
"""


def get_db():
    if "db" not in g:
        os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def slugify(name):
    slug = name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug or "member"


def unique_slug(db, name):
    base = slugify(name)
    slug = base
    n = 2
    while db.execute("SELECT 1 FROM people WHERE slug = ?", (slug,)).fetchone():
        slug = f"{base}-{n}"
        n += 1
    return slug


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


# ---------- public routes ----------

@app.route("/")
def index():
    db = get_db()
    people = db.execute(
        """SELECT p.*, COUNT(m.id) as msg_count
           FROM people p LEFT JOIN messages m ON m.person_id = p.id
           GROUP BY p.id ORDER BY p.name COLLATE NOCASE ASC"""
    ).fetchall()
    return render_template("index.html", people=people)


@app.route("/p/<slug>", methods=["GET"])
def person(slug):
    db = get_db()
    person = db.execute("SELECT * FROM people WHERE slug = ?", (slug,)).fetchone()
    if not person:
        abort(404)
    messages = db.execute(
        "SELECT * FROM messages WHERE person_id = ? ORDER BY id DESC", (person["id"],)
    ).fetchall()
    return render_template("person.html", person=person, messages=messages)


@app.route("/p/<slug>/message", methods=["POST"])
def send_message(slug):
    db = get_db()
    person = db.execute("SELECT * FROM people WHERE slug = ?", (slug,)).fetchone()
    if not person:
        abort(404)

    content = (request.form.get("content") or "").strip()
    is_anon = request.form.get("is_anon") == "on"
    sender_name = (request.form.get("sender_name") or "").strip()

    if not content:
        flash("Message can't be empty.", "error")
        return redirect(url_for("person", slug=slug))

    if is_anon or not sender_name:
        sender_name = None

    db.execute(
        "INSERT INTO messages (person_id, sender_name, content, created_at) VALUES (?, ?, ?, ?)",
        (person["id"], sender_name, content, datetime.utcnow().isoformat()),
    )
    db.commit()
    flash("Message sent.", "success")
    return redirect(url_for("person", slug=slug))


# ---------- admin routes ----------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["is_admin"] = True
            next_url = request.form.get("next") or url_for("admin")
            return redirect(next_url)
        flash("Wrong password.", "error")
    return render_template("admin_login.html", next=request.args.get("next", ""))


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("index"))


@app.route("/admin")
@login_required
def admin():
    db = get_db()
    people = db.execute(
        """SELECT p.*, COUNT(m.id) as msg_count
           FROM people p LEFT JOIN messages m ON m.person_id = p.id
           GROUP BY p.id ORDER BY p.name COLLATE NOCASE ASC"""
    ).fetchall()
    recent_messages = db.execute(
        """SELECT m.*, p.name as person_name, p.slug as person_slug
           FROM messages m JOIN people p ON p.id = m.person_id
           ORDER BY m.id DESC LIMIT 50"""
    ).fetchall()
    return render_template("admin.html", people=people, recent_messages=recent_messages)


@app.route("/admin/people/add", methods=["POST"])
@login_required
def add_person():
    db = get_db()
    name = (request.form.get("name") or "").strip()
    if not name:
        flash("Name can't be empty.", "error")
        return redirect(url_for("admin"))
    slug = unique_slug(db, name)
    db.execute(
        "INSERT INTO people (name, slug, created_at) VALUES (?, ?, ?)",
        (name, slug, datetime.utcnow().isoformat()),
    )
    db.commit()
    flash(f"Added {name}.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/people/<int:person_id>/delete", methods=["POST"])
@login_required
def delete_person(person_id):
    db = get_db()
    db.execute("DELETE FROM messages WHERE person_id = ?", (person_id,))
    db.execute("DELETE FROM people WHERE id = ?", (person_id,))
    db.commit()
    flash("Removed.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/messages/<int:message_id>/delete", methods=["POST"])
@login_required
def delete_message(message_id):
    db = get_db()
    db.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    db.commit()
    flash("Message removed.", "success")
    return redirect(url_for("admin"))


init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
