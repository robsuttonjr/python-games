#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The Underground Adventure — Tkinter GUI Edition
Single-file, no external dependencies.

Features:
- Scrollable text console with rich formatting
- Status bar: Location • Score • Inventory
- Input line with command history (↑/↓)
- Menus: Save/Load, Light/Dark theme, Clear
- Typewriter effect toggle (View → Typewriter)
- Same world, parser, and win condition as the terminal version

Run:
  python adventure_gui.py
"""

import json, os, re, sys, time
from textwrap import wrap as _wrap
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_TITLE = "The Underground Adventure"
SAVE_DEFAULT = "adventure_save.json"
ROOM_COLORS = {
    "clearing": "#2e8b57",
    "forest": "#1f5f3a",
    "front_porch": "#8b6f47",
    "living_room": "#5e6472",
    "kitchen": "#6d4c41",
    "basement": "#2f2f46",
    "collapsed_tunnel": "#3f3f46",
    "underground_lake": "#0f4c5c",
    "crystal_grotto": "#355070",
    "catacombs": "#2d1e2f",
    "ruins_courtyard": "#6b705c",
    "grand_library": "#7f5539",
    "forge": "#7f1d1d",
    "clock_tower": "#334155",
    "sky_temple": "#312e81",
    "stone_circle": "#4d7c0f",
}

# ---------------------------
# Game world & engine (logic)
# ---------------------------

def new_game_state():
    return {
        "location": "clearing",
        "inventory": [],
        "flags": {
            "mailbox_opened": False,
            "leaves_searched": False,
            "door_locked": True,
            "lantern_lit": False,
            "basement_seen_with_light": False,
            "library_searched": False,
            "forge_opened": False,
            "reliquary_opened": False,
            "vault_opened": False,
            "altar_completed": False,
            "basement_chest_opened": False,
        },
        "score": 0,
        "visited": set(),
        "theme": "dark",
        "typewriter": False,
    }

ROOMS = {
    "clearing": {
        "name": "Forest Clearing",
        "desc": ("You are in a sun-dappled clearing. To the north, a dense forest looms. "
                 "To the east, an old, weathered house stands silently. "
                 "A small, rusty mailbox is planted by the path to the house."),
        "exits": {"north": "forest", "east": "front_porch"},
        "items": [],
        "details": {"mailbox": "A dented, rusty mailbox on a wobbly post. It looks like it still opens."},
    },
    "forest": {
        "name": "Dark Forest",
        "desc": ("You are in a dark, spooky forest. The trees are thick and block out most of the light. "
                 "A faint path leads south back to the clearing. "
                 "You notice a pile of leaves against a large oak tree. A ring of ancient stones glimmers to the north."),
        "exits": {"south": "clearing", "north": "stone_circle"},
        "items": [],
        "details": {
            "leaves": "A suspicious pile of fallen leaves mounded near the roots of a huge oak.",
            "pile of leaves": "Same suspicious pile of leaves.",
            "stones": "The stones are etched with symbols that pulse when you approach.",
            "stone circle": "Ancient monoliths, cracked but still humming with power."
        },
    },
    "front_porch": {
        "name": "Front Porch",
        "desc": ("You are on the front porch of the old house. The wooden planks creak under your feet. "
                 "The front door is large and imposing. A path leads west back to the clearing."),
        "exits": {"west": "clearing", "south": "living_room"},
        "items": [],
        "details": {
            "door": "A heavy wooden door with an old brass lock.",
            "front door": "A heavy wooden door with an old brass lock."
        },
    },
    "living_room": {
        "name": "Living Room",
        "desc": ("You are in the living room. Dust motes dance in the single beam of light from a grimy window. "
                 "A decaying armchair and a small end table sit silently. There are doorways to the north and east."),
        "exits": {"north": "front_porch", "east": "kitchen"},
        "items": [],
        "details": {
            "armchair": "Stuffing spills from split seams. It has seen better centuries.",
            "table": "A tiny end table with water rings and a deep scratch.",
            "window": "Opaque with grime; almost no light gets through."
        }
    },
    "kitchen": {
        "name": "Kitchen",
        "desc": ("You've entered the kitchen. It smells of mildew and decay. A rusty stove sits in one corner, "
                 "and a rickety table is in the center. On the table, you see an old lantern. "
                 "A dark, ominous staircase leads down into a basement to the south. "
                 "A doorway leads west back to the living room."),
        "exits": {"west": "living_room", "south": "basement"},
        "items": ["lantern"],
        "details": {
            "stove": "Every surface is rust.",
            "table": "Barely level. The lantern rests upon it.",
            "lantern": "Old but serviceable. A bit of oil sloshes inside.",
            "staircase": "Steep and narrow. The shadows pool at the bottom.",
            "stairs": "Steep and narrow. The shadows pool at the bottom."
        }
    },
    "basement": {
        "name": "Pitch-Black Basement",
        "desc_dark": "The basement is pitch black. You can't see a thing. The air is cold and damp.",
        "desc_lit": ("With the lantern lit, you can see the basement clearly—stone walls slick with moisture. "
                     "Cobwebs drape the beams. In the corner, propped against a barrel, is a short, gleaming sword. "
                     "A heavy chest sits half-hidden behind old crates. A broken tunnel yawns east."),
        "exits": {"north": "kitchen", "east": "collapsed_tunnel"},
        "items": ["sword", "chest", "rope"],
        "details": {
            "chest": "An old wooden chest banded with iron. The lid is shut.",
            "barrel": "Dry as bone. Whatever was in it is long gone.",
            "cobwebs": "Strands like silver wire in the lantern glow.",
            "tunnel": "A jagged tunnel reinforced with old mine beams."
        }
    },
    "collapsed_tunnel": {
        "name": "Collapsed Tunnel",
        "desc": ("The tunnel floor is slick with clay and old tracks. Mine carts rust in place. "
                 "A path continues east to a faint blue glow, and south toward whispering catacombs."),
        "exits": {"west": "basement", "east": "underground_lake", "south": "catacombs"},
        "items": [],
        "details": {
            "tracks": "The rails are warped, but you can still follow them by touch.",
            "cart": "A mine cart full of cracked stones and broken tools."
        }
    },
    "underground_lake": {
        "name": "Underground Lake",
        "desc": ("A black mirror of water stretches across the cavern. Bioluminescent moss paints the walls cyan. "
                 "A narrow ledge continues east into a crystal grotto."),
        "exits": {"west": "collapsed_tunnel", "east": "crystal_grotto"},
        "items": [],
        "details": {
            "water": "Still and glassy. Tiny ripples distort your reflection.",
            "moss": "It glows brighter when your lantern passes nearby."
        }
    },
    "crystal_grotto": {
        "name": "Crystal Grotto",
        "desc": ("Needles of crystal jut from floor and ceiling, scattering rainbow light. "
                 "A carved archway north leads to forgotten ruins."),
        "exits": {"west": "underground_lake", "north": "ruins_courtyard"},
        "items": ["pickaxe"],
        "details": {
            "crystals": "Resonant and sharp. They hum softly at the edge of hearing.",
            "archway": "Ancient stonework with geometric carvings."
        }
    },
    "catacombs": {
        "name": "Whispering Catacombs",
        "desc": ("Rows of alcoves stretch into darkness. You hear whispers with no source. "
                 "A locked reliquary chest rests at the far wall."),
        "exits": {"north": "collapsed_tunnel"},
        "items": ["reliquary"],
        "details": {
            "alcoves": "Most are empty, but some still contain cracked funeral masks.",
            "reliquary": "A narrow chest with a moon crest engraved on its latch."
        }
    },
    "ruins_courtyard": {
        "name": "Sunken Ruins Courtyard",
        "desc": ("Broken statues and vine-covered pillars surround a dry fountain. "
                 "Passages lead north to a grand library, west to an old forge, and east to a clock tower."),
        "exits": {"south": "crystal_grotto", "north": "grand_library", "west": "forge", "east": "clock_tower"},
        "items": [],
        "details": {
            "fountain": "No water remains, only coin-sized petals carved in stone.",
            "statues": "Faceless sentinels eroded by centuries underground."
        }
    },
    "grand_library": {
        "name": "Grand Library",
        "desc": ("Towering shelves curve around a domed ceiling painted with constellations. "
                 "Loose papers swirl in a constant indoor breeze."),
        "exits": {"south": "ruins_courtyard"},
        "items": [],
        "details": {
            "shelves": "Dusty but organized by symbols rather than language.",
            "papers": "Some pages sketch maps of a sky temple."
        }
    },
    "forge": {
        "name": "Ember Forge",
        "desc": ("Black anvils and cracked crucibles fill this hall. A sealed furnace glows faintly from within."),
        "exits": {"east": "ruins_courtyard"},
        "items": [],
        "details": {
            "furnace": "A heatproof lockbox built into the furnace housing.",
            "anvil": "Pitted from impacts, yet still perfectly level."
        }
    },
    "clock_tower": {
        "name": "Clock Tower Hall",
        "desc": ("Massive gears rotate overhead with a low metallic pulse. "
                 "A bridge of stone to the east leads into a floating sky temple."),
        "exits": {"west": "ruins_courtyard", "east": "sky_temple"},
        "items": [],
        "details": {
            "gears": "Each tooth is etched with numerals from an unknown system.",
            "bridge": "The bridge floats without visible support."
        }
    },
    "sky_temple": {
        "name": "Sky Temple Vault",
        "desc": ("The chamber glows with starlight that has no source. At the center stands a tri-seal vault chest."),
        "exits": {"west": "clock_tower"},
        "items": ["vault_chest"],
        "details": {
            "vault": "Three circular recesses demand matching sigils.",
            "chest": "A vault chest with three empty sigil slots."
        }
    },
    "stone_circle": {
        "name": "Stone Circle",
        "desc": ("Ancient monoliths surround a low altar carved with a relic-shaped indentation."),
        "exits": {"south": "forest"},
        "items": ["altar"],
        "details": {
            "altar": "A polished groove in the exact shape of a relic.",
            "monoliths": "They vibrate softly as if singing through stone."
        }
    },
}

ITEMS = {
    "pamphlet": {
        "aliases": ["pamphlet", "brochure"],
        "portable": True,
        "desc": ("The pamphlet reads: 'Welcome to Zork! The Great Underground Empire awaits. "
                 "DANGER lies ahead!' It seems to be an advertisement."),
    },
    "key": {
        "aliases": ["key", "brass key", "tarnished key"],
        "portable": True,
        "desc": "A small tarnished brass key. The bit is simple.",
    },
    "lantern": {
        "aliases": ["lantern", "lamp"],
        "portable": True,
        "desc": "A dented oil lantern. It smells faintly of kerosene.",
    },
    "sword": {
        "aliases": ["sword", "short sword"],
        "portable": True,
        "desc": "A surprisingly sharp short sword. Balanced and eager.",
    },
    "chest": {
        "aliases": ["chest", "treasure chest"],
        "portable": False,
        "desc": "Heavy and iron-banded. The lid is shut.",
    },
    "rope": {
        "aliases": ["rope", "coil of rope"],
        "portable": True,
        "desc": "A coil of sturdy rope, stiff with age but still usable.",
    },
    "pickaxe": {
        "aliases": ["pickaxe", "pick"],
        "portable": True,
        "desc": "A miner's pickaxe, surprisingly well balanced.",
    },
    "moon_sigil": {
        "aliases": ["moon sigil", "moon crest"],
        "portable": True,
        "desc": "A silver sigil embossed with a crescent moon.",
    },
    "sun_sigil": {
        "aliases": ["sun sigil", "sun crest"],
        "portable": True,
        "desc": "A golden sigil stamped with a radiant sunburst.",
    },
    "ember_sigil": {
        "aliases": ["ember sigil", "ember crest"],
        "portable": True,
        "desc": "A copper sigil warm to the touch.",
    },
    "relic": {
        "aliases": ["relic", "sky relic", "star relic"],
        "portable": True,
        "desc": "A crystalline relic that refracts light into tiny constellations.",
    },
    "reliquary": {
        "aliases": ["reliquary", "reliquary chest"],
        "portable": False,
        "desc": "A moon-marked chest with a mechanical latch.",
    },
    "vault_chest": {
        "aliases": ["vault chest", "vault", "tri-seal chest"],
        "portable": False,
        "desc": "An ornate chest with three sigil sockets.",
    },
    "altar": {
        "aliases": ["altar", "stone altar"],
        "portable": False,
        "desc": "A monolithic altar waiting for something sacred.",
    },
}

DIRECTIONS = {
    "n": "north", "s": "south", "e": "east", "w": "west",
    "north": "north", "south": "south", "east": "east", "west": "west"
}

def normalize_item(token):
    token = token.strip().lower()
    for key, data in ITEMS.items():
        for alias in data["aliases"]:
            if token == alias:
                return key
    return None

# ---------------------------
# GUI application
# ---------------------------

class AdventureApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.minsize(820, 560)
        self.state = new_game_state()
        self.sanitize_state()
        self.cmd_history = []
        self.hist_index = -1
        self.build_ui()
        self.apply_theme(self.state["theme"])
        self.print_welcome()
        self.describe_room()

    # ----- UI build -----
    def build_ui(self):
        # Menus
        menubar = tk.Menu(self)
        filem = tk.Menu(menubar, tearoff=0)
        filem.add_command(label="Save…", command=self.save_game, accelerator="Ctrl+S")
        filem.add_command(label="Load…", command=self.load_game, accelerator="Ctrl+O")
        filem.add_separator()
        filem.add_command(label="Exit", command=self.quit, accelerator="Alt+F4")
        menubar.add_cascade(label="File", menu=filem)

        viewm = tk.Menu(menubar, tearoff=0)
        viewm.add_command(label="Theme: Dark", command=lambda: self.set_theme_cmd("dark"))
        viewm.add_command(label="Theme: Light", command=lambda: self.set_theme_cmd("light"))
        viewm.add_checkbutton(label="Typewriter", command=self.toggle_typewriter)
        viewm.add_command(label="Clear Screen", command=self.clear_console)
        menubar.add_cascade(label="View", menu=viewm)

        self.config(menu=menubar)
        self.bind_all("<Control-s>", lambda e: self.save_game())
        self.bind_all("<Control-o>", lambda e: self.load_game())

        # Layout
        outer = ttk.Frame(self, padding=(8, 8, 8, 8))
        outer.pack(fill="both", expand=True)

        # Visual area
        visual_row = ttk.Frame(outer)
        visual_row.pack(fill="x", pady=(0, 8))

        self.scene_canvas = tk.Canvas(visual_row, height=190, highlightthickness=1)
        self.scene_canvas.pack(side="left", fill="x", expand=True)
        self.map_canvas = tk.Canvas(visual_row, width=260, height=190, highlightthickness=1)
        self.map_canvas.pack(side="left", padx=(8, 0))

        # Console (Text) with scrollbar
        console_frame = ttk.Frame(outer)
        console_frame.pack(fill="both", expand=True)
        self.console = tk.Text(console_frame, wrap="word", height=18, state="disabled", undo=False)
        self.console_scroll = ttk.Scrollbar(console_frame, command=self.console.yview)
        self.console.configure(yscrollcommand=self.console_scroll.set)
        self.console.pack(side="left", fill="both", expand=True)
        self.console_scroll.pack(side="right", fill="y")

        # Status bar
        self.status = ttk.Label(outer, anchor="w")
        self.status.pack(fill="x", pady=(6, 2))

        # Input line
        input_row = ttk.Frame(outer)
        input_row.pack(fill="x")
        self.prompt = ttk.Label(input_row, text="> ")
        self.entry = ttk.Entry(input_row)
        self.entry.bind("<Return>", self.on_enter)
        self.entry.bind("<Up>", self.on_hist_up)
        self.entry.bind("<Down>", self.on_hist_down)
        self.prompt.pack(side="left")
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.focus_set()

        # Text tags (colors/styles)
        self.console.tag_configure("title", font=("Consolas", 14, "bold"))
        self.console.tag_configure("good", foreground="#6ee16e")  # green
        self.console.tag_configure("bad",  foreground="#ff6b6b")  # red
        self.console.tag_configure("info", foreground=self.fg())
        self.console.tag_configure("dim",  foreground=self.dimfg())
        self.draw_visuals()

    # ----- Theming -----
    def bg(self):
        return "#0b0f14" if self.state["theme"] == "dark" else "#f5f7fb"
    def fg(self):
        return "#d6e2f0" if self.state["theme"] == "dark" else "#0b0f14"
    def dimfg(self):
        return "#8aa0b2" if self.state["theme"] == "dark" else "#5a6b77"
    def boxfg(self):
        return "#334155" if self.state["theme"] == "dark" else "#b8c2cc"

    def apply_theme(self, variant):
        style = ttk.Style(self)
        if sys.platform.startswith("win"):
            style.theme_use("winnative")
        else:
            # fallbacks
            try:
                style.theme_use("clam")
            except tk.TclError:
                pass

        self.state["theme"] = variant
        self.configure(bg=self.bg())
        style.configure(".", background=self.bg(), foreground=self.fg())
        style.configure("TLabel", background=self.bg(), foreground=self.fg())
        style.configure("TFrame", background=self.bg())
        style.configure("TEntry", fieldbackground="#111827" if variant=="dark" else "#ffffff",
                        foreground=self.fg())
        style.configure("TMenubutton", background=self.bg(), foreground=self.fg())

        self.console.configure(bg=self.bg(), fg=self.fg(), insertbackground=self.fg())
        self.console.tag_configure("info", foreground=self.fg())
        self.console.tag_configure("dim", foreground=self.dimfg())
        self.scene_canvas.configure(bg=self.bg(), highlightbackground=self.boxfg())
        self.map_canvas.configure(bg=self.bg(), highlightbackground=self.boxfg())

        self.update_status()
        self.draw_visuals()

    def set_theme_cmd(self, variant):
        self.apply_theme(variant)
        self.describe_room()

    def toggle_typewriter(self):
        self.state["typewriter"] = not self.state["typewriter"]

    # ----- Console helpers -----
    def append(self, text, tag="info", newline=True, slow=False):
        """Append text to console with optional typewriter effect."""
        self.console.configure(state="normal")
        if slow and self.state["typewriter"]:
            for ch in text:
                self.console.insert("end", ch, tag)
                self.console.see("end")
                self.console.update()
                self.console.after(8)
            if newline:
                self.console.insert("end", "\n", tag)
        else:
            self.console.insert("end", text + ("\n" if newline else ""), tag)
        self.console.configure(state="disabled")
        self.console.see("end")

    def append_paragraph(self, text, tag="info", slow=False):
        width = max(70, int(self.console.winfo_width() / 7))  # rough wrap by pixels->chars
        lines = []
        for para in text.split("\n"):
            if para.strip():
                lines.extend(_wrap(para, width=width))
            else:
                lines.append("")
        for i, line in enumerate(lines):
            self.append(line, tag=tag, newline=(i < len(lines)-1), slow=slow)

    def clear_console(self):
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        self.console.configure(state="disabled")

    # ----- Status bar -----
    def update_status(self):
        inv = ", ".join(ITEMS[i]["aliases"][0] for i in self.state["inventory"]) if self.state["inventory"] else "nothing"
        locname = ROOMS[self.state["location"]]["name"]
        self.status.configure(text=f"{locname}   •   Score: {self.state['score']}   •   Inventory: {inv}")
        self.draw_visuals()

    # ----- Game I/O -----
    def print_welcome(self):
        self.append(APP_TITLE, tag="title")
        self.append_paragraph("Welcome to The Underground Adventure!", tag="info", slow=True)
        self.append_paragraph("New quest: explore the expanded underground world, gather moon/sun/ember sigils, open the sky vault, and place the relic at the Stone Circle.", tag="dim")
        self.append("", tag="info")
        self.append("Type 'help' for commands. Theme: View → Theme or 'theme dark|light'.", tag="dim")

    def describe_room(self):
        key = self.state["location"]
        room = ROOMS[key]
        self.state["visited"].add(key)
        if key == "basement":
            desc = room["desc_lit"] if self.state["flags"]["lantern_lit"] else room["desc_dark"]
        else:
            desc = room["desc"]
        visible = self.room_visible_items(key)
        if visible:
            names = [ITEMS[i]["aliases"][0] for i in visible]
            desc += f" (You see: {', '.join(names)}.)"
        exits = ", ".join(sorted(room["exits"].keys()))
        desc += f" [Exits: {exits}]"
        self.append_paragraph("", slow=False)
        self.append_paragraph(desc, slow=True)
        self.update_status()

    def draw_visuals(self):
        self.draw_scene()
        self.draw_map()

    def draw_scene(self):
        c = self.scene_canvas
        c.delete("all")
        w = max(c.winfo_width(), 520)
        h = max(c.winfo_height(), 190)
        loc = self.state["location"]
        room = ROOMS[loc]
        panel = ROOM_COLORS.get(loc, "#3a3f4b")
        for i in range(18):
            band_color = panel if i % 2 == 0 else self.bg()
            alpha_blend = "#" + "".join(f"{(int(panel[j:j+2], 16) + int(self.bg()[j:j+2], 16)) // 2:02x}" for j in (1, 3, 5))
            c.create_rectangle(0, i * (h / 18), w, (i + 1) * (h / 18), fill=alpha_blend if i % 3 == 0 else band_color, outline="")
        c.create_rectangle(10, 10, w - 10, h - 10, outline="#ffffff", width=2)
        c.create_text(24, 30, text=room["name"], fill="#ffffff", font=("Consolas", 18, "bold"), anchor="w")
        icon = {
            "forest": "🌲", "clearing": "🌿", "front_porch": "🏚", "living_room": "🛋",
            "kitchen": "🕯", "basement": "🕳", "collapsed_tunnel": "⛏", "underground_lake": "🌊",
            "crystal_grotto": "💎", "catacombs": "💀", "ruins_courtyard": "🏛",
            "grand_library": "📚", "forge": "🔥", "clock_tower": "⚙", "sky_temple": "✨", "stone_circle": "🗿"
        }.get(loc, "✦")
        c.create_text(w - 42, 34, text=icon, fill="#ffffff", font=("Segoe UI Emoji", 24), anchor="center")
        visible = self.room_visible_items(loc)
        exits = ", ".join(sorted(room["exits"].keys()))
        inventory_count = len(self.state["inventory"])
        lantern = "Lit" if self.state["flags"]["lantern_lit"] else "Unlit"
        door = "Unlocked" if not self.state["flags"]["door_locked"] else "Locked"
        c.create_text(24, 64, text=f"Exits: {exits}", fill="#eef2ff", font=("Consolas", 11), anchor="w")
        c.create_text(24, 88, text=f"Visible items: {', '.join(ITEMS[i]['aliases'][0] for i in visible) if visible else 'none'}",
                      fill="#eef2ff", font=("Consolas", 11), anchor="w")
        c.create_text(24, 112, text=f"Inventory slots used: {inventory_count}    Lantern: {lantern}    Front door: {door}",
                      fill="#eef2ff", font=("Consolas", 11), anchor="w")
        if self.state["visited"]:
            c.create_text(24, 136, text=f"World explored: {len(self.state['visited'])}/{len(ROOMS)} rooms",
                          fill="#dbeafe", font=("Consolas", 10), anchor="w")
        c.create_oval(w - 145, h - 64, w - 25, h - 20, fill="#0f172a", outline="#93c5fd", width=2)
        c.create_text(w - 85, h - 42, text=f"Score {self.state['score']}", fill="#e0f2fe", font=("Consolas", 11, "bold"))
        c.create_text(w - 28, h - 24, text="Zark Visual HUD", fill="#dbeafe", font=("Consolas", 10, "italic"), anchor="e")

    def draw_map(self):
        c = self.map_canvas
        c.delete("all")
        c.create_text(12, 16, text="World Map", anchor="w", fill=self.fg(), font=("Consolas", 12, "bold"))
        layout = {
            "stone_circle": (34, 28),
            "forest": (34, 58),
            "clearing": (34, 88),
            "front_porch": (34, 118),
            "living_room": (72, 118),
            "kitchen": (72, 88),
            "basement": (72, 58),
            "collapsed_tunnel": (110, 58),
            "underground_lake": (146, 58),
            "crystal_grotto": (182, 58),
            "ruins_courtyard": (182, 90),
            "grand_library": (182, 122),
            "forge": (146, 90),
            "clock_tower": (218, 90),
            "sky_temple": (242, 90),
            "catacombs": (110, 28),
        }
        edges = [
            ("stone_circle", "forest"),
            ("forest", "clearing"),
            ("clearing", "front_porch"),
            ("front_porch", "living_room"),
            ("living_room", "kitchen"),
            ("kitchen", "basement"),
            ("basement", "collapsed_tunnel"),
            ("collapsed_tunnel", "underground_lake"),
            ("collapsed_tunnel", "catacombs"),
            ("underground_lake", "crystal_grotto"),
            ("crystal_grotto", "ruins_courtyard"),
            ("ruins_courtyard", "grand_library"),
            ("ruins_courtyard", "forge"),
            ("ruins_courtyard", "clock_tower"),
            ("clock_tower", "sky_temple"),
        ]
        for a, b in edges:
            x1, y1 = layout[a]
            x2, y2 = layout[b]
            c.create_line(x1, y1, x2, y2, fill=self.dimfg(), width=2)
        for room_key, (x, y) in layout.items():
            is_here = (room_key == self.state["location"])
            seen = room_key in self.state["visited"]
            fill = "#60a5fa" if is_here else (ROOM_COLORS.get(room_key, "#4b5563") if seen else "#1f2937")
            outline = "#ffffff" if is_here else self.boxfg()
            c.create_oval(x - 12, y - 10, x + 12, y + 10, fill=fill, outline=outline, width=2)
            if seen or is_here:
                c.create_text(x, y + 16, text=room_key.replace("_", " "), fill=self.fg(), font=("Consolas", 6))

    def room_visible_items(self, room_key):
        items = list(ROOMS[room_key].get("items", []))
        if room_key == "basement" and not self.state["flags"]["lantern_lit"]:
            items = []
        return items

    def sanitize_state(self):
        """Resolve save/load and progression state conflicts safely."""
        if self.state.get("location") not in ROOMS:
            self.state["location"] = "clearing"

        # keep only valid, unique inventory items
        inv_clean = []
        for item in self.state.get("inventory", []):
            if item in ITEMS and item not in inv_clean:
                inv_clean.append(item)
        self.state["inventory"] = inv_clean

        # visited should only contain valid rooms
        visited = self.state.get("visited", set())
        if not isinstance(visited, set):
            visited = set(visited)
        self.state["visited"] = {r for r in visited if r in ROOMS}

        # remove items from rooms if already carried to avoid duplication conflicts
        inv_set = set(self.state["inventory"])
        for room in ROOMS.values():
            room["items"] = [i for i in room.get("items", []) if i not in inv_set]

        # keep flags dictionary intact with defaults merged in
        flags = new_game_state()["flags"]
        flags.update(self.state.get("flags", {}))
        self.state["flags"] = flags

    def have(self, item_key):
        return item_key in self.state["inventory"]

    # ----- Input handling -----
    def on_enter(self, event=None):
        raw = self.entry.get().strip()
        if not raw:
            return
        self.entry.delete(0, "end")
        self.cmd_history.append(raw)
        self.hist_index = len(self.cmd_history)
        self.append(f"> {raw}", tag="dim")

        tokens = self.normalize_command(raw.split())
        cmd = tokens[0].lower()
        args = tokens[1:]

        # command routing
        handlers = {
            "look": self.cmd_look, "l": self.cmd_look, "examine": self.cmd_look,
            "go": self.cmd_go, "move": self.cmd_go, "walk": self.cmd_go,
            "n": self.cmd_go, "s": self.cmd_go, "e": self.cmd_go, "w": self.cmd_go,
            "take": self.cmd_take, "get": self.cmd_take,
            "drop": self.cmd_drop,
            "inventory": self.cmd_inventory, "i": self.cmd_inventory,
            "open": self.cmd_open,
            "use": self.cmd_use,
            "light": self.cmd_light,
            "search": self.cmd_search,
            "read": self.cmd_read,
            "map": self.cmd_map,
            "place": self.cmd_place,
            "save": self.cmd_save_cmd,
            "load": self.cmd_load_cmd,
            "help": self.cmd_help, "?": self.cmd_help,
            "theme": self.cmd_theme,
            "cls": self.cmd_cls,
            "fast": self.cmd_fast_toggle,  # fast on/off
            "quit": self.cmd_quit, "exit": self.cmd_quit,
        }
        fn = handlers.get(cmd)
        if fn:
            fn(args)
        else:
            self.append("I don't understand that command. Type 'help' for options.", tag="bad")

    def on_hist_up(self, event=None):
        if self.cmd_history and self.hist_index > 0:
            self.hist_index -= 1
            self.entry.delete(0, "end")
            self.entry.insert(0, self.cmd_history[self.hist_index])
    def on_hist_down(self, event=None):
        if self.cmd_history and self.hist_index < len(self.cmd_history) - 1:
            self.hist_index += 1
            self.entry.delete(0, "end")
            self.entry.insert(0, self.cmd_history[self.hist_index])
        else:
            self.hist_index = len(self.cmd_history)
            self.entry.delete(0, "end")

    def normalize_command(self, tokens):
        if not tokens: return tokens
        head = tokens[0].lower()
        if head in ("n","s","e","w"):
            return ["go", head]
        return [head] + tokens[1:]

    # ----- Commands -----
    def cmd_help(self, _):
        msg = (
            "Commands:\n"
            "  look/l/examine [thing]   open [thing]          search [thing]\n"
            "  go/move/walk [n|s|e|w]   n/s/e/w               take/get [item]\n"
            "  use [item] (on [thing])  light (lantern)       read [item]\n"
            "  inventory/i              drop [item]           map, place [item]\n"
            "  save, load, quit\n"
            "Extras:\n"
            "  theme dark|light         fast on|off           cls"
        )
        self.append_paragraph(msg)

    def cmd_theme(self, args):
        if not args or args[0].lower() not in ("dark","light"):
            self.append("Usage: theme dark|light", tag="bad"); return
        self.apply_theme(args[0].lower())
        self.append(f"Theme set to {args[0].lower()}.", tag="good")
        self.describe_room()

    def cmd_fast_toggle(self, args):
        if not args or args[0].lower() not in ("on","off"):
            self.append("Usage: fast on|off"); return
        self.state["typewriter"] = (args[0].lower() == "on")
        self.append(f"Typewriter {'enabled' if self.state['typewriter'] else 'disabled'}.", tag="good")

    def cmd_cls(self, _):
        self.clear_console()
        self.describe_room()

    def cmd_quit(self, _):
        self.append(f"Farewell. Final score: {self.state['score']}")
        self.after(200, self.quit)

    def cmd_look(self, args):
        if not args:
            self.describe_room(); return
        target = " ".join(args).lower()
        loc = self.state["location"]

        if loc == "clearing" and target == "mailbox":
            if not self.state["flags"]["mailbox_opened"]:
                self.append("You open the small mailbox. Inside, there's a single, folded pamphlet.", tag="good")
                self.add_to_room("clearing", "pamphlet")
                self.state["flags"]["mailbox_opened"] = True
                self.state["score"] += 1
                self.update_status()
            else:
                self.append("The mailbox yawns emptily.")
            return

        if loc == "forest" and target in ("leaves","pile of leaves"):
            if not self.state["flags"]["leaves_searched"]:
                self.append("You kick through the pile of leaves and uncover a small, tarnished brass key.", tag="good")
                self.add_to_room("forest", "key")
                self.state["flags"]["leaves_searched"] = True
                self.state["score"] += 1
                self.update_status()
            else:
                self.append("Just a pile of recently disturbed leaves.")
            return

        details = ROOMS[loc].get("details", {})
        if target in details:
            self.append(details[target]); return

        for item_key in self.room_visible_items(loc):
            if target in ITEMS[item_key]["aliases"]:
                self.append(ITEMS[item_key]["desc"]); return

        for item_key in self.state["inventory"]:
            if target in ITEMS[item_key]["aliases"]:
                self.append(ITEMS[item_key]["desc"]); return

        self.append(f"You don't see anything special about the {target}.")

    def cmd_go(self, args):
        if not args:
            self.append("Go where?"); return
        d = DIRECTIONS.get(args[0].lower())
        if not d:
            self.append("That's not a direction.", tag="bad"); return
        here = ROOMS[self.state["location"]]
        if self.state["location"] == "front_porch" and d == "south" and self.state["flags"]["door_locked"]:
            self.append("The front door is locked.", tag="bad"); return
        dest = here["exits"].get(d)
        if not dest:
            self.append("You can't go that way.", tag="bad"); return
        self.state["location"] = dest
        self.describe_room()

    def cmd_take(self, args):
        if not args:
            self.append("Take what?"); return
        target = normalize_item(" ".join(args))
        if not target:
            self.append("I don't know what you mean."); return
        if self.state["location"] == "basement" and not self.state["flags"]["lantern_lit"]:
            self.append("It's too dark to find anything to take.", tag="bad"); return
        vis = self.room_visible_items(self.state["location"])
        if target in vis:
            if not ITEMS[target]["portable"]:
                self.append("It's far too heavy to take.", tag="bad"); return
            self.remove_from_room(self.state["location"], target)
            self.state["inventory"].append(target)
            self.state["score"] += 1
            self.update_status()
            self.append("Taken.", tag="good")
        else:
            self.append("You don't see that here.", tag="bad")

    def cmd_drop(self, args):
        if not args:
            self.append("Drop what?"); return
        target = normalize_item(" ".join(args))
        if not target or target not in self.state["inventory"]:
            self.append("You aren't carrying that.", tag="bad"); return
        self.state["inventory"].remove(target)
        self.add_to_room(self.state["location"], target)
        self.update_status()
        self.append("Dropped.", tag="good")

    def cmd_inventory(self, _):
        inv = ", ".join(ITEMS[i]["aliases"][0] for i in self.state["inventory"]) or "nothing"
        self.append("You are carrying: " + inv)

    def cmd_map(self, _):
        if not self.state["visited"]:
            self.append("Your map is blank."); return
        visited_names = [ROOMS[k]["name"] for k in sorted(self.state["visited"])]
        self.append("Discovered areas:")
        for name in visited_names:
            self.append(f"  - {name}", tag="dim")

    def cmd_place(self, args):
        if not args:
            self.append("Place what?"); return
        name = " ".join(args).lower()
        if self.state["location"] != "stone_circle" or name not in ("relic", "sky relic", "star relic"):
            self.append("There's nowhere suitable to place that."); return
        if not self.have("relic"):
            self.append("You don't have the relic.", tag="bad"); return
        self.state["inventory"].remove("relic")
        self.state["flags"]["altar_completed"] = True
        self.state["score"] += 10
        self.update_status()
        self.append("You set the relic into the altar. The monoliths ignite with starfire.", tag="good")
        self.append(f"*** You win! Final score: {self.state['score']} ***", tag="good")
        messagebox.showinfo(APP_TITLE, "You restored the Stone Circle. You win!")
        self.quit()

    def cmd_open(self, args):
        if not args:
            self.append("Open what?"); return
        target = " ".join(args).lower()
        if self.state["location"] == "clearing" and target == "mailbox":
            self.cmd_look(["mailbox"]); return
        if self.state["location"] == "front_porch" and target in ("door","front door"):
            if self.state["flags"]["door_locked"]:
                self.append("The door is locked.", tag="bad")
            else:
                self.append("You open the front door. The way south is clear.", tag="good")
            return
        if self.state["location"] == "basement" and target in ("chest","treasure chest"):
            if not self.state["flags"]["lantern_lit"]:
                self.append("You fumble in the dark. Perhaps some light first?", tag="bad"); return
            if not self.state["flags"]["basement_chest_opened"]:
                self.state["flags"]["basement_chest_opened"] = True
                if "moon_sigil" not in self.state["inventory"] and "moon_sigil" not in ROOMS["basement"]["items"]:
                    self.add_to_room("basement", "moon_sigil")
                self.append("With a groan the chest opens. Inside, resting on velvet, is a moon sigil.", tag="good")
                self.state["score"] += 2
                self.update_status()
            else:
                self.append("The basement chest is empty now.")
            return
        if self.state["location"] == "catacombs" and target in ("reliquary","reliquary chest","chest"):
            if not self.have("sword"):
                self.append("A wraith rises from the alcoves. You need a weapon before opening this.", tag="bad"); return
            if not self.state["flags"]["reliquary_opened"]:
                self.state["flags"]["reliquary_opened"] = True
                self.state["score"] += 2
                self.append("You force the latch and find journals detailing how to awaken the sky vault with three sigils.", tag="good")
                self.update_status()
            else:
                self.append("The reliquary stands open and empty.")
            return
        if self.state["location"] == "forge" and target in ("furnace","lockbox"):
            if not self.state["flags"]["lantern_lit"]:
                self.append("The controls are too dark to read. Light the lantern first.", tag="bad"); return
            if not self.state["flags"]["forge_opened"]:
                self.state["flags"]["forge_opened"] = True
                self.add_to_room("forge", "ember_sigil")
                self.state["score"] += 2
                self.append("Steam hisses out as the furnace lockbox opens, revealing an ember sigil.", tag="good")
                self.update_status()
            else:
                self.append("The lockbox hangs open.")
            return
        if self.state["location"] == "sky_temple" and target in ("vault chest","vault","chest"):
            needed = {"moon_sigil", "sun_sigil", "ember_sigil"}
            if not needed.issubset(set(self.state["inventory"])):
                self.append("Three sigils are required: moon, sun, and ember.", tag="bad"); return
            if not self.state["flags"]["vault_opened"]:
                self.state["flags"]["vault_opened"] = True
                self.add_to_room("sky_temple", "relic")
                self.state["score"] += 5
                self.append("The three sigils flare to life and the vault chest unlocks. A star relic rises out.", tag="good")
                self.update_status()
            else:
                self.append("The vault is open.")
            return
        self.append("It doesn't seem to open.")

    def cmd_use(self, args):
        if not args:
            self.append("Use what?"); return
        text = " ".join(args).lower()
        m = re.match(r"(.+?)\s+(on|with)\s+(.+)", text)
        if m:
            item_name, _, target_name = m.groups()
        else:
            item_name, target_name = text, None

        item_key = next((k for k in self.state["inventory"]
                         if item_name in ITEMS[k]["aliases"]), None)
        if not item_key:
            self.append("You don't have that.", tag="bad"); return

        if item_key == "key" and self.state["location"] == "front_porch":
            if target_name and target_name not in ("door","front door"):
                self.append("That key doesn't fit there.", tag="bad"); return
            if self.state["flags"]["door_locked"]:
                self.state["flags"]["door_locked"] = False
                self.state["score"] += 2
                self.update_status()
                self.append("You turn the key. With a loud *CLICK*, the door unlocks.", tag="good")
            else:
                self.append("The door is already unlocked.")
            return

        if item_key == "lantern":
            self.cmd_light([]); return
        if item_key == "relic" and self.state["location"] == "stone_circle":
            self.cmd_place(["relic"]); return

        self.append("Nothing happens.")

    def cmd_light(self, _):
        if self.have("lantern"):
            if self.state["flags"]["lantern_lit"]:
                self.append("The lantern is already lit."); return
            self.state["flags"]["lantern_lit"] = True
            self.state["score"] += 1
            self.update_status()
            self.append("You strike a spark and light the lantern. Warm, steady light floods the gloom.", tag="good")
            if self.state["location"] == "basement":
                self.describe_room()
        else:
            self.append("You have nothing to light.", tag="bad")

    def cmd_search(self, args):
        if not args:
            self.append("Search what?"); return
        t = " ".join(args).lower()
        if self.state["location"] == "forest" and t in ("leaves","pile of leaves"):
            self.cmd_look(["leaves"]); return
        if self.state["location"] == "clearing" and t == "mailbox":
            self.cmd_look(["mailbox"]); return
        if self.state["location"] == "grand_library" and t in ("shelves", "books", "bookcase"):
            if not self.state["flags"]["library_searched"]:
                self.state["flags"]["library_searched"] = True
                self.add_to_room("grand_library", "sun_sigil")
                self.state["score"] += 2
                self.update_status()
                self.append("Behind a sliding shelf panel you discover a sun sigil.", tag="good")
            else:
                self.append("You already found the library's hidden compartment.")
            return
        self.append("You find nothing of note.")

    def cmd_read(self, args):
        if not args:
            self.append("Read what?"); return
        name = " ".join(args).lower()
        if self.have("pamphlet") and name in ("pamphlet","brochure"):
            self.append(ITEMS["pamphlet"]["desc"]); return
        self.append("Nothing to read.")

    def cmd_save_cmd(self, _):
        self.save_game()

    def cmd_load_cmd(self, _):
        self.load_game()

    # ----- Persistence -----
    def save_game(self):
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            initialfile=SAVE_DEFAULT,
                                            filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if not path:
            return
        data = self.state.copy()
        data["visited"] = list(data.get("visited", []))
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.append(f"Game saved to {os.path.basename(path)}.", tag="good")
        except Exception as e:
            messagebox.showerror(APP_TITLE, f"Save failed:\n{e}")

    def load_game(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            defaults = new_game_state()
            merged = defaults.copy()
            merged.update(data)
            merged_flags = defaults["flags"].copy()
            merged_flags.update(data.get("flags", {}))
            merged["flags"] = merged_flags
            merged["visited"] = set(merged.get("visited", []))
            # keep current theme/typewriter (UX), but load rest
            keep_theme = self.state["theme"]
            keep_type = self.state["typewriter"]
            self.state = merged
            self.sanitize_state()
            self.state["theme"] = keep_theme
            self.state["typewriter"] = keep_type
            self.apply_theme(self.state["theme"])
            self.append("Game loaded.", tag="good")
            self.describe_room()
        except Exception as e:
            messagebox.showerror(APP_TITLE, f"Load failed:\n{e}")

    # ----- World helpers -----
    def add_to_room(self, room_key, item_key):
        ROOMS[room_key].setdefault("items", [])
        if item_key not in ROOMS[room_key]["items"]:
            ROOMS[room_key]["items"].append(item_key)

    def remove_from_room(self, room_key, item_key):
        ROOMS[room_key]["items"] = [i for i in ROOMS[room_key].get("items", []) if i != item_key]


if __name__ == "__main__":
    app = AdventureApp()
    app.mainloop()
