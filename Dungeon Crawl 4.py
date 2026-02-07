
import math
import random
import sys
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import pygame

# ======================= CONFIG =======================
WIDTH, HEIGHT = 1280, 720
FPS = 60
FONT_NAME = "consolas"

DIFFICULTY = {
    "Easy":   {"enemy_hp":0.9,"enemy_dmg":0.8,"enemy_speed":0.95,"max_enemies":6},
    "Normal": {"enemy_hp":1.0,"enemy_dmg":1.0,"enemy_speed":1.0, "max_enemies":7},
    "Hard":   {"enemy_hp":1.2,"enemy_dmg":1.25,"enemy_speed":1.05,"max_enemies":9},
}

PLAYER_SPEED = 250
PLAYER_HP = 140
PLAYER_MANA = 80

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

DASH_SPEED = 520
DASH_TIME = 0.22
DASH_CD = 1.5
IFRAME_TIME = 0.25

POTION_HEAL = 50
POTION_MANA = 40

ENEMY_BASE_HP = 40
ENEMY_BASE_DMG = (4, 8)
ENEMY_SPEED = 110
SPAWN_INTERVAL = 6.0
WAVE_SCALE = 1.10
MAX_ACTIVE_ENEMIES = 7

ELITE_PACK_CHANCE = 0.35
PACK_SIZE_RANGE = (3, 6)
ELITE_MULT = {"hp": 2.6, "dmg": 1.8, "spd": 1.08, "radius": 18}
AURA_RADIUS = 220
AURAS = {
    "haste":    {"speed":1.28,"damage":1.00,"taken":1.00,"color":(120,200,255)},
    "frenzy":   {"speed":1.00,"damage":1.35,"taken":1.00,"color":(255,150,90)},
    "guardian":  {"speed":1.00,"damage":1.00,"taken":0.66,"color":(120,255,160)},
}

BOSS_HP = 600
BOSS_DMG = (8, 14)
BOSS_SHOT_CD = (1.0, 1.6)
BOSS_PROJ_SPEED = 360

DMG_BOOST_MULT = 1.6
DMG_BOOST_TIME = 8.0
SHIELD_POINTS = 70
PICKUP_SPAWN_CHANCE = 0.25

GOLD_DROP = (3, 12)
POTION_DROP_CHANCE = 0.10
LOOT_DROP_CHANCE = 0.08
DMG_PICKUP_DROP_CHANCE = 0.06
SHIELD_PICKUP_DROP_CHANCE = 0.06

TILE = 34
MAP_W, MAP_H = 110, 85
LEVELS = 3
WALL = 1
FLOOR = 0

# ============ VISUAL CONFIG ============
AMBIENT_LIGHT = (20, 17, 25)
PLAYER_LIGHT_RADIUS = 280
PLAYER_LIGHT_COLOR = (255, 230, 190)
TORCH_LIGHT_RADIUS = 190
TORCH_LIGHT_COLOR = (255, 180, 80)
PROJ_LIGHT_RADIUS = 80
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
C_GOTHIC_FRAME = (90, 75, 50)
C_GOTHIC_FRAME_LIGHT = (140, 120, 80)
C_GOTHIC_BG = (12, 10, 15)

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
    def roll_damage(self) -> int:
        return random.randint(self.dmg_min, self.dmg_max)

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
    weapon: Weapon = field(default_factory=lambda: Weapon("Rusty Dagger", 6, 10, 2.5, False))
    dmg_mult: float = 1.0
    dmg_timer: float = 0.0
    shield: int = 0
    dash_cd: float = 0.0
    dash_timer: float = 0.0
    iframes: float = 0.0
    walk_anim: float = 0.0
    levelup_flash: float = 0.0

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

# ======================= DUNGEON =======================
class Dungeon:
    def __init__(self, level: int = 1):
        self.level = level
        self.tiles = [[WALL for _ in range(MAP_H)] for _ in range(MAP_W)]
        self.seen = [[False for _ in range(MAP_H)] for _ in range(MAP_W)]
        self.rooms: List[pygame.Rect] = []
        self.scenery: List[Tuple[int, int, str]] = []
        self.torches: List[Tuple[int, int]] = []
        self.blood_stains: List[Tuple[float, float, float]] = []
        self.stairs_tx = None
        self.stairs_ty = None
        self.tile_variants = [[random.randint(0, 7) for _ in range(MAP_H)] for _ in range(MAP_W)]
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
                self.scenery.append((tx, ty, 'pillar' if rng.random() < 0.6 else 'crate'))
            self._place_torches(new, rng)
        for x in range(MAP_W):
            self.tiles[x][0] = WALL
            self.tiles[x][MAP_H - 1] = WALL
        for y in range(MAP_H):
            self.tiles[0][y] = WALL
            self.tiles[MAP_W - 1][y] = WALL
        if self.rooms:
            sx, sy = self.center(self.rooms[-1])
            self.stairs_tx, self.stairs_ty = sx, sy
            self.tiles[sx][sy] = FLOOR

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

    def mark_seen_radius(self, pos: Vec, radius_px: int = 200):
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

# ======================= GAME =======================
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Dungeon of the Damned — ARPG")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(FONT_NAME, 18)
        self.bigfont = pygame.font.SysFont(FONT_NAME, 28, bold=True)
        self.dmgfont = pygame.font.SysFont(FONT_NAME, 20, bold=True)
        self.titlefont = pygame.font.SysFont(FONT_NAME, 52, bold=True)
        self.subfont = pygame.font.SysFont(FONT_NAME, 22)

        self.difficulty_name = self._difficulty_select()
        self.diff = DIFFICULTY[self.difficulty_name]
        global MAX_ACTIVE_ENEMIES
        MAX_ACTIVE_ENEMIES = self.diff["max_enemies"]

        self.current_level = 1
        self.dungeon = Dungeon(level=self.current_level)
        rx, ry = self.dungeon.center(self.dungeon.rooms[0]) if self.dungeon.rooms else (MAP_W // 2, MAP_H // 2)
        self.player = Player(pos=Vec(rx * TILE + TILE / 2, ry * TILE + TILE / 2), vel=Vec(0, 0), radius=14)
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
        self.dungeon.mark_seen_radius(self.player.pos)

        self._build_texture_cache()
        self._build_light_surfaces()
        self.light_map = pygame.Surface((WIDTH, HEIGHT))
        self.portal_angle = 0.0

        # ---- Mobile / Touch controls ----
        self.touch_mode = False  # auto-detected on first touch
        self.touch_move = Vec(0, 0)  # virtual joystick direction
        self.touch_joy_active = False
        self.touch_joy_id = None
        self.touch_joy_center = Vec(120, HEIGHT - 180)
        self.touch_joy_pos = Vec(120, HEIGHT - 180)
        self.touch_attack_active = False
        self.touch_power_active = False
        self.touch_dash_active = False
        self.touch_hppot_active = False
        self.touch_mpot_active = False
        # Button positions (right side)
        self.touch_btn_attack = Vec(WIDTH - 90, HEIGHT - 200)
        self.touch_btn_power = Vec(WIDTH - 170, HEIGHT - 160)
        self.touch_btn_dash = Vec(WIDTH - 90, HEIGHT - 120)
        self.touch_btn_hppot = Vec(WIDTH - 170, HEIGHT - 240)
        self.touch_btn_mpot = Vec(WIDTH - 250, HEIGHT - 200)
        self.touch_btn_radius = 32

    # ---- Texture generation ----
    def _build_texture_cache(self):
        self.wall_tiles = []
        for i in range(8):
            surf = pygame.Surface((TILE, TILE))
            base = 38 + (i * 3) % 16
            surf.fill((base, base - 2, base + 8))
            # stone brick mortar lines
            mortar = (base - 18, base - 20, base - 12)
            for row in range(3):
                y = row * (TILE // 3)
                pygame.draw.line(surf, mortar, (0, y), (TILE, y))
                offset = (TILE // 2) * (row % 2)
                for bx in range(offset, TILE + TILE // 2, TILE // 2):
                    if 0 <= bx < TILE:
                        pygame.draw.line(surf, mortar, (bx, y), (bx, y + TILE // 3))
            # highlight top edge
            pygame.draw.line(surf, (base + 12, base + 10, base + 18), (0, 0), (TILE - 1, 0))
            # noise
            for _ in range(6):
                nx, ny = random.randint(0, TILE - 1), random.randint(0, TILE - 1)
                c = random.randint(max(0, base - 12), min(255, base + 8))
                surf.set_at((nx, ny), (c, c - 2, c + 4))
            self.wall_tiles.append(surf)

        self.floor_tiles = []
        for i in range(8):
            surf = pygame.Surface((TILE, TILE))
            br = 22 + (i * 2) % 10
            bg = 20 + (i * 3) % 8
            bb = 24 + (i * 2) % 12
            surf.fill((br, bg, bb))
            # subtle stone joints
            jc = (br - 6, bg - 6, bb - 4)
            if i % 3 == 0:
                pygame.draw.line(surf, jc, (0, TILE // 2), (TILE, TILE // 2))
            if i % 3 == 1:
                pygame.draw.line(surf, jc, (TILE // 2, 0), (TILE // 2, TILE))
            # crack
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

        # torch texture
        self.torch_surf = pygame.Surface((12, 16), pygame.SRCALPHA)
        pygame.draw.rect(self.torch_surf, (90, 70, 40), (4, 6, 4, 10))
        pygame.draw.rect(self.torch_surf, (110, 85, 50), (3, 6, 6, 2))

    # ---- Lighting surfaces ----
    def _build_light_surfaces(self):
        self.light_surfs = {}
        for name, radius, color in [
            ("player", PLAYER_LIGHT_RADIUS, PLAYER_LIGHT_COLOR),
            ("torch", TORCH_LIGHT_RADIUS, TORCH_LIGHT_COLOR),
            ("proj_blue", PROJ_LIGHT_RADIUS, (140, 180, 255)),
            ("proj_red", PROJ_LIGHT_RADIUS, (255, 100, 80)),
            ("proj_power", PROJ_LIGHT_RADIUS + 20, (160, 140, 255)),
            ("elite_haste", 120, (100, 170, 255)),
            ("elite_frenzy", 120, (255, 130, 70)),
            ("elite_guardian", 120, (100, 220, 140)),
            ("portal", 140, (200, 200, 100)),
            ("loot", 50, (200, 180, 100)),
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

    # ---- Difficulty menu (gothic) ----
    def _difficulty_select(self) -> str:
        screen = self.screen
        font = self.bigfont
        small = self.font
        title_font = self.titlefont
        options = ["Easy", "Normal", "Hard"]
        descs = ["For the cautious adventurer", "The true dungeon experience", "Embrace suffering and death"]
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
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 120))

            # Decorative line
            ly = 185
            pygame.draw.line(screen, C_GOTHIC_FRAME, (WIDTH // 2 - 260, ly), (WIDTH // 2 + 260, ly), 2)
            pygame.draw.circle(screen, C_GOLD_DARK, (WIDTH // 2, ly), 5)
            pygame.draw.circle(screen, C_GOLD, (WIDTH // 2, ly), 3)

            # Subtitle
            sub = small.render("Choose your fate, wanderer", True, (150, 140, 120))
            screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 200))

            # Options
            for i, name in enumerate(options):
                bx = WIDTH // 2 - 300 + i * 300
                by = 290
                is_sel = (i == idx)
                # Selection box
                if is_sel:
                    glow = int(20 + 10 * math.sin(t * 4))
                    pygame.draw.rect(screen, (glow + 30, glow + 20, glow), (bx - 70, by - 10, 140, 80), border_radius=6)
                    pygame.draw.rect(screen, C_GOLD, (bx - 70, by - 10, 140, 80), 2, border_radius=6)
                col = C_GOLD if is_sel else (140, 135, 120)
                txt = font.render(name, True, col)
                screen.blit(txt, (bx - txt.get_width() // 2, by))
                desc = small.render(descs[i], True, (120, 115, 100) if is_sel else (80, 75, 65))
                screen.blit(desc, (bx - desc.get_width() // 2, by + 36))

            # Controls hint
            hint = small.render("[A/D] or [Arrow Keys] to choose  -  [Enter] to begin", True, (100, 95, 80))
            screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, 440))

            # Bottom decorative line
            pygame.draw.line(screen, (50, 45, 35), (100, 500), (WIDTH - 100, 500), 1)
            ver = small.render("Dungeon of the Damned v4.0", True, (60, 55, 45))
            screen.blit(ver, (WIDTH // 2 - ver.get_width() // 2, 520))

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
        e = Enemy(pos=pos, vel=Vec(0, 0), radius=14, hp=hp, max_hp=hp,
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

    def spawn_boss(self):
        if self.current_level != 3 or self.boss_spawned:
            return
        center_tx, center_ty = self.dungeon.center(self.dungeon.rooms[-1])
        pos = Vec(center_tx * TILE + TILE / 2, center_ty * TILE + TILE / 2)
        hp = int(BOSS_HP * self.diff["enemy_hp"])
        dmg_min = int(BOSS_DMG[0] * self.diff["enemy_dmg"])
        dmg_max = int(BOSS_DMG[1] * self.diff["enemy_dmg"])
        b = Boss(pos=pos, vel=Vec(0, 0), radius=24, hp=hp, max_hp=hp,
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
        # Merge touch joystick input
        if self.touch_mode and self.touch_joy_active and self.touch_move.length_squared() > 0:
            move = self.touch_move
        if move.length_squared() > 0:
            move = move.normalize()
        self.player.vel = move * PLAYER_SPEED

        # Dash: keyboard or touch button
        want_dash = keys[pygame.K_LSHIFT] or self.touch_dash_active
        if want_dash and self.player.dash_cd <= 0 and self.player.dash_timer <= 0:
            self.player.dash_timer = DASH_TIME
            self.player.dash_cd = DASH_CD
            self.player.iframes = max(self.player.iframes, IFRAME_TIME)
            self.emit_dust(self.player.pos.x, self.player.pos.y + 8, 6)
            self.touch_dash_active = False  # one-shot

        # Aim direction: mouse or auto-aim for touch
        if self.touch_mode:
            aim_dir = self._get_auto_aim_dir()
        else:
            mx, my = pygame.mouse.get_pos()
            world_mouse = Vec(mx + self.cam_x - self.shake_x, my + self.cam_y - self.shake_y)
            aim_dir = world_mouse - self.player.pos
            if aim_dir.length_squared() == 0:
                aim_dir = Vec(1, 0)
            aim_dir = aim_dir.normalize()

        # Shooting: mouse buttons or touch buttons
        buttons = pygame.mouse.get_pressed(3)
        want_basic = buttons[0] or self.touch_attack_active
        want_power = buttons[2] or self.touch_power_active
        if want_basic and self.player.basic_cd <= 0:
            self.shoot_basic(aim_dir)
        if want_power and self.player.power_cd <= 0 and self.player.mana >= POWER_MANA_COST:
            self.shoot_power(aim_dir)

        # Potions: keyboard or touch buttons
        want_hp_pot = keys[pygame.K_q] or self.touch_hppot_active
        want_mp_pot = keys[pygame.K_e] or self.touch_mpot_active
        if want_hp_pot and self.player.potions_hp > 0 and self.player.hp < PLAYER_HP:
            self.player.hp = min(PLAYER_HP + 10 * self.player.level, self.player.hp + POTION_HEAL)
            self.player.potions_hp -= 1
            self.emit_particles(self.player.pos.x, self.player.pos.y, 10, (100, 220, 100), speed=40, life=0.6, gravity=-60)
            self.add_floating_text(self.player.pos.x, self.player.pos.y - 20, f"+{POTION_HEAL}", (100, 255, 100))
            self.touch_hppot_active = False  # one-shot
        if want_mp_pot and self.player.potions_mana > 0 and self.player.mana < PLAYER_MANA:
            self.player.mana = min(PLAYER_MANA + 8 * self.player.level, self.player.mana + POTION_MANA)
            self.player.potions_mana -= 1
            self.emit_particles(self.player.pos.x, self.player.pos.y, 10, C_MANA_LIGHT, speed=40, life=0.6, gravity=-60)
            self.touch_mpot_active = False  # one-shot

    # ---- Combat ----
    def shoot_basic(self, direction: Vec):
        self.player.basic_cd = BASIC_CD
        base = random.randint(*BASIC_DMG)
        dmg = int(base * self.player.dmg_mult)
        proj = Projectile(pos=self.player.pos + direction * 20, vel=direction * PROJECTILE_SPEED,
                          dmg=dmg, ttl=0.9, radius=BASIC_RADIUS, pierce=BASIC_PIERCE)
        self.projectiles.append(proj)
        self.emit_sparks(self.player.pos.x + direction.x * 18, self.player.pos.y + direction.y * 18, 2)

    def shoot_power(self, direction: Vec):
        self.player.power_cd = POWER_CD
        self.player.mana -= POWER_MANA_COST
        base = random.randint(*POWER_DMG)
        dmg = int(base * self.player.dmg_mult)
        proj = Projectile(pos=self.player.pos + direction * 22, vel=direction * PROJECTILE_SPEED * 0.95,
                          dmg=dmg, ttl=1.1, radius=POWER_RADIUS, pierce=POWER_PIERCE)
        self.projectiles.append(proj)
        self.emit_magic(self.player.pos.x + direction.x * 20, self.player.pos.y + direction.y * 20, 5)
        self.add_screen_shake(2)

    # ---- Updates ----
    def update_player(self, dt: float):
        p = self.player
        p.basic_cd = max(0.0, p.basic_cd - dt)
        p.power_cd = max(0.0, p.power_cd - dt)
        p.dash_cd = max(0.0, p.dash_cd - dt)
        p.iframes = max(0.0, p.iframes - dt)
        p.levelup_flash = max(0.0, p.levelup_flash - dt)
        if p.dmg_timer > 0:
            p.dmg_timer -= dt
            if p.dmg_timer <= 0:
                p.dmg_mult = 1.0
        vel = p.vel
        if p.dash_timer > 0:
            p.dash_timer -= dt
            if vel.length_squared() > 0:
                vel = vel.normalize() * DASH_SPEED
            else:
                vel = Vec(1, 0) * DASH_SPEED
            # dash trail
            if random.random() < 0.5:
                self.emit_dust(p.pos.x, p.pos.y + 6, 1)
        # walking animation
        if vel.length_squared() > 100:
            p.walk_anim += dt * 10
            if random.random() < 0.05:
                self.emit_dust(p.pos.x, p.pos.y + 10, 1)
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
        if self.dungeon.stairs_tx is not None:
            sx = self.dungeon.stairs_tx * TILE + TILE / 2
            sy = self.dungeon.stairs_ty * TILE + TILE / 2
            if (Vec(sx, sy) - p.pos).length() < 18:
                self.next_level()

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
            desired = (p.pos - e.pos)
            dist = desired.length() or 0.0001
            desired = desired / dist
            jitter = Vec(random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2))
            acc = (desired + jitter).normalize() * (e.speed * e.mult_speed)
            e.vel += (acc - e.vel) * 0.1
            new_epos = e.pos + e.vel * dt
            # axis-separated wall collision (like player)
            test_x = Vec(new_epos.x, e.pos.y)
            if not self._circle_collides(test_x, e.radius):
                e.pos.x = test_x.x
            else:
                e.vel.x *= -0.3
            test_y = Vec(e.pos.x, new_epos.y)
            if not self._circle_collides(test_y, e.radius):
                e.pos.y = test_y.y
            else:
                e.vel.y *= -0.3
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
                    pr.ttl = 0
                    continue
            else:
                for e in self.enemies:
                    if not e.alive:
                        continue
                    if (e.pos - pr.pos).length() < e.radius + pr.radius:
                        damage = max(1, int(pr.dmg * e.mult_taken))
                        e.hp -= damage
                        e.knockback = 200
                        e.vel += (e.pos - pr.pos).normalize() * 300
                        e.hit_flash = 0.12
                        self.add_floating_text(e.pos.x, e.pos.y - e.radius - 8,
                                               str(damage), C_GOLD if damage > 15 else (220, 220, 220),
                                               scale=1.3 if damage > 20 else 1.0)
                        self.emit_blood(e.pos.x, e.pos.y, 4)
                        if damage > 15:
                            self.add_screen_shake(2)
                        pr.pierce -= 1
                        if pr.pierce <= 0:
                            pr.ttl = 0
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
                if l.potion_hp:
                    self.player.potions_hp += 1
                if l.potion_mana:
                    self.player.potions_mana += 1
                if l.weapon:
                    self.player.weapon = l.weapon
                    self.add_floating_text(l.pos.x, l.pos.y - 10, "New Weapon!", (255, 200, 80), 1.2)
                if l.dmg_boost:
                    self.player.dmg_mult = DMG_BOOST_MULT
                    self.player.dmg_timer = DMG_BOOST_TIME
                    self.add_floating_text(l.pos.x, l.pos.y - 10, "POWER UP!", (255, 160, 40), 1.3)
                    self.emit_particles(l.pos.x, l.pos.y, 12, C_FIRE_BRIGHT, speed=60, life=0.6, gravity=-40)
                if l.shield_boost:
                    self.player.shield = max(self.player.shield, SHIELD_POINTS)
                    self.add_floating_text(l.pos.x, l.pos.y - 10, "SHIELD!", C_ICE, 1.3)
                    self.emit_particles(l.pos.x, l.pos.y, 12, C_ICE, speed=60, life=0.6, gravity=-40)
                self.emit_sparks(l.pos.x, l.pos.y, 3)
                l.ttl = 0
        self.loots = [l for l in self.loots if l.ttl > 0]

    def on_enemy_dead(self, e: Enemy):
        old_level = self.player.level
        self.player.xp += 6 + self.wave
        while self.player.xp >= self.player.xp_to_next:
            self.player.xp -= self.player.xp_to_next
            self.player.level += 1
            self.player.xp_to_next = int(self.player.xp_to_next * 1.35)
            self.player.hp = min(PLAYER_HP + 10 * self.player.level, self.player.hp + 30)
            self.player.mana = min(PLAYER_MANA + 8 * self.player.level, self.player.mana + 20)
        if self.player.level > old_level:
            self.player.levelup_flash = 2.0
            self.add_floating_text(self.player.pos.x, self.player.pos.y - 30, "LEVEL UP!", C_GOLD, 1.5)
            self.emit_particles(self.player.pos.x, self.player.pos.y, 25, C_GOLD, speed=100, life=1.0, gravity=-50)
            self.add_screen_shake(5)

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

        # corpse
        self.corpses.append(Corpse(x=e.pos.x, y=e.pos.y, radius=e.radius, kind=e.kind,
                                   color=death_color, is_boss=isinstance(e, Boss),
                                   is_elite=isinstance(e, Elite)))

        drops: List[Loot] = []
        if random.random() < 0.9:
            drops.append(Loot(pos=e.pos.copy(), gold=random.randint(*GOLD_DROP)))
        if random.random() < POTION_DROP_CHANCE:
            potion = random.choice(["hp", "mana"])
            drops.append(Loot(pos=e.pos.copy(), potion_hp=(potion == "hp"), potion_mana=(potion == "mana")))
        if random.random() < LOOT_DROP_CHANCE:
            drops.append(Loot(pos=e.pos.copy(), weapon=Weapon("Find", 10, 16, 2.0, True)))
        if random.random() < DMG_PICKUP_DROP_CHANCE:
            drops.append(Loot(pos=e.pos.copy(), dmg_boost=True))
        if random.random() < SHIELD_PICKUP_DROP_CHANCE:
            drops.append(Loot(pos=e.pos.copy(), shield_boost=True))
        if isinstance(e, Elite):
            drops.append(Loot(pos=e.pos.copy(), gold=random.randint(15, 35)))
            if random.random() < 0.5:
                drops.append(Loot(pos=e.pos.copy(), dmg_boost=True))
            else:
                drops.append(Loot(pos=e.pos.copy(), shield_boost=True))
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
    def next_level(self):
        if self.current_level >= LEVELS:
            self.current_level = 1
        else:
            self.current_level += 1
        self.dungeon = Dungeon(level=self.current_level)
        rx, ry = self.dungeon.center(self.dungeon.rooms[0]) if self.dungeon.rooms else (MAP_W // 2, MAP_H // 2)
        self.player.pos = Vec(rx * TILE + TILE / 2, ry * TILE + TILE / 2)
        self.enemies.clear()
        self.projectiles.clear()
        self.loots.clear()
        self.particles.clear()
        self.floating_texts.clear()
        self.corpses.clear()
        self.wave = 1
        self.spawn_timer = SPAWN_INTERVAL
        self.dungeon.mark_seen_radius(self.player.pos)
        self.boss_spawned = False

    # ======================= RENDERING =======================
    def draw(self):
        s = self.screen
        s.fill(C_GOTHIC_BG)
        ox = int(self.shake_x)
        oy = int(self.shake_y)

        self._draw_tiles(s, ox, oy)
        self._draw_blood_stains(s, ox, oy)
        self._draw_scenery(s, ox, oy)
        self._draw_stairs_portal(s, ox, oy)
        self._draw_torches(s, ox, oy)
        self._draw_corpses(s, ox, oy)
        self._draw_loot(s, ox, oy)
        self._draw_projectiles(s, ox, oy)
        self._draw_enemies(s, ox, oy)
        self._draw_player(s, ox, oy)
        self._draw_particles(s, ox, oy)
        self._draw_floating_texts(s, ox, oy)
        self._draw_lighting(s, ox, oy)
        self._draw_ui(s)
        if not self.touch_mode:
            self._draw_reticle(s)
        self._draw_minimap(s)
        self._draw_touch_controls(s)
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
            if t == 'pillar':
                # shadow
                pygame.draw.ellipse(s, (10, 8, 12), (px + 4, py + TILE - 8, TILE - 8, 6))
                s.blit(self.pillar_surf, (px, py))
            else:
                pygame.draw.ellipse(s, (10, 8, 12), (px + 3, py + TILE - 7, TILE - 6, 5))
                s.blit(self.crate_surf, (px, py))

    def _draw_stairs_portal(self, s, ox, oy):
        if self.dungeon.stairs_tx is None:
            return
        if not self._tile_in_view(self.dungeon.stairs_tx, self.dungeon.stairs_ty):
            return
        px = self.dungeon.stairs_tx * TILE - self.cam_x + ox + TILE // 2
        py = self.dungeon.stairs_ty * TILE - self.cam_y + oy + TILE // 2
        self.portal_angle += 0.05
        # swirling portal
        for i in range(8):
            ang = self.portal_angle + i * (math.tau / 8)
            r = 12
            x = px + int(math.cos(ang) * r)
            y = py + int(math.sin(ang) * r)
            pulse = 0.6 + 0.4 * math.sin(self.game_time * 3 + i)
            col = (int(200 * pulse), int(200 * pulse), int(80 * pulse))
            pygame.draw.circle(s, col, (x, y), 3)
        # center glow
        glow = 0.7 + 0.3 * math.sin(self.game_time * 2)
        pygame.draw.circle(s, (int(160 * glow), int(160 * glow), int(60 * glow)), (px, py), 8)
        pygame.draw.circle(s, (int(220 * glow), int(220 * glow), int(80 * glow)), (px, py), 4)

    def _draw_torches(self, s, ox, oy):
        for tx, ty in self.dungeon.torches:
            if not self._tile_in_view(tx, ty):
                continue
            if not self.dungeon.seen[tx][ty]:
                continue
            px = tx * TILE - self.cam_x + ox + TILE // 2
            py = ty * TILE - self.cam_y + oy + TILE // 2
            # torch base
            pygame.draw.rect(s, (90, 70, 40), (px - 2, py, 4, 8))
            # flame
            flicker = random.uniform(0.6, 1.0)
            fr = int(255 * flicker)
            fg = int(160 * flicker)
            fb = int(40 * flicker)
            pygame.draw.circle(s, (fr, fg, fb), (px, py - 2), 4)
            pygame.draw.circle(s, (255, min(255, fg + 60), fb + 20), (px, py - 4), 2)
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

    def _draw_loot(self, s, ox, oy):
        for l in self.loots:
            vx = int(l.pos.x - self.cam_x + ox)
            vy = int(l.pos.y - self.cam_y + oy + math.sin(l.bob_phase) * 3)
            if not (-20 < vx < WIDTH + 20 and -20 < vy < HEIGHT + 20):
                continue
            # glow under loot
            glow_alpha = int(30 + 15 * math.sin(l.bob_phase * 1.5))
            if l.weapon:
                pygame.draw.circle(s, (glow_alpha + 20, glow_alpha + 10, 0), (vx, vy), 12)
                pygame.draw.rect(s, (255, 225, 120), (vx - 6, vy - 6, 12, 12), border_radius=2)
                pygame.draw.rect(s, (200, 170, 60), (vx - 6, vy - 6, 12, 12), 1, border_radius=2)
            elif l.potion_hp:
                pygame.draw.circle(s, (glow_alpha, 0, 0), (vx, vy), 10)
                pygame.draw.rect(s, (200, 40, 40), (vx - 5, vy - 5, 10, 10), border_radius=3)
                pygame.draw.rect(s, (255, 80, 80), (vx - 2, vy - 4, 4, 3))
            elif l.potion_mana:
                pygame.draw.circle(s, (0, 0, glow_alpha), (vx, vy), 10)
                pygame.draw.rect(s, (40, 80, 200), (vx - 5, vy - 5, 10, 10), border_radius=3)
                pygame.draw.rect(s, (80, 120, 255), (vx - 2, vy - 4, 4, 3))
            elif l.dmg_boost:
                pygame.draw.circle(s, (glow_alpha + 15, glow_alpha, 0), (vx, vy), 10)
                pygame.draw.circle(s, (250, 160, 40), (vx, vy), 7)
                pygame.draw.circle(s, (255, 220, 120), (vx, vy), 4)
                # pulsing rays
                for i in range(4):
                    ang = self.game_time * 2 + i * math.pi / 2
                    ex = vx + int(math.cos(ang) * 9)
                    ey = vy + int(math.sin(ang) * 9)
                    pygame.draw.line(s, (255, 200, 80), (vx, vy), (ex, ey), 1)
            elif l.shield_boost:
                pygame.draw.circle(s, (0, 0, glow_alpha + 10), (vx, vy), 10)
                pygame.draw.circle(s, (80, 200, 250), (vx, vy), 7)
                pygame.draw.circle(s, (180, 240, 255), (vx, vy), 4)
                for i in range(4):
                    ang = self.game_time * 2 + i * math.pi / 2
                    ex = vx + int(math.cos(ang) * 9)
                    ey = vy + int(math.sin(ang) * 9)
                    pygame.draw.line(s, (140, 220, 255), (vx, vy), (ex, ey), 1)
            elif l.gold:
                pygame.draw.circle(s, (glow_alpha + 10, glow_alpha + 5, 0), (vx, vy), 8)
                pygame.draw.circle(s, (255, 215, 0), (vx, vy), 5)
                pygame.draw.circle(s, (200, 170, 0), (vx, vy), 5, 1)

    def _draw_projectiles(self, s, ox, oy):
        for pr in self.projectiles:
            px = int(pr.pos.x - self.cam_x + ox)
            py = int(pr.pos.y - self.cam_y + oy)
            if not (-20 < px < WIDTH + 20 and -20 < py < HEIGHT + 20):
                continue
            if pr.hostile:
                # red enemy projectile with glow
                pygame.draw.circle(s, (120, 30, 30), (px, py), pr.radius + 3)
                pygame.draw.circle(s, (255, 100, 110), (px, py), pr.radius)
                pygame.draw.circle(s, (255, 180, 180), (px, py), max(1, pr.radius - 2))
            else:
                if pr.radius > BASIC_RADIUS:
                    # power shot - purple/blue glow
                    pygame.draw.circle(s, (60, 40, 120), (px, py), pr.radius + 4)
                    pygame.draw.circle(s, (140, 120, 255), (px, py), pr.radius)
                    pygame.draw.circle(s, (200, 190, 255), (px, py), max(1, pr.radius - 2))
                else:
                    # basic shot - blue glow
                    pygame.draw.circle(s, (40, 60, 100), (px, py), pr.radius + 2)
                    pygame.draw.circle(s, (140, 200, 255), (px, py), pr.radius)
                    pygame.draw.circle(s, (220, 240, 255), (px, py), max(1, pr.radius - 1))

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
        pygame.draw.ellipse(s, (8, 6, 10), (ex - e.radius, ey + e.radius - 4, e.radius * 2, 8))

        # Aura ring for buffed minions
        if e.mult_speed > 1.0 or e.mult_damage > 1.0 or e.mult_taken < 1.0:
            pulse = 0.6 + 0.4 * math.sin(self.game_time * 4)
            ac = (int(180 * pulse), int(160 * pulse), int(220 * pulse))
            pygame.draw.circle(s, ac, (ex, ey), e.radius + 5, 2)

        # Elite aura effect
        if isinstance(e, Elite):
            aura_col = AURAS[e.aura]["color"]
            pulse = 0.5 + 0.5 * math.sin(e.aura_pulse)
            r = int(aura_col[0] * pulse * 0.5)
            g = int(aura_col[1] * pulse * 0.5)
            b = int(aura_col[2] * pulse * 0.5)
            pygame.draw.circle(s, (r, g, b), (ex, ey), e.radius + 10, 3)
            # Crown
            crown_col = (240, 200, 100)
            pts = [(ex - 10, ey - 16), (ex - 5, ey - 24), (ex - 1, ey - 16),
                   (ex + 1, ey - 16), (ex + 5, ey - 24), (ex + 10, ey - 16)]
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
            pygame.draw.circle(s, (40, 15, 15), (ex, ey), e.radius + 2)
            pygame.draw.circle(s, body_col, (ex, ey), e.radius)
            # inner detail
            pygame.draw.circle(s, (max(0, body_col[0] - 30), max(0, body_col[1] - 30), max(0, body_col[2] - 20)),
                               (ex, ey), e.radius - 4)
            # Demonic eyes
            pygame.draw.circle(s, (255, 60, 20), (ex - 8, ey - 6), 4)
            pygame.draw.circle(s, (255, 60, 20), (ex + 8, ey - 6), 4)
            pygame.draw.circle(s, (255, 220, 60), (ex - 8, ey - 6), 2)
            pygame.draw.circle(s, (255, 220, 60), (ex + 8, ey - 6), 2)
            # Crown
            pts = [(ex - 14, ey - 18), (ex - 7, ey - 30), (ex, ey - 18),
                   (ex + 7, ey - 30), (ex + 14, ey - 18)]
            pygame.draw.polygon(s, (240, 180, 60), pts)
            pygame.draw.polygon(s, (180, 130, 30), pts, 2)
            # Mouth
            pygame.draw.arc(s, (0, 0, 0), (ex - 8, ey + 2, 16, 10), 3.14, 6.28, 2)
        else:
            # Regular enemy body
            pygame.draw.circle(s, (max(0, body_col[0] - 40), max(0, body_col[1] - 40), max(0, body_col[2] - 30)),
                               (ex, ey), e.radius + 1)
            pygame.draw.circle(s, body_col, (ex, ey), e.radius)

            if e.kind == 0:  # Eyes demon
                pygame.draw.circle(s, (220, 40, 20), (ex - 4, ey - 3), 3)
                pygame.draw.circle(s, (220, 40, 20), (ex + 4, ey - 3), 3)
                pygame.draw.circle(s, (255, 200, 60), (ex - 4, ey - 3), 1)
                pygame.draw.circle(s, (255, 200, 60), (ex + 4, ey - 3), 1)
            elif e.kind == 1:  # Horned
                pygame.draw.polygon(s, (140, 110, 80), [(ex - 8, ey - 10), (ex - 4, ey - 2), (ex - 12, ey - 2)])
                pygame.draw.polygon(s, (140, 110, 80), [(ex + 8, ey - 10), (ex + 4, ey - 2), (ex + 12, ey - 2)])
                pygame.draw.circle(s, (200, 40, 20), (ex - 3, ey - 2), 2)
                pygame.draw.circle(s, (200, 40, 20), (ex + 3, ey - 2), 2)
            elif e.kind == 2:  # Mandibles
                pygame.draw.line(s, (160, 120, 80), (ex - 4, ey + 4), (ex - 10, ey + 12), 2)
                pygame.draw.line(s, (160, 120, 80), (ex + 4, ey + 4), (ex + 10, ey + 12), 2)
                pygame.draw.circle(s, (200, 40, 20), (ex - 3, ey - 2), 2)
                pygame.draw.circle(s, (200, 40, 20), (ex + 3, ey - 2), 2)
            elif e.kind == 3:  # Spitter
                pygame.draw.circle(s, (30, 30, 50), (ex, ey), 4)
                pygame.draw.circle(s, (200, 60, 255), (ex, ey), 2)
                pygame.draw.circle(s, (200, 40, 20), (ex + 6, ey - 4), 2)
                pygame.draw.circle(s, (255, 200, 60), (ex + 6, ey - 4), 1)

        # HP bar above enemy
        if ratio < 1.0:
            bar_w = e.radius * 2 + 4
            bar_h = 3
            bar_x = ex - bar_w // 2
            bar_y = ey - e.radius - 10
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
        pygame.draw.ellipse(s, (8, 6, 10), (px - 10, py + 10, 20, 8))

        # Level up flash
        if p.levelup_flash > 0:
            flash_r = int(40 + 20 * math.sin(p.levelup_flash * 8))
            pygame.draw.circle(s, (flash_r, flash_r - 5, 0), (px, py), 30, 2)

        # Iframes blink
        if p.iframes > 0 and int(p.iframes * 20) % 2 == 0:
            return  # blink effect

        # Dash afterimage
        if p.dash_timer > 0:
            pygame.draw.circle(s, (40, 60, 100), (px, py), 16, 2)

        # Body - armored warrior
        # Feet with walk animation
        walk_offset = int(math.sin(p.walk_anim) * 3) if p.vel.length_squared() > 100 else 0
        pygame.draw.rect(s, (50, 45, 35), (px - 7, py + 9 + walk_offset, 6, 5), border_radius=2)
        pygame.draw.rect(s, (50, 45, 35), (px + 1, py + 9 - walk_offset, 6, 5), border_radius=2)

        # Torso (armor)
        pygame.draw.rect(s, (55, 65, 90), (px - 9, py - 6, 18, 18), border_radius=4)
        # Armor detail
        pygame.draw.rect(s, (70, 82, 110), (px - 7, py - 4, 14, 3), border_radius=1)
        pygame.draw.rect(s, (65, 75, 100), (px - 5, py + 2, 10, 2))
        # Shoulder pauldrons
        pygame.draw.circle(s, (70, 80, 105), (px - 10, py - 3), 5)
        pygame.draw.circle(s, (70, 80, 105), (px + 10, py - 3), 5)
        pygame.draw.circle(s, (85, 95, 125), (px - 10, py - 4), 3)
        pygame.draw.circle(s, (85, 95, 125), (px + 10, py - 4), 3)

        # Head (helmet)
        pygame.draw.circle(s, (75, 80, 95), (px, py - 9), 7)
        # Visor slit
        pygame.draw.rect(s, (180, 170, 140), (px - 4, py - 10, 8, 2))

        # Cape hint
        if p.vel.length_squared() > 100:
            cape_sway = int(math.sin(p.walk_anim * 0.7) * 3)
            pygame.draw.polygon(s, (50, 30, 30),
                                [(px - 6, py + 2), (px + 6, py + 2),
                                 (px + 4 + cape_sway, py + 14), (px - 4 + cape_sway, py + 14)])

        # Arm/weapon toward mouse
        mx, my = pygame.mouse.get_pos()
        ang = math.atan2(my - py, mx - px)
        hand_x = px + int(math.cos(ang) * 14)
        hand_y = py + int(math.sin(ang) * 14)
        # Weapon glow based on power cooldown
        if p.dmg_timer > 0:
            weapon_col = (255, 180, 60)
        else:
            weapon_col = (180, 180, 190)
        pygame.draw.line(s, (100, 95, 85), (px + int(math.cos(ang) * 6), py + int(math.sin(ang) * 6)),
                         (hand_x, hand_y), 2)
        pygame.draw.circle(s, weapon_col, (hand_x, hand_y), 3)

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
        self.light_map.fill(AMBIENT_LIGHT)
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

        # Portal light
        if self.dungeon.stairs_tx is not None and self._tile_in_view(self.dungeon.stairs_tx, self.dungeon.stairs_ty):
            stx = int(self.dungeon.stairs_tx * TILE + TILE // 2 - self.cam_x + ox)
            sty = int(self.dungeon.stairs_ty * TILE + TILE // 2 - self.cam_y + oy)
            pls3 = self.light_surfs["portal"]
            r3 = pls3.get_width() // 2
            self.light_map.blit(pls3, (stx - r3, sty - r3), special_flags=pygame.BLEND_RGB_ADD)

        # Apply lighting
        s.blit(self.light_map, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

    def _draw_reticle(self, s):
        mx, my = pygame.mouse.get_pos()
        # outer ring
        pygame.draw.circle(s, (180, 160, 120), (mx, my), 8, 1)
        # crosshair
        gap = 3
        length = 8
        pygame.draw.line(s, (200, 180, 140), (mx - length, my), (mx - gap, my), 1)
        pygame.draw.line(s, (200, 180, 140), (mx + gap, my), (mx + length, my), 1)
        pygame.draw.line(s, (200, 180, 140), (mx, my - length), (mx, my - gap), 1)
        pygame.draw.line(s, (200, 180, 140), (mx, my + gap), (mx, my + length), 1)
        # center dot
        pygame.draw.circle(s, (220, 200, 160), (mx, my), 1)

    def _draw_minimap(self, s):
        mm_w = 240
        mm_h = 170
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

        # stairs
        if self.dungeon.stairs_tx is not None:
            stpx = int(self.dungeon.stairs_tx * sx)
            stpy = int(self.dungeon.stairs_ty * sy)
            pulse = 0.5 + 0.5 * math.sin(self.game_time * 3)
            col = (int(220 * pulse), int(220 * pulse), int(80 * pulse), 255)
            pygame.draw.rect(surf, col, (stpx - 2, stpy - 2, 5, 5))

        s.blit(surf, (WIDTH - mm_w - 12, 12))

    # ---- Diablo-style UI ----
    def _draw_ui(self, s):
        p = self.player
        max_hp = PLAYER_HP + 10 * p.level
        max_mana = PLAYER_MANA + 8 * p.level

        # Bottom panel background
        panel_h = 80
        panel_surf = pygame.Surface((WIDTH, panel_h), pygame.SRCALPHA)
        panel_surf.fill((10, 8, 14, 200))
        pygame.draw.line(panel_surf, (80, 65, 45, 200), (0, 0), (WIDTH, 0), 2)
        s.blit(panel_surf, (0, HEIGHT - panel_h))

        # Health globe (left)
        globe_r = 32
        globe_cx = 60
        globe_cy = HEIGHT - panel_h // 2
        hp_frac = max(0, min(1, p.hp / max_hp))
        self._draw_globe(s, globe_cx, globe_cy, globe_r, hp_frac,
                         empty_color=(40, 10, 10), fill_color=(160, 25, 25),
                         highlight_color=(200, 60, 60), frame_color=C_GOTHIC_FRAME)
        # HP text
        hp_txt = self.font.render(f"{p.hp}", True, (220, 200, 200))
        s.blit(hp_txt, (globe_cx - hp_txt.get_width() // 2, globe_cy - hp_txt.get_height() // 2))

        # Mana globe (right)
        mana_cx = WIDTH - 60
        mana_frac = max(0, min(1, p.mana / max_mana))
        self._draw_globe(s, mana_cx, globe_cy, globe_r, mana_frac,
                         empty_color=(10, 15, 45), fill_color=(30, 50, 170),
                         highlight_color=(60, 90, 220), frame_color=C_GOTHIC_FRAME)
        mana_txt = self.font.render(f"{p.mana}", True, (200, 210, 240))
        s.blit(mana_txt, (mana_cx - mana_txt.get_width() // 2, globe_cy - mana_txt.get_height() // 2))

        # XP bar between globes
        xp_frac = p.xp / max(1, p.xp_to_next)
        bar_x = 110
        bar_w = WIDTH - 220
        bar_y = HEIGHT - 16
        bar_h = 8
        pygame.draw.rect(s, (25, 20, 15), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(s, (180, 160, 80), (bar_x, bar_y, int(bar_w * xp_frac), bar_h))
        pygame.draw.rect(s, C_GOTHIC_FRAME, (bar_x, bar_y, bar_w, bar_h), 1)
        xp_label = self.font.render(f"Level {p.level}", True, (200, 190, 150))
        s.blit(xp_label, (WIDTH // 2 - xp_label.get_width() // 2, bar_y - 16))

        # Skill indicators / cooldowns
        skill_y = HEIGHT - panel_h + 8
        # Basic attack
        cd_frac = p.basic_cd / BASIC_CD if BASIC_CD > 0 else 0
        self._draw_skill_icon(s, WIDTH // 2 - 60, skill_y, 28, cd_frac, (140, 200, 255), "LMB")
        # Power shot
        cd_frac2 = p.power_cd / POWER_CD if POWER_CD > 0 else 0
        self._draw_skill_icon(s, WIDTH // 2 - 20, skill_y, 28, cd_frac2, (160, 120, 255), "RMB")
        # Dash
        dash_frac = p.dash_cd / DASH_CD if DASH_CD > 0 else 0
        self._draw_skill_icon(s, WIDTH // 2 + 20, skill_y, 28, dash_frac, (100, 200, 140), "Shift")

        # Potion slots
        pot_y = HEIGHT - panel_h + 12
        # HP potion
        pygame.draw.rect(s, (60, 20, 20), (WIDTH // 2 + 80, pot_y, 24, 24), border_radius=4)
        pygame.draw.rect(s, (120, 40, 40), (WIDTH // 2 + 80, pot_y, 24, 24), 1, border_radius=4)
        pot_txt = self.font.render(f"{p.potions_hp}", True, (220, 160, 160))
        s.blit(pot_txt, (WIDTH // 2 + 86, pot_y + 4))
        q_label = self.font.render("Q", True, (150, 130, 120))
        s.blit(q_label, (WIDTH // 2 + 87, pot_y + 26))

        # Mana potion
        pygame.draw.rect(s, (20, 30, 80), (WIDTH // 2 + 112, pot_y, 24, 24), border_radius=4)
        pygame.draw.rect(s, (40, 60, 140), (WIDTH // 2 + 112, pot_y, 24, 24), 1, border_radius=4)
        pot_txt2 = self.font.render(f"{p.potions_mana}", True, (160, 180, 220))
        s.blit(pot_txt2, (WIDTH // 2 + 118, pot_y + 4))
        e_label = self.font.render("E", True, (150, 130, 120))
        s.blit(e_label, (WIDTH // 2 + 119, pot_y + 26))

        # Gold
        gold_txt = self.font.render(f"Gold: {p.gold}", True, C_GOLD)
        s.blit(gold_txt, (120, HEIGHT - panel_h + 10))

        # Active buffs
        buff_x = 120
        buff_y = HEIGHT - panel_h + 32
        if p.shield > 0:
            pygame.draw.rect(s, (60, 160, 210), (buff_x, buff_y, 100, 18), 1, border_radius=3)
            txt = self.font.render(f"Shield {p.shield}", True, C_ICE)
            s.blit(txt, (buff_x + 6, buff_y + 1))
            buff_x += 110
        if p.dmg_timer > 0:
            pygame.draw.rect(s, (200, 130, 30), (buff_x, buff_y, 120, 18), 1, border_radius=3)
            txt = self.font.render(f"Dmg x{DMG_BOOST_MULT:.1f} {p.dmg_timer:.1f}s", True, (255, 200, 100))
            s.blit(txt, (buff_x + 6, buff_y + 1))

        # Top-left info
        info = self.font.render(f"Dlvl {self.current_level}/{LEVELS}  {self.difficulty_name}  Wave {self.wave}", True, (170, 165, 150))
        s.blit(info, (16, 12))
        wave_txt = self.font.render(f"Next wave: {self.spawn_timer:.1f}s", True, (140, 135, 120))
        s.blit(wave_txt, (16, 32))
        hint = self.font.render("P=Pause  F1=Help", True, (90, 85, 75))
        s.blit(hint, (16, 52))

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
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        txt = self.titlefont.render("PAUSED", True, C_GOLD)
        self.screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 40))
        sub = self.subfont.render("Press P to resume", True, (160, 150, 130))
        self.screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2 + 20))
        pygame.display.flip()

    def _help_overlay(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.screen.blit(overlay, (0, 0))

        title = self.bigfont.render("- CONTROLS -", True, C_GOLD)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))
        pygame.draw.line(self.screen, C_GOTHIC_FRAME, (WIDTH // 2 - 150, 115), (WIDTH // 2 + 150, 115), 1)

        lines = [
            ("WASD", "Move"),
            ("Left Click", "Basic Shot"),
            ("Right Click", "Power Shot (costs mana)"),
            ("Q / E", "Use HP / Mana Potion"),
            ("Left Shift", "Dash (grants invulnerability)"),
            ("P", "Pause"),
            ("Esc", "Quit"),
            ("", ""),
            ("Elites", "Lead packs with auras: Haste / Frenzy / Guardian"),
            ("Goal", "Explore, find stairs, reach Level 3, defeat the Boss"),
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

    def game_over(self):
        # Death effects
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        # Fade to red-black
        for i in range(30):
            overlay.fill((0, 0, 0, 8))
            self.screen.blit(overlay, (0, 0))
            pygame.display.flip()
            pygame.time.delay(30)

        self.screen.fill((8, 4, 4))
        # Blood drip effect
        for i in range(20):
            x = random.randint(100, WIDTH - 100)
            h = random.randint(20, 120)
            pygame.draw.line(self.screen, (random.randint(60, 100), 5, 5), (x, 0), (x, h), random.randint(1, 3))

        txt = self.titlefont.render("YOU HAVE DIED", True, (180, 30, 30))
        self.screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 60))

        # Stats
        stats = [
            f"Level {self.player.level}  -  Dungeon Level {self.current_level}  -  Wave {self.wave}",
            f"Gold collected: {self.player.gold}",
            f"Difficulty: {self.difficulty_name}",
        ]
        y = HEIGHT // 2 + 10
        for line in stats:
            st = self.subfont.render(line, True, (140, 100, 100))
            self.screen.blit(st, (WIDTH // 2 - st.get_width() // 2, y))
            y += 30

        sub = self.font.render("Press any key to quit", True, (120, 90, 90))
        self.screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, y + 20))
        pygame.display.flip()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type in (pygame.KEYDOWN, pygame.QUIT):
                    waiting = False

    # ---- Touch input handlers ----
    def _touch_to_screen(self, event) -> Tuple[float, float]:
        """Convert normalized touch coords to screen pixels."""
        return event.x * WIDTH, event.y * HEIGHT

    def _touch_hit_btn(self, sx, sy, btn_pos) -> bool:
        dx = sx - btn_pos.x
        dy = sy - btn_pos.y
        return dx * dx + dy * dy <= self.touch_btn_radius * self.touch_btn_radius * 1.5

    def _handle_touch_down(self, event):
        self.touch_mode = True
        sx, sy = self._touch_to_screen(event)
        joy_r = 60
        # Check joystick area (left side)
        dx = sx - self.touch_joy_center.x
        dy = sy - self.touch_joy_center.y
        if dx * dx + dy * dy <= (joy_r + 40) ** 2:
            self.touch_joy_active = True
            self.touch_joy_id = event.finger_id
            self.touch_joy_pos = Vec(sx, sy)
            return
        # Check buttons (right side)
        if self._touch_hit_btn(sx, sy, self.touch_btn_attack):
            self.touch_attack_active = True
        elif self._touch_hit_btn(sx, sy, self.touch_btn_power):
            self.touch_power_active = True
        elif self._touch_hit_btn(sx, sy, self.touch_btn_dash):
            self.touch_dash_active = True
        elif self._touch_hit_btn(sx, sy, self.touch_btn_hppot):
            self.touch_hppot_active = True
        elif self._touch_hit_btn(sx, sy, self.touch_btn_mpot):
            self.touch_mpot_active = True

    def _handle_touch_up(self, event):
        if event.finger_id == self.touch_joy_id:
            self.touch_joy_active = False
            self.touch_joy_id = None
            self.touch_move = Vec(0, 0)
            self.touch_joy_pos = self.touch_joy_center.copy()
        # release all buttons on any finger up
        sx, sy = self._touch_to_screen(event)
        self.touch_attack_active = False
        self.touch_power_active = False
        self.touch_dash_active = False
        self.touch_hppot_active = False
        self.touch_mpot_active = False

    def _handle_touch_move(self, event):
        if event.finger_id == self.touch_joy_id and self.touch_joy_active:
            sx, sy = self._touch_to_screen(event)
            self.touch_joy_pos = Vec(sx, sy)
            diff = self.touch_joy_pos - self.touch_joy_center
            joy_r = 60
            if diff.length() > joy_r:
                diff = diff.normalize() * joy_r
                self.touch_joy_pos = self.touch_joy_center + diff
            if diff.length() > 8:  # dead zone
                self.touch_move = diff.normalize()
            else:
                self.touch_move = Vec(0, 0)

    def _get_auto_aim_dir(self) -> Vec:
        """Auto-aim at nearest visible enemy for touch controls."""
        nearest = None
        best_dist = float('inf')
        for e in self.enemies:
            if not e.alive:
                continue
            d = (e.pos - self.player.pos).length()
            if d < best_dist and d < 500:
                best_dist = d
                nearest = e
        if nearest:
            aim = nearest.pos - self.player.pos
            if aim.length_squared() > 0:
                return aim.normalize()
        # default: aim in movement direction or right
        if self.player.vel.length_squared() > 0:
            return self.player.vel.normalize()
        return Vec(1, 0)

    def _draw_touch_controls(self, s):
        """Draw virtual joystick and buttons for mobile."""
        if not self.touch_mode:
            return
        # Virtual joystick
        jc = self.touch_joy_center
        jr = 60
        # outer ring
        joy_surf = pygame.Surface((jr * 2 + 20, jr * 2 + 20), pygame.SRCALPHA)
        pygame.draw.circle(joy_surf, (255, 255, 255, 35), (jr + 10, jr + 10), jr, 2)
        s.blit(joy_surf, (int(jc.x - jr - 10), int(jc.y - jr - 10)))
        # thumb position
        thumb = self.touch_joy_pos
        thumb_surf = pygame.Surface((50, 50), pygame.SRCALPHA)
        pygame.draw.circle(thumb_surf, (255, 255, 255, 60), (25, 25), 22)
        pygame.draw.circle(thumb_surf, (255, 255, 255, 100), (25, 25), 18)
        s.blit(thumb_surf, (int(thumb.x - 25), int(thumb.y - 25)))

        # Buttons
        br = self.touch_btn_radius
        buttons = [
            (self.touch_btn_attack, self.touch_attack_active, (140, 200, 255), "ATK"),
            (self.touch_btn_power, self.touch_power_active, (160, 120, 255), "PWR"),
            (self.touch_btn_dash, self.touch_dash_active, (100, 200, 140), "DSH"),
            (self.touch_btn_hppot, self.touch_hppot_active, (220, 80, 80), "HP"),
            (self.touch_btn_mpot, self.touch_mpot_active, (80, 120, 220), "MP"),
        ]
        for pos, active, color, label in buttons:
            btn_surf = pygame.Surface((br * 2 + 4, br * 2 + 4), pygame.SRCALPHA)
            fill_alpha = 100 if active else 40
            pygame.draw.circle(btn_surf, (color[0], color[1], color[2], fill_alpha),
                               (br + 2, br + 2), br)
            pygame.draw.circle(btn_surf, (color[0], color[1], color[2], 120),
                               (br + 2, br + 2), br, 2)
            s.blit(btn_surf, (int(pos.x - br - 2), int(pos.y - br - 2)))
            lbl = self.font.render(label, True, (*color,))
            s.blit(lbl, (int(pos.x - lbl.get_width() // 2), int(pos.y - lbl.get_height() // 2)))

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
                        self.running = False
                    if event.key == pygame.K_p:
                        self.paused = not self.paused
                    if event.key == pygame.K_F1:
                        self._help_overlay()
                # Touch / finger events
                elif event.type == pygame.FINGERDOWN:
                    self._handle_touch_down(event)
                elif event.type == pygame.FINGERUP:
                    self._handle_touch_up(event)
                elif event.type == pygame.FINGERMOTION:
                    self._handle_touch_move(event)
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
            self.update_corpses(dt)
            self.update_blood_stains(dt)
            self.update_screen_shake(dt)
            if self.player.hp <= 0:
                self.game_over()
                return
            self.draw()


if __name__ == "__main__":
    try:
        Game().run()
    except Exception as e:
        print("Fatal error:", e)
        import traceback
        traceback.print_exc()
        pygame.quit()
        sys.exit(1)
