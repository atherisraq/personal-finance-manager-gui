import tkinter as tk
from tkinter import messagebox, ttk

import database as db
from utils import fmt, parse_amount, parse_date, today_str
from views.widgets import fill_tree, make_tree, summary_card


class ExpenseView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=18)
        self.app = app
        self.editing_id = None
        self.records = {}

        ttk.Label(self, text="Expense Management", style="Title.TLabel").pack(anchor="w")
        card, self.total_var = summary_card(self, "Total Expenditure", "CardValueBad.TLabel")
        card.pack(fill="x", pady=(10, 10))

        form = ttk.LabelFrame(self, text=" Record Expense ", padding=12)
        form.pack(fill="x")
        self.amount = tk.StringVar()
        self.category = tk.StringVar(value=db.EXPENSE_CATEGORIES[0])
        self.method = tk.StringVar(value=db.PAYMENT_METHODS[0])
        self.date = tk.StringVar(value=today_str())
        self.notes = tk.StringVar()

        heads = ("Amount", "Category", "Payment Method", "Date (YYYY-MM-DD)", "Notes")
        for col, text in enumerate(heads):
            ttk.Label(form, text=text).grid(row=0, column=col, sticky="w")
        ttk.Entry(form, textvariable=self.amount, width=12).grid(row=1, column=0, padx=(0, 10))
        ttk.Combobox(form, textvariable=self.category, values=db.EXPENSE_CATEGORIES, state="readonly",
                     width=13).grid(row=1, column=1, padx=(0, 10))
        ttk.Combobox(form, textvariable=self.method, values=db.PAYMENT_METHODS, state="readonly",
                     width=10).grid(row=1, column=2, padx=(0, 10))
        ttk.Entry(form, textvariable=self.date, width=14).grid(row=1, column=3, padx=(0, 10))
        ttk.Entry(form, textvariable=self.notes).grid(row=1, column=4, sticky="ew", padx=(0, 10))
        form.columnconfigure(4, weight=1)
        self.save_btn = ttk.Button(form, text="Add Expense", style="Accent.TButton", command=self.save)
        self.save_btn.grid(row=1, column=5)
        self.cancel_btn = ttk.Button(form, text="Cancel", command=self.reset_form)
        self.cancel_btn.grid(row=1, column=6, padx=(6, 0))
        self.cancel_btn.grid_remove()

        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(12, 6))
        ttk.Label(actions, text="All expenses", style="Muted.TLabel").pack(side="left")
        ttk.Button(actions, text="Delete Selected", style="Danger.TButton",
                   command=self.delete_selected).pack(side="right")
        ttk.Button(actions, text="Edit Selected", command=self.edit_selected).pack(side="right", padx=6)

        table, self.tree = make_tree(self, [
            ("date", "Date", 100, "w"), ("category", "Category", 110, "w"),
            ("method", "Payment", 90, "w"), ("notes", "Notes", 300, "w"),
            ("amount", "Amount", 120, "e")])
        table.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda _e: self.edit_selected())

    def refresh(self):
        rows = db.get_expenses(self.app.user_id)
        self.records = {r["id"]: r for r in rows}
        fill_tree(self.tree, [(r["id"], (r["date"], r["category"], r["payment_method"], r["notes"],
                                         fmt(r["amount"]))) for r in rows])
        self.total_var.set(fmt(sum(r["amount"] for r in rows)))

    def reset_form(self):
        self.editing_id = None
        self.amount.set("")
        self.notes.set("")
        self.date.set(today_str())
        self.category.set(db.EXPENSE_CATEGORIES[0])
        self.method.set(db.PAYMENT_METHODS[0])
        self.save_btn.configure(text="Add Expense")
        self.cancel_btn.grid_remove()

    def save(self):
        try:
            amount = parse_amount(self.amount.get())
            date_str = parse_date(self.date.get())
        except ValueError as exc:
            messagebox.showwarning("Invalid input", str(exc), parent=self)
            return
        args = (amount, self.category.get(), self.method.get(), date_str, self.notes.get().strip())
        if self.editing_id is None:
            db.add_expense(self.app.user_id, *args)
        else:
            db.update_expense(self.editing_id, self.app.user_id, *args)
        self.reset_form()
        self.refresh()

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select an entry", "Please select an expense first.", parent=self)
            return None
        return int(sel[0])

    def edit_selected(self):
        rid = self._selected_id()
        if rid is None:
            return
        rec = self.records[rid]
        self.editing_id = rid
        self.amount.set(f"{rec['amount']:.2f}")
        self.category.set(rec["category"])
        self.method.set(rec["payment_method"])
        self.date.set(rec["date"])
        self.notes.set(rec["notes"])
        self.save_btn.configure(text="Update Expense")
        self.cancel_btn.grid()

    def delete_selected(self):
        rid = self._selected_id()
        if rid is None:
            return
        if messagebox.askyesno("Delete expense", "Delete the selected expense?", parent=self):
            db.delete_expense(rid, self.app.user_id)
            if self.editing_id == rid:
                self.reset_form()
            self.refresh()
