# Legacy Python Architecture (py)

> **This directory is the original pure-Python implementation and is no longer actively developed. The active layer is `py2/`, which uses the C++ engine via pybind11.**

---

## Overview

All game logic lives in Python here — there is no C++ engine. The board, pieces, and move validation are implemented directly in `game/`. The same agent types exist as in `py2/` but operate on the Python board object rather than a pybind11 handle.

---

## Component Diagram

```
┌──────────────────────────────────────────────────────┐
│  GUI  (GUI/GUI.py)                                   │
│  — HiveGUI (QMainWindow)                             │
│  — BoardCanvas, SelectionCanvas (QGLWidget)          │
│  — owns the HiveBoard and agents directly            │
└──────────────┬───────────────────────────────────────┘
               │  direct method calls (not MVP)
┌──────────────▼───────────────────────────────────────┐
│  HiveBoard  (game/board.py)                          │
│  — mutable Python game state                         │
│  — place_tile / move_tile / undo_move                │
│  — get_legal_actions, game_over, get_game_state      │
└──────────────┬───────────────────────────────────────┘
               │  board reference passed in
┌──────────────▼───────────────────────────────────────┐
│  Agents  (AI/agents.py + AI/minimax/)                │
│  RandomAgent · HeuristicAgent · DQLAgent             │
│  — receive HiveBoard; HeuristicAgent deep-copies it  │
│    for search                                        │
└──────────────────────────────────────────────────────┘
```

> Note: `py` does not use the MVP pattern. The GUI owns the board directly and calls game methods during rendering and interaction. `py2` separates these concerns via `GameController`.

---

## Game Layer

**`game/board.py` — `HiveBoard`**

Central mutable state object. All pieces are Python objects stored in `tile_positions` (dict of hex coords → stacks), `pieces_remaining` (hand), and `queen_positions`.

Key methods:

| Method | Purpose |
|--------|---------|
| `place_tile(tile, pos)` | Place from hand onto board |
| `move_tile(tile, pos)` | Move a placed piece |
| `undo_move(tile, original_pos)` | Revert for minimax search |
| `get_legal_actions(player)` | Returns boolean action mask dict |
| `game_over()` | Returns winner (1/2), 0 (draw), or False |
| `get_game_state(player)` | Serialises board into dict for RL graph construction |

**`game/pieces.py`** — `HiveTile` base class and five subclasses, each implementing their own movement rules via Python methods.

**`game/ACTIONSPACE.py`** — maps piece names to indices 0–10 (same numbering as `py2`).

---

## Agents

All agents share an `Agent` ABC with a `sample_action()` method that both selects and applies the action (unlike `py2` where selection and application are separated).

**`RandomAgent`** — uniform random sample from `get_legal_actions`.

**`HeuristicAgent`** — uses `beam_minimax` from `AI/minimax/minimax.py`. Deep-copies the board for tree search, then executes the best action found on the original board.

**`DQLAgent`** — GCN/GAT Q-network. Converts board to a PyTorch Geometric graph via `get_graph_from_state`, runs a forward pass, and picks the highest-Q legal action.

### Minimax (`AI/minimax/`)

Two-phase beam search with alpha-beta pruning:
1. Apply every legal move shallowly, score with heuristic, undo. Keep top-`beam_width` candidates.
2. Recurse with full alpha-beta only on those candidates.

Uses `copy.deepcopy(board)` at the root rather than an apply/undo API — slower than `py2`'s in-place approach.

Heuristic weights (`heuristic.py::Params`): `queen_surrounding_reward`, `ownership_reward`, `win_reward`, `mp_reward`.

---

## Training (`AI/DQL/`)

Self-play training loops that produce `.pt` model checkpoints:

| Script | Opponent |
|--------|---------|
| `self_play_train.py` | Self (shared frozen target network) |
| `self_play_train_vs_random.py` | Fixed random agent |

Double Q-learning with experience replay. Reward signal driven by `REWARDS_DICT` weights (default: queen-surrounding only).

---

## File Structure

```
py/
├── ARCHITECTURE.md          # This file
├── CLAUDE.md                # Extended notes and usage guide
├── play.py                  # GUI entry point
├── arena.py                 # Tournament runner (agent vs agent)
├── game/
│   ├── board.py             # HiveBoard — mutable game state
│   ├── pieces.py            # HiveTile + 5 piece subclasses with movement rules
│   └── ACTIONSPACE.py       # 11-piece index mapping
├── AI/
│   ├── agents.py            # Agent ABC, RandomAgent, HeuristicAgent, DQLAgent
│   ├── minimax/
│   │   ├── minimax.py       # beam_minimax, minimax (alpha-beta)
│   │   └── heuristic.py     # evaluate() — 4-component heuristic
│   └── DQL/
│       ├── networks.py      # DQN (GCN), DQN_gat (GAT), DQN_simple
│       ├── rl_helper.py     # Graph construction, RewardCalculator, ReplayMemory
│       ├── self_play_train.py
│       └── self_play_train_vs_random.py
└── GUI/
    ├── GUI.py               # HiveGUI, BoardCanvas, SelectionCanvas
    ├── gui_pieces.py        # BoardPiece, ButtonPiece rendering
    └── drawing.py           # OpenGL drawing utilities
```
