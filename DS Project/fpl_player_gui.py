import tkinter as tk
from ttkbootstrap import Style
import theme
from tkinter import ttk
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import os
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "fpl_data.csv")

POSITION_CONFIG = {
    "GKP": {
        "stats": ["minutes", "saves", "clean_sheets", "goals_conceded",
                  "expected_goals_conceded", "penalties_saved"],
        "stat_labels": {
            "minutes": "Minutes", "saves": "Saves", "clean_sheets": "Clean Sheets",
            "goals_conceded": "Goals Conceded", "expected_goals_conceded": "xGC",
            "penalties_saved": "Pen Saved",
        },
        "features": ["expected_goals_conceded", "minutes"],
        "targets": [("saves", "Saves"), ("clean_sheets", "Clean Sheets")],
    },
    "DEF": {
        "stats": ["minutes", "clean_sheets", "clearances_blocks_interceptions",
                  "goals_conceded", "defensive_contribution", "influence"],
        "stat_labels": {
            "minutes": "Minutes", "clean_sheets": "Clean Sheets",
            "clearances_blocks_interceptions": "CBI", "goals_conceded": "Goals Conc.",
            "defensive_contribution": "Def. Contribution", "influence": "Influence",
        },
        "features": ["defensive_contribution", "influence", "minutes"],
        "targets": [("clearances_blocks_interceptions", "CBI"), ("clean_sheets", "Clean Sheets")],
    },
    "MID": {
        "stats": ["minutes", "goals_scored", "assists", "expected_assists",
                  "creativity", "influence"],
        "stat_labels": {
            "minutes": "Minutes", "goals_scored": "Goals", "assists": "Assists",
            "expected_assists": "xA", "creativity": "Creativity", "influence": "Influence",
        },
        "features": ["expected_assists", "creativity", "influence"],
        "targets": [("assists", "Assists"), ("expected_goal_involvements", "xGI")],
    },
    "FWD": {
        "stats": ["minutes", "goals_scored", "assists", "expected_goals",
                  "expected_goal_involvements", "threat"],
        "stat_labels": {
            "minutes": "Minutes", "goals_scored": "Goals", "assists": "Assists",
            "expected_goals": "xG", "expected_goal_involvements": "xGI", "threat": "Threat",
        },
        "features": ["threat", "expected_goal_involvements", "expected_goals"],
        "targets": [("goals_scored", "Goals"), ("expected_goals", "xG")],
    },
}

POS_COLORS   = {"GKP": "#F59E0B", "DEF": "#3B82F6", "MID": "#10B981", "FWD": "#EF4444"}
POS_DIM      = {"GKP": "#78532A", "DEF": "#1E3A5F", "MID": "#0C4A35", "FWD": "#5C1A1A"}

BG        = theme.Theme.get("BG")
SURFACE   = theme.Theme.get("SURFACE")
CARD      = theme.Theme.get("CARD")
CARD2     = theme.Theme.get("CARD2")
BORDER    = theme.Theme.get("BORDER")
BORDER2   = theme.Theme.get("BORDER2")
TEXT_PRI  = theme.Theme.get("TEXT_PRI")
TEXT_SEC  = theme.Theme.get("TEXT_SEC")
TEXT_MUT  = theme.Theme.get("TEXT_MUT")
ACCENT    = theme.Theme.get("ACCENT")
ACCENT_DIM= theme.Theme.get("ACCENT_DIM")
SUCCESS   = theme.Theme.get("SUCCESS")
SUCCESS_DIM= theme.Theme.get("SUCCESS_DIM")

FONT      = "Segoe UI"
FONT_MONO = "Consolas"

def fetch_fpl_data():
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    raw = response.json()
    df = pd.DataFrame(raw["elements"])
    df.to_csv(CSV_PATH, index=False)
    return df


def load_from_csv():
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        return df.to_dict(orient="records")

    try:
        df = fetch_fpl_data()
        return df.to_dict(orient="records")
    except Exception as e:
        raise FileNotFoundError(
            f"'{CSV_PATH}' not found.\n\n"
            "Also failed to download FPL data automatically.\n"
            "Run your notebook first and add this line at the end:\n\n"
            "    data.to_csv('fpl_data.csv', index=False)\n\n"
            f"Original error: {e}"
        ) from e


def predict_player(player, all_players, games_left=8):
    pos = player.get("position_name")
    cfg = POSITION_CONFIG.get(pos)
    if not cfg:
        return []

    position_df  = [p for p in all_players if p.get("position_name") == pos]
    matches_played = max((player.get("minutes") or 0) / 90, 0.5)
    results = []

    for target_col, target_name in cfg["targets"]:
        valid = [
            p for p in position_df
            if all(isinstance(p.get(f), (int, float)) for f in cfg["features"])
            and isinstance(p.get(target_col), (int, float))
        ]
        if len(valid) < 5:
            continue

        X = np.array([[p[f] for f in cfg["features"]] for p in valid])
        y = np.array([p[target_col] for p in valid])

        x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(x_train, y_train)

        player_features  = np.array([[player.get(f, 0) for f in cfg["features"]]])
        predicted_pace   = model.predict(player_features)[0]
        rate   = predicted_pace / matches_played
        future = rate * games_left
        current = player.get(target_col) or 0
        final   = current + future

        results.append({
            "name": target_name,
            "current": current,
            "rate": rate,
            "future": future,
            "final": final,
            "games": games_left,
        })

    return results


def make_separator(parent, color=BORDER):
    tk.Frame(parent, bg=color, height=1).pack(fill="x")


def section_header(parent, text):
    row = tk.Frame(parent, bg=BG)
    row.pack(fill="x", pady=(18, 6))
    tk.Label(row, text=text.upper(), bg=BG, fg=TEXT_SEC,
             font=(FONT, 8, "bold"), anchor="w").pack(side="left")
    tk.Frame(row, bg=BORDER, height=1).pack(side="left", fill="x", expand=True, padx=(8, 0), pady=8)


class RoundedCard(tk.Canvas):
    """A Canvas widget that draws a rounded-rectangle card background."""
    def __init__(self, parent, radius=10, bg_color=CARD, border_color=BORDER, **kwargs):
        self._bg_color     = bg_color
        self._border_color = border_color
        self._radius       = radius
        super().__init__(parent, bg=BG, highlightthickness=0, **kwargs)
        self.bind("<Configure>", self._redraw)

    def _redraw(self, event=None):
        self.delete("bg")
        w, h = self.winfo_width(), self.winfo_height()
        r = self._radius
        self.create_polygon(
            r, 0, w - r, 0,
            w, 0, w, r,
            w, h - r, w, h,
            w - r, h, r, h,
            0, h, 0, h - r,
            0, r, 0, 0,
            smooth=True,
            fill=self._bg_color,
            outline=self._border_color,
            width=1,
            tags="bg",
        )
        self.tag_lower("bg")


class FPLApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FPL Scout")
        self.configure(bg=BG)
        self.geometry("860x760")
        self.minsize(720, 600)
        self.resizable(True, True)
        # Initialize ttkbootstrap style
        self.style = Style(theme="darkly")
        # Theme toggle button
        self.toggle_btn = tk.Button(self, text="Toggle Theme", bg=ACCENT_DIM, fg=ACCENT, command=self.toggle_theme)
        self.toggle_btn.place(relx=0.95, rely=0.02, anchor="ne")

        self.all_players     = []
        self.filtered        = []
        self.selected_player = None
        self.games_left      = tk.IntVar(value=8)

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        top = tk.Frame(self, bg=BG, pady=20)
        top.pack(fill="x", padx=28)
        # Ensure theme toggle button is on top bar
        self.toggle_btn.lift()

        left_top = tk.Frame(top, bg=BG)
        left_top.pack(side="left", fill="y")

        tk.Label(left_top, text="FPL Scout", bg=BG, fg=TEXT_PRI,
                 font=(FONT, 20, "bold")).pack(side="left")
        tk.Label(left_top, text="  Beta", bg=ACCENT_DIM, fg=ACCENT,
                 font=(FONT, 8, "bold"), padx=6, pady=2).pack(side="left", pady=6)

        self.status_lbl = tk.Label(top, text="Loading…", bg=BG, fg=TEXT_SEC,
                                   font=(FONT, 9))
        self.status_lbl.pack(side="right", pady=6)

        make_separator(self, BORDER)

        search_wrap = tk.Frame(self, bg=BG, padx=28, pady=14)
        search_wrap.pack(fill="x")

        search_box = tk.Frame(search_wrap, bg=CARD2,
                              highlightbackground=BORDER2, highlightthickness=1)
        search_box.pack(fill="x")

        tk.Label(search_box, text="⌕", bg=CARD2, fg=TEXT_SEC,
                 font=(FONT, 15)).pack(side="left", padx=(14, 6))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)
        self.search_entry = tk.Entry(
            search_box, textvariable=self.search_var,
            bg=CARD2, fg=TEXT_PRI, insertbackground=ACCENT,
            relief="flat", font=(FONT, 13),
            highlightthickness=0, bd=0)
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=11, padx=(0, 14))
        self.search_entry.bind("<Return>",  self._on_enter)
        self.search_entry.bind("<Down>",    self._focus_list)

        sug_wrap = tk.Frame(self, bg=BG, padx=28)
        sug_wrap.pack(fill="x")
        self.sug_frame = tk.Frame(sug_wrap, bg=CARD2,
                                   highlightbackground=BORDER2, highlightthickness=1)
        self.sug_list = tk.Listbox(
            self.sug_frame, bg=CARD2, fg=TEXT_PRI,
            selectbackground=ACCENT_DIM, selectforeground=TEXT_PRI,
            relief="flat", bd=0, highlightthickness=0,
            font=(FONT, 11), height=5, activestyle="none")
        self.sug_list.pack(fill="x", padx=4, pady=4)
        self.sug_list.bind("<<ListboxSelect>>", self._on_sug_select)
        self.sug_list.bind("<Return>",          self._on_sug_select)

        ctrl = tk.Frame(self, bg=SURFACE, pady=10)
        ctrl.pack(fill="x", padx=28, pady=(6, 0))

        tk.Label(ctrl, text="Gameweeks remaining", bg=SURFACE, fg=TEXT_SEC,
                 font=(FONT, 10)).pack(side="left")

        self.games_lbl = tk.Label(ctrl, text="8", bg=ACCENT_DIM, fg=ACCENT,
                                   font=(FONT, 11, "bold"), padx=8, pady=2, width=2)
        self.games_lbl.pack(side="left", padx=10)

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Flat.Horizontal.TScale",
                        background=SURFACE,
                        troughcolor=BORDER,
                        sliderlength=20,
                        sliderthickness=14,
                        sliderrelief="flat",
                        troughrelief="flat")
        style.map("Flat.Horizontal.TScale",
                  background=[("active", SURFACE)],
                  troughcolor=[("active", BORDER2)])

        ttk.Scale(ctrl, from_=1, to=8, orient="horizontal",
                  variable=self.games_left, command=self._on_slider,
                  style="Flat.Horizontal.TScale").pack(
            side="left", fill="x", expand=True, padx=(0, 4))

        for gw in range(1, 9):
            tk.Label(ctrl, text=str(gw), bg=SURFACE, fg=TEXT_MUT,
                     font=(FONT, 8)).pack(side="left")
            if gw < 8:
                tk.Label(ctrl, text=" ", bg=SURFACE).pack(side="left", padx=2)

        make_separator(self, BORDER)

        self.canvas    = tk.Canvas(self, bg=BG, highlightthickness=0)
        scrollbar      = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y", pady=4, padx=(0, 4))
        self.canvas.pack(fill="both", expand=True, padx=28, pady=12)

        self.output_frame  = tk.Frame(self.canvas, bg=BG)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.output_frame, anchor="nw")

        self.output_frame.bind("<Configure>",   self._on_frame_configure)
        self.canvas.bind("<Configure>",          self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>",     self._on_mousewheel)

        self._show_placeholder("Search for a player to see their stats and forecast")

    def _load_data(self):
        try:
            self.all_players = load_from_csv()
            count = len(self.all_players)
            self.status_lbl.config(text=f"{count} players loaded")
            self._show_placeholder("Search for a player to see their stats and forecast")
            self.search_entry.focus_set()
        except FileNotFoundError as e:
            self._show_placeholder(str(e))
            self.status_lbl.config(text="CSV not found")

    def _on_search_change(self, *_):
        q = self.search_var.get().strip().lower()
        if not q or not self.all_players:
            self.sug_frame.pack_forget()
            return
        self.filtered = [p for p in self.all_players
                         if q in str(p.get("player_name", "")).lower()]
        if not self.filtered:
            self.sug_frame.pack_forget()
            return
        self.sug_list.delete(0, "end")
        for p in self.filtered[:8]:
            pos   = p.get("position_name", "")
            badge = f"[{pos}]"
            club  = p.get("club_name", "")
            self.sug_list.insert("end", f"  {p['player_name']}   {badge}  ·  {club}")
        self.sug_frame.pack(fill="x")

    def _on_enter(self, _=None):
        if self.filtered:
            self._load_player(self.filtered[0])
            self.sug_frame.pack_forget()

    def _focus_list(self, _=None):
        self.sug_list.focus_set()
        self.sug_list.selection_set(0)

    def _on_sug_select(self, _=None):
        sel = self.sug_list.curselection()
        if sel and self.filtered:
            idx = sel[0]
            if idx < len(self.filtered):
                self._load_player(self.filtered[idx])
                self.sug_frame.pack_forget()
                self.search_var.set(self.filtered[idx]["player_name"])

    def _load_player(self, player):
        self.selected_player = player
        self._render_player(player)

    def _on_slider(self, _=None):
        v = int(round(self.games_left.get()))
        self.games_left.set(v)
        self.games_lbl.config(text=str(v))
        if self.selected_player:
            self._render_player(self.selected_player)

    def _render_player(self, player):
        for w in self.output_frame.winfo_children():
            w.destroy()

        pos          = player.get("position_name", "")
        pos_color    = POS_COLORS.get(pos, ACCENT)
        pos_dim      = POS_DIM.get(pos, ACCENT_DIM)
        cfg          = POSITION_CONFIG.get(pos, {})
        minutes      = player.get("minutes") or 0
        matches      = max(minutes / 90, 0.1)

        hdr_outer = tk.Frame(self.output_frame, bg=CARD,
                             highlightbackground=BORDER, highlightthickness=1)
        hdr_outer.pack(fill="x", pady=(4, 0))

        tk.Frame(hdr_outer, bg=pos_color, width=4).pack(side="left", fill="y")

        hdr_inner = tk.Frame(hdr_outer, bg=CARD, padx=18, pady=16)
        hdr_inner.pack(side="left", fill="both", expand=True)

        av = tk.Canvas(hdr_inner, width=52, height=52, bg=CARD,
                       highlightthickness=0)
        av.pack(side="left", padx=(0, 16))
        av.create_oval(2, 2, 50, 50, fill=pos_dim, outline=pos_color, width=2)
        initials = "".join(w[0] for w in str(player.get("player_name", "??")).split()[:2]).upper()
        av.create_text(26, 27, text=initials, fill=pos_color,
                       font=(FONT, 13, "bold"))

        info = tk.Frame(hdr_inner, bg=CARD)
        info.pack(side="left", fill="both", expand=True)

        name_row = tk.Frame(info, bg=CARD)
        name_row.pack(fill="x", anchor="w")

        tk.Label(name_row, text=player.get("player_name", ""),
                 bg=CARD, fg=TEXT_PRI,
                 font=(FONT, 16, "bold"), anchor="w").pack(side="left")

        tk.Label(name_row, text=f" {pos} ", bg=pos_dim, fg=pos_color,
                 font=(FONT, 8, "bold"), padx=6, pady=2).pack(side="left", padx=(8, 0), pady=6)

        sub = f"{player.get('club_name', '')}   ·   {matches:.0f} appearances"
        tk.Label(info, text=sub, bg=CARD, fg=TEXT_SEC,
                 font=(FONT, 10), anchor="w").pack(fill="x")

        meta_row = tk.Frame(hdr_inner, bg=CARD)
        meta_row.pack(side="right", anchor="ne")

        for key, label in [("total_points", "pts"), ("now_cost", "£"), ("selected_by_percent", "sel%")]:
            val = player.get(key)
            if val is not None:
                col = tk.Frame(meta_row, bg=CARD, padx=10)
                col.pack(side="left")
                if key == "now_cost":
                    val = val / 10
                    txt = f"£{val:.1f}m"
                elif key == "selected_by_percent":
                    txt = f"{val}%"
                else:
                    txt = str(int(val))
                tk.Label(col, text=txt, bg=CARD, fg=TEXT_PRI,
                         font=(FONT_MONO, 15, "bold")).pack()
                tk.Label(col, text=label, bg=CARD, fg=TEXT_SEC,
                         font=(FONT, 8)).pack()

        section_header(self.output_frame, "Current Season Stats")

        stat_keys   = cfg.get("stats", [])
        stat_labels = cfg.get("stat_labels", {})

        stats_wrap = tk.Frame(self.output_frame, bg=BG)
        stats_wrap.pack(fill="x")

        cols = 3
        for col_i in range(cols):
            stats_wrap.columnconfigure(col_i, weight=1)

        for i, key in enumerate(stat_keys):
            val   = player.get(key) or 0
            label = stat_labels.get(key, key)
            r, c  = divmod(i, cols)

            cell = tk.Frame(stats_wrap, bg=CARD,
                            highlightbackground=BORDER, highlightthickness=1,
                            padx=16, pady=12)
            cell.grid(row=r, column=c, padx=(0 if c > 0 else 0, 6 if c < cols - 1 else 0),
                      pady=(0, 6), sticky="nsew", ipadx=2)

            tk.Label(cell, text=label, bg=CARD, fg=TEXT_SEC,
                     font=(FONT, 9), anchor="w").pack(fill="x")

            formatted = (f"{val:.0f}" if isinstance(val, float) and val == int(val)
                         else f"{val:.2f}")
            tk.Label(cell, text=formatted, bg=CARD, fg=TEXT_PRI,
                     font=(FONT_MONO, 22, "bold"), anchor="w").pack(fill="x")

            if key != "minutes" and matches > 0:
                per_game = val / matches
                tk.Label(cell, text=f"{per_game:.2f} / game", bg=CARD, fg=TEXT_MUT,
                         font=(FONT, 8), anchor="w").pack(fill="x")

        games   = int(round(self.games_left.get()))
        section_header(self.output_frame, f"End-of-Season Forecast  ·  +{games} gameweeks")

        forecasts = predict_player(player, self.all_players, games_left=games)

        if not forecasts:
            tk.Label(self.output_frame, text="Not enough data to generate a forecast.",
                     bg=BG, fg=TEXT_SEC, font=(FONT, 11)).pack(anchor="w", pady=8)
        else:
            fc_grid = tk.Frame(self.output_frame, bg=BG)
            fc_grid.pack(fill="x")
            fc_grid.columnconfigure(0, weight=1)
            fc_grid.columnconfigure(1, weight=1)

            for i, fc in enumerate(forecasts):
                col_pad = (0, 8) if i == 0 else (8, 0)

                card = tk.Frame(fc_grid, bg=CARD,
                                highlightbackground=BORDER, highlightthickness=1,
                                padx=20, pady=16)
                card.grid(row=0, column=i, padx=col_pad, sticky="nsew")

                tk.Label(card, text=fc["name"].upper(), bg=CARD, fg=TEXT_SEC,
                         font=(FONT, 8, "bold")).pack(anchor="w")

                num_row = tk.Frame(card, bg=CARD)
                num_row.pack(anchor="w", pady=(8, 0))

                tk.Label(num_row, text=f"{fc['current']:.0f}",
                         bg=CARD, fg=TEXT_PRI,
                         font=(FONT_MONO, 28, "bold")).pack(side="left")

                arrow_col = tk.Frame(num_row, bg=CARD)
                arrow_col.pack(side="left", padx=12)
                tk.Label(arrow_col, text=f"+{fc['future']:.1f}", bg=CARD, fg=SUCCESS,
                         font=(FONT, 11, "bold")).pack(anchor="w")
                tk.Label(arrow_col, text="projected", bg=CARD, fg=TEXT_MUT,
                         font=(FONT, 8)).pack(anchor="w")

                tk.Label(num_row, text="→", bg=CARD, fg=TEXT_SEC,
                         font=(FONT, 16)).pack(side="left", padx=4)

                tk.Label(num_row, text=f"{fc['final']:.0f}",
                         bg=CARD, fg=SUCCESS,
                         font=(FONT_MONO, 36, "bold")).pack(side="left")

                max_val = max(fc["final"], 1)
                bar_w   = 260
                bar_h   = 6

                progress_bg = tk.Canvas(card, width=bar_w, height=bar_h,
                                        bg=CARD, highlightthickness=0)
                progress_bg.pack(anchor="w", pady=(10, 2))

                progress_bg.create_rectangle(0, 0, bar_w, bar_h,
                                              fill=BORDER, outline="")
                cur_w = int(bar_w * (fc["current"] / max_val))
                if cur_w > 0:
                    progress_bg.create_rectangle(0, 0, cur_w, bar_h,
                                                  fill=TEXT_SEC, outline="")
                proj_w = int(bar_w * (fc["final"] / max_val))
                if proj_w > 0:
                    progress_bg.create_rectangle(0, 0, proj_w, bar_h,
                                                  fill=SUCCESS, outline="")

                tk.Label(card, text=f"{fc['rate']:.2f} per game  ·  over next {fc['games']} GW",
                         bg=CARD, fg=TEXT_MUT, font=(FONT, 9)).pack(anchor="w")

        self.output_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _show_placeholder(self, msg):
        for w in self.output_frame.winfo_children():
            w.destroy()

        wrap = tk.Frame(self.output_frame, bg=BG)
        wrap.pack(expand=True, fill="both", pady=80)

        tk.Label(wrap, text="◎", bg=BG, fg=BORDER2,
                 font=(FONT, 36)).pack()
        tk.Label(wrap, text=msg, bg=BG, fg=TEXT_SEC,
                 font=(FONT, 12), pady=10, wraplength=500,
                 justify="center").pack()

    def _on_frame_configure(self, _):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        # Update canvas width for responsive layout
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


    def toggle_theme(self):
        theme.Theme.toggle()
        # Update color globals
        global BG, SURFACE, CARD, CARD2, BORDER, BORDER2, TEXT_PRI, TEXT_SEC, TEXT_MUT, ACCENT, ACCENT_DIM, SUCCESS, SUCCESS_DIM
        BG = theme.Theme.get("BG")
        SURFACE = theme.Theme.get("SURFACE")
        CARD = theme.Theme.get("CARD")
        CARD2 = theme.Theme.get("CARD2")
        BORDER = theme.Theme.get("BORDER")
        BORDER2 = theme.Theme.get("BORDER2")
        TEXT_PRI = theme.Theme.get("TEXT_PRI")
        TEXT_SEC = theme.Theme.get("TEXT_SEC")
        TEXT_MUT = theme.Theme.get("TEXT_MUT")
        ACCENT = theme.Theme.get("ACCENT")
        ACCENT_DIM = theme.Theme.get("ACCENT_DIM")
        SUCCESS = theme.Theme.get("SUCCESS")
        SUCCESS_DIM = theme.Theme.get("SUCCESS_DIM")
        # Refresh UI colors
        self.configure(bg=BG)
        self._build_ui()
        self._load_data()

if __name__ == "__main__":
    app = FPLApp()
    app.mainloop()