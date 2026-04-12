# HIVE — System Architecture

## Overview

A Python implementation of the Hive board game with three AI agent types: random, minimax/heuristic, and deep Q-learning (DQL). Supports both a PyQt5/OpenGL GUI and a command-line interface.

---

## Directory Structure

```
py/
├── play.py                     # Entry point for GUI game
├── cl_interface.py             # Command-line interface for human play
├── arena.py                    # Tournament runner for agent vs agent evaluation
│
├── game/                       # Core game logic
│   ├── __init__.py
│   ├── board.py                # HiveBoard: game state, move validation, action generation
│   ├── pieces.py               # HiveTile base class + 5 piece subclasses
│   └── ACTIONSPACE.py          # 11-piece action space index mapping
│
├── AI/                         # Agent implementations
│   ├── agents.py               # Agent ABC, RandomAgent, HeuristicAgent, DQLAgent
│   ├── minimax/
│   │   ├── __init__.py
│   │   ├── minimax.py          # Alpha-beta minimax + beam minimax
│   │   └── heuristic.py        # Evaluation function + Params dataclass
│   └── DQL/
│       ├── __init__.py
│       ├── networks.py         # DQN (GCN) and DQN_gat (GAT) network architectures
│       ├── rl_helper.py        # Graph state builder, RewardCalculator, ExperienceReplay
│       └── self_play_train.py  # Self-play training loop
│
└── GUI/                        # Rendering and interaction
    ├── __init__.py
    ├── GUI.py                  # HiveGUI, BoardCanvas, SelectionCanvas
    ├── gui_pieces.py           # BoardPiece and ButtonPiece rendering classes
    ├── drawing.py              # OpenGL insect and shape drawing functions
    └── PX_SCALE.py             # Pixel scaling constant (PX_SCALE = 2)
```

---

## Game Layer (`game/`)

### `board.py` — `HiveBoard`

The central game state object. Tracks:
- `tile_positions`: `dict[coord -> list[HiveTile]]` — stacks of tiles at each hex position
- `pieces_remaining`: available pieces per player (hand)
- `player_turns`: turn counter per player

Key methods:
- `place_tile()` / `move_tile()` — apply a move
- `undo_move()` — revert a move (used by minimax search)
- `get_valid_placements()` — legal placement positions for the current player
- `get_legal_actions()` — full boolean action mask across all pieces and positions
- `game_over()` — checks win (queen surrounded), loss, and draw
- `get_game_state()` — serialises current state (used for RL graph construction)
- `check_unconnected()` — DFS to enforce the "one hive" connectivity rule

### `pieces.py` — `HiveTile` and subclasses

`HiveTile` is the base class with shared logic:
- `covered()` — is this piece on top of a stack?
- `check_slide_space()` — validates sliding movement (gate check)
- `test_breakage()` — removes piece temporarily and checks if hive stays connected

Subclasses each implement `get_valid_moves()`:
- `Queen` — slides 1 space in any direction
- `Ant` — BFS to any reachable position
- `Beetle` — 1 step, can climb onto other pieces (stacks)
- `Grasshopper` — jumps in a straight line over contiguous pieces
- `Spider` — must move exactly 3 spaces

### `ACTIONSPACE.py`

Maps the 11 piece names to action indices (0–10):
`queen1=0, spider1=1, spider2=2, beetle1=3, beetle2=4, ant1=5, ant2=6, ant3=7, grasshopper1=8, grasshopper2=9, grasshopper3=10`

---

## AI Layer (`AI/`)

### Agent Interface (`agents.py`)

All agents implement the `Agent` ABC:
- `set_board(board)` — attach the current game board
- `sample_action()` — return a legal action

Three concrete agents:
- `RandomAgent` — uniform random sampling over legal actions
- `HeuristicAgent` — wraps `beam_minimax()` with configurable `Params`
- `DQLAgent` — epsilon-greedy policy over Q-values from a trained GNN

### Minimax (`minimax/`)

**`minimax.py`**
- `minimax(board, depth, alpha, beta, maximising)` — standard alpha-beta pruning
- `beam_minimax(board, depth, beam_width=3)` — at each ply only the top `beam_width` moves (by heuristic) are explored, dramatically cutting the branching factor

**`heuristic.py`**
- `Params` dataclass holds configurable weights: `queen_surrounding_reward`, `ownership_reward`, `win_reward`, `mp_reward`
- `evaluate(board, player)` computes:
  1. Pieces surrounding the opponent's queen (primary threat signal)
  2. Queen ownership (is a beetle sitting on top?)
  3. Moveable piece count (mobility) for each player
  - Returns a weighted net score

### Deep Q-Learning (`DQL/`)

**`networks.py`**
- `DQN` — 4-layer GCN with a global feature vector; outputs masked Q-values per (node, action) pair. Illegal actions are masked with −1000.
- `DQN_gat` — same structure but uses multi-head GAT layers (4 heads, single head at final layer)

**`rl_helper.py`**
- `get_graph_from_state(state, player)` — converts serialised board state into a PyTorch Geometric `Data` object:
  - Nodes: on-board tiles + adjacent empty spaces + valid placements/moves
  - Node features: one-hot piece type encoding (13 or 25 dims), position type flags
  - Edges: hex adjacency + valid move edges
  - Global features: 22-dim hand inventory vector
  - Action mask: 11-dim boolean per node
  - Returns a `GraphState` (data, action_mask, pos→node mapping)
- `RewardCalculator` — 5 reward components (queen surroundings, ownership, mobility, win/loss); weighted sum
- `ExperienceReplay` — ring-buffer replay memory with prioritised sampling (rewarded vs random transitions)
- `Transition` dataclass: `(state, next_state, action, reward, done)`

**`self_play_train.py`**

Self-play training loop (CLI entry point):
- Two agents share a policy network; a separate frozen target network provides stable Q-targets
- Double Q-learning update (online net selects action, target net evaluates)
- Key hyperparameters: `batch_size=25`, `gamma=0`, `lr=1e-3`, `epsilon=0.9`, `capacity=10000`, `max_iter=300000`
- Every 25 iterations: gradient update; every 10000: epsilon decay + target network sync + model checkpoint

---

## GUI Layer (`GUI/`)

### `GUI.py`

`HiveGUI` (main window) coordinates:
- `BoardCanvas` — `QGLWidget` rendering the hexagonal board via OpenGL
  - Converts hex coordinates to screen pixels
  - Handles mouse events: click detection on tiles, valid move highlighting
  - Pan and zoom support
- `SelectionCanvas` — `QGLWidget` piece selection sidebar
  - Shows remaining pieces per player as clickable buttons
  - Sets `placing_tile` flag on the parent GUI

State tracked on the GUI:
- Active player, current placing/moving tile
- State-action memory for RL transition recording (`rl_update()`)

### `gui_pieces.py`

- `PieceMixin` — shared `render()` (hexagon + insect) and `contains()` (hit detection)
- `BoardPiece` — links a `HiveTile` to a canvas position
- `ButtonPiece` — selectable piece button with remaining count display

### `drawing.py`

Pure OpenGL drawing utilities:
- `draw_hexagon()`, `draw_ellipse()`, `draw_text()`
- One function per insect: `draw_ant()`, `draw_spider()`, `draw_grasshopper()`, `draw_beetle()`, `draw_queen()`
- `draw_insect()` — dispatcher via dict lookup

---

## Entry Points

| Script | Purpose |
|---|---|
| `play.py` | Launch GUI; pass `--agent dqn\|random\|mm` and optionally `--model <path>` |
| `cl_interface.py` | Text-based human play |
| `arena.py` | Run N games between two agents, report win rates |
| `AI/DQL/self_play_train.py` | Train DQL agent via self-play |

---

## Data Flow

```
HiveBoard (game state)
    │
    ├─► get_legal_actions() ──► Agent.sample_action()
    │       │                       ├─ RandomAgent: uniform random
    │       │                       ├─ HeuristicAgent: beam_minimax → evaluate()
    │       │                       └─ DQLAgent: get_graph_from_state() → DQN/DQN_gat → Q-values
    │       │
    └─► place_tile() / move_tile()
            │
            └─► GUI: update_GUI() → BoardCanvas.renderGL() / SelectionCanvas.renderGL()
```

---

## Key Design Decisions

- **Make/undo move pattern** — `undo_move()` on `HiveBoard` allows minimax to explore the game tree without copying board state
- **Graph representation for RL** — the board's natural relational structure (adjacency, stacking) maps cleanly to a graph; GCN/GAT layers aggregate neighbourhood information
- **Shared agent interface** — `Agent` ABC means the GUI and arena are agnostic to agent type; agents can be swapped without changing game/UI code
- **Action masking** — illegal actions are masked before argmax/sampling in the DQL agent, ensuring only legal moves are taken
- **Experience replay with prioritisation** — rewarded transitions are oversampled to address the sparsity of non-zero rewards in Hive
