import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import database as db
from utils import CURRENCIES, get_currency, today_str


class ProfileView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=18)
        self.app = app
        self.name = tk.StringVar()
        self.email = tk.StringVar()
        self.currency = tk.StringVar()
        self.username_text = tk.StringVar()

        ttk.Label(self, text="User Profile & Settings", style="Title.TLabel").pack(anchor="w", pady=(0, 10))

        info = ttk.LabelFrame(self, text=" Personal Information ", padding=14)
        info.pack(fill="x")
        ttk.Label(info, text="Username").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Label(info, textvariable=self.username_text, style="Muted.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Label(info, text="Display name").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(info, textvariable=self.name, width=36).grid(row=1, column=1, sticky="w")
        ttk.Label(info, text="Email").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(info, textvariable=self.email, width=36).grid(row=2, column=1, sticky="w")
        ttk.Button(info, text="Save Profile", style="Accent.TButton",
                   command=self.save_profile).grid(row=3, column=1, sticky="w", pady=(10, 0))
        info.columnconfigure(0, minsize=120)

        prefs = ttk.LabelFrame(self, text=" Preferences ", padding=14)
        prefs.pack(fill="x", pady=12)
        ttk.Label(prefs, text="Currency symbol").grid(row=0, column=0, sticky="w")
        box = ttk.Combobox(prefs, textvariable=self.currency, values=CURRENCIES, state="readonly", width=6)
        box.grid(row=0, column=1, padx=10)
        box.bind("<<ComboboxSelected>>", lambda _e: self.app.set_currency(self.currency.get()))
        ttk.Label(prefs, text="Updates amounts across every screen.", style="Muted.TLabel").grid(row=0, column=2)

        data = ttk.LabelFrame(self, text=" Data & Session ", padding=14)
        data.pack(fill="x")
        ttk.Button(data, text="Export to CSV", command=self.export_csv).pack(side="left")
        ttk.Button(data, text="Reset to Demo Data", style="Danger.TButton",
                   command=self.reset_demo).pack(side="left", padx=10)
        ttk.Button(data, text="Log out", command=self.app.logout).pack(side="right")

    def refresh(self):
        user = db.get_user(self.app.user_id)
        self.username_text.set("Guest (demo mode)" if user["is_demo"] else user["username"])
        self.name.set(user["display_name"])
        self.email.set(user["email"])
        self.currency.set(get_currency())

    def save_profile(self):
        name, email = self.name.get().strip(), self.email.get().strip()
        if not name:
            messagebox.showwarning("Invalid input", "Display name cannot be empty.", parent=self)
            return
        if email and ("@" not in email or "." not in email.split("@")[-1]):
            messagebox.showwarning("Invalid input", "Please enter a valid email address.", parent=self)
            return
        db.update_profile(self.app.user_id, name, email)
        self.app.reload_user()
        messagebox.showinfo("Profile", "Profile updated.", parent=self)

    def export_csv(self):
        path = filedialog.asksaveasfilename(
            parent=self, defaultextension=".csv", initialfile=f"transactions_{today_str()}.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as fh:
                writer = csv.writer(fh)
                writer.writerow(["ID", "Type", "Category", "Payment Method", "Amount", "Date", "Description"])
                for t in db.get_transactions(self.app.user_id):
                    writer.writerow([t["id"], t["type"], t["category"], t["method"],
                                     f"{t['amount']:.2f}", t["date"], t["description"]])
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc), parent=self)
            return
        messagebox.showinfo("Export complete", f"Transactions saved to:\n{path}", parent=self)

    def reset_demo(self):
        if messagebox.askyesno(
                "Reset to Demo Data",
                "This replaces all your incomes, expenses, budgets and savings goals with sample data.\n\n"
                "Continue?", icon="warning", parent=self):
            db.reset_to_demo(self.app.user_id)
            self.app.set_currency(db.get_setting(self.app.user_id, "currency", db.DEFAULT_CURRENCY))
            messagebox.showinfo("Reset", "Demo data restored.", parent=self)
