"""Personal Finance Manager - entry point and main window.

Run with:  python main.py
"""
import tkinter as tk
from tkinter import messagebox, ttk

import database as db
import utils
from theme import setup_styles
from views.auth_view import AuthView
from views.budget_view import BudgetView
from views.expense_view import ExpenseView
from views.history_view import HistoryView
from views.income_view import IncomeView
from views.profile_view import ProfileView
from views.reports_view import ReportsView
from views.savings_view import SavingsView

NAV_ITEMS = [
    ("Income Management", "income", IncomeView),
    ("Expense Management", "expense", ExpenseView),
    ("Budget Management", "budget", BudgetView),
    ("Savings Management", "savings", SavingsView),
    ("Transaction History & Search", "history", HistoryView),
    ("Financial Reports", "reports", ReportsView),
    ("Profile & Settings", "profile", ProfileView),
]


class App:
    def __init__(self, root):
        self.root = root
        root.title("Personal Finance Manager")
        root.geometry("1180x720")
        root.minsize(1000, 640)
        setup_styles(root)
        db.init_db()

        self.user = None
        self.views, self.nav_buttons = {}, {}
        self.container = ttk.Frame(root)
        self.container.pack(fill="both", expand=True)
        root.protocol("WM_DELETE_WINDOW", self.exit_app)
        self.show_auth()

    @property
    def user_id(self):
        return self.user["id"]

    def _clear(self):
        for child in self.container.winfo_children():
            child.destroy()
        self.views.clear()
        self.nav_buttons.clear()

    # ---- screens ---------------------------------------------------------- #
    def show_auth(self):
        self._clear()
        self.user = None
        AuthView(self.container, self.login).pack(fill="both", expand=True)

    def login(self, user):
        self.user = user
        utils.set_currency(db.get_setting(user["id"], "currency", db.DEFAULT_CURRENCY))
        self.build_main()

    def logout(self):
        if messagebox.askyesno("Log out", "Log out of your account?", parent=self.root):
            self.show_auth()

    def build_main(self):
        self._clear()
        side = ttk.Frame(self.container, style="Sidebar.TFrame", width=260)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        ttk.Label(side, text="Personal Finance\nManager", style="SidebarTitle.TLabel").pack(
            anchor="w", padx=20, pady=(24, 4))
        self.user_label = ttk.Label(side, style="SidebarUser.TLabel")
        self.user_label.pack(anchor="w", padx=20, pady=(0, 20))
        self.update_user_label()

        content = ttk.Frame(self.container)
        content.pack(side="right", fill="both", expand=True)
        content.rowconfigure(0, weight=1)
        content.columnconfigure(0, weight=1)

        for label, key, cls in NAV_ITEMS:
            view = cls(content, self)
            view.grid(row=0, column=0, sticky="nsew")
            self.views[key] = view
            btn = ttk.Button(side, text=label, style="Nav.TButton", command=lambda k=key: self.show_view(k))
            btn.pack(fill="x")
            self.nav_buttons[key] = btn
        ttk.Button(side, text="Exit", style="Nav.TButton", command=self.exit_app).pack(fill="x")
        self.show_view("income")

    def show_view(self, key):
        for k, btn in self.nav_buttons.items():
            btn.configure(style="NavActive.TButton" if k == key else "Nav.TButton")
        self.views[key].refresh()
        self.views[key].tkraise()

    # ---- shared actions --------------------------------------------------- #
    def refresh_all(self):
        for view in self.views.values():
            view.refresh()

    def set_currency(self, symbol):
        utils.set_currency(symbol)
        db.set_setting(self.user_id, "currency", utils.get_currency())
        self.refresh_all()

    def reload_user(self):
        self.user = db.get_user(self.user_id)
        self.update_user_label()

    def update_user_label(self):
        self.user_label.configure(text=f"Signed in as {self.user['display_name'] or self.user['username']}")

    def exit_app(self):
        if messagebox.askyesno("Exit", "Are you sure you want to exit Personal Finance Manager?",
                               parent=self.root):
            self.root.destroy()


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
