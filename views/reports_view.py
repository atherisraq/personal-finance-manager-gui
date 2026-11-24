from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

import database as db
from theme import C, CHART_COLORS
from utils import currency_code, fmt
from views.widgets import summary_card


class ReportsView(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=18)
        self.app = app
        ttk.Label(self, text="Financial Reports", style="Title.TLabel").pack(anchor="w")

        cards = ttk.Frame(self)
        cards.pack(fill="x", pady=10)
        self.vars = {}
        specs = [("income", "Total Income", "CardValueGood.TLabel"),
                 ("expense", "Total Expenses", "CardValueBad.TLabel"),
                 ("net", "Net Balance", "CardValue.TLabel"),
                 ("rate", "Savings Rate", "CardValue.TLabel")]
        for i, (key, caption, style) in enumerate(specs):
            card, var = summary_card(cards, caption, style)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))
            cards.columnconfigure(i, weight=1, uniform="cards")
            self.vars[key] = var

        # Figure is embedded in the window (no pop-ups); pyplot is not used on purpose.
        self.fig = Figure(figsize=(9, 4.2), dpi=100, facecolor="white", layout="constrained")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def refresh(self):
        uid = self.app.user_id
        income, expense = db.get_totals(uid)
        net = income - expense
        rate = net / income * 100 if income > 0 else 0.0
        self.vars["income"].set(fmt(income))
        self.vars["expense"].set(fmt(expense))
        self.vars["net"].set(fmt(net) if net >= 0 else f"-{fmt(-net)}")
        self.vars["rate"].set(f"{rate:.1f}%")
        self._draw(income, expense, db.expense_by_category(uid))

    def _draw(self, income, expense, by_cat):
        code = currency_code()
        self.fig.clear()
        pie_ax = self.fig.add_subplot(1, 2, 1)
        bar_ax = self.fig.add_subplot(1, 2, 2)

        # Donut: expense breakdown by category
        pie_ax.set_title("Expense Breakdown by Category", fontsize=11, fontweight="bold")
        if by_cat:
            labels, values = list(by_cat.keys()), list(by_cat.values())
            pie_ax.pie(values, colors=CHART_COLORS[:len(values)], startangle=90, counterclock=False,
                       wedgeprops={"width": 0.42, "edgecolor": "white"}, pctdistance=0.79,
                       autopct=lambda p: f"{p:.0f}%" if p >= 5 else "",
                       textprops={"color": "white", "fontsize": 8, "fontweight": "bold"})
            pie_ax.text(0, 0, f"{code}\n{sum(values):,.0f}", ha="center", va="center",
                        fontsize=10, fontweight="bold", color=C["text"])
            pie_ax.legend(labels, loc="upper center", bbox_to_anchor=(0.5, 0.02), ncol=3,
                          frameon=False, fontsize=8)
        else:
            pie_ax.text(0.5, 0.5, "No expense data yet", ha="center", va="center", color=C["muted"])
            pie_ax.axis("off")

        # Bar: income vs expenses
        bar_ax.set_title(f"Total Income vs Expenses ({code})", fontsize=11, fontweight="bold")
        bars = bar_ax.bar(["Income", "Expenses"], [income, expense],
                          color=[C["success"], C["danger"]], width=0.5)
        bar_ax.bar_label(bars, labels=[f"{income:,.0f}", f"{expense:,.0f}"], padding=3, fontsize=9)
        bar_ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
        bar_ax.set_ylim(0, max(income, expense, 1) * 1.15)
        for side in ("top", "right"):
            bar_ax.spines[side].set_visible(False)
        bar_ax.tick_params(labelsize=9)
        self.canvas.draw_idle()
