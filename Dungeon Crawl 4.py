
import json
import math
import os
import random
import sys
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import pygame
import numpy as np

# ======================= CONFIG =======================
WIDTH, HEIGHT = 1920, 1080
FPS = 60
FONT_NAME = "consolas"

DIFFICULTY = {
    "Easy":   {"enemy_hp":0.9,"enemy_dmg":0.8,"enemy_speed":0.95,"max_enemies":6},
    "Normal": {"enemy_hp":1.0,"enemy_dmg":1.0,"enemy_speed":1.0, "max_enemies":7},
    "Hard":   {"enemy_hp":1.2,"enemy_dmg":1.25,"enemy_speed":1.05,"max_enemies":9},
}

PLAYER_SPEED = 340
PLAYER_HP = 140
PLAYER_MANA = 80

BASIC_DMG = (7, 12)
POWER_DMG = (18, 30)
BASIC_CD = 0.18
POWER_CD = 0.60
POWER_MANA_COST = 12
PROJECTILE_SPEED = 760
BASIC_RADIUS = 6
POWER_RADIUS = 9
BASIC_PIERCE = 1
POWER_PIERCE = 1

MULTISHOT_COUNT = 5
MULTISHOT_SPREAD = math.pi / 4  # 45-degree fan

DASH_SPEED = 700
DASH_TIME = 0.22
DASH_CD = 1.5
IFRAME_TIME = 0.25

POTION_HEAL = 50
POTION_MANA = 40

ENEMY_BASE_HP = 40
ENEMY_BASE_DMG = (4, 8)
ENEMY_SPEED = 150
SPAWN_INTERVAL = 6.0
WAVE_SCALE = 1.10
MAX_ACTIVE_ENEMIES = 7

ELITE_PACK_CHANCE = 0.35
PACK_SIZE_RANGE = (3, 6)
ELITE_MULT = {"hp": 2.6, "dmg": 1.8, "spd": 1.08, "radius": 26}
AURA_RADIUS = 300
AURAS = {
    "haste":    {"speed":1.28,"damage":1.00,"taken":1.00,"color":(120,200,255)},
    "frenzy":   {"speed":1.00,"damage":1.35,"taken":1.00,"color":(255,150,90)},
    "guardian":  {"speed":1.00,"damage":1.00,"taken":0.66,"color":(120,255,160)},
}

BOSS_HP = 600
BOSS_DMG = (8, 14)
BOSS_SHOT_CD = (1.0, 1.6)
BOSS_PROJ_SPEED = 480

DMG_BOOST_MULT = 1.6
DMG_BOOST_TIME = 8.0
SHIELD_POINTS = 70
PICKUP_SPAWN_CHANCE = 0.25

GOLD_DROP = (3, 12)
POTION_DROP_CHANCE = 0.10
LOOT_DROP_CHANCE = 0.08
DMG_PICKUP_DROP_CHANCE = 0.06
SHIELD_PICKUP_DROP_CHANCE = 0.06

CHEST_HP = 3
CHEST_SPAWN_PER_ROOM = 0.45  # chance per room to have a chest
CHEST_GOLD_DROP = (8, 25)
CHEST_POTION_CHANCE = 0.35
CHEST_WEAPON_CHANCE = 0.10
CHEST_BOOST_CHANCE = 0.12
CRATE_HP = 1
CRATE_EXPLODE_CHANCE = 0.30  # chance a crate explodes on break
CRATE_EXPLODE_DMG = (4, 10)
CRATE_EXPLODE_RADIUS = 80
CRATE_DROP_CHANCE = 0.25  # much less than chests

MANA_REGEN_RATE = 3.0  # mana per second

INFUSION_DURATION = 15.0
INFUSION_TYPES = ["fire", "ice", "lightning"]
INFUSION_DROP_CHANCE = 0.07
INFUSION_COLORS = {"fire": (255, 140, 40), "ice": (140, 200, 255), "lightning": (255, 255, 100)}

GOBLIN_SPAWN_CHANCE = 0.06  # per wave
GOBLIN_SPEED_MULT = 1.5
GOBLIN_DESPAWN_TIME = 18.0
GOBLIN_LOOT_INTERVAL = 0.6

TILE = 48
MAP_W, MAP_H = 180, 140
WALL = 1
FLOOR = 0

BIOMES = ["crypt", "cave", "firepit", "icecavern", "swamp"]
BIOME_COLORS = {
    "crypt":      {"wall_base": 38, "floor_r": 22, "floor_g": 20, "floor_b": 24,
                   "wall_tint": (0, -2, 8), "floor_tint": (0, -2, 4)},
    "cave":       {"wall_base": 48, "floor_r": 35, "floor_g": 30, "floor_b": 22,
                   "wall_tint": (6, 2, -4), "floor_tint": (4, 2, -2)},
    "firepit":    {"wall_base": 42, "floor_r": 30, "floor_g": 16, "floor_b": 12,
                   "wall_tint": (12, -4, -8), "floor_tint": (8, -2, -4)},
    "icecavern":  {"wall_base": 36, "floor_r": 20, "floor_g": 28, "floor_b": 38,
                   "wall_tint": (-4, 2, 12), "floor_tint": (-2, 4, 8)},
    "swamp":      {"wall_base": 34, "floor_r": 18, "floor_g": 28, "floor_b": 16,
                   "wall_tint": (-4, 8, -6), "floor_tint": (-2, 6, -4)},
}
BIOME_AMBIENT = {
    "crypt":     (20, 17, 25),
    "cave":      (25, 20, 15),
    "firepit":   (35, 14, 10),
    "icecavern": (14, 20, 30),
    "swamp":     (16, 24, 14),
}
BIOME_NAMES = {
    "crypt": "Ancient Crypt", "cave": "Dark Caverns", "firepit": "Infernal Pits",
    "icecavern": "Frozen Depths", "swamp": "Poison Swamp",
}
BIOME_HAZARD = {
    "crypt": "poison", "cave": None, "firepit": "lava", "icecavern": "ice", "swamp": "poison",
}
PORTALS_PER_LEVEL = 2

# ============ VISUAL CONFIG ============
AMBIENT_LIGHT = (20, 17, 25)
PLAYER_LIGHT_RADIUS = 400
PLAYER_LIGHT_COLOR = (255, 230, 190)
TORCH_LIGHT_RADIUS = 270
TORCH_LIGHT_COLOR = (255, 180, 80)
PROJ_LIGHT_RADIUS = 110
MAX_PARTICLES = 500
SCREEN_SHAKE_DECAY = 10.0

# ============ COLOR PALETTE (D2R dark fantasy) ============
C_BLOOD = (160, 20, 20)
C_BLOOD_DARK = (100, 10, 10)
C_GOLD = (255, 215, 80)
C_GOLD_DARK = (180, 140, 40)
C_MANA_BLUE = (60, 80, 200)
C_MANA_LIGHT = (100, 140, 255)
C_FIRE = (255, 140, 40)
C_FIRE_BRIGHT = (255, 220, 100)
C_POISON = (80, 200, 60)
C_ICE = (140, 200, 255)
C_LIGHTNING = (255, 255, 100)
C_LAVA = (255, 80, 20)
C_GOTHIC_FRAME = (90, 75, 50)
C_GOTHIC_FRAME_LIGHT = (140, 120, 80)
C_GOTHIC_BG = (12, 10, 15)

BIOME_PORTAL_COLORS = {
    "crypt": (180, 160, 120), "cave": (160, 130, 80), "firepit": (255, 120, 40),
    "icecavern": (100, 180, 255), "swamp": (80, 200, 60),
}

# ============ D2 ITEM RARITY SYSTEM ============
RARITY_NORMAL = "normal"
RARITY_MAGIC = "magic"
RARITY_RARE = "rare"
RARITY_UNIQUE = "unique"
RARITY_SET = "set"
RARITY_COLORS = {
    RARITY_NORMAL: (180, 180, 180),    # white/gray
    RARITY_MAGIC: (100, 100, 255),     # blue
    RARITY_RARE: (255, 255, 100),      # yellow
    RARITY_UNIQUE: (255, 190, 50),     # bright gold
    RARITY_SET: (0, 220, 0),           # green
}
RARITY_NAMES = {
    RARITY_NORMAL: "Normal", RARITY_MAGIC: "Magic", RARITY_RARE: "Rare",
    RARITY_UNIQUE: "Unique", RARITY_SET: "Set",
}
RARITY_DROP_WEIGHTS = {
    RARITY_NORMAL: 50, RARITY_MAGIC: 30, RARITY_RARE: 14,
    RARITY_UNIQUE: 4, RARITY_SET: 2,
}

# ============ D2 CHARACTER STATS ============
STAT_POINTS_PER_LEVEL = 5
SKILL_POINTS_PER_LEVEL = 1
BASE_STATS = {"strength": 10, "dexterity": 15, "vitality": 12, "energy": 8}
# What each stat point gives:
# Strength: +1% melee/bow dmg per pt, +2 carry capacity
# Dexterity: +1% attack speed, +0.5% crit chance, +1% arrow speed
# Vitality: +3 max HP, +0.5 HP regen/sec
# Energy: +4 max Mana, +0.3 mana regen/sec, +1% skill dmg

# ============ D2 BOW & CROSSBOW DATABASE ============
# Base weapon types: (name, base_dmg_min, base_dmg_max, base_speed, weapon_class)
# weapon_class: "bow" or "crossbow"
# crossbows are slower but hit harder, bows are faster
BOW_BASES = [
    # --- Bows (faster, less damage) ---
    ("Short Bow",       3,  7,  2.8, "bow",      1),   # ilvl 1+
    ("Hunter's Bow",    5, 11,  2.6, "bow",      3),
    ("Long Bow",        7, 15,  2.4, "bow",      6),
    ("Composite Bow",  10, 19,  2.3, "bow",      9),
    ("War Bow",        12, 24,  2.2, "bow",     12),
    ("Gothic Bow",     15, 30,  2.1, "bow",     16),
    ("Rune Bow",       20, 38,  2.0, "bow",     20),
    ("Hydra Bow",      25, 50,  1.9, "bow",     25),
    # --- Crossbows (slower, more damage) ---
    ("Light Crossbow",  6, 12,  3.2, "crossbow",  1),
    ("Crossbow",       10, 20,  3.0, "crossbow",  5),
    ("Heavy Crossbow", 14, 28,  3.4, "crossbow",  8),
    ("Repeating Xbow", 12, 22,  2.4, "crossbow", 12),
    ("Siege Crossbow", 20, 40,  3.6, "crossbow", 16),
    ("Ballista",       28, 55,  3.8, "crossbow", 22),
    ("Demon Xbow",     32, 60,  3.0, "crossbow", 26),
]

# Affixes for magic/rare items
PREFIXES = [
    ("Fine",      {"dmg_min": (1, 3), "dmg_max": (2, 5)}),
    ("Sharp",     {"dmg_max": (3, 8)}),
    ("Deadly",    {"crit_chance": (3, 8)}),
    ("Swift",     {"attack_speed": (-0.2, -0.4)}),  # negative = faster
    ("Sturdy",    {"bonus_hp": (10, 30)}),
    ("Arcane",    {"bonus_mana": (8, 20)}),
    ("Vampiric",  {"life_steal": (2, 6)}),
    ("Frozen",    {"ice_dmg": (3, 10)}),
    ("Blazing",   {"fire_dmg": (4, 12)}),
    ("Shocking",  {"lightning_dmg": (3, 14)}),
    ("Cruel",     {"dmg_min": (3, 6), "dmg_max": (5, 12)}),
    ("Massive",   {"knockback": (20, 50)}),
]
SUFFIXES = [
    ("of Precision",  {"dexterity": (1, 4)}),
    ("of Might",      {"strength": (1, 4)}),
    ("of the Leech",  {"life_steal": (1, 4)}),
    ("of Speed",      {"attack_speed": (-0.1, -0.3)}),
    ("of the Titan",  {"bonus_hp": (8, 25)}),
    ("of Wizardry",   {"bonus_mana": (6, 15), "energy": (1, 3)}),
    ("of Piercing",   {"pierce": (1, 2)}),
    ("of Multishot",  {"extra_arrows": (1, 2)}),
    ("of Flame",      {"fire_dmg": (2, 8)}),
    ("of Frost",      {"ice_dmg": (2, 8)}),
    ("of Thunder",    {"lightning_dmg": (2, 10)}),
    ("of the Fox",    {"vitality": (1, 3)}),
]

# Unique weapons (hand-crafted)
UNIQUE_WEAPONS = [
    {"base": "Long Bow",      "name": "Witherstring",     "rarity": RARITY_UNIQUE,
     "fixed_mods": {"dmg_min": 15, "dmg_max": 28, "ice_dmg": 22, "life_steal": 8,
                    "bonus_hp": 40, "crit_chance": 6, "dexterity": 4}},
    {"base": "War Bow",       "name": "Eaglehorn",        "rarity": RARITY_UNIQUE,
     "fixed_mods": {"dmg_min": 20, "dmg_max": 40, "crit_chance": 18, "dexterity": 10,
                    "pierce": 3, "attack_speed": -0.5, "strength": 5}},
    {"base": "Hydra Bow",     "name": "Windforce",        "rarity": RARITY_UNIQUE,
     "fixed_mods": {"dmg_min": 30, "dmg_max": 55, "knockback": 60, "attack_speed": -0.7,
                    "strength": 10, "life_steal": 6, "bonus_hp": 30, "crit_chance": 8}},
    {"base": "Rune Bow",      "name": "Lycander's Aim",   "rarity": RARITY_UNIQUE,
     "fixed_mods": {"dmg_min": 22, "dmg_max": 38, "dexterity": 12, "vitality": 8,
                    "bonus_mana": 40, "bonus_hp": 30, "crit_chance": 7}},
    {"base": "Heavy Crossbow","name": "Hellrack",         "rarity": RARITY_UNIQUE,
     "fixed_mods": {"dmg_min": 25, "dmg_max": 48, "fire_dmg": 30, "lightning_dmg": 25,
                    "pierce": 2, "crit_chance": 10, "strength": 6}},
    {"base": "Ballista",      "name": "Buriza-Do Kyanon", "rarity": RARITY_UNIQUE,
     "fixed_mods": {"dmg_min": 35, "dmg_max": 65, "ice_dmg": 40, "pierce": 5,
                    "attack_speed": -0.5, "dexterity": 8, "crit_chance": 12, "bonus_hp": 25}},
    {"base": "Demon Xbow",    "name": "Gut Siphon",       "rarity": RARITY_UNIQUE,
     "fixed_mods": {"dmg_min": 38, "dmg_max": 58, "life_steal": 15, "crit_chance": 14,
                    "bonus_hp": 60, "strength": 8, "vitality": 6}},
    {"base": "Gothic Bow",    "name": "Goldstrike Arch",  "rarity": RARITY_UNIQUE,
     "fixed_mods": {"dmg_min": 20, "dmg_max": 35, "fire_dmg": 25, "lightning_dmg": 20,
                    "extra_arrows": 2, "crit_chance": 10, "dexterity": 6}},
]

# Set weapons (2 items form partial set)
SET_WEAPONS = [
    {"base": "Composite Bow", "name": "Vidala's Barb",    "rarity": RARITY_SET, "set_name": "Vidala's Rig",
     "fixed_mods": {"dmg_min": 6, "dmg_max": 10, "dexterity": 3, "lightning_dmg": 6}},
    {"base": "Repeating Xbow","name": "Iratha's Coil",    "rarity": RARITY_SET, "set_name": "Iratha's Finery",
     "fixed_mods": {"dmg_min": 8, "dmg_max": 12, "fire_dmg": 5, "ice_dmg": 5, "attack_speed": -0.2}},
    {"base": "Gothic Bow",    "name": "M'avina's Caster", "rarity": RARITY_SET, "set_name": "M'avina's Arsenal",
     "fixed_mods": {"dmg_min": 10, "dmg_max": 18, "crit_chance": 8, "extra_arrows": 1, "dexterity": 4}},
]

# ============ SKILL TREE ============
# Three trees: Bow Skills, Crossbow Skills, Passive Skills
SKILL_TREES = {
    "bow": {
        "name": "Bow Mastery",
        "skills": [
            {"id": "rapid_fire",    "name": "Rapid Fire",     "row": 0, "col": 0, "max": 5,
             "desc": "+8% bow attack speed per level", "req": None},
            {"id": "power_shot",    "name": "Power Shot",     "row": 0, "col": 2, "max": 5,
             "desc": "+15% single arrow damage per level", "req": None},
            {"id": "multishot_up",  "name": "Arrow Spray",    "row": 1, "col": 1, "max": 5,
             "desc": "+1 arrow per 2 levels in multishot", "req": "rapid_fire"},
            {"id": "guided_arrow",  "name": "Guided Arrow",   "row": 2, "col": 0, "max": 5,
             "desc": "+5% arrow homing strength per level", "req": "power_shot"},
            {"id": "rain_of_arrows","name": "Rain of Arrows", "row": 2, "col": 2, "max": 5,
             "desc": "RMB shoots upward, arrows rain in area", "req": "multishot_up"},
            {"id": "strafe",        "name": "Strafe",         "row": 3, "col": 1, "max": 5,
             "desc": "Hold LMB to auto-target nearby enemies", "req": "guided_arrow"},
        ]
    },
    "crossbow": {
        "name": "Crossbow Mastery",
        "skills": [
            {"id": "bolt_mastery",  "name": "Bolt Mastery",   "row": 0, "col": 0, "max": 5,
             "desc": "+10% crossbow damage per level", "req": None},
            {"id": "explosive_bolt","name": "Explosive Bolt", "row": 0, "col": 2, "max": 5,
             "desc": "Bolts explode on hit for AoE dmg", "req": None},
            {"id": "piercing_bolt", "name": "Piercing Bolt",  "row": 1, "col": 1, "max": 5,
             "desc": "+1 pierce per 2 levels", "req": "bolt_mastery"},
            {"id": "siege_mode",    "name": "Siege Mode",     "row": 2, "col": 0, "max": 5,
             "desc": "Stand still for +30% dmg per level", "req": "explosive_bolt"},
            {"id": "volley",        "name": "Volley",         "row": 2, "col": 2, "max": 5,
             "desc": "RMB fires 3 heavy bolts in a line", "req": "piercing_bolt"},
            {"id": "immolation",    "name": "Immolation Bolt","row": 3, "col": 1, "max": 5,
             "desc": "Bolts leave fire trail, +fire dmg", "req": "siege_mode"},
        ]
    },
    "passive": {
        "name": "Passive & Magic",
        "skills": [
            {"id": "critical_eye",  "name": "Critical Eye",   "row": 0, "col": 0, "max": 5,
             "desc": "+3% critical hit chance per level", "req": None},
            {"id": "dodge",         "name": "Dodge",           "row": 0, "col": 2, "max": 5,
             "desc": "+4% chance to avoid damage per level", "req": None},
            {"id": "inner_sight",   "name": "Inner Sight",    "row": 1, "col": 1, "max": 5,
             "desc": "+10% light radius, enemies glow", "req": "critical_eye"},
            {"id": "life_leech",    "name": "Blood Arrows",   "row": 2, "col": 0, "max": 5,
             "desc": "+2% life steal per level", "req": "dodge"},
            {"id": "mana_regen",    "name": "Meditation",     "row": 2, "col": 2, "max": 5,
             "desc": "+15% mana regen per level", "req": "inner_sight"},
            {"id": "penetrate",     "name": "Penetrate",      "row": 3, "col": 1, "max": 5,
             "desc": "+10% damage to elites/bosses per level", "req": "life_leech"},
        ]
    }
}

# Inventory grid size
INV_COLS = 10
INV_ROWS = 4

# Vendor NPC
VENDOR_STOCK_SIZE = 8  # weapons for sale
VENDOR_INTERACT_RANGE = 80  # pixels to interact
VENDOR_RESTOCK_ON_LEVEL = True

Vec = pygame.math.Vector2

# ======================= DATA CLASSES =======================
@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    r: int
    g: int
    b: int
    life: float
    max_life: float
    size: float
    gravity: float = 0.0

@dataclass
class FloatingText:
    x: float
    y: float
    text: str
    r: int
    g: int
    b: int
    life: float = 1.2
    max_life: float = 1.2
    vy: float = -50.0
    scale: float = 1.0

@dataclass
class Corpse:
    x: float
    y: float
    radius: int
    kind: int
    color: Tuple[int, int, int]
    life: float = 4.0
    is_boss: bool = False
    is_elite: bool = False

@dataclass
class Weapon:
    name: str
    dmg_min: int
    dmg_max: int
    attack_speed: float
    ranged: bool
    rarity: str = RARITY_NORMAL
    weapon_class: str = "bow"  # "bow" or "crossbow"
    # Affix bonuses (accumulated from prefixes/suffixes)
    mods: dict = field(default_factory=dict)
    # Display info
    base_name: str = ""
    prefix: str = ""
    suffix: str = ""
    set_name: str = ""
    ilvl: int = 1  # item level
    def roll_damage(self) -> int:
        base = random.randint(self.dmg_min, self.dmg_max)
        base += self.mods.get("fire_dmg", 0) + self.mods.get("ice_dmg", 0) + self.mods.get("lightning_dmg", 0)
        return base
    def get_color(self) -> Tuple[int, int, int]:
        return RARITY_COLORS.get(self.rarity, (180, 180, 180))
    def get_tooltip_lines(self) -> List[str]:
        lines = [self.name]
        lines.append(f"{self.base_name or self.name}  ({self.weapon_class.title()})")
        lines.append(f"Damage: {self.dmg_min}-{self.dmg_max}")
        lines.append(f"Speed: {self.attack_speed:.1f}")
        for k, v in self.mods.items():
            if v and k not in ("dmg_min", "dmg_max", "attack_speed"):
                label = k.replace("_", " ").title()
                if isinstance(v, float):
                    lines.append(f"  +{v:.1f} {label}")
                else:
                    lines.append(f"  +{v} {label}")
        return lines

@dataclass
class Loot:
    pos: Vec
    gold: int = 0
    potion_hp: bool = False
    potion_mana: bool = False
    weapon: Optional[Weapon] = None
    dmg_boost: bool = False
    shield_boost: bool = False
    infusion: Optional[str] = None  # "fire", "ice", "lightning"
    ttl: float = 30.0
    bob_phase: float = 0.0

@dataclass
class Projectile:
    pos: Vec
    vel: Vec
    dmg: int
    ttl: float
    radius: int
    pierce: int = 1
    hostile: bool = False
    trail_timer: float = 0.0
    is_arrow: bool = False
    angle: float = 0.0
    infusion: Optional[str] = None  # "fire", "ice", "lightning"

@dataclass
class Entity:
    pos: Vec
    vel: Vec
    radius: int

@dataclass
class Player(Entity):
    hp: int = PLAYER_HP
    mana: int = PLAYER_MANA
    level: int = 1
    xp: int = 0
    xp_to_next: int = 40
    gold: int = 0
    potions_hp: int = 1
    potions_mana: int = 1
    basic_cd: float = 0.0
    power_cd: float = 0.0
    weapon: Weapon = field(default_factory=lambda: Weapon("Wooden Bow", 6, 10, 2.5, True,
                                                           weapon_class="bow", base_name="Short Bow"))
    dmg_mult: float = 1.0
    dmg_timer: float = 0.0
    shield: int = 0
    dash_cd: float = 0.0
    dash_timer: float = 0.0
    iframes: float = 0.0
    walk_anim: float = 0.0
    levelup_flash: float = 0.0
    infusion_type: Optional[str] = None
    infusion_timer: float = 0.0
    # Character stats (D2 style)
    strength: int = BASE_STATS["strength"]
    dexterity: int = BASE_STATS["dexterity"]
    vitality: int = BASE_STATS["vitality"]
    energy: int = BASE_STATS["energy"]
    stat_points: int = 0  # unspent stat points
    skill_points: int = 0  # unspent skill points
    skills: dict = field(default_factory=dict)  # skill_id -> level
    crit_chance: float = 5.0  # base 5% crit
    # Inventory: list of Weapon items
    inventory: list = field(default_factory=list)  # List[Weapon], max INV_COLS*INV_ROWS
    # Lives / respawn
    lives: int = 3
    max_lives: int = 3

    def max_hp(self) -> int:
        base = PLAYER_HP + 10 * self.level + self.vitality * 3
        base += self.weapon.mods.get("bonus_hp", 0)
        return base

    def max_mana(self) -> int:
        base = PLAYER_MANA + 8 * self.level + self.energy * 4
        base += self.weapon.mods.get("bonus_mana", 0)
        return base

    def mana_regen(self) -> float:
        base = MANA_REGEN_RATE + self.energy * 0.3
        skill_bonus = 1.0 + 0.15 * self.skills.get("mana_regen", 0)
        return base * skill_bonus

    def calc_crit_chance(self) -> float:
        c = self.crit_chance + self.dexterity * 0.5
        c += self.weapon.mods.get("crit_chance", 0)
        c += self.skills.get("critical_eye", 0) * 3.0
        return min(c, 75.0)

    def calc_attack_speed_mult(self) -> float:
        m = 1.0 + self.dexterity * 0.01
        m += abs(self.weapon.mods.get("attack_speed", 0)) * 0.5
        if self.weapon.weapon_class == "bow":
            m += self.skills.get("rapid_fire", 0) * 0.08
        return m

    def calc_dmg_mult(self) -> float:
        m = self.dmg_mult + self.strength * 0.01
        m += self.energy * 0.01
        if self.weapon.weapon_class == "bow":
            m += self.skills.get("power_shot", 0) * 0.15
        elif self.weapon.weapon_class == "crossbow":
            m += self.skills.get("bolt_mastery", 0) * 0.10
        return m

    def calc_life_steal(self) -> float:
        ls = self.weapon.mods.get("life_steal", 0)
        ls += self.skills.get("life_leech", 0) * 2.0
        return ls

    def calc_dodge_chance(self) -> float:
        return self.skills.get("dodge", 0) * 4.0

    def calc_multishot_count(self) -> int:
        base = MULTISHOT_COUNT + self.weapon.mods.get("extra_arrows", 0)
        base += self.skills.get("multishot_up", 0) // 2
        return base

    def calc_pierce(self) -> int:
        base = BASIC_PIERCE + self.weapon.mods.get("pierce", 0)
        if self.weapon.weapon_class == "crossbow":
            base += self.skills.get("piercing_bolt", 0) // 2
        return base

@dataclass
class Enemy(Entity):
    hp: int = ENEMY_BASE_HP
    max_hp: int = ENEMY_BASE_HP
    dmg_min: int = ENEMY_BASE_DMG[0]
    dmg_max: int = ENEMY_BASE_DMG[1]
    speed: float = ENEMY_SPEED
    knockback: float = 0.0
    alive: bool = True
    kind: int = 0
    mult_speed: float = 1.0
    mult_damage: float = 1.0
    mult_taken: float = 1.0
    shot_cd: float = 0.0
    hit_flash: float = 0.0
    death_timer: float = -1.0
    def roll_damage(self) -> int:
        base = random.randint(self.dmg_min, self.dmg_max)
        return int(base * self.mult_damage)

@dataclass
class Elite(Enemy):
    aura: str = "haste"
    aura_radius: int = AURA_RADIUS
    aura_pulse: float = 0.0

@dataclass
class Boss(Enemy):
    shot_cd: float = 1.0

@dataclass
class TreasureGoblin(Enemy):
    flee_timer: float = 0.0
    loot_drop_timer: float = 0.0
    portal_timer: float = GOBLIN_DESPAWN_TIME

@dataclass
class Chest:
    pos: Vec
    hp: int = CHEST_HP
    alive: bool = True
    kind: str = "wood"  # wood, gold
    hit_flash: float = 0.0

@dataclass
class Crate:
    pos: Vec
    hp: int = CRATE_HP
    alive: bool = True
    hit_flash: float = 0.0

@dataclass
class Vendor:
    pos: Vec
    stock: list = field(default_factory=list)  # List[Weapon]
    name: str = "Gheed"
    interact_anim: float = 0.0

# ======================= DUNGEON =======================
class Dungeon:
    def __init__(self, level: int = 1, biome: str = "crypt"):
        self.level = level
        self.biome = biome
        self.tiles = [[WALL for _ in range(MAP_H)] for _ in range(MAP_W)]
        self.seen = [[False for _ in range(MAP_H)] for _ in range(MAP_W)]
        self.rooms: List[pygame.Rect] = []
        self.scenery: List[Tuple[int, int, str]] = []
        self.torches: List[Tuple[int, int]] = []
        self.blood_stains: List[Tuple[float, float, float]] = []
        self.portal_positions: List[Tuple[int, int, str]] = []  # (tx, ty, dest_biome)
        self.chest_positions: List[Tuple[int, int]] = []
        self.crate_positions: List[Tuple[int, int]] = []  # breakable crates
        self.hazard_pools: List[Tuple[int, int]] = []  # lava, poison, ice based on biome
        self.tile_variants = [[random.randint(0, 7) for _ in range(MAP_H)] for _ in range(MAP_W)]
        self.generate()

    def generate(self):
        rng = random.Random()
        max_rooms = 50 + self.level * 10
        min_size, max_size = 6, 15
        for _ in range(max_rooms):
            w = rng.randint(min_size, max_size)
            h = rng.randint(min_size, max_size)
            x = rng.randint(2, MAP_W - w - 3)
            y = rng.randint(2, MAP_H - h - 3)
            new = pygame.Rect(x, y, w, h)
            if any(new.colliderect(r.inflate(2, 2)) for r in self.rooms):
                continue
            self.carve_room(new)
            if self.rooms:
                px, py = self.center(self.rooms[-1])
                nx, ny = self.center(new)
                self.carve_tunnel(px, py, nx, ny)
            self.rooms.append(new)
            for _ in range(rng.randint(0, 2)):
                tx = rng.randint(new.left + 1, new.right - 2)
                ty = rng.randint(new.top + 1, new.bottom - 2)
                self.tiles[tx][ty] = WALL
                if self.biome == "cave":
                    stype = 'stalagmite' if rng.random() < 0.7 else 'rock'
                elif self.biome == "icecavern":
                    stype = 'ice_crystal' if rng.random() < 0.6 else 'pillar'
                elif self.biome == "swamp":
                    stype = 'mushroom' if rng.random() < 0.5 else 'crate'
                elif self.biome == "firepit":
                    stype = 'pillar' if rng.random() < 0.7 else 'crate'
                else:
                    stype = 'pillar' if rng.random() < 0.6 else 'crate'
                self.scenery.append((tx, ty, stype))
                if stype == 'crate':
                    self.crate_positions.append((tx, ty))
            self._place_torches(new, rng)
        # Place treasure chests in rooms
        for room in self.rooms[1:]:  # skip first room (player spawn)
            if rng.random() < CHEST_SPAWN_PER_ROOM:
                for _ in range(20):
                    tx = rng.randint(room.left + 1, room.right - 2)
                    ty = rng.randint(room.top + 1, room.bottom - 2)
                    if self.tiles[tx][ty] == FLOOR:
                        too_close = any(abs(cx - tx) + abs(cy - ty) < 3 for cx, cy in self.chest_positions)
                        if not too_close:
                            chest_kind = "gold" if rng.random() < 0.15 else "wood"
                            self.chest_positions.append((tx, ty))
                            break
            # Rare: extra gold chest in large rooms
            if room.w >= 10 and room.h >= 10 and rng.random() < 0.25:
                for _ in range(20):
                    tx = rng.randint(room.left + 2, room.right - 3)
                    ty = rng.randint(room.top + 2, room.bottom - 3)
                    if self.tiles[tx][ty] == FLOOR:
                        too_close = any(abs(cx - tx) + abs(cy - ty) < 3 for cx, cy in self.chest_positions)
                        if not too_close:
                            self.chest_positions.append((tx, ty))
                            break
        # Place additional breakable crates in rooms (on floor, not walls)
        for room in self.rooms[1:]:
            num_crates = rng.randint(0, 3)
            for _ in range(num_crates):
                for _ in range(15):
                    tx = rng.randint(room.left + 1, room.right - 2)
                    ty = rng.randint(room.top + 1, room.bottom - 2)
                    if self.tiles[tx][ty] == FLOOR:
                        too_close = (any(abs(cx - tx) + abs(cy - ty) < 2 for cx, cy in self.crate_positions)
                                     or any(abs(cx - tx) + abs(cy - ty) < 2 for cx, cy in self.chest_positions))
                        if not too_close:
                            self.crate_positions.append((tx, ty))
                            break

        # Place hazard pools based on biome
        hazard_chance = 0.20 if self.biome in ("swamp", "firepit") else 0.12
        for room in self.rooms[2:]:
            if rng.random() < hazard_chance:
                cx = rng.randint(room.left + 2, max(room.left + 2, room.right - 3))
                cy = rng.randint(room.top + 2, max(room.top + 2, room.bottom - 3))
                if self.tiles[cx][cy] == FLOOR:
                    self.hazard_pools.append((cx, cy))

        for x in range(MAP_W):
            self.tiles[x][0] = WALL
            self.tiles[x][MAP_H - 1] = WALL
        for y in range(MAP_H):
            self.tiles[0][y] = WALL
            self.tiles[MAP_W - 1][y] = WALL

        # Place biome portals in later rooms
        if len(self.rooms) >= 3:
            available_biomes = [b for b in BIOMES if b != self.biome]
            portal_rooms = list(self.rooms[len(self.rooms) // 2:])
            rng.shuffle(portal_rooms)
            for i in range(min(PORTALS_PER_LEVEL, len(portal_rooms), len(available_biomes))):
                room = portal_rooms[i]
                px, py = self.center(room)
                dest = available_biomes[i]
                self.portal_positions.append((px, py, dest))
                self.tiles[px][py] = FLOOR

    def _place_torches(self, room: pygame.Rect, rng):
        walls = []
        for x in range(room.left, room.right):
            if room.top - 1 >= 0 and self.tiles[x][room.top - 1] == WALL:
                walls.append((x, room.top))
            if room.bottom < MAP_H and self.tiles[x][room.bottom] == WALL:
                walls.append((x, room.bottom - 1))
        for y in range(room.top, room.bottom):
            if room.left - 1 >= 0 and self.tiles[room.left - 1][y] == WALL:
                walls.append((room.left, y))
            if room.right < MAP_W and self.tiles[room.right][y] == WALL:
                walls.append((room.right - 1, y))
        rng.shuffle(walls)
        count = max(1, len(walls) // 6)
        for i in range(min(count, len(walls))):
            tx, ty = walls[i]
            too_close = False
            for etx, ety in self.torches:
                if abs(etx - tx) + abs(ety - ty) < 4:
                    too_close = True
                    break
            if not too_close:
                self.torches.append((tx, ty))

    def carve_room(self, rect: pygame.Rect):
        for x in range(rect.left, rect.right):
            for y in range(rect.top, rect.bottom):
                self.tiles[x][y] = FLOOR

    def carve_tunnel(self, x1, y1, x2, y2):
        if random.random() < 0.5:
            self.carve_h_tunnel(x1, x2, y1)
            self.carve_v_tunnel(y1, y2, x2)
        else:
            self.carve_v_tunnel(y1, y2, x1)
            self.carve_h_tunnel(x1, x2, y2)

    def carve_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for dy in (-1, 0, 1):
                if 0 <= y + dy < MAP_H:
                    self.tiles[x][y + dy] = FLOOR

    def carve_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for dx in (-1, 0, 1):
                if 0 <= x + dx < MAP_W:
                    self.tiles[x + dx][y] = FLOOR

    def center(self, rect: pygame.Rect):
        return rect.left + rect.w // 2, rect.top + rect.h // 2

    def is_solid_at_px(self, pos: Vec) -> bool:
        tx = int(pos.x // TILE)
        ty = int(pos.y // TILE)
        if tx < 0 or ty < 0 or tx >= MAP_W or ty >= MAP_H:
            return True
        return self.tiles[tx][ty] == WALL

    def mark_seen_radius(self, pos: Vec, radius_px: int = 320):
        r2 = radius_px * radius_px
        min_tx = max(0, int((pos.x - radius_px) // TILE))
        max_tx = min(MAP_W - 1, int((pos.x + radius_px) // TILE))
        min_ty = max(0, int((pos.y - radius_px) // TILE))
        max_ty = min(MAP_H - 1, int((pos.y + radius_px) // TILE))
        for tx in range(min_tx, max_tx + 1):
            for ty in range(min_ty, max_ty + 1):
                cx = tx * TILE + TILE / 2
                cy = ty * TILE + TILE / 2
                if (cx - pos.x) ** 2 + (cy - pos.y) ** 2 <= r2:
                    self.seen[tx][ty] = True

# ======================= WEAPON GENERATOR =======================
def _pick_rarity(depth: int = 1) -> str:
    """Pick item rarity with depth-scaled chances (higher depth = better drops)."""
    weights = dict(RARITY_DROP_WEIGHTS)
    # Slightly increase rare/unique/set at higher depths
    bonus = min(depth * 0.5, 15)
    weights[RARITY_MAGIC] += bonus * 0.6
    weights[RARITY_RARE] += bonus * 0.4
    weights[RARITY_UNIQUE] += bonus * 0.15
    weights[RARITY_SET] += bonus * 0.1
    total = sum(weights.values())
    roll = random.random() * total
    cumulative = 0
    for rarity, w in weights.items():
        cumulative += w
        if roll <= cumulative:
            return rarity
    return RARITY_NORMAL

def _get_base_for_depth(depth: int) -> Tuple:
    """Pick an appropriate base weapon for the current dungeon depth."""
    eligible = [b for b in BOW_BASES if b[5] <= depth + 3]
    if not eligible:
        eligible = BOW_BASES[:2]
    # Weight toward higher-level bases
    weights = [1.0 + max(0, depth - b[5]) * 0.5 for b in eligible]
    return random.choices(eligible, weights=weights, k=1)[0]

def generate_weapon(depth: int = 1, force_rarity: Optional[str] = None) -> Weapon:
    """Generate a random weapon with D2-style rarity and affixes."""
    rarity = force_rarity or _pick_rarity(depth)
    base = _get_base_for_depth(depth)
    bname, bdmin, bdmax, bspd, bclass, bilvl = base

    # Scale base damage slightly with depth
    scale = 1.0 + max(0, depth - bilvl) * 0.06
    dmg_min = int(bdmin * scale)
    dmg_max = int(bdmax * scale)
    speed = bspd
    mods = {}
    prefix_name = ""
    suffix_name = ""
    display_name = bname
    set_name_str = ""

    if rarity == RARITY_UNIQUE:
        # Pick a matching unique if possible
        eligible_uniques = [u for u in UNIQUE_WEAPONS if u["base"] == bname]
        if not eligible_uniques:
            eligible_uniques = UNIQUE_WEAPONS
        u = random.choice(eligible_uniques)
        display_name = u["name"]
        bname = u["base"]
        mods = dict(u["fixed_mods"])
        dmg_min += mods.pop("dmg_min", 0)
        dmg_max += mods.pop("dmg_max", 0)
        speed += mods.pop("attack_speed", 0)

    elif rarity == RARITY_SET:
        eligible_sets = [s for s in SET_WEAPONS if s["base"] == bname]
        if not eligible_sets:
            eligible_sets = SET_WEAPONS
        sw = random.choice(eligible_sets)
        display_name = sw["name"]
        bname = sw["base"]
        set_name_str = sw.get("set_name", "")
        mods = dict(sw["fixed_mods"])
        dmg_min += mods.pop("dmg_min", 0)
        dmg_max += mods.pop("dmg_max", 0)
        speed += mods.pop("attack_speed", 0)

    elif rarity == RARITY_RARE:
        # 2 prefixes + 1 suffix (or 1+2)
        num_pre = random.choice([1, 2])
        num_suf = 3 - num_pre
        chosen_pre = random.sample(PREFIXES, min(num_pre, len(PREFIXES)))
        chosen_suf = random.sample(SUFFIXES, min(num_suf, len(SUFFIXES)))
        # Build rare name: random fantasy name
        rare_names = ["Doom", "Storm", "Shadow", "Blood", "Soul", "Bone", "Wrath",
                      "Raven", "Wolf", "Viper", "Drake", "Grim", "Death", "Iron"]
        rare_suffixes = ["bane", "mark", "song", "fury", "strike", "gaze", "fang",
                         "claw", "horn", "bite", "wind", "fire", "bringer", "slayer"]
        display_name = random.choice(rare_names) + random.choice(rare_suffixes)
        for pname, pmod in chosen_pre:
            for mk, (lo, hi) in pmod.items():
                val = random.uniform(lo, hi) if isinstance(lo, float) else random.randint(lo, hi)
                mods[mk] = mods.get(mk, 0) + val
        for sname, smod in chosen_suf:
            for mk, (lo, hi) in smod.items():
                val = random.uniform(lo, hi) if isinstance(lo, float) else random.randint(lo, hi)
                mods[mk] = mods.get(mk, 0) + val
        dmg_min += int(mods.pop("dmg_min", 0))
        dmg_max += int(mods.pop("dmg_max", 0))
        speed += mods.pop("attack_speed", 0)

    elif rarity == RARITY_MAGIC:
        # 1 prefix and/or 1 suffix
        has_pre = random.random() < 0.7
        has_suf = random.random() < 0.7 if has_pre else True
        if not has_pre and not has_suf:
            has_pre = True
        if has_pre:
            pname, pmod = random.choice(PREFIXES)
            prefix_name = pname
            for mk, (lo, hi) in pmod.items():
                val = random.uniform(lo, hi) if isinstance(lo, float) else random.randint(lo, hi)
                mods[mk] = mods.get(mk, 0) + val
        if has_suf:
            sname, smod = random.choice(SUFFIXES)
            suffix_name = sname
            for mk, (lo, hi) in smod.items():
                val = random.uniform(lo, hi) if isinstance(lo, float) else random.randint(lo, hi)
                mods[mk] = mods.get(mk, 0) + val
        dmg_min += int(mods.pop("dmg_min", 0))
        dmg_max += int(mods.pop("dmg_max", 0))
        speed += mods.pop("attack_speed", 0)
        display_name = f"{prefix_name} {bname} {suffix_name}".strip()

    # Clamp values
    speed = max(0.5, speed)
    dmg_min = max(1, dmg_min)
    dmg_max = max(dmg_min + 1, dmg_max)
    # Round float mods
    for k in list(mods.keys()):
        if isinstance(mods[k], float):
            mods[k] = round(mods[k], 1)

    return Weapon(
        name=display_name, dmg_min=dmg_min, dmg_max=dmg_max,
        attack_speed=round(speed, 2), ranged=True,
        rarity=rarity, weapon_class=bclass, mods=mods,
        base_name=bname, prefix=prefix_name, suffix=suffix_name,
        set_name=set_name_str, ilvl=depth
    )


# ======================= GAME =======================
class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        self._build_sounds()
        self.fullscreen = False
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Dungeon of the Damned — ARPG")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(FONT_NAME, 24)
        self.bigfont = pygame.font.SysFont(FONT_NAME, 36, bold=True)
        self.dmgfont = pygame.font.SysFont(FONT_NAME, 28, bold=True)
        self.titlefont = pygame.font.SysFont(FONT_NAME, 72, bold=True)
        self.subfont = pygame.font.SysFont(FONT_NAME, 28)

        # Check if save file exists for "Continue" option
        self._has_save = os.path.exists(self._get_save_path())
        menu_choice = self._title_menu()

        # Initialize all game state first (needed before _load_game)
        self.current_level = 1
        self.current_biome = "crypt"
        self.difficulty_name = "Normal"
        self.diff = DIFFICULTY["Normal"]
        global MAX_ACTIVE_ENEMIES
        self.dungeon = Dungeon(level=1, biome="crypt")
        rx, ry = self.dungeon.center(self.dungeon.rooms[0]) if self.dungeon.rooms else (MAP_W // 2, MAP_H // 2)
        self.player = Player(pos=Vec(rx * TILE + TILE / 2, ry * TILE + TILE / 2), vel=Vec(0, 0), radius=20)
        self.enemies: List[Enemy] = []
        self.projectiles: List[Projectile] = []
        self.loots: List[Loot] = []
        self.particles: List[Particle] = []
        self.floating_texts: List[FloatingText] = []
        self.corpses: List[Corpse] = []
        self.spawn_timer = SPAWN_INTERVAL
        self.wave = 1
        self.running = True
        self.paused = False
        self.cam_x = 0
        self.cam_y = 0
        self.shake_x = 0.0
        self.shake_y = 0.0
        self.shake_intensity = 0.0
        self.game_time = 0.0
        self.boss_spawned = False
        self.kills = 0
        self.treasure_goblin: Optional[TreasureGoblin] = None
        self.lightning_chains: List[Tuple[Vec, Vec, float]] = []  # (start, end, life)
        self.portal_angle = 0.0
        self.chests: List[Chest] = []
        self.crates: List[Crate] = []
        self.vendor: Optional[Vendor] = None
        self.show_vendor_hint = False

        if menu_choice == "continue":
            # Load saved game
            if not self._load_game():
                # Failed to load, start fresh
                self.difficulty_name = self._difficulty_select()
                self.diff = DIFFICULTY[self.difficulty_name]
                MAX_ACTIVE_ENEMIES = self.diff["max_enemies"]
                self.dungeon = Dungeon(level=1, biome="crypt")
                rx, ry = self.dungeon.center(self.dungeon.rooms[0]) if self.dungeon.rooms else (MAP_W // 2, MAP_H // 2)
                self.player.pos = Vec(rx * TILE + TILE / 2, ry * TILE + TILE / 2)
                self._spawn_chests()
                self._spawn_crates()
                self._spawn_vendor()
            MAX_ACTIVE_ENEMIES = self.diff["max_enemies"]
        else:
            self.difficulty_name = menu_choice
            self.diff = DIFFICULTY[self.difficulty_name]
            MAX_ACTIVE_ENEMIES = self.diff["max_enemies"]
            self._spawn_chests()
            self._spawn_crates()
            self._spawn_vendor()

        self.dungeon.mark_seen_radius(self.player.pos)
        self._build_texture_cache(self.current_biome)
        self._build_light_surfaces()
        self.light_map = pygame.Surface((WIDTH, HEIGHT))

    # ---- Texture generation ----
    def _build_texture_cache(self, biome: str = "crypt"):
        bc = BIOME_COLORS.get(biome, BIOME_COLORS["crypt"])
        wt = bc["wall_tint"]
        ft = bc["floor_tint"]
        wb = bc["wall_base"]

        self.wall_tiles = []
        for i in range(8):
            surf = pygame.Surface((TILE, TILE))
            base = wb + (i * 3) % 16
            surf.fill((max(0, min(255, base + wt[0])),
                        max(0, min(255, base - 2 + wt[1])),
                        max(0, min(255, base + 8 + wt[2]))))
            mortar = (max(0, base - 18 + wt[0]), max(0, base - 20 + wt[1]), max(0, base - 12 + wt[2]))
            for row in range(3):
                y = row * (TILE // 3)
                pygame.draw.line(surf, mortar, (0, y), (TILE, y))
                offset = (TILE // 2) * (row % 2)
                for bx in range(offset, TILE + TILE // 2, TILE // 2):
                    if 0 <= bx < TILE:
                        pygame.draw.line(surf, mortar, (bx, y), (bx, y + TILE // 3))
            hl = (min(255, base + 12 + wt[0]), min(255, base + 10 + wt[1]), min(255, base + 18 + wt[2]))
            pygame.draw.line(surf, hl, (0, 0), (TILE - 1, 0))
            for _ in range(6):
                nx, ny = random.randint(0, TILE - 1), random.randint(0, TILE - 1)
                c = random.randint(max(0, base - 12), min(255, base + 8))
                surf.set_at((nx, ny), (max(0, min(255, c + wt[0])),
                                        max(0, min(255, c - 2 + wt[1])),
                                        max(0, min(255, c + 4 + wt[2]))))
            self.wall_tiles.append(surf)

        self.floor_tiles = []
        for i in range(8):
            surf = pygame.Surface((TILE, TILE))
            br = bc["floor_r"] + (i * 2) % 10
            bg = bc["floor_g"] + (i * 3) % 8
            bb = bc["floor_b"] + (i * 2) % 12
            surf.fill((br, bg, bb))
            jc = (max(0, br - 6), max(0, bg - 6), max(0, bb - 4))
            if i % 3 == 0:
                pygame.draw.line(surf, jc, (0, TILE // 2), (TILE, TILE // 2))
            if i % 3 == 1:
                pygame.draw.line(surf, jc, (TILE // 2, 0), (TILE // 2, TILE))
            if i % 4 == 0:
                cx = random.randint(4, TILE - 4)
                cy = random.randint(4, TILE - 4)
                pygame.draw.line(surf, (br - 10, bg - 10, bb - 8),
                                 (cx, cy), (cx + random.randint(-8, 8), cy + random.randint(-8, 8)))
            # noise
            for _ in range(4):
                nx, ny = random.randint(0, TILE - 1), random.randint(0, TILE - 1)
                v = random.randint(-4, 4)
                surf.set_at((nx, ny), (max(0, br + v), max(0, bg + v), max(0, bb + v)))
            self.floor_tiles.append(surf)

        self.unseen_wall = pygame.Surface((TILE, TILE))
        self.unseen_wall.fill((14, 12, 18))
        self.unseen_floor = pygame.Surface((TILE, TILE))
        self.unseen_floor.fill((8, 7, 10))

        # pillar texture
        self.pillar_surf = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        self.pillar_surf.fill((0, 0, 0, 0))
        pygame.draw.rect(self.pillar_surf, (65, 62, 80), (5, 3, TILE - 10, TILE - 6), border_radius=6)
        pygame.draw.rect(self.pillar_surf, (80, 78, 100), (6, 4, TILE - 12, 4), border_radius=2)
        pygame.draw.rect(self.pillar_surf, (50, 48, 65), (6, TILE - 8, TILE - 12, 4), border_radius=2)

        # crate texture
        self.crate_surf = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        self.crate_surf.fill((0, 0, 0, 0))
        pygame.draw.rect(self.crate_surf, (85, 65, 40), (4, 4, TILE - 8, TILE - 8))
        pygame.draw.rect(self.crate_surf, (100, 80, 50), (4, 4, TILE - 8, TILE - 8), 2)
        pygame.draw.line(self.crate_surf, (110, 90, 55), (4, 4), (TILE - 4, TILE - 4), 2)
        pygame.draw.line(self.crate_surf, (110, 90, 55), (TILE - 4, 4), (4, TILE - 4), 2)
        # metal bands
        pygame.draw.rect(self.crate_surf, (70, 65, 55), (3, TILE // 2 - 1, TILE - 6, 3))

        # treasure chest texture
        self.chest_surf = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        self.chest_surf.fill((0, 0, 0, 0))
        # chest body
        pygame.draw.rect(self.chest_surf, (120, 85, 45), (6, 14, TILE - 12, TILE - 20), border_radius=4)
        # lid (slightly wider)
        pygame.draw.rect(self.chest_surf, (140, 100, 55), (4, 8, TILE - 8, 14), border_radius=5)
        # metal bands
        pygame.draw.rect(self.chest_surf, (180, 170, 80), (4, 11, TILE - 8, 3))
        pygame.draw.rect(self.chest_surf, (180, 170, 80), (4, TILE - 11, TILE - 8, 3))
        # lock/clasp
        pygame.draw.circle(self.chest_surf, (220, 200, 80), (TILE // 2, 20), 6)
        pygame.draw.circle(self.chest_surf, (180, 160, 60), (TILE // 2, 20), 6, 1)
        # highlight
        pygame.draw.line(self.chest_surf, (170, 130, 75), (8, 10), (TILE - 9, 10))

        # gold chest texture
        self.gold_chest_surf = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        self.gold_chest_surf.fill((0, 0, 0, 0))
        pygame.draw.rect(self.gold_chest_surf, (180, 150, 50), (6, 14, TILE - 12, TILE - 20), border_radius=4)
        pygame.draw.rect(self.gold_chest_surf, (200, 170, 60), (4, 8, TILE - 8, 14), border_radius=5)
        pygame.draw.rect(self.gold_chest_surf, (255, 230, 100), (4, 11, TILE - 8, 3))
        pygame.draw.rect(self.gold_chest_surf, (255, 230, 100), (4, TILE - 11, TILE - 8, 3))
        pygame.draw.circle(self.gold_chest_surf, (255, 240, 120), (TILE // 2, 20), 7)
        pygame.draw.circle(self.gold_chest_surf, (200, 180, 60), (TILE // 2, 20), 7, 1)
        pygame.draw.line(self.gold_chest_surf, (220, 190, 80), (8, 10), (TILE - 9, 10))

        # Biome-specific scenery
        # Stalagmite
        self.stalagmite_surf = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        self.stalagmite_surf.fill((0, 0, 0, 0))
        pygame.draw.polygon(self.stalagmite_surf, (75, 65, 50),
                            [(TILE // 2, 2), (TILE // 2 - 12, TILE - 4), (TILE // 2 + 12, TILE - 4)])
        pygame.draw.polygon(self.stalagmite_surf, (60, 52, 40),
                            [(TILE // 2, 2), (TILE // 2 - 12, TILE - 4), (TILE // 2 + 12, TILE - 4)], 2)
        # Rock
        self.rock_surf = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        self.rock_surf.fill((0, 0, 0, 0))
        pygame.draw.ellipse(self.rock_surf, (68, 60, 48), (4, 8, TILE - 8, TILE - 12))
        pygame.draw.ellipse(self.rock_surf, (55, 48, 38), (4, 8, TILE - 8, TILE - 12), 2)
        # Ice crystal
        self.ice_crystal_surf = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        self.ice_crystal_surf.fill((0, 0, 0, 0))
        pts = [(TILE // 2, 0), (TILE - 4, TILE // 2), (TILE // 2, TILE - 2), (4, TILE // 2)]
        pygame.draw.polygon(self.ice_crystal_surf, (120, 180, 230, 180), pts)
        pygame.draw.polygon(self.ice_crystal_surf, (180, 220, 255, 220), pts, 2)
        # Mushroom
        self.mushroom_surf = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        self.mushroom_surf.fill((0, 0, 0, 0))
        pygame.draw.rect(self.mushroom_surf, (80, 70, 50), (TILE // 2 - 3, TILE // 2, 6, TILE // 2 - 2))
        pygame.draw.ellipse(self.mushroom_surf, (60, 120, 50), (4, 4, TILE - 8, TILE // 2))
        pygame.draw.ellipse(self.mushroom_surf, (80, 160, 60), (8, 8, TILE - 16, TILE // 2 - 8))

        # torch texture
        self.torch_surf = pygame.Surface((17, 22), pygame.SRCALPHA)
        pygame.draw.rect(self.torch_surf, (90, 70, 40), (6, 8, 5, 14))
        pygame.draw.rect(self.torch_surf, (110, 85, 50), (4, 8, 9, 3))

    # ---- Lighting surfaces ----
    def _build_light_surfaces(self):
        self.light_surfs = {}
        for name, radius, color in [
            ("player", PLAYER_LIGHT_RADIUS, PLAYER_LIGHT_COLOR),
            ("torch", TORCH_LIGHT_RADIUS, TORCH_LIGHT_COLOR),
            ("proj_blue", PROJ_LIGHT_RADIUS, (140, 180, 255)),
            ("proj_red", PROJ_LIGHT_RADIUS, (255, 100, 80)),
            ("proj_power", PROJ_LIGHT_RADIUS + 20, (160, 140, 255)),
            ("elite_haste", 170, (100, 170, 255)),
            ("elite_frenzy", 170, (255, 130, 70)),
            ("elite_guardian", 170, (100, 220, 140)),
            ("portal", 200, (200, 200, 100)),
            ("loot", 70, (200, 180, 100)),
            ("chest", 100, (200, 180, 100)),
            ("gold_chest", 130, (255, 220, 80)),
            ("poison", 110, (60, 180, 40)),
            ("lava", 130, (255, 100, 30)),
            ("ice_pool", 90, (100, 160, 255)),
            ("infusion_fire", PROJ_LIGHT_RADIUS + 15, (255, 140, 40)),
            ("infusion_ice", PROJ_LIGHT_RADIUS + 15, (100, 180, 255)),
            ("infusion_lightning", PROJ_LIGHT_RADIUS + 15, (255, 255, 100)),
        ]:
            self.light_surfs[name] = self._make_light_surf(radius, color)

    def _make_light_surf(self, radius: int, color: Tuple[int, int, int]) -> pygame.Surface:
        size = radius * 2
        surf = pygame.Surface((size, size))
        surf.fill((0, 0, 0))
        for i in range(radius, 0, -2):
            t = i / radius
            brightness = max(0.0, 1.0 - t * t)
            r = min(255, int(color[0] * brightness))
            g = min(255, int(color[1] * brightness))
            b = min(255, int(color[2] * brightness))
            pygame.draw.circle(surf, (r, g, b), (radius, radius), i)
        return surf

    # ---- Sound generation ----
    def _build_sounds(self):
        rate = 22050
        self.sounds = {}
        num_channels = pygame.mixer.get_init()[2]  # actual channel count (1=mono, 2=stereo)

        def make_sound(samples):
            """Convert float array (-1..1) to pygame Sound."""
            arr = (np.clip(samples, -1, 1) * 32767).astype(np.int16)
            if num_channels == 2:
                arr = np.column_stack((arr, arr))
            else:
                arr = arr.reshape(-1, 1)
            return pygame.sndarray.make_sound(arr)

        def tone(freq, dur, vol=0.3):
            t = np.linspace(0, dur, int(rate * dur), endpoint=False)
            return np.sin(2 * np.pi * freq * t) * vol

        def noise(dur, vol=0.15):
            return np.random.uniform(-vol, vol, int(rate * dur))

        def fade_out(s):
            env = np.linspace(1.0, 0.0, len(s))
            return s * env

        def fade_in_out(s, attack=0.1):
            n = len(s)
            a = int(n * attack)
            env = np.ones(n)
            env[:a] = np.linspace(0, 1, a)
            env[-a:] = np.linspace(1, 0, a)
            return s * env

        # Arrow shoot - short twang
        t = np.linspace(0, 0.08, int(rate * 0.08), endpoint=False)
        twang = np.sin(2 * np.pi * 600 * t) * 0.2 * np.exp(-t * 40)
        twang += noise(0.08, 0.06) * np.exp(-t * 50)
        self.sounds["arrow"] = make_sound(twang)

        # Multishot - wider twang
        t = np.linspace(0, 0.12, int(rate * 0.12), endpoint=False)
        multi = np.sin(2 * np.pi * 500 * t) * 0.25 * np.exp(-t * 30)
        multi += np.sin(2 * np.pi * 750 * t) * 0.12 * np.exp(-t * 35)
        multi += noise(0.12, 0.05) * np.exp(-t * 40)
        self.sounds["multishot"] = make_sound(multi)

        # Hit - thud
        t = np.linspace(0, 0.06, int(rate * 0.06), endpoint=False)
        hit = np.sin(2 * np.pi * 200 * t) * 0.3 * np.exp(-t * 50)
        hit += noise(0.06, 0.1) * np.exp(-t * 60)
        self.sounds["hit"] = make_sound(hit)

        # Enemy death - low burst
        t = np.linspace(0, 0.15, int(rate * 0.15), endpoint=False)
        death = np.sin(2 * np.pi * 120 * t) * 0.3 * np.exp(-t * 20)
        death += noise(0.15, 0.12) * np.exp(-t * 15)
        self.sounds["death"] = make_sound(death)

        # Pickup - bright chime
        chime = fade_out(tone(880, 0.06, 0.2))
        chime2 = fade_out(tone(1100, 0.06, 0.15))
        pad = np.zeros(int(rate * 0.03))
        pickup = np.concatenate([chime, pad, chime2])
        self.sounds["pickup"] = make_sound(pickup)

        # Gold pickup - coin clink
        t = np.linspace(0, 0.05, int(rate * 0.05), endpoint=False)
        coin = np.sin(2 * np.pi * 2000 * t) * 0.15 * np.exp(-t * 60)
        coin += np.sin(2 * np.pi * 3000 * t) * 0.08 * np.exp(-t * 70)
        self.sounds["gold"] = make_sound(coin)

        # Goblin spawn - playful jingle
        g1 = fade_out(tone(660, 0.07, 0.2))
        g2 = fade_out(tone(880, 0.07, 0.2))
        g3 = fade_out(tone(1100, 0.1, 0.25))
        gpad = np.zeros(int(rate * 0.02))
        goblin = np.concatenate([g1, gpad, g2, gpad, g3])
        self.sounds["goblin"] = make_sound(goblin)

        # Goblin jackpot - triumphant
        j1 = fade_out(tone(880, 0.08, 0.25))
        j2 = fade_out(tone(1100, 0.08, 0.25))
        j3 = fade_out(tone(1320, 0.08, 0.25))
        j4 = fade_out(tone(1760, 0.15, 0.3))
        jp = np.zeros(int(rate * 0.02))
        jackpot = np.concatenate([j1, jp, j2, jp, j3, jp, j4])
        self.sounds["jackpot"] = make_sound(jackpot)

        # Portal enter - whoosh
        t = np.linspace(0, 0.25, int(rate * 0.25), endpoint=False)
        sweep = np.sin(2 * np.pi * (200 + 400 * t / 0.25) * t) * 0.2
        sweep += noise(0.25, 0.08)
        sweep = fade_in_out(sweep)
        self.sounds["portal"] = make_sound(sweep)

        # Level up - ascending tones
        lu1 = fade_out(tone(440, 0.08, 0.2))
        lu2 = fade_out(tone(550, 0.08, 0.2))
        lu3 = fade_out(tone(660, 0.08, 0.2))
        lu4 = fade_out(tone(880, 0.15, 0.25))
        lp = np.zeros(int(rate * 0.02))
        self.sounds["levelup"] = make_sound(np.concatenate([lu1, lp, lu2, lp, lu3, lp, lu4]))

        # Chest break
        t = np.linspace(0, 0.12, int(rate * 0.12), endpoint=False)
        chest_brk = noise(0.12, 0.2) * np.exp(-t * 20)
        chest_brk += np.sin(2 * np.pi * 300 * t) * 0.15 * np.exp(-t * 25)
        self.sounds["chest"] = make_sound(chest_brk)

        # Crate explosion - loud boom
        t = np.linspace(0, 0.2, int(rate * 0.2), endpoint=False)
        boom = np.sin(2 * np.pi * 60 * t) * 0.35 * np.exp(-t * 12)
        boom += np.sin(2 * np.pi * 120 * t) * 0.2 * np.exp(-t * 15)
        boom += noise(0.2, 0.25) * np.exp(-t * 10)
        self.sounds["crate_explode"] = make_sound(boom)

        # Dash - quick whoosh
        t = np.linspace(0, 0.1, int(rate * 0.1), endpoint=False)
        dash = noise(0.1, 0.15) * np.exp(-t * 25)
        self.sounds["dash"] = make_sound(fade_in_out(dash, 0.2))

        # Player hurt
        t = np.linspace(0, 0.1, int(rate * 0.1), endpoint=False)
        hurt = np.sin(2 * np.pi * 150 * t) * 0.25 * np.exp(-t * 25)
        hurt += noise(0.1, 0.1) * np.exp(-t * 30)
        self.sounds["hurt"] = make_sound(hurt)

        # Infusion pickup - sparkle
        sp1 = fade_out(tone(1200, 0.05, 0.15))
        sp2 = fade_out(tone(1600, 0.05, 0.15))
        sp3 = fade_out(tone(2000, 0.08, 0.2))
        sp = np.zeros(int(rate * 0.02))
        self.sounds["infusion"] = make_sound(np.concatenate([sp1, sp, sp2, sp, sp3]))

        # Lightning zap
        t = np.linspace(0, 0.08, int(rate * 0.08), endpoint=False)
        zap = noise(0.08, 0.25) * np.exp(-t * 35)
        zap += np.sin(2 * np.pi * 3000 * t) * 0.1 * np.exp(-t * 50)
        self.sounds["zap"] = make_sound(zap)

        # --- Creature-specific hit/death sounds ---
        # Kind 0: Skeleton - bone rattle
        t = np.linspace(0, 0.08, int(rate * 0.08), endpoint=False)
        bone_hit = noise(0.08, 0.2) * np.exp(-t * 40)
        bone_hit += np.sin(2 * np.pi * 800 * t) * 0.1 * np.exp(-t * 50)
        bone_hit += np.sin(2 * np.pi * 1200 * t) * 0.08 * np.exp(-t * 55)
        self.sounds["hit_skeleton"] = make_sound(bone_hit)
        t = np.linspace(0, 0.2, int(rate * 0.2), endpoint=False)
        bone_death = noise(0.2, 0.18) * np.exp(-t * 12)
        bone_death += np.sin(2 * np.pi * 400 * t) * 0.12 * np.exp(-t * 15)
        bone_death += np.sin(2 * np.pi * 900 * t) * 0.08 * np.exp(-t * 20)
        self.sounds["death_skeleton"] = make_sound(bone_death)

        # Kind 1: Demon - deep growl
        t = np.linspace(0, 0.1, int(rate * 0.1), endpoint=False)
        demon_hit = np.sin(2 * np.pi * 80 * t) * 0.25 * np.exp(-t * 25)
        demon_hit += np.sin(2 * np.pi * 160 * t) * 0.15 * np.exp(-t * 30)
        demon_hit += noise(0.1, 0.08) * np.exp(-t * 35)
        self.sounds["hit_demon"] = make_sound(demon_hit)
        t = np.linspace(0, 0.25, int(rate * 0.25), endpoint=False)
        demon_death = np.sin(2 * np.pi * 60 * t) * 0.3 * np.exp(-t * 10)
        demon_death += np.sin(2 * np.pi * (60 + 80 * t / 0.25) * t) * 0.15
        demon_death *= np.exp(-t * 8)
        demon_death += noise(0.25, 0.12) * np.exp(-t * 10)
        self.sounds["death_demon"] = make_sound(demon_death)

        # Kind 2: Spider - chittering hiss
        t = np.linspace(0, 0.07, int(rate * 0.07), endpoint=False)
        spider_hit = noise(0.07, 0.22) * np.exp(-t * 45)
        spider_hit += np.sin(2 * np.pi * 2200 * t) * 0.12 * np.exp(-t * 50)
        spider_hit += np.sin(2 * np.pi * 3400 * t) * 0.06 * np.exp(-t * 55)
        self.sounds["hit_spider"] = make_sound(spider_hit)
        t = np.linspace(0, 0.18, int(rate * 0.18), endpoint=False)
        spider_death = noise(0.18, 0.2) * np.exp(-t * 15)
        spider_death += np.sin(2 * np.pi * 1800 * t) * 0.1 * np.exp(-t * 18)
        freq_sweep = 2500 - 1500 * t / 0.18
        spider_death += np.sin(2 * np.pi * freq_sweep * t) * 0.08
        spider_death *= np.exp(-t * 12)
        self.sounds["death_spider"] = make_sound(spider_death)

        # Kind 3: Wraith - ethereal wail
        t = np.linspace(0, 0.1, int(rate * 0.1), endpoint=False)
        wraith_hit = np.sin(2 * np.pi * 500 * t) * 0.15
        wraith_hit += np.sin(2 * np.pi * 750 * t) * 0.1
        wraith_hit *= np.exp(-t * 20)
        wraith_hit = fade_in_out(wraith_hit, 0.2)
        self.sounds["hit_wraith"] = make_sound(wraith_hit)
        t = np.linspace(0, 0.3, int(rate * 0.3), endpoint=False)
        wraith_death = np.sin(2 * np.pi * (600 - 200 * t / 0.3) * t) * 0.2
        wraith_death += np.sin(2 * np.pi * (900 - 400 * t / 0.3) * t) * 0.1
        wraith_death *= np.exp(-t * 6)
        wraith_death = fade_in_out(wraith_death, 0.15)
        self.sounds["death_wraith"] = make_sound(wraith_death)

        # Boss hit/death - thunderous impact
        t = np.linspace(0, 0.12, int(rate * 0.12), endpoint=False)
        boss_hit = np.sin(2 * np.pi * 100 * t) * 0.3 * np.exp(-t * 25)
        boss_hit += np.sin(2 * np.pi * 200 * t) * 0.2 * np.exp(-t * 30)
        boss_hit += noise(0.12, 0.15) * np.exp(-t * 35)
        self.sounds["hit_boss"] = make_sound(boss_hit)
        t = np.linspace(0, 0.35, int(rate * 0.35), endpoint=False)
        boss_death = np.sin(2 * np.pi * 50 * t) * 0.35 * np.exp(-t * 6)
        boss_death += np.sin(2 * np.pi * 120 * t) * 0.2 * np.exp(-t * 8)
        boss_death += noise(0.35, 0.15) * np.exp(-t * 5)
        self.sounds["death_boss"] = make_sound(boss_death)

        # Respawn - angelic rising tone
        r1 = fade_out(tone(440, 0.1, 0.2))
        r2 = fade_out(tone(660, 0.1, 0.2))
        r3 = fade_out(tone(880, 0.15, 0.25))
        rp = np.zeros(int(rate * 0.03))
        self.sounds["respawn"] = make_sound(np.concatenate([r1, rp, r2, rp, r3]))

        # Save confirm - soft chime
        sv = fade_out(tone(1000, 0.06, 0.15))
        sv2 = fade_out(tone(1500, 0.08, 0.2))
        self.sounds["save"] = make_sound(np.concatenate([sv, np.zeros(int(rate * 0.02)), sv2]))

        # Set volumes
        for s in self.sounds.values():
            s.set_volume(0.4)
        self.sounds["gold"].set_volume(0.25)
        self.sounds["goblin"].set_volume(0.5)
        self.sounds["jackpot"].set_volume(0.6)
        self.sounds["levelup"].set_volume(0.5)
        self.sounds["death_boss"].set_volume(0.6)
        self.sounds["hit_boss"].set_volume(0.5)

    _CREATURE_SOUND_MAP = {0: "skeleton", 1: "demon", 2: "spider", 3: "wraith"}

    def _creature_sound_name(self, e) -> str:
        """Get sound suffix for an enemy kind."""
        if isinstance(e, Boss):
            return "boss"
        return self._CREATURE_SOUND_MAP.get(e.kind, "skeleton")

    def play_sound(self, name):
        snd = self.sounds.get(name)
        if snd:
            snd.play()

    # ---- Difficulty menu (gothic) ----
    def _title_menu(self) -> str:
        """Show title menu with Continue/New Game. Returns 'continue' or goes to difficulty select."""
        screen = self.screen
        small = self.font
        title_font = self.titlefont
        has_save = self._has_save
        if not has_save:
            # No save, go straight to difficulty select
            return self._difficulty_select()
        # Load save info for display
        save_info = ""
        try:
            with open(self._get_save_path(), "r") as f:
                data = json.load(f)
            pd = data["player"]
            gd = data["game"]
            save_info = (f"Level {pd['level']}  |  Depth {gd['current_level']}  |  "
                        f"{gd.get('difficulty', 'Normal')}  |  "
                        f"Kills: {gd.get('kills', 0)}  |  Gold: {pd.get('gold', 0)}")
        except Exception:
            save_info = "Saved game found"

        options = [("Continue", "continue"), ("New Game", "new")]
        idx = 0
        t = 0.0
        while True:
            dt = 16 / 1000.0
            t += dt
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                if ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_UP, pygame.K_w):
                        idx = (idx - 1) % len(options)
                    elif ev.key in (pygame.K_DOWN, pygame.K_s):
                        idx = (idx + 1) % len(options)
                    elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if options[idx][1] == "continue":
                            return "continue"
                        else:
                            return self._difficulty_select()

            screen.fill(C_GOTHIC_BG)
            # Ambient particles
            for _ in range(2):
                px = random.randint(0, WIDTH)
                py = random.randint(0, HEIGHT)
                a = random.randint(15, 40)
                pygame.draw.circle(screen, (a, a - 2, a + 5), (px, py), random.randint(1, 2))
            # Title
            flicker = 0.9 + 0.1 * math.sin(t * 3.0)
            tc = tuple(min(255, int(c * flicker)) for c in (200, 160, 80))
            title = title_font.render("DUNGEON OF THE DAMNED", True, tc)
            title_y = HEIGHT // 5
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, title_y))
            # Decorative line
            ly = title_y + title.get_height() + 20
            pygame.draw.line(screen, C_GOTHIC_FRAME, (WIDTH // 2 - 320, ly), (WIDTH // 2 + 320, ly), 2)
            pygame.draw.circle(screen, C_GOLD_DARK, (WIDTH // 2, ly), 6)
            pygame.draw.circle(screen, C_GOLD, (WIDTH // 2, ly), 4)

            y = HEIGHT // 2 - 40
            for i, (label, _) in enumerate(options):
                is_sel = (i == idx)
                col = C_GOLD if is_sel else (140, 130, 110)
                marker = "> " if is_sel else "  "
                ot = self.bigfont.render(f"{marker}{label}", True, col)
                screen.blit(ot, (WIDTH // 2 - 100, y))
                if i == 0 and is_sel and save_info:
                    si = small.render(save_info, True, (140, 130, 100))
                    screen.blit(si, (WIDTH // 2 - si.get_width() // 2, y + 40))
                y += 65

            hint = small.render("[W/S] or [Arrows] to choose  -  [Enter] to select", True, (100, 95, 80))
            screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT * 2 // 3 + 60))
            pygame.display.flip()
            pygame.time.delay(16)

    def _difficulty_select(self) -> str:
        screen = self.screen
        font = self.bigfont
        small = self.font
        title_font = self.titlefont
        options = ["Easy", "Normal", "Hard"]
        descs = ["For the cautious", "The true experience", "Embrace death"]
        idx = 1
        selecting = True
        t = 0.0
        while selecting:
            dt = 16 / 1000.0
            t += dt
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_LEFT, pygame.K_a):
                        idx = (idx - 1) % 3
                    if e.key in (pygame.K_RIGHT, pygame.K_d):
                        idx = (idx + 1) % 3
                    if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                        selecting = False
                    if e.key == pygame.K_f:
                        self.fullscreen = not self.fullscreen
                        if self.fullscreen:
                            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
                        else:
                            screen = pygame.display.set_mode((WIDTH, HEIGHT))
                        self.screen = screen
                if e.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = e.pos
                    for i in range(3):
                        bx = WIDTH // 2 - 380 + i * 380
                        by = HEIGHT // 2 - 30
                        if abs(mx - bx) < 90 and abs(my - by - 25) < 60:
                            idx = i
                            selecting = False
                            break
            screen.fill(C_GOTHIC_BG)

            # Ambient particles on menu
            for _ in range(2):
                px = random.randint(0, WIDTH)
                py = random.randint(0, HEIGHT)
                a = random.randint(15, 40)
                pygame.draw.circle(screen, (a, a - 2, a + 5), (px, py), random.randint(1, 2))

            # Title with flicker
            flicker = 0.9 + 0.1 * math.sin(t * 3.0)
            tc = tuple(min(255, int(c * flicker)) for c in (200, 160, 80))
            title = title_font.render("DUNGEON OF THE DAMNED", True, tc)
            title_y = HEIGHT // 6
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, title_y))

            # Decorative line
            ly = title_y + title.get_height() + 20
            pygame.draw.line(screen, C_GOTHIC_FRAME, (WIDTH // 2 - 320, ly), (WIDTH // 2 + 320, ly), 2)
            pygame.draw.circle(screen, C_GOLD_DARK, (WIDTH // 2, ly), 6)
            pygame.draw.circle(screen, C_GOLD, (WIDTH // 2, ly), 4)

            # Subtitle
            sub = small.render("Choose your fate, wanderer", True, (150, 140, 120))
            sub_y = ly + 30
            screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, sub_y))

            # Options — spread across width
            opt_y = HEIGHT // 2 - 30
            opt_spacing = 380
            for i, name in enumerate(options):
                bx = WIDTH // 2 - opt_spacing + i * opt_spacing
                by = opt_y
                is_sel = (i == idx)
                # Selection box
                if is_sel:
                    glow = int(20 + 10 * math.sin(t * 4))
                    pygame.draw.rect(screen, (glow + 30, glow + 20, glow), (bx - 90, by - 15, 180, 100), border_radius=8)
                    pygame.draw.rect(screen, C_GOLD, (bx - 90, by - 15, 180, 100), 2, border_radius=8)
                col = C_GOLD if is_sel else (140, 135, 120)
                txt = font.render(name, True, col)
                screen.blit(txt, (bx - txt.get_width() // 2, by))
                desc = small.render(descs[i], True, (120, 115, 100) if is_sel else (80, 75, 65))
                screen.blit(desc, (bx - desc.get_width() // 2, by + 44))

            # Controls hint
            hint = small.render("[A/D] or [Arrow Keys] to choose  -  [Enter] to begin  -  [F] Fullscreen", True, (100, 95, 80))
            screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT * 2 // 3 + 40))

            # Fullscreen indicator
            fs_txt = small.render(f"Display: {'Fullscreen' if self.fullscreen else 'Windowed'}  [F11 in-game]", True, (80, 75, 65))
            screen.blit(fs_txt, (WIDTH // 2 - fs_txt.get_width() // 2, HEIGHT * 2 // 3 + 70))

            # Bottom decorative line
            bot_y = HEIGHT - 140
            pygame.draw.line(screen, (50, 45, 35), (200, bot_y), (WIDTH - 200, bot_y), 1)
            ver = small.render("Dungeon of the Damned v6.0", True, (60, 55, 45))
            screen.blit(ver, (WIDTH // 2 - ver.get_width() // 2, bot_y + 20))

            pygame.display.flip()
            pygame.time.delay(16)
        return options[idx]

    # ---- Particle helpers ----
    def emit_particles(self, x, y, count, color, speed=80, life=0.6, size=2.5, gravity=120, spread=math.tau):
        for _ in range(min(count, MAX_PARTICLES - len(self.particles))):
            ang = random.uniform(0, spread)
            spd = random.uniform(speed * 0.3, speed)
            self.particles.append(Particle(
                x=x, y=y,
                vx=math.cos(ang) * spd, vy=math.sin(ang) * spd,
                r=min(255, color[0] + random.randint(-20, 20)),
                g=min(255, max(0, color[1] + random.randint(-20, 20))),
                b=min(255, max(0, color[2] + random.randint(-20, 20))),
                life=life * random.uniform(0.5, 1.0),
                max_life=life,
                size=size * random.uniform(0.5, 1.5),
                gravity=gravity
            ))

    def emit_blood(self, x, y, count=8):
        self.emit_particles(x, y, count, C_BLOOD, speed=100, life=0.7, size=2.5, gravity=180)

    def emit_death_burst(self, x, y, color, count=20):
        self.emit_particles(x, y, count, color, speed=140, life=0.9, size=3.0, gravity=100)
        # blood stain on ground
        self.dungeon.blood_stains.append((x, y, 2.0 + random.random() * 2.0))

    def emit_magic(self, x, y, count=6):
        self.emit_particles(x, y, count, C_MANA_LIGHT, speed=60, life=0.5, size=2.0, gravity=-40)

    def emit_fire(self, x, y, count=3):
        self.emit_particles(x, y, count, C_FIRE, speed=30, life=0.4, size=2.0, gravity=-100)

    def emit_dust(self, x, y, count=2):
        self.emit_particles(x, y, count, (120, 110, 90), speed=20, life=0.5, size=1.5, gravity=-10)

    def emit_sparks(self, x, y, count=5):
        self.emit_particles(x, y, count, C_FIRE_BRIGHT, speed=120, life=0.3, size=1.5, gravity=60)

    def add_floating_text(self, x, y, text, color, scale=1.0):
        self.floating_texts.append(FloatingText(
            x=x, y=y, text=text,
            r=color[0], g=color[1], b=color[2],
            scale=scale
        ))

    def add_screen_shake(self, intensity):
        self.shake_intensity = max(self.shake_intensity, intensity)

    # ---- Spawning (same mechanics) ----
    def _random_floor_pos(self, near_player=True, max_tries=200):
        tries = 0
        while tries < max_tries:
            if near_player:
                base_tx = int(self.player.pos.x // TILE)
                base_ty = int(self.player.pos.y // TILE)
                tx = random.randint(max(1, base_tx - 12), min(MAP_W - 2, base_tx + 12))
                ty = random.randint(max(1, base_ty - 8), min(MAP_H - 2, base_ty + 8))
            else:
                tx = random.randint(1, MAP_W - 2)
                ty = random.randint(1, MAP_H - 2)
            if self.dungeon.tiles[tx][ty] == FLOOR:
                pos = Vec(tx * TILE + TILE / 2, ty * TILE + TILE / 2)
                if (pos - self.player.pos).length() > 200:
                    return pos
            tries += 1
        return self.player.pos + Vec(random.randint(-240, 240), random.randint(-240, 240))

    def spawn_enemy(self, near_player: bool = True, kind_override: Optional[int] = None):
        if len(self.enemies) >= MAX_ACTIVE_ENEMIES:
            return
        pos = self._random_floor_pos(near_player)
        scale = (WAVE_SCALE ** (self.wave - 1)) * (1.0 + 0.1 * (self.current_level - 1))
        hp = int(ENEMY_BASE_HP * scale * self.diff["enemy_hp"])
        dmg_min = int(ENEMY_BASE_DMG[0] * scale * self.diff["enemy_dmg"])
        dmg_max = int(ENEMY_BASE_DMG[1] * scale * self.diff["enemy_dmg"])
        speed = ENEMY_SPEED * (0.95 + 0.1 * random.random()) * self.diff["enemy_speed"]
        kind = kind_override if kind_override is not None else random.choices([0, 1, 2, 3], [0.35, 0.25, 0.25, 0.15])[0]
        e = Enemy(pos=pos, vel=Vec(0, 0), radius=20, hp=hp, max_hp=hp,
                  dmg_min=dmg_min, dmg_max=dmg_max, speed=speed, kind=kind)
        if kind == 3:
            e.shot_cd = random.uniform(1.4, 2.2)
        self.enemies.append(e)
        # spawn particles
        self.emit_particles(pos.x, pos.y, 8, (80, 40, 120), speed=60, life=0.5, gravity=-30)

    def _find_room_at(self, pos: Vec) -> Optional[pygame.Rect]:
        """Find which room a world-space position is in."""
        tx = int(pos.x // TILE)
        ty = int(pos.y // TILE)
        for room in self.dungeon.rooms:
            if room.left <= tx < room.right and room.top <= ty < room.bottom:
                return room
        return None

    def _random_floor_in_room(self, room: pygame.Rect, max_tries=40) -> Optional[Vec]:
        """Pick a random floor tile inside a room."""
        for _ in range(max_tries):
            tx = random.randint(room.left + 1, room.right - 2)
            ty = random.randint(room.top + 1, room.bottom - 2)
            if self.dungeon.tiles[tx][ty] == FLOOR:
                return Vec(tx * TILE + TILE / 2, ty * TILE + TILE / 2)
        return None

    def spawn_elite_pack(self):
        if len(self.enemies) >= MAX_ACTIVE_ENEMIES:
            return
        pos = self._random_floor_pos(near_player=True)
        scale = (WAVE_SCALE ** (self.wave - 1)) * (1.0 + 0.1 * (self.current_level - 1))
        hp = int(ENEMY_BASE_HP * ELITE_MULT["hp"] * scale * self.diff["enemy_hp"])
        dmg_min = int(ENEMY_BASE_DMG[0] * ELITE_MULT["dmg"] * scale * self.diff["enemy_dmg"])
        dmg_max = int(ENEMY_BASE_DMG[1] * ELITE_MULT["dmg"] * scale * self.diff["enemy_dmg"])
        spd = ENEMY_SPEED * ELITE_MULT["spd"] * self.diff["enemy_speed"]
        aura_name = random.choice(list(AURAS.keys()))
        elite = Elite(pos=pos, vel=Vec(0, 0), radius=ELITE_MULT["radius"], hp=hp, max_hp=hp,
                      dmg_min=dmg_min, dmg_max=dmg_max, speed=spd, kind=1, aura=aura_name)
        self.enemies.append(elite)
        self.emit_particles(pos.x, pos.y, 15, AURAS[aura_name]["color"], speed=80, life=0.8, gravity=-20)
        # Scatter minions across random floor positions in nearby rooms
        count = random.randint(*PACK_SIZE_RANGE)
        # find elite's room or use random rooms
        elite_room = self._find_room_at(pos)
        # build candidate rooms: elite's room + adjacent rooms
        candidate_rooms = []
        if elite_room:
            candidate_rooms.append(elite_room)
        # add a few other random rooms for variety
        other_rooms = [r for r in self.dungeon.rooms if r != elite_room]
        random.shuffle(other_rooms)
        candidate_rooms.extend(other_rooms[:3])
        if not candidate_rooms:
            candidate_rooms = self.dungeon.rooms[:5]
        for i in range(count):
            if len(self.enemies) >= MAX_ACTIVE_ENEMIES:
                break
            kind = random.choices([0, 1, 2, 3], [0.4, 0.25, 0.2, 0.15])[0]
            # pick a random room from candidates
            room = random.choice(candidate_rooms)
            mpos = self._random_floor_in_room(room)
            if mpos is None:
                mpos = self._random_floor_pos(near_player=False)
            self.spawn_enemy(near_player=False, kind_override=kind)
            self.enemies[-1].pos = mpos

    def spawn_treasure_goblin(self):
        if self.treasure_goblin is not None:
            return
        pos = self._random_floor_pos(near_player=True)
        scale = 1.0 + 0.1 * (self.current_level - 1)
        hp = int(50 * scale)
        goblin = TreasureGoblin(
            pos=pos, vel=Vec(0, 0), radius=16,
            hp=hp, max_hp=hp, dmg_min=0, dmg_max=0,
            speed=ENEMY_SPEED * GOBLIN_SPEED_MULT, kind=4,
            portal_timer=GOBLIN_DESPAWN_TIME
        )
        self.treasure_goblin = goblin
        self.enemies.append(goblin)
        self.add_floating_text(pos.x, pos.y - 30, "TREASURE GOBLIN!", C_GOLD, 1.5)
        self.play_sound("goblin")
        self.emit_particles(pos.x, pos.y, 25, C_GOLD, speed=100, life=0.8, gravity=-40)
        self.add_screen_shake(4)

    def spawn_boss(self):
        if self.current_level % 5 != 0 or self.boss_spawned:
            return
        center_tx, center_ty = self.dungeon.center(self.dungeon.rooms[-1])
        pos = Vec(center_tx * TILE + TILE / 2, center_ty * TILE + TILE / 2)
        boss_scale = 1.0 + (self.current_level // 5 - 1) * 0.3
        hp = int(BOSS_HP * self.diff["enemy_hp"] * boss_scale)
        dmg_min = int(BOSS_DMG[0] * self.diff["enemy_dmg"] * boss_scale)
        dmg_max = int(BOSS_DMG[1] * self.diff["enemy_dmg"] * boss_scale)
        b = Boss(pos=pos, vel=Vec(0, 0), radius=34, hp=hp, max_hp=hp,
                 dmg_min=dmg_min, dmg_max=dmg_max,
                 speed=ENEMY_SPEED * 0.9 * self.diff["enemy_speed"],
                 kind=1, shot_cd=random.uniform(*BOSS_SHOT_CD))
        self.enemies.append(b)
        self.boss_spawned = True
        self.add_screen_shake(12)
        self.emit_death_burst(pos.x, pos.y, (180, 60, 60), 30)

    def spawn_pickup_near_player(self):
        base_tx = int(self.player.pos.x // TILE)
        base_ty = int(self.player.pos.y // TILE)
        for _ in range(50):
            tx = random.randint(max(1, base_tx - 10), min(MAP_W - 2, base_tx + 10))
            ty = random.randint(max(1, base_ty - 8), min(MAP_H - 2, base_ty + 8))
            if self.dungeon.tiles[tx][ty] == FLOOR:
                pos = Vec(tx * TILE + TILE / 2, ty * TILE + TILE / 2)
                if (pos - self.player.pos).length() > 140:
                    if random.random() < 0.5:
                        self.loots.append(Loot(pos=pos, dmg_boost=True))
                    else:
                        self.loots.append(Loot(pos=pos, shield_boost=True))
                    return

    # ---- Vendor NPC ----
    def _spawn_vendor(self):
        """Place vendor NPC in the first room of the dungeon."""
        if not self.dungeon.rooms:
            return
        room = self.dungeon.rooms[0]
        # Place vendor near the edge of the first room, offset from center
        cx, cy = self.dungeon.center(room)
        # Offset a bit so player doesn't spawn directly on vendor
        vx = (cx + 3) * TILE + TILE / 2
        vy = cy * TILE + TILE / 2
        vendor_names = ["Gheed", "Charsi", "Akara", "Ormus", "Anya", "Lysander", "Halbu"]
        name = random.choice(vendor_names)
        stock = self._generate_vendor_stock()
        self.vendor = Vendor(pos=Vec(vx, vy), stock=stock, name=name)

    def _generate_vendor_stock(self) -> list:
        """Generate vendor's weapon inventory, scaled to depth."""
        stock = []
        depth = self.current_level
        for _ in range(VENDOR_STOCK_SIZE):
            # Vendors sell normal and magic, with occasional rare at high depth
            roll = random.random()
            if roll < 0.05 + depth * 0.01:
                rarity = RARITY_RARE
            elif roll < 0.50:
                rarity = RARITY_MAGIC
            else:
                rarity = RARITY_NORMAL
            stock.append(generate_weapon(depth, rarity))
        return stock

    def _get_vendor_buy_price(self, w: Weapon) -> int:
        """Price to buy from vendor."""
        base = (w.dmg_min + w.dmg_max) * 2 + w.ilvl * 3
        rarity_mult = {RARITY_NORMAL: 1, RARITY_MAGIC: 3, RARITY_RARE: 8,
                       RARITY_UNIQUE: 15, RARITY_SET: 12}
        return max(5, int(base * rarity_mult.get(w.rarity, 1)))

    def _get_vendor_sell_price(self, w: Weapon) -> int:
        """Price vendor pays for player's item (less than buy price)."""
        return max(1, self._get_vendor_buy_price(w) // 3)

    # ---- Chest system ----
    def _spawn_chests(self):
        """Create chest objects from dungeon chest positions."""
        self.chests = []
        for tx, ty in self.dungeon.chest_positions:
            pos = Vec(tx * TILE + TILE / 2, ty * TILE + TILE / 2)
            kind = "gold" if random.random() < 0.15 else "wood"
            self.chests.append(Chest(pos=pos, kind=kind))

    def _spawn_crates(self):
        """Create crate objects from dungeon crate positions."""
        self.crates = []
        for tx, ty in self.dungeon.crate_positions:
            pos = Vec(tx * TILE + TILE / 2, ty * TILE + TILE / 2)
            self.crates.append(Crate(pos=pos))

    def _on_crate_broken(self, crate: Crate):
        """Handle crate breaking - possible explosion and loot."""
        explodes = random.random() < CRATE_EXPLODE_CHANCE
        if explodes:
            # Explosion effect
            self.emit_death_burst(crate.pos.x, crate.pos.y, (255, 140, 40), 25)
            self.emit_particles(crate.pos.x, crate.pos.y, 20, (255, 100, 30),
                                speed=120, life=0.6, gravity=60)
            self.add_screen_shake(6)
            self.add_floating_text(crate.pos.x, crate.pos.y - 15, "BOOM!", (255, 160, 40), 1.0)
            self.play_sound("crate_explode")
            # Damage nearby enemies
            for e in self.enemies:
                if not e.alive:
                    continue
                dist = (e.pos - crate.pos).length()
                if dist < CRATE_EXPLODE_RADIUS:
                    dmg = random.randint(*CRATE_EXPLODE_DMG)
                    falloff = 1.0 - dist / CRATE_EXPLODE_RADIUS
                    dmg = max(1, int(dmg * falloff))
                    e.hp -= dmg
                    e.hit_flash = 0.15
                    e.vel += (e.pos - crate.pos).normalize() * 200
                    self.add_floating_text(e.pos.x, e.pos.y - e.radius - 5,
                                           str(dmg), (255, 160, 40), 0.8)
                    if e.hp <= 0 and e.alive:
                        e.alive = False
                        self.on_enemy_dead(e)
            # Light damage to player if close
            p = self.player
            pdist = (p.pos - crate.pos).length()
            if pdist < CRATE_EXPLODE_RADIUS and p.iframes <= 0:
                pdmg = max(1, int(random.randint(*CRATE_EXPLODE_DMG) * (1.0 - pdist / CRATE_EXPLODE_RADIUS)))
                if p.shield > 0:
                    absorb = min(p.shield, pdmg)
                    p.shield -= absorb
                    pdmg -= absorb
                if pdmg > 0:
                    p.hp -= pdmg
                    self.add_floating_text(p.pos.x, p.pos.y - 20, f"-{pdmg}", (255, 100, 40), 1.0)
                    p.iframes = max(p.iframes, 0.3)
        else:
            # Normal break - wood splinters
            self.emit_particles(crate.pos.x, crate.pos.y, 8, (140, 100, 50),
                                speed=60, life=0.4, gravity=80)
            self.add_screen_shake(2)
            self.play_sound("chest")  # reuse chest break sound

        # Loot drop (less common than chests)
        if random.random() < CRATE_DROP_CHANCE:
            roll = random.random()
            if roll < 0.35:
                self.loots.append(Loot(pos=self._safe_loot_pos(crate.pos),
                                       gold=random.randint(2, 10)))
            elif roll < 0.60:
                pt = random.choice(["hp", "mana"])
                self.loots.append(Loot(pos=self._safe_loot_pos(crate.pos),
                                       potion_hp=(pt == "hp"), potion_mana=(pt == "mana")))
            elif roll < 0.80:
                self.loots.append(Loot(pos=self._safe_loot_pos(crate.pos),
                                       dmg_boost=True))
            elif roll < 0.92:
                self.loots.append(Loot(pos=self._safe_loot_pos(crate.pos),
                                       infusion=random.choice(INFUSION_TYPES)))
            else:
                # Rare weapon from crate
                w_rarity = RARITY_NORMAL if random.random() < 0.7 else RARITY_MAGIC
                self.loots.append(Loot(pos=self._safe_loot_pos(crate.pos),
                                       weapon=generate_weapon(self.current_level, w_rarity)))

    def _safe_loot_pos(self, center: Vec, spread: float = 25.0) -> Vec:
        """Return a loot position guaranteed to be on a floor tile."""
        for _ in range(20):
            p = center + Vec(random.uniform(-spread, spread), random.uniform(-spread, spread))
            tx, ty = int(p.x // TILE), int(p.y // TILE)
            if 0 <= tx < MAP_W and 0 <= ty < MAP_H and self.dungeon.tiles[tx][ty] == FLOOR:
                return p
        # Fallback: search outward in a grid
        cx, cy = int(center.x // TILE), int(center.y // TILE)
        for r in range(1, 6):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < MAP_W and 0 <= ny < MAP_H and self.dungeon.tiles[nx][ny] == FLOOR:
                        return Vec(nx * TILE + TILE / 2, ny * TILE + TILE / 2)
        return center.copy()

    def _on_chest_broken(self, chest: Chest):
        """Handle chest breaking - spawn loot: always 2-3 items + weapon."""
        # Burst effect
        color = C_GOLD if chest.kind == "gold" else (160, 120, 60)
        self.emit_death_burst(chest.pos.x, chest.pos.y, color, 15)
        self.add_screen_shake(3)
        self.add_floating_text(chest.pos.x, chest.pos.y - 15, "LOOT!", C_GOLD, 1.2)
        self.play_sound("chest")

        # Gold drop (always)
        gold_mult = 3 if chest.kind == "gold" else 1
        gold = random.randint(*CHEST_GOLD_DROP) * gold_mult
        self.loots.append(Loot(pos=self._safe_loot_pos(chest.pos), gold=gold))

        # Always drop 2-3 consumables (potions, boosts, infusions)
        num_drops = random.randint(2, 3)
        for _ in range(num_drops):
            roll = random.random()
            if roll < 0.35:
                pt = random.choice(["hp", "mana"])
                self.loots.append(Loot(pos=self._safe_loot_pos(chest.pos),
                                       potion_hp=(pt == "hp"), potion_mana=(pt == "mana")))
            elif roll < 0.55:
                self.loots.append(Loot(pos=self._safe_loot_pos(chest.pos), dmg_boost=True))
            elif roll < 0.75:
                self.loots.append(Loot(pos=self._safe_loot_pos(chest.pos), shield_boost=True))
            elif roll < 0.88:
                self.loots.append(Loot(pos=self._safe_loot_pos(chest.pos),
                                       infusion=random.choice(INFUSION_TYPES)))
            else:
                self.loots.append(Loot(pos=self._safe_loot_pos(chest.pos),
                                       gold=random.randint(5, 20) * gold_mult))

        # Always drop a weapon — same rarity chances as a normal monster
        roll = random.random()
        depth = self.current_level
        if chest.kind == "gold":
            # Gold chests slightly better
            if roll < 0.05 + depth * 0.005:
                w_rarity = RARITY_RARE
            elif roll < 0.45:
                w_rarity = RARITY_MAGIC
            else:
                w_rarity = RARITY_NORMAL
        else:
            if roll < 0.03 + depth * 0.005:
                w_rarity = RARITY_RARE
            elif roll < 0.35:
                w_rarity = RARITY_MAGIC
            else:
                w_rarity = RARITY_NORMAL
        self.loots.append(Loot(pos=self._safe_loot_pos(chest.pos),
                               weapon=generate_weapon(depth, w_rarity)))

    def update_chests(self, dt: float):
        for chest in self.chests:
            if chest.alive:
                chest.hit_flash = max(0.0, chest.hit_flash - dt)

    def update_crates(self, dt: float):
        for crate in self.crates:
            if crate.alive:
                crate.hit_flash = max(0.0, crate.hit_flash - dt)

    # ---- Input ----
    def handle_input(self, dt: float):
        keys = pygame.key.get_pressed()
        move = Vec(0, 0)
        if keys[pygame.K_w]:
            move.y -= 1
        if keys[pygame.K_s]:
            move.y += 1
        if keys[pygame.K_a]:
            move.x -= 1
        if keys[pygame.K_d]:
            move.x += 1
        if move.length_squared() > 0:
            move = move.normalize()
        self.player.vel = move * PLAYER_SPEED

        # Dash
        if keys[pygame.K_LSHIFT] and self.player.dash_cd <= 0 and self.player.dash_timer <= 0:
            self.player.dash_timer = DASH_TIME
            self.player.dash_cd = DASH_CD
            self.player.iframes = max(self.player.iframes, IFRAME_TIME)
            self.emit_dust(self.player.pos.x, self.player.pos.y + 8, 6)
            self.play_sound("dash")

        # Aim direction: mouse
        mx, my = pygame.mouse.get_pos()
        world_mouse = Vec(mx + self.cam_x - self.shake_x, my + self.cam_y - self.shake_y)
        aim_dir = world_mouse - self.player.pos
        if aim_dir.length_squared() == 0:
            aim_dir = Vec(1, 0)
        aim_dir = aim_dir.normalize()

        # Shooting: mouse buttons
        buttons = pygame.mouse.get_pressed(3)
        want_basic = buttons[0]
        want_power = buttons[2]
        if want_basic and self.player.basic_cd <= 0:
            self.shoot_basic(aim_dir)
        if want_power and self.player.power_cd <= 0 and self.player.mana >= POWER_MANA_COST:
            self.shoot_power(aim_dir)

        # Potions
        if keys[pygame.K_q] and self.player.potions_hp > 0 and self.player.hp < self.player.max_hp():
            self.player.hp = min(self.player.max_hp(), self.player.hp + POTION_HEAL)
            self.player.potions_hp -= 1
            self.emit_particles(self.player.pos.x, self.player.pos.y, 10, (100, 220, 100), speed=40, life=0.6, gravity=-60)
            self.add_floating_text(self.player.pos.x, self.player.pos.y - 20, f"+{POTION_HEAL}", (100, 255, 100))
        if keys[pygame.K_e] and self.player.potions_mana > 0 and self.player.mana < self.player.max_mana():
            self.player.mana = min(self.player.max_mana(), self.player.mana + POTION_MANA)
            self.player.potions_mana -= 1
            self.emit_particles(self.player.pos.x, self.player.pos.y, 10, C_MANA_LIGHT, speed=40, life=0.6, gravity=-60)

    # ---- Combat ----
    def shoot_basic(self, direction: Vec):
        p = self.player
        spd_mult = p.calc_attack_speed_mult()
        self.player.basic_cd = BASIC_CD / spd_mult
        base = p.weapon.roll_damage()
        dmg = int(base * p.calc_dmg_mult())
        # Critical hit
        if random.random() * 100 < p.calc_crit_chance():
            dmg = int(dmg * 1.8)
            self.add_floating_text(p.pos.x, p.pos.y - 30, "CRIT!", (255, 255, 100), 0.8)
        ang = math.atan2(direction.y, direction.x)
        arrow_speed = PROJECTILE_SPEED * (1.0 + p.dexterity * 0.01)
        proj = Projectile(pos=p.pos + direction * 20, vel=direction * arrow_speed,
                          dmg=dmg, ttl=0.9, radius=BASIC_RADIUS, pierce=p.calc_pierce(),
                          is_arrow=True, angle=ang, infusion=p.infusion_type)
        self.projectiles.append(proj)
        self.play_sound("arrow")
        self.emit_particles(p.pos.x + direction.x * 18, p.pos.y + direction.y * 18,
                            3, (180, 160, 120), speed=40, life=0.25, gravity=0)

    def shoot_power(self, direction: Vec):
        p = self.player
        spd_mult = p.calc_attack_speed_mult()
        self.player.power_cd = POWER_CD / spd_mult
        self.player.mana -= POWER_MANA_COST
        base = p.weapon.roll_damage()
        dmg = int(base * p.calc_dmg_mult() * 1.3)
        is_crit = random.random() * 100 < p.calc_crit_chance()
        if is_crit:
            dmg = int(dmg * 1.8)
        base_angle = math.atan2(direction.y, direction.x)
        arrow_count = p.calc_multishot_count()
        arrow_speed = PROJECTILE_SPEED * 0.92 * (1.0 + p.dexterity * 0.01)
        for i in range(arrow_count):
            offset = (i - arrow_count // 2) * (MULTISHOT_SPREAD / max(1, arrow_count - 1))
            a = base_angle + offset
            arrow_dir = Vec(math.cos(a), math.sin(a))
            proj = Projectile(pos=p.pos + arrow_dir * 22,
                              vel=arrow_dir * arrow_speed,
                              dmg=dmg, ttl=1.0, radius=BASIC_RADIUS, pierce=p.calc_pierce(),
                              is_arrow=True, angle=a, infusion=p.infusion_type)
            self.projectiles.append(proj)
        if is_crit:
            self.add_floating_text(p.pos.x, p.pos.y - 30, "CRIT!", (255, 255, 100), 0.8)
        self.emit_particles(p.pos.x, p.pos.y, 8,
                            (180, 200, 220), speed=60, life=0.4, gravity=0)
        self.add_screen_shake(2)
        self.play_sound("multishot")

    # ---- Updates ----
    def update_player(self, dt: float):
        p = self.player
        p.basic_cd = max(0.0, p.basic_cd - dt)
        p.power_cd = max(0.0, p.power_cd - dt)
        p.dash_cd = max(0.0, p.dash_cd - dt)
        p.iframes = max(0.0, p.iframes - dt)
        p.levelup_flash = max(0.0, p.levelup_flash - dt)
        # Passive mana regeneration
        max_mana = p.max_mana()
        if p.mana < max_mana:
            p.mana = min(max_mana, p.mana + p.mana_regen() * dt)
        # Infusion timer
        if p.infusion_timer > 0:
            p.infusion_timer -= dt
            if p.infusion_timer <= 0:
                p.infusion_type = None
        if p.dmg_timer > 0:
            p.dmg_timer -= dt
            if p.dmg_timer <= 0:
                p.dmg_mult = 1.0
        # Vendor proximity check
        self.show_vendor_hint = False
        if self.vendor:
            dist = (p.pos - self.vendor.pos).length()
            if dist < VENDOR_INTERACT_RANGE:
                self.show_vendor_hint = True
            self.vendor.interact_anim += dt
        vel = p.vel
        if p.dash_timer > 0:
            p.dash_timer -= dt
            if vel.length_squared() > 0:
                vel = vel.normalize() * DASH_SPEED
            else:
                vel = Vec(1, 0) * DASH_SPEED
            # dash trail
            if random.random() < 0.5:
                self.emit_dust(p.pos.x, p.pos.y + 8, 1)
        # walking animation
        if vel.length_squared() > 100:
            p.walk_anim += dt * 10
            if random.random() < 0.05:
                self.emit_dust(p.pos.x, p.pos.y + 14, 1)
        new_pos = p.pos + vel * dt
        test = Vec(new_pos.x, p.pos.y)
        if not self.dungeon.is_solid_at_px(test) and not self._circle_collides(test, p.radius):
            p.pos.x = test.x
        test = Vec(p.pos.x, new_pos.y)
        if not self.dungeon.is_solid_at_px(test) and not self._circle_collides(test, p.radius):
            p.pos.y = test.y
        p.pos.x = max(p.radius, min(MAP_W * TILE - p.radius, p.pos.x))
        p.pos.y = max(p.radius, min(MAP_H * TILE - p.radius, p.pos.y))
        self.dungeon.mark_seen_radius(p.pos)
        self.cam_x = int(p.pos.x - WIDTH / 2)
        self.cam_y = int(p.pos.y - HEIGHT / 2)
        self.cam_x = max(0, min(self.cam_x, MAP_W * TILE - WIDTH))
        self.cam_y = max(0, min(self.cam_y, MAP_H * TILE - HEIGHT))
        # Hazard pool damage
        ptx = int(p.pos.x // TILE)
        pty = int(p.pos.y // TILE)
        for ppx, ppy in self.dungeon.hazard_pools:
            if abs(ptx - ppx) <= 1 and abs(pty - ppy) <= 1:
                pool_center = Vec(ppx * TILE + TILE / 2, ppy * TILE + TILE / 2)
                if (pool_center - p.pos).length() < TILE * 1.2:
                    if p.iframes <= 0:
                        hazard = BIOME_HAZARD.get(self.current_biome, "poison")
                        dmg_rate = 3 if hazard == "lava" else 2
                        p.hp -= max(1, int(dmg_rate * dt * 10))
                        if random.random() < 0.3:
                            hcol = C_LAVA if hazard == "lava" else C_ICE if hazard == "ice" else C_POISON
                            self.emit_particles(p.pos.x, p.pos.y, 2, hcol, speed=20, life=0.4, gravity=-40)

        # Portal collision
        for ptx, pty, dest_biome in self.dungeon.portal_positions:
            portal_pos = Vec(ptx * TILE + TILE / 2, pty * TILE + TILE / 2)
            if (portal_pos - p.pos).length() < 24:
                self.next_level(dest_biome)
                break

    def _circle_collides(self, pos: Vec, radius: int) -> bool:
        for ang in (0, math.pi * 0.5, math.pi, math.pi * 1.5):
            pt = Vec(pos.x + math.cos(ang) * radius, pos.y + math.sin(ang) * radius)
            if self.dungeon.is_solid_at_px(pt):
                return True
        return False

    def update_enemies(self, dt: float):
        p = self.player
        for e in self.enemies:
            e.mult_speed = 1.0
            e.mult_damage = 1.0
            e.mult_taken = 1.0
        for e in self.enemies:
            if isinstance(e, Elite) and e.alive:
                e.aura_pulse += dt * 2.0
                aura = AURAS[e.aura]
                for m in self.enemies:
                    if m is e or not m.alive:
                        continue
                    if (m.pos - e.pos).length() <= e.aura_radius:
                        m.mult_speed *= aura["speed"]
                        m.mult_damage *= aura["damage"]
                        m.mult_taken *= aura["taken"]
        for e in self.enemies:
            if not e.alive:
                continue
            e.hit_flash = max(0.0, e.hit_flash - dt)
            # Treasure goblin: flee from player, drop loot
            if isinstance(e, TreasureGoblin) and e.alive:
                e.portal_timer -= dt
                if e.portal_timer <= 0:
                    e.alive = False
                    if self.treasure_goblin is e:
                        self.treasure_goblin = None
                    self.emit_particles(e.pos.x, e.pos.y, 20, C_GOLD, speed=80, life=0.6, gravity=-30)
                    self.add_floating_text(e.pos.x, e.pos.y - 20, "ESCAPED!", (200, 180, 60), 1.2)
                    continue
                # Flee from player — with wall avoidance
                flee_dir = (e.pos - p.pos)
                if flee_dir.length_squared() > 0:
                    flee_dir = flee_dir.normalize()
                else:
                    flee_dir = Vec(1, 0)
                # Wall avoidance: probe ahead and to sides, redirect if blocked
                probe_dist = TILE * 1.5
                probe_ahead = e.pos + flee_dir * probe_dist
                if self.dungeon.is_solid_at_px(probe_ahead):
                    # Try perpendicular directions to find open path
                    perp1 = Vec(-flee_dir.y, flee_dir.x)
                    perp2 = Vec(flee_dir.y, -flee_dir.x)
                    p1_ok = not self.dungeon.is_solid_at_px(e.pos + perp1 * probe_dist)
                    p2_ok = not self.dungeon.is_solid_at_px(e.pos + perp2 * probe_dist)
                    if p1_ok and p2_ok:
                        flee_dir = random.choice([perp1, perp2])
                    elif p1_ok:
                        flee_dir = perp1
                    elif p2_ok:
                        flee_dir = perp2
                    else:
                        # Fully blocked, try random direction
                        ang = random.uniform(0, math.tau)
                        flee_dir = Vec(math.cos(ang), math.sin(ang))
                jitter = Vec(random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3))
                acc = (flee_dir + jitter).normalize() * (e.speed * 1.1)
                e.vel += (acc - e.vel) * 0.2
                # Drop loot periodically
                e.loot_drop_timer -= dt
                if e.loot_drop_timer <= 0:
                    e.loot_drop_timer = GOBLIN_LOOT_INTERVAL
                    drop_pos = self._safe_loot_pos(e.pos)
                    self.loots.append(Loot(pos=drop_pos, gold=random.randint(3, 10)))
                    self.emit_particles(e.pos.x, e.pos.y, 3, C_GOLD, speed=30, life=0.3, gravity=-20)
                # Wall collision with sliding
                new_epos = e.pos + e.vel * dt
                test_x = Vec(new_epos.x, e.pos.y)
                if not self._circle_collides(test_x, e.radius):
                    e.pos.x = test_x.x
                else:
                    e.vel.x *= -0.5  # bounce off instead of stop
                test_y = Vec(e.pos.x, new_epos.y)
                if not self._circle_collides(test_y, e.radius):
                    e.pos.y = test_y.y
                else:
                    e.vel.y = 0
                e.pos.x = max(e.radius, min(MAP_W * TILE - e.radius, e.pos.x))
                e.pos.y = max(e.radius, min(MAP_H * TILE - e.radius, e.pos.y))
                if e.hp <= 0 and e.alive:
                    e.alive = False
                    self.on_enemy_dead(e)
                continue
            desired = (p.pos - e.pos)
            dist = desired.length() or 0.0001
            desired = desired / dist
            jitter = Vec(random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2))
            acc = (desired + jitter).normalize() * (e.speed * e.mult_speed)
            e.vel += (acc - e.vel) * 0.1
            new_epos = e.pos + e.vel * dt
            # axis-separated wall collision with wall sliding
            test_x = Vec(new_epos.x, e.pos.y)
            if not self._circle_collides(test_x, e.radius):
                e.pos.x = test_x.x
            else:
                e.vel.x = 0
            test_y = Vec(e.pos.x, new_epos.y)
            if not self._circle_collides(test_y, e.radius):
                e.pos.y = test_y.y
            else:
                e.vel.y = 0
            # Push away from nearby walls to prevent sticking
            push = Vec(0, 0)
            for ang_i in range(8):
                ang = ang_i * math.pi / 4
                probe = Vec(e.pos.x + math.cos(ang) * (e.radius + 2),
                            e.pos.y + math.sin(ang) * (e.radius + 2))
                if self.dungeon.is_solid_at_px(probe):
                    push.x -= math.cos(ang)
                    push.y -= math.sin(ang)
            if push.length_squared() > 0:
                push = push.normalize() * 60
                e.pos.x += push.x * dt
                e.pos.y += push.y * dt
            # clamp to world bounds
            e.pos.x = max(e.radius, min(MAP_W * TILE - e.radius, e.pos.x))
            e.pos.y = max(e.radius, min(MAP_H * TILE - e.radius, e.pos.y))
            # spitter ranged attack
            if e.kind == 3 and e.alive:
                e.shot_cd -= dt
                if e.shot_cd <= 0:
                    dirv = (p.pos - e.pos)
                    if dirv.length_squared() > 0:
                        dirv = dirv.normalize()
                        pr = Projectile(pos=e.pos + dirv * 14, vel=dirv * 320,
                                        dmg=e.roll_damage(), ttl=1.6, radius=4, pierce=1, hostile=True)
                        self.projectiles.append(pr)
                        self.emit_particles(e.pos.x, e.pos.y, 3, (200, 80, 80), speed=30, life=0.3, gravity=0)
                    e.shot_cd = random.uniform(1.2, 2.0)
            # Boss shooting
            if isinstance(e, Boss):
                e.shot_cd -= dt
                if e.shot_cd <= 0:
                    dirv = (p.pos - e.pos)
                    if dirv.length_squared() > 0:
                        dirv = dirv.normalize()
                        pr = Projectile(pos=e.pos + dirv * 18, vel=dirv * BOSS_PROJ_SPEED,
                                        dmg=e.roll_damage(), ttl=2.0, radius=5, pierce=1, hostile=True)
                        self.projectiles.append(pr)
                        self.emit_particles(e.pos.x, e.pos.y, 6, C_FIRE, speed=50, life=0.4, gravity=0)
                        self.add_screen_shake(3)
                    e.shot_cd = random.uniform(*BOSS_SHOT_CD)
            # Touch damage
            if (e.pos - p.pos).length() < e.radius + p.radius and p.iframes <= 0:
                if random.random() < 0.02:
                    # Dodge check
                    if random.random() * 100 < p.calc_dodge_chance():
                        self.add_floating_text(p.pos.x, p.pos.y - 20, "DODGE!", (140, 255, 140), 0.8)
                    else:
                        dmg = e.roll_damage()
                        if p.shield > 0:
                            absorb = min(p.shield, dmg)
                            p.shield -= absorb
                            dmg -= absorb
                        if dmg > 0:
                            p.hp -= dmg
                            self.add_floating_text(p.pos.x, p.pos.y - 20, f"-{dmg}", (255, 60, 60), 1.2)
                            self.add_screen_shake(4)
                            self.emit_blood(p.pos.x, p.pos.y, 6)
                            self.play_sound("hurt")
                    kb = (p.pos - e.pos).normalize() * 150
                    p.pos += kb * dt
            e.knockback = max(0.0, e.knockback - 200 * dt)
            e.vel *= 0.98
            if e.hp <= 0 and e.alive:
                e.alive = False
                self.on_enemy_dead(e)
        self.enemies = [e for e in self.enemies if e.alive or random.random() > 0.01]

    def update_projectiles(self, dt: float):
        for pr in self.projectiles:
            pr.ttl -= dt
            pr.pos += pr.vel * dt
            if pr.is_arrow:
                pr.angle = math.atan2(pr.vel.y, pr.vel.x)
            pr.trail_timer += dt
            # particle trail
            if pr.trail_timer > 0.03:
                pr.trail_timer = 0.0
                if pr.hostile:
                    self.emit_particles(pr.pos.x, pr.pos.y, 1, (200, 80, 70), speed=15, life=0.2, size=1.5, gravity=0)
                else:
                    col = (100, 160, 255) if pr.radius <= BASIC_RADIUS else (160, 120, 255)
                    self.emit_particles(pr.pos.x, pr.pos.y, 1, col, speed=15, life=0.2, size=1.5, gravity=0)
            if self.dungeon.is_solid_at_px(pr.pos):
                pr.ttl = 0
                self.emit_sparks(pr.pos.x, pr.pos.y, 4)
                continue
            if pr.hostile:
                if (self.player.pos - pr.pos).length() < self.player.radius + pr.radius and self.player.iframes <= 0:
                    # Dodge check
                    if random.random() * 100 < self.player.calc_dodge_chance():
                        self.add_floating_text(self.player.pos.x, self.player.pos.y - 20, "DODGE!", (140, 255, 140), 0.8)
                        pr.ttl = 0
                        continue
                    dmg = pr.dmg
                    if self.player.shield > 0:
                        absorb = min(self.player.shield, dmg)
                        self.player.shield -= absorb
                        dmg -= absorb
                    if dmg > 0:
                        self.player.hp -= dmg
                        self.player.iframes = max(self.player.iframes, 0.12)
                        self.add_floating_text(self.player.pos.x, self.player.pos.y - 20, f"-{dmg}", (255, 60, 60))
                        self.add_screen_shake(3)
                        self.emit_blood(self.player.pos.x, self.player.pos.y, 4)
                        self.play_sound("hurt")
                    pr.ttl = 0
                    continue
            else:
                for e in self.enemies:
                    if not e.alive:
                        continue
                    if (e.pos - pr.pos).length() < e.radius + pr.radius:
                        damage = max(1, int(pr.dmg * e.mult_taken))
                        # Elemental infusion effects
                        if pr.infusion == "fire":
                            damage = int(damage * 1.35)
                            self.emit_fire(e.pos.x, e.pos.y, 8)
                        elif pr.infusion == "ice":
                            e.vel *= 0.3
                            e.mult_speed *= 0.5
                            self.emit_particles(e.pos.x, e.pos.y, 6, C_ICE, speed=40, life=0.5, gravity=-20)
                        elif pr.infusion == "lightning":
                            damage = int(damage * 1.15)
                            # Chain lightning to one nearby enemy
                            for nearby in self.enemies:
                                if nearby is e or not nearby.alive:
                                    continue
                                if (nearby.pos - e.pos).length() < 150:
                                    chain_dmg = max(1, damage // 3)
                                    nearby.hp -= chain_dmg
                                    nearby.hit_flash = 0.1
                                    self.add_floating_text(nearby.pos.x, nearby.pos.y - 10,
                                                           str(chain_dmg), C_LIGHTNING, 0.9)
                                    self.lightning_chains.append((
                                        Vec(e.pos.x, e.pos.y),
                                        Vec(nearby.pos.x, nearby.pos.y), 0.2))
                                    self.emit_particles(nearby.pos.x, nearby.pos.y, 4,
                                                        C_LIGHTNING, speed=50, life=0.3, gravity=0)
                                    break
                        e.hp -= damage
                        e.knockback = 200
                        e.vel += (e.pos - pr.pos).normalize() * 300
                        e.hit_flash = 0.12
                        dmg_col = INFUSION_COLORS.get(pr.infusion, C_GOLD if damage > 15 else (220, 220, 220))
                        self.add_floating_text(e.pos.x, e.pos.y - e.radius - 8,
                                               str(damage), dmg_col,
                                               scale=1.3 if damage > 20 else 1.0)
                        self.emit_blood(e.pos.x, e.pos.y, 4)
                        self.play_sound(f"hit_{self._creature_sound_name(e)}")
                        # Life steal
                        ls = self.player.calc_life_steal()
                        if ls > 0:
                            heal = max(1, int(damage * ls / 100))
                            self.player.hp = min(self.player.max_hp(), self.player.hp + heal)
                        if pr.infusion == "lightning":
                            self.play_sound("zap")
                        if damage > 15:
                            self.add_screen_shake(2)
                        pr.pierce -= 1
                        if pr.pierce <= 0:
                            pr.ttl = 0
                            break
        # Projectile-chest collision (player projectiles only)
        for pr in self.projectiles:
            if pr.hostile or pr.ttl <= 0:
                continue
            for chest in self.chests:
                if not chest.alive:
                    continue
                if (chest.pos - pr.pos).length() < 20 + pr.radius:
                    chest.hp -= 1
                    chest.hit_flash = 0.15
                    self.emit_sparks(chest.pos.x, chest.pos.y, 5)
                    self.add_screen_shake(1)
                    pr.pierce -= 1
                    if pr.pierce <= 0:
                        pr.ttl = 0
                    if chest.hp <= 0:
                        chest.alive = False
                        self._on_chest_broken(chest)
                    break

        # Projectile-crate collision (player projectiles only)
        for pr in self.projectiles:
            if pr.hostile or pr.ttl <= 0:
                continue
            for crate in self.crates:
                if not crate.alive:
                    continue
                if (crate.pos - pr.pos).length() < 20 + pr.radius:
                    crate.hp -= 1
                    crate.hit_flash = 0.12
                    self.emit_sparks(crate.pos.x, crate.pos.y, 3)
                    pr.pierce -= 1
                    if pr.pierce <= 0:
                        pr.ttl = 0
                    if crate.hp <= 0:
                        crate.alive = False
                        self._on_crate_broken(crate)
                    break

        self.projectiles = [pr for pr in self.projectiles if pr.ttl > 0]

    def update_loot(self, dt: float):
        for l in self.loots:
            l.ttl -= dt
            l.bob_phase += dt * 3.0
            if (l.pos - self.player.pos).length() < 24:
                if l.gold:
                    self.player.gold += l.gold
                    self.add_floating_text(l.pos.x, l.pos.y - 10, f"+{l.gold}g", C_GOLD, 0.8)
                    self.play_sound("gold")
                if l.potion_hp:
                    self.player.potions_hp += 1
                    self.play_sound("pickup")
                if l.potion_mana:
                    self.player.potions_mana += 1
                    self.play_sound("pickup")
                if l.weapon:
                    wc = l.weapon.get_color()
                    # Auto-equip if better, otherwise add to inventory
                    old_avg = (self.player.weapon.dmg_min + self.player.weapon.dmg_max) / 2
                    new_avg = (l.weapon.dmg_min + l.weapon.dmg_max) / 2
                    if new_avg > old_avg:
                        # Stash old weapon in inventory
                        if len(self.player.inventory) < INV_COLS * INV_ROWS:
                            self.player.inventory.append(self.player.weapon)
                        self.player.weapon = l.weapon
                        self.add_floating_text(l.pos.x, l.pos.y - 10, l.weapon.name, wc, 1.5)
                    else:
                        if len(self.player.inventory) < INV_COLS * INV_ROWS:
                            self.player.inventory.append(l.weapon)
                            self.add_floating_text(l.pos.x, l.pos.y - 10, f"[Inv] {l.weapon.name}", wc, 1.2)
                        else:
                            self.add_floating_text(l.pos.x, l.pos.y - 10, "Inventory Full!", (200, 60, 60), 1.0)
                    self.play_sound("pickup")
                if l.dmg_boost:
                    self.player.dmg_mult = DMG_BOOST_MULT
                    self.player.dmg_timer = DMG_BOOST_TIME
                    self.add_floating_text(l.pos.x, l.pos.y - 10, "POWER UP!", (255, 160, 40), 1.3)
                    self.emit_particles(l.pos.x, l.pos.y, 12, C_FIRE_BRIGHT, speed=60, life=0.6, gravity=-40)
                if l.shield_boost:
                    self.player.shield = max(self.player.shield, SHIELD_POINTS)
                    self.add_floating_text(l.pos.x, l.pos.y - 10, "SHIELD!", C_ICE, 1.3)
                    self.emit_particles(l.pos.x, l.pos.y, 12, C_ICE, speed=60, life=0.6, gravity=-40)
                if l.infusion:
                    self.player.infusion_type = l.infusion
                    self.player.infusion_timer = INFUSION_DURATION
                    icol = INFUSION_COLORS[l.infusion]
                    self.add_floating_text(l.pos.x, l.pos.y - 10,
                                           f"{l.infusion.upper()} ARROWS!", icol, 1.3)
                    self.emit_particles(l.pos.x, l.pos.y, 15, icol, speed=80, life=0.7, gravity=-30)
                    self.play_sound("infusion")
                self.emit_sparks(l.pos.x, l.pos.y, 3)
                l.ttl = 0
        self.loots = [l for l in self.loots if l.ttl > 0]

    def on_enemy_dead(self, e: Enemy):
        self.kills += 1
        old_level = self.player.level
        self.player.xp += 6 + self.wave
        while self.player.xp >= self.player.xp_to_next:
            self.player.xp -= self.player.xp_to_next
            self.player.level += 1
            self.player.xp_to_next = int(self.player.xp_to_next * 1.35)
            self.player.hp = min(self.player.max_hp(), self.player.hp + 30)
            self.player.mana = min(self.player.max_mana(), self.player.mana + 20)
            self.player.stat_points += STAT_POINTS_PER_LEVEL
            self.player.skill_points += SKILL_POINTS_PER_LEVEL
        if self.player.level > old_level:
            self.player.levelup_flash = 2.0
            self.add_floating_text(self.player.pos.x, self.player.pos.y - 30, "LEVEL UP!", C_GOLD, 1.5)
            self.emit_particles(self.player.pos.x, self.player.pos.y, 25, C_GOLD, speed=100, life=1.0, gravity=-50)
            self.add_screen_shake(5)
            self.play_sound("levelup")

        # Treasure goblin: massive loot explosion
        if isinstance(e, TreasureGoblin):
            if self.treasure_goblin is e:
                self.treasure_goblin = None
            self.emit_death_burst(e.pos.x, e.pos.y, C_GOLD, 50)
            self.add_screen_shake(8)
            self.add_floating_text(e.pos.x, e.pos.y - 30, "JACKPOT!", C_GOLD, 2.0)
            self.play_sound("jackpot")
            for _ in range(10):
                self.loots.append(Loot(pos=self._safe_loot_pos(e.pos, 40), gold=random.randint(12, 35)))
            self.loots.append(Loot(pos=self._safe_loot_pos(e.pos), dmg_boost=True))
            self.loots.append(Loot(pos=self._safe_loot_pos(e.pos), shield_boost=True))
            # Guaranteed infusion drop
            inf = random.choice(INFUSION_TYPES)
            self.loots.append(Loot(pos=self._safe_loot_pos(e.pos), infusion=inf))
            if random.random() < 0.5:
                self.loots.append(Loot(pos=self._safe_loot_pos(e.pos), potion_hp=True))
            # Goblin weapon drops: 2-3 weapons, magic to rare range
            for gi in range(random.randint(2, 3)):
                gob_rarity = random.choice([RARITY_MAGIC, RARITY_MAGIC, RARITY_RARE])
                self.loots.append(Loot(pos=self._safe_loot_pos(e.pos, 35),
                                       weapon=generate_weapon(self.current_level, gob_rarity)))
            self.corpses.append(Corpse(x=e.pos.x, y=e.pos.y, radius=e.radius, kind=e.kind,
                                       color=C_GOLD, is_boss=False, is_elite=False))
            return

        # death effects
        death_color = (180, 60, 60)
        if isinstance(e, Elite):
            death_color = AURAS[e.aura]["color"]
            self.emit_death_burst(e.pos.x, e.pos.y, death_color, 30)
            self.add_screen_shake(6)
        elif isinstance(e, Boss):
            self.emit_death_burst(e.pos.x, e.pos.y, (255, 100, 40), 50)
            self.add_screen_shake(15)
            self.add_floating_text(e.pos.x, e.pos.y - 30, "BOSS SLAIN!", (255, 200, 60), 2.0)
        else:
            self.emit_death_burst(e.pos.x, e.pos.y, death_color, 15)
        self.play_sound(f"death_{self._creature_sound_name(e)}")

        # corpse
        self.corpses.append(Corpse(x=e.pos.x, y=e.pos.y, radius=e.radius, kind=e.kind,
                                   color=death_color, is_boss=isinstance(e, Boss),
                                   is_elite=isinstance(e, Elite)))

        drops: List[Loot] = []
        sp = lambda: self._safe_loot_pos(e.pos)
        if random.random() < 0.9:
            drops.append(Loot(pos=sp(), gold=random.randint(*GOLD_DROP)))
        if random.random() < POTION_DROP_CHANCE:
            potion = random.choice(["hp", "mana"])
            drops.append(Loot(pos=sp(), potion_hp=(potion == "hp"), potion_mana=(potion == "mana")))
        if random.random() < LOOT_DROP_CHANCE:
            # Tiered drop system:
            # Normal monsters: normal or magic (occasional rare at high depth)
            # Elites: magic-rare, small chance unique
            # Bosses: rare-unique, small chance set
            force = None
            if isinstance(e, Boss):
                roll = random.random()
                if roll < 0.10:
                    force = RARITY_SET
                elif roll < 0.35:
                    force = RARITY_UNIQUE
                else:
                    force = RARITY_RARE
            elif isinstance(e, Elite):
                roll = random.random()
                if roll < 0.05:
                    force = RARITY_UNIQUE
                elif roll < 0.40:
                    force = RARITY_RARE
                else:
                    force = RARITY_MAGIC
            else:
                # Regular monsters: mostly normal/magic
                roll = random.random()
                if roll < 0.03 + self.current_level * 0.005:
                    force = RARITY_RARE
                elif roll < 0.35:
                    force = RARITY_MAGIC
                else:
                    force = RARITY_NORMAL
            drops.append(Loot(pos=sp(), weapon=generate_weapon(self.current_level, force)))
        if random.random() < DMG_PICKUP_DROP_CHANCE:
            drops.append(Loot(pos=sp(), dmg_boost=True))
        if random.random() < SHIELD_PICKUP_DROP_CHANCE:
            drops.append(Loot(pos=sp(), shield_boost=True))
        if random.random() < INFUSION_DROP_CHANCE:
            drops.append(Loot(pos=sp(), infusion=random.choice(INFUSION_TYPES)))
        if isinstance(e, Elite):
            drops.append(Loot(pos=sp(), gold=random.randint(15, 35)))
            if random.random() < 0.5:
                drops.append(Loot(pos=sp(), dmg_boost=True))
            else:
                drops.append(Loot(pos=sp(), shield_boost=True))
            # Elites always drop at least magic gear
            if not any(d.weapon for d in drops):
                elite_rarity = RARITY_MAGIC if random.random() < 0.6 else RARITY_RARE
                drops.append(Loot(pos=self._safe_loot_pos(e.pos, 15),
                                  weapon=generate_weapon(self.current_level, elite_rarity)))
        if isinstance(e, Boss):
            # Bosses always drop 2 weapons: one rare+, one magic+
            drops.append(Loot(pos=self._safe_loot_pos(e.pos, 30),
                              weapon=generate_weapon(self.current_level,
                                  RARITY_UNIQUE if random.random() < 0.25 else RARITY_RARE)))
            drops.append(Loot(pos=self._safe_loot_pos(e.pos, 30),
                              weapon=generate_weapon(self.current_level, RARITY_MAGIC)))
            drops.append(Loot(pos=sp(), gold=random.randint(40, 100)))
        self.loots.extend(drops)

    def update_spawning(self, dt: float):
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            did_pack = False
            if random.random() < ELITE_PACK_CHANCE and len(self.enemies) < MAX_ACTIVE_ENEMIES:
                self.spawn_elite_pack()
                did_pack = True
            to_spawn = min(2, MAX_ACTIVE_ENEMIES - len(self.enemies))
            if not did_pack:
                for _ in range(max(0, to_spawn)):
                    self.spawn_enemy(near_player=True)
            else:
                if random.random() < 0.5 and len(self.enemies) < MAX_ACTIVE_ENEMIES:
                    self.spawn_enemy(near_player=True)
            if random.random() < PICKUP_SPAWN_CHANCE:
                self.spawn_pickup_near_player()
            # Treasure goblin chance
            if self.treasure_goblin is None and random.random() < GOBLIN_SPAWN_CHANCE:
                self.spawn_treasure_goblin()
            self.wave += 1
            self.spawn_timer = SPAWN_INTERVAL
            self.spawn_boss()

    def update_particles(self, dt: float):
        alive = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0:
                continue
            p.vy += p.gravity * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            alive.append(p)
        self.particles = alive

    def update_floating_texts(self, dt: float):
        alive = []
        for ft in self.floating_texts:
            ft.life -= dt
            if ft.life <= 0:
                continue
            ft.y += ft.vy * dt
            alive.append(ft)
        self.floating_texts = alive

    def update_corpses(self, dt: float):
        alive = []
        for c in self.corpses:
            c.life -= dt
            if c.life > 0:
                alive.append(c)
        self.corpses = alive

    def update_blood_stains(self, dt: float):
        alive = []
        for bx, by, life in self.dungeon.blood_stains:
            life -= dt * 0.1
            if life > 0:
                alive.append((bx, by, life))
        self.dungeon.blood_stains = alive

    def update_screen_shake(self, dt: float):
        if self.shake_intensity > 0.1:
            self.shake_x = random.uniform(-self.shake_intensity, self.shake_intensity)
            self.shake_y = random.uniform(-self.shake_intensity, self.shake_intensity)
            self.shake_intensity -= self.shake_intensity * SCREEN_SHAKE_DECAY * dt
        else:
            self.shake_x = 0
            self.shake_y = 0
            self.shake_intensity = 0

    # ---- Level management ----
    def next_level(self, dest_biome: Optional[str] = None):
        self.current_level += 1
        if dest_biome:
            self.current_biome = dest_biome
        self.dungeon = Dungeon(level=self.current_level, biome=self.current_biome)
        rx, ry = self.dungeon.center(self.dungeon.rooms[0]) if self.dungeon.rooms else (MAP_W // 2, MAP_H // 2)
        self.player.pos = Vec(rx * TILE + TILE / 2, ry * TILE + TILE / 2)
        self.enemies.clear()
        self.projectiles.clear()
        self.loots.clear()
        self.particles.clear()
        self.floating_texts.clear()
        self.corpses.clear()
        self.chests.clear()
        self.crates.clear()
        self.treasure_goblin = None
        self.lightning_chains.clear()
        self._build_texture_cache(self.current_biome)
        self._spawn_chests()
        self._spawn_crates()
        self.wave = 1
        self.spawn_timer = SPAWN_INTERVAL
        self.dungeon.mark_seen_radius(self.player.pos)
        self.boss_spawned = False
        self._spawn_vendor()
        self.play_sound("portal")
        # Announce biome
        biome_name = BIOME_NAMES.get(self.current_biome, self.current_biome)
        self.add_floating_text(self.player.pos.x, self.player.pos.y - 40,
                               f"Entering {biome_name} - Depth {self.current_level}",
                               BIOME_PORTAL_COLORS.get(self.current_biome, C_GOLD), 1.5)

    # ======================= RENDERING =======================
    def draw(self):
        s = self.screen
        s.fill(C_GOTHIC_BG)
        ox = int(self.shake_x)
        oy = int(self.shake_y)

        self._draw_tiles(s, ox, oy)
        self._draw_blood_stains(s, ox, oy)
        self._draw_hazard_pools(s, ox, oy)
        self._draw_scenery(s, ox, oy)
        self._draw_portals(s, ox, oy)
        self._draw_torches(s, ox, oy)
        self._draw_corpses(s, ox, oy)
        self._draw_chests(s, ox, oy)
        self._draw_crates(s, ox, oy)
        self._draw_vendor(s, ox, oy)
        self._draw_loot(s, ox, oy)
        self._draw_projectiles(s, ox, oy)
        self._draw_enemies(s, ox, oy)
        self._draw_player(s, ox, oy)
        self._draw_particles(s, ox, oy)
        self._draw_floating_texts(s, ox, oy)
        self._draw_lighting(s, ox, oy)
        self._draw_ui(s)
        self._draw_reticle(s)
        self._draw_minimap(s)
        pygame.display.flip()

    def _tile_in_view(self, tx: int, ty: int) -> bool:
        return ((self.cam_x // TILE) - 2 <= tx <= ((self.cam_x + WIDTH) // TILE) + 2 and
                (self.cam_y // TILE) - 2 <= ty <= ((self.cam_y + HEIGHT) // TILE) + 2)

    def _draw_tiles(self, s, ox, oy):
        start_tx = max(0, self.cam_x // TILE)
        end_tx = min(MAP_W - 1, (self.cam_x + WIDTH) // TILE + 1)
        start_ty = max(0, self.cam_y // TILE)
        end_ty = min(MAP_H - 1, (self.cam_y + HEIGHT) // TILE + 1)
        for tx in range(start_tx, end_tx + 1):
            for ty in range(start_ty, end_ty + 1):
                px = tx * TILE - self.cam_x + ox
                py = ty * TILE - self.cam_y + oy
                seen = self.dungeon.seen[tx][ty]
                variant = self.dungeon.tile_variants[tx][ty]
                if self.dungeon.tiles[tx][ty] == WALL:
                    if seen:
                        s.blit(self.wall_tiles[variant], (px, py))
                    else:
                        s.blit(self.unseen_wall, (px, py))
                else:
                    if seen:
                        s.blit(self.floor_tiles[variant], (px, py))
                    else:
                        s.blit(self.unseen_floor, (px, py))

    def _draw_blood_stains(self, s, ox, oy):
        for bx, by, life in self.dungeon.blood_stains:
            sx = int(bx - self.cam_x + ox)
            sy = int(by - self.cam_y + oy)
            if -20 < sx < WIDTH + 20 and -20 < sy < HEIGHT + 20:
                alpha = min(1.0, life)
                r = int(80 * alpha)
                pygame.draw.circle(s, (r, 5, 5), (sx, sy), int(6 + (1 - alpha) * 4))

    def _draw_scenery(self, s, ox, oy):
        for (tx, ty, t) in self.dungeon.scenery:
            if not self._tile_in_view(tx, ty):
                continue
            if not self.dungeon.seen[tx][ty]:
                continue
            px = tx * TILE - self.cam_x + ox
            py = ty * TILE - self.cam_y + oy
            # shadow
            pygame.draw.ellipse(s, (10, 8, 12), (px + 4, py + TILE - 8, TILE - 8, 6))
            if t == 'pillar':
                s.blit(self.pillar_surf, (px, py))
            elif t == 'stalagmite':
                s.blit(self.stalagmite_surf, (px, py))
            elif t == 'rock':
                s.blit(self.rock_surf, (px, py))
            elif t == 'ice_crystal':
                s.blit(self.ice_crystal_surf, (px, py))
            elif t == 'mushroom':
                s.blit(self.mushroom_surf, (px, py))
            elif t == 'crate':
                # Scenery crates handled by _draw_crates; skip here
                pass

    def _draw_portals(self, s, ox, oy):
        self.portal_angle += 0.05
        for ptx, pty, dest_biome in self.dungeon.portal_positions:
            if not self._tile_in_view(ptx, pty):
                continue
            px = ptx * TILE - self.cam_x + ox + TILE // 2
            py = pty * TILE - self.cam_y + oy + TILE // 2
            pcol = BIOME_PORTAL_COLORS.get(dest_biome, (200, 200, 100))
            # Swirling portal with biome color
            for i in range(8):
                ang = self.portal_angle + i * (math.tau / 8)
                r = 17
                x = px + int(math.cos(ang) * r)
                y = py + int(math.sin(ang) * r)
                pulse = 0.6 + 0.4 * math.sin(self.game_time * 3 + i)
                col = (int(pcol[0] * pulse), int(pcol[1] * pulse), int(pcol[2] * pulse))
                pygame.draw.circle(s, col, (x, y), 4)
            # Center glow
            glow = 0.7 + 0.3 * math.sin(self.game_time * 2)
            center_col = (int(pcol[0] * 0.7 * glow), int(pcol[1] * 0.7 * glow), int(pcol[2] * 0.5 * glow))
            pygame.draw.circle(s, center_col, (px, py), 11)
            bright = (min(255, int(pcol[0] * glow)), min(255, int(pcol[1] * glow)), min(255, int(pcol[2] * 0.6 * glow)))
            pygame.draw.circle(s, bright, (px, py), 6)
            # Biome name label
            name = BIOME_NAMES.get(dest_biome, dest_biome)
            label = self.font.render(name, True, pcol)
            s.blit(label, (px - label.get_width() // 2, py - 30))

    def _draw_torches(self, s, ox, oy):
        for tx, ty in self.dungeon.torches:
            if not self._tile_in_view(tx, ty):
                continue
            if not self.dungeon.seen[tx][ty]:
                continue
            px = tx * TILE - self.cam_x + ox + TILE // 2
            py = ty * TILE - self.cam_y + oy + TILE // 2
            # torch base
            pygame.draw.rect(s, (90, 70, 40), (px - 3, py, 6, 11))
            # flame
            flicker = random.uniform(0.6, 1.0)
            fr = int(255 * flicker)
            fg = int(160 * flicker)
            fb = int(40 * flicker)
            pygame.draw.circle(s, (fr, fg, fb), (px, py - 3), 6)
            pygame.draw.circle(s, (255, min(255, fg + 60), fb + 20), (px, py - 6), 3)
            # emit occasional fire particles
            if random.random() < 0.15:
                self.emit_fire(px + self.cam_x - ox, py + self.cam_y - oy, 1)

    def _draw_corpses(self, s, ox, oy):
        for c in self.corpses:
            sx = int(c.x - self.cam_x + ox)
            sy = int(c.y - self.cam_y + oy)
            if -40 < sx < WIDTH + 40 and -40 < sy < HEIGHT + 40:
                alpha = min(1.0, c.life / 2.0)
                r = max(0, int(c.color[0] * alpha * 0.4))
                g = max(0, int(c.color[1] * alpha * 0.4))
                b = max(0, int(c.color[2] * alpha * 0.4))
                rad = int(c.radius * (0.8 + 0.2 * alpha))
                pygame.draw.circle(s, (r, g, b), (sx, sy), rad)

    def _draw_hazard_pools(self, s, ox, oy):
        hazard = BIOME_HAZARD.get(self.current_biome, "poison")
        for ppx, ppy in self.dungeon.hazard_pools:
            if not self._tile_in_view(ppx, ppy):
                continue
            if not self.dungeon.seen[ppx][ppy]:
                continue
            px = ppx * TILE - self.cam_x + ox + TILE // 2
            py = ppy * TILE - self.cam_y + oy + TILE // 2
            pulse = 0.6 + 0.4 * math.sin(self.game_time * 2 + ppx * 0.7)
            r = int(TILE * 0.8)
            pool_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            if hazard == "lava":
                pygame.draw.ellipse(pool_surf, (80, int(30 * pulse), 5, 140), (0, 4, r * 2, r * 2 - 8))
                pygame.draw.ellipse(pool_surf, (120, int(50 * pulse), 10, 100), (4, 8, r * 2 - 8, r * 2 - 16))
                bubble_col = (255, 120, 20)
            elif hazard == "ice":
                pygame.draw.ellipse(pool_surf, (20, int(60 * pulse), int(100 * pulse), 120), (0, 4, r * 2, r * 2 - 8))
                pygame.draw.ellipse(pool_surf, (40, int(80 * pulse), int(140 * pulse), 80), (4, 8, r * 2 - 8, r * 2 - 16))
                bubble_col = (140, 200, 255)
            else:  # poison
                pygame.draw.ellipse(pool_surf, (30, int(80 * pulse), 20, 120), (0, 4, r * 2, r * 2 - 8))
                pygame.draw.ellipse(pool_surf, (40, int(120 * pulse), 30, 80), (4, 8, r * 2 - 8, r * 2 - 16))
                bubble_col = (60, 180, 40)
            s.blit(pool_surf, (px - r, py - r))
            if random.random() < 0.12:
                bx = px + random.randint(-12, 12)
                by = py + random.randint(-8, 8)
                pygame.draw.circle(s, bubble_col, (bx, by), random.randint(2, 4))
            # Lava emits fire particles
            if hazard == "lava" and random.random() < 0.08:
                self.emit_fire(px + self.cam_x - ox + random.randint(-10, 10),
                               py + self.cam_y - oy + random.randint(-10, 10), 1)

    def _draw_chests(self, s, ox, oy):
        for chest in self.chests:
            if not chest.alive:
                continue
            cx = int(chest.pos.x - self.cam_x + ox)
            cy = int(chest.pos.y - self.cam_y + oy)
            if not (-TILE < cx < WIDTH + TILE and -TILE < cy < HEIGHT + TILE):
                continue
            # Shadow
            pygame.draw.ellipse(s, (8, 6, 10), (cx - 17, cy + 14, 34, 11))
            # Chest sprite
            if chest.hit_flash > 0:
                # Flash white on hit
                flash_surf = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
                flash_surf.fill((255, 255, 255, 180))
                s.blit(flash_surf, (cx - TILE // 2, cy - TILE // 2))
            else:
                surf = self.gold_chest_surf if chest.kind == "gold" else self.chest_surf
                s.blit(surf, (cx - TILE // 2, cy - TILE // 2))
            # HP pips
            for i in range(chest.hp):
                pip_x = cx - (CHEST_HP * 6) // 2 + i * 12
                pygame.draw.rect(s, (200, 180, 80), (pip_x, cy - TILE // 2 - 8, 8, 5))

    def _draw_crates(self, s, ox, oy):
        for crate in self.crates:
            if not crate.alive:
                continue
            cx = int(crate.pos.x - self.cam_x + ox)
            cy = int(crate.pos.y - self.cam_y + oy)
            if not (-TILE < cx < WIDTH + TILE and -TILE < cy < HEIGHT + TILE):
                continue
            # Shadow
            pygame.draw.ellipse(s, (10, 8, 12), (cx - 14, cy + 12, 28, 8))
            # Crate sprite (or flash)
            if crate.hit_flash > 0:
                flash_surf = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
                flash_surf.fill((255, 255, 255, 180))
                s.blit(flash_surf, (cx - TILE // 2, cy - TILE // 2))
            else:
                s.blit(self.crate_surf, (cx - TILE // 2, cy - TILE // 2))

    def _draw_vendor(self, s, ox, oy):
        """Draw the vendor NPC in the world."""
        if not self.vendor:
            return
        v = self.vendor
        vx = int(v.pos.x - self.cam_x + ox)
        vy = int(v.pos.y - self.cam_y + oy)
        if not (-50 < vx < WIDTH + 50 and -50 < vy < HEIGHT + 50):
            return
        t = v.interact_anim

        # Shadow
        pygame.draw.ellipse(s, (15, 12, 10), (vx - 18, vy + 12, 36, 10))

        # Body - hooded merchant figure
        # Robe (brown/dark)
        pygame.draw.polygon(s, (80, 60, 40), [(vx - 14, vy + 14), (vx + 14, vy + 14),
                                               (vx + 10, vy - 8), (vx - 10, vy - 8)])
        # Hood
        pygame.draw.circle(s, (70, 55, 35), (vx, vy - 14), 12)
        pygame.draw.circle(s, (50, 40, 25), (vx, vy - 14), 10)
        # Face shadow (mysterious)
        pygame.draw.circle(s, (30, 25, 18), (vx, vy - 12), 7)
        # Eyes (small glowing)
        eye_glow = int(180 + 40 * math.sin(t * 2.5))
        pygame.draw.circle(s, (eye_glow, eye_glow - 30, 0), (vx - 3, vy - 13), 2)
        pygame.draw.circle(s, (eye_glow, eye_glow - 30, 0), (vx + 3, vy - 13), 2)
        # Belt
        pygame.draw.line(s, (120, 100, 60), (vx - 10, vy - 2), (vx + 10, vy - 2), 2)
        # Gold pouch on belt
        pygame.draw.circle(s, (200, 170, 50), (vx + 8, vy - 1), 4)
        pygame.draw.circle(s, (160, 130, 30), (vx + 8, vy - 1), 4, 1)

        # Floating name
        name_txt = self.font.render(v.name, True, C_GOLD)
        s.blit(name_txt, (vx - name_txt.get_width() // 2, vy - 34))

        # Interaction prompt when near
        if self.show_vendor_hint:
            pulse = int(180 + 40 * math.sin(t * 3))
            hint_txt = self.font.render("[V] Trade", True, (pulse, pulse - 20, pulse // 2))
            s.blit(hint_txt, (vx - hint_txt.get_width() // 2, vy - 52))
            # Glow ring around vendor
            ring_r = int(20 + 3 * math.sin(t * 2))
            pygame.draw.circle(s, (80, 70, 40), (vx, vy), ring_r, 2)

    def _draw_loot(self, s, ox, oy):
        for l in self.loots:
            vx = int(l.pos.x - self.cam_x + ox)
            vy = int(l.pos.y - self.cam_y + oy + math.sin(l.bob_phase) * 4)
            if not (-20 < vx < WIDTH + 20 and -20 < vy < HEIGHT + 20):
                continue
            # glow under loot
            glow_alpha = int(30 + 15 * math.sin(l.bob_phase * 1.5))
            if l.weapon:
                wc = l.weapon.get_color()
                is_unique = l.weapon.rarity == RARITY_UNIQUE
                is_set = l.weapon.rarity == RARITY_SET
                # Unique/Set weapons get a pulsing golden aura
                if is_unique or is_set:
                    aura_pulse = 0.6 + 0.4 * math.sin(self.game_time * 4)
                    aura_r = 24 + int(4 * math.sin(self.game_time * 3))
                    ac = wc if is_unique else (0, 220, 0)
                    pygame.draw.circle(s, (int(ac[0] * 0.3 * aura_pulse),
                                           int(ac[1] * 0.3 * aura_pulse),
                                           int(ac[2] * 0.15 * aura_pulse)), (vx, vy), aura_r)
                    # Sparkle particles
                    for i in range(3):
                        ang = self.game_time * 2.5 + i * math.tau / 3
                        sx = vx + int(math.cos(ang) * 18)
                        sy = vy + int(math.sin(ang) * 14)
                        pygame.draw.circle(s, (255, 240, 150) if is_unique else (120, 255, 120),
                                           (sx, sy), 2)
                    # Column of light for uniques
                    if is_unique:
                        beam_alpha = int(40 * aura_pulse)
                        pygame.draw.line(s, (beam_alpha, beam_alpha - 5, 0),
                                         (vx, vy - 30), (vx, vy + 15), 2)
                glow_c = (min(255, wc[0]//2 + glow_alpha), min(255, wc[1]//2 + glow_alpha), min(255, wc[2]//2))
                pygame.draw.circle(s, glow_c, (vx, vy), 17)
                pygame.draw.rect(s, wc, (vx - 8, vy - 8, 16, 16), border_radius=3)
                pygame.draw.rect(s, (min(255, wc[0]+40), min(255, wc[1]+40), min(255, wc[2]+40)),
                                 (vx - 8, vy - 8, 16, 16), 1, border_radius=3)
                # Weapon name label with rarity color
                wlabel = self.font.render(l.weapon.name, True, wc)
                s.blit(wlabel, (vx - wlabel.get_width() // 2, vy - 22))
            elif l.potion_hp:
                pygame.draw.circle(s, (glow_alpha, 0, 0), (vx, vy), 14)
                pygame.draw.rect(s, (200, 40, 40), (vx - 7, vy - 7, 14, 14), border_radius=4)
                pygame.draw.rect(s, (255, 80, 80), (vx - 3, vy - 6, 6, 4))
            elif l.potion_mana:
                pygame.draw.circle(s, (0, 0, glow_alpha), (vx, vy), 14)
                pygame.draw.rect(s, (40, 80, 200), (vx - 7, vy - 7, 14, 14), border_radius=4)
                pygame.draw.rect(s, (80, 120, 255), (vx - 3, vy - 6, 6, 4))
            elif l.dmg_boost:
                pygame.draw.circle(s, (glow_alpha + 15, glow_alpha, 0), (vx, vy), 14)
                pygame.draw.circle(s, (250, 160, 40), (vx, vy), 10)
                pygame.draw.circle(s, (255, 220, 120), (vx, vy), 6)
                # pulsing rays
                for i in range(4):
                    ang = self.game_time * 2 + i * math.pi / 2
                    ex = vx + int(math.cos(ang) * 13)
                    ey = vy + int(math.sin(ang) * 13)
                    pygame.draw.line(s, (255, 200, 80), (vx, vy), (ex, ey), 2)
            elif l.shield_boost:
                pygame.draw.circle(s, (0, 0, glow_alpha + 10), (vx, vy), 14)
                pygame.draw.circle(s, (80, 200, 250), (vx, vy), 10)
                pygame.draw.circle(s, (180, 240, 255), (vx, vy), 6)
                for i in range(4):
                    ang = self.game_time * 2 + i * math.pi / 2
                    ex = vx + int(math.cos(ang) * 13)
                    ey = vy + int(math.sin(ang) * 13)
                    pygame.draw.line(s, (140, 220, 255), (vx, vy), (ex, ey), 2)
            elif l.infusion:
                icol = INFUSION_COLORS[l.infusion]
                pygame.draw.circle(s, (icol[0] // 3, icol[1] // 3, icol[2] // 3), (vx, vy), 16)
                pygame.draw.circle(s, icol, (vx, vy), 11)
                # Arrow symbol inside
                pygame.draw.line(s, (255, 255, 255), (vx - 5, vy), (vx + 5, vy), 2)
                pygame.draw.polygon(s, (255, 255, 255), [(vx + 5, vy), (vx + 2, vy - 3), (vx + 2, vy + 3)])
                # Pulsing ring
                ring_pulse = int(3 + 2 * math.sin(self.game_time * 4))
                pygame.draw.circle(s, icol, (vx, vy), 11 + ring_pulse, 2)
            elif l.gold:
                pygame.draw.circle(s, (glow_alpha + 10, glow_alpha + 5, 0), (vx, vy), 11)
                pygame.draw.circle(s, (255, 215, 0), (vx, vy), 7)
                pygame.draw.circle(s, (200, 170, 0), (vx, vy), 7, 1)

    def _draw_projectiles(self, s, ox, oy):
        for pr in self.projectiles:
            px = int(pr.pos.x - self.cam_x + ox)
            py = int(pr.pos.y - self.cam_y + oy)
            if not (-20 < px < WIDTH + 20 and -20 < py < HEIGHT + 20):
                continue
            if pr.hostile:
                pygame.draw.circle(s, (120, 30, 30), (px, py), pr.radius + 3)
                pygame.draw.circle(s, (255, 100, 110), (px, py), pr.radius)
                pygame.draw.circle(s, (255, 180, 180), (px, py), max(1, pr.radius - 2))
            elif pr.is_arrow:
                # Arrow shaft
                arrow_len = 14
                tail_x = px - int(math.cos(pr.angle) * arrow_len)
                tail_y = py - int(math.sin(pr.angle) * arrow_len)
                # Infusion color or default
                if pr.infusion:
                    icol = INFUSION_COLORS[pr.infusion]
                    shaft_col = (min(255, icol[0] // 2 + 70), min(255, icol[1] // 2 + 50), min(255, icol[2] // 2 + 40))
                else:
                    shaft_col = (160, 140, 110)
                pygame.draw.line(s, shaft_col, (tail_x, tail_y), (px, py), 2)
                # Arrowhead
                head_len = 7
                hx = px + int(math.cos(pr.angle) * head_len)
                hy = py + int(math.sin(pr.angle) * head_len)
                left_a = pr.angle + 2.6
                right_a = pr.angle - 2.6
                lx = px + int(math.cos(left_a) * 5)
                ly = py + int(math.sin(left_a) * 5)
                rx = px + int(math.cos(right_a) * 5)
                ry = py + int(math.sin(right_a) * 5)
                head_col = (200, 190, 170) if not pr.infusion else icol
                pygame.draw.polygon(s, head_col, [(hx, hy), (lx, ly), (rx, ry)])
                # Fletching
                fl = pr.angle + math.pi
                for fa in (fl + 0.4, fl - 0.4):
                    fx = tail_x + int(math.cos(fa) * 5)
                    fy = tail_y + int(math.sin(fa) * 5)
                    pygame.draw.line(s, (120, 100, 80), (tail_x, tail_y), (fx, fy), 1)
                # Infusion glow
                if pr.infusion:
                    pygame.draw.circle(s, (*icol, ), (px, py), pr.radius + 3, 2)
            else:
                pygame.draw.circle(s, (40, 60, 100), (px, py), pr.radius + 2)
                pygame.draw.circle(s, (140, 200, 255), (px, py), pr.radius)
                pygame.draw.circle(s, (220, 240, 255), (px, py), max(1, pr.radius - 1))
        # Draw lightning chains
        for start, end, life in self.lightning_chains:
            if life > 0:
                sx = int(start.x - self.cam_x + ox)
                sy = int(start.y - self.cam_y + oy)
                ex = int(end.x - self.cam_x + ox)
                ey = int(end.y - self.cam_y + oy)
                alpha = min(1.0, life / 0.15)
                col = (int(255 * alpha), int(255 * alpha), int(100 * alpha))
                # Jagged lightning line
                points = [(sx, sy)]
                dx, dy = ex - sx, ey - sy
                steps = max(3, int(math.sqrt(dx * dx + dy * dy) / 20))
                for i in range(1, steps):
                    t = i / steps
                    mx = int(sx + dx * t + random.randint(-8, 8))
                    my = int(sy + dy * t + random.randint(-8, 8))
                    points.append((mx, my))
                points.append((ex, ey))
                if len(points) >= 2:
                    pygame.draw.lines(s, col, False, points, 2)

    def _draw_enemies(self, s, ox, oy):
        for e in self.enemies:
            if not e.alive:
                continue
            self._draw_single_enemy(s, e, ox, oy)

    def _draw_single_enemy(self, s, e, ox, oy):
        ex = int(e.pos.x - self.cam_x + ox)
        ey = int(e.pos.y - self.cam_y + oy)
        if not (-40 < ex < WIDTH + 40 and -40 < ey < HEIGHT + 40):
            return
        ratio = max(0.0, min(1.0, e.hp / max(1, e.max_hp)))

        # Shadow
        pygame.draw.ellipse(s, (8, 6, 10), (ex - e.radius, ey + e.radius - 6, e.radius * 2, 11))

        # Aura ring for buffed minions
        if e.mult_speed > 1.0 or e.mult_damage > 1.0 or e.mult_taken < 1.0:
            pulse = 0.6 + 0.4 * math.sin(self.game_time * 4)
            ac = (int(180 * pulse), int(160 * pulse), int(220 * pulse))
            pygame.draw.circle(s, ac, (ex, ey), e.radius + 7, 3)

        # Elite aura effect
        if isinstance(e, Elite):
            aura_col = AURAS[e.aura]["color"]
            pulse = 0.5 + 0.5 * math.sin(e.aura_pulse)
            r = int(aura_col[0] * pulse * 0.5)
            g = int(aura_col[1] * pulse * 0.5)
            b = int(aura_col[2] * pulse * 0.5)
            pygame.draw.circle(s, (r, g, b), (ex, ey), e.radius + 14, 4)
            # Crown
            crown_col = (240, 200, 100)
            pts = [(ex - 14, ey - 22), (ex - 7, ey - 34), (ex - 1, ey - 22),
                   (ex + 1, ey - 22), (ex + 7, ey - 34), (ex + 14, ey - 22)]
            pygame.draw.polygon(s, crown_col, pts)
            pygame.draw.polygon(s, (200, 160, 60), pts, 1)

        # Body - demonic look based on kind
        if e.hit_flash > 0:
            body_col = (255, 255, 255)
        elif ratio > 0.66:
            body_col = (70, 160, 70)
        elif ratio > 0.33:
            body_col = (200, 170, 60)
        else:
            body_col = (190, 50, 50)

        if isinstance(e, Boss):
            # Boss: larger, more imposing
            pygame.draw.circle(s, (40, 15, 15), (ex, ey), e.radius + 3)
            pygame.draw.circle(s, body_col, (ex, ey), e.radius)
            pygame.draw.circle(s, (max(0, body_col[0] - 30), max(0, body_col[1] - 30), max(0, body_col[2] - 20)),
                               (ex, ey), e.radius - 6)
            # Demonic eyes
            pygame.draw.circle(s, (255, 60, 20), (ex - 12, ey - 8), 6)
            pygame.draw.circle(s, (255, 60, 20), (ex + 12, ey - 8), 6)
            pygame.draw.circle(s, (255, 220, 60), (ex - 12, ey - 8), 3)
            pygame.draw.circle(s, (255, 220, 60), (ex + 12, ey - 8), 3)
            # Crown
            pts = [(ex - 20, ey - 26), (ex - 10, ey - 42), (ex, ey - 26),
                   (ex + 10, ey - 42), (ex + 20, ey - 26)]
            pygame.draw.polygon(s, (240, 180, 60), pts)
            pygame.draw.polygon(s, (180, 130, 30), pts, 2)
            # Mouth
            pygame.draw.arc(s, (0, 0, 0), (ex - 12, ey + 4, 24, 14), 3.14, 6.28, 2)
        elif e.kind == 4:  # Treasure Goblin
            shimmer = 0.7 + 0.3 * math.sin(self.game_time * 8)
            gcol = (int(255 * shimmer), int(215 * shimmer), int(40 * shimmer))
            pygame.draw.circle(s, gcol, (ex, ey), e.radius)
            pygame.draw.circle(s, (200, 170, 30), (ex, ey), e.radius, 2)
            # Loot bag on back
            pygame.draw.circle(s, (180, 150, 50), (ex - 5, ey - 8), 8)
            pygame.draw.circle(s, (160, 130, 40), (ex - 5, ey - 8), 8, 1)
            pygame.draw.line(s, (140, 110, 40), (ex - 5, ey - 16), (ex - 5, ey - 10), 2)
            # Eyes (excited)
            pygame.draw.circle(s, (255, 255, 200), (ex - 3, ey - 2), 3)
            pygame.draw.circle(s, (255, 255, 200), (ex + 5, ey - 2), 3)
            pygame.draw.circle(s, (40, 20, 10), (ex - 3, ey - 2), 1)
            pygame.draw.circle(s, (40, 20, 10), (ex + 5, ey - 2), 1)
            # Timer arc
            if isinstance(e, TreasureGoblin):
                timer_frac = max(0, e.portal_timer / GOBLIN_DESPAWN_TIME)
                if timer_frac < 1.0:
                    pygame.draw.arc(s, C_GOLD, (ex - e.radius - 4, ey - e.radius - 4,
                                    (e.radius + 4) * 2, (e.radius + 4) * 2),
                                    0, math.tau * timer_frac, 2)
        else:
            # --- Kind 0: SKELETON - bony, pale, skull-shaped ---
            if e.kind == 0:
                bone_col = (220, 210, 180) if e.hit_flash <= 0 else (255, 255, 255)
                bone_dark = (180, 165, 130) if e.hit_flash <= 0 else (240, 240, 240)
                # Skull body (slightly oval)
                pygame.draw.ellipse(s, bone_dark, (ex - e.radius, ey - e.radius + 2,
                                    e.radius * 2, int(e.radius * 1.8)))
                pygame.draw.ellipse(s, bone_col, (ex - e.radius + 2, ey - e.radius + 3,
                                    e.radius * 2 - 4, int(e.radius * 1.8) - 4))
                # Eye sockets (dark holes)
                pygame.draw.circle(s, (15, 10, 10), (ex - 6, ey - 3), 5)
                pygame.draw.circle(s, (15, 10, 10), (ex + 6, ey - 3), 5)
                # Glowing red pupils
                glow = 0.7 + 0.3 * math.sin(self.game_time * 5)
                eye_r = int(200 * glow)
                pygame.draw.circle(s, (eye_r, 30, 20), (ex - 6, ey - 3), 2)
                pygame.draw.circle(s, (eye_r, 30, 20), (ex + 6, ey - 3), 2)
                # Nose hole
                pygame.draw.polygon(s, (15, 10, 10), [(ex, ey + 2), (ex - 2, ey + 5), (ex + 2, ey + 5)])
                # Jaw / teeth
                for tx in range(-7, 8, 3):
                    pygame.draw.rect(s, bone_col, (ex + tx, ey + 7, 2, 4))
                pygame.draw.line(s, bone_dark, (ex - 8, ey + 7), (ex + 8, ey + 7), 1)
                # Rib lines below
                for ry in range(12, 18, 3):
                    pygame.draw.line(s, bone_dark, (ex - 8, ey + ry), (ex + 8, ey + ry), 1)

            # --- Kind 1: DEMON - red/dark, horns, muscular ---
            elif e.kind == 1:
                dcol = (180, 40, 30) if e.hit_flash <= 0 else (255, 255, 255)
                dcol_dark = (120, 20, 15) if e.hit_flash <= 0 else (240, 240, 240)
                # Muscular body
                pygame.draw.circle(s, dcol_dark, (ex, ey), e.radius + 2)
                pygame.draw.circle(s, dcol, (ex, ey), e.radius)
                # Inner body shading
                pygame.draw.circle(s, (min(255, dcol[0] + 30), dcol[1], dcol[2]),
                                   (ex - 3, ey - 3), e.radius - 5)
                # Horns (curved)
                horn_col = (100, 80, 50)
                pygame.draw.polygon(s, horn_col, [
                    (ex - 10, ey - 12), (ex - 18, ey - 28), (ex - 14, ey - 26), (ex - 6, ey - 10)])
                pygame.draw.polygon(s, horn_col, [
                    (ex + 10, ey - 12), (ex + 18, ey - 28), (ex + 14, ey - 26), (ex + 6, ey - 10)])
                # Angry eyes
                pygame.draw.line(s, (255, 200, 40), (ex - 9, ey - 6), (ex - 3, ey - 4), 3)
                pygame.draw.line(s, (255, 200, 40), (ex + 3, ey - 4), (ex + 9, ey - 6), 3)
                pygame.draw.circle(s, (255, 255, 100), (ex - 6, ey - 4), 2)
                pygame.draw.circle(s, (255, 255, 100), (ex + 6, ey - 4), 2)
                # Fanged mouth
                pygame.draw.arc(s, (50, 10, 10), (ex - 7, ey + 2, 14, 10), 3.14, 6.28, 2)
                pygame.draw.polygon(s, (255, 240, 200), [(ex - 5, ey + 5), (ex - 4, ey + 9), (ex - 3, ey + 5)])
                pygame.draw.polygon(s, (255, 240, 200), [(ex + 3, ey + 5), (ex + 4, ey + 9), (ex + 5, ey + 5)])

            # --- Kind 2: SPIDER - dark, multiple legs, mandibles ---
            elif e.kind == 2:
                sp_col = (50, 40, 60) if e.hit_flash <= 0 else (255, 255, 255)
                sp_light = (70, 55, 80) if e.hit_flash <= 0 else (240, 240, 240)
                # Body (two segments: abdomen + head)
                pygame.draw.ellipse(s, sp_col, (ex - e.radius + 2, ey - 4,
                                    e.radius * 2 - 4, e.radius + 6))  # abdomen
                pygame.draw.circle(s, sp_light, (ex, ey - 6), e.radius - 6)  # head
                # Hourglass marking on abdomen
                pygame.draw.polygon(s, (200, 30, 30), [
                    (ex, ey + 2), (ex - 3, ey + 6), (ex, ey + 10), (ex + 3, ey + 6)])
                # 8 legs (4 per side, animated)
                walk = math.sin(self.game_time * 8) * 3
                leg_col = sp_col
                for i, ang in enumerate([-0.8, -0.4, 0.1, 0.5]):
                    ofs = walk if i % 2 == 0 else -walk
                    # Left legs
                    lx1 = ex - e.radius + 2
                    ly1 = ey + int(ang * 12) + int(ofs)
                    lx2 = lx1 - 14
                    ly2 = ly1 + 8
                    pygame.draw.line(s, leg_col, (lx1, ly1), (lx2, ly2), 2)
                    pygame.draw.line(s, leg_col, (lx2, ly2), (lx2 - 4, ly2 + 6), 2)
                    # Right legs
                    rx1 = ex + e.radius - 2
                    ry1 = ey + int(ang * 12) + int(ofs)
                    rx2 = rx1 + 14
                    ry2 = ry1 + 8
                    pygame.draw.line(s, leg_col, (rx1, ry1), (rx2, ry2), 2)
                    pygame.draw.line(s, leg_col, (rx2, ry2), (rx2 + 4, ry2 + 6), 2)
                # Multiple eyes (cluster)
                for dx, dy in [(-5, -8), (-2, -10), (2, -10), (5, -8), (-3, -6), (3, -6)]:
                    pygame.draw.circle(s, (180, 0, 0), (ex + dx, ey + dy), 2)
                    pygame.draw.circle(s, (255, 100, 100), (ex + dx, ey + dy), 1)
                # Mandibles / fangs
                pygame.draw.line(s, (160, 140, 100), (ex - 4, ey - 2), (ex - 8, ey + 6), 2)
                pygame.draw.line(s, (160, 140, 100), (ex + 4, ey - 2), (ex + 8, ey + 6), 2)

            # --- Kind 3: WRAITH - translucent, floating, purple wispy ---
            elif e.kind == 3:
                float_ofs = math.sin(self.game_time * 3) * 4
                wy = ey + int(float_ofs)
                # Wispy trailing tail
                for i in range(5):
                    t_alpha = 0.3 - i * 0.05
                    t_col = (int(100 * t_alpha), int(50 * t_alpha), int(160 * t_alpha))
                    trail_y = wy + 8 + i * 5
                    trail_w = e.radius - i * 2
                    if trail_w > 0:
                        pygame.draw.ellipse(s, t_col, (ex - trail_w, trail_y, trail_w * 2, 6))
                # Ghostly body (translucent-look with layered circles)
                if e.hit_flash > 0:
                    wr_col = (255, 255, 255)
                else:
                    pulse = 0.6 + 0.4 * math.sin(self.game_time * 4)
                    wr_col = (int(80 * pulse), int(40 * pulse), int(150 * pulse))
                pygame.draw.circle(s, wr_col, (ex, wy), e.radius)
                # Inner glow
                glow_col = (int(min(255, wr_col[0] + 60)), int(min(255, wr_col[1] + 40)),
                            int(min(255, wr_col[2] + 50)))
                pygame.draw.circle(s, glow_col, (ex, wy), e.radius - 5)
                # Hollow eyes (bright glowing)
                pygame.draw.circle(s, (200, 180, 255), (ex - 6, wy - 3), 4)
                pygame.draw.circle(s, (200, 180, 255), (ex + 6, wy - 3), 4)
                pygame.draw.circle(s, (255, 255, 255), (ex - 6, wy - 3), 2)
                pygame.draw.circle(s, (255, 255, 255), (ex + 6, wy - 3), 2)
                # Ghostly mouth (open wail)
                pygame.draw.ellipse(s, (40, 20, 60), (ex - 4, wy + 4, 8, 6))
                # Wispy particles around
                for i in range(3):
                    ang = self.game_time * 2 + i * math.tau / 3
                    wx = ex + int(math.cos(ang) * (e.radius + 6))
                    wwy = wy + int(math.sin(ang) * (e.radius + 4))
                    pygame.draw.circle(s, (100, 70, 180), (wx, wwy), 2)

            else:
                # Fallback generic body
                pygame.draw.circle(s, body_col, (ex, ey), e.radius)

        # HP bar above enemy
        if ratio < 1.0:
            bar_w = e.radius * 2 + 8
            bar_h = 5
            bar_x = ex - bar_w // 2
            bar_y = ey - e.radius - 14
            pygame.draw.rect(s, (20, 15, 15), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2))
            pygame.draw.rect(s, (60, 20, 20), (bar_x, bar_y, bar_w, bar_h))
            fill_w = int(bar_w * ratio)
            if ratio > 0.5:
                bar_col = (60, 180, 60)
            elif ratio > 0.25:
                bar_col = (200, 160, 40)
            else:
                bar_col = (200, 40, 40)
            pygame.draw.rect(s, bar_col, (bar_x, bar_y, fill_w, bar_h))

    def _draw_player(self, s, ox, oy):
        p = self.player
        px = int(p.pos.x - self.cam_x + ox)
        py = int(p.pos.y - self.cam_y + oy)

        # Shadow
        pygame.draw.ellipse(s, (8, 6, 10), (px - 14, py + 14, 28, 10))

        # Level up flash
        if p.levelup_flash > 0:
            flash_r = int(40 + 20 * math.sin(p.levelup_flash * 8))
            pygame.draw.circle(s, (flash_r, flash_r - 5, 0), (px, py), 40, 2)

        # Iframes blink
        if p.iframes > 0 and int(p.iframes * 20) % 2 == 0:
            return  # blink effect

        # Dash afterimage
        if p.dash_timer > 0:
            pygame.draw.circle(s, (40, 60, 100), (px, py), 22, 2)

        # Body - armored warrior
        # Feet with walk animation
        walk_offset = int(math.sin(p.walk_anim) * 4) if p.vel.length_squared() > 100 else 0
        pygame.draw.rect(s, (50, 45, 35), (px - 10, py + 12 + walk_offset, 8, 7), border_radius=2)
        pygame.draw.rect(s, (50, 45, 35), (px + 2, py + 12 - walk_offset, 8, 7), border_radius=2)

        # Torso (armor)
        pygame.draw.rect(s, (55, 65, 90), (px - 13, py - 8, 26, 24), border_radius=5)
        # Armor detail
        pygame.draw.rect(s, (70, 82, 110), (px - 10, py - 6, 20, 4), border_radius=1)
        pygame.draw.rect(s, (65, 75, 100), (px - 7, py + 3, 14, 3))
        # Shoulder pauldrons
        pygame.draw.circle(s, (70, 80, 105), (px - 14, py - 4), 7)
        pygame.draw.circle(s, (70, 80, 105), (px + 14, py - 4), 7)
        pygame.draw.circle(s, (85, 95, 125), (px - 14, py - 5), 4)
        pygame.draw.circle(s, (85, 95, 125), (px + 14, py - 5), 4)

        # Head (helmet)
        pygame.draw.circle(s, (75, 80, 95), (px, py - 13), 10)
        # Visor slit
        pygame.draw.rect(s, (180, 170, 140), (px - 6, py - 14, 12, 3))

        # Cape hint
        if p.vel.length_squared() > 100:
            cape_sway = int(math.sin(p.walk_anim * 0.7) * 4)
            pygame.draw.polygon(s, (50, 30, 30),
                                [(px - 8, py + 3), (px + 8, py + 3),
                                 (px + 6 + cape_sway, py + 20), (px - 6 + cape_sway, py + 20)])

        # Arm/bow toward mouse
        mx, my = pygame.mouse.get_pos()
        ang = math.atan2(my - py, mx - px)
        hand_x = px + int(math.cos(ang) * 18)
        hand_y = py + int(math.sin(ang) * 18)
        # Arm
        pygame.draw.line(s, (100, 95, 85), (px + int(math.cos(ang) * 8), py + int(math.sin(ang) * 8)),
                         (hand_x, hand_y), 3)
        # Bow
        bow_r = 14
        perp = ang + math.pi / 2
        bow_top_x = hand_x + int(math.cos(perp) * bow_r)
        bow_top_y = hand_y + int(math.sin(perp) * bow_r)
        bow_bot_x = hand_x + int(math.cos(perp) * -bow_r)
        bow_bot_y = hand_y + int(math.sin(perp) * -bow_r)
        # Bow limbs
        bow_col = (120, 90, 50) if p.dmg_timer <= 0 else (200, 160, 60)
        pygame.draw.line(s, bow_col, (bow_top_x, bow_top_y), (hand_x, hand_y), 3)
        pygame.draw.line(s, bow_col, (hand_x, hand_y), (bow_bot_x, bow_bot_y), 3)
        # Bowstring
        pygame.draw.line(s, (200, 200, 210), (bow_top_x, bow_top_y), (bow_bot_x, bow_bot_y), 1)
        # Infusion glow on bow
        if p.infusion_type:
            icol = INFUSION_COLORS[p.infusion_type]
            pygame.draw.circle(s, icol, (hand_x, hand_y), 8, 2)

        # Shield visual
        if p.shield > 0:
            pulse = 0.6 + 0.4 * math.sin(self.game_time * 3)
            shield_col = (int(60 * pulse), int(160 * pulse), int(220 * pulse))
            pygame.draw.circle(s, shield_col, (px, py), p.radius + 8, 2)

        # Damage boost aura
        if p.dmg_timer > 0:
            pulse = 0.5 + 0.5 * math.sin(self.game_time * 5)
            aura_col = (int(200 * pulse), int(120 * pulse), int(20 * pulse))
            pygame.draw.circle(s, aura_col, (px, py), p.radius + 4, 1)

    def _draw_particles(self, s, ox, oy):
        for p in self.particles:
            sx = int(p.x - self.cam_x + ox)
            sy = int(p.y - self.cam_y + oy)
            if not (-10 < sx < WIDTH + 10 and -10 < sy < HEIGHT + 10):
                continue
            alpha = max(0.0, p.life / p.max_life)
            r = max(0, min(255, int(p.r * alpha)))
            g = max(0, min(255, int(p.g * alpha)))
            b = max(0, min(255, int(p.b * alpha)))
            size = max(1, int(p.size * alpha))
            pygame.draw.circle(s, (r, g, b), (sx, sy), size)

    def _draw_floating_texts(self, s, ox, oy):
        for ft in self.floating_texts:
            sx = int(ft.x - self.cam_x + ox)
            sy = int(ft.y - self.cam_y + oy)
            if not (-100 < sx < WIDTH + 100 and -50 < sy < HEIGHT + 50):
                continue
            alpha = max(0.0, ft.life / ft.max_life)
            r = max(0, min(255, int(ft.r * alpha)))
            g = max(0, min(255, int(ft.g * alpha)))
            b = max(0, min(255, int(ft.b * alpha)))
            if ft.scale > 1.2:
                rendered = self.bigfont.render(ft.text, True, (r, g, b))
            else:
                rendered = self.dmgfont.render(ft.text, True, (r, g, b))
            s.blit(rendered, (sx - rendered.get_width() // 2, sy - rendered.get_height() // 2))

    def _draw_lighting(self, s, ox, oy):
        self.light_map.fill(BIOME_AMBIENT.get(self.current_biome, AMBIENT_LIGHT))
        # Player light
        plx = int(self.player.pos.x - self.cam_x + ox)
        ply = int(self.player.pos.y - self.cam_y + oy)
        pls = self.light_surfs["player"]
        pr = PLAYER_LIGHT_RADIUS
        # flicker
        flicker = random.uniform(0.95, 1.0)
        self.light_map.blit(pls, (plx - pr, ply - pr), special_flags=pygame.BLEND_RGB_ADD)

        # Torch lights
        for tx, ty in self.dungeon.torches:
            if not self._tile_in_view(tx, ty):
                continue
            lx = int(tx * TILE + TILE // 2 - self.cam_x + ox)
            ly = int(ty * TILE + TILE // 2 - self.cam_y + oy)
            tr = TORCH_LIGHT_RADIUS
            flick = random.uniform(0.75, 1.0)
            tls = self.light_surfs["torch"]
            self.light_map.blit(tls, (lx - tr, ly - tr), special_flags=pygame.BLEND_RGB_ADD)

        # Projectile lights
        for pr_obj in self.projectiles:
            prx = int(pr_obj.pos.x - self.cam_x + ox)
            pry = int(pr_obj.pos.y - self.cam_y + oy)
            if -100 < prx < WIDTH + 100 and -100 < pry < HEIGHT + 100:
                if pr_obj.hostile:
                    key = "proj_red"
                elif pr_obj.infusion and f"infusion_{pr_obj.infusion}" in self.light_surfs:
                    key = f"infusion_{pr_obj.infusion}"
                elif pr_obj.radius > BASIC_RADIUS:
                    key = "proj_power"
                else:
                    key = "proj_blue"
                pls2 = self.light_surfs[key]
                r2 = pls2.get_width() // 2
                self.light_map.blit(pls2, (prx - r2, pry - r2), special_flags=pygame.BLEND_RGB_ADD)

        # Elite aura lights
        for e in self.enemies:
            if isinstance(e, Elite) and e.alive:
                elx = int(e.pos.x - self.cam_x + ox)
                ely = int(e.pos.y - self.cam_y + oy)
                if -150 < elx < WIDTH + 150 and -150 < ely < HEIGHT + 150:
                    key = f"elite_{e.aura}"
                    if key in self.light_surfs:
                        els = self.light_surfs[key]
                        er = els.get_width() // 2
                        self.light_map.blit(els, (elx - er, ely - er), special_flags=pygame.BLEND_RGB_ADD)

        # Portal lights
        for ptx, pty, _ in self.dungeon.portal_positions:
            if self._tile_in_view(ptx, pty):
                stx = int(ptx * TILE + TILE // 2 - self.cam_x + ox)
                sty = int(pty * TILE + TILE // 2 - self.cam_y + oy)
                pls3 = self.light_surfs["portal"]
                r3 = pls3.get_width() // 2
                self.light_map.blit(pls3, (stx - r3, sty - r3), special_flags=pygame.BLEND_RGB_ADD)

        # Chest lights
        for chest in self.chests:
            if not chest.alive:
                continue
            clx = int(chest.pos.x - self.cam_x + ox)
            cly = int(chest.pos.y - self.cam_y + oy)
            if -100 < clx < WIDTH + 100 and -100 < cly < HEIGHT + 100:
                key = "gold_chest" if chest.kind == "gold" else "chest"
                cls = self.light_surfs[key]
                cr = cls.get_width() // 2
                self.light_map.blit(cls, (clx - cr, cly - cr), special_flags=pygame.BLEND_RGB_ADD)

        # Hazard pool lights
        hazard = BIOME_HAZARD.get(self.current_biome, "poison")
        hazard_light_key = "lava" if hazard == "lava" else "ice_pool" if hazard == "ice" else "poison"
        for ppx, ppy in self.dungeon.hazard_pools:
            if not self._tile_in_view(ppx, ppy):
                continue
            plx = int(ppx * TILE + TILE // 2 - self.cam_x + ox)
            ply = int(ppy * TILE + TILE // 2 - self.cam_y + oy)
            if hazard_light_key in self.light_surfs:
                pls4 = self.light_surfs[hazard_light_key]
                pr4 = pls4.get_width() // 2
                self.light_map.blit(pls4, (plx - pr4, ply - pr4), special_flags=pygame.BLEND_RGB_ADD)

        # Vendor light
        if self.vendor:
            vlx = int(self.vendor.pos.x - self.cam_x + ox)
            vly = int(self.vendor.pos.y - self.cam_y + oy)
            if -200 < vlx < WIDTH + 200 and -200 < vly < HEIGHT + 200:
                if "torch" in self.light_surfs:
                    vls = self.light_surfs["torch"]
                    vr = vls.get_width() // 2
                    self.light_map.blit(vls, (vlx - vr, vly - vr), special_flags=pygame.BLEND_RGB_ADD)

        # Apply lighting
        s.blit(self.light_map, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

    def _draw_reticle(self, s):
        mx, my = pygame.mouse.get_pos()
        # outer ring
        pygame.draw.circle(s, (180, 160, 120), (mx, my), 12, 2)
        # crosshair
        gap = 4
        length = 12
        pygame.draw.line(s, (200, 180, 140), (mx - length, my), (mx - gap, my), 2)
        pygame.draw.line(s, (200, 180, 140), (mx + gap, my), (mx + length, my), 2)
        pygame.draw.line(s, (200, 180, 140), (mx, my - length), (mx, my - gap), 2)
        pygame.draw.line(s, (200, 180, 140), (mx, my + gap), (mx, my + length), 2)
        # center dot
        pygame.draw.circle(s, (220, 200, 160), (mx, my), 2)

    def _draw_minimap(self, s):
        mm_w = 300
        mm_h = 220
        surf = pygame.Surface((mm_w, mm_h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 150))
        # Gothic frame
        pygame.draw.rect(surf, (80, 65, 45, 200), (0, 0, mm_w, mm_h), 2)
        pygame.draw.rect(surf, (50, 40, 28, 150), (1, 1, mm_w - 2, mm_h - 2), 1)

        sx = mm_w / MAP_W
        sy = mm_h / MAP_H
        for tx in range(0, MAP_W, 2):
            for ty in range(0, MAP_H, 2):
                if not self.dungeon.seen[tx][ty]:
                    continue
                if self.dungeon.tiles[tx][ty] == WALL:
                    col = (60, 55, 65, 200)
                else:
                    col = (100, 95, 110, 180)
                pygame.draw.rect(surf, col, (tx * sx, ty * sy, sx * 2, sy * 2))

        # player dot
        ppx = int(self.player.pos.x / TILE * sx)
        ppy = int(self.player.pos.y / TILE * sy)
        pygame.draw.circle(surf, (180, 255, 180), (ppx, ppy), 3)
        pygame.draw.circle(surf, (100, 200, 100), (ppx, ppy), 3, 1)

        # enemies
        for e in self.enemies:
            if not e.alive:
                continue
            epx = int(e.pos.x / TILE * sx)
            epy = int(e.pos.y / TILE * sy)
            if isinstance(e, Boss):
                color = (255, 80, 40)
                pygame.draw.circle(surf, color, (epx, epy), 3)
            elif isinstance(e, Elite):
                color = (255, 220, 100)
                pygame.draw.circle(surf, color, (epx, epy), 2)
            else:
                pygame.draw.circle(surf, (220, 80, 80), (epx, epy), 2)

        # chests
        for chest in self.chests:
            if not chest.alive:
                continue
            cpx = int(chest.pos.x / TILE * sx)
            cpy = int(chest.pos.y / TILE * sy)
            col = (255, 220, 80) if chest.kind == "gold" else (200, 160, 60)
            pygame.draw.rect(surf, col, (cpx - 1, cpy - 1, 3, 3))

        # hazard pools
        hazard = BIOME_HAZARD.get(self.current_biome, "poison")
        for ppx, ppy in self.dungeon.hazard_pools:
            rpx = int(ppx * sx)
            rpy = int(ppy * sy)
            if hazard == "lava":
                col = (200, 60, 10, 180)
            elif hazard == "ice":
                col = (60, 120, 200, 180)
            else:
                col = (40, 160, 30, 180)
            pygame.draw.circle(surf, col, (rpx, rpy), 2)

        # portals
        for ptx, pty, dest in self.dungeon.portal_positions:
            ppx = int(ptx * sx)
            ppy = int(pty * sy)
            pulse = 0.5 + 0.5 * math.sin(self.game_time * 3)
            pcol = BIOME_PORTAL_COLORS.get(dest, (200, 200, 100))
            col = (int(pcol[0] * pulse), int(pcol[1] * pulse), int(pcol[2] * pulse), 255)
            pygame.draw.rect(surf, col, (ppx - 2, ppy - 2, 5, 5))

        # treasure goblin
        if self.treasure_goblin and self.treasure_goblin.alive:
            gpx = int(self.treasure_goblin.pos.x / TILE * sx)
            gpy = int(self.treasure_goblin.pos.y / TILE * sy)
            pulse = 0.5 + 0.5 * math.sin(self.game_time * 6)
            pygame.draw.circle(surf, (int(255 * pulse), int(215 * pulse), 0), (gpx, gpy), 3)

        # vendor
        if self.vendor:
            vpx = int(self.vendor.pos.x / TILE * sx)
            vpy = int(self.vendor.pos.y / TILE * sy)
            pygame.draw.circle(surf, (100, 200, 255), (vpx, vpy), 3)
            pygame.draw.circle(surf, (60, 140, 200), (vpx, vpy), 3, 1)

        s.blit(surf, (WIDTH - mm_w - 12, 12))

    # ---- Diablo-style UI ----
    def _draw_ui(self, s):
        p = self.player
        max_hp = p.max_hp()
        max_mana = p.max_mana()

        # Bottom panel background
        panel_h = 100
        panel_surf = pygame.Surface((WIDTH, panel_h), pygame.SRCALPHA)
        panel_surf.fill((10, 8, 14, 200))
        pygame.draw.line(panel_surf, (80, 65, 45, 200), (0, 0), (WIDTH, 0), 3)
        s.blit(panel_surf, (0, HEIGHT - panel_h))

        # Health globe (left)
        globe_r = 42
        globe_cx = 70
        globe_cy = HEIGHT - panel_h // 2
        hp_frac = max(0, min(1, p.hp / max_hp))
        self._draw_globe(s, globe_cx, globe_cy, globe_r, hp_frac,
                         empty_color=(40, 10, 10), fill_color=(160, 25, 25),
                         highlight_color=(200, 60, 60), frame_color=C_GOTHIC_FRAME)
        # HP text
        hp_txt = self.font.render(f"{p.hp}", True, (220, 200, 200))
        s.blit(hp_txt, (globe_cx - hp_txt.get_width() // 2, globe_cy - hp_txt.get_height() // 2))

        # Mana globe (right)
        mana_cx = WIDTH - 70
        mana_frac = max(0, min(1, p.mana / max_mana))
        self._draw_globe(s, mana_cx, globe_cy, globe_r, mana_frac,
                         empty_color=(10, 15, 45), fill_color=(30, 50, 170),
                         highlight_color=(60, 90, 220), frame_color=C_GOTHIC_FRAME)
        mana_txt = self.font.render(f"{int(p.mana)}", True, (200, 210, 240))
        s.blit(mana_txt, (mana_cx - mana_txt.get_width() // 2, globe_cy - mana_txt.get_height() // 2))

        # XP bar between globes
        xp_frac = p.xp / max(1, p.xp_to_next)
        bar_x = 130
        bar_w = WIDTH - 260
        bar_y = HEIGHT - 18
        bar_h = 10
        pygame.draw.rect(s, (25, 20, 15), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(s, (180, 160, 80), (bar_x, bar_y, int(bar_w * xp_frac), bar_h))
        pygame.draw.rect(s, C_GOTHIC_FRAME, (bar_x, bar_y, bar_w, bar_h), 1)
        xp_label = self.font.render(f"Level {p.level}", True, (200, 190, 150))
        s.blit(xp_label, (WIDTH // 2 - xp_label.get_width() // 2, bar_y - 22))

        # Skill indicators / cooldowns
        skill_y = HEIGHT - panel_h + 10
        # Basic attack
        cd_frac = p.basic_cd / BASIC_CD if BASIC_CD > 0 else 0
        self._draw_skill_icon(s, WIDTH // 2 - 80, skill_y, 36, cd_frac, (140, 200, 255), "LMB")
        # Power shot
        cd_frac2 = p.power_cd / POWER_CD if POWER_CD > 0 else 0
        self._draw_skill_icon(s, WIDTH // 2 - 30, skill_y, 36, cd_frac2, (160, 120, 255), "RMB")
        # Dash
        dash_frac = p.dash_cd / DASH_CD if DASH_CD > 0 else 0
        self._draw_skill_icon(s, WIDTH // 2 + 20, skill_y, 36, dash_frac, (100, 200, 140), "Shift")

        # Potion slots
        pot_y = HEIGHT - panel_h + 14
        # HP potion
        pygame.draw.rect(s, (60, 20, 20), (WIDTH // 2 + 100, pot_y, 32, 32), border_radius=5)
        pygame.draw.rect(s, (120, 40, 40), (WIDTH // 2 + 100, pot_y, 32, 32), 1, border_radius=5)
        pot_txt = self.font.render(f"{p.potions_hp}", True, (220, 160, 160))
        s.blit(pot_txt, (WIDTH // 2 + 108, pot_y + 6))
        q_label = self.font.render("Q", True, (150, 130, 120))
        s.blit(q_label, (WIDTH // 2 + 109, pot_y + 34))

        # Mana potion
        pygame.draw.rect(s, (20, 30, 80), (WIDTH // 2 + 145, pot_y, 32, 32), border_radius=5)
        pygame.draw.rect(s, (40, 60, 140), (WIDTH // 2 + 145, pot_y, 32, 32), 1, border_radius=5)
        pot_txt2 = self.font.render(f"{p.potions_mana}", True, (160, 180, 220))
        s.blit(pot_txt2, (WIDTH // 2 + 153, pot_y + 6))
        e_label = self.font.render("E", True, (150, 130, 120))
        s.blit(e_label, (WIDTH // 2 + 154, pot_y + 34))

        # Gold
        gold_txt = self.font.render(f"Gold: {p.gold}", True, C_GOLD)
        s.blit(gold_txt, (140, HEIGHT - panel_h + 12))

        # Weapon name with rarity color
        wc = p.weapon.get_color()
        wname_txt = self.font.render(f"{p.weapon.name} ({p.weapon.dmg_min}-{p.weapon.dmg_max})", True, wc)
        s.blit(wname_txt, (WIDTH // 2 - wname_txt.get_width() // 2, HEIGHT - panel_h - 22))

        # Stat point / skill point indicators
        if p.stat_points > 0 or p.skill_points > 0:
            notify_parts = []
            if p.stat_points > 0:
                notify_parts.append(f"[C] {p.stat_points} stat pts")
            if p.skill_points > 0:
                notify_parts.append(f"[T] {p.skill_points} skill pts")
            notify_txt = self.font.render("  ".join(notify_parts), True, C_GOLD)
            s.blit(notify_txt, (WIDTH // 2 - notify_txt.get_width() // 2, HEIGHT - panel_h - 42))

        # Active buffs
        buff_x = 140
        buff_y = HEIGHT - panel_h + 40
        if p.shield > 0:
            pygame.draw.rect(s, (60, 160, 210), (buff_x, buff_y, 100, 18), 1, border_radius=3)
            txt = self.font.render(f"Shield {p.shield}", True, C_ICE)
            s.blit(txt, (buff_x + 6, buff_y + 1))
            buff_x += 110
        if p.dmg_timer > 0:
            pygame.draw.rect(s, (200, 130, 30), (buff_x, buff_y, 120, 18), 1, border_radius=3)
            txt = self.font.render(f"Dmg x{DMG_BOOST_MULT:.1f} {p.dmg_timer:.1f}s", True, (255, 200, 100))
            s.blit(txt, (buff_x + 6, buff_y + 1))
            buff_x += 130
        if p.infusion_type and p.infusion_timer > 0:
            icol = INFUSION_COLORS[p.infusion_type]
            pygame.draw.rect(s, icol, (buff_x, buff_y, 130, 18), 1, border_radius=3)
            txt = self.font.render(f"{p.infusion_type.upper()} {p.infusion_timer:.1f}s", True, icol)
            s.blit(txt, (buff_x + 6, buff_y + 1))

        # Top-left info
        biome_name = BIOME_NAMES.get(self.current_biome, self.current_biome)
        info = self.font.render(f"Depth {self.current_level}  {biome_name}  {self.difficulty_name}  Wave {self.wave}", True, (170, 165, 150))
        s.blit(info, (16, 12))
        wave_txt = self.font.render(f"Next wave: {self.spawn_timer:.1f}s", True, (140, 135, 120))
        s.blit(wave_txt, (16, 32))
        # Lives display
        lives_col = (100, 200, 100) if p.lives > 1 else ((220, 180, 60) if p.lives == 1 else (200, 60, 60))
        lives_txt = self.font.render(f"Lives: {p.lives}/{p.max_lives}", True, lives_col)
        s.blit(lives_txt, (16, 52))
        hint = self.font.render("C=Stats  I=Inventory  T=Skills  Esc=Menu  F1=Help", True, (90, 85, 75))
        s.blit(hint, (16, 72))

    def _draw_globe(self, s, cx, cy, r, frac, empty_color, fill_color, highlight_color, frame_color):
        # Empty globe
        pygame.draw.circle(s, empty_color, (cx, cy), r)
        # Fill level
        if frac > 0:
            fill_height = int(2 * r * frac)
            fill_top = cy + r - fill_height
            # draw filled portion by clipping
            for dy in range(fill_height):
                y = fill_top + dy
                # calculate circle width at this y
                dist = abs(y - cy)
                if dist > r:
                    continue
                half_w = int(math.sqrt(r * r - dist * dist))
                # gradient: lighter at top of liquid
                t = dy / max(1, fill_height)
                cr = int(fill_color[0] + (highlight_color[0] - fill_color[0]) * (1 - t) * 0.3)
                cg = int(fill_color[1] + (highlight_color[1] - fill_color[1]) * (1 - t) * 0.3)
                cb = int(fill_color[2] + (highlight_color[2] - fill_color[2]) * (1 - t) * 0.3)
                pygame.draw.line(s, (min(255, cr), min(255, cg), min(255, cb)),
                                 (cx - half_w, y), (cx + half_w, y))
        # Glass highlight
        pygame.draw.circle(s, (255, 255, 255), (cx - r // 3, cy - r // 3), r // 4, 1)
        # Frame
        pygame.draw.circle(s, frame_color, (cx, cy), r, 3)
        pygame.draw.circle(s, C_GOTHIC_FRAME_LIGHT, (cx, cy), r + 1, 1)

    def _draw_skill_icon(self, s, x, y, size, cd_frac, color, label):
        pygame.draw.rect(s, (20, 18, 25), (x, y, size, size), border_radius=4)
        if cd_frac > 0:
            # cooldown overlay
            fill_h = int(size * cd_frac)
            pygame.draw.rect(s, (10, 8, 12), (x, y, size, fill_h), border_radius=4)
        pygame.draw.rect(s, (color[0] // 2, color[1] // 2, color[2] // 2), (x, y, size, size), 1, border_radius=4)
        lbl = self.font.render(label, True, color if cd_frac <= 0 else (80, 80, 80))
        s.blit(lbl, (x + size // 2 - lbl.get_width() // 2, y + size + 2))

    # ---- Overlays ----
    def _pause_screen(self):
        idx = 0
        options = [
            ("Resume", "resume"),
            ("Save Game", "save"),
            ("Save & Quit", "save_quit"),
            ("Quit (no save)", "quit"),
        ]
        while True:
            self.clock.tick(30)
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))

            txt = self.titlefont.render("PAUSED", True, C_GOLD)
            self.screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 120))

            # Lives display
            p = self.player
            lives_str = f"Lives: {p.lives}/{p.max_lives}   Depth: {self.current_level}   Level: {p.level}"
            info = self.font.render(lives_str, True, (160, 150, 130))
            self.screen.blit(info, (WIDTH // 2 - info.get_width() // 2, HEIGHT // 2 - 55))

            y = HEIGHT // 2 - 15
            for i, (label, _) in enumerate(options):
                is_sel = (i == idx)
                col = C_GOLD if is_sel else (140, 130, 110)
                marker = "> " if is_sel else "  "
                ot = self.bigfont.render(f"{marker}{label}", True, col)
                self.screen.blit(ot, (WIDTH // 2 - 120, y))
                y += 45

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    self.paused = False
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        idx = (idx - 1) % len(options)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        idx = (idx + 1) % len(options)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        action = options[idx][1]
                        if action == "resume":
                            self.paused = False
                            return
                        elif action == "save":
                            self._save_game()
                            self.paused = False
                            return
                        elif action == "save_quit":
                            self._save_game()
                            self.running = False
                            self.paused = False
                            return
                        elif action == "quit":
                            self.running = False
                            self.paused = False
                            return
                    elif event.key in (pygame.K_p, pygame.K_ESCAPE):
                        self.paused = False
                        return

    def _help_overlay(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.screen.blit(overlay, (0, 0))

        title = self.bigfont.render("- CONTROLS -", True, C_GOLD)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))
        pygame.draw.line(self.screen, C_GOTHIC_FRAME, (WIDTH // 2 - 150, 115), (WIDTH // 2 + 150, 115), 1)

        lines = [
            ("WASD", "Move"),
            ("Left Click", "Single Arrow"),
            ("Right Click", "Multishot (fan of arrows, costs mana)"),
            ("Q / E", "Use HP / Mana Potion"),
            ("Left Shift", "Dash (grants invulnerability)"),
            ("C", "Character Stats (allocate stat points)"),
            ("I", "Inventory (equip/sell weapons)"),
            ("T", "Skill Tree (spend skill points)"),
            ("F11", "Toggle Fullscreen"),
            ("P / Esc", "Pause Menu (Resume, Save, Quit)"),
            ("", ""),
            ("Shoot Chests", "Break open for gold, potions, weapons, boosts"),
            ("Infusions", "Pick up Fire/Ice/Lightning arrows for timed buffs"),
            ("V", "Trade with vendor NPC (when nearby)"),
            ("", ""),
            ("Portals", "Step into colored portals to enter new biomes"),
            ("Vendor NPC", "Buy/sell weapons in the starting room"),
            ("Creatures", "Skeletons, Demons, Spiders, Wraiths - each with unique sounds"),
            ("Treasure Goblin", "Chase it! Drops gold as it flees, jackpot on kill"),
            ("Elites", "Lead packs with auras: Haste / Frenzy / Guardian"),
            ("Lives", "3 respawns in place, then return to start of depth"),
            ("Save", "Auto-saves on quit; continue from title screen"),
            ("Goal", "Explore endless depths, hunt goblins, slay bosses"),
        ]
        y = 140
        for key, desc in lines:
            if key:
                kt = self.font.render(key, True, (200, 180, 140))
                dt = self.font.render(f"  -  {desc}", True, (160, 155, 140))
                self.screen.blit(kt, (WIDTH // 2 - 200, y))
                self.screen.blit(dt, (WIDTH // 2 - 200 + kt.get_width(), y))
            y += 28

        hint = self.font.render("Press any key to close", True, (120, 115, 100))
        self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, y + 20))
        pygame.display.flip()
        waiting = True
        while waiting:
            for e in pygame.event.get():
                if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.QUIT):
                    waiting = False

    # ---- CHARACTER STATS SCREEN (C key) ----
    def _character_screen(self):
        """D2-style character stat allocation screen."""
        p = self.player
        stats = ["strength", "dexterity", "vitality", "energy"]
        stat_labels = {"strength": "Strength", "dexterity": "Dexterity",
                       "vitality": "Vitality", "energy": "Energy"}
        stat_colors = {"strength": (255, 140, 140), "dexterity": (140, 255, 140),
                       "vitality": (255, 200, 100), "energy": (140, 180, 255)}
        stat_desc = {
            "strength": "+1% damage per point",
            "dexterity": "+1% attack speed, +0.5% crit, +1% arrow speed",
            "vitality": "+3 max HP, +0.5 HP regen per point",
            "energy": "+4 max Mana, +0.3 mana regen, +1% skill dmg",
        }
        selected = 0
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False
                    return
                if ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_c, pygame.K_ESCAPE):
                        running = False
                    elif ev.key in (pygame.K_w, pygame.K_UP):
                        selected = (selected - 1) % len(stats)
                    elif ev.key in (pygame.K_s, pygame.K_DOWN):
                        selected = (selected + 1) % len(stats)
                    elif ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_RIGHT, pygame.K_d):
                        if p.stat_points > 0:
                            setattr(p, stats[selected], getattr(p, stats[selected]) + 1)
                            p.stat_points -= 1
                            self.play_sound("pickup")
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    mx, my = ev.pos
                    for i, st in enumerate(stats):
                        btn_x = WIDTH // 2 + 180
                        btn_y = 240 + i * 80
                        if btn_x <= mx <= btn_x + 28 and btn_y <= my <= btn_y + 28 and p.stat_points > 0:
                            setattr(p, st, getattr(p, st) + 1)
                            p.stat_points -= 1
                            self.play_sound("pickup")

            # Draw
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 230))
            self.screen.blit(overlay, (0, 0))

            title = self.bigfont.render("- CHARACTER STATS -", True, C_GOLD)
            self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 60))
            pygame.draw.line(self.screen, C_GOTHIC_FRAME,
                             (WIDTH // 2 - 200, 95), (WIDTH // 2 + 200, 95), 1)

            # Level and points
            lvl_txt = self.font.render(f"Level {p.level}   Stat Points: {p.stat_points}", True, C_GOLD)
            self.screen.blit(lvl_txt, (WIDTH // 2 - lvl_txt.get_width() // 2, 110))

            # Stats
            for i, st in enumerate(stats):
                y = 240 + i * 80
                color = stat_colors[st]
                is_sel = i == selected
                # Highlight
                if is_sel:
                    pygame.draw.rect(self.screen, (40, 35, 25),
                                     (WIDTH // 2 - 250, y - 8, 500, 65), border_radius=5)
                    pygame.draw.rect(self.screen, color,
                                     (WIDTH // 2 - 250, y - 8, 500, 65), 1, border_radius=5)

                val = getattr(p, st)
                name_txt = self.bigfont.render(f"{stat_labels[st]}: {val}", True, color)
                self.screen.blit(name_txt, (WIDTH // 2 - 220, y))
                desc_txt = self.font.render(stat_desc[st], True, (140, 135, 120))
                self.screen.blit(desc_txt, (WIDTH // 2 - 220, y + 34))

                # + button
                if p.stat_points > 0:
                    btn_x = WIDTH // 2 + 180
                    pygame.draw.rect(self.screen, (60, 120, 60), (btn_x, y, 28, 28), border_radius=4)
                    pygame.draw.rect(self.screen, (100, 200, 100), (btn_x, y, 28, 28), 1, border_radius=4)
                    plus = self.font.render("+", True, (200, 255, 200))
                    self.screen.blit(plus, (btn_x + 7, y + 2))

            # Derived stats
            y = 580
            derived = [
                f"Max HP: {p.max_hp()}",
                f"Max Mana: {p.max_mana()}",
                f"Crit Chance: {p.calc_crit_chance():.1f}%",
                f"Attack Speed: {p.calc_attack_speed_mult():.2f}x",
                f"Damage Mult: {p.calc_dmg_mult():.2f}x",
                f"Life Steal: {p.calc_life_steal():.1f}%",
                f"Dodge: {p.calc_dodge_chance():.1f}%",
                f"Mana Regen: {p.mana_regen():.1f}/s",
                f"Pierce: {p.calc_pierce()}",
                f"Multishot: {p.calc_multishot_count()} arrows",
            ]
            dtitle = self.font.render("Derived Stats:", True, (180, 170, 140))
            self.screen.blit(dtitle, (WIDTH // 2 - 220, y))
            y += 28
            for j, d in enumerate(derived):
                col = j % 2
                row = j // 2
                dx = WIDTH // 2 - 220 + col * 280
                dy = y + row * 24
                dt = self.font.render(d, True, (160, 155, 140))
                self.screen.blit(dt, (dx, dy))

            hint = self.font.render("[W/S] Select   [Enter/D/Click +] Add Point   [C/Esc] Close", True, (100, 95, 85))
            self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 60))

            pygame.display.flip()
            self.clock.tick(30)

    # ---- INVENTORY SCREEN (I key) ----
    def _inventory_screen(self):
        """D2-style inventory with equipped weapon and grid."""
        p = self.player
        cell_w, cell_h = 60, 60
        grid_x = WIDTH // 2 - (INV_COLS * cell_w) // 2
        grid_y = 360
        selected = -1  # -1 = equipped, 0+ = inventory slot
        scroll = 0
        running = True
        while running:
            mx, my = pygame.mouse.get_pos()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False
                    return
                if ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_i, pygame.K_ESCAPE):
                        running = False
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    if ev.button == 1:  # Left click - equip
                        for idx in range(len(p.inventory)):
                            row = idx // INV_COLS
                            col = idx % INV_COLS
                            cx = grid_x + col * cell_w
                            cy = grid_y + row * cell_h
                            if cx <= mx <= cx + cell_w and cy <= my <= cy + cell_h:
                                # Swap with equipped
                                old = p.weapon
                                p.weapon = p.inventory[idx]
                                p.inventory[idx] = old
                                self.play_sound("pickup")
                                self.add_floating_text(p.pos.x, p.pos.y - 20,
                                                       f"Equipped {p.weapon.name}", p.weapon.get_color(), 1.0)
                    elif ev.button == 3:  # Right click - sell for gold
                        for idx in range(len(p.inventory)):
                            row = idx // INV_COLS
                            col = idx % INV_COLS
                            cx = grid_x + col * cell_w
                            cy = grid_y + row * cell_h
                            if cx <= mx <= cx + cell_w and cy <= my <= cy + cell_h:
                                sell_price = max(1, (p.inventory[idx].dmg_min + p.inventory[idx].dmg_max) // 2)
                                rarity_mult = {RARITY_NORMAL: 1, RARITY_MAGIC: 2, RARITY_RARE: 4,
                                               RARITY_UNIQUE: 8, RARITY_SET: 6}
                                sell_price *= rarity_mult.get(p.inventory[idx].rarity, 1)
                                p.gold += sell_price
                                self.add_floating_text(p.pos.x, p.pos.y - 20,
                                                       f"+{sell_price}g (sold)", C_GOLD, 1.0)
                                p.inventory.pop(idx)
                                self.play_sound("gold")
                                break

            # Draw
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 230))
            self.screen.blit(overlay, (0, 0))

            title = self.bigfont.render("- INVENTORY -", True, C_GOLD)
            self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 40))
            pygame.draw.line(self.screen, C_GOTHIC_FRAME,
                             (WIDTH // 2 - 160, 75), (WIDTH // 2 + 160, 75), 1)

            # Equipped weapon display
            eq_x = WIDTH // 2 - 250
            eq_y = 100
            self.screen.blit(self.font.render("Equipped:", True, (180, 170, 140)), (eq_x, eq_y))
            w = p.weapon
            wc = w.get_color()
            pygame.draw.rect(self.screen, (30, 25, 20), (eq_x, eq_y + 28, 500, 120), border_radius=6)
            pygame.draw.rect(self.screen, wc, (eq_x, eq_y + 28, 500, 120), 2, border_radius=6)
            name_txt = self.bigfont.render(w.name, True, wc)
            self.screen.blit(name_txt, (eq_x + 15, eq_y + 35))
            rarity_txt = self.font.render(f"[{RARITY_NAMES[w.rarity]}] {w.weapon_class.title()}", True, wc)
            self.screen.blit(rarity_txt, (eq_x + 15, eq_y + 65))
            dmg_txt = self.font.render(f"Damage: {w.dmg_min}-{w.dmg_max}   Speed: {w.attack_speed:.1f}", True, (200, 190, 160))
            self.screen.blit(dmg_txt, (eq_x + 15, eq_y + 90))
            # Show mods
            mod_x = eq_x + 280
            mod_y = eq_y + 65
            for mk, mv in w.mods.items():
                if mv:
                    label = mk.replace("_", " ").title()
                    mod_color = (100, 200, 255) if mk.endswith("_dmg") else (200, 200, 140)
                    mt = self.font.render(f"+{mv} {label}", True, mod_color)
                    self.screen.blit(mt, (mod_x, mod_y))
                    mod_y += 20

            # Gold
            gold_txt = self.font.render(f"Gold: {p.gold}", True, C_GOLD)
            self.screen.blit(gold_txt, (eq_x + 360, eq_y))

            # Inventory grid header
            inv_title = self.font.render(f"Backpack ({len(p.inventory)}/{INV_COLS * INV_ROWS})", True, (180, 170, 140))
            self.screen.blit(inv_title, (grid_x, grid_y - 28))

            # Grid
            for idx in range(INV_COLS * INV_ROWS):
                row = idx // INV_COLS
                col = idx % INV_COLS
                cx = grid_x + col * cell_w
                cy = grid_y + row * cell_h
                # Cell background
                pygame.draw.rect(self.screen, (20, 18, 14), (cx, cy, cell_w - 2, cell_h - 2), border_radius=3)
                pygame.draw.rect(self.screen, (60, 50, 40), (cx, cy, cell_w - 2, cell_h - 2), 1, border_radius=3)
                if idx < len(p.inventory):
                    item = p.inventory[idx]
                    ic = item.get_color()
                    # Item icon (colored square)
                    pygame.draw.rect(self.screen, ic, (cx + 8, cy + 8, cell_w - 18, cell_h - 18), border_radius=4)
                    pygame.draw.rect(self.screen, (min(255, ic[0]+60), min(255, ic[1]+60), min(255, ic[2]+60)),
                                     (cx + 8, cy + 8, cell_w - 18, cell_h - 18), 1, border_radius=4)
                    # Weapon class icon
                    icon_char = "B" if item.weapon_class == "bow" else "X"
                    it = self.font.render(icon_char, True, (20, 15, 10))
                    self.screen.blit(it, (cx + cell_w // 2 - it.get_width() // 2,
                                          cy + cell_h // 2 - it.get_height() // 2))

            # Tooltip for hovered item
            for idx in range(len(p.inventory)):
                row = idx // INV_COLS
                col = idx % INV_COLS
                cx = grid_x + col * cell_w
                cy = grid_y + row * cell_h
                if cx <= mx <= cx + cell_w and cy <= my <= cy + cell_h:
                    item = p.inventory[idx]
                    self._draw_weapon_tooltip(item, mx + 15, my)
                    break

            # Check hover on equipped
            if eq_x <= mx <= eq_x + 500 and eq_y + 28 <= my <= eq_y + 148:
                pass  # Already showing details above

            hint = self.font.render("[Left Click] Equip   [Right Click] Sell for Gold   [I/Esc] Close", True, (100, 95, 85))
            self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 50))

            pygame.display.flip()
            self.clock.tick(30)

    def _draw_weapon_tooltip(self, w: Weapon, x: int, y: int):
        """Draw a floating tooltip for a weapon."""
        lines = w.get_tooltip_lines()
        # Calculate size
        max_w = 0
        rendered = []
        for i, line in enumerate(lines):
            color = w.get_color() if i == 0 else (200, 190, 160)
            if line.startswith("  +"):
                color = (100, 200, 255)
            t = self.font.render(line, True, color)
            rendered.append(t)
            max_w = max(max_w, t.get_width())
        total_h = len(rendered) * 24 + 16
        # Keep on screen
        if x + max_w + 20 > WIDTH:
            x = WIDTH - max_w - 25
        if y + total_h > HEIGHT:
            y = HEIGHT - total_h - 10
        # Background
        pygame.draw.rect(self.screen, (15, 12, 10), (x, y, max_w + 20, total_h), border_radius=5)
        pygame.draw.rect(self.screen, w.get_color(), (x, y, max_w + 20, total_h), 1, border_radius=5)
        for i, t in enumerate(rendered):
            self.screen.blit(t, (x + 10, y + 8 + i * 24))

    # ---- SKILL TREE SCREEN (T key) ----
    def _skill_tree_screen(self):
        """D2-style skill tree with three tabs."""
        p = self.player
        tabs = ["bow", "crossbow", "passive"]
        tab_idx = 0
        running = True
        while running:
            mx, my = pygame.mouse.get_pos()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False
                    return
                if ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_t, pygame.K_ESCAPE):
                        running = False
                    elif ev.key == pygame.K_TAB:
                        tab_idx = (tab_idx + 1) % len(tabs)
                    elif ev.key in (pygame.K_1,):
                        tab_idx = 0
                    elif ev.key in (pygame.K_2,):
                        tab_idx = 1
                    elif ev.key in (pygame.K_3,):
                        tab_idx = 2
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    # Check skill buttons
                    tree = SKILL_TREES[tabs[tab_idx]]
                    for skill in tree["skills"]:
                        sx = WIDTH // 2 - 200 + skill["col"] * 200
                        sy = 220 + skill["row"] * 130
                        if sx <= mx <= sx + 160 and sy <= my <= sy + 100:
                            cur = p.skills.get(skill["id"], 0)
                            if cur < skill["max"] and p.skill_points > 0:
                                # Check requirement
                                req = skill.get("req")
                                if req is None or p.skills.get(req, 0) > 0:
                                    p.skills[skill["id"]] = cur + 1
                                    p.skill_points -= 1
                                    self.play_sound("levelup")

            # Draw
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 230))
            self.screen.blit(overlay, (0, 0))

            title = self.bigfont.render("- SKILL TREE -", True, C_GOLD)
            self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))
            pts_txt = self.font.render(f"Skill Points: {p.skill_points}", True, C_GOLD)
            self.screen.blit(pts_txt, (WIDTH // 2 - pts_txt.get_width() // 2, 55))

            # Tabs
            tab_colors = [(200, 160, 100), (160, 140, 200), (140, 200, 140)]
            for i, tab in enumerate(tabs):
                tx = WIDTH // 2 - 300 + i * 200
                ty = 85
                is_active = i == tab_idx
                color = tab_colors[i] if is_active else (80, 70, 60)
                pygame.draw.rect(self.screen, (30, 25, 20) if is_active else (15, 12, 10),
                                 (tx, ty, 190, 34), border_radius=5)
                pygame.draw.rect(self.screen, color, (tx, ty, 190, 34), 2 if is_active else 1, border_radius=5)
                tab_name = SKILL_TREES[tab]["name"]
                tt = self.font.render(f"{i+1}. {tab_name}", True, color)
                self.screen.blit(tt, (tx + 10, ty + 6))

            # Draw current tree
            tree = SKILL_TREES[tabs[tab_idx]]
            for skill in tree["skills"]:
                sx = WIDTH // 2 - 200 + skill["col"] * 200
                sy = 220 + skill["row"] * 130
                cur = p.skills.get(skill["id"], 0)
                maxl = skill["max"]
                req = skill.get("req")
                can_learn = p.skill_points > 0 and cur < maxl
                if req and p.skills.get(req, 0) == 0:
                    can_learn = False
                locked = req and p.skills.get(req, 0) == 0

                # Draw connection line to required skill
                if req:
                    for rs in tree["skills"]:
                        if rs["id"] == req:
                            rx = WIDTH // 2 - 200 + rs["col"] * 200 + 80
                            ry = 220 + rs["row"] * 130 + 100
                            pygame.draw.line(self.screen, (60, 55, 45), (rx, ry), (sx + 80, sy), 2)
                            break

                # Skill box
                bg_color = (40, 35, 25) if cur > 0 else (20, 18, 14)
                border_color = C_GOLD if cur > 0 else ((80, 70, 55) if not locked else (40, 35, 30))
                if locked:
                    bg_color = (12, 10, 8)
                pygame.draw.rect(self.screen, bg_color, (sx, sy, 160, 100), border_radius=6)
                pygame.draw.rect(self.screen, border_color, (sx, sy, 160, 100), 2 if cur > 0 else 1,
                                 border_radius=6)

                # Skill name
                name_color = C_GOLD if cur > 0 else ((180, 170, 140) if not locked else (80, 75, 65))
                nt = self.font.render(skill["name"], True, name_color)
                self.screen.blit(nt, (sx + 80 - nt.get_width() // 2, sy + 8))

                # Level indicator
                level_txt = self.font.render(f"{cur}/{maxl}", True, C_GOLD if cur > 0 else (120, 115, 100))
                self.screen.blit(level_txt, (sx + 80 - level_txt.get_width() // 2, sy + 32))

                # Pips
                pip_total_w = maxl * 14
                pip_start = sx + 80 - pip_total_w // 2
                for pi in range(maxl):
                    pc = C_GOLD if pi < cur else (50, 45, 35)
                    pygame.draw.rect(self.screen, pc, (pip_start + pi * 14, sy + 56, 10, 6), border_radius=2)

                # Description on hover
                if sx <= mx <= sx + 160 and sy <= my <= sy + 100:
                    desc_bg = pygame.Surface((320, 30), pygame.SRCALPHA)
                    desc_bg.fill((10, 8, 6, 220))
                    self.screen.blit(desc_bg, (sx - 80, sy + 102))
                    dt = self.font.render(skill["desc"], True, (200, 190, 160))
                    self.screen.blit(dt, (sx - 80 + 10, sy + 106))

                # + indicator
                if can_learn:
                    plus = self.font.render("+", True, (100, 255, 100))
                    self.screen.blit(plus, (sx + 140, sy + 4))

            hint = self.font.render("[Click] Learn Skill   [Tab/1-3] Switch Tree   [T/Esc] Close", True, (100, 95, 85))
            self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 40))

            pygame.display.flip()
            self.clock.tick(30)

    # ---- VENDOR SHOP SCREEN (V key near vendor) ----
    def _vendor_screen(self):
        """D2-style vendor buy/sell interface."""
        if not self.vendor:
            return
        p = self.player
        v = self.vendor
        tab = 0  # 0 = buy, 1 = sell
        scroll_buy = 0
        scroll_sell = 0
        running = True
        while running:
            mx, my = pygame.mouse.get_pos()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False
                    return
                if ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_v, pygame.K_ESCAPE):
                        running = False
                    elif ev.key == pygame.K_TAB:
                        tab = 1 - tab
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    # Tab clicks
                    if 200 <= mx <= 400 and 80 <= my <= 110:
                        tab = 0
                    elif 420 <= mx <= 620 and 80 <= my <= 110:
                        tab = 1

                    if tab == 0:
                        # Buy from vendor
                        for i, w in enumerate(v.stock):
                            iy = 160 + i * 70 - scroll_buy
                            if 200 <= mx <= WIDTH - 200 and iy <= my <= iy + 64:
                                price = self._get_vendor_buy_price(w)
                                if p.gold >= price and len(p.inventory) < INV_COLS * INV_ROWS:
                                    p.gold -= price
                                    p.inventory.append(w)
                                    v.stock.pop(i)
                                    self.play_sound("gold")
                                    self.add_floating_text(p.pos.x, p.pos.y - 20,
                                                           f"-{price}g", (255, 100, 100), 1.0)
                                break
                    else:
                        # Sell to vendor
                        for i, w in enumerate(p.inventory):
                            iy = 160 + i * 70 - scroll_sell
                            if 200 <= mx <= WIDTH - 200 and iy <= my <= iy + 64:
                                price = self._get_vendor_sell_price(w)
                                p.gold += price
                                v.stock.append(w)
                                p.inventory.pop(i)
                                self.play_sound("gold")
                                self.add_floating_text(p.pos.x, p.pos.y - 20,
                                                       f"+{price}g", C_GOLD, 1.0)
                                break

                if ev.type == pygame.MOUSEBUTTONDOWN:
                    if ev.button == 4:  # scroll up
                        if tab == 0:
                            scroll_buy = max(0, scroll_buy - 70)
                        else:
                            scroll_sell = max(0, scroll_sell - 70)
                    elif ev.button == 5:  # scroll down
                        if tab == 0:
                            scroll_buy += 70
                        else:
                            scroll_sell += 70

            # Draw
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 230))
            self.screen.blit(overlay, (0, 0))

            # Header
            title = self.bigfont.render(f"- {v.name}'s Trading Post -", True, C_GOLD)
            self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 25))
            gold_txt = self.font.render(f"Gold: {p.gold}", True, C_GOLD)
            self.screen.blit(gold_txt, (WIDTH - 280, 30))
            inv_txt = self.font.render(f"Inventory: {len(p.inventory)}/{INV_COLS * INV_ROWS}", True, (180, 170, 140))
            self.screen.blit(inv_txt, (WIDTH - 280, 55))

            # Tabs
            for ti, (tlabel, tx) in enumerate([("Buy", 200), ("Sell", 420)]):
                is_active = ti == tab
                color = C_GOLD if is_active else (100, 90, 70)
                bg = (40, 35, 25) if is_active else (20, 18, 14)
                pygame.draw.rect(self.screen, bg, (tx, 80, 190, 30), border_radius=5)
                pygame.draw.rect(self.screen, color, (tx, 80, 190, 30), 2 if is_active else 1, border_radius=5)
                tt = self.font.render(tlabel, True, color)
                self.screen.blit(tt, (tx + 95 - tt.get_width() // 2, 85))

            # Separator
            pygame.draw.line(self.screen, C_GOTHIC_FRAME, (200, 120), (WIDTH - 200, 120), 1)

            # Clip region for items
            clip_rect = pygame.Rect(190, 130, WIDTH - 380, HEIGHT - 200)

            if tab == 0:
                # Buy tab — show vendor stock
                if not v.stock:
                    no_stock = self.font.render("Sold out! Come back next level.", True, (120, 115, 100))
                    self.screen.blit(no_stock, (WIDTH // 2 - no_stock.get_width() // 2, 250))
                for i, w in enumerate(v.stock):
                    iy = 160 + i * 70 - scroll_buy
                    if iy < 125 or iy > HEIGHT - 80:
                        continue
                    price = self._get_vendor_buy_price(w)
                    wc = w.get_color()
                    can_afford = p.gold >= price and len(p.inventory) < INV_COLS * INV_ROWS
                    # Hover highlight
                    hovered = 200 <= mx <= WIDTH - 200 and iy <= my <= iy + 64
                    bg = (35, 30, 22) if hovered else (22, 18, 14)
                    pygame.draw.rect(self.screen, bg, (200, iy, WIDTH - 400, 64), border_radius=5)
                    pygame.draw.rect(self.screen, wc if hovered else (50, 45, 35),
                                     (200, iy, WIDTH - 400, 64), 1, border_radius=5)
                    # Item icon
                    pygame.draw.rect(self.screen, wc, (215, iy + 10, 44, 44), border_radius=5)
                    icon_char = "B" if w.weapon_class == "bow" else "X"
                    it = self.font.render(icon_char, True, (20, 15, 10))
                    self.screen.blit(it, (237 - it.get_width() // 2, iy + 22))
                    # Weapon info
                    nt = self.bigfont.render(w.name, True, wc)
                    self.screen.blit(nt, (275, iy + 5))
                    rarity_label = f"[{RARITY_NAMES[w.rarity]}] {w.weapon_class.title()}  Dmg: {w.dmg_min}-{w.dmg_max}  Spd: {w.attack_speed:.1f}"
                    rt = self.font.render(rarity_label, True, (160, 155, 140))
                    self.screen.blit(rt, (275, iy + 36))
                    # Mods summary (compact)
                    mod_x = WIDTH - 550
                    for mk, mv in w.mods.items():
                        if mv:
                            label = mk.replace("_", " ").title()
                            mt = self.font.render(f"+{mv} {label}", True, (100, 200, 255))
                            self.screen.blit(mt, (mod_x, iy + 8))
                            mod_x += mt.get_width() + 15
                            if mod_x > WIDTH - 350:
                                break
                    # Price
                    price_color = C_GOLD if can_afford else (160, 60, 60)
                    pt = self.bigfont.render(f"{price}g", True, price_color)
                    self.screen.blit(pt, (WIDTH - 300, iy + 15))
                    if not can_afford:
                        reason = "Not enough gold" if p.gold < price else "Inventory full"
                        rt2 = self.font.render(reason, True, (140, 60, 60))
                        self.screen.blit(rt2, (WIDTH - 300, iy + 42))
            else:
                # Sell tab — show player inventory
                if not p.inventory:
                    no_inv = self.font.render("Your inventory is empty.", True, (120, 115, 100))
                    self.screen.blit(no_inv, (WIDTH // 2 - no_inv.get_width() // 2, 250))
                for i, w in enumerate(p.inventory):
                    iy = 160 + i * 70 - scroll_sell
                    if iy < 125 or iy > HEIGHT - 80:
                        continue
                    price = self._get_vendor_sell_price(w)
                    wc = w.get_color()
                    hovered = 200 <= mx <= WIDTH - 200 and iy <= my <= iy + 64
                    bg = (35, 30, 22) if hovered else (22, 18, 14)
                    pygame.draw.rect(self.screen, bg, (200, iy, WIDTH - 400, 64), border_radius=5)
                    pygame.draw.rect(self.screen, wc if hovered else (50, 45, 35),
                                     (200, iy, WIDTH - 400, 64), 1, border_radius=5)
                    # Item icon
                    pygame.draw.rect(self.screen, wc, (215, iy + 10, 44, 44), border_radius=5)
                    icon_char = "B" if w.weapon_class == "bow" else "X"
                    it = self.font.render(icon_char, True, (20, 15, 10))
                    self.screen.blit(it, (237 - it.get_width() // 2, iy + 22))
                    # Weapon info
                    nt = self.bigfont.render(w.name, True, wc)
                    self.screen.blit(nt, (275, iy + 5))
                    rarity_label = f"[{RARITY_NAMES[w.rarity]}] {w.weapon_class.title()}  Dmg: {w.dmg_min}-{w.dmg_max}  Spd: {w.attack_speed:.1f}"
                    rt = self.font.render(rarity_label, True, (160, 155, 140))
                    self.screen.blit(rt, (275, iy + 36))
                    # Sell price
                    pt = self.bigfont.render(f"+{price}g", True, C_GOLD)
                    self.screen.blit(pt, (WIDTH - 300, iy + 15))
                    sell_label = self.font.render("Click to sell", True, (180, 170, 120) if hovered else (100, 95, 80))
                    self.screen.blit(sell_label, (WIDTH - 300, iy + 42))

            # Tooltip for hovered item
            items_list = v.stock if tab == 0 else p.inventory
            scroll = scroll_buy if tab == 0 else scroll_sell
            for i, w in enumerate(items_list):
                iy = 160 + i * 70 - scroll
                if 200 <= mx <= WIDTH - 200 and iy <= my <= iy + 64 and 125 < iy < HEIGHT - 80:
                    self._draw_weapon_tooltip(w, mx + 15, my)
                    break

            hint = self.font.render("[Tab] Switch Buy/Sell   [Click] Buy or Sell   [Scroll] Navigate   [V/Esc] Close",
                                    True, (100, 95, 85))
            self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 40))

            pygame.display.flip()
            self.clock.tick(30)

    def _get_save_path(self) -> str:
        """Return save file path in the same directory as the game."""
        game_dir = os.path.dirname(os.path.abspath(sys.argv[0])) if sys.argv[0] else os.getcwd()
        return os.path.join(game_dir, "dungeon_crawl_save.json")

    def _save_game(self):
        """Save character and game state to JSON file."""
        p = self.player
        save_data = {
            "version": 1,
            "player": {
                "level": p.level,
                "xp": p.xp,
                "xp_to_next": p.xp_to_next,
                "gold": p.gold,
                "hp": p.hp,
                "mana": p.mana,
                "potions_hp": p.potions_hp,
                "potions_mana": p.potions_mana,
                "strength": p.strength,
                "dexterity": p.dexterity,
                "vitality": p.vitality,
                "energy": p.energy,
                "stat_points": p.stat_points,
                "skill_points": p.skill_points,
                "skills": p.skills,
                "crit_chance": p.crit_chance,
                "lives": p.lives,
                "max_lives": p.max_lives,
                "weapon": {
                    "name": p.weapon.name,
                    "dmg_min": p.weapon.dmg_min,
                    "dmg_max": p.weapon.dmg_max,
                    "attack_speed": p.weapon.attack_speed,
                    "ranged": p.weapon.ranged,
                    "rarity": p.weapon.rarity,
                    "weapon_class": p.weapon.weapon_class,
                    "mods": p.weapon.mods,
                    "base_name": p.weapon.base_name,
                    "prefix": p.weapon.prefix,
                    "suffix": p.weapon.suffix,
                    "set_name": p.weapon.set_name,
                    "ilvl": p.weapon.ilvl,
                },
                "inventory": [
                    {
                        "name": w.name, "dmg_min": w.dmg_min, "dmg_max": w.dmg_max,
                        "attack_speed": w.attack_speed, "ranged": w.ranged,
                        "rarity": w.rarity, "weapon_class": w.weapon_class,
                        "mods": w.mods, "base_name": w.base_name,
                        "prefix": w.prefix, "suffix": w.suffix,
                        "set_name": w.set_name, "ilvl": w.ilvl,
                    }
                    for w in p.inventory
                ],
            },
            "game": {
                "current_level": self.current_level,
                "current_biome": self.current_biome,
                "wave": self.wave,
                "kills": self.kills,
                "difficulty": self.difficulty_name,
            },
        }
        try:
            with open(self._get_save_path(), "w") as f:
                json.dump(save_data, f, indent=2)
            self.play_sound("save")
            self.add_floating_text(self.player.pos.x, self.player.pos.y - 30,
                                   "Game Saved!", (100, 255, 100), 1.5)
            return True
        except Exception:
            self.add_floating_text(self.player.pos.x, self.player.pos.y - 30,
                                   "Save Failed!", (255, 80, 80), 1.5)
            return False

    def _weapon_from_dict(self, d: dict) -> Weapon:
        """Reconstruct a Weapon from a save dict."""
        return Weapon(
            name=d["name"], dmg_min=d["dmg_min"], dmg_max=d["dmg_max"],
            attack_speed=d["attack_speed"], ranged=d["ranged"],
            rarity=d.get("rarity", RARITY_NORMAL),
            weapon_class=d.get("weapon_class", "bow"),
            mods=d.get("mods", {}), base_name=d.get("base_name", ""),
            prefix=d.get("prefix", ""), suffix=d.get("suffix", ""),
            set_name=d.get("set_name", ""), ilvl=d.get("ilvl", 1),
        )

    def _load_game(self) -> bool:
        """Load saved game. Returns True if loaded successfully."""
        path = self._get_save_path()
        if not os.path.exists(path):
            return False
        try:
            with open(path, "r") as f:
                data = json.load(f)
            if data.get("version") != 1:
                return False
            pd = data["player"]
            gd = data["game"]
            # Restore game state
            self.difficulty_name = gd.get("difficulty", "Normal")
            self.diff = DIFFICULTY.get(self.difficulty_name, DIFFICULTY["Normal"])
            global MAX_ACTIVE_ENEMIES
            MAX_ACTIVE_ENEMIES = self.diff["max_enemies"]
            self.current_level = gd["current_level"]
            self.current_biome = gd["current_biome"]
            self.wave = gd["wave"]
            self.kills = gd["kills"]
            # Rebuild dungeon for current level
            self.dungeon = Dungeon(level=self.current_level, biome=self.current_biome)
            rx, ry = self.dungeon.center(self.dungeon.rooms[0]) if self.dungeon.rooms else (MAP_W // 2, MAP_H // 2)
            self.player.pos = Vec(rx * TILE + TILE / 2, ry * TILE + TILE / 2)
            # Restore player stats
            p = self.player
            p.level = pd["level"]
            p.xp = pd["xp"]
            p.xp_to_next = pd["xp_to_next"]
            p.gold = pd["gold"]
            p.strength = pd["strength"]
            p.dexterity = pd["dexterity"]
            p.vitality = pd["vitality"]
            p.energy = pd["energy"]
            p.stat_points = pd.get("stat_points", 0)
            p.skill_points = pd.get("skill_points", 0)
            p.skills = pd.get("skills", {})
            p.crit_chance = pd.get("crit_chance", 5.0)
            p.lives = pd.get("lives", 3)
            p.max_lives = pd.get("max_lives", 3)
            p.potions_hp = pd.get("potions_hp", 1)
            p.potions_mana = pd.get("potions_mana", 1)
            p.hp = min(pd.get("hp", p.max_hp()), p.max_hp())
            p.mana = min(pd.get("mana", p.max_mana()), p.max_mana())
            p.weapon = self._weapon_from_dict(pd["weapon"])
            p.inventory = [self._weapon_from_dict(w) for w in pd.get("inventory", [])]
            # Rebuild level
            self._build_texture_cache(self.current_biome)
            self.enemies.clear()
            self.projectiles.clear()
            self.loots.clear()
            self.particles.clear()
            self.floating_texts.clear()
            self.corpses.clear()
            self.chests.clear()
            self.crates.clear()
            self.lightning_chains.clear()
            self._spawn_chests()
            self._spawn_crates()
            self._spawn_vendor()
            self.dungeon.mark_seen_radius(self.player.pos)
            self.boss_spawned = False
            self.spawn_timer = SPAWN_INTERVAL
            return True
        except Exception:
            return False

    def _delete_save(self):
        """Delete the save file."""
        path = self._get_save_path()
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

    def _death_screen(self) -> str:
        """Show death screen. Returns 'respawn', 'quit', or 'start'."""
        p = self.player
        # Death fade
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for i in range(30):
            for ev in pygame.event.get():
                pass
            overlay.fill((0, 0, 0, 8))
            self.screen.blit(overlay, (0, 0))
            pygame.display.flip()
            self.clock.tick(30)

        selecting = True
        idx = 0
        while selecting:
            self.clock.tick(30)
            self.screen.fill((8, 4, 4))
            # Blood drip effect
            for i in range(20):
                x = random.randint(100, WIDTH - 100)
                h = random.randint(20, 120)
                pygame.draw.line(self.screen, (random.randint(60, 100), 5, 5),
                                 (x, 0), (x, h), random.randint(1, 3))

            txt = self.titlefont.render("YOU HAVE DIED", True, (180, 30, 30))
            self.screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 120))

            # Stats
            stats = [
                f"Level {p.level}  -  Depth {self.current_level} ({BIOME_NAMES.get(self.current_biome, '')})  -  Wave {self.wave}",
                f"Gold: {p.gold}   Kills: {self.kills}   Difficulty: {self.difficulty_name}",
                f"Weapon: {p.weapon.name} [{RARITY_NAMES[p.weapon.rarity]}]",
            ]
            y = HEIGHT // 2 - 50
            for line in stats:
                st = self.subfont.render(line, True, (140, 100, 100))
                self.screen.blit(st, (WIDTH // 2 - st.get_width() // 2, y))
                y += 30

            # Lives info
            lives_text = f"Lives remaining: {p.lives}"
            lives_col = (100, 200, 100) if p.lives > 0 else (200, 60, 60)
            lt = self.bigfont.render(lives_text, True, lives_col)
            self.screen.blit(lt, (WIDTH // 2 - lt.get_width() // 2, y + 10))
            y += 55

            # Options
            options = []
            if p.lives > 0:
                options.append(("Respawn Here", "respawn",
                               f"Continue from where you died ({p.lives} {'lives' if p.lives != 1 else 'life'} left)"))
            else:
                options.append(("Return to Start", "start",
                               "No lives left - return to the beginning of this depth"))
            options.append(("Save & Quit", "quit", "Save your character and exit"))

            for i, (label, action, desc) in enumerate(options):
                is_sel = (i == idx)
                col = C_GOLD if is_sel else (120, 100, 90)
                marker = "> " if is_sel else "  "
                ot = self.bigfont.render(f"{marker}{label}", True, col)
                self.screen.blit(ot, (WIDTH // 2 - 160, y))
                if is_sel:
                    dt = self.font.render(desc, True, (160, 140, 120))
                    self.screen.blit(dt, (WIDTH // 2 - 160, y + 36))
                y += 55

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        idx = (idx - 1) % len(options)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        idx = (idx + 1) % len(options)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        return options[idx][1]
                    elif event.key == pygame.K_ESCAPE:
                        return "quit"

        return "quit"

    def _respawn_player(self, at_start: bool = False):
        """Respawn the player, restoring HP/mana."""
        p = self.player
        if at_start:
            # Go back to room 0 of current level, reset lives
            p.lives = p.max_lives
            rx, ry = self.dungeon.center(self.dungeon.rooms[0]) if self.dungeon.rooms else (MAP_W // 2, MAP_H // 2)
            p.pos = Vec(rx * TILE + TILE / 2, ry * TILE + TILE / 2)
            # Clear enemies to give breathing room
            self.enemies.clear()
            self.projectiles.clear()
            self.spawn_timer = SPAWN_INTERVAL * 2
            # Lose some gold as penalty
            gold_lost = p.gold // 4
            p.gold -= gold_lost
            self.add_floating_text(p.pos.x, p.pos.y - 40,
                                   f"Lost {gold_lost} gold", (200, 80, 80), 1.5)
        else:
            p.lives -= 1
            # Ensure player is on a valid floor tile (knockback can push into walls)
            tx, ty = int(p.pos.x // TILE), int(p.pos.y // TILE)
            if (tx < 0 or tx >= MAP_W or ty < 0 or ty >= MAP_H
                    or self.dungeon.tiles[tx][ty] != FLOOR
                    or self._circle_collides(p.pos, p.radius)):
                # Player is stuck in a wall — find nearest floor tile
                safe = self._safe_loot_pos(p.pos, 60)
                p.pos = safe
            # Clear nearby enemies so player doesn't immediately die again
            safe_dist = 250
            self.enemies = [e for e in self.enemies
                            if (e.pos - p.pos).length() > safe_dist or isinstance(e, TreasureGoblin)]
            self.projectiles = [pr for pr in self.projectiles if not pr.hostile]
        # Restore HP, mana, and reset movement state
        p.hp = p.max_hp()
        p.mana = p.max_mana()
        p.vel = Vec(0, 0)
        p.iframes = 2.0  # generous invincibility on respawn
        p.shield = 0
        p.dmg_timer = 0
        p.dmg_mult = 1.0
        p.dash_timer = 0
        p.dash_cd = 0
        self.play_sound("respawn")
        self.emit_particles(p.pos.x, p.pos.y, 30, (100, 200, 255), speed=80, life=1.0, gravity=-40)
        self.add_floating_text(p.pos.x, p.pos.y - 30,
                               "RESPAWNED!" if not at_start else "RETURNED TO START!",
                               (100, 200, 255), 1.5)
        self.dungeon.mark_seen_radius(p.pos)

    # ---- Main Loop ----
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.game_time += dt
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.paused = True
                    if event.key == pygame.K_p:
                        self.paused = not self.paused
                    if event.key == pygame.K_F1:
                        self._help_overlay()
                    if event.key == pygame.K_c:
                        self._character_screen()
                    if event.key == pygame.K_i:
                        self._inventory_screen()
                    if event.key == pygame.K_t:
                        self._skill_tree_screen()
                    if event.key == pygame.K_v and self.show_vendor_hint:
                        self._vendor_screen()
                    if event.key == pygame.K_F11:
                        self.fullscreen = not self.fullscreen
                        if self.fullscreen:
                            self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
                        else:
                            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
                        self.light_map = pygame.Surface((WIDTH, HEIGHT))
            if self.paused:
                self._pause_screen()
                continue
            self.handle_input(dt)
            self.update_player(dt)
            self.update_enemies(dt)
            self.update_projectiles(dt)
            self.update_loot(dt)
            self.update_spawning(dt)
            self.update_particles(dt)
            self.update_floating_texts(dt)
            self.update_chests(dt)
            self.update_crates(dt)
            self.update_corpses(dt)
            self.update_blood_stains(dt)
            self.update_screen_shake(dt)
            # Update lightning chains
            self.lightning_chains = [(s, e, l - dt) for s, e, l in self.lightning_chains if l - dt > 0]
            if self.player.hp <= 0:
                result = self._death_screen()
                if result == "respawn":
                    self._respawn_player(at_start=False)
                elif result == "start":
                    self._respawn_player(at_start=True)
                else:  # quit
                    self._save_game()
                    self.running = False
                    continue
            self.draw()


if __name__ == "__main__":
    try:
        Game().run()
    except Exception as e:
        print("Fatal error:", e)
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit(0)
