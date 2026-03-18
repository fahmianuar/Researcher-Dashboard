# -*- coding: utf-8 -*-

"""
AcademiX — Academic Dashboard
Python | tkinter + matplotlib + tkcalendar

pip install matplotlib tkcalendar
python academix.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta
from tkcalendar import DateEntry, Calendar
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import calendar

# ── Palette ───────────────────────────────────────────────────────────────────
BG      = "#11121a"
PAN     = "#161c2b"
PAN2    = "#1b2236"
PAN3    = "#1f2840"
BORDER  = "#1e2d45"
BLUE    = "#63b3ed"
GREEN   = "#68d391"
ORANGE  = "#f6ad55"
RED     = "#fc8181"
PURPLE  = "#b794f4"
TEAL    = "#4fd1c5"
TEXT    = "#e2e8f0"
MUTED   = "#718096"
WHITE   = "#ffffff"
PALETTE = [BLUE, GREEN, ORANGE, RED, PURPLE, TEAL, "#4a90c4"]

FONT_TITLE = ("Helvetica", 13, "bold")
FONT_STAT  = ("Helvetica", 32, "bold")
FONT_LABEL = ("Helvetica", 9)
FONT_BODY  = ("Helvetica", 10)
FONT_SMALL = ("Helvetica", 8)
FONT_MONO  = ("Courier", 9)
FONT_BTN   = ("Helvetica", 10)
FONT_HEAD  = ("Helvetica", 11, "bold")
FONT_CAL   = ("Helvetica", 8)

DATE_KW = dict(
    background=BLUE, foreground=WHITE,
    normalbackground=PAN2, normalforeground=TEXT,
    selectbackground=BLUE, selectforeground=WHITE,
    weekendbackground=PAN2, weekendforeground=ORANGE,
    headersbackground=PAN, headersforeground=BLUE,
    othermonthbackground=BG, othermonthforeground=MUTED,
    othermonthwebackground=BG, othermonthweforeground=MUTED,
    borderwidth=0,
)

# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────
def make_btn(parent, text, cmd, bg=BLUE, fg=WHITE, width=14):
    return tk.Button(parent, text=text, command=cmd,
                     bg=bg, fg=fg, font=FONT_BTN,
                     relief="flat", bd=0, padx=8, pady=4,
                     activebackground=bg, activeforeground=fg,
                     cursor="hand2", width=width)

def make_entry(parent, ph="", width=24):
    e = tk.Entry(parent, bg=PAN2, fg=TEXT, insertbackground=TEXT,
                 font=FONT_BODY, relief="flat", bd=4, width=width)
    if ph:
        e.insert(0, ph); e.config(fg=MUTED)
        e.bind("<FocusIn>",  lambda ev, w=e, p=ph:
               (w.delete(0, tk.END), w.config(fg=TEXT)) if w.get() == p else None)
        e.bind("<FocusOut>", lambda ev, w=e, p=ph:
               (w.insert(0, p), w.config(fg=MUTED)) if w.get() == "" else None)
    return e

def entry_val(e, ph=""):
    v = e.get().strip()
    return "" if v == ph else v

def make_combo(parent, values, width=16):
    cb = ttk.Combobox(parent, values=values, width=width,
                      state="readonly", font=FONT_BODY)
    cb.current(0)
    return cb

def make_date(parent, initial=None):
    d = initial or date.today()
    return DateEntry(parent, width=12, date_pattern="dd/mm/yyyy",
                     font=FONT_BODY,
                     fieldbackground=PAN2,
                     year=d.year, month=d.month, day=d.day, **DATE_KW)

def styled_tree(parent, columns, headings, widths, height=18):
    s = ttk.Style()
    s.theme_use("clam")
    s.configure("Dark.Treeview",
                background=PAN2, foreground=TEXT,
                fieldbackground=PAN2, rowheight=24, font=FONT_BODY)
    s.configure("Dark.Treeview.Heading",
                background=PAN, foreground=BLUE,
                font=("Helvetica", 9, "bold"), relief="flat")
    s.map("Dark.Treeview",
          background=[("selected", BORDER)],
          foreground=[("selected", WHITE)])
    tree = ttk.Treeview(parent, columns=columns, show="headings",
                        style="Dark.Treeview", height=height)
    for col, head, w in zip(columns, headings, widths):
        tree.heading(col, text=head)
        tree.column(col, width=w, anchor="w")
    sb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    return tree, sb

def section_head(parent, text, color=BLUE):
    f = tk.Frame(parent, bg=PAN)
    f.pack(fill="x", padx=8, pady=(8, 2))
    tk.Label(f, text=text, bg=PAN, fg=color,
             font=("Helvetica", 9, "bold")).pack(side="left")
    tk.Frame(f, bg=BORDER, height=1).pack(side="left", fill="x",
                                           expand=True, padx=(6, 0))
    return f

def bind_delete(tree, callback):
    """Bind Delete key to a treeview."""
    tree.bind("<Delete>",     lambda e: callback())
    tree.bind("<BackSpace>",  lambda e: callback())


# ─────────────────────────────────────────────────────────────────────────────
#  Mini Calendar with hover tooltips
# ─────────────────────────────────────────────────────────────────────────────
class MiniCalendar(tk.Frame):
    """
    Draws a simple month calendar. Days that have due-date items
    are highlighted. Hovering shows a tooltip with item names.
    """
    DAY_W = 28
    DAY_H = 20

    def __init__(self, parent, get_events_fn, **kw):
        super().__init__(parent, bg=PAN, **kw)
        self.get_events = get_events_fn   # fn() -> {date: [label,...]}
        self._today = date.today()
        self._year  = self._today.year
        self._month = self._today.month
        self._tooltip = None
        self._build()
        self.refresh()

    def _build(self):
        # Nav row
        nav = tk.Frame(self, bg=PAN)
        nav.pack(fill="x", padx=4, pady=(4,0))
        tk.Button(nav, text="◀", bg=PAN, fg=MUTED, relief="flat",
                  font=FONT_SMALL, bd=0, cursor="hand2",
                  command=self._prev).pack(side="left")
        self._month_lbl = tk.Label(nav, text="", bg=PAN, fg=TEXT,
                                   font=("Helvetica", 9, "bold"))
        self._month_lbl.pack(side="left", expand=True)
        tk.Button(nav, text="▶", bg=PAN, fg=MUTED, relief="flat",
                  font=FONT_SMALL, bd=0, cursor="hand2",
                  command=self._next).pack(side="right")

        # Day-name headers
        hf = tk.Frame(self, bg=PAN)
        hf.pack(fill="x", padx=4)
        for day_name in ["Mo","Tu","We","Th","Fr","Sa","Su"]:
            tk.Label(hf, text=day_name, bg=PAN, fg=MUTED,
                     font=FONT_SMALL, width=3,
                     anchor="center").pack(side="left")

        # Canvas for day cells
        w = self.DAY_W * 7 + 8
        h = self.DAY_H * 6 + 4
        self._canvas = tk.Canvas(self, bg=PAN, bd=0,
                                 highlightthickness=0,
                                 width=w, height=h)
        self._canvas.pack(padx=4, pady=(2, 4))
        self._canvas.bind("<Motion>",   self._on_hover)
        self._canvas.bind("<Leave>",    self._hide_tip)

    def _prev(self):
        if self._month == 1:
            self._month = 12; self._year -= 1
        else:
            self._month -= 1
        self.refresh()

    def _next(self):
        if self._month == 12:
            self._month = 1; self._year += 1
        else:
            self._month += 1
        self.refresh()

    def refresh(self):
        self._month_lbl.config(
            text=f"{calendar.month_abbr[self._month]} {self._year}")
        self._canvas.delete("all")
        self._cell_map = {}   # (row, col) -> date

        events = self.get_events()
        cal = calendar.monthcalendar(self._year, self._month)

        for row, week in enumerate(cal):
            for col, day in enumerate(week):
                if day == 0:
                    continue
                d = date(self._year, self._month, day)
                x1 = col * self.DAY_W + 4
                y1 = row * self.DAY_H + 2
                x2 = x1 + self.DAY_W - 2
                y2 = y1 + self.DAY_H - 2
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2

                # Colours
                is_today  = (d == self._today)
                has_event = (d in events)
                is_past   = (d < self._today) and has_event

                if is_today:
                    bg_col, fg_col = BLUE, WHITE
                    self._canvas.create_oval(
                        x1, y1, x2, y2, fill=BLUE, outline="")
                elif has_event:
                    bg_col = RED if is_past else ORANGE
                    self._canvas.create_oval(
                        x1+2, y1+2, x2-2, y2-2, fill=bg_col, outline="")
                    fg_col = WHITE
                else:
                    fg_col = MUTED if col >= 5 else TEXT

                self._canvas.create_text(
                    cx, cy, text=str(day), fill=fg_col,
                    font=FONT_SMALL)
                self._cell_map[(row, col)] = d

    def _get_cell(self, x, y):
        col = int(x // self.DAY_W)
        row = int(y // self.DAY_H)
        return self._cell_map.get((row, col))

    def _on_hover(self, event):
        d = self._get_cell(event.x - 4, event.y - 2)
        if d is None:
            self._hide_tip(); return
        events = self.get_events()
        if d not in events:
            self._hide_tip(); return
        items = events[d]
        tip_text = f"{d.strftime('%d %b %Y')}\n" + "\n".join(f"• {i}" for i in items)
        self._show_tip(event.x_root + 14, event.y_root + 10, tip_text)

    def _show_tip(self, x, y, text):
        self._hide_tip()
        self._tooltip = tk.Toplevel(self)
        self._tooltip.wm_overrideredirect(True)
        self._tooltip.wm_geometry(f"+{x}+{y}")
        self._tooltip.configure(bg=BORDER)
        tk.Label(self._tooltip, text=text, bg=PAN2, fg=TEXT,
                 font=FONT_SMALL, justify="left",
                 padx=8, pady=6, relief="flat").pack()

    def _hide_tip(self, *_):
        if self._tooltip:
            self._tooltip.destroy()
            self._tooltip = None


# ─────────────────────────────────────────────────────────────────────────────
#  Main App
# ─────────────────────────────────────────────────────────────────────────────
class AcademiX:
    def __init__(self, root):
        self.root = root
        self.root.title("AcademiX — Academic Dashboard")
        self.root.configure(bg=BG)
        self.root.geometry("1340x860")
        self.root.minsize(1100, 700)

        self.task_data  = []
        self.pub_data   = []
        self.grant_data = []
        self.conf_data  = []
        self.skill_data = []

        self._seed()
        self._build_ui()
        self._refresh_all()

    # ── Seed ─────────────────────────────────────────────────────────────
    def _seed(self):
        t = date.today()
        self.task_data = [
            ["Prepare lecture slides - SECI 3213",  "Teaching",   "High",   t,               "Pending"],
            ["Grade midterm scripts (48 students)", "Teaching",   "Urgent", t+timedelta(2),  "Pending"],
            ["Submit literature review draft",       "Research",   "High",   t-timedelta(3),  "Done"],
            ["Revise FRGS research proposal",        "Grant",      "High",   t+timedelta(7),  "Pending"],
            ["Complete Python for DS Module 4",     "Learning",   "Medium", t+timedelta(11), "In Progress"],
            ["Register for IEEE ICSCA 2025",         "Conference", "Medium", t-timedelta(2),  "Done"],
            ["Submit final exam paper to registry", "Teaching",   "High",   t+timedelta(31), "Pending"],
            ["Write abstract for NeurIPS 2025",      "Research",   "Medium", t+timedelta(15), "Pending"],
        ]
        self.pub_data = [
            ["Deep Learning Fault Detection in IIoT",      "IEEE Trans. Industrial IoT",  "Under Review", 9.1, date(2025,2,10)],
            ["Federated Learning for Smart Grid",           "Elsevier Energy and AI",       "Accepted",     8.6, date(2024,11,5)],
            ["Explainable AI in Clinical Decision Support", "Nature Scientific Reports",    "In Writing",   4.4, date(2025,3,1)],
        ]
        self.grant_data = [
            ["FRGS 2024/2025 Cycle 2",          "MOE Malaysia", 120000, "Under Evaluation", date(2024,10,15)],
            ["UTM Tier 1 University Grant",      "UTM Research",  50000, "Approved",         date(2025,1,8)],
            ["MRANTI Smart Manufacturing Grant","MRANTI",        200000, "Pending Docs",     date(2025,3,5)],
        ]
        self.conf_data = [
            ["IEEE ICSCA 2025", "Kuala Lumpur, MY", date(2025,5,22),  "Registered + Presenting"],
            ["NeurIPS 2025",    "Vancouver, CA",    date(2025,12,9),  "Submitting Abstract"],
            ["ICLR 2026",       "Singapore",        date(2026,5,1),   "Watching CFP"],
        ]
        self.skill_data = [
            ["Python for Data Science",  "Programming", 60],
            ["LaTeX and Overleaf",       "Writing",     80],
            ["Large Language Models",    "AI/ML",       25],
            ["Grant Writing MOE/FRGS",   "Academic",    45],
            ["Research Methodology",     "Academic",    70],
            ["MATLAB and Simulink",      "Programming", 85],
            ["Deep Learning PyTorch",    "AI/ML",       50],
        ]

    # ── Calendar events map ───────────────────────────────────────────────
    def _get_calendar_events(self):
        events = {}
        for t in self.task_data:
            if t[4] != "Done":
                events.setdefault(t[3], []).append(t[0][:40])
        for c in self.conf_data:
            events.setdefault(c[2], []).append(f"[Conf] {c[0][:35]}")
        for p in self.pub_data:
            if p[2] not in ("Accepted","Published"):
                events.setdefault(p[4], []).append(f"[Pub] {p[0][:35]}")
        return events

    # ── Build UI ──────────────────────────────────────────────────────────
    def _build_ui(self):
        # Top bar
        top = tk.Frame(self.root, bg=PAN, height=40)
        top.pack(fill="x"); top.pack_propagate(False)
        tk.Label(top, text="AcademiX  |  Academic Dashboard",
                 bg=PAN, fg=BLUE, font=FONT_TITLE).pack(side="left", padx=14)
        tk.Label(top, text="Fahmi Anuar  |  Researcher  |  UPM",
                 bg=PAN, fg=MUTED, font=FONT_LABEL).pack(side="left", padx=10)
        tk.Label(top, text=date.today().strftime("%A, %d %b %Y"),
                 bg=PAN, fg=MUTED, font=FONT_LABEL).pack(side="right", padx=14)

        # Notebook
        s = ttk.Style()
        s.configure("Dark.TNotebook",     background=BG, borderwidth=0)
        s.configure("Dark.TNotebook.Tab", background=PAN, foreground=MUTED,
                    padding=[14, 6], font=FONT_BODY, borderwidth=0)
        s.map("Dark.TNotebook.Tab",
              background=[("selected", BG)],
              foreground=[("selected", BLUE)])

        nb = ttk.Notebook(self.root, style="Dark.TNotebook")
        nb.pack(fill="both", expand=True)

        frames = [tk.Frame(nb, bg=BG) for _ in range(6)]
        for f, title in zip(frames, ["  Overview  ","  Tasks / To-Do  ",
                                      "  Publications  ","  Grants  ",
                                      "  Conferences  ","  Skills  "]):
            nb.add(f, text=title)

        (self.tab_ov, self.tab_tk, self.tab_pb,
         self.tab_gr, self.tab_cf, self.tab_sk) = frames

        self._build_overview(self.tab_ov)
        self._build_tasks(self.tab_tk)
        self._build_pubs(self.tab_pb)
        self._build_grants(self.tab_gr)
        self._build_confs(self.tab_cf)
        self._build_skills(self.tab_sk)

    # ══════════════════════════════════════════════════════════════════════
    #  TAB 1 — OVERVIEW  (3-column layout)
    # ══════════════════════════════════════════════════════════════════════
    def _build_overview(self, p):
        # ── Stat cards row ────────────────────────────────────────────────
        sf = tk.Frame(p, bg=PAN, height=100)
        sf.pack(fill="x", padx=10, pady=(10,6))
        sf.pack_propagate(False)

        stat_defs = [
            ("0", "Active Tasks",    BLUE),
            ("0", "Due This Week",   RED),
            ("0", "Publications",    GREEN),
            ("0", "Grants Applied",  PURPLE),
            ("0", "Conferences",     ORANGE),
            ("0", "Skills Tracked",  TEAL),
        ]
        self.stat_labels = []
        for num, lbl, col in stat_defs:
            f = tk.Frame(sf, bg=PAN2)
            f.pack(side="left", expand=True, fill="both", padx=5, pady=6)
            n = tk.Label(f, text=num, bg=PAN2, fg=col, font=FONT_STAT)
            n.pack(pady=(6,0))
            tk.Label(f, text=lbl, bg=PAN2, fg=MUTED, font=FONT_SMALL).pack()
            self.stat_labels.append(n)

        # ── 3-column body ─────────────────────────────────────────────────
        body = tk.Frame(p, bg=BG)
        body.pack(fill="both", expand=True, padx=10, pady=(0,10))
        body.columnconfigure(0, weight=2, minsize=260)
        body.columnconfigure(1, weight=3)
        body.columnconfigure(2, weight=2, minsize=280)
        body.rowconfigure(0, weight=1)

        left   = tk.Frame(body, bg=PAN)
        middle = tk.Frame(body, bg=BG)
        right  = tk.Frame(body, bg=PAN)

        left.grid(  row=0, column=0, sticky="nsew", padx=(0,6))
        middle.grid(row=0, column=1, sticky="nsew", padx=(0,6))
        right.grid( row=0, column=2, sticky="nsew")

        self._build_ov_left(left)
        self._build_ov_middle(middle)
        self._build_ov_right(right)

    # ── LEFT: Progress gauges + Mini Calendar ─────────────────────────────
    def _build_ov_left(self, p):
        # Progress
        tk.Label(p, text="Progress", bg=PAN, fg=TEXT,
                 font=FONT_HEAD).pack(anchor="w", padx=10, pady=(10,4))
        self.gauges = {}
        for key, lbl, val, col in [
            ("sem",   "Semester Progress",  67, BLUE),
            ("tasks", "Tasks Completed",     0, GREEN),
            ("grant", "Grant Success Rate",  0, ORANGE),
        ]:
            tk.Label(p, text=lbl, bg=PAN, fg=MUTED,
                     font=FONT_SMALL).pack(anchor="w", padx=10, pady=(6,1))
            bg_bar = tk.Frame(p, bg=BORDER, height=7)
            bg_bar.pack(fill="x", padx=10, pady=(0,1))
            bg_bar.pack_propagate(False)
            fill = tk.Frame(bg_bar, bg=col, height=7)
            fill.place(relwidth=val/100, relheight=1)
            pct = tk.Label(p, text=f"{val}%", bg=PAN, fg=col, font=FONT_MONO)
            pct.pack(anchor="e", padx=12)
            self.gauges[key] = (fill, pct, col)

        # Divider
        tk.Frame(p, bg=BORDER, height=1).pack(fill="x", padx=10, pady=8)

        # Mini calendar
        tk.Label(p, text="Calendar", bg=PAN, fg=TEXT,
                 font=FONT_HEAD).pack(anchor="w", padx=10, pady=(0,4))
        self.mini_cal = MiniCalendar(p, self._get_calendar_events)
        self.mini_cal.pack(fill="x", padx=4, pady=(0,6))

        # Legend
        leg = tk.Frame(p, bg=PAN)
        leg.pack(fill="x", padx=10, pady=(0,8))
        for dot_col, label in [(BLUE,"Today"),(ORANGE,"Due Soon"),(RED,"Overdue")]:
            tk.Canvas(leg, bg=PAN, width=10, height=10,
                      highlightthickness=0).pack(side="left")
            c = tk.Canvas(leg, bg=PAN, width=10, height=10, highlightthickness=0)
            c.pack(side="left")
            c.create_oval(1,1,9,9, fill=dot_col, outline="")
            tk.Label(leg, text=label, bg=PAN, fg=MUTED,
                     font=FONT_SMALL).pack(side="left", padx=(2,8))

    # ── MIDDLE: To-Do + Publications + Grants ─────────────────────────────
    def _build_ov_middle(self, p):
        # ── To-Do summary ────────────────────────────────────────────────
        section_head(p, "To-Do  —  Pending Tasks")
        self.ov_todo_frame = tk.Frame(p, bg=PAN2)
        self.ov_todo_frame.pack(fill="x", padx=8, pady=(2,6))

        # ── Publications summary ──────────────────────────────────────────
        section_head(p, "Publications")
        self.ov_pub_frame = tk.Frame(p, bg=PAN2)
        self.ov_pub_frame.pack(fill="x", padx=8, pady=(2,6))

        # ── Grants summary ────────────────────────────────────────────────
        section_head(p, "Grants")
        self.ov_grant_frame = tk.Frame(p, bg=PAN2)
        self.ov_grant_frame.pack(fill="x", padx=8, pady=(2,6))

        # ── Achievements ─────────────────────────────────────────────────
        section_head(p, "Recent Achievements", GREEN)
        af = tk.Frame(p, bg=PAN2)
        af.pack(fill="both", expand=True, padx=8, pady=(2,8))
        self.activity_list = tk.Listbox(
            af, bg=PAN2, fg=GREEN, font=FONT_SMALL,
            relief="flat", selectbackground=BORDER,
            selectforeground=WHITE, activestyle="none",
            bd=0, height=5)
        self.activity_list.pack(fill="both", expand=True, padx=4, pady=4)

    # ── RIGHT: Deadlines + Conferences + Skills ───────────────────────────
    def _build_ov_right(self, p):
        # Upcoming deadlines
        section_head(p, "Upcoming Deadlines", RED)
        df = tk.Frame(p, bg=PAN2)
        df.pack(fill="x", padx=8, pady=(2,6))
        self.ov_deadline_list = tk.Listbox(
            df, bg=PAN2, fg=RED, font=FONT_SMALL,
            relief="flat", selectbackground=BORDER,
            selectforeground=WHITE, activestyle="none",
            bd=0, height=6)
        self.ov_deadline_list.pack(fill="x", padx=4, pady=4)

        # Future conferences
        section_head(p, "Future Conferences", ORANGE)
        cf = tk.Frame(p, bg=PAN2)
        cf.pack(fill="x", padx=8, pady=(2,6))
        self.ov_conf_list = tk.Listbox(
            cf, bg=PAN2, fg=ORANGE, font=FONT_SMALL,
            relief="flat", selectbackground=BORDER,
            selectforeground=WHITE, activestyle="none",
            bd=0, height=5)
        self.ov_conf_list.pack(fill="x", padx=4, pady=4)

        # Skills to learn
        section_head(p, "Skills to Learn", TEAL)
        skf = tk.Frame(p, bg=PAN2)
        skf.pack(fill="both", expand=True, padx=8, pady=(2,8))
        self.ov_skill_frame = tk.Frame(skf, bg=PAN2)
        self.ov_skill_frame.pack(fill="both", expand=True, padx=4, pady=4)

    # ══════════════════════════════════════════════════════════════════════
    #  TAB 2 — TASKS
    # ══════════════════════════════════════════════════════════════════════
    def _build_tasks(self, p):
        form = tk.Frame(p, bg=PAN)
        form.pack(fill="x", padx=12, pady=(12,6))
        tk.Label(form, text="Add New Task", bg=PAN, fg=TEXT,
                 font=FONT_HEAD).grid(row=0, column=0, columnspan=7,
                                      sticky="w", padx=10, pady=(6,4))

        self.tk_title = make_entry(form, "Task title...", width=40)
        self.tk_title.grid(row=1, column=0, padx=(10,4), pady=6)

        self.tk_cat  = make_combo(form, ["Teaching","Research","Grant",
                                          "Conference","Learning","Admin"], width=13)
        self.tk_cat.grid(row=1, column=1, padx=4)

        self.tk_prio = make_combo(form, ["Urgent","High","Medium","Low"], width=9)
        self.tk_prio.grid(row=1, column=2, padx=4)

        tk.Label(form, text="Due Date:", bg=PAN, fg=MUTED,
                 font=FONT_LABEL).grid(row=1, column=3, padx=(8,2))
        self.tk_due = make_date(form, date.today()+timedelta(7))
        self.tk_due.grid(row=1, column=4, padx=4)

        make_btn(form, "Add Task", self._add_task, bg=BLUE, width=12).grid(
            row=1, column=5, padx=(8,10))

        br = tk.Frame(form, bg=PAN)
        br.grid(row=2, column=0, columnspan=7, sticky="w", padx=10, pady=(0,8))
        make_btn(br, "Mark as Done",    self._mark_done,   bg=GREEN, fg="#0a2a14").pack(side="left", padx=(0,8))
        make_btn(br, "Delete Selected", self._delete_task, bg=RED).pack(side="left")
        tk.Label(br, text="  ← or press Delete key on selected row",
                 bg=PAN, fg=MUTED, font=FONT_SMALL).pack(side="left", padx=8)

        tf = tk.Frame(p, bg=BG)
        tf.pack(fill="both", expand=True, padx=12, pady=(0,12))
        self.task_tree, tsb = styled_tree(
            tf, ("title","cat","prio","due","status"),
            ("Title","Category","Priority","Due Date","Status"),
            [400,110,90,110,110], height=24)
        self.task_tree.pack(side="left", fill="both", expand=True)
        tsb.pack(side="left", fill="y")
        bind_delete(self.task_tree, self._delete_task)

    # ══════════════════════════════════════════════════════════════════════
    #  TAB 3 — PUBLICATIONS
    # ══════════════════════════════════════════════════════════════════════
    def _build_pubs(self, p):
        form = tk.Frame(p, bg=PAN)
        form.pack(fill="x", padx=12, pady=(12,6))
        tk.Label(form, text="Add Publication", bg=PAN, fg=TEXT,
                 font=FONT_HEAD).grid(row=0, column=0, columnspan=7,
                                      sticky="w", padx=10, pady=(6,4))

        self.pb_title   = make_entry(form, "Paper title...", width=38)
        self.pb_title.grid(row=1, column=0, padx=(10,4), pady=6)

        self.pb_journal = make_entry(form, "Journal or venue...", width=26)
        self.pb_journal.grid(row=1, column=1, padx=4)

        self.pb_status  = make_combo(form, ["In Writing","Under Review","Major Revision",
                                            "Minor Revision","Accepted","Published","Rejected"], width=15)
        self.pb_status.grid(row=1, column=2, padx=4)

        tk.Label(form, text="IF:", bg=PAN, fg=MUTED,
                 font=FONT_LABEL).grid(row=1, column=3, padx=(6,2))
        self.pb_if = make_entry(form, "0.0", width=6)
        self.pb_if.grid(row=1, column=4, padx=4)

        tk.Label(form, text="Submit Date:", bg=PAN, fg=MUTED,
                 font=FONT_LABEL).grid(row=2, column=0, padx=(10,4),
                                       sticky="w", pady=(0,8))
        self.pb_date = make_date(form, date.today())
        self.pb_date.grid(row=2, column=1, padx=4, pady=(0,8), sticky="w")

        make_btn(form, "Add",    self._add_pub, bg=BLUE, width=10).grid(row=1, column=5, padx=(8,4))
        make_btn(form, "Delete", self._del_pub, bg=RED,  width=10).grid(row=2, column=5, padx=(8,4), pady=(0,8))

        pf = tk.Frame(p, bg=BG)
        pf.pack(fill="both", expand=True, padx=12, pady=(0,12))
        self.pub_tree, psb = styled_tree(
            pf, ("title","journal","status","if","submitted"),
            ("Title","Journal / Venue","Status","IF","Submitted"),
            [360,240,130,60,110], height=24)
        self.pub_tree.pack(side="left", fill="both", expand=True)
        psb.pack(side="left", fill="y")
        bind_delete(self.pub_tree, self._del_pub)

    # ══════════════════════════════════════════════════════════════════════
    #  TAB 4 — GRANTS
    # ══════════════════════════════════════════════════════════════════════
    def _build_grants(self, p):
        form = tk.Frame(p, bg=PAN)
        form.pack(fill="x", padx=12, pady=(12,6))
        tk.Label(form, text="Add Grant Application", bg=PAN, fg=TEXT,
                 font=FONT_HEAD).grid(row=0, column=0, columnspan=7,
                                      sticky="w", padx=10, pady=(6,4))

        self.gr_name   = make_entry(form, "Grant name or scheme...", width=32)
        self.gr_name.grid(row=1, column=0, padx=(10,4), pady=6)

        self.gr_body   = make_entry(form, "Funding body...", width=20)
        self.gr_body.grid(row=1, column=1, padx=4)

        tk.Label(form, text="RM:", bg=PAN, fg=MUTED,
                 font=FONT_LABEL).grid(row=1, column=2, padx=(6,2))
        self.gr_amt    = make_entry(form, "0", width=10)
        self.gr_amt.grid(row=1, column=3, padx=4)

        self.gr_status = make_combo(form, ["Preparing","Submitted","Under Evaluation",
                                           "Pending Docs","Approved","Rejected","Completed"], width=17)
        self.gr_status.grid(row=1, column=4, padx=4)

        tk.Label(form, text="Apply Date:", bg=PAN, fg=MUTED,
                 font=FONT_LABEL).grid(row=2, column=0, padx=(10,4),
                                       sticky="w", pady=(0,8))
        self.gr_date   = make_date(form, date.today())
        self.gr_date.grid(row=2, column=1, padx=4, pady=(0,8), sticky="w")

        make_btn(form, "Add Grant", self._add_grant, bg=PURPLE, width=12).grid(row=1, column=5, padx=(8,10))
        make_btn(form, "Delete",    self._del_grant, bg=RED,    width=12).grid(row=2, column=5, padx=(8,10), pady=(0,8))

        gf = tk.Frame(p, bg=BG)
        gf.pack(fill="both", expand=True, padx=12, pady=(0,12))
        self.grant_tree, gsb = styled_tree(
            gf, ("name","body","amount","status","applied"),
            ("Grant Name","Funding Body","Amount","Status","Applied"),
            [290,190,110,140,110], height=24)
        self.grant_tree.pack(side="left", fill="both", expand=True)
        gsb.pack(side="left", fill="y")
        bind_delete(self.grant_tree, self._del_grant)

    # ══════════════════════════════════════════════════════════════════════
    #  TAB 5 — CONFERENCES
    # ══════════════════════════════════════════════════════════════════════
    def _build_confs(self, p):
        form = tk.Frame(p, bg=PAN)
        form.pack(fill="x", padx=12, pady=(12,6))
        tk.Label(form, text="Add Conference", bg=PAN, fg=TEXT,
                 font=FONT_HEAD).grid(row=0, column=0, columnspan=6,
                                      sticky="w", padx=10, pady=(6,4))

        self.cf_name   = make_entry(form, "Conference name...", width=34)
        self.cf_name.grid(row=1, column=0, padx=(10,4), pady=6)

        self.cf_loc    = make_entry(form, "City, Country...", width=20)
        self.cf_loc.grid(row=1, column=1, padx=4)

        tk.Label(form, text="Date:", bg=PAN, fg=MUTED,
                 font=FONT_LABEL).grid(row=1, column=2, padx=(6,2))
        self.cf_date   = make_date(form, date.today()+timedelta(90))
        self.cf_date.grid(row=1, column=3, padx=4)

        self.cf_status = make_combo(form, ["Watching CFP","Abstract Submitted",
                                           "Paper Submitted","Accepted","Registered",
                                           "Registered + Presenting","Attended"], width=22)
        self.cf_status.grid(row=2, column=0, padx=(10,4), pady=(0,8), sticky="w")

        make_btn(form, "Add",    self._add_conf, bg=ORANGE, fg="#1a0d00", width=10).grid(row=1, column=4, padx=(8,10))
        make_btn(form, "Delete", self._del_conf, bg=RED,    width=10).grid(row=2, column=4, padx=(8,10), pady=(0,8))

        cf = tk.Frame(p, bg=BG)
        cf.pack(fill="both", expand=True, padx=12, pady=(0,12))
        self.conf_tree, csb = styled_tree(
            cf, ("name","loc","date","status"),
            ("Conference Name","Location","Date","Status"),
            [340,200,110,200], height=24)
        self.conf_tree.pack(side="left", fill="both", expand=True)
        csb.pack(side="left", fill="y")
        bind_delete(self.conf_tree, self._del_conf)

    # ══════════════════════════════════════════════════════════════════════
    #  TAB 6 — SKILLS
    # ══════════════════════════════════════════════════════════════════════
    def _build_skills(self, p):
        form = tk.Frame(p, bg=PAN)
        form.pack(fill="x", padx=12, pady=(12,6))
        tk.Label(form, text="Add Skill to Learn", bg=PAN, fg=TEXT,
                 font=FONT_HEAD).grid(row=0, column=0, columnspan=6,
                                      sticky="w", padx=10, pady=(6,4))

        self.sk_name = make_entry(form, "Skill name...", width=28)
        self.sk_name.grid(row=1, column=0, padx=(10,4), pady=6)

        self.sk_cat  = make_combo(form, ["Programming","AI/ML","Writing","Academic",
                                          "Teaching","Research","Soft Skills","Other"], width=13)
        self.sk_cat.grid(row=1, column=1, padx=4)

        tk.Label(form, text="Progress %:", bg=PAN, fg=MUTED,
                 font=FONT_LABEL).grid(row=1, column=2, padx=(8,2))

        self.sk_var = tk.IntVar(value=0)
        self.sk_lbl = tk.Label(form, text="0%", bg=PAN, fg=BLUE,
                               font=("Helvetica",11,"bold"), width=4)
        self.sk_lbl.grid(row=1, column=4, padx=4)

        sl = ttk.Scale(form, from_=0, to=100, orient="horizontal",
                       variable=self.sk_var,
                       command=lambda v: self.sk_lbl.config(text=f"{int(float(v))}%"))
        sl.grid(row=1, column=3, padx=4, pady=6, sticky="ew")
        form.columnconfigure(3, weight=1)

        make_btn(form, "Add Skill", self._add_skill, bg=GREEN, fg="#0a2a14", width=12).grid(row=1, column=5, padx=(8,4))
        make_btn(form, "Delete",    self._del_skill, bg=RED,   width=12).grid(row=2, column=5, padx=(8,4), pady=(0,8))

        bot = tk.Frame(p, bg=BG)
        bot.pack(fill="both", expand=True, padx=12, pady=(0,12))

        sf = tk.Frame(bot, bg=BG)
        sf.pack(side="left", fill="both", expand=True)
        self.skill_tree, ssb = styled_tree(
            sf, ("skill","cat","prog"),
            ("Skill","Category","Progress (%)"),
            [260,120,90], height=24)
        self.skill_tree.pack(side="left", fill="both", expand=True)
        ssb.pack(side="left", fill="y")
        bind_delete(self.skill_tree, self._del_skill)

        self.chart_frame = tk.Frame(bot, bg=PAN)
        self.chart_frame.pack(side="left", fill="both", expand=True, padx=(10,0))
        self._draw_chart()

    def _draw_chart(self):
        for w in self.chart_frame.winfo_children():
            w.destroy()
        n = len(self.skill_data)
        fig, ax = plt.subplots(figsize=(5.5, max(3, n*0.55)))
        fig.patch.set_facecolor(PAN)
        ax.set_facecolor(PAN)
        if n == 0:
            ax.text(0.5, 0.5, "No skills added yet",
                    ha="center", va="center", color=MUTED,
                    fontsize=10, transform=ax.transAxes)
        else:
            vals  = [r[2] for r in self.skill_data]
            names = [r[0] for r in self.skill_data]
            colors = [PALETTE[i % len(PALETTE)] for i in range(n)]
            ax.barh(range(n), vals, color=colors, height=0.6, edgecolor="none")
            for i, v in enumerate(vals):
                ax.text(v+1.5, i, f"{v}%", va="center", ha="left",
                        color=TEXT, fontsize=8)
            ax.set_yticks(range(n))
            ax.set_yticklabels(names, color=TEXT, fontsize=8)
            ax.set_xlim(0, 115)
            ax.set_ylim(-0.5, n-0.5)
            ax.invert_yaxis()
            ax.tick_params(axis="x", colors=MUTED, labelsize=7)
            ax.tick_params(axis="y", colors=TEXT,  labelsize=8)
            for sp in ["top","right","left"]:
                ax.spines[sp].set_visible(False)
            ax.spines["bottom"].set_color(BORDER)
            ax.xaxis.grid(True, color=BORDER, linewidth=0.5)
            ax.set_axisbelow(True)
            ax.set_title("Skills Progress", color=TEXT, fontsize=10, pad=8)
        plt.tight_layout(pad=1.2)
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        plt.close(fig)

    # ══════════════════════════════════════════════════════════════════════
    #  Refresh
    # ══════════════════════════════════════════════════════════════════════
    def _refresh_all(self):
        self._refresh_ov()
        self._refresh_tasks()
        self._refresh_pubs()
        self._refresh_grants()
        self._refresh_confs()
        self._refresh_skills()

    def _refresh_ov(self):
        today    = date.today()
        n_active = sum(1 for t in self.task_data if t[4] != "Done")
        n_due    = sum(1 for t in self.task_data
                       if t[4] != "Done" and (t[3]-today).days <= 7)
        self.stat_labels[0].config(text=str(n_active))
        self.stat_labels[1].config(text=str(n_due))
        self.stat_labels[2].config(text=str(len(self.pub_data)))
        self.stat_labels[3].config(text=str(len(self.grant_data)))
        self.stat_labels[4].config(text=str(len(self.conf_data)))
        self.stat_labels[5].config(text=str(len(self.skill_data)))

        # Gauges
        n_tot  = len(self.task_data)
        n_done = sum(1 for t in self.task_data if t[4]=="Done")
        t_pct  = round(n_done/n_tot*100) if n_tot > 0 else 0
        n_gr   = len(self.grant_data)
        n_app  = sum(1 for g in self.grant_data if g[3]=="Approved")
        g_pct  = round(n_app/n_gr*100) if n_gr > 0 else 0
        for key, pct in [("tasks",t_pct),("grant",g_pct)]:
            fill, lbl, col = self.gauges[key]
            fill.place(relwidth=pct/100, relheight=1)
            lbl.config(text=f"{pct}%")

        # Mini calendar refresh
        self.mini_cal.refresh()

        # ── Middle: To-Do list ────────────────────────────────────────────
        for w in self.ov_todo_frame.winfo_children():
            w.destroy()
        pending = [t for t in self.task_data if t[4] != "Done"]
        pending.sort(key=lambda x: x[3])
        for i, t in enumerate(pending[:6]):
            diff = (t[3]-today).days
            if diff < 0:    tag = f"[OVERDUE]"; col = RED
            elif diff == 0: tag = "[TODAY]";    col = ORANGE
            elif diff <= 3: tag = f"[{diff}d]"; col = ORANGE
            else:           tag = f"[{diff}d]"; col = MUTED
            row = tk.Frame(self.ov_todo_frame, bg=PAN2)
            row.pack(fill="x", padx=4, pady=1)
            # Priority dot
            dot_col = {"Urgent":RED,"High":ORANGE,"Medium":BLUE,"Low":TEAL}.get(t[2], MUTED)
            c = tk.Canvas(row, bg=PAN2, width=8, height=8, highlightthickness=0)
            c.pack(side="left", padx=(4,2), pady=6)
            c.create_oval(1,1,7,7, fill=dot_col, outline="")
            tk.Label(row, text=t[0][:42], bg=PAN2, fg=TEXT,
                     font=FONT_SMALL, anchor="w").pack(side="left", expand=True)
            tk.Label(row, text=tag, bg=PAN2, fg=col,
                     font=FONT_MONO).pack(side="right", padx=6)

        # ── Middle: Publications ──────────────────────────────────────────
        for w in self.ov_pub_frame.winfo_children():
            w.ov_pub_frame.destroy() if hasattr(w,"ov_pub_frame") else w.destroy()
        for w in self.ov_pub_frame.winfo_children():
            w.destroy()
        STATUS_COL = {"In Writing":MUTED,"Under Review":BLUE,"Major Revision":ORANGE,
                      "Minor Revision":ORANGE,"Accepted":GREEN,"Published":TEAL,"Rejected":RED}
        for pub in self.pub_data[:4]:
            row = tk.Frame(self.ov_pub_frame, bg=PAN2)
            row.pack(fill="x", padx=4, pady=1)
            sc = STATUS_COL.get(pub[2], MUTED)
            tk.Label(row, text="●", bg=PAN2, fg=sc,
                     font=FONT_SMALL).pack(side="left", padx=4)
            tk.Label(row, text=pub[0][:42], bg=PAN2, fg=TEXT,
                     font=FONT_SMALL, anchor="w").pack(side="left", expand=True)
            tk.Label(row, text=pub[2], bg=PAN2, fg=sc,
                     font=FONT_MONO).pack(side="right", padx=6)

        # ── Middle: Grants ────────────────────────────────────────────────
        for w in self.ov_grant_frame.winfo_children():
            w.destroy()
        GRANT_COL = {"Preparing":MUTED,"Submitted":BLUE,"Under Evaluation":ORANGE,
                     "Pending Docs":ORANGE,"Approved":GREEN,"Rejected":RED,"Completed":TEAL}
        for g in self.grant_data[:4]:
            row = tk.Frame(self.ov_grant_frame, bg=PAN2)
            row.pack(fill="x", padx=4, pady=1)
            gc = GRANT_COL.get(g[3], MUTED)
            tk.Label(row, text="●", bg=PAN2, fg=gc,
                     font=FONT_SMALL).pack(side="left", padx=4)
            tk.Label(row, text=g[0][:38], bg=PAN2, fg=TEXT,
                     font=FONT_SMALL, anchor="w").pack(side="left", expand=True)
            amt = tk.Label(row, text=f"RM {g[2]:,}", bg=PAN2, fg=MUTED,
                           font=FONT_MONO)
            amt.pack(side="right", padx=2)
            tk.Label(row, text=g[3], bg=PAN2, fg=gc,
                     font=FONT_MONO).pack(side="right", padx=6)

        # ── Middle: Achievements ──────────────────────────────────────────
        self.activity_list.delete(0, tk.END)
        items = []
        for t in self.task_data:
            if t[4]=="Done": items.append(f"[Done]  {t[0]}")
        for pub in self.pub_data:
            if pub[2] in ("Accepted","Published"):
                items.append(f"[Paper]  Accepted: {pub[0][:45]}")
        for g in self.grant_data:
            if g[3]=="Approved":
                items.append(f"[Grant]  Grant Approved: {g[0][:35]}")
        for item in (items or ["No completed items yet."]):
            self.activity_list.insert(tk.END, item)

        # ── Right: Upcoming Deadlines ────────────────────────────────────
        self.ov_deadline_list.delete(0, tk.END)
        pending = [(t,(t[3]-today).days) for t in self.task_data if t[4]!="Done"]
        pending.sort(key=lambda x: x[1])
        for task, diff in pending[:8]:
            if diff < 0:    tag = f"OVERDUE {abs(diff)}d"
            elif diff == 0: tag = "TODAY"
            else:           tag = f"{diff}d left"
            self.ov_deadline_list.insert(tk.END, f"{tag:<14}  {task[0][:32]}")

        # ── Right: Future Conferences ────────────────────────────────────
        self.ov_conf_list.delete(0, tk.END)
        upcoming = sorted(self.conf_data, key=lambda x: x[2])
        for c in upcoming[:6]:
            diff = (c[2]-today).days
            self.ov_conf_list.insert(
                tk.END, f"{c[2].strftime('%d %b %y')}  {c[0][:30]}")

        # ── Right: Skills ─────────────────────────────────────────────────
        for w in self.ov_skill_frame.winfo_children():
            w.destroy()
        for s in self.skill_data[:7]:
            row = tk.Frame(self.ov_skill_frame, bg=PAN2)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=s[0][:28], bg=PAN2, fg=TEXT,
                     font=FONT_SMALL, width=22, anchor="w").pack(side="left", padx=4)
            # Mini bar
            bar_bg = tk.Frame(row, bg=BORDER, height=6, width=80)
            bar_bg.pack(side="left", padx=4)
            bar_bg.pack_propagate(False)
            col = PALETTE[self.skill_data.index(s) % len(PALETTE)]
            tk.Frame(bar_bg, bg=col, height=6,
                     width=int(80*s[2]/100)).place(x=0, y=0, relheight=1)
            tk.Label(row, text=f"{s[2]}%", bg=PAN2, fg=MUTED,
                     font=FONT_MONO).pack(side="left", padx=2)

    def _refresh_tasks(self):
        for r in self.task_tree.get_children(): self.task_tree.delete(r)
        for t in self.task_data:
            self.task_tree.insert("","end",
                values=(t[0],t[1],t[2],t[3].strftime("%d %b %Y"),t[4]))

    def _refresh_pubs(self):
        for r in self.pub_tree.get_children(): self.pub_tree.delete(r)
        for p in self.pub_data:
            self.pub_tree.insert("","end",
                values=(p[0],p[1],p[2],f"{p[3]:.1f}",p[4].strftime("%d %b %Y")))

    def _refresh_grants(self):
        for r in self.grant_tree.get_children(): self.grant_tree.delete(r)
        for g in self.grant_data:
            self.grant_tree.insert("","end",
                values=(g[0],g[1],f"RM {g[2]:,}",g[3],g[4].strftime("%d %b %Y")))

    def _refresh_confs(self):
        for r in self.conf_tree.get_children(): self.conf_tree.delete(r)
        for c in self.conf_data:
            self.conf_tree.insert("","end",
                values=(c[0],c[1],c[2].strftime("%d %b %Y"),c[3]))

    def _refresh_skills(self):
        for r in self.skill_tree.get_children(): self.skill_tree.delete(r)
        for s in self.skill_data:
            self.skill_tree.insert("","end", values=(s[0],s[1],s[2]))
        self._draw_chart()

    # ══════════════════════════════════════════════════════════════════════
    #  Callbacks
    # ══════════════════════════════════════════════════════════════════════
    def _add_task(self):
        title = entry_val(self.tk_title, "Task title...")
        if not title:
            messagebox.showwarning("Input Required","Please enter a task title."); return
        self.task_data.append([title, self.tk_cat.get(), self.tk_prio.get(),
                                self.tk_due.get_date(), "Pending"])
        self.tk_title.delete(0,tk.END); self.tk_title.insert(0,"Task title..."); self.tk_title.config(fg=MUTED)
        self._refresh_tasks(); self._refresh_ov()

    def _mark_done(self):
        sel = self.task_tree.selection()
        if not sel: messagebox.showwarning("No Selection","Please select a row first."); return
        self.task_data[self.task_tree.index(sel[0])][4] = "Done"
        self._refresh_tasks(); self._refresh_ov()

    def _delete_task(self):
        sel = self.task_tree.selection()
        if not sel: return
        if messagebox.askyesno("Delete","Delete selected task?"): 
            del self.task_data[self.task_tree.index(sel[0])]
            self._refresh_tasks(); self._refresh_ov()

    def _add_pub(self):
        title   = entry_val(self.pb_title,   "Paper title...")
        journal = entry_val(self.pb_journal, "Journal or venue...")
        if not title or not journal:
            messagebox.showwarning("Input Required","Please enter title and journal."); return
        try:    impact = float(entry_val(self.pb_if,"0.0") or 0)
        except: impact = 0.0
        self.pub_data.append([title, journal, self.pb_status.get(),
                               impact, self.pb_date.get_date()])
        for w,ph in [(self.pb_title,"Paper title..."),(self.pb_journal,"Journal or venue...")]:
            w.delete(0,tk.END); w.insert(0,ph); w.config(fg=MUTED)
        self._refresh_pubs(); self._refresh_ov()

    def _del_pub(self):
        sel = self.pub_tree.selection()
        if not sel: return
        if messagebox.askyesno("Delete","Delete selected publication?"):
            del self.pub_data[self.pub_tree.index(sel[0])]
            self._refresh_pubs(); self._refresh_ov()

    def _add_grant(self):
        name = entry_val(self.gr_name,"Grant name or scheme...")
        if not name:
            messagebox.showwarning("Input Required","Please enter a grant name."); return
        try:    amt = int(entry_val(self.gr_amt,"0") or 0)
        except: amt = 0
        self.grant_data.append([name, entry_val(self.gr_body,"Funding body..."),
                                 amt, self.gr_status.get(), self.gr_date.get_date()])
        for w,ph in [(self.gr_name,"Grant name or scheme..."),(self.gr_body,"Funding body...")]:
            w.delete(0,tk.END); w.insert(0,ph); w.config(fg=MUTED)
        self._refresh_grants(); self._refresh_ov()

    def _del_grant(self):
        sel = self.grant_tree.selection()
        if not sel: return
        if messagebox.askyesno("Delete","Delete selected grant?"):
            del self.grant_data[self.grant_tree.index(sel[0])]
            self._refresh_grants(); self._refresh_ov()

    def _add_conf(self):
        name = entry_val(self.cf_name,"Conference name...")
        if not name:
            messagebox.showwarning("Input Required","Please enter a conference name."); return
        self.conf_data.append([name, entry_val(self.cf_loc,"City, Country..."),
                                self.cf_date.get_date(), self.cf_status.get()])
        for w,ph in [(self.cf_name,"Conference name..."),(self.cf_loc,"City, Country...")]:
            w.delete(0,tk.END); w.insert(0,ph); w.config(fg=MUTED)
        self._refresh_confs(); self._refresh_ov()

    def _del_conf(self):
        sel = self.conf_tree.selection()
        if not sel: return
        if messagebox.askyesno("Delete","Delete selected conference?"):
            del self.conf_data[self.conf_tree.index(sel[0])]
            self._refresh_confs(); self._refresh_ov()

    def _add_skill(self):
        name = entry_val(self.sk_name,"Skill name...")
        if not name:
            messagebox.showwarning("Input Required","Please enter a skill name."); return
        self.skill_data.append([name, self.sk_cat.get(), int(self.sk_var.get())])
        self.sk_name.delete(0,tk.END); self.sk_name.insert(0,"Skill name..."); self.sk_name.config(fg=MUTED)
        self.sk_var.set(0); self.sk_lbl.config(text="0%")
        self._refresh_skills(); self._refresh_ov()

    def _del_skill(self):
        sel = self.skill_tree.selection()
        if not sel: return
        if messagebox.askyesno("Delete","Delete selected skill?"):
            del self.skill_data[self.skill_tree.index(sel[0])]
            self._refresh_skills(); self._refresh_ov()


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    AcademiX(root)
    root.mainloop()

