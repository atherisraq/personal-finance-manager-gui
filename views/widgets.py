"""Small reusable widgets shared by the views."""
import tkinter as tk
from tkinter import ttk

from theme import C


def make_tree(parent, columns, height=10):
    """Build a Treeview with a scrollbar. columns: [(key, heading, width, anchor), ...]"""
    frame = ttk.Frame(parent)
    tree = ttk.Treeview(frame, columns=[c[0] for c in columns], show="headings",
                        selectmode="browse", height=height)
    for key, heading, width, anchor in columns:
        tree.heading(key, text=heading)
        tree.column(key, width=width, minwidth=60, anchor=anchor, stretch=True)
    tree.tag_configure("odd", background=C["row_alt"])
    scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    tree.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")
    return frame, tree


def fill_tree(tree, rows):
    """rows: [(iid, values_tuple), ...]"""
    tree.delete(*tree.get_children())
    for i, (iid, values) in enumerate(rows):
        tree.insert("", "end", iid=str(iid), values=values, tags=("odd",) if i % 2 else ())


def summary_card(parent, caption, style="CardValue.TLabel"):
    """A white card with a caption and a big value. Returns (frame, StringVar)."""
    card = ttk.Frame(parent, style="Card.TFrame", padding=(16, 10))
    ttk.Label(card, text=caption, style="CardCaption.TLabel").pack(anchor="w")
    var = tk.StringVar(value="-")
    ttk.Label(card, textvariable=var, style=style).pack(anchor="w")
    return card, var


class ScrollableFrame(ttk.Frame):
    """A vertically scrollable container; put children in `.inner`."""

    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, highlightthickness=0, bg=C["bg"])
        bar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>",
                        lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._win, width=e.width))
        self.canvas.configure(yscrollcommand=bar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")
        self.canvas.bind("<Enter>", self._bind_wheel)
        self.canvas.bind("<Leave>", self._unbind_wheel)

    def _bind_wheel(self, _e):
        self.canvas.bind_all("<MouseWheel>", self._on_wheel)
        self.canvas.bind_all("<Button-4>", self._on_wheel)
        self.canvas.bind_all("<Button-5>", self._on_wheel)

    def _unbind_wheel(self, _e):
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.canvas.unbind_all(seq)

    def _on_wheel(self, event):
        step = -1 if (event.num == 4 or event.delta > 0) else 1
        self.canvas.yview_scroll(step, "units")

    def clear(self):
        for child in self.inner.winfo_children():
            child.destroy()
