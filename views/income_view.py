import tkinter as tk
from tkinter import messagebox, ttk

import database as db
from utils import fmt, parse_amount, parse_date, today_str
from views.widgets import fill_tree, make_tree, summary_card


class IncomeView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=18)
        self.app = app
        self.editing_id = None
        self.records = {}

        ttk.Label(self, text="Income Management", style="Title.TLabel").pack(anchor="w")
        card, self.total_var = summary_card(self, "Total Income", "CardValueGood.TLabel")
        card.pack(fill="x", pady=(10, 10))

        form = ttk.LabelFrame(self, text=" Record Income ", padding=12)
        form.pack(fill="x")
        self.amount = tk.StringVar()
        self.category = tk.StringVar(value=db.INCOME_CATEGORIES[0])
        self.date = tk.StringVar(value=today_str())
        self.desc = tk.StringVar()

        for col, text in enumerate(("Amount", "Source / Category", "Date (YYYY-MM-DD)", "Description")):
            ttk.Label(form, text=text).grid(row=0, column=col, sticky="w")
        ttk.Entry(form, textvariable=self.amount, width=14).grid(row=1, column=0, padx=(0, 10))
        ttk.Combobox(form, textvariable=self.category, values=db.INCOME_CATEGORIES, state="readonly",
                     width=14).grid(row=1, column=1, padx=(0, 10))
        ttk.Entry(form, textvariable=self.date, width=16).grid(row=1, column=2, padx=(0, 10))
        ttk.Entry(form, textvariable=self.desc).grid(row=1, column=3, sticky="ew", padx=(0, 10))
        form.columnconfigure(3, weight=1)
        self.save_btn = ttk.Button(form, text="Add Income", style="Accent.TButton", command=self.save)
        self.save_btn.grid(row=1, column=4)
        self.cancel_btn = ttk.Button(form, text="Cancel", command=self.reset_form)
        self.cancel_btn.grid(row=1, column=5, padx=(6, 0))
        self.cancel_btn.grid_remove()

        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(12, 6))
        ttk.Label(actions, text="All income", style="Muted.TLabel").pack(side="left")
        ttk.Button(actions, text="Delete Selected", style="Danger.TButton",
                   command=self.delete_selected).pack(side="right")
        ttk.Button(actions, text="Edit Selected", command=self.edit_selected).pack(side="right", padx=6)

        table, self.tree = make_tree(self, [
            ("date", "Date", 110, "w"), ("category", "Source", 130, "w"),
            ("description", "Description", 360, "w"), ("amount", "Amount", 130, "e")])
        table.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda _e: self.edit_selected())

    def refresh(self):
        rows = db.get_incomes(self.app.user_id)
        self.records = {r["id"]: r for r in rows}
        fill_tree(self.tree, [(r["id"], (r["date"], r["category"], r["description"], fmt(r["amount"])))
                              for r in rows])
        self.total_var.set(fmt(sum(r["amount"] for r in rows)))

    def reset_form(self):
        self.editing_id = None
        self.amount.set("")
        self.desc.set("")
        self.date.set(today_str())
        self.category.set(db.INCOME_CATEGORIES[0])
        self.save_btn.configure(text="Add Income")
        self.cancel_btn.grid_remove()

    def save(self):
        try:
            amount = parse_amount(self.amount.get())
            date_str = parse_date(self.date.get())
        except ValueError as exc:
            messagebox.showwarning("Invalid input", str(exc), parent=self)
            return
        args = (amount, self.category.get(), date_str, self.desc.get().strip())
        if self.editing_id is None:
            db.add_income(self.app.user_id, *args)
        else:
            db.update_income(self.editing_id, self.app.user_id, *args)
        self.reset_form()
        self.refresh()

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select an entry", "Please select an income entry first.", parent=self)
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
        self.date.set(rec["date"])
        self.desc.set(rec["description"])
        self.save_btn.configure(text="Update Income")
        self.cancel_btn.grid()

    def delete_selected(self):
        rid = self._selected_id()
        if rid is None:
            return
        if messagebox.askyesno("Delete income", "Delete the selected income entry?", parent=self):
            db.delete_income(rid, self.app.user_id)
            if self.editing_id == rid:
                self.reset_form()
            self.refresh()
