"""Colors and ttk styling (uses the built-in 'clam' theme for consistent looks)."""
import tkinter.font as tkfont
from tkinter import ttk

C = {
    "bg": "#f4f6fa", "card": "#ffffff", "sidebar": "#1f2a44", "sidebar_hover": "#2b3a5e",
    "text": "#1f2937", "muted": "#6b7280", "primary": "#2563eb", "primary_dark": "#1d4ed8",
    "success": "#16a34a", "warning": "#f59e0b", "danger": "#dc2626",
    "trough": "#e5e7eb", "row_alt": "#f3f6fb", "heading": "#e8edf6",
}
CHART_COLORS = ["#2563eb", "#16a34a", "#f59e0b", "#dc2626", "#8b5cf6", "#06b6d4", "#ec4899"]


def setup_styles(root):
    s = ttk.Style(root)
    s.theme_use("clam")
    root.configure(bg=C["bg"])
    base = tkfont.nametofont("TkDefaultFont")
    base.configure(size=10)
    fam = base.actual("family")

    s.configure(".", background=C["bg"], foreground=C["text"], font=(fam, 10))
    s.configure("TFrame", background=C["bg"])
    s.configure("Card.TFrame", background=C["card"])
    s.configure("Sidebar.TFrame", background=C["sidebar"])
    s.configure("TLabelframe", background=C["bg"])
    s.configure("TLabelframe.Label", background=C["bg"], foreground=C["muted"], font=(fam, 10, "bold"))

    # Labels
    s.configure("TLabel", background=C["bg"], foreground=C["text"])
    s.configure("Title.TLabel", font=(fam, 18, "bold"))
    s.configure("Muted.TLabel", foreground=C["muted"])
    s.configure("AuthTitle.TLabel", background=C["card"], font=(fam, 20, "bold"))
    s.configure("CardText.TLabel", background=C["card"])
    s.configure("CardMuted.TLabel", background=C["card"], foreground=C["muted"])
    s.configure("CardCaption.TLabel", background=C["card"], foreground=C["muted"], font=(fam, 10))
    s.configure("CardHeading.TLabel", background=C["card"], font=(fam, 12, "bold"))
    for name, color in (("CardValue", C["text"]), ("CardValueGood", C["success"]),
                        ("CardValueBad", C["danger"])):
        s.configure(f"{name}.TLabel", background=C["card"], foreground=color, font=(fam, 20, "bold"))
    s.configure("StatusOk.TLabel", background=C["card"], foreground=C["success"], font=(fam, 10, "bold"))
    s.configure("StatusWarn.TLabel", background=C["card"], foreground="#b45309", font=(fam, 10, "bold"))
    s.configure("StatusDanger.TLabel", background=C["card"], foreground=C["danger"], font=(fam, 10, "bold"))
    s.configure("SidebarTitle.TLabel", background=C["sidebar"], foreground="white", font=(fam, 15, "bold"))
    s.configure("SidebarUser.TLabel", background=C["sidebar"], foreground="#9fb0d3")

    # Buttons
    s.configure("TButton", padding=(12, 6))
    s.configure("Accent.TButton", background=C["primary"], foreground="white", borderwidth=0, padding=(14, 6))
    s.map("Accent.TButton", background=[("active", C["primary_dark"]), ("disabled", "#9ca3af")])
    s.configure("Danger.TButton", background=C["danger"], foreground="white", borderwidth=0, padding=(14, 6))
    s.map("Danger.TButton", background=[("active", "#b91c1c")])
    s.configure("Link.TButton", background=C["card"], foreground=C["primary"], borderwidth=0)
    s.map("Link.TButton", background=[("active", C["card"])], foreground=[("active", C["primary_dark"])])
    s.configure("Nav.TButton", background=C["sidebar"], foreground="#dbe3f4", anchor="w",
                padding=(20, 11), borderwidth=0)
    s.map("Nav.TButton", background=[("active", C["sidebar_hover"])])
    s.configure("NavActive.TButton", background=C["primary"], foreground="white", anchor="w",
                padding=(20, 11), borderwidth=0, font=(fam, 10, "bold"))
    s.map("NavActive.TButton", background=[("active", C["primary"])])

    # Progress bars: normal (<80%), warning (>=80%), over budget (>=100%)
    for name, color in (("Green", C["success"]), ("Orange", C["warning"]), ("Red", C["danger"])):
        s.configure(f"{name}.Horizontal.TProgressbar", background=color, lightcolor=color,
                    darkcolor=color, troughcolor=C["trough"], borderwidth=0, thickness=14)

    # Tables
    s.configure("Treeview", rowheight=28, background="white", fieldbackground="white", borderwidth=0)
    s.configure("Treeview.Heading", background=C["heading"], foreground=C["text"],
                font=(fam, 10, "bold"), padding=6, relief="flat")
    s.map("Treeview", background=[("selected", C["primary"])], foreground=[("selected", "white")])
