# HIVE — v2 (C++ Engine)

> **WIP** — this is the rewritten stack: C++ game engine + Python/Qt GUI.
> The original Python engine lives in `py/` and still works independently.

---

## Prerequisites

| Dependency | Install |
|------------|---------|
| CMake ≥ 3.20 | `brew install cmake` |
| C++20 compiler | Xcode Command Line Tools (macOS) |
| [fmt](https://github.com/fmtlib/fmtlib) | `brew install fmt` |
| [pybind11](https://pybind11.readthedocs.io) | `brew install pybind11` |
| Python ≥ 3.10 | `brew install python` |
| PyQt5 | `pip install PyQt5` |
| PyOpenGL | `pip install PyOpenGL PyOpenGL_accelerate` |

---

## Building the C++ engine

The C++ game engine is exposed to Python as `hive_engine` via pybind11.
The build step compiles everything and drops `hive_engine.so` straight into `py2/`
so Python can import it without any extra path setup.

```bash
# Always run these from inside cpp/ — not from the project root
cd HIVE/cpp

# First-time configure + build
cmake -S . -B build
cmake --build build

# On subsequent code changes, just rebuild:
cmake --build build
```

If cmake cannot find pybind11, point it at your installation:
```bash
cmake -S . -B build -Dpybind11_DIR=$(python3 -m pybind11 --cmakedir)
```

After a successful build you should see `py2/hive_engine*.so`.

---

## Running the game

```bash
cd py2

# Human vs Human
python main.py

# Human (player 1) vs Random agent (player 2)
python main.py --player2 random

# Random vs Random — watch two AIs play
python main.py --player1 random --player2 random

# Simplified rules: queen surrounded by 3 pieces = loss (default is 6)
python main.py --player2 random --simplified

# Cap total turns (draw if neither queen is surrounded by then)
python main.py --player2 random --max-turns 50
```

---

## How to play

### The board

The board is a hex grid rendered in the top panel. Each player's pieces are colour-coded:
- **Player 1** — gold hexagons
- **Player 2** — black hexagons

### Placing a piece

1. Look at the **bottom tray** — it shows the pieces you still have in hand (only insects with remaining copies are shown).
2. Click a piece in the tray to select it. Valid placement positions light up **green** on the board.
3. Click a green hex to place the piece there.

### Moving a piece

1. Click any of your pieces **already on the board** to select it. Valid destination hexes light up green.
2. Click a green hex to move there.
3. Click anywhere else (or select a different piece) to cancel.

### AI turns

When the current player is an AI agent, the **"Next Turn"** button in the toolbar activates. Click it to execute one AI move. The button is disabled when it is a human's turn.

### Panning the board

Click and drag on an empty area of the board to pan the view.

### Win condition

**Standard rules:** surround the opponent's Queen Bee completely (all 6 adjacent hexes occupied).

**Simplified rules** (`--simplified`): surround the opponent's Queen Bee with just 3 pieces — good for faster games and training.

---

## Project structure

```
HIVE/
├── cpp/                    # C++ game engine
│   ├── Game.h / Game.cpp         — core game state and rules
│   ├── MoveFetcher.h / .cpp      — per-insect move generation
│   ├── Position.h                — axial hex coordinate
│   ├── Pieces.h                  — HiveTile data type + Insect enum
│   ├── bindings.cpp              — pybind11 module definition
│   └── CMakeLists.txt
│
└── py2/                    # Python layer (MVC)
    ├── main.py                   — entry point / argument parsing
    ├── hive_engine*.so           — built C++ module (generated)
    ├── agents/
    │   ├── base.py               — Agent ABC + Action dataclass
    │   └── random_agent.py       — uniform random agent
    ├── controller/
    │   └── game_controller.py    — mediates engine ↔ view
    └── gui/
        ├── main_window.py        — HiveGUI (QMainWindow)
        ├── board_canvas.py       — hex board rendering + mouse events
        ├── selection_canvas.py   — piece-selection tray
        ├── gui_pieces.py         — BoardPiece / ButtonPiece renderers
        └── drawing.py            — OpenGL shape + insect drawing
```

---

## Adding agents

Subclass `agents.base.Agent` and implement `select_action`:

```python
from agents.base import Agent, Action

class MyAgent(Agent):
    def select_action(self, game) -> Action:
        actions = game.get_legal_actions()   # list of hive_engine.Action
        # ... your logic ...
        a = actions[0]
        return Action(tile_idx=a.tile_idx, to=(a.to.q, a.to.r))
```

Then pass an instance to `main.py` via `_make_agent` or wire it up directly:

```python
controller = GameController(game=game, view=view, player2=MyAgent())
```
