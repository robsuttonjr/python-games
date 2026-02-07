
import math
import random
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import pygame

# ---------- Config ----------
WIDTH, HEIGHT = 1024, 576
FPS = 60
FONT_NAME = "consolas"

# Difficulty presets (set at start)
DIFFICULTY = {
    "Easy":    {"enemy_hp":0.9, "enemy_dmg":0.8, "enemy_speed":0.95, "max_enemies":6},
    "Normal":  {"enemy_hp":1.0, "enemy_dmg":1.0, "enemy_speed":1.0,  "max_enemies":7},
    "Hard":    {"enemy_hp":1.2, "enemy_dmg":1.25,"enemy_speed":1.05, "max_enemies":9},
}

PLAYER_SPEED = 250  # px/s
PLAYER_HP = 140
PLAYER_MANA = 80

# Shooting balance
BASIC_DMG = (7, 12)
POWER_DMG = (18, 30)
BASIC_CD = 0.18
POWER_CD = 0.60
POWER_MANA_COST = 12
PROJECTILE_SPEED = 560
BASIC_RADIUS = 4
POWER_RADIUS = 6
BASIC_PIERCE = 1
POWER_PIERCE = 2

# Dash
DASH_SPEED = 520
DASH_TIME = 0.22
DASH_CD = 1.5
IFRAME_TIME = 0.25

POTION_HEAL = 50
POTION_MANA = 40

# Enemy base (scaled by difficulty & level)
ENEMY_BASE_HP = 40
ENEMY_BASE_DMG = (4, 8)
ENEMY_SPEED = 110
SPAWN_INTERVAL = 6.0
WAVE_SCALE = 1.10
MAX_ACTIVE_ENEMIES = 7  # overridden by difficulty

# --- Elite (sub-boss) packs ---
ELITE_PACK_CHANCE = 0.35
PACK_SIZE_RANGE = (3, 6)
ELITE_MULT = {"hp": 2.6, "dmg": 1.8, "spd": 1.08, "radius": 18}
AURA_RADIUS = 220
AURAS = {
    "haste":   {"speed": 1.28, "damage": 1.00, "taken": 1.00, "color": (120,200,255)},
    "frenzy":  {"speed": 1.00, "damage": 1.35, "taken": 1.00, "color": (255,150,90)},
    "guardian":{"speed": 1.00, "damage": 1.00, "taken": 0.66, "color": (120,255,160)},
}

# Boss
BOSS_HP = 600
BOSS_DMG = (8, 14)
BOSS_SHOT_CD = (1.0, 1.6)
BOSS_PROJ_SPEED = 360

# Pickups
DMG_BOOST_MULT = 1.6
DMG_BOOST_TIME = 8.0
SHIELD_POINTS = 70
PICKUP_SPAWN_CHANCE = 0.25

GOLD_DROP = (3, 12)
POTION_DROP_CHANCE = 0.10
LOOT_DROP_CHANCE = 0.08
DMG_PICKUP_DROP_CHANCE = 0.06
SHIELD_PICKUP_DROP_CHANCE = 0.06

# Dungeon
TILE = 34
MAP_W, MAP_H = 110, 85  # tiles
LEVELS = 3

WALL = 1
FLOOR = 0
TRAP_TILE = 2  # spike trap
POISON_TRAP_TILE = 3  # poison trap

# --- Spells ---
FIREBALL_MANA = 25
FIREBALL_CD = 3.0
FIREBALL_RADIUS = 80
FIREBALL_DMG = (30, 50)
FIREBALL_PROJ_SPEED = 400

FROST_NOVA_MANA = 20
FROST_NOVA_CD = 5.0
FROST_NOVA_RADIUS = 140
FROST_NOVA_DMG = (8, 14)
FROST_NOVA_SLOW_DUR = 3.0
FROST_NOVA_SLOW_MULT = 0.4

HEAL_AURA_MANA = 30
HEAL_AURA_CD = 8.0
HEAL_AURA_AMOUNT = 40
HEAL_AURA_HOT_DUR = 4.0  # heal-over-time duration
HEAL_AURA_HOT_TICK = 5   # hp per tick

# --- Traps ---
SPIKE_TRAP_DMG = (8, 16)
SPIKE_TRAP_CD = 2.0  # re-arm time
POISON_TRAP_DUR = 4.0
POISON_TRAP_DPS = 3

# --- Weapon tiers ---
WEAPON_TIERS = [
    {"name": "Rusty Dagger",       "dmg": (6,  10), "speed": 2.5, "ranged": False, "tier": 0},
    {"name": "Iron Shortsword",    "dmg": (9,  14), "speed": 2.2, "ranged": False, "tier": 1},
    {"name": "Flame Wand",         "dmg": (11, 18), "speed": 1.8, "ranged": True,  "tier": 1},
    {"name": "Steel Longsword",    "dmg": (14, 22), "speed": 2.0, "ranged": False, "tier": 2},
    {"name": "Arcane Staff",       "dmg": (16, 26), "speed": 1.6, "ranged": True,  "tier": 2},
    {"name": "Obsidian Cleaver",   "dmg": (20, 32), "speed": 1.4, "ranged": False, "tier": 3},
    {"name": "Thunderbolt Scepter","dmg": (18, 30), "speed": 1.5, "ranged": True,  "tier": 3},
    {"name": "Demon Edge",         "dmg": (26, 40), "speed": 1.2, "ranged": False, "tier": 4},
    {"name": "Void Staff",         "dmg": (22, 36), "speed": 1.3, "ranged": True,  "tier": 4},
]

# ---------- Helpers ----------
Vec = pygame.math.Vector2

@dataclass
class Weapon:
    name: str
    dmg_min: int
    dmg_max: int
    attack_speed: float
    ranged: bool
    tier: int = 0
    def roll_damage(self) -> int:
        return random.randint(self.dmg_min, self.dmg_max)

@dataclass
class StatusEffect:
    kind: str       # "poison", "slow", "burn"
    duration: float
    value: float    # dps for poison/burn, speed mult for slow
    tick_timer: float = 0.0

@dataclass
class Particle:
    pos: Vec
    vel: Vec
    color: Tuple[int,int,int]
    life: float
    max_life: float
    size: float = 3.0

@dataclass
class FloatingText:
    pos: Vec
    text: str
    color: Tuple[int,int,int]
    life: float = 1.0
    max_life: float = 1.0

@dataclass
class Loot:
    pos: Vec
    gold: int = 0
    potion_hp: bool = False
    potion_mana: bool = False
    weapon: Optional[Weapon] = None
    dmg_boost: bool = False
    shield_boost: bool = False
    ttl: float = 30.0

@dataclass
class Projectile:
    pos: Vec
    vel: Vec
    dmg: int
    ttl: float
    radius: int
    pierce: int = 1
    hostile: bool = False
    is_fireball: bool = False  # explodes on hit

@dataclass
class Entity:
    pos: Vec
    vel: Vec
    radius: int

@dataclass
class Player(Entity):
    hp: int = PLAYER_HP
    max_hp: int = PLAYER_HP
    mana: int = PLAYER_MANA
    max_mana: int = PLAYER_MANA
    level: int = 1
    xp: int = 0
    xp_to_next: int = 40
    gold: int = 0
    potions_hp: int = 1
    potions_mana: int = 1
    basic_cd: float = 0.0
    power_cd: float = 0.0
    weapon: Weapon = field(default_factory=lambda: Weapon("Rusty Dagger", 6, 10, 2.5, False, 0))
    dmg_mult: float = 1.0
    dmg_timer: float = 0.0
    shield: int = 0
    # dash
    dash_cd: float = 0.0
    dash_timer: float = 0.0
    iframes: float = 0.0
    # spells
    fireball_cd: float = 0.0
    frost_nova_cd: float = 0.0
    heal_aura_cd: float = 0.0
    spell_fireball: bool = False   # unlocked?
    spell_frost_nova: bool = False
    spell_heal_aura: bool = False
    # status effects
    effects: List[StatusEffect] = field(default_factory=list)
    # heal over time
    hot_timer: float = 0.0
    hot_tick_timer: float = 0.0
    # mana regen
    mana_regen: float = 2.0  # per second

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
    # dynamic aura-modified multipliers (reset each frame)
    mult_speed: float = 1.0
    mult_damage: float = 1.0
    mult_taken: float = 1.0
    # basic ranged minion support
    shot_cd: float = 0.0
    # status effects
    effects: List[StatusEffect] = field(default_factory=list)

    def roll_damage(self) -> int:
        base = random.randint(self.dmg_min, self.dmg_max)
        return int(base * self.mult_damage)

    def get_slow_mult(self) -> float:
        worst = 1.0
        for eff in self.effects:
            if eff.kind == "slow":
                worst = min(worst, eff.value)
        return worst

@dataclass
class Elite(Enemy):
    aura: str = "haste"
    aura_radius: int = AURA_RADIUS

@dataclass
class Boss(Enemy):
    shot_cd: float = 1.0

@dataclass
class Trap:
    tx: int
    ty: int
    kind: str  # "spike" or "poison"
    cooldown: float = 0.0
    armed: bool = True

class Dungeon:
    def __init__(self, level: int = 1):
        self.level = level
        self.tiles = [[WALL for _ in range(MAP_H)] for _ in range(MAP_W)]
        self.seen = [[False for _ in range(MAP_H)] for _ in range(MAP_W)]
        self.rooms: List[pygame.Rect] = []
        self.scenery: List[Tuple[int,int,str]] = []
        self.traps: List[Trap] = []
        self.stairs_tx = None
        self.stairs_ty = None
        self.generate()

    def generate(self):
        rng = random.Random()
        max_rooms = 30 + self.level * 6
        min_size, max_size = 6, 13
        for _ in range(max_rooms):
            w = rng.randint(min_size, max_size)
            h = rng.randint(min_size, max_size)
            x = rng.randint(2, MAP_W - w - 3)
            y = rng.randint(2, MAP_H - h - 3)
            new = pygame.Rect(x, y, w, h)
            if any(new.colliderect(r.inflate(2,2)) for r in self.rooms):
                continue
            self.carve_room(new)
            if self.rooms:
                px, py = self.center(self.rooms[-1])
                nx, ny = self.center(new)
                self.carve_tunnel(px, py, nx, ny)
            self.rooms.append(new)
            # scenery
            for _ in range(rng.randint(0, 2)):
                tx = rng.randint(new.left+1, new.right-2)
                ty = rng.randint(new.top+1, new.bottom-2)
                self.tiles[tx][ty] = WALL
                self.scenery.append((tx, ty, 'pillar' if rng.random()<0.6 else 'crate'))
            # traps (more on higher levels, skip first room)
            if len(self.rooms) > 1:
                trap_count = rng.randint(0, 1 + self.level)
                for _ in range(trap_count):
                    ttx = rng.randint(new.left+1, new.right-2)
                    tty = rng.randint(new.top+1, new.bottom-2)
                    if self.tiles[ttx][tty] == FLOOR:
                        trap_kind = "spike" if rng.random() < 0.6 else "poison"
                        self.traps.append(Trap(tx=ttx, ty=tty, kind=trap_kind))
        # borders
        for x in range(MAP_W):
            self.tiles[x][0] = WALL
            self.tiles[x][MAP_H-1] = WALL
        for y in range(MAP_H):
            self.tiles[0][y] = WALL
            self.tiles[MAP_W-1][y] = WALL
        # stairs at last room
        if self.rooms:
            sx, sy = self.center(self.rooms[-1])
            self.stairs_tx, self.stairs_ty = sx, sy
            self.tiles[sx][sy] = FLOOR

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
        for x in range(min(x1,x2), max(x1,x2)+1):
            for dy in (-1,0,1):
                if 0 <= y+dy < MAP_H:
                    self.tiles[x][y+dy] = FLOOR

    def carve_v_tunnel(self, y1, y2, x):
        for y in range(min(y1,y2), max(y1,y2)+1):
            for dx in (-1,0,1):
                if 0 <= x+dx < MAP_W:
                    self.tiles[x+dx][y] = FLOOR

    def center(self, rect: pygame.Rect):
        return rect.left + rect.w//2, rect.top + rect.h//2

    def is_solid_at_px(self, pos: Vec) -> bool:
        tx = int(pos.x // TILE)
        ty = int(pos.y // TILE)
        if tx < 0 or ty < 0 or tx >= MAP_W or ty >= MAP_H:
            return True
        return self.tiles[tx][ty] == WALL

    def mark_seen_radius(self, pos: Vec, radius_px: int = 200):
        r2 = radius_px*radius_px
        min_tx = max(0, int((pos.x - radius_px)//TILE))
        max_tx = min(MAP_W-1, int((pos.x + radius_px)//TILE))
        min_ty = max(0, int((pos.y - radius_px)//TILE))
        max_ty = min(MAP_H-1, int((pos.y + radius_px)//TILE))
        for tx in range(min_tx, max_tx+1):
            for ty in range(min_ty, max_ty+1):
                cx = tx*TILE + TILE/2
                cy = ty*TILE + TILE/2
                if (cx - pos.x)**2 + (cy - pos.y)**2 <= r2:
                    self.seen[tx][ty] = True

# ---------- Game ----------
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("ARPG — Enhanced Build (Spells, Traps & More)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(FONT_NAME, 18)
        self.bigfont = pygame.font.SysFont(FONT_NAME, 28, bold=True)
        self.smallfont = pygame.font.SysFont(FONT_NAME, 14)
        # Difficulty select
        self.difficulty_name = self._difficulty_select()
        self.diff = DIFFICULTY[self.difficulty_name]
        global MAX_ACTIVE_ENEMIES
        MAX_ACTIVE_ENEMIES = self.diff["max_enemies"]
        self.current_level = 1
        self.dungeon = Dungeon(level=self.current_level)
        rx, ry = self.dungeon.center(self.dungeon.rooms[0]) if self.dungeon.rooms else (MAP_W//2, MAP_H//2)
        self.player = Player(pos=Vec(rx*TILE+TILE/2, ry*TILE+TILE/2), vel=Vec(0,0), radius=14)
        self.enemies: List[Enemy] = []
        self.projectiles: List[Projectile] = []
        self.loots: List[Loot] = []
        self.particles: List[Particle] = []
        self.floating_texts: List[FloatingText] = []
        self.spawn_timer = SPAWN_INTERVAL
        self.wave = 1
        self.running = True
        self.paused = False
        # Camera
        self.cam_x = 0
        self.cam_y = 0
        self.dungeon.mark_seen_radius(self.player.pos)
        # Boss flag
        self.boss_spawned = False
        self.boss_defeated = False
        # Screen shake
        self.shake_timer = 0.0
        self.shake_intensity = 0
        # Kill count
        self.kill_count = 0

    # ----- Difficulty menu -----
    def _difficulty_select(self) -> str:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        font = pygame.font.SysFont(FONT_NAME, 28, bold=True)
        small = pygame.font.SysFont(FONT_NAME, 18)
        options = ["Easy", "Normal", "Hard"]
        idx = 1
        selecting = True
        while selecting:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit(0)
                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_LEFT, pygame.K_a): idx = (idx-1) % 3
                    if e.key in (pygame.K_RIGHT, pygame.K_d): idx = (idx+1) % 3
                    if e.key in (pygame.K_RETURN, pygame.K_SPACE): selecting = False
            screen.fill((10,10,12))
            title = font.render("Select Difficulty", True, (230,230,240))
            screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 80))
            x = WIDTH//2
            for i,name in enumerate(options):
                col = (250,210,120) if i==idx else (170,170,180)
                txt = font.render(name, True, col)
                screen.blit(txt, (x - 220 + i*220 - txt.get_width()//2, HEIGHT//2 - 20))
            hint = small.render("←/→ to choose • Enter to start", True, (190,190,200))
            screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT//2 + 40))
            pygame.display.flip()
            pygame.time.delay(16)
        return options[idx]

    # ----- Particles & Effects -----
    def spawn_particles(self, pos: Vec, color, count=6, speed=120, life=0.5, size=3.0):
        for _ in range(count):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(speed*0.3, speed)
            vel = Vec(math.cos(ang)*spd, math.sin(ang)*spd)
            p = Particle(pos=pos.copy(), vel=vel, color=color, life=life, max_life=life, size=size)
            self.particles.append(p)

    def spawn_float_text(self, pos: Vec, text: str, color=(255,255,255), life=0.8):
        ft = FloatingText(pos=pos.copy(), text=text, color=color, life=life, max_life=life)
        self.floating_texts.append(ft)

    def trigger_shake(self, intensity=6, duration=0.15):
        self.shake_intensity = max(self.shake_intensity, intensity)
        self.shake_timer = max(self.shake_timer, duration)

    def update_particles(self, dt: float):
        for p in self.particles:
            p.life -= dt
            p.pos += p.vel * dt
            p.vel *= 0.96
        self.particles = [p for p in self.particles if p.life > 0]
        for ft in self.floating_texts:
            ft.life -= dt
            ft.pos.y -= 40 * dt
        self.floating_texts = [ft for ft in self.floating_texts if ft.life > 0]

    # ----- Spawning -----
    def _random_floor_pos(self, near_player=True, max_tries=200):
        tries = 0
        while tries < max_tries:
            if near_player:
                base_tx = int(self.player.pos.x//TILE)
                base_ty = int(self.player.pos.y//TILE)
                tx = random.randint(max(1, base_tx-12), min(MAP_W-2, base_tx+12))
                ty = random.randint(max(1, base_ty-8),  min(MAP_H-2, base_ty+8))
            else:
                tx = random.randint(1, MAP_W-2)
                ty = random.randint(1, MAP_H-2)
            if self.dungeon.tiles[tx][ty] == FLOOR:
                pos = Vec(tx*TILE + TILE/2, ty*TILE + TILE/2)
                if (pos - self.player.pos).length() > 200:
                    return pos
            tries += 1
        return self.player.pos + Vec(random.randint(-240,240), random.randint(-240,240))

    def spawn_enemy(self, near_player: bool = True, kind_override: Optional[int]=None):
        if len(self.enemies) >= MAX_ACTIVE_ENEMIES:
            return
        pos = self._random_floor_pos(near_player)
        scale = (WAVE_SCALE ** (self.wave-1)) * (1.0 + 0.1*(self.current_level-1))
        hp = int(ENEMY_BASE_HP * scale * self.diff["enemy_hp"])
        dmg_min = int(ENEMY_BASE_DMG[0] * scale * self.diff["enemy_dmg"])
        dmg_max = int(ENEMY_BASE_DMG[1] * scale * self.diff["enemy_dmg"])
        speed = ENEMY_SPEED * (0.95 + 0.1*random.random()) * self.diff["enemy_speed"]
        kind = kind_override if kind_override is not None else random.choices([0,1,2,3],[0.35,0.25,0.25,0.15])[0]
        e = Enemy(pos=pos, vel=Vec(0,0), radius=14, hp=hp, max_hp=hp, dmg_min=dmg_min, dmg_max=dmg_max, speed=speed, kind=kind)
        if kind == 3:
            e.shot_cd = random.uniform(1.4, 2.2)
        self.enemies.append(e)

    def spawn_elite_pack(self):
        if len(self.enemies) >= MAX_ACTIVE_ENEMIES:
            return
        pos = self._random_floor_pos(near_player=True)
        scale = (WAVE_SCALE ** (self.wave-1)) * (1.0 + 0.1*(self.current_level-1))
        hp = int(ENEMY_BASE_HP * ELITE_MULT["hp"] * scale * self.diff["enemy_hp"])
        dmg_min = int(ENEMY_BASE_DMG[0] * ELITE_MULT["dmg"] * scale * self.diff["enemy_dmg"])
        dmg_max = int(ENEMY_BASE_DMG[1] * ELITE_MULT["dmg"] * scale * self.diff["enemy_dmg"])
        spd = ENEMY_SPEED * ELITE_MULT["spd"] * self.diff["enemy_speed"]
        aura_name = random.choice(list(AURAS.keys()))
        elite = Elite(pos=pos, vel=Vec(0,0), radius=ELITE_MULT["radius"], hp=hp, max_hp=hp,
                      dmg_min=dmg_min, dmg_max=dmg_max, speed=spd, kind=1, aura=aura_name)
        self.enemies.append(elite)
        count = random.randint(*PACK_SIZE_RANGE)
        ang0 = random.random()*math.tau
        for i in range(count):
            r = random.randint(46, 88)
            ang = ang0 + i*(math.tau/count)
            mpos = pos + Vec(math.cos(ang)*r, math.sin(ang)*r)
            kind = random.choices([0,1,2,3],[0.4,0.25,0.2,0.15])[0]
            self.spawn_enemy(near_player=False, kind_override=kind)
            if self.enemies:
                self.enemies[-1].pos = mpos

    def spawn_boss(self):
        if self.current_level != 3 or self.boss_spawned:
            return
        center_tx, center_ty = self.dungeon.center(self.dungeon.rooms[-1])
        pos = Vec(center_tx*TILE + TILE/2, center_ty*TILE + TILE/2)
        hp = int(BOSS_HP * self.diff["enemy_hp"])
        dmg_min = int(BOSS_DMG[0] * self.diff["enemy_dmg"])
        dmg_max = int(BOSS_DMG[1] * self.diff["enemy_dmg"])
        b = Boss(pos=pos, vel=Vec(0,0), radius=24, hp=hp, max_hp=hp, dmg_min=dmg_min, dmg_max=dmg_max, speed=ENEMY_SPEED*0.9*self.diff["enemy_speed"], kind=1, shot_cd=random.uniform(*BOSS_SHOT_CD))
        self.enemies.append(b)
        self.boss_spawned = True

    def spawn_pickup_near_player(self):
        base_tx = int(self.player.pos.x//TILE)
        base_ty = int(self.player.pos.y//TILE)
        for _ in range(50):
            tx = random.randint(max(1, base_tx-10), min(MAP_W-2, base_tx+10))
            ty = random.randint(max(1, base_ty-8),  min(MAP_H-2, base_ty+8))
            if self.dungeon.tiles[tx][ty] == FLOOR:
                pos = Vec(tx*TILE + TILE/2, ty*TILE + TILE/2)
                if (pos - self.player.pos).length() > 140:
                    if random.random() < 0.5:
                        self.loots.append(Loot(pos=pos, dmg_boost=True))
                    else:
                        self.loots.append(Loot(pos=pos, shield_boost=True))
                    return

    # ----- Input -----
    def handle_input(self, dt: float):
        keys = pygame.key.get_pressed()
        move = Vec(0,0)
        if keys[pygame.K_w]: move.y -= 1
        if keys[pygame.K_s]: move.y += 1
        if keys[pygame.K_a]: move.x -= 1
        if keys[pygame.K_d]: move.x += 1

        # slow effect on player
        player_slow = 1.0
        for eff in self.player.effects:
            if eff.kind == "slow":
                player_slow = min(player_slow, eff.value)

        if move.length_squared() > 0:
            move = move.normalize()
        self.player.vel = move * PLAYER_SPEED * player_slow

        # dash (Left Shift)
        if keys[pygame.K_LSHIFT] and self.player.dash_cd <= 0 and self.player.dash_timer <= 0:
            self.player.dash_timer = DASH_TIME
            self.player.dash_cd = DASH_CD
            self.player.iframes = max(self.player.iframes, IFRAME_TIME)

        mx, my = pygame.mouse.get_pos()
        world_mouse = Vec(mx + self.cam_x, my + self.cam_y)
        aim_dir = world_mouse - self.player.pos
        if aim_dir.length_squared() == 0:
            aim_dir = Vec(1,0)
        aim_dir = aim_dir.normalize()

        buttons = pygame.mouse.get_pressed(3)
        if buttons[0] and self.player.basic_cd <= 0:
            self.shoot_basic(aim_dir)
        if buttons[2] and self.player.power_cd <= 0 and self.player.mana >= POWER_MANA_COST:
            self.shoot_power(aim_dir)

        if keys[pygame.K_q] and self.player.potions_hp > 0 and self.player.hp < self.player.max_hp:
            self.player.hp = min(self.player.max_hp, self.player.hp + POTION_HEAL)
            self.player.potions_hp -= 1
            self.spawn_float_text(self.player.pos + Vec(0, -20), f"+{POTION_HEAL} HP", (100,255,100))
            self.spawn_particles(self.player.pos, (100,255,100), count=8, speed=60)
        if keys[pygame.K_e] and self.player.potions_mana > 0 and self.player.mana < self.player.max_mana:
            self.player.mana = min(self.player.max_mana, self.player.mana + POTION_MANA)
            self.player.potions_mana -= 1
            self.spawn_float_text(self.player.pos + Vec(0, -20), f"+{POTION_MANA} Mana", (100,160,255))
            self.spawn_particles(self.player.pos, (100,160,255), count=8, speed=60)

        # Spells: 1=Fireball, 2=Frost Nova, 3=Heal Aura
        if keys[pygame.K_1] and self.player.spell_fireball and self.player.fireball_cd <= 0 and self.player.mana >= FIREBALL_MANA:
            self.cast_fireball(aim_dir)
        if keys[pygame.K_2] and self.player.spell_frost_nova and self.player.frost_nova_cd <= 0 and self.player.mana >= FROST_NOVA_MANA:
            self.cast_frost_nova()
        if keys[pygame.K_3] and self.player.spell_heal_aura and self.player.heal_aura_cd <= 0 and self.player.mana >= HEAL_AURA_MANA:
            self.cast_heal_aura()

    # ----- Spells -----
    def cast_fireball(self, dir: Vec):
        self.player.fireball_cd = FIREBALL_CD
        self.player.mana -= FIREBALL_MANA
        dmg = random.randint(*FIREBALL_DMG)
        dmg = int(dmg * self.player.dmg_mult)
        proj = Projectile(pos=self.player.pos + dir*22, vel=dir*FIREBALL_PROJ_SPEED, dmg=dmg,
                          ttl=1.5, radius=8, pierce=99, hostile=False, is_fireball=True)
        self.projectiles.append(proj)
        self.spawn_particles(self.player.pos + dir*22, (255,140,40), count=4, speed=80)

    def cast_frost_nova(self):
        self.player.frost_nova_cd = FROST_NOVA_CD
        self.player.mana -= FROST_NOVA_MANA
        # damage and slow all enemies in radius
        for e in self.enemies:
            if not e.alive:
                continue
            dist = (e.pos - self.player.pos).length()
            if dist <= FROST_NOVA_RADIUS:
                dmg = random.randint(*FROST_NOVA_DMG)
                dmg = max(1, int(dmg * e.mult_taken))
                e.hp -= dmg
                self.spawn_float_text(e.pos + Vec(0, -10), str(dmg), (120,200,255))
                # apply slow
                e.effects.append(StatusEffect(kind="slow", duration=FROST_NOVA_SLOW_DUR, value=FROST_NOVA_SLOW_MULT))
                self.spawn_particles(e.pos, (120,200,255), count=4, speed=60)
        # visual burst
        self.spawn_particles(self.player.pos, (150,220,255), count=16, speed=200, life=0.6, size=4)
        self.spawn_float_text(self.player.pos + Vec(0, -30), "Frost Nova!", (150,220,255))

    def cast_heal_aura(self):
        self.player.heal_aura_cd = HEAL_AURA_CD
        self.player.mana -= HEAL_AURA_MANA
        heal = HEAL_AURA_AMOUNT
        self.player.hp = min(self.player.max_hp, self.player.hp + heal)
        self.player.hot_timer = HEAL_AURA_HOT_DUR
        self.player.hot_tick_timer = 0.0
        self.spawn_float_text(self.player.pos + Vec(0, -30), f"+{heal} Heal!", (100,255,180))
        self.spawn_particles(self.player.pos, (100,255,180), count=12, speed=100, life=0.7, size=4)

    def fireball_explode(self, pos: Vec, dmg: int):
        self.trigger_shake(8, 0.2)
        self.spawn_particles(pos, (255,160,40), count=20, speed=180, life=0.6, size=5)
        self.spawn_particles(pos, (255,80,20), count=10, speed=100, life=0.4, size=3)
        for e in self.enemies:
            if not e.alive:
                continue
            dist = (e.pos - pos).length()
            if dist <= FIREBALL_RADIUS:
                falloff = 1.0 - (dist / FIREBALL_RADIUS) * 0.5
                actual = max(1, int(dmg * falloff * e.mult_taken))
                e.hp -= actual
                e.vel += (e.pos - pos).normalize() * 400
                self.spawn_float_text(e.pos + Vec(0,-10), str(actual), (255,180,60))
                # burn DOT
                e.effects.append(StatusEffect(kind="poison", duration=3.0, value=4))

    # ----- Combat (shooting) -----
    def shoot_basic(self, dir: Vec):
        self.player.basic_cd = BASIC_CD
        base = random.randint(*BASIC_DMG)
        dmg = int(base * self.player.dmg_mult)
        proj = Projectile(pos=self.player.pos + dir*20, vel=dir*PROJECTILE_SPEED, dmg=dmg, ttl=0.9, radius=BASIC_RADIUS, pierce=BASIC_PIERCE)
        self.projectiles.append(proj)

    def shoot_power(self, dir: Vec):
        self.player.power_cd = POWER_CD
        self.player.mana -= POWER_MANA_COST
        base = random.randint(*POWER_DMG)
        dmg = int(base * self.player.dmg_mult)
        proj = Projectile(pos=self.player.pos + dir*22, vel=dir*PROJECTILE_SPEED*0.95, dmg=dmg, ttl=1.1, radius=POWER_RADIUS, pierce=POWER_PIERCE)
        self.projectiles.append(proj)

    # ----- Updates -----
    def update_player(self, dt: float):
        p = self.player
        p.basic_cd = max(0.0, p.basic_cd - dt)
        p.power_cd = max(0.0, p.power_cd - dt)
        p.dash_cd = max(0.0, p.dash_cd - dt)
        p.iframes = max(0.0, p.iframes - dt)
        p.fireball_cd = max(0.0, p.fireball_cd - dt)
        p.frost_nova_cd = max(0.0, p.frost_nova_cd - dt)
        p.heal_aura_cd = max(0.0, p.heal_aura_cd - dt)
        if p.dmg_timer > 0:
            p.dmg_timer -= dt
            if p.dmg_timer <= 0:
                p.dmg_mult = 1.0

        # mana regen
        p.mana = min(p.max_mana, p.mana + p.mana_regen * dt)

        # heal over time
        if p.hot_timer > 0:
            p.hot_timer -= dt
            p.hot_tick_timer -= dt
            if p.hot_tick_timer <= 0:
                p.hp = min(p.max_hp, p.hp + HEAL_AURA_HOT_TICK)
                p.hot_tick_timer = 0.5
                self.spawn_particles(p.pos, (100,255,180), count=3, speed=40)

        # status effects on player
        for eff in p.effects:
            eff.duration -= dt
            if eff.kind == "poison":
                eff.tick_timer -= dt
                if eff.tick_timer <= 0:
                    eff.tick_timer = 1.0
                    dmg = int(eff.value)
                    p.hp -= dmg
                    self.spawn_float_text(p.pos + Vec(0,-15), str(dmg), (120,200,60))
        p.effects = [e for e in p.effects if e.duration > 0]

        # dash movement override
        vel = p.vel
        if p.dash_timer > 0:
            p.dash_timer -= dt
            if vel.length_squared()>0:
                vel = vel.normalize() * DASH_SPEED
            else:
                vel = Vec(1,0) * DASH_SPEED
        new_pos = p.pos + vel * dt
        # X
        test = Vec(new_pos.x, p.pos.y)
        if not self.dungeon.is_solid_at_px(test) and not self._circle_collides(test, p.radius):
            p.pos.x = test.x
        # Y
        test = Vec(p.pos.x, new_pos.y)
        if not self.dungeon.is_solid_at_px(test) and not self._circle_collides(test, p.radius):
            p.pos.y = test.y
        # Clamp to world
        p.pos.x = max(p.radius, min(MAP_W*TILE - p.radius, p.pos.x))
        p.pos.y = max(p.radius, min(MAP_H*TILE - p.radius, p.pos.y))
        # Reveal fog
        self.dungeon.mark_seen_radius(p.pos)
        # Camera
        self.cam_x = int(p.pos.x - WIDTH/2)
        self.cam_y = int(p.pos.y - HEIGHT/2)
        self.cam_x = max(0, min(self.cam_x, MAP_W*TILE - WIDTH))
        self.cam_y = max(0, min(self.cam_y, MAP_H*TILE - HEIGHT))
        # Stairs check
        if self.dungeon.stairs_tx is not None:
            sx = self.dungeon.stairs_tx*TILE + TILE/2
            sy = self.dungeon.stairs_ty*TILE + TILE/2
            if (Vec(sx, sy) - p.pos).length() < 18:
                self.next_level()

    def _circle_collides(self, pos: Vec, radius: int) -> bool:
        for ang in (0, math.pi*0.5, math.pi, math.pi*1.5):
            pt = Vec(pos.x + math.cos(ang)*radius, pos.y + math.sin(ang)*radius)
            if self.dungeon.is_solid_at_px(pt):
                return True
        return False

    def update_status_effects(self, entity, dt: float):
        for eff in entity.effects:
            eff.duration -= dt
            if eff.kind == "poison":
                eff.tick_timer -= dt
                if eff.tick_timer <= 0:
                    eff.tick_timer = 1.0
                    dmg = int(eff.value)
                    entity.hp -= dmg
                    self.spawn_float_text(entity.pos + Vec(0,-10), str(dmg), (120,200,60))
                    self.spawn_particles(entity.pos, (120,200,60), count=2, speed=30)
        entity.effects = [e for e in entity.effects if e.duration > 0]

    def update_enemies(self, dt: float):
        p = self.player

        # reset aura multipliers each frame
        for e in self.enemies:
            e.mult_speed = 1.0
            e.mult_damage = 1.0
            e.mult_taken = 1.0

        # apply auras from elites
        for e in self.enemies:
            if isinstance(e, Elite) and e.alive:
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

            # status effects (poison/slow)
            self.update_status_effects(e, dt)

            slow_mult = e.get_slow_mult()

            desired = (p.pos - e.pos)
            dist = desired.length() or 0.0001
            desired = desired / dist
            jitter = Vec(random.uniform(-0.2,0.2), random.uniform(-0.2,0.2))
            acc = (desired + jitter).normalize() * (e.speed * e.mult_speed * slow_mult)
            e.vel += (acc - e.vel) * 0.1
            e.pos += e.vel * dt
            if self._circle_collides(e.pos, e.radius):
                e.vel *= -0.4
                e.pos += e.vel * dt

            # spitter minion ranged attack
            if e.kind == 3 and e.alive:
                e.shot_cd -= dt
                if e.shot_cd <= 0:
                    dirv = (p.pos - e.pos)
                    if dirv.length_squared()>0:
                        dirv = dirv.normalize()
                        pr = Projectile(pos=e.pos + dirv*14, vel=dirv*320, dmg=e.roll_damage(), ttl=1.6, radius=4, pierce=1, hostile=True)
                        self.projectiles.append(pr)
                    e.shot_cd = random.uniform(1.2, 2.0)

            # Boss shooting
            if isinstance(e, Boss):
                e.shot_cd -= dt
                if e.shot_cd <= 0:
                    dirv = (p.pos - e.pos)
                    if dirv.length_squared()>0:
                        dirv = dirv.normalize()
                        pr = Projectile(pos=e.pos + dirv*18, vel=dirv*BOSS_PROJ_SPEED, dmg=e.roll_damage(), ttl=2.0, radius=5, pierce=1, hostile=True)
                        self.projectiles.append(pr)
                    e.shot_cd = random.uniform(*BOSS_SHOT_CD)
            # Touch damage
            if (e.pos - p.pos).length() < e.radius + p.radius and p.iframes<=0:
                if random.random() < 0.02:
                    dmg = e.roll_damage()
                    if p.shield > 0:
                        absorb = min(p.shield, dmg)
                        p.shield -= absorb
                        dmg -= absorb
                    if dmg > 0:
                        p.hp -= dmg
                        self.spawn_float_text(p.pos + Vec(0,-20), str(dmg), (255,80,80))
                        self.spawn_particles(p.pos, (255,80,80), count=4, speed=80)
                        if dmg >= 10:
                            self.trigger_shake(4, 0.1)
                    kb = (p.pos - e.pos).normalize() * 150
                    p.pos += kb * dt
            e.knockback = max(0.0, e.knockback - 200*dt)
            e.vel *= 0.98
            if e.hp <= 0 and e.alive:
                e.alive = False
                self.on_enemy_dead(e)
        # Cull bodies sometimes
        self.enemies = [e for e in self.enemies if e.alive or random.random() > 0.01]

    def update_projectiles(self, dt: float):
        for pr in self.projectiles:
            pr.ttl -= dt
            pr.pos += pr.vel * dt
            if self.dungeon.is_solid_at_px(pr.pos):
                if pr.is_fireball:
                    self.fireball_explode(pr.pos, pr.dmg)
                pr.ttl = 0
                continue
            if pr.hostile:
                # hit player
                if (self.player.pos - pr.pos).length() < self.player.radius + pr.radius and self.player.iframes<=0:
                    dmg = pr.dmg
                    if self.player.shield>0:
                        absorb = min(self.player.shield, dmg)
                        self.player.shield -= absorb
                        dmg -= absorb
                    if dmg>0:
                        self.player.hp -= dmg
                        self.player.iframes = max(self.player.iframes, 0.12)
                        self.spawn_float_text(self.player.pos + Vec(0,-20), str(dmg), (255,80,80))
                        self.spawn_particles(self.player.pos, (255,80,80), count=4, speed=80)
                        if dmg >= 8:
                            self.trigger_shake(3, 0.08)
                    pr.ttl = 0
                    continue
            else:
                # hit enemies
                for e in self.enemies:
                    if not e.alive: continue
                    if (e.pos - pr.pos).length() < e.radius + pr.radius:
                        if pr.is_fireball:
                            self.fireball_explode(pr.pos, pr.dmg)
                            pr.ttl = 0
                            break
                        # apply "taken" multiplier (guardian aura reduces damage)
                        damage = max(1, int(pr.dmg * e.mult_taken))
                        e.hp -= damage
                        e.knockback = 200
                        e.vel += (e.pos - pr.pos).normalize() * 300
                        # floating damage text
                        self.spawn_float_text(e.pos + Vec(random.randint(-8,8), -10), str(damage), (255,220,140))
                        self.spawn_particles(e.pos, (200,180,140), count=3, speed=60)
                        pr.pierce -= 1
                        if pr.pierce <= 0:
                            pr.ttl = 0
                            break
        self.projectiles = [pr for pr in self.projectiles if pr.ttl > 0]

    def update_traps(self, dt: float):
        p = self.player
        for trap in self.dungeon.traps:
            if not trap.armed:
                trap.cooldown -= dt
                if trap.cooldown <= 0:
                    trap.armed = True
                continue
            # check player proximity
            trap_px = trap.tx * TILE + TILE/2
            trap_py = trap.ty * TILE + TILE/2
            dist = (Vec(trap_px, trap_py) - p.pos).length()
            if dist < 20 and p.iframes <= 0:
                trap.armed = False
                trap.cooldown = SPIKE_TRAP_CD
                if trap.kind == "spike":
                    dmg = random.randint(*SPIKE_TRAP_DMG)
                    if p.shield > 0:
                        absorb = min(p.shield, dmg)
                        p.shield -= absorb
                        dmg -= absorb
                    if dmg > 0:
                        p.hp -= dmg
                    self.spawn_float_text(p.pos + Vec(0, -20), f"Trap! -{dmg}", (255,100,100))
                    self.spawn_particles(Vec(trap_px, trap_py), (200,200,200), count=8, speed=100)
                    self.trigger_shake(5, 0.12)
                elif trap.kind == "poison":
                    p.effects.append(StatusEffect(kind="poison", duration=POISON_TRAP_DUR, value=POISON_TRAP_DPS))
                    self.spawn_float_text(p.pos + Vec(0, -20), "Poisoned!", (120,200,60))
                    self.spawn_particles(Vec(trap_px, trap_py), (120,200,60), count=10, speed=80)

            # check enemy proximity too
            for e in self.enemies:
                if not e.alive:
                    continue
                edist = (Vec(trap_px, trap_py) - e.pos).length()
                if edist < 18 and trap.armed:
                    trap.armed = False
                    trap.cooldown = SPIKE_TRAP_CD
                    if trap.kind == "spike":
                        dmg = random.randint(*SPIKE_TRAP_DMG)
                        e.hp -= dmg
                        self.spawn_float_text(e.pos + Vec(0, -10), str(dmg), (200,200,200))
                    elif trap.kind == "poison":
                        e.effects.append(StatusEffect(kind="poison", duration=POISON_TRAP_DUR, value=POISON_TRAP_DPS))
                    break

    def update_loot(self, dt: float):
        for l in self.loots:
            l.ttl -= dt
            if (l.pos - self.player.pos).length() < 24:
                if l.gold:
                    self.player.gold += l.gold
                    self.spawn_float_text(l.pos + Vec(0,-10), f"+{l.gold}g", (255,215,0))
                if l.potion_hp:
                    self.player.potions_hp += 1
                    self.spawn_float_text(l.pos + Vec(0,-10), "+HP Pot", (220,60,60))
                if l.potion_mana:
                    self.player.potions_mana += 1
                    self.spawn_float_text(l.pos + Vec(0,-10), "+Mana Pot", (60,120,220))
                if l.weapon:
                    old_tier = self.player.weapon.tier
                    self.player.weapon = l.weapon
                    color = (255,225,120) if l.weapon.tier > old_tier else (200,200,200)
                    self.spawn_float_text(l.pos + Vec(0,-10), l.weapon.name, color)
                    self.spawn_particles(l.pos, color, count=10, speed=100)
                if l.dmg_boost:
                    self.player.dmg_mult = DMG_BOOST_MULT
                    self.player.dmg_timer = DMG_BOOST_TIME
                    self.spawn_float_text(l.pos + Vec(0,-10), "DMG UP!", (250,160,40))
                    self.spawn_particles(l.pos, (250,160,40), count=8, speed=80)
                if l.shield_boost:
                    self.player.shield = max(self.player.shield, SHIELD_POINTS)
                    self.spawn_float_text(l.pos + Vec(0,-10), "SHIELD!", (80,200,250))
                    self.spawn_particles(l.pos, (80,200,250), count=8, speed=80)
                l.ttl = 0
        self.loots = [l for l in self.loots if l.ttl > 0]

    def _roll_weapon_drop(self, dungeon_level: int) -> Weapon:
        # filter tiers based on dungeon level
        max_tier = dungeon_level + 1
        candidates = [w for w in WEAPON_TIERS if w["tier"] <= max_tier and w["tier"] >= max(0, dungeon_level - 1)]
        if not candidates:
            candidates = [WEAPON_TIERS[1]]
        chosen = random.choice(candidates)
        # slight random variance
        dmg_min = chosen["dmg"][0] + random.randint(-1, 2)
        dmg_max = chosen["dmg"][1] + random.randint(-1, 3)
        return Weapon(chosen["name"], max(1, dmg_min), max(dmg_min+1, dmg_max),
                      chosen["speed"], chosen["ranged"], chosen["tier"])

    def on_enemy_dead(self, e: Enemy):
        self.kill_count += 1
        self.player.xp += 6 + self.wave
        # death particles
        self.spawn_particles(e.pos, (180,60,60), count=10, speed=120, life=0.5)
        if isinstance(e, Boss):
            self.spawn_particles(e.pos, (255,200,60), count=30, speed=200, life=1.0, size=6)
            self.trigger_shake(12, 0.4)
            self.boss_defeated = True
        elif isinstance(e, Elite):
            self.spawn_particles(e.pos, (255,200,100), count=15, speed=150, life=0.7, size=4)
            self.trigger_shake(6, 0.2)

        while self.player.xp >= self.player.xp_to_next:
            self.player.xp -= self.player.xp_to_next
            self.player.level += 1
            self.player.xp_to_next = int(self.player.xp_to_next * 1.35)
            self.player.max_hp = PLAYER_HP + 10 * self.player.level
            self.player.max_mana = PLAYER_MANA + 8 * self.player.level
            self.player.hp = min(self.player.max_hp, self.player.hp + 30)
            self.player.mana = min(self.player.max_mana, self.player.mana + 20)
            self.spawn_float_text(self.player.pos + Vec(0, -35), f"LEVEL UP! ({self.player.level})", (255,255,100), life=1.5)
            self.spawn_particles(self.player.pos, (255,255,100), count=16, speed=140, life=0.8, size=4)
            # unlock spells on level up
            if self.player.level == 2 and not self.player.spell_fireball:
                self.player.spell_fireball = True
                self.spawn_float_text(self.player.pos + Vec(0, -50), "Fireball Unlocked! (1)", (255,140,40), life=2.0)
            elif self.player.level == 3 and not self.player.spell_frost_nova:
                self.player.spell_frost_nova = True
                self.spawn_float_text(self.player.pos + Vec(0, -50), "Frost Nova Unlocked! (2)", (150,220,255), life=2.0)
            elif self.player.level == 5 and not self.player.spell_heal_aura:
                self.player.spell_heal_aura = True
                self.spawn_float_text(self.player.pos + Vec(0, -50), "Heal Aura Unlocked! (3)", (100,255,180), life=2.0)

        drops: List[Loot] = []
        if random.random() < 0.9:
            drops.append(Loot(pos=e.pos.copy(), gold=random.randint(*GOLD_DROP)))
        if random.random() < POTION_DROP_CHANCE:
            potion = random.choice(["hp","mana"])
            drops.append(Loot(pos=e.pos.copy(), potion_hp=(potion=="hp"), potion_mana=(potion=="mana")))
        if random.random() < LOOT_DROP_CHANCE:
            weapon = self._roll_weapon_drop(self.current_level)
            drops.append(Loot(pos=e.pos.copy(), weapon=weapon))
        if random.random() < DMG_PICKUP_DROP_CHANCE:
            drops.append(Loot(pos=e.pos.copy(), dmg_boost=True))
        if random.random() < SHIELD_PICKUP_DROP_CHANCE:
            drops.append(Loot(pos=e.pos.copy(), shield_boost=True))

        # elites drop extra goodies
        if isinstance(e, Elite):
            drops.append(Loot(pos=e.pos.copy(), gold=random.randint(15, 35)))
            if random.random() < 0.5:
                drops.append(Loot(pos=e.pos.copy(), dmg_boost=True))
            else:
                drops.append(Loot(pos=e.pos.copy(), shield_boost=True))
            # elite guaranteed weapon drop
            if random.random() < 0.35:
                weapon = self._roll_weapon_drop(self.current_level)
                drops.append(Loot(pos=e.pos.copy(), weapon=weapon))

        # boss drops top-tier weapon
        if isinstance(e, Boss):
            top_weapons = [w for w in WEAPON_TIERS if w["tier"] >= 3]
            chosen = random.choice(top_weapons)
            weapon = Weapon(chosen["name"], chosen["dmg"][0]+3, chosen["dmg"][1]+5,
                          chosen["speed"], chosen["ranged"], chosen["tier"])
            drops.append(Loot(pos=e.pos.copy(), weapon=weapon))
            drops.append(Loot(pos=e.pos.copy() + Vec(10,0), gold=random.randint(40, 80)))
            drops.append(Loot(pos=e.pos.copy() + Vec(-10,0), dmg_boost=True))
            drops.append(Loot(pos=e.pos.copy() + Vec(0,10), shield_boost=True))

        self.loots.extend(drops)

    # ----- Waves / Exploration spawning -----
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
            self.wave += 1
            self.spawn_timer = SPAWN_INTERVAL
            self.spawn_boss()

    # ----- Level management -----
    def next_level(self):
        if self.current_level >= LEVELS:
            self.current_level = 1
        else:
            self.current_level += 1
        self.dungeon = Dungeon(level=self.current_level)
        rx, ry = self.dungeon.center(self.dungeon.rooms[0]) if self.dungeon.rooms else (MAP_W//2, MAP_H//2)
        self.player.pos = Vec(rx*TILE+TILE/2, ry*TILE+TILE/2)
        self.enemies.clear()
        self.projectiles.clear()
        self.loots.clear()
        self.particles.clear()
        self.floating_texts.clear()
        self.wave = 1
        self.spawn_timer = SPAWN_INTERVAL
        self.dungeon.mark_seen_radius(self.player.pos)
        self.boss_spawned = False
        self.spawn_float_text(self.player.pos + Vec(0, -30), f"Dungeon Level {self.current_level}", (230,230,240), life=2.0)

    # ----- Render -----
    def draw(self):
        s = self.screen
        s.fill((8, 8, 10))

        # screen shake offset
        shake_ox, shake_oy = 0, 0
        if self.shake_timer > 0:
            shake_ox = random.randint(-self.shake_intensity, self.shake_intensity)
            shake_oy = random.randint(-self.shake_intensity, self.shake_intensity)

        # tiles in view
        start_tx = max(0, self.cam_x // TILE)
        end_tx = min(MAP_W-1, (self.cam_x + WIDTH) // TILE + 1)
        start_ty = max(0, self.cam_y // TILE)
        end_ty = min(MAP_H-1, (self.cam_y + HEIGHT) // TILE + 1)
        for tx in range(start_tx, end_tx+1):
            for ty in range(start_ty, end_ty+1):
                px = tx*TILE - self.cam_x + shake_ox
                py = ty*TILE - self.cam_y + shake_oy
                seen = self.dungeon.seen[tx][ty]
                if self.dungeon.tiles[tx][ty] == WALL:
                    col = (46,46,58) if seen else (18,18,22)
                else:
                    col = (24,24,28) if seen else (12,12,14)
                pygame.draw.rect(s, col, (px, py, TILE, TILE))
        # traps
        for trap in self.dungeon.traps:
            if not self._tile_in_view(trap.tx, trap.ty):
                continue
            if not self.dungeon.seen[trap.tx][trap.ty]:
                continue
            tpx = trap.tx*TILE - self.cam_x + shake_ox
            tpy = trap.ty*TILE - self.cam_y + shake_oy
            if trap.kind == "spike":
                col = (160,80,80) if trap.armed else (80,40,40)
                pygame.draw.rect(s, col, (tpx+8, tpy+8, TILE-16, TILE-16))
                if trap.armed:
                    # spikes
                    for ox in (12, 17, 22):
                        pygame.draw.polygon(s, (200,120,120), [(tpx+ox, tpy+10), (tpx+ox-3, tpy+20), (tpx+ox+3, tpy+20)])
            elif trap.kind == "poison":
                col = (80,160,60) if trap.armed else (40,80,30)
                pygame.draw.rect(s, col, (tpx+8, tpy+8, TILE-16, TILE-16))
                if trap.armed:
                    pygame.draw.circle(s, (120,200,80), (tpx+TILE//2, tpy+TILE//2), 6)
        # scenery
        for (tx,ty,t) in self.dungeon.scenery:
            if not self._tile_in_view(tx,ty):
                continue
            px = tx*TILE - self.cam_x + shake_ox
            py = ty*TILE - self.cam_y + shake_oy
            if t=='pillar':
                pygame.draw.rect(s, (70,70,90), (px+6,py+6,TILE-12,TILE-12), border_radius=6)
            else:
                pygame.draw.rect(s, (90,72,48), (px+4,py+4,TILE-8,TILE-8))
                pygame.draw.line(s, (120,96,64), (px+4,py+4), (px+TILE-4,py+TILE-4), 2)
                pygame.draw.line(s, (120,96,64), (px+TILE-4,py+4), (px+4,py+TILE-4), 2)
        # stairs
        if self.dungeon.stairs_tx is not None and self._tile_in_view(self.dungeon.stairs_tx,self.dungeon.stairs_ty):
            px = self.dungeon.stairs_tx*TILE - self.cam_x + shake_ox
            py = self.dungeon.stairs_ty*TILE - self.cam_y + shake_oy
            pygame.draw.rect(s, (200, 200, 90), (px+8, py+8, TILE-16, TILE-16), border_radius=4)
            pygame.draw.rect(s, (120, 120, 40), (px+10, py+10, TILE-20, TILE-20), border_radius=4)
        # particles (behind entities)
        for p in self.particles:
            alpha = max(0.0, p.life / p.max_life)
            col = (int(p.color[0]*alpha), int(p.color[1]*alpha), int(p.color[2]*alpha))
            sz = max(1, int(p.size * alpha))
            pygame.draw.circle(s, col, (int(p.pos.x - self.cam_x + shake_ox), int(p.pos.y - self.cam_y + shake_oy)), sz)
        # projectiles
        for pr in self.projectiles:
            prx = int(pr.pos.x - self.cam_x + shake_ox)
            pry = int(pr.pos.y - self.cam_y + shake_oy)
            if pr.is_fireball:
                pygame.draw.circle(s, (255,160,40), (prx, pry), pr.radius)
                pygame.draw.circle(s, (255,220,100), (prx, pry), pr.radius-3)
            elif pr.hostile:
                pygame.draw.circle(s, (255,100,110), (prx, pry), pr.radius)
            else:
                pygame.draw.circle(s, (180,220,255), (prx, pry), pr.radius)
        # player sprite
        self._draw_player(shake_ox, shake_oy)
        # enemies
        for e in self.enemies:
            self._draw_enemy(e, shake_ox, shake_oy)
        # loot
        for l in self.loots:
            vx = int(l.pos.x - self.cam_x + shake_ox)
            vy = int(l.pos.y - self.cam_y + shake_oy)
            if l.weapon:
                tier_col = [(200,200,200),(180,220,255),(120,255,120),(255,200,80),(255,120,255)][min(l.weapon.tier, 4)]
                pygame.draw.rect(s, tier_col, (vx-6, vy-6, 12, 12))
                pygame.draw.rect(s, (40,40,40), (vx-6, vy-6, 12, 12), 1)
            elif l.potion_hp:
                pygame.draw.rect(s, (220, 60, 60), (vx-5, vy-5, 10, 10))
            elif l.potion_mana:
                pygame.draw.rect(s, (60, 120, 220), (vx-5, vy-5, 10, 10))
            elif l.dmg_boost:
                pygame.draw.circle(s, (250,160,40), (vx, vy), 7)
                pygame.draw.circle(s, (255,210,120), (vx, vy), 3)
            elif l.shield_boost:
                pygame.draw.circle(s, (80,200,250), (vx, vy), 7)
                pygame.draw.circle(s, (180,240,255), (vx, vy), 3)
            elif l.gold:
                pygame.draw.circle(s, (255, 215, 0), (vx, vy), 5)
        # floating text
        for ft in self.floating_texts:
            alpha = max(0.0, ft.life / ft.max_life)
            col = (int(ft.color[0]*alpha), int(ft.color[1]*alpha), int(ft.color[2]*alpha))
            txt = self.smallfont.render(ft.text, True, col)
            sx = int(ft.pos.x - self.cam_x + shake_ox) - txt.get_width()//2
            sy = int(ft.pos.y - self.cam_y + shake_oy) - txt.get_height()//2
            s.blit(txt, (sx, sy))
        self.draw_ui()
        # aim reticle
        mx, my = pygame.mouse.get_pos()
        pygame.draw.circle(s, (200,200,200), (mx, my), 6, 1)
        pygame.draw.line(s, (200,200,200), (mx-8,my), (mx-2,my), 1)
        pygame.draw.line(s, (200,200,200), (mx+2,my), (mx+8,my), 1)
        pygame.draw.line(s, (200,200,200), (mx,my-8), (mx,my-2), 1)
        pygame.draw.line(s, (200,200,200), (mx,my+2), (mx,my+8), 1)
        # minimap
        self._draw_minimap()
        pygame.display.flip()

    def _tile_in_view(self, tx:int, ty:int) -> bool:
        return (self.cam_x // TILE) - 2 <= tx <= ((self.cam_x + WIDTH) // TILE) + 2 and \
               (self.cam_y // TILE) - 2 <= ty <= ((self.cam_y + HEIGHT) // TILE) + 2

    def _draw_player(self, sox=0, soy=0):
        s = self.screen
        px = int(self.player.pos.x - self.cam_x + sox)
        py = int(self.player.pos.y - self.cam_y + soy)
        # body
        pygame.draw.circle(s, (220, 225, 235), (px, py-8), 6)  # head
        pygame.draw.rect(s, (70,100,160), (px-8, py-6, 16, 18), border_radius=4)  # torso
        # arm toward mouse
        mx, my = pygame.mouse.get_pos()
        ang = math.atan2(my - (py), mx - (px))
        hand = (px + int(math.cos(ang)*12), py + int(math.sin(ang)*12))
        pygame.draw.circle(s, (220,220,220), hand, 3)
        # tiny feet for motion cue
        pygame.draw.rect(s, (60,80,120), (px-8, py+10, 16, 4), border_radius=2)
        # shield aura
        if self.player.shield > 0:
            pygame.draw.circle(s, (80,200,250), (px, py), self.player.radius+6, 1)
        if self.player.dmg_timer > 0:
            pygame.draw.circle(s, (250,160,40), (px, py), self.player.radius+2, 1)
        # poison indicator
        has_poison = any(e.kind == "poison" for e in self.player.effects)
        if has_poison:
            pygame.draw.circle(s, (120,200,60), (px, py), self.player.radius+4, 1)
        # HOT indicator
        if self.player.hot_timer > 0:
            pygame.draw.circle(s, (100,255,180), (px, py), self.player.radius+8, 1)

    def _draw_enemy(self, e: Enemy, sox=0, soy=0):
        s = self.screen
        ex = int(e.pos.x - self.cam_x + sox)
        ey = int(e.pos.y - self.cam_y + soy)
        ratio = max(0.0, min(1.0, e.hp / max(1, e.max_hp)))
        if ratio > 0.66:
            col = (90, 200, 90)
        elif ratio > 0.33:
            col = (240, 210, 80)
        else:
            col = (220, 80, 80)

        # aura halo if buffed by an elite
        if e.mult_speed>1.0 or e.mult_damage>1.0 or e.mult_taken<1.0:
            pygame.draw.circle(s, (200,200,230), (ex,ey), e.radius+4, 1)

        # elite visuals
        if isinstance(e, Elite):
            aura_col = AURAS[e.aura]["color"]
            pygame.draw.circle(s, aura_col, (ex,ey), e.radius+6, 2)
            pygame.draw.polygon(s, (240,200,100), [(ex-10,ey-14),(ex-4,ey-22),(ex,ey-14),(ex+4,ey-22),(ex+10,ey-14)])

        pygame.draw.circle(s, col, (ex, ey), e.radius)

        # slow visual (blue tint overlay)
        if e.get_slow_mult() < 1.0:
            pygame.draw.circle(s, (100,180,255), (ex, ey), e.radius, 2)

        # poison visual (green tint)
        has_poison = any(eff.kind == "poison" for eff in e.effects)
        if has_poison:
            pygame.draw.circle(s, (120,200,60), (ex, ey), e.radius+2, 1)

        # HP bar for enemies
        if e.hp < e.max_hp:
            bar_w = e.radius * 2 + 4
            bar_h = 3
            bar_x = ex - bar_w//2
            bar_y = ey - e.radius - 8
            pygame.draw.rect(s, (40,40,40), (bar_x, bar_y, bar_w, bar_h))
            fill = max(0, int(bar_w * ratio))
            pygame.draw.rect(s, col, (bar_x, bar_y, fill, bar_h))

        # kind-specific features
        if isinstance(e, Boss):
            pygame.draw.polygon(s, (240,200,100), [(ex-12,ey-16),(ex-5,ey-26),(ex,ey-16),(ex+5,ey-26),(ex+12,ey-16)])
        elif e.kind == 0:
            pygame.draw.circle(s, (0,0,0), (ex-4, ey-2), 2)
            pygame.draw.circle(s, (0,0,0), (ex+4, ey-2), 2)
        elif e.kind == 1:
            pygame.draw.polygon(s, (180,180,200), [(ex-6,ey-8),(ex-2,ey-2),(ex-10,ey-2)])
            pygame.draw.polygon(s, (180,180,200), [(ex+6,ey-8),(ex+2,ey-2),(ex+10,ey-2)])
        elif e.kind == 2:
            pygame.draw.line(s, (0,0,0), (ex-4,ey+4), (ex-8,ey+10), 2)
            pygame.draw.line(s, (0,0,0), (ex+4,ey+4), (ex+8,ey+10), 2)
        elif e.kind == 3:  # spitter
            pygame.draw.circle(s, (40,40,60), (ex, ey), 3)
            pygame.draw.circle(s, (200,240,255), (ex+5, ey-3), 2)

    def _draw_minimap(self):
        mm_w = 220
        mm_h = 160
        surf = pygame.Surface((mm_w, mm_h), pygame.SRCALPHA)
        surf.fill((0,0,0,120))
        sx = mm_w / (MAP_W)
        sy = mm_h / (MAP_H)
        for tx in range(0, MAP_W, 2):
            for ty in range(0, MAP_H, 2):
                if not self.dungeon.seen[tx][ty]:
                    continue
                col = (70,70,80) if self.dungeon.tiles[tx][ty]==WALL else (120,120,140)
                pygame.draw.rect(surf, col, (tx*sx, ty*sy, sx*2, sy*2))
        # player
        pygame.draw.circle(surf, (200,240,200), (int(self.player.pos.x/ (TILE) * sx), int(self.player.pos.y/ (TILE) * sy)), 3)
        # enemies
        for e in self.enemies:
            if not e.alive: continue
            color = (255,150,150)
            if isinstance(e, Elite):
                color = (255,230,120)
            elif isinstance(e, Boss):
                color = (255,100,50)
            pygame.draw.circle(surf, color, (int(e.pos.x/(TILE)*sx), int(e.pos.y/(TILE)*sy)), 2)
        # stairs
        if self.dungeon.stairs_tx is not None:
            pygame.draw.rect(surf, (220,220,100), (int(self.dungeon.stairs_tx*sx), int(self.dungeon.stairs_ty*sy), 4, 4))
        self.screen.blit(surf, (WIDTH-mm_w-10, 10))

    def draw_ui(self):
        s = self.screen
        def bar(x,y,w,h, frac, bg=(40,40,44), fg=(120,200,120)):
            pygame.draw.rect(s, bg, (x,y,w,h))
            pygame.draw.rect(s, fg, (x+2,y+2,int((w-4)*max(0.0,min(1.0,frac))),h-4))
        # HP
        bar(16, 12, 260, 18, self.player.hp / self.player.max_hp)
        s.blit(self.font.render(f"HP {self.player.hp}/{self.player.max_hp}", True, (220,220,220)), (20, 12))
        # Mana
        bar(16, 36, 260, 18, self.player.mana / self.player.max_mana, fg=(120,160,220))
        s.blit(self.font.render(f"Mana {int(self.player.mana)}/{self.player.max_mana}", True, (220,220,220)), (20, 36))
        # XP/Level
        s.blit(self.font.render(f"Lvl {self.player.level}  Dlvl {self.current_level}/{LEVELS}  {self.difficulty_name}  Kills: {self.kill_count}", True, (255,255,255)), (16, 64))
        frac = self.player.xp / max(1, self.player.xp_to_next)
        bar(16, 84, 260, 12, frac, fg=(220, 200, 120))
        # buffs
        bx = 300
        if self.player.shield > 0:
            pygame.draw.rect(s, (80,200,250), (bx, 12, 90, 18), 1)
            s.blit(self.font.render(f"Shield {self.player.shield}", True, (180,240,255)), (bx+6, 14))
            bx += 104
        if self.player.dmg_timer > 0:
            pygame.draw.rect(s, (250,160,40), (bx, 12, 120, 18), 1)
            s.blit(self.font.render(f"Damage x{DMG_BOOST_MULT:.1f}", True, (255,210,120)), (bx+6, 14))
            bx += 134
        # poison indicator
        has_poison = any(e.kind == "poison" for e in self.player.effects)
        if has_poison:
            pygame.draw.rect(s, (120,200,60), (bx, 12, 80, 18), 1)
            s.blit(self.font.render("POISON", True, (120,200,60)), (bx+6, 14))
            bx += 94
        # gold/pots/weapon
        s.blit(self.font.render(f"Gold {self.player.gold}", True, (230,210,120)), (16, 104))
        s.blit(self.font.render(f"HP Pots [{self.player.potions_hp}]  Mana Pots [{self.player.potions_mana}]", True, (200,200,200)), (16, 124))
        s.blit(self.font.render(f"Weapon: {self.player.weapon.name} ({self.player.weapon.dmg_min}-{self.player.weapon.dmg_max})", True, (200,200,220)), (16, 144))

        # spell bar
        spell_y = HEIGHT - 50
        spell_x = 16
        spells = [
            ("1:Fireball", self.player.spell_fireball, self.player.fireball_cd, FIREBALL_CD, (255,140,40), FIREBALL_MANA),
            ("2:FrostNova", self.player.spell_frost_nova, self.player.frost_nova_cd, FROST_NOVA_CD, (150,220,255), FROST_NOVA_MANA),
            ("3:HealAura", self.player.spell_heal_aura, self.player.heal_aura_cd, HEAL_AURA_CD, (100,255,180), HEAL_AURA_MANA),
        ]
        for name, unlocked, cd, max_cd, color, mana_cost in spells:
            if unlocked:
                ready = cd <= 0 and self.player.mana >= mana_cost
                box_col = color if ready else (60,60,60)
                pygame.draw.rect(s, box_col, (spell_x, spell_y, 90, 22), 2 if ready else 1)
                if cd > 0:
                    cd_frac = cd / max_cd
                    pygame.draw.rect(s, (40,40,44), (spell_x+2, spell_y+2, 86, 18))
                    pygame.draw.rect(s, (60,60,70), (spell_x+2, spell_y+2, int(86*(1-cd_frac)), 18))
                txt_col = color if ready else (100,100,110)
                s.blit(self.smallfont.render(name, True, txt_col), (spell_x+4, spell_y+4))
            else:
                pygame.draw.rect(s, (30,30,34), (spell_x, spell_y, 90, 22), 1)
                s.blit(self.smallfont.render(name, True, (50,50,55)), (spell_x+4, spell_y+4))
            spell_x += 100

        # wave timer / controls hint
        s.blit(self.font.render(f"Wave {self.wave} in {self.spawn_timer:0.1f}s  •  P=Pause  F1=Help  Shift=Dash", True, (180,180,200)), (16, HEIGHT-24))

    # ----- Main Loop -----
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    if event.key == pygame.K_p:
                        self.paused = not self.paused
                    if event.key == pygame.K_F1:
                        self._help_overlay()
            if self.paused:
                self._pause_screen(); continue
            self.handle_input(dt)
            self.update_player(dt)
            self.update_enemies(dt)
            self.update_projectiles(dt)
            self.update_traps(dt)
            self.update_loot(dt)
            self.update_spawning(dt)
            self.update_particles(dt)
            # screen shake decay
            if self.shake_timer > 0:
                self.shake_timer -= dt
                if self.shake_timer <= 0:
                    self.shake_intensity = 0
            if self.player.hp <= 0:
                self.game_over(); return
            if self.boss_defeated:
                self.victory_screen(); return
            self.draw()

    def _pause_screen(self):
        s = self.screen
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,160))
        s.blit(overlay, (0,0))
        txt = self.bigfont.render("Paused", True, (240,240,250))
        s.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 20))
        pygame.display.flip()

    def _help_overlay(self):
        s = self.screen
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,200))
        s.blit(overlay, (0,0))
        lines = [
            "Controls:",
            "WASD move • LMB basic shot • RMB power shot (mana)",
            "Q/E use HP/Mana potions • Shift dash (i-frames)",
            "1: Fireball (AOE, unlocks Lv2) • 2: Frost Nova (slow, Lv3)",
            "3: Heal Aura (heal+HOT, unlocks Lv5)",
            "Elites lead packs with auras: Haste/Frenzy/Guardian.",
            "Watch out for spike and poison traps on the floor!",
            "Goal: explore, find stairs, reach Level 3, defeat Boss.",
        ]
        y = 90
        for ln in lines:
            t = self.font.render(ln, True, (230,230,240))
            s.blit(t, (WIDTH//2 - t.get_width()//2, y))
            y += 32
        pygame.display.flip()
        waiting = True
        while waiting:
            for e in pygame.event.get():
                if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.QUIT):
                    waiting = False

    def victory_screen(self):
        s = self.screen
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,180))
        s.blit(overlay, (0,0))

        title = self.bigfont.render("VICTORY!", True, (255, 220, 80))
        s.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 100))

        stats = [
            f"Difficulty: {self.difficulty_name}",
            f"Player Level: {self.player.level}",
            f"Enemies Slain: {self.kill_count}",
            f"Gold Collected: {self.player.gold}",
            f"Weapon: {self.player.weapon.name}",
        ]
        y = HEIGHT//2 - 40
        for line in stats:
            t = self.font.render(line, True, (220,220,230))
            s.blit(t, (WIDTH//2 - t.get_width()//2, y))
            y += 28

        sub = self.font.render("Press any key to quit", True, (180,180,190))
        s.blit(sub, (WIDTH//2 - sub.get_width()//2, y + 20))
        pygame.display.flip()
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type in (pygame.KEYDOWN, pygame.QUIT):
                    waiting = False

    def game_over(self):
        s = self.screen
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,180))
        s.blit(overlay, (0,0))

        txt = self.bigfont.render("You Died", True, (230, 100, 100))
        s.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 80))

        stats = [
            f"Difficulty: {self.difficulty_name}",
            f"Player Level: {self.player.level}",
            f"Dungeon Level: {self.current_level}",
            f"Enemies Slain: {self.kill_count}",
            f"Gold Collected: {self.player.gold}",
        ]
        y = HEIGHT//2 - 30
        for line in stats:
            t = self.font.render(line, True, (200,200,210))
            s.blit(t, (WIDTH//2 - t.get_width()//2, y))
            y += 26

        sub = self.font.render("Press any key to quit", True, (180,180,190))
        s.blit(sub, (WIDTH//2 - sub.get_width()//2, y + 16))
        pygame.display.flip()
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type in (pygame.KEYDOWN, pygame.QUIT):
                    waiting = False


if __name__ == "__main__":
    try:
        Game().run()
    except Exception as e:
        print("Fatal error:", e)
        pygame.quit()
        sys.exit(1)
