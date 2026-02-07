# CLAUDE.md — AI Assistant Guide for python-games

## Project Overview

A collection of standalone Python games created with AI assistance. Each game is a single self-contained `.py` file with no shared modules or external assets. Games span multiple genres: action RPG, puzzle, and text adventure.

## Repository Structure

```
python-games/
├── CLAUDE.md              # This file
├── README.md              # Project description
├── Dungeon Crawl 2.py     # ARPG dungeon crawler (pygame) — base version
├── Dungeon Crawl 3.py     # ARPG — adds difficulty selector, minimap, dash, boss fights
├── Dungeon Crawl 4.py     # ARPG — adds elite enemies, aura system, enemy packs
├── Tetros.py              # Tetris clone (pygame)
└── Zark 1.py              # Text adventure with Tkinter GUI
```

**No subdirectories.** All game files live in the project root.

## Dependencies

| Game(s) | Dependencies |
|---------|-------------|
| Dungeon Crawl 2/3/4, Tetros | `pygame` (install via `pip install pygame`) |
| Zark 1 | `tkinter` (included with standard Python) |

There is no `requirements.txt`, `setup.py`, or `pyproject.toml`. Install pygame manually.

## Running Games

Each game is run directly:

```bash
python "Dungeon Crawl 4.py"
python "Tetros.py"
python "Zark 1.py"
```

Note: Filenames contain spaces — always quote them.

## Code Conventions

### Architecture
- **Single-file design**: Each game is entirely self-contained. No imports between game files.
- **Object-oriented**: Main game class (`Game`, `Tetros`, `AdventureApp`) with entity classes (`Player`, `Enemy`, `Boss`, `Elite`, `Piece`).
- **Dataclasses**: Used extensively for entity definitions (`@dataclass`).

### Naming
- **Variables/functions**: `snake_case` (e.g., `player_speed`, `drop_timer`)
- **Classes**: `PascalCase` (e.g., `Player`, `Enemy`, `Boss`)
- **Constants**: `UPPER_CASE` grouped at the top of each file (e.g., `WIDTH`, `HEIGHT`, `FPS`, `PLAYER_HP`)

### File Organization (within each game)
1. Imports
2. Constants / configuration block
3. Data classes and entity classes
4. Main game class with game loop
5. Entry point (`if __name__` or direct invocation)

### Game Loop Pattern (pygame games)
```python
while running:
    dt = clock.tick(FPS) / 1000.0
    handle_input(dt)
    update(dt)
    draw()
    pygame.display.flip()
```

### Code Style
- Type hints in dataclass fields and some function signatures
- Section markers as comments: `# ----- Section Name -----`
- Configuration values at file top with descriptive comments
- `try/except` around main entry points for clean `pygame.quit()` / `sys.exit()`

## Versioning Convention

Games are improved iteratively. The number suffix indicates the version:
- `Dungeon Crawl 2.py` → `Dungeon Crawl 3.py` → `Dungeon Crawl 4.py`
- `Zark 1.py` (first version)

When creating a new version, copy the previous file and increment the number. Do not modify older versions in place.

## Game Details

### Dungeon Crawl Series (pygame ARPG)
- Isometric-style dungeon exploration with procedural generation
- Combat: basic shot (LMB), power shot (RMB), mana system
- Fog of war, room/corridor generation, pickups, level progression
- v3 adds: difficulty selector, minimap, dash, boss fight, pause/help overlays
- v4 adds: elite enemies with aura buffs (Haste/Frenzy/Guardian), ranged spitter enemies, enemy packs
- Controls: WASD move, mouse aim/shoot, Q/E potions, Shift dash, P pause, F1 help

### Tetros (pygame Tetris clone)
- 10x22 board, standard 7-piece bag randomizer
- Wall kicks, hold piece, ghost piece, hard/soft drop
- Scoring with B2B Tetris bonus and combo system
- Controls: Arrows move, Z/X/Up rotate, A 180, Space hard drop, C hold

### Zark 1 (Tkinter text adventure)
- 5-room world inspired by Zork
- Inventory, puzzles, item interactions, score tracking
- Save/load via JSON, dark/light theme toggle
- Commands: go/move, look/examine, take/get, drop, use, inventory, help

## Guidelines for AI Assistants

1. **Preserve single-file architecture.** Do not split games into multiple files or create shared modules.
2. **Create new versions** rather than modifying existing ones when making significant changes (e.g., `Dungeon Crawl 5.py` from `Dungeon Crawl 4.py`).
3. **Keep constants at the top** of each file for easy tuning.
4. **Quote filenames** in shell commands — they contain spaces.
5. **No test framework exists.** Games are tested by running them manually. If adding tests, note that these are GUI applications requiring display access.
6. **No linter or formatter configured.** Follow the existing style (PEP 8-ish with dataclasses and type hints).
7. **pygame must be installed** before running Dungeon Crawl or Tetros games.
