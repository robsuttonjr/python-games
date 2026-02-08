"""
Claude Usage Stats Dashboard
A tkinter application to track and visualize Claude AI usage statistics.
Tracks current session metrics, daily breakdowns, and weekly totals.
Data persists between sessions via a local JSON file.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Data persistence
# ---------------------------------------------------------------------------

DATA_FILE = Path(__file__).with_name("claude_usage_data.json")

DEFAULT_DATA = {
    "sessions": [],
    "daily": {},
}


def load_data():
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return dict(DEFAULT_DATA)
    return dict(DEFAULT_DATA)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------

BG = "#1a1a2e"
BG_CARD = "#16213e"
BG_CARD_ALT = "#0f3460"
FG = "#e0e0e0"
FG_DIM = "#8899aa"
ACCENT = "#e94560"
ACCENT2 = "#0f9b8e"
ACCENT3 = "#f5a623"
BAR_COLORS = ["#e94560", "#0f9b8e", "#f5a623", "#5dade2", "#a569bd", "#48c9b0", "#f0b27a"]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def fmt_duration(seconds):
    """Format seconds into a human-readable string."""
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    minutes, secs = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m {secs}s"


def week_dates(ref_date=None):
    """Return list of date strings (Mon-Sun) for the week containing ref_date."""
    if ref_date is None:
        ref_date = datetime.now()
    monday = ref_date - timedelta(days=ref_date.weekday())
    return [(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]


def day_label(date_str):
    """Return short weekday name from a YYYY-MM-DD string."""
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%a")


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------

class UsageStatsDashboard(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Claude Usage Stats Dashboard")
        self.configure(bg=BG)
        self.minsize(900, 680)
        self.geometry("960x720")

        # State
        self.data = load_data()
        self.session_active = False
        self.session_start = None
        self.session_messages = 0
        self.session_tokens = 0
        self.elapsed = 0

        # Styles
        self._setup_styles()

        # Layout
        self._build_ui()

        # Populate
        self._refresh_weekly()
        self._refresh_history()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---- styles ----------------------------------------------------------

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("Card.TFrame", background=BG_CARD)
        style.configure("CardAlt.TFrame", background=BG_CARD_ALT)
        style.configure("TLabel", background=BG_CARD, foreground=FG, font=("Segoe UI", 11))
        style.configure("Title.TLabel", background=BG, foreground=FG, font=("Segoe UI", 18, "bold"))
        style.configure("Subtitle.TLabel", background=BG, foreground=FG_DIM, font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background=BG_CARD, foreground=ACCENT, font=("Segoe UI", 13, "bold"))
        style.configure("BigNum.TLabel", background=BG_CARD, foreground=FG, font=("Consolas", 28, "bold"))
        style.configure("MedNum.TLabel", background=BG_CARD, foreground=FG, font=("Consolas", 18, "bold"))
        style.configure("SmallDim.TLabel", background=BG_CARD, foreground=FG_DIM, font=("Segoe UI", 9))
        style.configure("Accent.TButton", font=("Segoe UI", 11, "bold"))
        style.configure("WeekCard.TFrame", background=BG_CARD_ALT)
        style.configure("WeekLabel.TLabel", background=BG_CARD_ALT, foreground=FG_DIM, font=("Segoe UI", 9))
        style.configure("WeekNum.TLabel", background=BG_CARD_ALT, foreground=FG, font=("Consolas", 13, "bold"))
        style.configure("HistCard.TFrame", background=BG_CARD)
        style.configure("HistTitle.TLabel", background=BG_CARD, foreground=ACCENT, font=("Segoe UI", 12, "bold"))

    # ---- UI construction -------------------------------------------------

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=20, pady=(16, 4))
        ttk.Label(header, text="Claude Usage Stats", style="Title.TLabel").pack(side="left")
        ttk.Label(header, text="Track your conversations, tokens & time", style="Subtitle.TLabel").pack(side="left", padx=(12, 0), pady=(6, 0))

        # Main scrollable area
        container = tk.Frame(self, bg=BG)
        container.pack(fill="both", expand=True, padx=16, pady=8)

        # Row 1: Session controls + current session card
        row1 = tk.Frame(container, bg=BG)
        row1.pack(fill="x", pady=(0, 10))

        self._build_session_card(row1)
        self._build_log_card(row1)

        # Row 2: Weekly overview
        row2 = tk.Frame(container, bg=BG)
        row2.pack(fill="x", pady=(0, 10))
        self._build_weekly_cards(row2)

        # Row 3: Chart + History
        row3 = tk.Frame(container, bg=BG)
        row3.pack(fill="both", expand=True, pady=(0, 10))
        self._build_chart(row3)
        self._build_history(row3)

    # ---- Session Card ----------------------------------------------------

    def _build_session_card(self, parent):
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.pack(side="left", fill="both", expand=True, padx=(0, 6))

        inner = tk.Frame(frame, bg=BG_CARD)
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        ttk.Label(inner, text="Current Session", style="CardTitle.TLabel").pack(anchor="w")

        # Timer
        self.timer_var = tk.StringVar(value="00:00:00")
        ttk.Label(inner, textvariable=self.timer_var, style="BigNum.TLabel").pack(anchor="w", pady=(6, 2))

        stats_row = tk.Frame(inner, bg=BG_CARD)
        stats_row.pack(fill="x", pady=(4, 8))

        self.sess_msg_var = tk.StringVar(value="0")
        self.sess_tok_var = tk.StringVar(value="0")

        for label_text, var in [("Messages", self.sess_msg_var), ("Tokens", self.sess_tok_var)]:
            col = tk.Frame(stats_row, bg=BG_CARD)
            col.pack(side="left", padx=(0, 24))
            ttk.Label(col, textvariable=var, style="MedNum.TLabel").pack(anchor="w")
            ttk.Label(col, text=label_text, style="SmallDim.TLabel").pack(anchor="w")

        # Buttons
        btn_row = tk.Frame(inner, bg=BG_CARD)
        btn_row.pack(fill="x")

        self.start_btn = tk.Button(
            btn_row, text="Start Session", font=("Segoe UI", 11, "bold"),
            bg=ACCENT2, fg="white", activebackground="#0bb5a5", activeforeground="white",
            bd=0, padx=18, pady=6, cursor="hand2", command=self._toggle_session
        )
        self.start_btn.pack(side="left", padx=(0, 8))

        self.reset_btn = tk.Button(
            btn_row, text="Reset", font=("Segoe UI", 11),
            bg="#333", fg=FG_DIM, activebackground="#444", activeforeground=FG,
            bd=0, padx=14, pady=6, cursor="hand2", command=self._reset_session
        )
        self.reset_btn.pack(side="left")

    # ---- Log Card --------------------------------------------------------

    def _build_log_card(self, parent):
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.pack(side="left", fill="both", expand=True, padx=(6, 0))

        inner = tk.Frame(frame, bg=BG_CARD)
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        ttk.Label(inner, text="Log Interaction", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(inner, text="Record a conversation exchange", style="SmallDim.TLabel").pack(anchor="w", pady=(2, 10))

        # Token entry
        tok_frame = tk.Frame(inner, bg=BG_CARD)
        tok_frame.pack(fill="x", pady=(0, 6))
        ttk.Label(tok_frame, text="Tokens used:").pack(side="left")
        self.token_entry = tk.Entry(
            tok_frame, width=12, font=("Consolas", 12),
            bg="#0d1b2a", fg=FG, insertbackground=FG, bd=0, relief="flat"
        )
        self.token_entry.insert(0, "1000")
        self.token_entry.pack(side="left", padx=(8, 0), ipady=4)

        # Messages entry
        msg_frame = tk.Frame(inner, bg=BG_CARD)
        msg_frame.pack(fill="x", pady=(0, 12))
        ttk.Label(msg_frame, text="Messages:    ").pack(side="left")
        self.msg_entry = tk.Entry(
            msg_frame, width=12, font=("Consolas", 12),
            bg="#0d1b2a", fg=FG, insertbackground=FG, bd=0, relief="flat"
        )
        self.msg_entry.insert(0, "2")
        self.msg_entry.pack(side="left", padx=(8, 0), ipady=4)

        log_btn = tk.Button(
            inner, text="Log Interaction", font=("Segoe UI", 11, "bold"),
            bg=ACCENT, fg="white", activebackground="#ff5a75", activeforeground="white",
            bd=0, padx=18, pady=6, cursor="hand2", command=self._log_interaction
        )
        log_btn.pack(anchor="w")

        # Quick-add row
        quick = tk.Frame(inner, bg=BG_CARD)
        quick.pack(fill="x", pady=(10, 0))
        ttk.Label(quick, text="Quick add:", style="SmallDim.TLabel").pack(side="left")
        for label, msgs, toks in [("Short chat", 2, 500), ("Medium", 6, 2000), ("Long session", 20, 8000)]:
            b = tk.Button(
                quick, text=label, font=("Segoe UI", 9),
                bg=BG_CARD_ALT, fg=FG_DIM, activebackground="#1a3a5c", activeforeground=FG,
                bd=0, padx=8, pady=2, cursor="hand2",
                command=lambda m=msgs, t=toks: self._quick_log(m, t)
            )
            b.pack(side="left", padx=(6, 0))

    # ---- Weekly Cards ----------------------------------------------------

    def _build_weekly_cards(self, parent):
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.pack(fill="x")

        header = tk.Frame(frame, bg=BG_CARD)
        header.pack(fill="x", padx=16, pady=(12, 0))
        ttk.Label(header, text="This Week", style="CardTitle.TLabel").pack(side="left")

        self.week_total_var = tk.StringVar(value="0 messages  |  0 tokens  |  0s")
        ttk.Label(header, textvariable=self.week_total_var, style="SmallDim.TLabel").pack(side="right")

        # Navigation row
        nav_row = tk.Frame(frame, bg=BG_CARD)
        nav_row.pack(fill="x", padx=16, pady=(4, 0))

        self.week_offset = 0
        self.week_nav_var = tk.StringVar()

        nav_prev = tk.Button(
            nav_row, text="< Prev", font=("Segoe UI", 9),
            bg=BG_CARD_ALT, fg=FG_DIM, activebackground="#1a3a5c", activeforeground=FG,
            bd=0, padx=8, pady=2, cursor="hand2", command=self._prev_week
        )
        nav_prev.pack(side="left")
        ttk.Label(nav_row, textvariable=self.week_nav_var, style="SmallDim.TLabel").pack(side="left", padx=10)
        nav_next = tk.Button(
            nav_row, text="Next >", font=("Segoe UI", 9),
            bg=BG_CARD_ALT, fg=FG_DIM, activebackground="#1a3a5c", activeforeground=FG,
            bd=0, padx=8, pady=2, cursor="hand2", command=self._next_week
        )
        nav_next.pack(side="left")

        self.week_row = tk.Frame(frame, bg=BG_CARD)
        self.week_row.pack(fill="x", padx=12, pady=(6, 12))

        self.day_frames = {}

    def _refresh_weekly(self):
        for w in self.week_row.winfo_children():
            w.destroy()
        self.day_frames.clear()

        ref = datetime.now() + timedelta(weeks=self.week_offset)
        dates = week_dates(ref)

        monday = datetime.strptime(dates[0], "%Y-%m-%d")
        sunday = datetime.strptime(dates[6], "%Y-%m-%d")
        self.week_nav_var.set(f"{monday.strftime('%b %d')} - {sunday.strftime('%b %d, %Y')}")

        total_msgs = 0
        total_toks = 0
        total_dur = 0

        today_str = datetime.now().strftime("%Y-%m-%d")

        for i, date_str in enumerate(dates):
            card = tk.Frame(self.week_row, bg=BG_CARD_ALT, highlightthickness=1,
                            highlightbackground="#223355" if date_str != today_str else ACCENT)
            card.pack(side="left", fill="both", expand=True, padx=3, pady=2)

            dl = day_label(date_str)
            ttk.Label(card, text=dl, style="WeekLabel.TLabel").pack(pady=(6, 0))

            day_data = self.data.get("daily", {}).get(date_str, {})
            msgs = day_data.get("messages", 0)
            toks = day_data.get("tokens", 0)
            dur = day_data.get("duration", 0)

            total_msgs += msgs
            total_toks += toks
            total_dur += dur

            msg_var = tk.StringVar(value=str(msgs))
            ttk.Label(card, textvariable=msg_var, style="WeekNum.TLabel").pack()
            ttk.Label(card, text="msgs", style="WeekLabel.TLabel").pack()
            ttk.Label(card, text=f"{toks:,} tok", style="WeekLabel.TLabel").pack()
            ttk.Label(card, text=fmt_duration(dur), style="WeekLabel.TLabel").pack(pady=(0, 6))

            self.day_frames[date_str] = card

        self.week_total_var.set(
            f"{total_msgs} messages  |  {total_toks:,} tokens  |  {fmt_duration(total_dur)}"
        )

    # ---- Bar Chart -------------------------------------------------------

    def _build_chart(self, parent):
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.pack(side="left", fill="both", expand=True, padx=(0, 6))

        inner = tk.Frame(frame, bg=BG_CARD)
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        ttk.Label(inner, text="Weekly Token Usage", style="CardTitle.TLabel").pack(anchor="w")

        self.chart_canvas = tk.Canvas(inner, bg=BG_CARD, highlightthickness=0)
        self.chart_canvas.pack(fill="both", expand=True, pady=(8, 0))
        self.chart_canvas.bind("<Configure>", lambda e: self._draw_chart())

    def _draw_chart(self):
        c = self.chart_canvas
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 50 or h < 50:
            return

        ref = datetime.now() + timedelta(weeks=self.week_offset)
        dates = week_dates(ref)
        values = []
        for d in dates:
            day_data = self.data.get("daily", {}).get(d, {})
            values.append(day_data.get("tokens", 0))

        max_val = max(values) if max(values) > 0 else 1
        pad_left = 60
        pad_right = 20
        pad_top = 20
        pad_bottom = 40
        chart_w = w - pad_left - pad_right
        chart_h = h - pad_top - pad_bottom
        bar_gap = 8
        bar_w = (chart_w - bar_gap * (len(values) + 1)) / len(values)

        # Grid lines
        for i in range(5):
            y = pad_top + chart_h - (chart_h * i / 4)
            c.create_line(pad_left, y, w - pad_right, y, fill="#223355", dash=(2, 4))
            val = int(max_val * i / 4)
            c.create_text(pad_left - 8, y, text=f"{val:,}", anchor="e", fill=FG_DIM, font=("Consolas", 8))

        # Bars
        for i, (val, date_str) in enumerate(zip(values, dates)):
            x0 = pad_left + bar_gap + i * (bar_w + bar_gap)
            x1 = x0 + bar_w
            bar_h = (val / max_val) * chart_h if max_val > 0 else 0
            y0 = pad_top + chart_h - bar_h
            y1 = pad_top + chart_h

            color = BAR_COLORS[i % len(BAR_COLORS)]
            if bar_h > 0:
                c.create_rectangle(x0, y0, x1, y1, fill=color, outline="", width=0)
                # Value on top
                c.create_text((x0 + x1) / 2, y0 - 6, text=f"{val:,}", fill=color, font=("Consolas", 8))

            # Day label
            dl = day_label(date_str)
            c.create_text((x0 + x1) / 2, y1 + 14, text=dl, fill=FG_DIM, font=("Segoe UI", 9))

    # ---- History ---------------------------------------------------------

    def _build_history(self, parent):
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.pack(side="left", fill="both", expand=True, padx=(6, 0))

        inner = tk.Frame(frame, bg=BG_CARD)
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        top_row = tk.Frame(inner, bg=BG_CARD)
        top_row.pack(fill="x")
        ttk.Label(top_row, text="Recent Sessions", style="CardTitle.TLabel").pack(side="left")

        clear_btn = tk.Button(
            top_row, text="Clear All", font=("Segoe UI", 9),
            bg="#333", fg=FG_DIM, activebackground="#444", activeforeground=FG,
            bd=0, padx=8, pady=2, cursor="hand2", command=self._clear_history
        )
        clear_btn.pack(side="right")

        self.history_frame = tk.Frame(inner, bg=BG_CARD)
        self.history_frame.pack(fill="both", expand=True, pady=(8, 0))

        # Scrollable
        self.hist_canvas = tk.Canvas(self.history_frame, bg=BG_CARD, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.history_frame, orient="vertical", command=self.hist_canvas.yview)
        self.hist_inner = tk.Frame(self.hist_canvas, bg=BG_CARD)

        self.hist_inner.bind("<Configure>", lambda e: self.hist_canvas.configure(scrollregion=self.hist_canvas.bbox("all")))
        self.hist_canvas.create_window((0, 0), window=self.hist_inner, anchor="nw")
        self.hist_canvas.configure(yscrollcommand=scrollbar.set)

        self.hist_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _refresh_history(self):
        for w in self.hist_inner.winfo_children():
            w.destroy()

        sessions = self.data.get("sessions", [])
        if not sessions:
            ttk.Label(self.hist_inner, text="No sessions recorded yet.", style="SmallDim.TLabel").pack(pady=20)
            return

        for sess in reversed(sessions[-50:]):
            row = tk.Frame(self.hist_inner, bg="#0d1b2a", highlightthickness=0)
            row.pack(fill="x", pady=2)

            dt = sess.get("date", "")
            msgs = sess.get("messages", 0)
            toks = sess.get("tokens", 0)
            dur = sess.get("duration", 0)

            left = tk.Frame(row, bg="#0d1b2a")
            left.pack(side="left", fill="x", expand=True, padx=8, pady=4)

            ttk.Label(left, text=dt, background="#0d1b2a", foreground=FG, font=("Segoe UI", 9, "bold")).pack(anchor="w")
            ttk.Label(left, text=f"{msgs} msgs  |  {toks:,} tokens  |  {fmt_duration(dur)}",
                       background="#0d1b2a", foreground=FG_DIM, font=("Segoe UI", 8)).pack(anchor="w")

    # ---- Actions ---------------------------------------------------------

    def _toggle_session(self):
        if not self.session_active:
            self.session_active = True
            self.session_start = time.time()
            self.start_btn.config(text="End Session", bg=ACCENT)
            self._tick()
        else:
            self._end_session()

    def _end_session(self):
        self.session_active = False
        self.elapsed = time.time() - self.session_start if self.session_start else 0
        self.start_btn.config(text="Start Session", bg=ACCENT2)

        # Save session
        today = datetime.now().strftime("%Y-%m-%d")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        session_record = {
            "date": now_str,
            "messages": self.session_messages,
            "tokens": self.session_tokens,
            "duration": int(self.elapsed),
        }
        self.data.setdefault("sessions", []).append(session_record)

        # Update daily
        daily = self.data.setdefault("daily", {})
        day = daily.setdefault(today, {"messages": 0, "tokens": 0, "duration": 0})
        day["messages"] += self.session_messages
        day["tokens"] += self.session_tokens
        day["duration"] += int(self.elapsed)

        save_data(self.data)
        self._refresh_weekly()
        self._refresh_history()
        self._draw_chart()

    def _reset_session(self):
        if self.session_active:
            self.session_active = False
            self.start_btn.config(text="Start Session", bg=ACCENT2)
        self.session_start = None
        self.session_messages = 0
        self.session_tokens = 0
        self.elapsed = 0
        self.timer_var.set("00:00:00")
        self.sess_msg_var.set("0")
        self.sess_tok_var.set("0")

    def _tick(self):
        if self.session_active and self.session_start:
            elapsed = time.time() - self.session_start
            h, rem = divmod(int(elapsed), 3600)
            m, s = divmod(rem, 60)
            self.timer_var.set(f"{h:02d}:{m:02d}:{s:02d}")
            self.after(1000, self._tick)

    def _log_interaction(self):
        try:
            tokens = int(self.token_entry.get())
            messages = int(self.msg_entry.get())
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter valid numbers for tokens and messages.")
            return

        if tokens < 0 or messages < 0:
            messagebox.showwarning("Invalid Input", "Values must be non-negative.")
            return

        self.session_messages += messages
        self.session_tokens += tokens
        self.sess_msg_var.set(str(self.session_messages))
        self.sess_tok_var.set(f"{self.session_tokens:,}")

        # Also log to daily immediately
        today = datetime.now().strftime("%Y-%m-%d")
        daily = self.data.setdefault("daily", {})
        day = daily.setdefault(today, {"messages": 0, "tokens": 0, "duration": 0})
        day["messages"] += messages
        day["tokens"] += tokens
        save_data(self.data)

        self._refresh_weekly()
        self._draw_chart()

    def _quick_log(self, messages, tokens):
        self.session_messages += messages
        self.session_tokens += tokens
        self.sess_msg_var.set(str(self.session_messages))
        self.sess_tok_var.set(f"{self.session_tokens:,}")

        today = datetime.now().strftime("%Y-%m-%d")
        daily = self.data.setdefault("daily", {})
        day = daily.setdefault(today, {"messages": 0, "tokens": 0, "duration": 0})
        day["messages"] += messages
        day["tokens"] += tokens
        save_data(self.data)

        self._refresh_weekly()
        self._draw_chart()

    def _prev_week(self):
        self.week_offset -= 1
        self._refresh_weekly()
        self._draw_chart()

    def _next_week(self):
        if self.week_offset < 0:
            self.week_offset += 1
            self._refresh_weekly()
            self._draw_chart()

    def _clear_history(self):
        if messagebox.askyesno("Confirm", "Clear all session history and usage data?"):
            self.data = dict(DEFAULT_DATA)
            self.data["sessions"] = []
            self.data["daily"] = {}
            save_data(self.data)
            self._reset_session()
            self._refresh_weekly()
            self._refresh_history()
            self._draw_chart()

    def _on_close(self):
        if self.session_active:
            if messagebox.askyesno("Active Session", "You have an active session. Save and exit?"):
                self._end_session()
        self.destroy()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = UsageStatsDashboard()
    app.mainloop()
