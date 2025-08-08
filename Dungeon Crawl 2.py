"""
Diablo-like ARPG — Exploration Build (Python + Pygame)
------------------------------------------------------
New features you asked for:
- **Enemy HP color**: green (healthy) → yellow (wounded) → red (near death)
- **Pickups**: temporary **Damage Boost** and **Shield**
- **Wider halls**, light **scenery** (pillars/crates), and **3 dungeon levels** with stairs
- **Sprites**: simple person-like player and creature-like enemies (shapes/eyes/horns)
- Controls: WASD move • LMB basic shot • RMB power shot (uses mana) • Q/E potions • Esc quit

Run:
  pip install pygame
  python arpg_explore.py

Notes:
- Still single-file and primitive art; easy to swap in sprite images later.
"""
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

POTION_HEAL = 50
POTION_MANA = 40

# Enemy balance (calmer pacing)
ENEMY_BASE_HP = 40
ENEMY_BASE_DMG = (4, 8)
ENEMY_SPEED = 110
SPAWN_INTERVAL = 6.0
WAVE_SCALE = 1.10
MAX_ACTIVE_ENEMIES = 6

# Pickups
DMG_BOOST_MULT = 1.6
DMG_BOOST_TIME = 8.0
SHIELD_POINTS = 70
PICKUP_SPAWN_CHANCE = 0.25  # per wave spawn tick, one near player

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
    attack_speed: float  # attacks per second
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

@dataclass
class Enemy(Entity):
    hp: int = ENEMY_BASE_HP
    max_hp: int = ENEMY_BASE_HP
    dmg_min: int = ENEMY_BASE_DMG[0]
    dmg_max: int = ENEMY_BASE_DMG[1]
    speed: float = ENEMY_SPEED
    knockback: float = 0.0
    alive: bool = True
    kind: int = 0  # for variety of creature drawing

    def roll_damage(self) -> int:
        return random.randint(self.dmg_min, self.dmg_max)

class Dungeon:
    def __init__(self, level: int = 1):
        self.level = level
        self.tiles = [[WALL for _ in range(MAP_H)] for _ in range(MAP_W)]
        self.seen = [[False for _ in range(MAP_H)] for _ in range(MAP_W)]
        self.rooms: List[pygame.Rect] = []
        self.scenery: List[Tuple[int,int,str]] = []  # (tx,ty,type) type in {pillar,crate}
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
            # Add a bit of scenery to this room (solid pillars)
            for _ in range(rng.randint(0, 2)):
                tx = rng.randint(new.left+1, new.right-2)
                ty = rng.randint(new.top+1, new.bottom-2)
                # make sure not blocking single-tile corridors by keeping rooms larger
                self.tiles[tx][ty] = WALL
                self.scenery.append((tx, ty, 'pillar' if rng.random()<0.6 else 'crate'))
        # Borders
        for x in range(MAP_W):
            self.tiles[x][0] = WALL
            self.tiles[x][MAP_H-1] = WALL
        for y in range(MAP_H):
            self.tiles[0][y] = WALL
            self.tiles[MAP_W-1][y] = WALL
        # Stairs at the last room center
        if self.rooms:
            sx, sy = self.center(self.rooms[-1])
            self.stairs_tx, self.stairs_ty = sx, sy
            self.tiles[sx][sy] = FLOOR

    def carve_room(self, rect: pygame.Rect):
        for x in range(rect.left, rect.right):
            for y in range(rect.top, rect.bottom):
                self.tiles[x][y] = FLOOR

    def carve_tunnel(self, x1, y1, x2, y2):
        # L-shaped with width 3
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
        pygame.display.set_caption("ARPG — Exploration Build")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(FONT_NAME, 18)
        self.bigfont = pygame.font.SysFont(FONT_NAME, 28, bold=True)
        self.current_level = 1
        self.dungeon = Dungeon(level=self.current_level)
        # Start in the first room
        rx, ry = self.dungeon.center(self.dungeon.rooms[0]) if self.dungeon.rooms else (MAP_W//2, MAP_H//2)
        self.player = Player(pos=Vec(rx*TILE+TILE/2, ry*TILE+TILE/2), vel=Vec(0,0), radius=14)
        self.enemies: List[Enemy] = []
        self.projectiles: List[Projectile] = []
        self.loots: List[Loot] = []
        self.spawn_timer = SPAWN_INTERVAL
        self.wave = 1
        self.running = True
        # Camera
        self.cam_x = 0
        self.cam_y = 0
        self.dungeon.mark_seen_radius(self.player.pos)

    # ----- Spawning -----
    def spawn_enemy(self, near_player: bool = True):
        if len(self.enemies) >= MAX_ACTIVE_ENEMIES:
            return
        tries = 0
        while tries < 200:
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
                    break
            tries += 1
        else:
            pos = self.player.pos + Vec(random.randint(-240,240), random.randint(-240,240))
        scale = (WAVE_SCALE ** (self.wave-1)) * (1.0 + 0.1*(self.current_level-1))
        hp = int(ENEMY_BASE_HP * scale)
        dmg_min = int(ENEMY_BASE_DMG[0] * scale)
        dmg_max = int(ENEMY_BASE_DMG[1] * scale)
        speed = ENEMY_SPEED * (0.95 + 0.1*random.random())
        kind = random.randint(0,2)
        e = Enemy(pos=pos, vel=Vec(0,0), radius=14, hp=hp, max_hp=hp, dmg_min=dmg_min, dmg_max=dmg_max, speed=speed, kind=kind)
        self.enemies.append(e)

    def spawn_pickup_near_player(self):
        # Spawn either damage boost or shield near player
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
        # buffs
        if p.dmg_timer > 0:
            p.dmg_timer -= dt
            if p.dmg_timer <= 0:
                p.dmg_mult = 1.0
        # attempt axis-aligned movement with tile collision
        new_pos = p.pos + p.vel * dt
        # X axis
        test = Vec(new_pos.x, p.pos.y)
        if not self.dungeon.is_solid_at_px(test) and not self._circle_collides(test, p.radius):
            p.pos.x = test.x
        # Y axis
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
        for e in self.enemies:
            if not e.alive:
                continue
            desired = (p.pos - e.pos)
            dist = desired.length() or 0.0001
            desired = desired / dist
            jitter = Vec(random.uniform(-0.2,0.2), random.uniform(-0.2,0.2))
            acc = (desired + jitter).normalize() * e.speed
            e.vel += (acc - e.vel) * 0.1
            e.pos += e.vel * dt
            if self._circle_collides(e.pos, e.radius):
                e.vel *= -0.4
                e.pos += e.vel * dt
            # Touch damage
            if (e.pos - p.pos).length() < e.radius + p.radius:
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
        self.enemies = [e for e in self.enemies if e.alive or random.random() > 0.01]

    def update_projectiles(self, dt: float):
        for pr in self.projectiles:
            pr.ttl -= dt
            pr.pos += pr.vel * dt
            if self.dungeon.is_solid_at_px(pr.pos):
                pr.ttl = 0
                continue
            for e in self.enemies:
                if not e.alive: continue
                if (e.pos - pr.pos).length() < e.radius + pr.radius:
                    e.hp -= pr.dmg
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
        self.loots.extend(drops)

    # ----- Waves / Exploration spawning -----
    def update_spawning(self, dt: float):
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            to_spawn = min(2, MAX_ACTIVE_ENEMIES - len(self.enemies))
            for _ in range(max(0, to_spawn)):
                self.spawn_enemy(near_player=True)
            if random.random() < PICKUP_SPAWN_CHANCE:
                self.spawn_pickup_near_player()
            self.wave += 1
            self.spawn_timer = SPAWN_INTERVAL

    # ----- Level management -----
    def next_level(self):
        if self.current_level >= LEVELS:
            # loop back to 1, keep stats
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
            else:  # crate
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
            pygame.draw.circle(s, (180,220,255), (int(pr.pos.x - self.cam_x), int(pr.pos.y - self.cam_y)), pr.radius)
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
        # simple facing arm (towards mouse)
        mx, my = pygame.mouse.get_pos()
        ang = math.atan2(my - (py), mx - (px))
        hand = (px + int(math.cos(ang)*12), py + int(math.sin(ang)*12))
        pygame.draw.circle(s, (220,220,220), hand, 3)
        # shield aura if active
        if self.player.shield > 0:
            pygame.draw.circle(s, (80,200,250), (px, py), self.player.radius+6, 1)
        # damage buff glow
        if self.player.dmg_timer > 0:
            pygame.draw.circle(s, (250,160,40), (px, py), self.player.radius+2, 1)

    def _draw_enemy(self, e: Enemy):
        s = self.screen
        ex, ey = int(e.pos.x - self.cam_x), int(e.pos.y - self.cam_y)
        # HP color
        ratio = max(0.0, min(1.0, e.hp / max(1, e.max_hp)))
        if ratio > 0.66:
            col = (90, 200, 90)   # green
        elif ratio > 0.33:
            col = (240, 210, 80)  # yellow
        else:
            col = (220, 80, 80)   # red
        # creature variants
        pygame.draw.circle(s, col, (ex, ey), e.radius)
        if e.kind == 0:
            # eyes
            pygame.draw.circle(s, (0,0,0), (ex-4, ey-2), 2)
            pygame.draw.circle(s, (0,0,0), (ex+4, ey-2), 2)
        elif e.kind == 1:
            # horns
            pygame.draw.polygon(s, (180,180,200), [(ex-6,ey-8),(ex-2,ey-2),(ex-10,ey-2)])
            pygame.draw.polygon(s, (180,180,200), [(ex+6,ey-8),(ex+2,ey-2),(ex+10,ey-2)])
        else:
            # mandibles
            pygame.draw.line(s, (0,0,0), (ex-4,ey+4), (ex-8,ey+10), 2)
            pygame.draw.line(s, (0,0,0), (ex+4,ey+4), (ex+8,ey+10), 2)

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
        s.blit(self.font.render(f"Lvl {self.player.level}  Dlvl {self.current_level}/{LEVELS}", True, (255,255,255)), (16, 64))
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
        # wave timer
        s.blit(self.font.render(f"Wave {self.wave} in {self.spawn_timer:0.1f}s", True, (180,180,200)), (WIDTH-280, 12))

    # ----- Main Loop -----
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
            self.handle_input(dt)
            self.update_player(dt)
            self.update_enemies(dt)
            self.update_projectiles(dt)
            self.update_loot(dt)
            self.update_spawning(dt)
            if self.player.hp <= 0:
                self.game_over(); return
            self.draw()

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
