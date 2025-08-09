
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

# --- NEW: Elite (sub-boss) packs ---
ELITE_PACK_CHANCE = 0.35         # chance a spawn cycle creates a pack
PACK_SIZE_RANGE = (3, 6)         # minions per elite
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

# ---------- Helpers ----------
Vec = pygame.math.Vector2

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

@dataclass
class Projectile:
    pos: Vec
    vel: Vec
    dmg: int
    ttl: float
    radius: int
    pierce: int = 1
    hostile: bool = False  # true for enemy projectiles

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
    # dash
    dash_cd: float = 0.0
    dash_timer: float = 0.0
    iframes: float = 0.0

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
    # NEW: dynamic aura-modified multipliers (reset each frame)
    mult_speed: float = 1.0
    mult_damage: float = 1.0
    mult_taken: float = 1.0
    # NEW: basic ranged minion support
    shot_cd: float = 0.0

    def roll_damage(self) -> int:
        base = random.randint(self.dmg_min, self.dmg_max)
        return int(base * self.mult_damage)

@dataclass
class Elite(Enemy):
    aura: str = "haste"   # haste/frenzy/guardian
    aura_radius: int = AURA_RADIUS

@dataclass
class Boss(Enemy):
    shot_cd: float = 1.0

class Dungeon:
    def __init__(self, level: int = 1):
        self.level = level
        self.tiles = [[WALL for _ in range(MAP_H)] for _ in range(MAP_W)]
        self.seen = [[False for _ in range(MAP_H)] for _ in range(MAP_W)]
        self.rooms: List[pygame.Rect] = []
        self.scenery: List[Tuple[int,int,str]] = []  # (tx,ty,type)
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
        pygame.display.set_caption("ARPG — Exploration Build (Elites)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(FONT_NAME, 18)
        self.bigfont = pygame.font.SysFont(FONT_NAME, 28, bold=True)
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
        # NEW: kind 3 = spitter ranged minion
        kind = kind_override if kind_override is not None else random.choices([0,1,2,3],[0.35,0.25,0.25,0.15])[0]
        e = Enemy(pos=pos, vel=Vec(0,0), radius=14, hp=hp, max_hp=hp, dmg_min=dmg_min, dmg_max=dmg_max, speed=speed, kind=kind)
        if kind == 3:
            e.shot_cd = random.uniform(1.4, 2.2)
        self.enemies.append(e)

    # NEW: spawn an elite pack (sub-boss + minions)
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
        # ring of minions
        count = random.randint(*PACK_SIZE_RANGE)
        ang0 = random.random()*math.tau
        for i in range(count):
            r = random.randint(46, 88)
            ang = ang0 + i*(math.tau/count)
            mpos = pos + Vec(math.cos(ang)*r, math.sin(ang)*r)
            kind = random.choices([0,1,2,3],[0.4,0.25,0.2,0.15])[0]
            self.spawn_enemy(near_player=False, kind_override=kind)
            self.enemies[-1].pos = mpos

    def spawn_boss(self):
        # Boss in level 3 (once)
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
        if move.length_squared() > 0:
            move = move.normalize()
        self.player.vel = move * PLAYER_SPEED

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

        if keys[pygame.K_q] and self.player.potions_hp > 0 and self.player.hp < PLAYER_HP:
            self.player.hp = min(PLAYER_HP + 10*self.player.level, self.player.hp + POTION_HEAL)
            self.player.potions_hp -= 1
        if keys[pygame.K_e] and self.player.potions_mana > 0 and self.player.mana < PLAYER_MANA:
            self.player.mana = min(PLAYER_MANA + 8*self.player.level, self.player.mana + POTION_MANA)
            self.player.potions_mana -= 1

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
        if p.dmg_timer > 0:
            p.dmg_timer -= dt
            if p.dmg_timer <= 0:
                p.dmg_mult = 1.0
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
            desired = (p.pos - e.pos)
            dist = desired.length() or 0.0001
            desired = desired / dist
            jitter = Vec(random.uniform(-0.2,0.2), random.uniform(-0.2,0.2))
            acc = (desired + jitter).normalize() * (e.speed * e.mult_speed)
            e.vel += (acc - e.vel) * 0.1
            e.pos += e.vel * dt
            if self._circle_collides(e.pos, e.radius):
                e.vel *= -0.4
                e.pos += e.vel * dt

            # NEW: spitter minion ranged attack
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
                    pr.ttl = 0
                    continue
            else:
                # hit enemies
                for e in self.enemies:
                    if not e.alive: continue
                    if (e.pos - pr.pos).length() < e.radius + pr.radius:
                        # apply "taken" multiplier (guardian aura reduces damage)
                        damage = max(1, int(pr.dmg * e.mult_taken))
                        e.hp -= damage
                        e.knockback = 200
                        e.vel += (e.pos - pr.pos).normalize() * 300
                        pr.pierce -= 1
                        if pr.pierce <= 0:
                            pr.ttl = 0
                            break
        self.projectiles = [pr for pr in self.projectiles if pr.ttl > 0]

    def update_loot(self, dt: float):
        for l in self.loots:
            l.ttl -= dt
            if (l.pos - self.player.pos).length() < 24:
                if l.gold:
                    self.player.gold += l.gold
                if l.potion_hp:
                    self.player.potions_hp += 1
                if l.potion_mana:
                    self.player.potions_mana += 1
                if l.weapon:
                    self.player.weapon = l.weapon
                if l.dmg_boost:
                    self.player.dmg_mult = DMG_BOOST_MULT
                    self.player.dmg_timer = DMG_BOOST_TIME
                if l.shield_boost:
                    self.player.shield = max(self.player.shield, SHIELD_POINTS)
                l.ttl = 0
        self.loots = [l for l in self.loots if l.ttl > 0]

    def on_enemy_dead(self, e: Enemy):
        self.player.xp += 6 + self.wave
        while self.player.xp >= self.player.xp_to_next:
            self.player.xp -= self.player.xp_to_next
            self.player.level += 1
            self.player.xp_to_next = int(self.player.xp_to_next * 1.35)
            self.player.hp = min(PLAYER_HP + 10*self.player.level, self.player.hp + 30)
            self.player.mana = min(PLAYER_MANA + 8*self.player.level, self.player.mana + 20)
        drops: List[Loot] = []
        # base drops
        if random.random() < 0.9:
            drops.append(Loot(pos=e.pos.copy(), gold=random.randint(*GOLD_DROP)))
        if random.random() < POTION_DROP_CHANCE:
            potion = random.choice(["hp","mana"])
            drops.append(Loot(pos=e.pos.copy(), potion_hp=(potion=="hp"), potion_mana=(potion=="mana")))
        if random.random() < LOOT_DROP_CHANCE:
            drops.append(Loot(pos=e.pos.copy(), weapon=Weapon("Find", 10, 16, 2.0, True)))
        if random.random() < DMG_PICKUP_DROP_CHANCE:
            drops.append(Loot(pos=e.pos.copy(), dmg_boost=True))
        if random.random() < SHIELD_PICKUP_DROP_CHANCE:
            drops.append(Loot(pos=e.pos.copy(), shield_boost=True))

        # NEW: elites drop extra goodies
        if isinstance(e, Elite):
            drops.append(Loot(pos=e.pos.copy(), gold=random.randint(15, 35)))
            # guaranteed buff
            if random.random() < 0.5:
                drops.append(Loot(pos=e.pos.copy(), dmg_boost=True))
            else:
                drops.append(Loot(pos=e.pos.copy(), shield_boost=True))

        self.loots.extend(drops)

    # ----- Waves / Exploration spawning -----
    def update_spawning(self, dt: float):
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            # try elite pack spawn
            did_pack = False
            if random.random() < ELITE_PACK_CHANCE and len(self.enemies) < MAX_ACTIVE_ENEMIES:
                self.spawn_elite_pack()
                did_pack = True
            # regular adds
            to_spawn = min(2, MAX_ACTIVE_ENEMIES - len(self.enemies))
            if not did_pack:
                for _ in range(max(0, to_spawn)):
                    self.spawn_enemy(near_player=True)
            else:
                # after a pack, maybe one extra add
                if random.random() < 0.5 and len(self.enemies) < MAX_ACTIVE_ENEMIES:
                    self.spawn_enemy(near_player=True)
            if random.random() < PICKUP_SPAWN_CHANCE:
                self.spawn_pickup_near_player()
            self.wave += 1
            self.spawn_timer = SPAWN_INTERVAL
            # Try spawning a boss at level 3
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
        self.wave = 1
        self.spawn_timer = SPAWN_INTERVAL
        self.dungeon.mark_seen_radius(self.player.pos)
        self.boss_spawned = False

    # ----- Render -----
    def draw(self):
        s = self.screen
        s.fill((8, 8, 10))
        # tiles in view
        start_tx = max(0, self.cam_x // TILE)
        end_tx = min(MAP_W-1, (self.cam_x + WIDTH) // TILE + 1)
        start_ty = max(0, self.cam_y // TILE)
        end_ty = min(MAP_H-1, (self.cam_y + HEIGHT) // TILE + 1)
        for tx in range(start_tx, end_tx+1):
            for ty in range(start_ty, end_ty+1):
                px = tx*TILE - self.cam_x
                py = ty*TILE - self.cam_y
                seen = self.dungeon.seen[tx][ty]
                if self.dungeon.tiles[tx][ty] == WALL:
                    col = (46,46,58) if seen else (18,18,22)
                else:
                    col = (24,24,28) if seen else (12,12,14)
                pygame.draw.rect(s, col, (px, py, TILE, TILE))
        # scenery
        for (tx,ty,t) in self.dungeon.scenery:
            if not self._tile_in_view(tx,ty):
                continue
            px = tx*TILE - self.cam_x
            py = ty*TILE - self.cam_y
            if t=='pillar':
                pygame.draw.rect(s, (70,70,90), (px+6,py+6,TILE-12,TILE-12), border_radius=6)
            else:
                pygame.draw.rect(s, (90,72,48), (px+4,py+4,TILE-8,TILE-8))
                pygame.draw.line(s, (120,96,64), (px+4,py+4), (px+TILE-4,py+TILE-4), 2)
                pygame.draw.line(s, (120,96,64), (px+TILE-4,py+4), (px+4,py+TILE-4), 2)
        # stairs
        if self.dungeon.stairs_tx is not None and self._tile_in_view(self.dungeon.stairs_tx,self.dungeon.stairs_ty):
            px = self.dungeon.stairs_tx*TILE - self.cam_x
            py = self.dungeon.stairs_ty*TILE - self.cam_y
            pygame.draw.rect(s, (200, 200, 90), (px+8, py+8, TILE-16, TILE-16), border_radius=4)
            pygame.draw.rect(s, (120, 120, 40), (px+10, py+10, TILE-20, TILE-20), border_radius=4)
        # projectiles
        for pr in self.projectiles:
            col = (180,220,255) if not pr.hostile else (255,100,110)
            pygame.draw.circle(s, col, (int(pr.pos.x - self.cam_x), int(pr.pos.y - self.cam_y)), pr.radius)
        # player sprite
        self._draw_player()
        # enemies
        for e in self.enemies:
            self._draw_enemy(e)
        # loot
        for l in self.loots:
            vx, vy = int(l.pos.x - self.cam_x), int(l.pos.y - self.cam_y)
            if l.weapon:
                pygame.draw.rect(s, (255, 225, 120), (vx-6, vy-6, 12, 12))
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

    def _draw_player(self):
        s = self.screen
        px, py = int(self.player.pos.x - self.cam_x), int(self.player.pos.y - self.cam_y)
        # body
        pygame.draw.circle(s, (220, 225, 235), (px, py-8), 6)  # head
        pygame.draw.rect(s, (70,100,160), (px-8, py-6, 16, 18), border_radius=4)  # torso
        # arm toward mouse
        mx, my = pygame.mouse.get_pos()
        ang = math.atan2(my - (py), mx - (px))
        hand = (px + int(math.cos(ang)*12), py + int(math.sin(ang)*12))
        pygame.draw.circle(s, (220,220,220), hand, 3)
        # NEW: tiny feet for motion cue
        pygame.draw.rect(s, (60,80,120), (px-8, py+10, 16, 4), border_radius=2)
        # shield aura
        if self.player.shield > 0:
            pygame.draw.circle(s, (80,200,250), (px, py), self.player.radius+6, 1)
        if self.player.dmg_timer > 0:
            pygame.draw.circle(s, (250,160,40), (px, py), self.player.radius+2, 1)

    def _draw_enemy(self, e: Enemy):
        s = self.screen
        ex, ey = int(e.pos.x - self.cam_x), int(e.pos.y - self.cam_y)
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
            pygame.draw.circle(s, aura_col, (ex,ey), e.radius+6, 2)  # aura ring
            pygame.draw.polygon(s, (240,200,100), [(ex-10,ey-14),(ex-4,ey-22),(ex,ey-14),(ex+4,ey-22),(ex+10,ey-14)])  # small crown

        pygame.draw.circle(s, col, (ex, ey), e.radius)

        # kind-specific features
        if isinstance(e, Boss):
            # crown
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
        # simple overview of seen tiles
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
        bar(16, 12, 260, 18, self.player.hp / (PLAYER_HP + 10*self.player.level))
        s.blit(self.font.render(f"HP {self.player.hp}", True, (220,220,220)), (20, 12))
        # Mana
        bar(16, 36, 260, 18, self.player.mana / (PLAYER_MANA + 8*self.player.level), fg=(120,160,220))
        s.blit(self.font.render(f"Mana {self.player.mana}", True, (220,220,220)), (20, 36))
        # XP/Level
        s.blit(self.font.render(f"Lvl {self.player.level}  Dlvl {self.current_level}/{LEVELS}  {self.difficulty_name}", True, (255,255,255)), (16, 64))
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
        # gold/pots
        s.blit(self.font.render(f"Gold {self.player.gold}", True, (230,210,120)), (16, 104))
        s.blit(self.font.render(f"HP Pots [{self.player.potions_hp}]  Mana Pots [{self.player.potions_mana}]", True, (200,200,200)), (16, 124))
        # wave timer / pause hint
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
            self.update_loot(dt)
            self.update_spawning(dt)
            if self.player.hp <= 0:
                self.game_over(); return
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
            "Elites lead packs with auras: Haste/Frenzy/Guardian.",
            "Goal: explore, find stairs, reach Level 3, defeat Boss.",
        ]
        y = 120
        for ln in lines:
            t = self.bigfont.render(ln, True, (230,230,240))
            s.blit(t, (WIDTH//2 - t.get_width()//2, y))
            y += 40
        pygame.display.flip()
        waiting = True
        while waiting:
            for e in pygame.event.get():
                if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.QUIT):
                    waiting = False

    def game_over(self):
        s = self.screen
        txt = self.bigfont.render("You Died", True, (230, 100, 100))
        sub = self.font.render("Press any key to quit", True, (220,220,220))
        s.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 40))
        s.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 4))
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
