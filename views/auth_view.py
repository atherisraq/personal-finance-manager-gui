import tkinter as tk
from tkinter import ttk

import database as db


class AuthView(ttk.Frame):
    def __init__(self, parent, on_login):
        super().__init__(parent)
        self.on_login = on_login
        self.mode = "login"
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.confirm = tk.StringVar()
        self.error = tk.StringVar()

        card = ttk.Frame(self, style="Card.TFrame", padding=36)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.columnconfigure(0, weight=1)

        ttk.Label(card, text="Personal Finance Manager", style="AuthTitle.TLabel").grid(row=0, column=0)
        self.subtitle = ttk.Label(card, text="Sign in to continue", style="CardMuted.TLabel")
        self.subtitle.grid(row=1, column=0, pady=(2, 18))

        ttk.Label(card, text="Username", style="CardText.TLabel").grid(row=2, column=0, sticky="w")
        self.user_entry = ttk.Entry(card, textvariable=self.username, width=34)
        self.user_entry.grid(row=3, column=0, sticky="ew", pady=(2, 10))

        ttk.Label(card, text="Password", style="CardText.TLabel").grid(row=4, column=0, sticky="w")
        self.pass_entry = ttk.Entry(card, textvariable=self.password, show="*", width=34)
        self.pass_entry.grid(row=5, column=0, sticky="ew", pady=(2, 10))

        self.confirm_label = ttk.Label(card, text="Confirm password", style="CardText.TLabel")
        self.confirm_label.grid(row=6, column=0, sticky="w")
        self.confirm_entry = ttk.Entry(card, textvariable=self.confirm, show="*", width=34)
        self.confirm_entry.grid(row=7, column=0, sticky="ew", pady=(2, 10))

        ttk.Label(card, textvariable=self.error, style="StatusDanger.TLabel",
                  wraplength=280).grid(row=8, column=0, sticky="w")
        self.primary = ttk.Button(card, text="Login", style="Accent.TButton", command=self.submit)
        self.primary.grid(row=9, column=0, sticky="ew", pady=(8, 4))
        self.toggle = ttk.Button(card, text="No account? Register", style="Link.TButton",
                                 command=self.switch_mode)
        self.toggle.grid(row=10, column=0)
        ttk.Separator(card).grid(row=11, column=0, sticky="ew", pady=12)
        ttk.Button(card, text="Continue as Guest (Demo Mode)",
                   command=self.guest).grid(row=12, column=0, sticky="ew")

        for entry in (self.user_entry, self.pass_entry, self.confirm_entry):
            entry.bind("<Return>", lambda _e: self.submit())
        self._apply_mode()
        self.user_entry.focus_set()

    def _apply_mode(self):
        register = self.mode == "register"
        for w in (self.confirm_label, self.confirm_entry):
            w.grid() if register else w.grid_remove()
        self.subtitle.configure(text="Create your account" if register else "Sign in to continue")
        self.primary.configure(text="Create Account" if register else "Login")
        self.toggle.configure(text="Have an account? Login" if register else "No account? Register")
        self.error.set("")

    def switch_mode(self):
        self.mode = "register" if self.mode == "login" else "login"
        self.password.set("")
        self.confirm.set("")
        self._apply_mode()

    def submit(self):
        user, pw = self.username.get().strip(), self.password.get()
        if not user or not pw:
            self.error.set("Username and password are required.")
            return
        if self.mode == "login":
            row = db.authenticate(user, pw)
            if row is None:
                self.error.set("Incorrect username or password.")
                return
            self.on_login(row)
            return
        if len(user) < 3:
            self.error.set("Username must be at least 3 characters.")
        elif len(pw) < 4:
            self.error.set("Password must be at least 4 characters.")
        elif pw != self.confirm.get():
            self.error.set("Passwords do not match.")
        else:
            try:
                uid = db.create_user(user, pw)
            except ValueError as exc:
                self.error.set(str(exc))
                return
            self.on_login(db.get_user(uid))

    def guest(self):
        self.on_login(db.get_demo_user())
