import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

import database as db
from utils import fmt, parse_amount
from views.widgets import ScrollableFrame


class BudgetView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=18)
        self.app = app
        ttk.Label(self, text="Budget Management", style="Title.TLabel").pack(anchor="w")
        self.month_label = ttk.Label(self, style="Muted.TLabel")
        self.month_label.pack(anchor="w", pady=(0, 10))

        form = ttk.LabelFrame(self, text=" Set Monthly Limit ", padding=12)
        form.pack(fill="x")
        self.category = tk.StringVar(value=db.EXPENSE_CATEGORIES[0])
        self.limit = tk.StringVar()
        ttk.Label(form, text="Category").grid(row=0, column=0, sticky="w")
        ttk.Label(form, text="Monthly limit").grid(row=0, column=1, sticky="w")
        combo = ttk.Combobox(form, textvariable=self.category, values=db.EXPENSE_CATEGORIES,
                             state="readonly", width=16)
        combo.grid(row=1, column=0, padx=(0, 10))
        combo.bind("<<ComboboxSelected>>", self._prefill)
        entry = ttk.Entry(form, textvariable=self.limit, width=16)
        entry.grid(row=1, column=1, padx=(0, 10))
        entry.bind("<Return>", lambda _e: self.save())
        ttk.Button(form, text="Set Budget", style="Accent.TButton", command=self.save).grid(row=1, column=2)

        ttk.Label(self, text="Green: under 80%   |   Orange: 80% or more   |   Red: 100% or more",
                  style="Muted.TLabel").pack(anchor="w", pady=(10, 4))
        self.scroll = ScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True)

    def _prefill(self, _event=None):
        current = db.get_budgets(self.app.user_id).get(self.category.get())
        self.limit.set(f"{current:.2f}" if current else "")

    def save(self):
        try:
            value = parse_amount(self.limit.get())
        except ValueError as exc:
            messagebox.showwarning("Invalid input", str(exc), parent=self)
            return
        db.set_budget(self.app.user_id, self.category.get(), value)
        self.limit.set("")
        self.refresh()

    def remove(self, category):
        if messagebox.askyesno("Remove limit", f"Remove the {category} budget limit?", parent=self):
            db.delete_budget(self.app.user_id, category)
            self.refresh()

    def refresh(self):
        today = date.today()
        self.month_label.configure(text=f"Limits apply per month. Showing spending for {today:%B %Y}.")
        budgets = db.get_budgets(self.app.user_id)
        spent = db.get_month_spending(self.app.user_id, today.year, today.month)
        self.scroll.clear()
        for cat in db.EXPENSE_CATEGORIES:
            limit, used = budgets.get(cat), spent.get(cat, 0.0)
            row = ttk.Frame(self.scroll.inner, style="Card.TFrame", padding=12)
            row.pack(fill="x", pady=4, padx=(0, 6))
            top = ttk.Frame(row, style="Card.TFrame")
            top.pack(fill="x")
            ttk.Label(top, text=cat, style="CardHeading.TLabel").pack(side="left")
            if limit:
                pct = used / limit * 100
                if pct >= 100:
                    bar_style, st_style, status = "Red", "StatusDanger.TLabel", f"Over budget ({pct:.0f}%)"
                elif pct >= 80:
                    bar_style, st_style, status = "Orange", "StatusWarn.TLabel", f"Warning ({pct:.0f}% used)"
                else:
                    bar_style, st_style, status = "Green", "StatusOk.TLabel", f"On track ({pct:.0f}% used)"
                remaining = limit - used
                rem_text = (f"Remaining {fmt(remaining)}" if remaining >= 0
                            else f"Over by {fmt(-remaining)}")
                detail = f"Limit {fmt(limit)}   |   Spent {fmt(used)}   |   {rem_text}"
                ttk.Button(top, text="Remove", command=lambda c=cat: self.remove(c)).pack(side="right")
                ttk.Label(top, text=status, style=st_style).pack(side="right", padx=12)
                value = min(pct, 100)
            else:
                bar_style, value = "Green", 0
                detail = f"No limit set   |   Spent {fmt(used)}"
            ttk.Label(row, text=detail, style="CardMuted.TLabel").pack(anchor="w", pady=(4, 6))
            ttk.Progressbar(row, maximum=100, value=value,
                            style=f"{bar_style}.Horizontal.TProgressbar").pack(fill="x")
        self._prefill()
