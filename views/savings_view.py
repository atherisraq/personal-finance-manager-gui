"""Savings Management: goals, progress and deposits."""
import tkinter as tk
from datetime import date, timedelta
from tkinter import messagebox, simpledialog, ttk

import database as db
from utils import get_currency, fmt, parse_amount, parse_date
from views.widgets import ScrollableFrame


class SavingsView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=18)
        self.app = app
        ttk.Label(self, text="Savings Management", style="Title.TLabel").pack(anchor="w", pady=(0, 10))

        form = ttk.LabelFrame(self, text=" New Savings Goal ", padding=12)
        form.pack(fill="x")
        self.name = tk.StringVar()
        self.target = tk.StringVar()
        self.target_date = tk.StringVar(value=(date.today() + timedelta(days=180)).isoformat())
        for col, text in enumerate(("Goal name", "Target amount", "Target date (YYYY-MM-DD)")):
            ttk.Label(form, text=text).grid(row=0, column=col, sticky="w")
        ttk.Entry(form, textvariable=self.name).grid(row=1, column=0, sticky="ew", padx=(0, 10))
        ttk.Entry(form, textvariable=self.target, width=16).grid(row=1, column=1, padx=(0, 10))
        ttk.Entry(form, textvariable=self.target_date, width=18).grid(row=1, column=2, padx=(0, 10))
        form.columnconfigure(0, weight=1)
        ttk.Button(form, text="Create Goal", style="Accent.TButton", command=self.create_goal).grid(row=1, column=3)

        self.scroll = ScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, pady=(12, 0))

    def create_goal(self):
        name = self.name.get().strip()
        if not name:
            messagebox.showwarning("Invalid input", "Please enter a goal name.", parent=self)
            return
        try:
            target = parse_amount(self.target.get())
            when = parse_date(self.target_date.get())
        except ValueError as exc:
            messagebox.showwarning("Invalid input", str(exc), parent=self)
            return
        if when < date.today().isoformat():
            messagebox.showwarning("Invalid input", "Target date cannot be in the past.", parent=self)
            return
        db.add_goal(self.app.user_id, name, target, when)
        self.name.set("")
        self.target.set("")
        self.refresh()

    def add_deposit(self, goal):
        amount = simpledialog.askfloat(
            "Add Deposit", f"Amount to deposit into '{goal['name']}' ({get_currency()}):",
            parent=self, minvalue=0.01, maxvalue=1e12)
        if amount is None:
            return
        db.add_deposit(goal["id"], self.app.user_id, round(amount, 2))
        self.refresh()

    def delete_goal(self, goal):
        if messagebox.askyesno("Delete goal", f"Delete the goal '{goal['name']}'?", parent=self):
            db.delete_goal(goal["id"], self.app.user_id)
            self.refresh()

    def refresh(self):
        self.scroll.clear()
        goals = db.get_goals(self.app.user_id)
        if not goals:
            ttk.Label(self.scroll.inner, text="No savings goals yet. Create one above.",
                      style="Muted.TLabel").pack(pady=20)
            return
        for g in goals:
            pct = g["saved_amount"] / g["target_amount"] * 100 if g["target_amount"] else 0
            days = (date.fromisoformat(g["target_date"]) - date.today()).days
            if pct >= 100:
                when_text = "Goal reached!"
            elif days < 0:
                when_text = f"Target date passed ({g['target_date']})"
            else:
                when_text = f"Target date {g['target_date']} ({days} days left)"
            card = ttk.Frame(self.scroll.inner, style="Card.TFrame", padding=14)
            card.pack(fill="x", pady=5, padx=(0, 6))
            top = ttk.Frame(card, style="Card.TFrame")
            top.pack(fill="x")
            ttk.Label(top, text=g["name"], style="CardHeading.TLabel").pack(side="left")
            ttk.Button(top, text="Delete", command=lambda x=g: self.delete_goal(x)).pack(side="right")
            ttk.Button(top, text="+ Add Deposit", style="Accent.TButton",
                       command=lambda x=g: self.add_deposit(x)).pack(side="right", padx=6)
            ttk.Label(card, text=when_text, style="CardMuted.TLabel").pack(anchor="w")
            ttk.Label(card, style="CardText.TLabel",
                      text=f"Target {fmt(g['target_amount'])}   |   Saved {fmt(g['saved_amount'])}   |   "
                           f"Progress {pct:.1f}%").pack(anchor="w", pady=(6, 6))
            ttk.Progressbar(card, maximum=100, value=min(pct, 100),
                            style="Green.Horizontal.TProgressbar").pack(fill="x")
