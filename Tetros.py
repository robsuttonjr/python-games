#!/usr/bin/env python3
# Deluxe "Tetros" - Pygame
# Enhancements in this build:
# - 180° rotate (press A) so pieces can face all four orientations quickly
# - Flash animation on line clears before collapse/removal
#
# Controls:
#   Left/Right: move | Down: soft drop | Space: hard drop
#   Z: rotate CCW | X or Up: rotate CW | A: rotate 180°
#   C: Hold | P: Pause | R: Restart | G: Toggle Ghost | F: Toggle grid

import random
import sys
from dataclasses import dataclass, field
from typing import List
import pygame

# --------------------------- Config ---------------------------
WIDTH, HEIGHT = 900, 720
FPS = 60
COLS, ROWS = 10, 22          # 2 hidden rows at top
VISIBLE_ROWS = 20
TILE = 30
PLAY_W = COLS * TILE
PLAY_H = VISIBLE_ROWS * TILE
PLAY_X = (WIDTH - PLAY_W) // 2 - 120
PLAY_Y = (HEIGHT - PLAY_H) // 2
PANEL_X = PLAY_X + PLAY_W + 24
PANEL_Y = PLAY_Y

BG = (18, 18, 22)
PANEL_BG = (28, 28, 36)
GRID_COLOR = (50, 50, 64)

COLORS = {
    "I": (0, 240, 240),
    "J": (0, 0, 240),
    "L": (240, 160, 0),
    "O": (240, 240, 0),
    "S": (0, 240, 0),
    "T": (160, 0, 240),
    "Z": (240, 0, 0),
}

# Rotation states (we keep 4 indices even when 2 are duplicates so rotation modulo 4 works)
PIECES = {
    "I": [
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
    ],
    "J": [
        [(0, 1), (0, 2), (1, 2), (2, 2)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "L": [
        [(2, 1), (0, 2), (1, 2), (2, 2)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
    "O": [
        [(1, 1), (2, 1), (1, 2), (2, 2)],
        [(1, 1), (2, 1), (1, 2), (2, 2)],
        [(1, 1), (2, 1), (1, 2), (2, 2)],
        [(1, 1), (2, 1), (1, 2), (2, 2)],
    ],
    "S": [
        [(1, 1), (2, 1), (0, 2), (1, 2)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
        [(1, 1), (2, 1), (0, 2), (1, 2)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
    ],
    "T": [
        [(1, 1), (0, 2), (1, 2), (2, 2)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "Z": [
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
    ],
}

SCORES = {1: 40, 2: 100, 3: 300, 4: 1200}
MOVE_REPEAT_DELAY = 150
MOVE_REPEAT_RATE = 35
SOFT_DROP_RATE = 30
GRAVITY_BY_LEVEL = [0.8, 0.72, 0.63, 0.55, 0.47, 0.38, 0.3, 0.22, 0.14, 0.1]
GRAVITY_MIN = 0.05

# Clear animation
CLEAR_FLASH_MS = 80          # duration per flash
CLEAR_FLASH_CYCLES = 6       # how many flashes before collapse

# --------------------------- Data ---------------------------
@dataclass
class Piece:
    kind: str
    rot: int = 0
    x: int = 3
    y: int = 0
    locked: bool = False
    @property
    def tiles(self): return PIECES[self.kind][self.rot]
    def cells(self):
        for (cx, cy) in self.tiles:
            yield self.x + cx, self.y + cy

@dataclass
class Bag7:
    bag: List[str] = field(default_factory=list)
    def next(self):
        if not self.bag:
            self.bag = list("IJLOSTZ")
            random.shuffle(self.bag)
        return self.bag.pop()

# --------------------------- Game ---------------------------
class Tetros:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Deluxe Tetros")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 20)
        self.big_font = pygame.font.SysFont("consolas", 36, bold=True)
        self.reset()

    def reset(self):
        self.board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.bag = Bag7()
        self.hold = None
        self.hold_used = False
        self.queue: List[str] = [self.bag.next() for _ in range(5)]
        self.cur: Piece = self.spawn_piece()
        self.drop_timer = 0.0
        self.gravity = GRAVITY_BY_LEVEL[0]
        self.level = 0
        self.lines = 0
        self.score = 0
        self.combo = -1
        self.b2b = False
        self.game_over = False
        self.paused = False
        self.show_ghost = True
        self.show_grid = True

        # Input repeat
        self.left_held = False; self.right_held = False
        self.left_timer = 0; self.right_timer = 0
        self.down_held = False; self.down_timer = 0

        # Clearing animation state
        self.clearing_rows: List[int] = []
        self.clear_flash_elapsed = 0
        self.clear_flash_count = 0
        self.flash_on = False
        self.pending_spawn = False  # spawn next after animation completes
        self.pending_cleared_count = 0

    def spawn_piece(self):
        k = self.queue.pop(0)
        self.queue.append(self.bag.next())
        p = Piece(kind=k, rot=0, x=3, y=0)
        if not self.valid(p):
            self.game_over = True
        return p

    # --------------------------- Board Helpers ---------------------------
    def valid(self, p: Piece):
        for (x, y) in p.cells():
            if x < 0 or x >= COLS or y < 0 or y >= ROWS:
                return False
            if self.board[y][x] is not None:
                return False
        return True

    def lock_piece(self, p: Piece):
        for (x, y) in p.cells():
            if 0 <= y < ROWS:
                self.board[y][x] = p.kind
        self.cur.locked = True

    def get_full_lines(self):
        full = []
        for y in range(ROWS):
            if all(self.board[y][x] is not None for x in range(COLS)):
                full.append(y)
        return full

    def start_clear_animation(self, rows: List[int]):
        self.clearing_rows = rows[:]
        self.clear_flash_elapsed = 0
        self.clear_flash_count = 0
        self.flash_on = True
        self.pending_spawn = True

    def finalize_clear(self):
        # Remove full rows
        rows_set = set(self.clearing_rows)
        new_board = [row for i, row in enumerate(self.board) if i not in rows_set]
        cleared = len(self.clearing_rows)
        while len(new_board) < ROWS:
            new_board.insert(0, [None for _ in range(COLS)])
        self.board = new_board
        self.clearing_rows = []
        self.flash_on = False
        return cleared

    def rotate(self, cw=True, half=False):
        if self.cur.kind == "O" and not half:
            return
        old_rot = self.cur.rot
        if half:
            self.cur.rot = (self.cur.rot + 2) % 4
            kicks = [(0, 0), (-1, 0), (1, 0), (0, -1), (-2, 0), (2, 0)]
        else:
            self.cur.rot = (self.cur.rot + (1 if cw else -1)) % 4
            kicks = [(0, 0), (-1, 0), (1, 0), (0, -1), (-2, 0), (2, 0)]
        for dx, dy in kicks:
            test = Piece(self.cur.kind, self.cur.rot, self.cur.x + dx, self.cur.y + dy)
            if self.valid(test):
                self.cur = test
                return
        self.cur.rot = old_rot  # revert if all kicks fail

    def move(self, dx, dy):
        test = Piece(self.cur.kind, self.cur.rot, self.cur.x + dx, self.cur.y + dy)
        if self.valid(test):
            self.cur = test
            return True
        return False

    def hard_drop(self):
        if self.clearing_rows:
            return
        dist = 0
        while self.move(0, 1):
            dist += 1
        self.lock_piece(self.cur)
        rows = self.get_full_lines()
        if rows:
            # start flashing, scoring later after collapse
            self.start_clear_animation(rows)
            self.pending_cleared_count = len(rows)
            self.score += 2 * dist  # hard drop bonus now
        else:
            # no clear; score hard drop distance and spawn immediately
            self.score += 2 * dist
            self.hold_used = False
            self.cur = self.spawn_piece()

    def soft_drop_step(self):
        if not self.move(0, 1):
            self.lock_piece(self.cur)
            rows = self.get_full_lines()
            if rows:
                self.start_clear_animation(rows)
                self.pending_cleared_count = len(rows)
            else:
                self.handle_scoring(0, hard_drop=False, drop_distance=0)
                self.hold_used = False
                self.cur = self.spawn_piece()

    def hold_piece(self):
        if self.hold_used or self.clearing_rows:
            return
        self.hold_used = True
        if self.hold is None:
            self.hold = self.cur.kind
            self.cur = self.spawn_piece()
        else:
            self.hold, self.cur = self.cur.kind, Piece(self.hold, 0, 3, 0)
            if not self.valid(self.cur):
                self.game_over = True

    def ghost_drop_y(self):
        ghost = Piece(self.cur.kind, self.cur.rot, self.cur.x, self.cur.y)
        while self.valid(Piece(ghost.kind, ghost.rot, ghost.x, ghost.y + 1)):
            ghost.y += 1
        return ghost.y

    # --------------------------- Scoring & Levels ---------------------------
    def handle_scoring(self, cleared, hard_drop, drop_distance):
        if hard_drop:
            self.score += 2 * drop_distance
        if cleared > 0:
            base = SCORES.get(cleared, 0)
            gained = (self.level + 1) * base
            if cleared == 4 and self.b2b:
                gained = int(gained * 1.5)
            self.score += gained
            self.lines += cleared
            self.combo = self.combo + 1 if self.combo >= 0 else 0
            self.b2b = (cleared == 4)
            new_level = self.lines // 10
            if new_level != self.level:
                self.level = new_level
                idx = min(self.level, len(GRAVITY_BY_LEVEL)-1)
                self.gravity = max(GRAVITY_MIN, GRAVITY_BY_LEVEL[idx] - 0.02*self.level)
        else:
            self.combo = -1

    # --------------------------- Rendering ---------------------------
    def draw_cell(self, surface, x, y, color, alpha=255):
        rect = pygame.Rect(PLAY_X + x*TILE, PLAY_Y + (y- (ROWS - VISIBLE_ROWS))*TILE, TILE, TILE)
        s = pygame.Surface((TILE-1, TILE-1), pygame.SRCALPHA)
        r, g, b = color
        s.fill((int(r*0.7), int(g*0.7), int(b*0.7), alpha))
        pygame.draw.rect(s, (r, g, b, alpha), s.get_rect(), border_radius=4)
        pygame.draw.rect(s, (255, 255, 255, alpha//3), pygame.Rect(2,2,TILE-5,TILE//3), border_radius=3)
        surface.blit(s, rect.topleft)

    def draw_board(self):
        pygame.draw.rect(self.screen, PANEL_BG, (PLAY_X-8, PLAY_Y-8, PLAY_W+16, PLAY_H+16), border_radius=12)
        if self.show_grid:
            for c in range(COLS+1):
                x = PLAY_X + c*TILE
                pygame.draw.line(self.screen, GRID_COLOR, (x, PLAY_Y), (x, PLAY_Y+PLAY_H), 1)
            for r in range(VISIBLE_ROWS+1):
                y = PLAY_Y + r*TILE
                pygame.draw.line(self.screen, GRID_COLOR, (PLAY_X, y), (PLAY_X+PLAY_W, y), 1)
        # Locked tiles (apply flash if in clearing rows)
        for y in range(2, ROWS):
            for x in range(COLS):
                k = self.board[y][x]
                if not k:
                    continue
                if y in self.clearing_rows and self.flash_on:
                    # flash white
                    self.draw_cell(self.screen, x, y, (255, 255, 255))
                else:
                    self.draw_cell(self.screen, x, y, COLORS[k])

        # Ghost piece
        if self.show_ghost and not self.game_over and not self.paused and not self.clearing_rows:
            gy = self.ghost_drop_y()
            for (cx, cy) in self.cur.tiles:
                gx, gy2 = self.cur.x + cx, gy + cy
                if gy2 >= 2:
                    self.draw_cell(self.screen, gx, gy2, (220, 220, 220), alpha=70)

        # Current piece
        if not self.game_over and not self.clearing_rows:
            for (cx, cy) in self.cur.tiles:
                x, y = self.cur.x + cx, self.cur.y + cy
                if y >= 2:
                    self.draw_cell(self.screen, x, y, COLORS[self.cur.kind])

    def draw_panel(self):
        panel_w = 260
        pygame.draw.rect(self.screen, PANEL_BG, (PANEL_X-8, PANEL_Y-8, panel_w, PLAY_H+16), border_radius=12)
        def text(lbl, val, y):
            t1 = self.font.render(lbl, True, (200, 200, 210))
            t2 = self.big_font.render(str(val), True, (255, 255, 255))
            self.screen.blit(t1, (PANEL_X, y))
            self.screen.blit(t2, (PANEL_X, y+22))
        text("SCORE", self.score, PANEL_Y)
        text("LEVEL", self.level, PANEL_Y + 90)
        text("LINES", self.lines, PANEL_Y + 180)

        y = PANEL_Y + 270
        self.draw_box(PANEL_X, y, 110, 110, "HOLD")
        if self.hold:
            self.draw_mini_piece(self.hold, PANEL_X+55, y+70)

        y2 = y + 140
        self.draw_box(PANEL_X, y2, 110, 240, "NEXT")
        for i, k in enumerate(self.queue[:5]):
            self.draw_mini_piece(k, PANEL_X+55, y2 + 45 + i*44, scale=0.65)

        tip = self.font.render("Z/X: Rotate  A: 180°  C: Hold", True, (180, 180, 190))
        tip2 = self.font.render("Space: Hard drop  P: Pause  R: Restart", True, (180, 180, 190))
        self.screen.blit(tip, (PANEL_X, PANEL_Y + PLAY_H - 40))
        self.screen.blit(tip2, (PANEL_X, PANEL_Y + PLAY_H - 18))

    def draw_box(self, x, y, w, h, title):
        pygame.draw.rect(self.screen, (38, 38, 48), (x, y, w, h), border_radius=10)
        lab = self.font.render(title, True, (220, 220, 230))
        self.screen.blit(lab, (x+8, y+6))

    def draw_mini_piece(self, kind, cx, cy, scale=0.8):
        tiles = PIECES[kind][0]
        color = COLORS[kind]
        size = int(TILE * scale)
        xs = [p[0] for p in tiles]; ys = [p[1] for p in tiles]
        minx, maxx = min(xs), max(xs); miny, maxy = min(ys), max(ys)
        w = (maxx - minx + 1) * size; h = (maxy - miny + 1) * size
        ox = cx - w//2; oy = cy - h//2
        for (tx, ty) in tiles:
            rx = ox + (tx - minx) * size; ry = oy + (ty - miny) * size
            rect = pygame.Rect(rx, ry, size-2, size-2)
            pygame.draw.rect(self.screen, color, rect, border_radius=4)
            pygame.draw.rect(self.screen, (255,255,255), rect.inflate(-6, -size//2), width=0, border_radius=3)

    def draw_overlay(self, title, subtitle):
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 140))
        self.screen.blit(s, (0, 0))
        t = self.big_font.render(title, True, (255, 255, 255))
        st = self.font.render(subtitle, True, (220, 220, 230))
        self.screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2 - 40))
        self.screen.blit(st, (WIDTH//2 - st.get_width()//2, HEIGHT//2 + 10))

    # --------------------------- Game Loop ---------------------------
    def update(self, dt_ms):
        if self.game_over or self.paused:
            return

        # Handle active clear animation
        if self.clearing_rows:
            self.clear_flash_elapsed += dt_ms
            while self.clear_flash_elapsed >= CLEAR_FLASH_MS:
                self.clear_flash_elapsed -= CLEAR_FLASH_MS
                self.flash_on = not self.flash_on
                if self.flash_on:
                    self.clear_flash_count += 1
                    if self.clear_flash_count >= CLEAR_FLASH_CYCLES:
                        # finalize, score, then spawn next
                        cleared = self.finalize_clear()
                        self.handle_scoring(cleared, hard_drop=False, drop_distance=0)
                        self.hold_used = False
                        self.cur = self.spawn_piece()
                        self.clear_flash_count = 0
                        self.clear_flash_elapsed = 0
                        self.flash_on = False
                        break
            return  # don't apply gravity while flashing

        # Gravity (normal fall)
        self.drop_timer += dt_ms / 1000.0
        while self.drop_timer >= self.gravity:
            self.drop_timer -= self.gravity
            if not self.move(0, 1):
                self.lock_piece(self.cur)
                rows = self.get_full_lines()
                if rows:
                    self.start_clear_animation(rows)
                    self.pending_cleared_count = len(rows)
                else:
                    self.handle_scoring(0, hard_drop=False, drop_distance=0)
                    self.hold_used = False
                    self.cur = self.spawn_piece()
                break

        # DAS/ARR and soft drop handled in events via timers
        now = pygame.time.get_ticks()
        if self.left_held:
            if self.left_timer == 0:
                self.move(-1, 0); self.left_timer = now + MOVE_REPEAT_DELAY
            elif now >= self.left_timer:
                self.move(-1, 0); self.left_timer += MOVE_REPEAT_RATE
        if self.right_held:
            if self.right_timer == 0:
                self.move(1, 0); self.right_timer = now + MOVE_REPEAT_DELAY
            elif now >= self.right_timer:
                self.move(1, 0); self.right_timer += MOVE_REPEAT_RATE
        if self.down_held:
            if self.down_timer == 0:
                if self.move(0, 1): self.score += 1
                self.down_timer = now + SOFT_DROP_RATE
            elif now >= self.down_timer:
                if self.move(0, 1): self.score += 1
                self.down_timer += SOFT_DROP_RATE

    def handle_event(self, e):
        if e.type == pygame.QUIT:
            pygame.quit(); sys.exit(0)
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_p: self.paused = not self.paused
            if e.key == pygame.K_r: self.reset()
            if self.game_over or self.paused: return
            if e.key == pygame.K_LEFT:
                self.left_held = True; self.left_timer = 0
            elif e.key == pygame.K_RIGHT:
                self.right_held = True; self.right_timer = 0
            elif e.key == pygame.K_DOWN:
                self.down_held = True; self.down_timer = 0
            elif e.key == pygame.K_z:
                self.rotate(cw=False)
            elif e.key in (pygame.K_x, pygame.K_UP):
                self.rotate(cw=True)
            elif e.key == pygame.K_a:
                self.rotate(half=True)  # 180°
            elif e.key == pygame.K_SPACE:
                self.hard_drop()
            elif e.key == pygame.K_c:
                self.hold_piece()
            elif e.key == pygame.K_g:
                self.show_ghost = not self.show_ghost
            elif e.key == pygame.K_f:
                self.show_grid = not self.show_grid
        elif e.type == pygame.KEYUP:
            if e.key == pygame.K_LEFT:
                self.left_held = False; self.left_timer = 0
            elif e.key == pygame.K_RIGHT:
                self.right_held = False; self.right_timer = 0
            elif e.key == pygame.K_DOWN:
                self.down_held = False; self.down_timer = 0

    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            for e in pygame.event.get():
                self.handle_event(e)
            self.update(dt)
            self.screen.fill(BG)
            self.draw_board()
            self.draw_panel()
            if self.paused: self.draw_overlay("PAUSED", "Press P to resume")
            if self.game_over: self.draw_overlay("GAME OVER", "Press R to restart")
            pygame.display.flip()

def main():
    Tetros().run()

if __name__ == "__main__":
    main()
