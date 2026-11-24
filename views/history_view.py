import tkinter as tk
from tkinter import ttk

import database as db
from utils import fmt
from views.widgets import fill_tree, make_tree

ALL_CATEGORIES = sorted(set(db.INCOME_CATEGORIES + db.EXPENSE_CATEGORIES))


class HistoryView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=18)
        self.app = app
        self.sort_col, self.sort_rev = "date", True

        ttk.Label(self, text="Transaction History & Search", style="Title.TLabel").pack(anchor="w")

        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=10)
        self.keyword = tk.StringVar()
        self.type_var = tk.StringVar(value="All")
        self.cat_var = tk.StringVar(value="All")
        ttk.Label(bar, text="Search").pack(side="left")
        ttk.Entry(bar, textvariable=self.keyword, width=28).pack(side="left", padx=(6, 14))
        ttk.Label(bar, text="Type").pack(side="left")
        type_box = ttk.Combobox(bar, textvariable=self.type_var, values=["All", "Income", "Expense"],
                                state="readonly", width=10)
        type_box.pack(side="left", padx=(6, 14))
        ttk.Label(bar, text="Category").pack(side="left")
        self.cat_box = ttk.Combobox(bar, textvariable=self.cat_var, values=["All"] + ALL_CATEGORIES,
                                    state="readonly", width=14)
        self.cat_box.pack(side="left", padx=(6, 14))
        ttk.Button(bar, text="Clear / Reset", command=self.reset_filters).pack(side="left")
        self.count_label = ttk.Label(bar, style="Muted.TLabel")
        self.count_label.pack(side="right")

        table, self.tree = make_tree(self, [
            ("id", "ID", 80, "w"), ("type", "Type", 80, "w"), ("category", "Category", 120, "w"),
            ("amount", "Amount", 120, "e"), ("date", "Date", 100, "w"),
            ("description", "Description", 320, "w")])
        table.pack(fill="both", expand=True)
        for col in ("id", "type", "category", "amount", "date", "description"):
            self.tree.heading(col, command=lambda c=col: self.sort_by(c))
        self.tree.tag_configure("income", foreground="#15803d")
        self.tree.tag_configure("expense", foreground="#b91c1c")

        self.keyword.trace_add("write", lambda *_: self.refresh())
        self.cat_var.trace_add("write", lambda *_: self.refresh())
        type_box.bind("<<ComboboxSelected>>", self._type_changed)

    def _type_changed(self, _event=None):
        kind = self.type_var.get()
        cats = {"Income": db.INCOME_CATEGORIES, "Expense": db.EXPENSE_CATEGORIES}.get(kind, ALL_CATEGORIES)
        self.cat_box.configure(values=["All"] + list(cats))
        if self.cat_var.get() not in cats:
            self.cat_var.set("All")   # triggers refresh
        self.refresh()

    def reset_filters(self):
        self.keyword.set("")
        self.type_var.set("All")
        self.cat_box.configure(values=["All"] + ALL_CATEGORIES)
        self.cat_var.set("All")
        self.refresh()

    def sort_by(self, col):
        self.sort_rev = not self.sort_rev if col == self.sort_col else False
        self.sort_col = col
        self.refresh()

    def refresh(self):
        everything = db.get_transactions(self.app.user_id)
        kw = self.keyword.get().strip().lower()
        kind, cat = self.type_var.get(), self.cat_var.get()
        rows = []
        for t in everything:
            if kind != "All" and t["type"] != kind:
                continue
            if cat != "All" and t["category"] != cat:
                continue
            haystack = " ".join([t["id"], t["type"], t["category"], t["date"], t["description"],
                                 f"{t['amount']:.2f}"]).lower()
            if kw and kw not in haystack:
                continue
            rows.append(t)
        key = {"amount": lambda t: t["amount"], "id": lambda t: (t["type"], int(t["id"].split("-")[1]))}.get(
            self.sort_col, lambda t: str(t[self.sort_col]).lower())
        rows.sort(key=key, reverse=self.sort_rev)
        fill_tree(self.tree, [(t["id"], (t["id"], t["type"], t["category"], fmt(t["amount"]),
                                         t["date"], t["description"])) for t in rows])
        for t in rows:
            self.tree.item(t["id"], tags=(t["type"].lower(),))
        self.count_label.configure(text=f"Showing {len(rows)} of {len(everything)} transactions")
