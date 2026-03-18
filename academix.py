# -*- coding: utf-8 -*-
"""
AcademiX - Academic Dashboard
pip install matplotlib tkcalendar
python academix.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date, timedelta, datetime
from tkcalendar import DateEntry
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import calendar
import json
import os
import hashlib

# ---- Palette ----------------------------------------------------------------
BG      = "#0d0f18"
PAN     = "#13192a"
PAN2    = "#1a2035"
PAN3    = "#202840"
BORDER  = "#243050"
BLUE    = "#5eadf2"
GREEN   = "#56c97a"
ORANGE  = "#f5a623"
RED     = "#f07070"
PURPLE  = "#a78bfa"
TEAL    = "#38c9b8"
YELLOW  = "#f6d860"
TEXT    = "#dde4f0"
MUTED   = "#6b7a99"
WHITE   = "#ffffff"
PALETTE = [BLUE, GREEN, ORANGE, RED, PURPLE, TEAL, YELLOW]

_APP_DIR     = os.path.join(os.path.expanduser("~"), "AcademiX")
os.makedirs(_APP_DIR, exist_ok=True)
PROFILE_FILE = os.path.join(_APP_DIR, "academix_profile.json")
DATA_FILE    = os.path.join(_APP_DIR, "academix_data.json")
HISTORY_DIR  = os.path.join(_APP_DIR, "academix_history")
MAX_HISTORY  = 20
AUTOSAVE_MS  = 30000

# ---- Password ---------------------------------------------------------------
# The History button and triple-click title trigger are both password-protected.
#
# Default password : academix2025
#
# To set your own password, replace the hash below.
# Generate your hash by running this in terminal:
#   python -c "import hashlib; print(hashlib.sha256(b'yourpassword').hexdigest())"
# Then paste the result as the HISTORY_PASSWORD_HASH value.
#
HISTORY_PASSWORD_HASH = "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"

# ---- Fonts ------------------------------------------------------------------
FONT_APPNAME = ("Helvetica", 15, "bold")
FONT_PROFILE = ("Helvetica", 11)
FONT_DATE    = ("Helvetica", 10)
FONT_STAT    = ("Helvetica", 28, "bold")
FONT_STATLBL = ("Helvetica", 10)
FONT_HEAD    = ("Helvetica", 12, "bold")
FONT_SUBHEAD = ("Helvetica", 10, "bold")
FONT_BODY    = ("Helvetica", 11)
FONT_SMALL   = ("Helvetica", 9)
FONT_MONO    = ("Courier", 10)
FONT_BTN     = ("Helvetica", 11, "bold")
FONT_TAB     = ("Helvetica", 11)
FONT_INPUT   = ("Helvetica", 11)
FONT_TABLE   = ("Helvetica", 10)
FONT_TABLEH  = ("Helvetica", 10, "bold")

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

# ---- Helpers ----------------------------------------------------------------

def make_btn(parent, text, cmd, bg=BLUE, fg=WHITE, width=12, height=1):
    b = tk.Button(parent, text=text, command=cmd,
                  bg=bg, fg=fg, font=FONT_BTN,
                  relief="flat", bd=0, padx=10, pady=6,
                  activebackground=bg, activeforeground=fg,
                  cursor="hand2", width=width, height=height)
    b.bind("<Enter>", lambda e: b.config(bg=_lighten(bg)))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b

def _lighten(hex_col):
    r = min(255, int(hex_col[1:3], 16) + 30)
    g = min(255, int(hex_col[3:5], 16) + 30)
    b = min(255, int(hex_col[5:7], 16) + 30)
    return "#{:02x}{:02x}{:02x}".format(r, g, b)

def make_entry(parent, ph="", width=24, font=None):
    f = font or FONT_INPUT
    e = tk.Entry(parent, bg=PAN2, fg=TEXT, insertbackground=TEXT,
                 font=f, relief="flat", bd=0, width=width,
                 highlightthickness=1, highlightbackground=BORDER,
                 highlightcolor=BLUE)
    if ph:
        e.insert(0, ph)
        e.config(fg=MUTED)
        def on_in(ev, w=e, p=ph):
            if w.get() == p:
                w.delete(0, tk.END)
                w.config(fg=TEXT)
        def on_out(ev, w=e, p=ph):
            if w.get() == "":
                w.insert(0, p)
                w.config(fg=MUTED)
        e.bind("<FocusIn>",  on_in)
        e.bind("<FocusOut>", on_out)
    return e

def entry_val(e, ph=""):
    v = e.get().strip()
    return "" if v == ph else v

def make_combo(parent, values, width=16, font=None):
    f = font or FONT_INPUT
    cb = ttk.Combobox(parent, values=values, width=width,
                      state="readonly", font=f)
    cb.current(0)
    return cb

def make_date(parent, initial=None):
    d = initial or date.today()
    return DateEntry(parent, width=13, date_pattern="dd/mm/yyyy",
                     font=FONT_INPUT,
                     fieldbackground=PAN2,
                     year=d.year, month=d.month, day=d.day,
                     **DATE_KW)

def styled_tree(parent, columns, headings, widths, height=18):
    s = ttk.Style()
    s.theme_use("clam")
    s.configure("Dark.Treeview",
                background=PAN2, foreground=TEXT,
                fieldbackground=PAN2, rowheight=30,
                font=FONT_TABLE)
    s.configure("Dark.Treeview.Heading",
                background=PAN3, foreground=BLUE,
                font=FONT_TABLEH, relief="flat")
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
    f.pack(fill="x", padx=8, pady=(10, 3))
    tk.Label(f, text=text, bg=PAN, fg=color,
             font=FONT_SUBHEAD).pack(side="left")
    tk.Frame(f, bg=color, height=1).pack(side="left", fill="x",
                                          expand=True, padx=(8, 0))

def bind_delete(tree, callback):
    tree.bind("<Delete>",    lambda e: callback())
    tree.bind("<BackSpace>", lambda e: callback())

def status_color(status):
    mapping = {
        "Pending": ORANGE, "In Progress": BLUE, "Done": GREEN,
        "Urgent": RED, "High": ORANGE, "Medium": BLUE, "Low": TEAL,
        "Under Review": BLUE, "Accepted": GREEN, "Published": TEAL,
        "In Writing": MUTED, "Rejected": RED, "Major Revision": ORANGE,
        "Minor Revision": YELLOW,
        "Approved": GREEN, "Under Evaluation": BLUE,
        "Pending Docs": ORANGE, "Preparing": MUTED,
        "Submitted": BLUE, "Completed": TEAL,
        "Registered + Presenting": GREEN, "Watching CFP": MUTED,
        "Submitting Abstract": ORANGE,
    }
    return mapping.get(status, MUTED)

# ---- Mini Calendar ----------------------------------------------------------

class MiniCalendar(tk.Frame):
    DAY_W = 36
    DAY_H = 26

    def __init__(self, parent, get_events_fn, **kw):
        super().__init__(parent, bg=PAN, **kw)
        self.get_events = get_events_fn
        self._today     = date.today()
        self._year      = self._today.year
        self._month     = self._today.month
        self._tooltip   = None
        self._cell_map  = {}
        self._build()
        self.refresh()

    def _build(self):
        nav = tk.Frame(self, bg=PAN)
        nav.pack(fill="x", padx=6, pady=(6, 2))
        tk.Button(nav, text="  <  ", bg=PAN3, fg=TEXT, relief="flat",
                  font=FONT_SMALL, bd=0, cursor="hand2",
                  command=self._prev).pack(side="left")
        self._month_lbl = tk.Label(nav, text="", bg=PAN, fg=TEXT,
                                   font=FONT_SUBHEAD)
        self._month_lbl.pack(side="left", expand=True)
        tk.Button(nav, text="  >  ", bg=PAN3, fg=TEXT, relief="flat",
                  font=FONT_SMALL, bd=0, cursor="hand2",
                  command=self._next).pack(side="right")

        hf = tk.Frame(self, bg=PAN)
        hf.pack(fill="x", padx=6)
        for dn in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
            tk.Label(hf, text=dn, bg=PAN, fg=MUTED,
                     font=FONT_SMALL, width=3,
                     anchor="center").pack(side="left", padx=1)

        w = self.DAY_W * 7 + 12
        h = self.DAY_H * 6 + 6
        self._canvas = tk.Canvas(self, bg=PAN, bd=0,
                                 highlightthickness=0,
                                 width=w, height=h)
        self._canvas.pack(padx=6, pady=(2, 6))
        self._canvas.bind("<Motion>", self._on_hover)
        self._canvas.bind("<Leave>",  self._hide_tip)

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
        mn = calendar.month_abbr[self._month]
        self._month_lbl.config(text=mn + "  " + str(self._year))
        self._canvas.delete("all")
        self._cell_map = {}
        events = self.get_events()
        cal = calendar.monthcalendar(self._year, self._month)

        for row, week in enumerate(cal):
            for col, day in enumerate(week):
                if day == 0:
                    continue
                d  = date(self._year, self._month, day)
                x1 = col * self.DAY_W + 4
                y1 = row * self.DAY_H + 2
                x2 = x1 + self.DAY_W - 2
                y2 = y1 + self.DAY_H - 2
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2

                is_today  = (d == self._today)
                has_event = (d in events)
                is_past   = has_event and (d < self._today)

                if is_today:
                    self._canvas.create_oval(
                        x1+1, y1+1, x2-1, y2-1, fill=BLUE, outline="")
                    fg_col = WHITE
                elif has_event:
                    dot_col = RED if is_past else ORANGE
                    self._canvas.create_oval(
                        x1+3, y1+3, x2-3, y2-3, fill=dot_col, outline="")
                    fg_col = WHITE
                else:
                    fg_col = MUTED if col >= 5 else TEXT

                self._canvas.create_text(cx, cy, text=str(day),
                                         fill=fg_col, font=FONT_SMALL)
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
        tip_text = d.strftime("%d %b %Y") + "\n" + \
                   "\n".join("  - " + i for i in items)
        self._show_tip(event.x_root + 16, event.y_root + 12, tip_text)

    def _show_tip(self, x, y, text):
        self._hide_tip()
        self._tooltip = tk.Toplevel(self)
        self._tooltip.wm_overrideredirect(True)
        self._tooltip.wm_geometry("+" + str(x) + "+" + str(y))
        self._tooltip.configure(bg=BLUE)
        tk.Label(self._tooltip, text=text, bg=PAN3, fg=TEXT,
                 font=FONT_SMALL, justify="left",
                 padx=10, pady=8, relief="flat").pack(padx=1, pady=1)

    def _hide_tip(self, *_):
        if self._tooltip:
            self._tooltip.destroy()
            self._tooltip = None


# ---- Status Badge -----------------------------------------------------------

class StatusBadge(tk.Label):
    def __init__(self, parent, status, **kw):
        col = status_color(status)
        super().__init__(parent, text=" " + status + " ",
                         bg=PAN2, fg=col, font=FONT_SMALL,
                         relief="flat", padx=4, pady=2, **kw)


# ---- Editable Profile Dialog ------------------------------------------------

class ProfileDialog(tk.Toplevel):
    def __init__(self, parent, name, affiliation, on_save):
        super().__init__(parent)
        self.title("Edit Profile")
        self.configure(bg=PAN)
        self.resizable(False, False)
        self.grab_set()

        w, h = 420, 220
        self.geometry("{}x{}+{}+{}".format(
            w, h,
            parent.winfo_rootx() + parent.winfo_width()//2 - w//2,
            parent.winfo_rooty() + parent.winfo_height()//2 - h//2))

        tk.Label(self, text="Edit Profile", bg=PAN, fg=BLUE,
                 font=FONT_HEAD).pack(pady=(18, 10))

        form = tk.Frame(self, bg=PAN)
        form.pack(padx=24, fill="x")

        tk.Label(form, text="Name:", bg=PAN, fg=MUTED,
                 font=FONT_BODY).grid(row=0, column=0, sticky="w", pady=6)
        self.name_entry = tk.Entry(form, bg=PAN2, fg=TEXT,
                                   insertbackground=TEXT, font=FONT_BODY,
                                   relief="flat", bd=0, width=30,
                                   highlightthickness=1,
                                   highlightbackground=BORDER,
                                   highlightcolor=BLUE)
        self.name_entry.grid(row=0, column=1, padx=(10, 0), pady=6,
                             sticky="ew")
        self.name_entry.insert(0, name)

        tk.Label(form, text="Affiliation:", bg=PAN, fg=MUTED,
                 font=FONT_BODY).grid(row=1, column=0, sticky="w", pady=6)
        self.aff_entry = tk.Entry(form, bg=PAN2, fg=TEXT,
                                  insertbackground=TEXT, font=FONT_BODY,
                                  relief="flat", bd=0, width=30,
                                  highlightthickness=1,
                                  highlightbackground=BORDER,
                                  highlightcolor=BLUE)
        self.aff_entry.grid(row=1, column=1, padx=(10, 0), pady=6,
                            sticky="ew")
        self.aff_entry.insert(0, affiliation)
        form.columnconfigure(1, weight=1)

        btn_row = tk.Frame(self, bg=PAN)
        btn_row.pack(pady=18)
        make_btn(btn_row, "Save", lambda: self._save(on_save),
                 bg=BLUE, width=10).pack(side="left", padx=8)
        make_btn(btn_row, "Cancel", self.destroy,
                 bg=PAN3, fg=MUTED, width=10).pack(side="left", padx=8)

    def _save(self, on_save):
        name = self.name_entry.get().strip()
        aff  = self.aff_entry.get().strip()
        if name:
            on_save(name, aff)
        self.destroy()


# ---- Password Dialog --------------------------------------------------------

class PasswordDialog(tk.Toplevel):
    """
    Modal password prompt. Calls on_success() if the correct
    password is entered. The password is verified against a
    SHA-256 hash so the plain-text password never appears in memory
    longer than needed.
    """
    def __init__(self, parent, on_success, max_attempts=3):
        super().__init__(parent)
        self.title("Authentication Required")
        self.configure(bg=PAN)
        self.resizable(False, False)
        self.grab_set()
        self._on_success   = on_success
        self._max_attempts = max_attempts
        self._attempts     = 0

        # Centre on parent
        w, h = 380, 230
        px = parent.winfo_rootx() + parent.winfo_width()  // 2 - w // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2 - h // 2
        self.geometry("{}x{}+{}+{}".format(w, h, px, py))

        # Lock icon label
        tk.Label(self, text="[  RESTRICTED  ]",
                 bg=PAN, fg=RED,
                 font=("Helvetica", 11, "bold")).pack(pady=(20, 4))

        tk.Label(self, text="Enter password to access Version History",
                 bg=PAN, fg=MUTED,
                 font=FONT_SMALL).pack(pady=(0, 16))

        # Password entry
        entry_frame = tk.Frame(self, bg=PAN)
        entry_frame.pack(padx=30, fill="x")
        self._pw_entry = tk.Entry(entry_frame,
                                  show="*",
                                  bg=PAN2, fg=TEXT,
                                  insertbackground=TEXT,
                                  font=FONT_BODY,
                                  relief="flat", bd=0,
                                  highlightthickness=1,
                                  highlightbackground=BORDER,
                                  highlightcolor=BLUE)
        self._pw_entry.pack(fill="x", ipady=6)
        self._pw_entry.focus_set()
        self._pw_entry.bind("<Return>", lambda e: self._check())

        # Error message label (hidden until needed)
        self._err_lbl = tk.Label(self, text="",
                                 bg=PAN, fg=RED,
                                 font=FONT_SMALL)
        self._err_lbl.pack(pady=(6, 0))

        # Attempt counter
        self._att_lbl = tk.Label(self,
                                 text="Attempts remaining: {}".format(max_attempts),
                                 bg=PAN, fg=MUTED,
                                 font=FONT_SMALL)
        self._att_lbl.pack(pady=(2, 12))

        # Buttons
        btn_row = tk.Frame(self, bg=PAN)
        btn_row.pack()
        tk.Button(btn_row, text="Unlock", command=self._check,
                  bg=BLUE, fg=WHITE, font=FONT_BTN,
                  relief="flat", bd=0, padx=16, pady=6,
                  activebackground=BLUE, cursor="hand2",
                  width=10).pack(side="left", padx=(0, 10))
        tk.Button(btn_row, text="Cancel", command=self.destroy,
                  bg=PAN3, fg=MUTED, font=FONT_BTN,
                  relief="flat", bd=0, padx=16, pady=6,
                  activebackground=PAN3, cursor="hand2",
                  width=10).pack(side="left")

    def _check(self):
        pw   = self._pw_entry.get()
        hsh  = hashlib.sha256(pw.encode("utf-8")).hexdigest()
        self._pw_entry.delete(0, tk.END)
        self._attempts += 1
        remaining = self._max_attempts - self._attempts

        if hsh == HISTORY_PASSWORD_HASH:
            self.destroy()
            self._on_success()
        else:
            if remaining <= 0:
                messagebox.showwarning(
                    "Access Denied",
                    "Too many failed attempts. Access locked.",
                    parent=self)
                self.destroy()
            else:
                self._err_lbl.config(text="Incorrect password.")
                self._att_lbl.config(
                    text="Attempts remaining: {}".format(remaining))
                # Shake the window for feedback
                self._shake()

    def _shake(self):
        x0 = self.winfo_x()
        y0 = self.winfo_y()
        for dx in [8, -8, 6, -6, 4, -4, 0]:
            self.after(30 * abs(dx), lambda x=x0+dx, y=y0:
                       self.geometry("+{}+{}".format(x, y)))


# ---- Main App ---------------------------------------------------------------

class AcademiX:

    def __init__(self, root):
        self.root = root
        self.root.title("AcademiX - Academic Dashboard")
        self.root.configure(bg=BG)
        self.root.geometry("1400x900")
        self.root.minsize(1100, 700)

        self._load_profile()

        self.task_data  = []
        self.pub_data   = []
        self.grant_data = []
        self.conf_data  = []
        self.skill_data = []

        # Load saved data or seed with samples
        if not self._load_data():
            self._seed()

        self._build_ui()
        self._refresh_all()

        # Start autosave timer
        self.root.after(AUTOSAVE_MS, self._autosave)

        # Save on close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---- profile ------------------------------------------------------------

    def _on_close(self):
        """Save a final snapshot on close, then quit."""
        self._save_data(snapshot_label="on_close")
        self.root.destroy()

    def _load_profile(self):
        default = {"name": "Fahmi Anuar", "affiliation": "Researcher  |  UPM"}
        if os.path.exists(PROFILE_FILE):
            try:
                with open(PROFILE_FILE, "r") as f:
                    data = json.load(f)
                    self.profile_name = data.get("name", default["name"])
                    self.profile_aff  = data.get("affiliation", default["affiliation"])
                    return
            except Exception:
                pass
        self.profile_name = default["name"]
        self.profile_aff  = default["affiliation"]

    def _save_profile(self):
        with open(PROFILE_FILE, "w") as f:
            json.dump({"name": self.profile_name,
                       "affiliation": self.profile_aff}, f)

    def _edit_profile(self):
        ProfileDialog(self.root, self.profile_name, self.profile_aff,
                      self._on_profile_saved)

    def _on_profile_saved(self, name, aff):
        self.profile_name = name
        self.profile_aff  = aff
        self._save_profile()
        if hasattr(self, "name_lbl"):
            self.name_lbl.config(text=name)
        if hasattr(self, "aff_lbl"):
            self.aff_lbl.config(text=aff)

    # ---- data serialisation -------------------------------------------------

    def _data_to_dict(self):
        """Serialise all app data to a plain dict (JSON-safe)."""
        def d2s(d):
            return d.isoformat() if isinstance(d, date) else d
        return {
            "task_data":  [[r[0],r[1],r[2],d2s(r[3]),r[4]]
                           for r in self.task_data],
            "pub_data":   [[r[0],r[1],r[2],r[3],d2s(r[4])]
                           for r in self.pub_data],
            "grant_data": [[r[0],r[1],r[2],r[3],d2s(r[4])]
                           for r in self.grant_data],
            "conf_data":  [[r[0],r[1],d2s(r[2]),r[3]]
                           for r in self.conf_data],
            "skill_data": [list(r) for r in self.skill_data],
        }

    def _dict_to_data(self, d):
        """Load data dict back into app, parsing date strings."""
        def s2d(s):
            for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S",
                        "%Y-%m-%d %H:%M:%S"):
                try:
                    return datetime.strptime(s, fmt).date()
                except Exception:
                    pass
            return date.today()
        self.task_data  = [[r[0],r[1],r[2],s2d(r[3]),r[4]]
                           for r in d.get("task_data", [])]
        self.pub_data   = [[r[0],r[1],r[2],r[3],s2d(r[4])]
                           for r in d.get("pub_data", [])]
        self.grant_data = [[r[0],r[1],r[2],r[3],s2d(r[4])]
                           for r in d.get("grant_data", [])]
        self.conf_data  = [[r[0],r[1],s2d(r[2]),r[3]]
                           for r in d.get("conf_data", [])]
        self.skill_data = [list(r) for r in d.get("skill_data", [])]

    # ---- save ---------------------------------------------------------------

    def _save_data(self, snapshot_label=None):
        """Save current data to DATA_FILE and optionally add a history snapshot."""
        payload = self._data_to_dict()
        payload["saved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        if snapshot_label:
            self._save_snapshot(snapshot_label)

        self._update_save_status("Saved  " + datetime.now().strftime("%H:%M:%S"))

    def _save_snapshot(self, label):
        """Write a numbered snapshot into HISTORY_DIR."""
        os.makedirs(HISTORY_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_label = "".join(c if c.isalnum() or c in "_-" else "_"
                             for c in label[:40])
        filename = os.path.join(HISTORY_DIR, ts + "_" + safe_label + ".json")
        payload = self._data_to_dict()
        payload["snapshot_label"] = label
        payload["snapshot_time"]  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        self._prune_history()

    def _prune_history(self):
        """Keep only the newest MAX_HISTORY snapshots."""
        try:
            files = sorted([
                f for f in os.listdir(HISTORY_DIR) if f.endswith(".json")
            ])
            while len(files) > MAX_HISTORY:
                os.remove(os.path.join(HISTORY_DIR, files.pop(0)))
        except Exception:
            pass

    def _autosave(self):
        """Called on a repeating timer."""
        try:
            self._save_data()
        except Exception:
            pass
        self.root.after(AUTOSAVE_MS, self._autosave)

    # ---- load ---------------------------------------------------------------

    def _load_data(self):
        """Load from DATA_FILE if it exists, else fall through to seed."""
        if not os.path.exists(DATA_FILE):
            return False
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            self._dict_to_data(d)
            return True
        except Exception:
            return False

    # ---- history browser ----------------------------------------------------

    def _list_snapshots(self):
        """Return list of (filename, label, time_str) sorted newest first."""
        if not os.path.isdir(HISTORY_DIR):
            return []
        files = sorted([
            f for f in os.listdir(HISTORY_DIR) if f.endswith(".json")
        ], reverse=True)
        result = []
        for fname in files:
            try:
                with open(os.path.join(HISTORY_DIR, fname),
                          "r", encoding="utf-8") as fh:
                    d = json.load(fh)
                label = d.get("snapshot_label", fname)
                ts    = d.get("snapshot_time",  fname[:15])
                result.append((fname, label, ts))
            except Exception:
                result.append((fname, fname, "unknown"))
        return result

    def _open_history(self):
        """Open history browser directly - callers must authenticate first."""
        self._open_history_unlocked()

    def _open_history_unlocked(self):
        """History browser - called after successful password entry."""
        snapshots = self._list_snapshots()

        win = tk.Toplevel(self.root)
        win.title("Version History")
        win.configure(bg=PAN)
        win.resizable(True, True)
        win.grab_set()

        # Centre on parent, larger window
        w, h = 700, 580
        px = self.root.winfo_rootx() + self.root.winfo_width()  // 2 - w // 2
        py = self.root.winfo_rooty() + self.root.winfo_height() // 2 - h // 2
        win.geometry("{}x{}+{}+{}".format(w, h, max(0,px), max(0,py)))
        win.minsize(560, 420)

        # Header
        hdr = tk.Frame(win, bg=PAN)
        hdr.pack(fill="x", padx=16, pady=(14, 4))
        tk.Label(hdr, text="Version History",
                 bg=PAN, fg=BLUE, font=FONT_HEAD).pack(anchor="w")
        tk.Label(hdr,
                 text="Select a snapshot below, then click  Restore Selected.",
                 bg=PAN, fg=MUTED, font=FONT_SMALL).pack(anchor="w", pady=(2, 0))

        # ---- Buttons FIRST (packed at bottom, always visible) ---------------
        btn_bar = tk.Frame(win, bg=PAN2, height=54)
        btn_bar.pack(fill="x", side="bottom")
        btn_bar.pack_propagate(False)

        btn_inner = tk.Frame(btn_bar, bg=PAN2)
        btn_inner.pack(side="left", padx=12, pady=10)

        def do_restore():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("No Selection",
                                       "Please select a version first.",
                                       parent=win)
                return
            tags = tree.item(sel[0], "tags")
            if not tags or tags[0] == "":
                return
            fname = tags[0]
            if not messagebox.askyesno(
                    "Restore Version",
                    "This will replace your current data with the selected "
                    "snapshot.\n\nYour current data will be saved as a backup "
                    "first.\n\nContinue?",
                    parent=win):
                return
            self._save_snapshot("before_restore")
            try:
                with open(os.path.join(HISTORY_DIR, fname),
                          "r", encoding="utf-8") as fh:
                    d = json.load(fh)
                self._dict_to_data(d)
                self._save_data()
                self._refresh_all()
                self._update_save_status("Restored from snapshot")
                messagebox.showinfo("Restored",
                                    "Data restored successfully.",
                                    parent=win)
                win.destroy()
            except Exception as e:
                messagebox.showerror("Error",
                                     "Failed to restore: " + str(e),
                                     parent=win)

        def do_delete():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("No Selection",
                                       "Please select a snapshot first.",
                                       parent=win)
                return
            tags = tree.item(sel[0], "tags")
            if not tags or tags[0] == "":
                return
            fname = tags[0]
            if messagebox.askyesno("Delete Snapshot",
                                   "Delete this snapshot?\nThis cannot be undone.",
                                   parent=win):
                try:
                    os.remove(os.path.join(HISTORY_DIR, fname))
                    tree.delete(sel[0])
                except Exception:
                    pass

        make_btn(btn_inner, "Restore Selected", do_restore,
                 bg=GREEN, fg="#0a1a0e", width=18).pack(side="left", padx=(0, 8))
        make_btn(btn_inner, "Delete Snapshot",  do_delete,
                 bg=RED, width=16).pack(side="left")

        close_frame = tk.Frame(btn_bar, bg=PAN2)
        close_frame.pack(side="right", padx=12, pady=10)
        make_btn(close_frame, "Close", win.destroy,
                 bg=PAN3, fg=MUTED, width=10).pack()

        # Divider above buttons
        tk.Frame(win, bg=BORDER, height=1).pack(fill="x", side="bottom")

        # ---- Snapshot list (fills remaining space) --------------------------
        listframe = tk.Frame(win, bg=PAN2,
                             highlightthickness=1,
                             highlightbackground=BORDER)
        listframe.pack(fill="both", expand=True, padx=16, pady=(8, 0))

        cols   = ("time", "label")
        heads  = ("Saved At", "Description")
        widths = [200, 420]
        s = ttk.Style()
        s.configure("Hist.Treeview",
                    background=PAN2, foreground=TEXT,
                    fieldbackground=PAN2, rowheight=30,
                    font=FONT_BODY)
        s.configure("Hist.Treeview.Heading",
                    background=PAN3, foreground=BLUE,
                    font=FONT_TABLEH, relief="flat")
        s.map("Hist.Treeview",
              background=[("selected", BORDER)],
              foreground=[("selected", WHITE)])

        tree = ttk.Treeview(listframe, columns=cols, show="headings",
                            style="Hist.Treeview")
        for col, head, w in zip(cols, heads, widths):
            tree.heading(col, text=head)
            tree.column(col, width=w, anchor="w")

        sb = ttk.Scrollbar(listframe, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")

        # Double-click to restore
        tree.bind("<Double-1>", lambda e: do_restore())

        if not snapshots:
            tree.insert("", "end", values=("No snapshots yet", ""))
        else:
            for fname, label, ts in snapshots:
                try:
                    dt = datetime.fromisoformat(ts)
                    ts_disp = dt.strftime("%d %b %Y  %H:%M:%S")
                except Exception:
                    ts_disp = ts
                tree.insert("", "end",
                            values=(ts_disp, label),
                            tags=(fname,))

    # ---- Password-protected version restore ---------------------------------

    def _protected_history(self):
        """Open version history only after password is verified."""
        PasswordDialog(self.root, self._open_history_unlocked)

    # ---- hidden trigger counter ---------------------------------------------
    # Triple-click the AcademiX title to trigger the password prompt

    def _register_hidden_trigger(self, widget):
        """Bind triple-click on a widget to open the protected history."""
        self._click_count  = 0
        self._click_timer  = None

        def on_click(event):
            self._click_count += 1
            if self._click_timer:
                self.root.after_cancel(self._click_timer)
            if self._click_count >= 3:
                self._click_count = 0
                self._protected_history()
            else:
                self._click_timer = self.root.after(
                    600, self._reset_click_count)

        widget.bind("<Button-1>", on_click, add="+")

    def _reset_click_count(self):
        self._click_count = 0

    def _manual_save(self):
        """Called by the Save Now button."""
        label = "manual_" + datetime.now().strftime("%H%M%S")
        self._save_data(snapshot_label=label)
        messagebox.showinfo("Saved",
                            "Data saved successfully!\n\nSnapshot: " + label)

    def _update_save_status(self, msg):
        """Update the status bar label."""
        self.save_status_lbl.config(text=msg, fg=GREEN)
        self.root.after(4000, lambda m=msg: self.save_status_lbl.config(
            text=m, fg=MUTED))

    # ---- seed ---------------------------------------------------------------

    def _seed(self):
        t = date.today()
        self.task_data = [
            ["Prepare lecture slides - SECI 3213",  "Teaching",   "High",   t,                "Pending"],
            ["Grade midterm scripts (48 students)", "Teaching",   "Urgent", t+timedelta(2),   "Pending"],
            ["Submit literature review draft",       "Research",   "High",   t-timedelta(3),   "Done"],
            ["Revise FRGS research proposal",        "Grant",      "High",   t+timedelta(7),   "Pending"],
            ["Complete Python for DS Module 4",     "Learning",   "Medium", t+timedelta(11),  "In Progress"],
            ["Register for IEEE ICSCA 2025",         "Conference", "Medium", t-timedelta(2),   "Done"],
            ["Submit final exam paper to registry", "Teaching",   "High",   t+timedelta(31),  "Pending"],
            ["Write abstract for NeurIPS 2025",      "Research",   "Medium", t+timedelta(15),  "Pending"],
        ]
        self.pub_data = [
            ["Deep Learning Fault Detection in IIoT",
             "IEEE Trans. Industrial IoT", "Under Review", 9.1, date(2025,2,10)],
            ["Federated Learning for Smart Grid",
             "Elsevier Energy and AI", "Accepted", 8.6, date(2024,11,5)],
            ["Explainable AI in Clinical Decision Support",
             "Nature Scientific Reports", "In Writing", 4.4, date(2025,3,1)],
        ]
        self.grant_data = [
            ["FRGS 2024/2025 Cycle 2",
             "MOE Malaysia", 120000, "Under Evaluation", date(2024,10,15)],
            ["UTM Tier 1 University Grant",
             "UTM Research", 50000, "Approved", date(2025,1,8)],
            ["MRANTI Smart Manufacturing Grant",
             "MRANTI", 200000, "Pending Docs", date(2025,3,5)],
        ]
        self.conf_data = [
            ["IEEE ICSCA 2025", "Kuala Lumpur, MY",
             date(2025,5,22), "Registered + Presenting"],
            ["NeurIPS 2025", "Vancouver, CA",
             date(2025,12,9), "Submitting Abstract"],
            ["ICLR 2026", "Singapore",
             date(2026,5,1), "Watching CFP"],
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

    # ---- calendar events ----------------------------------------------------

    def _get_calendar_events(self):
        events = {}
        for t in self.task_data:
            if t[4] != "Done":
                events.setdefault(t[3], []).append(t[0][:40])
        for c in self.conf_data:
            events.setdefault(c[2], []).append("[Conf] " + c[0][:35])
        for p in self.pub_data:
            if p[2] not in ("Accepted", "Published"):
                events.setdefault(p[4], []).append("[Pub] " + p[0][:35])
        return events

    # ---- build UI -----------------------------------------------------------

    def _build_ui(self):
        self._build_topbar()
        self._build_notebook()

    def _build_topbar(self):
        top = tk.Frame(self.root, bg=PAN, height=62)
        top.pack(fill="x", side="top")
        top.pack_propagate(False)

        # Left - App name
        left = tk.Frame(top, bg=PAN)
        left.pack(side="left", padx=16, pady=6)
        title_lbl = tk.Label(left, text="AcademiX", bg=PAN, fg=BLUE,
                 font=FONT_APPNAME, cursor="hand2")
        title_lbl.pack(anchor="w")
        tk.Label(left, text="Academic Research Dashboard",
                 bg=PAN, fg=MUTED, font=FONT_SMALL).pack(anchor="w")

        # Register hidden triple-click trigger on the title
        self._register_hidden_trigger(title_lbl)

        # Divider
        tk.Frame(top, bg=BORDER, width=1).pack(side="left", fill="y",
                                                padx=10, pady=8)

        # Profile area - clickable to edit
        profile = tk.Frame(top, bg=PAN, cursor="hand2")
        profile.pack(side="left", pady=6)
        profile.bind("<Button-1>", lambda e: self._edit_profile())

        self.name_lbl = tk.Label(profile, text=self.profile_name,
                                 bg=PAN, fg=TEXT, font=FONT_PROFILE,
                                 cursor="hand2")
        self.name_lbl.pack(anchor="w")
        self.name_lbl.bind("<Button-1>", lambda e: self._edit_profile())

        self.aff_lbl = tk.Label(profile, text=self.profile_aff,
                                bg=PAN, fg=MUTED, font=FONT_SMALL,
                                cursor="hand2")
        self.aff_lbl.pack(anchor="w")
        self.aff_lbl.bind("<Button-1>", lambda e: self._edit_profile())

        # Edit hint
        tk.Label(top, text="(click to edit)", bg=PAN, fg=BORDER,
                 font=FONT_SMALL).pack(side="left", padx=4)

        # Right side - history button + save status + date
        right = tk.Frame(top, bg=PAN)
        right.pack(side="right", padx=16, pady=6)

        tk.Label(right, text=date.today().strftime("%A"),
                 bg=PAN, fg=MUTED, font=FONT_SMALL).pack(anchor="e")
        tk.Label(right, text=date.today().strftime("%d %b %Y"),
                 bg=PAN, fg=TEXT, font=FONT_PROFILE).pack(anchor="e")

        # Divider
        tk.Frame(top, bg=BORDER, width=1).pack(side="right", fill="y",
                                                padx=10, pady=8)

        # Save controls
        save_panel = tk.Frame(top, bg=PAN)
        save_panel.pack(side="right", padx=8, pady=6)

        self.save_status_lbl = tk.Label(save_panel, text="Not saved yet",
                                        bg=PAN, fg=MUTED, font=FONT_SMALL)
        self.save_status_lbl.pack(anchor="e", pady=(0, 2))

        btn_row = tk.Frame(save_panel, bg=PAN)
        btn_row.pack(anchor="e")

        make_btn(btn_row, "Save Now", self._manual_save,
                 bg=PAN3, fg=TEAL, width=10).pack(side="left", padx=(0, 6))
        # History button - always requires password
        make_btn(btn_row, "History", self._protected_history,
                 bg=PAN3, fg=PURPLE, width=10).pack(side="left")

        # Second hidden trigger: triple-click the date label
        self._register_hidden_trigger(right)

    def _build_notebook(self):
        # Custom tab bar - bypasses ttk so size is fully controllable
        self._tab_frames = []
        self._tab_btns   = []
        self._active_tab = 0

        TAB_H      = 46
        TAB_FONT   = ("Helvetica", 13, "bold")
        TAB_LABELS = ["  Overview  ", "  Tasks / To-Do  ",
                      "  Publications  ", "  Grants  ",
                      "  Conferences  ", "  Skills  "]

        # Tab button bar
        tab_bar = tk.Frame(self.root, bg=PAN, height=TAB_H)
        tab_bar.pack(fill="x")
        tab_bar.pack_propagate(False)

        # Content area
        content = tk.Frame(self.root, bg=BG)
        content.pack(fill="both", expand=True)

        # Create one frame per tab (stacked, only one visible at a time)
        for _ in TAB_LABELS:
            f = tk.Frame(content, bg=BG)
            f.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._tab_frames.append(f)

        def switch_tab(idx):
            self._active_tab = idx
            # Show selected frame, hide others
            for i, f in enumerate(self._tab_frames):
                if i == idx:
                    f.lift()
                else:
                    f.lower()
            # Update button styles
            for i, btn in enumerate(self._tab_btns):
                if i == idx:
                    btn.config(bg=BG, fg=BLUE,
                               relief="flat",
                               bd=0)
                    # Active indicator line
                    btn._indicator.config(bg=BLUE)
                else:
                    btn.config(bg=PAN, fg=MUTED,
                               relief="flat",
                               bd=0)
                    btn._indicator.config(bg=PAN)

        # Build tab buttons
        for i, label in enumerate(TAB_LABELS):
            frame = tk.Frame(tab_bar, bg=PAN)
            frame.pack(side="left")

            btn = tk.Button(frame, text=label,
                            font=TAB_FONT,
                            bg=PAN, fg=MUTED,
                            relief="flat", bd=0,
                            padx=18, pady=10,
                            activebackground=PAN3,
                            activeforeground=TEXT,
                            cursor="hand2",
                            command=lambda idx=i: switch_tab(idx))
            btn.pack(side="top", fill="x")

            # Bottom indicator line
            indicator = tk.Frame(frame, bg=PAN, height=3)
            indicator.pack(fill="x", side="bottom")
            btn._indicator = indicator

            btn.bind("<Enter>", lambda e, b=btn, idx=i:
                     b.config(fg=TEXT) if idx != self._active_tab else None)
            btn.bind("<Leave>", lambda e, b=btn, idx=i:
                     b.config(fg=MUTED) if idx != self._active_tab else None)

            self._tab_btns.append(btn)

        # Bottom border of tab bar
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")

        # Assign named references
        (self.tab_ov, self.tab_tk, self.tab_pb,
         self.tab_gr, self.tab_cf, self.tab_sk) = self._tab_frames

        # Show first tab
        switch_tab(0)

        self._build_overview(self.tab_ov)
        self._build_tasks(self.tab_tk)
        self._build_pubs(self.tab_pb)
        self._build_grants(self.tab_gr)
        self._build_confs(self.tab_cf)
        self._build_skills(self.tab_sk)

    # =========================================================================
    #  Overview
    # =========================================================================

    def _build_overview(self, p):
        # Stat row
        sf = tk.Frame(p, bg=PAN, height=108)
        sf.pack(fill="x", padx=12, pady=(12, 8))
        sf.pack_propagate(False)
        self.stat_labels = []
        for num, lbl, col in [
            ("0", "Active Tasks",   BLUE),
            ("0", "Due This Week",  RED),
            ("0", "Publications",   GREEN),
            ("0", "Grants Applied", PURPLE),
            ("0", "Conferences",    ORANGE),
            ("0", "Skills Tracked", TEAL),
        ]:
            card = tk.Frame(sf, bg=PAN3,
                            highlightthickness=1,
                            highlightbackground=BORDER)
            card.pack(side="left", expand=True, fill="both",
                      padx=5, pady=6)
            n = tk.Label(card, text=num, bg=PAN3, fg=col, font=FONT_STAT)
            n.pack(pady=(8, 2))
            tk.Label(card, text=lbl, bg=PAN3, fg=MUTED,
                     font=FONT_STATLBL).pack(pady=(0, 6))
            self.stat_labels.append(n)

        # 3-column body
        body = tk.Frame(p, bg=BG)
        body.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        body.columnconfigure(0, weight=20, minsize=260)
        body.columnconfigure(1, weight=42)
        body.columnconfigure(2, weight=22, minsize=240)
        body.rowconfigure(0, weight=1)

        left   = tk.Frame(body, bg=PAN,
                          highlightthickness=1,
                          highlightbackground=BORDER)
        middle = tk.Frame(body, bg=PAN,
                          highlightthickness=1,
                          highlightbackground=BORDER)
        right  = tk.Frame(body, bg=PAN,
                          highlightthickness=1,
                          highlightbackground=BORDER)

        left.grid(  row=0, column=0, sticky="nsew", padx=(0, 5))
        middle.grid(row=0, column=1, sticky="nsew", padx=(0, 5))
        right.grid( row=0, column=2, sticky="nsew")

        self._build_ov_left(left)
        self._build_ov_middle(middle)
        self._build_ov_right(right)

    def _build_ov_left(self, p):
        # Progress section at top
        tk.Label(p, text="Progress", bg=PAN, fg=TEXT,
                 font=FONT_HEAD).pack(anchor="w", padx=12, pady=(12, 6))
        self.gauges = {}
        for key, lbl, val, col in [
            ("sem",   "Semester Progress", 67, BLUE),
            ("tasks", "Tasks Completed",    0, GREEN),
            ("grant", "Grant Success Rate", 0, ORANGE),
        ]:
            row = tk.Frame(p, bg=PAN)
            row.pack(fill="x", padx=12, pady=(4, 0))
            tk.Label(row, text=lbl, bg=PAN, fg=MUTED,
                     font=FONT_SMALL, width=18,
                     anchor="w").pack(side="left")
            pct = tk.Label(row, text=str(val)+"%", bg=PAN, fg=col,
                           font=FONT_MONO, width=5, anchor="e")
            pct.pack(side="right")
            bg_bar = tk.Frame(p, bg=BORDER, height=8)
            bg_bar.pack(fill="x", padx=12, pady=(1, 6))
            bg_bar.pack_propagate(False)
            fill = tk.Frame(bg_bar, bg=col, height=8)
            fill.place(relwidth=val/100, relheight=1)
            self.gauges[key] = (fill, pct, col)

        tk.Frame(p, bg=BORDER, height=1).pack(fill="x", padx=12, pady=(8, 0))

        # Calendar fills all remaining space
        cal_frame = tk.Frame(p, bg=PAN)
        cal_frame.pack(fill="both", expand=True, padx=4, pady=(6, 4))

        tk.Label(cal_frame, text="Calendar", bg=PAN, fg=TEXT,
                 font=FONT_HEAD).pack(anchor="w", padx=8, pady=(0, 4))

        self.mini_cal = MiniCalendar(cal_frame, self._get_calendar_events)
        self.mini_cal.pack(fill="both", expand=True, padx=2)

        # Legend at very bottom
        leg = tk.Frame(p, bg=PAN)
        leg.pack(fill="x", padx=12, pady=(4, 10))
        for dot_col, label in [(BLUE, "Today"), (ORANGE, "Due"), (RED, "Overdue")]:
            c = tk.Canvas(leg, bg=PAN, width=12, height=12,
                          highlightthickness=0)
            c.pack(side="left")
            c.create_oval(1, 1, 11, 11, fill=dot_col, outline="")
            tk.Label(leg, text=label, bg=PAN, fg=MUTED,
                     font=FONT_SMALL).pack(side="left", padx=(2, 10))

    def _build_ov_middle(self, p):
        section_head(p, "To-Do  -  Pending Tasks")
        self.ov_todo_frame = tk.Frame(p, bg=PAN)
        self.ov_todo_frame.pack(fill="x", padx=8, pady=(0, 4))

        section_head(p, "Publications")
        self.ov_pub_frame = tk.Frame(p, bg=PAN)
        self.ov_pub_frame.pack(fill="x", padx=8, pady=(0, 4))

        section_head(p, "Grants")
        self.ov_grant_frame = tk.Frame(p, bg=PAN)
        self.ov_grant_frame.pack(fill="x", padx=8, pady=(0, 4))

        section_head(p, "Recent Achievements", GREEN)
        af = tk.Frame(p, bg=PAN)
        af.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.activity_list = tk.Listbox(
            af, bg=PAN2, fg=GREEN, font=FONT_BODY,
            relief="flat", selectbackground=PAN3,
            selectforeground=GREEN, activestyle="none",
            bd=0, height=4)
        self.activity_list.pack(fill="both", expand=True, padx=2, pady=4)

    def _build_ov_right(self, p):
        section_head(p, "Upcoming Deadlines", RED)
        df = tk.Frame(p, bg=PAN)
        df.pack(fill="x", padx=8, pady=(0, 4))
        self.ov_deadline_list = tk.Listbox(
            df, bg=PAN2, fg=TEXT, font=FONT_BODY,
            relief="flat", selectbackground=PAN3,
            selectforeground=WHITE, activestyle="none",
            bd=0, height=6)
        self.ov_deadline_list.pack(fill="x", padx=2, pady=4)

        section_head(p, "Future Conferences", ORANGE)
        cf = tk.Frame(p, bg=PAN)
        cf.pack(fill="x", padx=8, pady=(0, 4))
        self.ov_conf_list = tk.Listbox(
            cf, bg=PAN2, fg=ORANGE, font=FONT_BODY,
            relief="flat", selectbackground=PAN3,
            selectforeground=WHITE, activestyle="none",
            bd=0, height=4)
        self.ov_conf_list.pack(fill="x", padx=2, pady=4)

        section_head(p, "Skills to Learn", TEAL)
        skf = tk.Frame(p, bg=PAN)
        skf.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.ov_skill_frame = tk.Frame(skf, bg=PAN)
        self.ov_skill_frame.pack(fill="both", expand=True, padx=2, pady=4)

    # =========================================================================
    #  Tasks Tab
    # =========================================================================

    def _build_tasks(self, p):
        form = tk.Frame(p, bg=PAN,
                        highlightthickness=1,
                        highlightbackground=BORDER)
        form.pack(fill="x", padx=12, pady=(12, 6))
        tk.Label(form, text="Add New Task", bg=PAN, fg=TEXT,
                 font=FONT_HEAD).grid(row=0, column=0, columnspan=7,
                                      sticky="w", padx=14, pady=(10, 4))

        self.tk_title = make_entry(form, "Task title...", width=38)
        self.tk_title.grid(row=1, column=0, padx=(14, 6), pady=8, ipady=4)

        self.tk_cat = make_combo(form, ["Teaching","Research","Grant",
                                        "Conference","Learning","Admin"], width=13)
        self.tk_cat.grid(row=1, column=1, padx=6, pady=8)

        self.tk_prio = make_combo(form, ["Urgent","High","Medium","Low"], width=10)
        self.tk_prio.grid(row=1, column=2, padx=6, pady=8)

        tk.Label(form, text="Due:", bg=PAN, fg=MUTED,
                 font=FONT_SMALL).grid(row=1, column=3, padx=(8, 2))
        self.tk_due = make_date(form, date.today()+timedelta(7))
        self.tk_due.grid(row=1, column=4, padx=6, pady=8)

        make_btn(form, "Add Task", self._add_task,
                 bg=BLUE, width=12).grid(row=1, column=5,
                                          padx=(8, 14), pady=8)

        br = tk.Frame(form, bg=PAN)
        br.grid(row=2, column=0, columnspan=7, sticky="w",
                padx=14, pady=(0, 10))
        make_btn(br, "Mark Done",       self._mark_done,
                 bg=GREEN, fg="#0a1a0e", width=12).pack(side="left", padx=(0, 8))
        make_btn(br, "Delete Selected", self._delete_task,
                 bg=RED, width=14).pack(side="left")
        tk.Label(br, text="  or press  Delete  key",
                 bg=PAN, fg=MUTED, font=FONT_SMALL).pack(side="left", padx=8)

        tf = tk.Frame(p, bg=BG)
        tf.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.task_tree, tsb = styled_tree(
            tf, ("title","cat","prio","due","status"),
            ("Title", "Category", "Priority", "Due Date", "Status"),
            [450, 120, 100, 120, 120], height=24)
        self.task_tree.pack(side="left", fill="both", expand=True)
        tsb.pack(side="left", fill="y")
        bind_delete(self.task_tree, self._delete_task)
        self.task_tree.bind("<Double-1>", lambda e: self._mark_done())

    # =========================================================================
    #  Publications Tab
    # =========================================================================

    def _build_pubs(self, p):
        form = tk.Frame(p, bg=PAN,
                        highlightthickness=1,
                        highlightbackground=BORDER)
        form.pack(fill="x", padx=12, pady=(12, 6))
        tk.Label(form, text="Add Publication", bg=PAN, fg=TEXT,
                 font=FONT_HEAD).grid(row=0, column=0, columnspan=7,
                                      sticky="w", padx=14, pady=(10, 4))

        self.pb_title   = make_entry(form, "Paper title...", width=36)
        self.pb_title.grid(row=1, column=0, padx=(14, 6), pady=8, ipady=4)

        self.pb_journal = make_entry(form, "Journal or venue...", width=26)
        self.pb_journal.grid(row=1, column=1, padx=6, pady=8, ipady=4)

        self.pb_status  = make_combo(form, ["In Writing","Under Review",
                                            "Major Revision","Minor Revision",
                                            "Accepted","Published","Rejected"], width=15)
        self.pb_status.grid(row=1, column=2, padx=6, pady=8)

        tk.Label(form, text="IF:", bg=PAN, fg=MUTED,
                 font=FONT_SMALL).grid(row=1, column=3, padx=(6, 2))
        self.pb_if = make_entry(form, "0.0", width=7)
        self.pb_if.grid(row=1, column=4, padx=6, pady=8, ipady=4)

        tk.Label(form, text="Submit Date:", bg=PAN, fg=MUTED,
                 font=FONT_SMALL).grid(row=2, column=0, padx=(14, 4),
                                       sticky="w", pady=(0, 10))
        self.pb_date = make_date(form, date.today())
        self.pb_date.grid(row=2, column=1, padx=6, pady=(0, 10), sticky="w")

        make_btn(form, "Add",    self._add_pub,
                 bg=BLUE, width=10).grid(row=1, column=5, padx=(8, 6))
        make_btn(form, "Delete", self._del_pub,
                 bg=RED,  width=10).grid(row=2, column=5, padx=(8, 6),
                                          pady=(0, 10))

        pf = tk.Frame(p, bg=BG)
        pf.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.pub_tree, psb = styled_tree(
            pf, ("title","journal","status","if","submitted"),
            ("Title", "Journal / Venue", "Status", "IF", "Submitted"),
            [400, 260, 140, 70, 120], height=24)
        self.pub_tree.pack(side="left", fill="both", expand=True)
        psb.pack(side="left", fill="y")
        bind_delete(self.pub_tree, self._del_pub)

    # =========================================================================
    #  Grants Tab
    # =========================================================================

    def _build_grants(self, p):
        form = tk.Frame(p, bg=PAN,
                        highlightthickness=1,
                        highlightbackground=BORDER)
        form.pack(fill="x", padx=12, pady=(12, 6))
        tk.Label(form, text="Add Grant Application", bg=PAN, fg=TEXT,
                 font=FONT_HEAD).grid(row=0, column=0, columnspan=7,
                                      sticky="w", padx=14, pady=(10, 4))

        self.gr_name   = make_entry(form, "Grant name or scheme...", width=30)
        self.gr_name.grid(row=1, column=0, padx=(14, 6), pady=8, ipady=4)

        self.gr_body   = make_entry(form, "Funding body...", width=20)
        self.gr_body.grid(row=1, column=1, padx=6, pady=8, ipady=4)

        tk.Label(form, text="RM:", bg=PAN, fg=MUTED,
                 font=FONT_SMALL).grid(row=1, column=2, padx=(8, 2))
        self.gr_amt    = make_entry(form, "0", width=10)
        self.gr_amt.grid(row=1, column=3, padx=6, pady=8, ipady=4)

        self.gr_status = make_combo(form, ["Preparing","Submitted","Under Evaluation",
                                           "Pending Docs","Approved","Rejected","Completed"], width=17)
        self.gr_status.grid(row=1, column=4, padx=6, pady=8)

        tk.Label(form, text="Apply Date:", bg=PAN, fg=MUTED,
                 font=FONT_SMALL).grid(row=2, column=0, padx=(14, 4),
                                       sticky="w", pady=(0, 10))
        self.gr_date   = make_date(form, date.today())
        self.gr_date.grid(row=2, column=1, padx=6, pady=(0, 10), sticky="w")

        make_btn(form, "Add Grant", self._add_grant,
                 bg=PURPLE, width=12).grid(row=1, column=5, padx=(8, 14))
        make_btn(form, "Delete",    self._del_grant,
                 bg=RED,    width=12).grid(row=2, column=5, padx=(8, 14),
                                            pady=(0, 10))

        gf = tk.Frame(p, bg=BG)
        gf.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.grant_tree, gsb = styled_tree(
            gf, ("name","body","amount","status","applied"),
            ("Grant Name", "Funding Body", "Amount", "Status", "Applied"),
            [320, 200, 120, 150, 120], height=24)
        self.grant_tree.pack(side="left", fill="both", expand=True)
        gsb.pack(side="left", fill="y")
        bind_delete(self.grant_tree, self._del_grant)

    # =========================================================================
    #  Conferences Tab
    # =========================================================================

    def _build_confs(self, p):
        form = tk.Frame(p, bg=PAN,
                        highlightthickness=1,
                        highlightbackground=BORDER)
        form.pack(fill="x", padx=12, pady=(12, 6))
        tk.Label(form, text="Add Conference", bg=PAN, fg=TEXT,
                 font=FONT_HEAD).grid(row=0, column=0, columnspan=6,
                                      sticky="w", padx=14, pady=(10, 4))

        self.cf_name   = make_entry(form, "Conference name...", width=32)
        self.cf_name.grid(row=1, column=0, padx=(14, 6), pady=8, ipady=4)

        self.cf_loc    = make_entry(form, "City, Country...", width=20)
        self.cf_loc.grid(row=1, column=1, padx=6, pady=8, ipady=4)

        tk.Label(form, text="Date:", bg=PAN, fg=MUTED,
                 font=FONT_SMALL).grid(row=1, column=2, padx=(8, 2))
        self.cf_date   = make_date(form, date.today()+timedelta(90))
        self.cf_date.grid(row=1, column=3, padx=6, pady=8)

        self.cf_status = make_combo(form, ["Watching CFP","Abstract Submitted",
                                           "Paper Submitted","Accepted","Registered",
                                           "Registered + Presenting","Attended"], width=24)
        self.cf_status.grid(row=2, column=0, padx=(14, 6), pady=(0, 10), sticky="w")

        make_btn(form, "Add",    self._add_conf,
                 bg=ORANGE, fg="#1a0d00", width=10).grid(row=1, column=4, padx=(8, 14))
        make_btn(form, "Delete", self._del_conf,
                 bg=RED,    width=10).grid(row=2, column=4, padx=(8, 14),
                                            pady=(0, 10))

        cf = tk.Frame(p, bg=BG)
        cf.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.conf_tree, csb = styled_tree(
            cf, ("name","loc","date","status"),
            ("Conference Name", "Location", "Date", "Status"),
            [380, 220, 120, 210], height=24)
        self.conf_tree.pack(side="left", fill="both", expand=True)
        csb.pack(side="left", fill="y")
        bind_delete(self.conf_tree, self._del_conf)

    # =========================================================================
    #  Skills Tab
    # =========================================================================

    def _build_skills(self, p):
        form = tk.Frame(p, bg=PAN,
                        highlightthickness=1,
                        highlightbackground=BORDER)
        form.pack(fill="x", padx=12, pady=(12, 6))
        tk.Label(form, text="Add Skill to Learn", bg=PAN, fg=TEXT,
                 font=FONT_HEAD).grid(row=0, column=0, columnspan=7,
                                      sticky="w", padx=14, pady=(10, 4))

        self.sk_name = make_entry(form, "Skill name...", width=28)
        self.sk_name.grid(row=1, column=0, padx=(14, 6), pady=8, ipady=4)

        self.sk_cat  = make_combo(form, ["Programming","AI/ML","Writing","Academic",
                                          "Teaching","Research","Soft Skills","Other"], width=14)
        self.sk_cat.grid(row=1, column=1, padx=6, pady=8)

        tk.Label(form, text="Progress:", bg=PAN, fg=MUTED,
                 font=FONT_SMALL).grid(row=1, column=2, padx=(8, 4))

        self.sk_var = tk.IntVar(value=0)
        self.sk_lbl = tk.Label(form, text="0%", bg=PAN, fg=BLUE,
                               font=("Helvetica", 12, "bold"), width=5)
        self.sk_lbl.grid(row=1, column=4, padx=6)

        sl = ttk.Scale(form, from_=0, to=100, orient="horizontal",
                       variable=self.sk_var,
                       command=lambda v: self.sk_lbl.config(
                           text=str(int(float(v))) + "%"))
        sl.grid(row=1, column=3, padx=4, pady=8, sticky="ew")
        form.columnconfigure(3, weight=1)

        make_btn(form, "Add Skill", self._add_skill,
                 bg=GREEN, fg="#0a1a0e", width=12).grid(row=1, column=5, padx=(8, 6))
        make_btn(form, "Delete",    self._del_skill,
                 bg=RED, width=12).grid(row=2, column=5, padx=(8, 6),
                                         pady=(0, 10))

        bot = tk.Frame(p, bg=BG)
        bot.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        sf = tk.Frame(bot, bg=BG)
        sf.pack(side="left", fill="both", expand=True)
        self.skill_tree, ssb = styled_tree(
            sf, ("skill","cat","prog"),
            ("Skill", "Category", "Progress (%)"),
            [300, 140, 110], height=24)
        self.skill_tree.pack(side="left", fill="both", expand=True)
        ssb.pack(side="left", fill="y")
        bind_delete(self.skill_tree, self._del_skill)

        self.chart_frame = tk.Frame(bot, bg=PAN,
                                    highlightthickness=1,
                                    highlightbackground=BORDER)
        self.chart_frame.pack(side="left", fill="both",
                              expand=True, padx=(10, 0))
        self._draw_chart()

    def _draw_chart(self):
        for w in self.chart_frame.winfo_children():
            w.destroy()
        n = len(self.skill_data)
        fig_h = max(3.5, n * 0.6)
        fig, ax = plt.subplots(figsize=(6, fig_h), dpi=96)
        fig.patch.set_facecolor(PAN)
        ax.set_facecolor(PAN)
        if n == 0:
            ax.text(0.5, 0.5, "No skills added yet",
                    ha="center", va="center", color=MUTED,
                    fontsize=11, transform=ax.transAxes)
        else:
            vals   = [r[2] for r in self.skill_data]
            names  = [r[0] for r in self.skill_data]
            colors = [PALETTE[i % len(PALETTE)] for i in range(n)]
            bars   = ax.barh(range(n), vals, color=colors,
                             height=0.6, edgecolor="none")
            for i, v in enumerate(vals):
                ax.text(v+1, i, str(v)+"%", va="center", ha="left",
                        color=TEXT, fontsize=9, fontweight="bold")
            ax.set_yticks(range(n))
            ax.set_yticklabels(names, color=TEXT, fontsize=9)
            ax.set_xlim(0, 118)
            ax.set_ylim(-0.6, n-0.4)
            ax.invert_yaxis()
            ax.tick_params(axis="x", colors=MUTED, labelsize=8)
            ax.tick_params(axis="y", colors=TEXT,  labelsize=9,
                           length=0, pad=6)
            for sp in ["top","right","left"]:
                ax.spines[sp].set_visible(False)
            ax.spines["bottom"].set_color(BORDER)
            ax.xaxis.grid(True, color=BORDER, linewidth=0.6,
                          linestyle="--")
            ax.set_axisbelow(True)
            ax.set_title("Skills Progress", color=TEXT,
                         fontsize=11, pad=10, fontweight="bold")
        plt.tight_layout(pad=1.4)
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        plt.close(fig)

    # =========================================================================
    #  Refresh
    # =========================================================================

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
        for key, pct in [("tasks", t_pct), ("grant", g_pct)]:
            fill, lbl, col = self.gauges[key]
            fill.place(relwidth=max(0.01, pct/100), relheight=1)
            lbl.config(text=str(pct)+"%")

        # Calendar
        self.mini_cal.refresh()

        # To-Do list
        for w in self.ov_todo_frame.winfo_children():
            w.destroy()
        pending = [t for t in self.task_data if t[4] != "Done"]
        pending.sort(key=lambda x: x[3])
        for t in pending[:7]:
            diff = (t[3]-today).days
            if diff < 0:
                tag = "OVERDUE"; tag_col = RED
            elif diff == 0:
                tag = "TODAY";   tag_col = ORANGE
            elif diff <= 3:
                tag = str(diff)+"d"; tag_col = ORANGE
            else:
                tag = str(diff)+"d"; tag_col = MUTED
            prio_col = {"Urgent":RED,"High":ORANGE,
                        "Medium":BLUE,"Low":TEAL}.get(t[2], MUTED)
            row = tk.Frame(self.ov_todo_frame, bg=PAN2,
                           highlightthickness=0)
            row.pack(fill="x", padx=4, pady=2)
            dot = tk.Canvas(row, bg=PAN2, width=10, height=10,
                            highlightthickness=0)
            dot.pack(side="left", padx=(8,4), pady=8)
            dot.create_oval(1,1,9,9, fill=prio_col, outline="")
            tk.Label(row, text=t[0][:44], bg=PAN2, fg=TEXT,
                     font=FONT_BODY, anchor="w").pack(side="left",
                                                       expand=True)
            tk.Label(row, text=tag, bg=PAN2, fg=tag_col,
                     font=FONT_MONO, width=8,
                     anchor="e").pack(side="right", padx=8)

        # Publications
        for w in self.ov_pub_frame.winfo_children():
            w.destroy()
        for pub in self.pub_data[:4]:
            col = status_color(pub[2])
            row = tk.Frame(self.ov_pub_frame, bg=PAN2)
            row.pack(fill="x", padx=4, pady=2)
            tk.Label(row, text="*", bg=PAN2, fg=col,
                     font=FONT_BODY).pack(side="left", padx=(8,4), pady=6)
            tk.Label(row, text=pub[0][:44], bg=PAN2, fg=TEXT,
                     font=FONT_BODY, anchor="w").pack(side="left",
                                                       expand=True)
            tk.Label(row, text=pub[2], bg=PAN2, fg=col,
                     font=FONT_SMALL).pack(side="right", padx=8)

        # Grants
        for w in self.ov_grant_frame.winfo_children():
            w.destroy()
        for g in self.grant_data[:4]:
            col = status_color(g[3])
            row = tk.Frame(self.ov_grant_frame, bg=PAN2)
            row.pack(fill="x", padx=4, pady=2)
            tk.Label(row, text="*", bg=PAN2, fg=col,
                     font=FONT_BODY).pack(side="left", padx=(8,4), pady=6)
            tk.Label(row, text=g[0][:38], bg=PAN2, fg=TEXT,
                     font=FONT_BODY, anchor="w").pack(side="left",
                                                       expand=True)
            tk.Label(row, text="RM "+str(g[2]), bg=PAN2, fg=MUTED,
                     font=FONT_SMALL).pack(side="right", padx=2)
            tk.Label(row, text=g[3], bg=PAN2, fg=col,
                     font=FONT_SMALL).pack(side="right", padx=8)

        # Achievements
        self.activity_list.delete(0, tk.END)
        items = []
        for t in self.task_data:
            if t[4]=="Done":
                items.append("[Done]   " + t[0])
        for pub in self.pub_data:
            if pub[2] in ("Accepted","Published"):
                items.append("[Paper]  Accepted: " + pub[0][:40])
        for g in self.grant_data:
            if g[3]=="Approved":
                items.append("[Grant]  Approved: " + g[0][:35])
        for item in (items or ["No completed items yet."]):
            self.activity_list.insert(tk.END, item)

        # Upcoming Deadlines
        self.ov_deadline_list.delete(0, tk.END)
        pending2 = [(t,(t[3]-today).days)
                    for t in self.task_data if t[4]!="Done"]
        pending2.sort(key=lambda x: x[1])
        for task, diff in pending2[:8]:
            if diff < 0:
                tag = "OVERDUE "+str(abs(diff))+"d"
            elif diff == 0:
                tag = "TODAY"
            else:
                tag = str(diff)+"d left"
            line = "{:<14}  {}".format(tag, task[0][:32])
            self.ov_deadline_list.insert(tk.END, line)
            idx = self.ov_deadline_list.size() - 1
            if diff < 0:
                self.ov_deadline_list.itemconfig(idx, fg=RED)
            elif diff <= 3:
                self.ov_deadline_list.itemconfig(idx, fg=ORANGE)
            else:
                self.ov_deadline_list.itemconfig(idx, fg=TEXT)

        # Future Conferences
        self.ov_conf_list.delete(0, tk.END)
        upcoming = sorted(self.conf_data, key=lambda x: x[2])
        for c in upcoming[:6]:
            diff = (c[2]-today).days
            line = c[2].strftime("%d %b %y") + "  " + c[0][:32]
            self.ov_conf_list.insert(tk.END, line)
            idx = self.ov_conf_list.size()-1
            col = status_color(c[3])
            self.ov_conf_list.itemconfig(idx, fg=col)

        # Skills mini bars
        for w in self.ov_skill_frame.winfo_children():
            w.destroy()
        for i, s in enumerate(self.skill_data[:7]):
            col = PALETTE[i % len(PALETTE)]
            row = tk.Frame(self.ov_skill_frame, bg=PAN)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=s[0][:26], bg=PAN, fg=TEXT,
                     font=FONT_BODY, width=22,
                     anchor="w").pack(side="left", padx=(4,6))
            bg_bar = tk.Frame(row, bg=BORDER, height=8, width=100)
            bg_bar.pack(side="left")
            bg_bar.pack_propagate(False)
            fill_w = max(2, int(100*s[2]/100))
            tk.Frame(bg_bar, bg=col, height=8,
                     width=fill_w).place(x=0, y=0, relheight=1)
            tk.Label(row, text=str(s[2])+"%", bg=PAN, fg=col,
                     font=FONT_MONO, width=5).pack(side="left", padx=4)

    def _refresh_tasks(self):
        for r in self.task_tree.get_children():
            self.task_tree.delete(r)
        for t in self.task_data:
            self.task_tree.insert("","end",
                values=(t[0], t[1], t[2],
                        t[3].strftime("%d %b %Y"), t[4]))

    def _refresh_pubs(self):
        for r in self.pub_tree.get_children():
            self.pub_tree.delete(r)
        for p in self.pub_data:
            self.pub_tree.insert("","end",
                values=(p[0], p[1], p[2],
                        "{:.1f}".format(p[3]),
                        p[4].strftime("%d %b %Y")))

    def _refresh_grants(self):
        for r in self.grant_tree.get_children():
            self.grant_tree.delete(r)
        for g in self.grant_data:
            self.grant_tree.insert("","end",
                values=(g[0], g[1],
                        "RM {:,}".format(g[2]),
                        g[3],
                        g[4].strftime("%d %b %Y")))

    def _refresh_confs(self):
        for r in self.conf_tree.get_children():
            self.conf_tree.delete(r)
        for c in self.conf_data:
            self.conf_tree.insert("","end",
                values=(c[0], c[1],
                        c[2].strftime("%d %b %Y"),
                        c[3]))

    def _refresh_skills(self):
        for r in self.skill_tree.get_children():
            self.skill_tree.delete(r)
        for s in self.skill_data:
            self.skill_tree.insert("","end",
                values=(s[0], s[1], s[2]))
        self._draw_chart()

    # =========================================================================
    #  Callbacks
    # =========================================================================

    def _confirm_delete(self, label="item"):
        return messagebox.askyesno(
            "Confirm Delete",
            "Delete this " + label + "?\n\nThis cannot be undone.",
            icon="warning")

    def _add_task(self):
        title = entry_val(self.tk_title, "Task title...")
        if not title:
            messagebox.showwarning("Input Required",
                                   "Please enter a task title.")
            return
        self.task_data.append([title, self.tk_cat.get(), self.tk_prio.get(),
                                self.tk_due.get_date(), "Pending"])
        self.tk_title.delete(0, tk.END)
        self.tk_title.insert(0, "Task title...")
        self.tk_title.config(fg=MUTED)
        self._refresh_tasks()
        self._refresh_ov()
        self._save_data(snapshot_label="add_task_" + title[:30])

    def _mark_done(self):
        sel = self.task_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection",
                                   "Please select a row first.")
            return
        self.task_data[self.task_tree.index(sel[0])][4] = "Done"
        self._refresh_tasks()
        self._refresh_ov()
        self._save_data(snapshot_label="mark_done")

    def _delete_task(self):
        sel = self.task_tree.selection()
        if not sel:
            return
        if self._confirm_delete("task"):
            del self.task_data[self.task_tree.index(sel[0])]
            self._refresh_tasks()
            self._refresh_ov()
            self._save_data(snapshot_label="delete_task")

    def _add_pub(self):
        title   = entry_val(self.pb_title,   "Paper title...")
        journal = entry_val(self.pb_journal, "Journal or venue...")
        if not title or not journal:
            messagebox.showwarning("Input Required",
                                   "Please enter title and journal.")
            return
        try:
            impact = float(entry_val(self.pb_if, "0.0") or 0)
        except ValueError:
            impact = 0.0
        self.pub_data.append([title, journal, self.pb_status.get(),
                               impact, self.pb_date.get_date()])
        for w, ph in [(self.pb_title,   "Paper title..."),
                      (self.pb_journal, "Journal or venue...")]:
            w.delete(0, tk.END)
            w.insert(0, ph)
            w.config(fg=MUTED)
        self._refresh_pubs()
        self._refresh_ov()
        self._save_data(snapshot_label="add_pub_" + title[:30])

    def _del_pub(self):
        sel = self.pub_tree.selection()
        if not sel:
            return
        if self._confirm_delete("publication"):
            del self.pub_data[self.pub_tree.index(sel[0])]
            self._refresh_pubs()
            self._refresh_ov()
            self._save_data(snapshot_label="delete_pub")

    def _add_grant(self):
        name = entry_val(self.gr_name, "Grant name or scheme...")
        if not name:
            messagebox.showwarning("Input Required",
                                   "Please enter a grant name.")
            return
        try:
            amt = int(entry_val(self.gr_amt, "0") or 0)
        except ValueError:
            amt = 0
        self.grant_data.append([name,
                                 entry_val(self.gr_body, "Funding body..."),
                                 amt, self.gr_status.get(),
                                 self.gr_date.get_date()])
        for w, ph in [(self.gr_name, "Grant name or scheme..."),
                      (self.gr_body, "Funding body...")]:
            w.delete(0, tk.END)
            w.insert(0, ph)
            w.config(fg=MUTED)
        self._refresh_grants()
        self._refresh_ov()
        self._save_data(snapshot_label="add_grant_" + name[:30])

    def _del_grant(self):
        sel = self.grant_tree.selection()
        if not sel:
            return
        if self._confirm_delete("grant"):
            del self.grant_data[self.grant_tree.index(sel[0])]
            self._refresh_grants()
            self._refresh_ov()
            self._save_data(snapshot_label="delete_grant")

    def _add_conf(self):
        name = entry_val(self.cf_name, "Conference name...")
        if not name:
            messagebox.showwarning("Input Required",
                                   "Please enter a conference name.")
            return
        self.conf_data.append([name,
                                entry_val(self.cf_loc, "City, Country..."),
                                self.cf_date.get_date(),
                                self.cf_status.get()])
        for w, ph in [(self.cf_name, "Conference name..."),
                      (self.cf_loc,  "City, Country...")]:
            w.delete(0, tk.END)
            w.insert(0, ph)
            w.config(fg=MUTED)
        self._refresh_confs()
        self._refresh_ov()
        self._save_data(snapshot_label="add_conf_" + name[:30])

    def _del_conf(self):
        sel = self.conf_tree.selection()
        if not sel:
            return
        if self._confirm_delete("conference"):
            del self.conf_data[self.conf_tree.index(sel[0])]
            self._refresh_confs()
            self._refresh_ov()
            self._save_data(snapshot_label="delete_conf")

    def _add_skill(self):
        name = entry_val(self.sk_name, "Skill name...")
        if not name:
            messagebox.showwarning("Input Required",
                                   "Please enter a skill name.")
            return
        self.skill_data.append([name, self.sk_cat.get(),
                                 int(self.sk_var.get())])
        self.sk_name.delete(0, tk.END)
        self.sk_name.insert(0, "Skill name...")
        self.sk_name.config(fg=MUTED)
        self.sk_var.set(0)
        self.sk_lbl.config(text="0%")
        self._refresh_skills()
        self._refresh_ov()
        self._save_data(snapshot_label="add_skill_" + name[:30])

    def _del_skill(self):
        sel = self.skill_tree.selection()
        if not sel:
            return
        if self._confirm_delete("skill"):
            del self.skill_data[self.skill_tree.index(sel[0])]
            self._refresh_skills()
            self._refresh_ov()
            self._save_data(snapshot_label="delete_skill")


# ---- Entry point ------------------------------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    AcademiX(root)
    root.mainloop()
