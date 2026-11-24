import hashlib
import hmac
import os
import secrets
import sqlite3
from contextlib import closing
from datetime import date, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "finance.db")

INCOME_CATEGORIES = ["Salary", "Freelance", "Investment", "Other"]
EXPENSE_CATEGORIES = ["Housing", "Food", "Transport", "Utilities", "Entertainment", "Other"]
PAYMENT_METHODS = ["Cash", "Card", "Bank"]
DEMO_USERNAME = "demo_guest"
DEFAULT_CURRENCY = "৳"


# Low-level helpers
def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _query(sql, params=()):
    with closing(_connect()) as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def _one(sql, params=()):
    rows = _query(sql, params)
    return rows[0] if rows else None


def _run(sql, params=()):
    with closing(_connect()) as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid


# Schema + seeding
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL DEFAULT '',
    salt          TEXT NOT NULL DEFAULT '',
    display_name  TEXT NOT NULL DEFAULT '',
    email         TEXT NOT NULL DEFAULT '',
    is_demo       INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS incomes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount      REAL NOT NULL,
    category    TEXT NOT NULL,
    date        TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS expenses (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount         REAL NOT NULL,
    category       TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    date           TEXT NOT NULL,
    notes          TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS budgets (
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category     TEXT NOT NULL,
    limit_amount REAL NOT NULL,
    PRIMARY KEY (user_id, category)
);
CREATE TABLE IF NOT EXISTS goals (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name          TEXT NOT NULL,
    target_amount REAL NOT NULL,
    saved_amount  REAL NOT NULL DEFAULT 0,
    target_date   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key     TEXT NOT NULL,
    value   TEXT NOT NULL,
    PRIMARY KEY (user_id, key)
);
"""


def init_db():
    """Create tables and seed the demo (guest) account if it is empty."""
    with closing(_connect()) as conn:
        conn.executescript(SCHEMA)
        conn.commit()
    demo = get_demo_user()
    if demo is None:
        _run("INSERT INTO users(username, display_name, is_demo) VALUES(?, 'Guest', 1)",
             (DEMO_USERNAME,))
        demo = get_demo_user()
    empty = not (_one("SELECT 1 AS x FROM incomes WHERE user_id=? LIMIT 1", (demo["id"],))
                 or _one("SELECT 1 AS x FROM expenses WHERE user_id=? LIMIT 1", (demo["id"],))
                 or _one("SELECT 1 AS x FROM goals WHERE user_id=? LIMIT 1", (demo["id"],)))
    if empty:
        seed_demo_data(demo["id"])


def _month_date(months_back, day):
    today = date.today()
    year, month = today.year, today.month - months_back
    while month < 1:
        month += 12
        year -= 1
    if months_back == 0:
        day = min(day, today.day)
    return date(year, month, min(day, 28)).isoformat()


def seed_demo_data(user_id):
    incomes, expenses = [], []
    freelance = {2: (12000, 12, "Website project"), 1: (8500, 18, "Logo design"),
                 0: (15000, 6, "App UI mockups")}
    invest = {2: (3200, 20, "Dividend payout"), 0: (2800, 5, "Mutual fund return")}
    base = [
        (1, 15000, "Housing", "Bank", "Monthly rent"),
        (2, 1850, "Food", "Cash", "Weekly groceries"),
        (3, 600, "Transport", "Card", "Ride-sharing"),
        (4, 2400, "Utilities", "Bank", "Electricity & gas bill"),
        (5, 1200, "Utilities", "Bank", "Internet bill"),
        (6, 1200, "Food", "Card", "Dinner with friends"),
        (7, 900, "Transport", "Cash", "Monthly bus pass"),
        (8, 700, "Other", "Cash", "Pharmacy"),
        (9, 1500, "Food", "Cash", "Weekly groceries"),
        (10, 800, "Entertainment", "Card", "Movie night"),
    ]
    extras = {
        2: [(14, 1500, "Entertainment", "Card", "Streaming & games")],
        1: [(15, 2200, "Other", "Bank", "Family gift")],
        0: [(5, 2600, "Entertainment", "Card", "Concert tickets")],
    }
    factor = {2: 0.93, 1: 1.04, 0: 1.0}
    for back in (2, 1, 0):
        incomes.append((user_id, 55000, "Salary", _month_date(back, 1), "Monthly salary"))
        amt, day, desc = freelance[back]
        incomes.append((user_id, amt, "Freelance", _month_date(back, day), desc))
        if back in invest:
            amt, day, desc = invest[back]
            incomes.append((user_id, amt, "Investment", _month_date(back, day), desc))
        for day, amt, cat, method, note in base + extras[back]:
            expenses.append((user_id, round(amt * factor[back], 2), cat, method,
                             _month_date(back, day), note))
    incomes.append((user_id, 2500, "Other", _month_date(1, 25), "Sold old phone"))

    budgets = [(user_id, "Housing", 16000), (user_id, "Food", 9000), (user_id, "Transport", 4000),
               (user_id, "Utilities", 5000), (user_id, "Entertainment", 3000),
               (user_id, "Other", 3000)]
    today = date.today()
    goals = [
        (user_id, "Emergency Fund", 100000, 42000, (today + timedelta(days=180)).isoformat()),
        (user_id, "New Laptop", 90000, 31500, (today + timedelta(days=120)).isoformat()),
        (user_id, "Vacation", 60000, 12000, (today + timedelta(days=300)).isoformat()),
    ]
    with closing(_connect()) as conn:
        for table in ("incomes", "expenses", "budgets", "goals"):
            conn.execute(f"DELETE FROM {table} WHERE user_id=?", (user_id,))
        conn.executemany("INSERT INTO incomes(user_id, amount, category, date, description) "
                         "VALUES(?,?,?,?,?)", incomes)
        conn.executemany("INSERT INTO expenses(user_id, amount, category, payment_method, date, notes) "
                         "VALUES(?,?,?,?,?,?)", expenses)
        conn.executemany("INSERT INTO budgets(user_id, category, limit_amount) VALUES(?,?,?)", budgets)
        conn.executemany("INSERT INTO goals(user_id, name, target_amount, saved_amount, target_date) "
                         "VALUES(?,?,?,?,?)", goals)
        conn.execute("INSERT OR REPLACE INTO settings(user_id, key, value) VALUES(?, 'currency', ?)",
                     (user_id, DEFAULT_CURRENCY))
        conn.commit()


def reset_to_demo(user_id):
    seed_demo_data(user_id)


# Users
def _hash(password, salt_hex):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                               bytes.fromhex(salt_hex), 120_000).hex()


def create_user(username, password):
    salt = secrets.token_hex(16)
    try:
        return _run("INSERT INTO users(username, password_hash, salt, display_name) VALUES(?,?,?,?)",
                    (username, _hash(password, salt), salt, username))
    except sqlite3.IntegrityError:
        raise ValueError("That username is already taken.")


def authenticate(username, password):
    row = _one("SELECT * FROM users WHERE username=? AND is_demo=0", (username,))
    if row and hmac.compare_digest(row["password_hash"], _hash(password, row["salt"])):
        return row
    return None


def get_user(user_id):
    return _one("SELECT * FROM users WHERE id=?", (user_id,))


def get_demo_user():
    return _one("SELECT * FROM users WHERE is_demo=1")


def update_profile(user_id, display_name, email):
    _run("UPDATE users SET display_name=?, email=? WHERE id=?", (display_name, email, user_id))



# Settings
def get_setting(user_id, key, default=None):
    row = _one("SELECT value FROM settings WHERE user_id=? AND key=?", (user_id, key))
    return row["value"] if row else default


def set_setting(user_id, key, value):
    _run("INSERT OR REPLACE INTO settings(user_id, key, value) VALUES(?,?,?)", (user_id, key, value))


# Incomes
def add_income(user_id, amount, category, date_str, description):
    return _run("INSERT INTO incomes(user_id, amount, category, date, description) VALUES(?,?,?,?,?)",
                (user_id, amount, category, date_str, description))


def update_income(income_id, user_id, amount, category, date_str, description):
    _run("UPDATE incomes SET amount=?, category=?, date=?, description=? WHERE id=? AND user_id=?",
         (amount, category, date_str, description, income_id, user_id))


def delete_income(income_id, user_id):
    _run("DELETE FROM incomes WHERE id=? AND user_id=?", (income_id, user_id))


def get_incomes(user_id):
    return _query("SELECT * FROM incomes WHERE user_id=? ORDER BY date DESC, id DESC", (user_id,))



# Expenses
def add_expense(user_id, amount, category, method, date_str, notes):
    return _run("INSERT INTO expenses(user_id, amount, category, payment_method, date, notes) "
                "VALUES(?,?,?,?,?,?)", (user_id, amount, category, method, date_str, notes))


def update_expense(expense_id, user_id, amount, category, method, date_str, notes):
    _run("UPDATE expenses SET amount=?, category=?, payment_method=?, date=?, notes=? "
         "WHERE id=? AND user_id=?", (amount, category, method, date_str, notes, expense_id, user_id))


def delete_expense(expense_id, user_id):
    _run("DELETE FROM expenses WHERE id=? AND user_id=?", (expense_id, user_id))


def get_expenses(user_id):
    return _query("SELECT * FROM expenses WHERE user_id=? ORDER BY date DESC, id DESC", (user_id,))



# Budgets
def set_budget(user_id, category, limit_amount):
    _run("INSERT OR REPLACE INTO budgets(user_id, category, limit_amount) VALUES(?,?,?)",
         (user_id, category, limit_amount))


def delete_budget(user_id, category):
    _run("DELETE FROM budgets WHERE user_id=? AND category=?", (user_id, category))


def get_budgets(user_id):
    return {r["category"]: r["limit_amount"]
            for r in _query("SELECT category, limit_amount FROM budgets WHERE user_id=?", (user_id,))}


def get_month_spending(user_id, year, month):
    rows = _query("SELECT category, SUM(amount) AS total FROM expenses "
                  "WHERE user_id=? AND strftime('%Y-%m', date)=? GROUP BY category",
                  (user_id, f"{year:04d}-{month:02d}"))
    return {r["category"]: r["total"] for r in rows}


# Savings goals
def add_goal(user_id, name, target_amount, target_date):
    return _run("INSERT INTO goals(user_id, name, target_amount, saved_amount, target_date) "
                "VALUES(?,?,?,0,?)", (user_id, name, target_amount, target_date))


def get_goals(user_id):
    return _query("SELECT * FROM goals WHERE user_id=? ORDER BY target_date, id", (user_id,))


def add_deposit(goal_id, user_id, amount):
    _run("UPDATE goals SET saved_amount = saved_amount + ? WHERE id=? AND user_id=?",
         (amount, goal_id, user_id))


def delete_goal(goal_id, user_id):
    _run("DELETE FROM goals WHERE id=? AND user_id=?", (goal_id, user_id))



# Combined views / totals
def get_transactions(user_id):
    rows = []
    for r in get_incomes(user_id):
        rows.append({"id": f"INC-{r['id']}", "type": "Income", "category": r["category"],
                     "amount": r["amount"], "date": r["date"],
                     "description": r["description"], "method": ""})
    for r in get_expenses(user_id):
        rows.append({"id": f"EXP-{r['id']}", "type": "Expense", "category": r["category"],
                     "amount": r["amount"], "date": r["date"],
                     "description": r["notes"], "method": r["payment_method"]})
    rows.sort(key=lambda t: (t["date"], t["id"]), reverse=True)
    return rows


def get_totals(user_id):
    inc = _one("SELECT COALESCE(SUM(amount), 0) AS t FROM incomes WHERE user_id=?", (user_id,))["t"]
    exp = _one("SELECT COALESCE(SUM(amount), 0) AS t FROM expenses WHERE user_id=?", (user_id,))["t"]
    return inc, exp


def expense_by_category(user_id):
    rows = _query("SELECT category, SUM(amount) AS total FROM expenses WHERE user_id=? "
                  "GROUP BY category ORDER BY total DESC", (user_id,))
    return {r["category"]: r["total"] for r in rows}
