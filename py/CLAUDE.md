# HIVE Project Architecture & Structure

## Overview

A Python implementation of the Hive board game with three AI agent types (random, minimax/heuristic, and deep Q-learning). Supports GUI play, CLI, and tournament evaluation.

---

## Directory Structure

```
py/
├── play.py                          # GUI entry point - configurable agent selection
├── cl_interface.py                  # Command-line human play
├── arena.py                         # Tournament runner - agent vs agent evaluation
├── delete_models.py                 # Utility to clean up saved model checkpoints
│
├── game/                            # Core game logic (rules, board state)
│   ├── __init__.py
│   ├── board.py                     # HiveBoard: state, move validation, action generation
│   ├── pieces.py                    # HiveTile + 5 piece types with movement rules
│   └── ACTIONSPACE.py               # 11-piece action space index mapping
│
├── AI/                              # Agent implementations
│   ├── agents.py                    # Agent ABC + RandomAgent, HeuristicAgent, DQLAgent
│   ├── minimax/
│   │   ├── __init__.py
│   │   ├── minimax.py               # Alpha-beta + beam minimax search
│   │   └── heuristic.py             # Evaluation function with configurable weights
│   └── DQL/
│       ├── __init__.py
│       ├── networks.py              # DQN (GCN), DQN_gat (GAT), DQN_simple (single-layer GCN)
│       ├── rl_helper.py             # Graph builder, reward calculation, experience replay
│       ├── self_play_train.py       # Self-play training loop (agent vs trained agent)
│       └── self_play_train_vs_random.py  # Training loop (agent vs random opponent)
│
└── GUI/                             # Rendering & interaction (PyQt5/OpenGL)
    ├── __init__.py
    ├── GUI.py                       # HiveGUI main window + BoardCanvas + SelectionCanvas
    ├── gui_pieces.py                # BoardPiece and ButtonPiece rendering
    ├── drawing.py                   # OpenGL insect and shape drawing functions
    └── PX_SCALE.py                  # Pixel scaling constant (PX_SCALE = 2)
```

---

## Core Concepts

### Game State (board.py)

**HiveBoard** tracks:
- `tile_positions`: dict mapping hex coordinates to stacks of HiveTile objects
- `queen_positions`: [player_1_queen_pos, player_2_queen_pos]
- `pieces_remaining`: available pieces per player (hand)
- `player_turns`: turn counter per player

**Key methods:**
- `place_tile(tile, pos)` / `move_tile(tile, pos)` — apply moves
- `undo_move()` — revert (used by minimax)
- `get_legal_actions(player)` — returns boolean action mask
- `game_over()` — returns winner (1, 2, 0 for draw, False if ongoing)
- `get_game_state(player)` — serializes board for RL graph construction

### Pieces (pieces.py)

Base class `HiveTile` with subclasses implementing movement rules:
- **Queen**: slides 1 space
- **Ant**: BFS to any reachable position
- **Beetle**: 1 step, can climb stacks
- **Grasshopper**: jumps in straight line over pieces
- **Spider**: exactly 3 spaces

All use `test_breakage()` and `check_slide_space()` to enforce hive connectivity.

### Action Space (ACTIONSPACE.py)

11 pieces mapped to indices 0–10:
```
queen1=0, spider1=1, spider2=2, beetle1=3, beetle2=4,
ant1=5, ant2=6, ant3=7, grasshopper1=8, grasshopper2=9, grasshopper3=10
```

---

## Agent Types

### RandomAgent (agents.py)

Uniformly samples from legal actions.

### HeuristicAgent (AI/minimax/)

Uses `beam_minimax()` with configurable `Params`:
- `queen_surrounding_reward` — pieces adjacent to opponent queen
- `ownership_reward` — beetle control of opponent queen
- `win_reward` — game-ending states
- `mp_reward` — mobility (moveable piece count)

Beam width limits branching; depth controls lookahead.

### DQLAgent (agents.py + AI/DQL/)

Epsilon-greedy policy over Q-values from GCN/GAT.

**Key files:**
- `networks.py` — DQN (4-layer GCN), DQN_gat (4-layer GAT), DQN_simple (1-layer GCN)
- `rl_helper.py` — graph construction, reward calculation, replay memory
- `self_play_train.py` / `self_play_train_vs_random.py` — training loops

**Graph representation:**
- Nodes: on-board tiles + adjacent empty spaces + valid placements
- Node features: one-hot piece type (13 or 25 dims) + position flags
- Edges: hex adjacency + valid move edges
- Global features: 22-dim hand inventory vector
- Action mask: illegal actions masked with −1000

**Reward signal:**
- `queen_surrounding`: pieces adjacent to opponent queen (configurable weight)
- Other rewards (ownership, mobility) weighted by `REWARDS_DICT`

---

## Training Scripts

### self_play_train.py
- Two agents share a policy network
- Separate frozen target network for stability
- Double Q-learning update
- Hyperparameters: `batch_size=25, gamma=0, lr=5e-3, epsilon=0.9`
- Saves models based on **win rate** (best metric)

### self_play_train_vs_random.py
- DQN agent vs random opponent
- Only player 1 (DQN) is trained
- Saves models based on **win rate**
- Includes `--debug` flag for reward tracing

### Key Training Options
```bash
# vs random, simplified game
python -m AI.DQL.self_play_train_vs_random --simplified_game --max_iter 100000

# With custom hyperparameters
python -m AI.DQL.self_play_train_vs_random --gamma 0.8 --learning_rate 1e-4 --epsilon 0.95

# Debug mode (prints reward calculations)
python -m AI.DQL.self_play_train_vs_random --debug --simplified_game --max_iter 5000
```

---

## Running the Game

### GUI (play.py)
```bash
# Human vs Human
python play.py

# Human vs Random
python play.py --player2 random

# Human vs Minimax (depth 3)
python play.py --player2 mm

# Human vs DQN
python play.py --player2 dqn

# AI vs AI (both players specified)
python play.py --player1 random --player2 mm

# Simplified game rules
python play.py --player1 dqn --player2 random --simplified
```

**GUI Controls:**
- Click pieces in bottom tray to select
- Click valid placements (green hexagons) to place
- Click placed pieces to move them
- **"Next Turn" button** — advances AI turns (no mouse wiggling required!)
  - Button enabled when it's an AI player's turn
  - Button disabled when it's a human player's turn

### Arena Tournament (arena.py)
```bash
# Random vs Random, 100 games
python arena.py --player1 random --player2 random --games 100

# DQN vs Minimax
python arena.py --player1 dqn --player2 mm --games 50

# With logging
python arena.py --player1 dqn --player2 random --games 20 --log

# Simplified rules
python arena.py --player1 dqn --player2 random --games 50 --simplified
```

### Cleanup Utility (delete_models.py)
```bash
# Preview what would be deleted
python delete_models.py --prefix vs_random --dry-run

# Actually delete models
python delete_models.py --prefix simplified_it

# Custom directory
python delete_models.py --prefix dqn --dir /path/to/models
```

---

## GUI Architecture (GUI.py)

### HiveGUI (QMainWindow)

**State:**
- `board` — the HiveBoard object
- `player1` / `player2` — Agent instances (or None for human)
- `placing_tile` / `moving_tile` — transient interaction state
- `p1_memory` / `p2_memory` — state-action pairs for RL (if enabled)

**Key methods:**
- `set_player(player, agent)` — set AI agent for a player
- `refresh_display()` — render both canvases, check game over
- `step_ai_turn()` — execute one AI turn (button click)
- `_update_button_state()` — enable/disable "Next Turn" button
- `update_from_board()` — sync BoardCanvas with board state
- `update_memory()` — record transitions for RL

**Toolbar:**
- "Next Turn" button — executes one AI move per click
  - `self.next_turn_btn` (QAction) connected to `step_ai_turn()`
  - Automatically enabled/disabled based on current player type

### BoardCanvas (QGLWidget)

Main hex-grid rendering and interaction.

**State:**
- `tiles` — dict mapping board coordinates to (BoardPiece, canvas_pos) tuples
- `pan_x`, `pan_y`, `dragging` — user interaction tracking
- Mouse position for rendering tile preview during placement/movement

**Interaction:**
- Mouse move → calls `refresh_display()` (continuous feedback)
- Mouse press → selects/moves pieces, calls `refresh_display()`
- Green hexagon overlay shows valid placements/moves

### SelectionCanvas (QGLWidget)

Bottom panel (150px) showing remaining pieces per player.

**State:**
- `buttons_p1` / `buttons_p2` — ButtonPiece objects for each insect type

**Interaction:**
- Click a piece button → `placing_tile` set, waits for board placement

---

## Reward System (rl_helper.py)

### RewardCalculator

**Components** (weighted by `REWARDS_DICT`):
- `reward_queen_surrounding()` — pieces adjacent to opponent's queen (±1 per change)
- `reward_queen_ownership()` — beetle stacking on opponent queen
- `reward_change_in_moves()` — opponent mobility reduction vs own gain
- `reward_change_moveable_pieces()` — number of moveable pieces per player
- `reward_win_lose()` — game end conditions (±100 for win/loss)

**Simplified game** (typical):
```python
REWARDS_DICT = {
    'queen_surrounding': 1,      # Only reward this
    'queen_ownership': 0,
    'change_in_moves': 0,
    'change_moveable_pieces': 0,
    'win_lose': 0                # (or 1 if training for wins)
}
```

### Graph Construction (get_graph_from_state)

Rebuilds from scratch each call — maps board state → PyTorch Geometric Data object:

- Node count and order can vary per state (unstable node IDs)
- Position-to-node mapping stored separately (`pos_node_mapping`)
- Action mask handles illegal actions

---

## Important Notes

### Known Issues & Design Decisions

1. **Node ID Instability** — Graph is rebuilt from scratch each state, so node IDs change. Use `pos_node_mapping` to link board positions to graph nodes.

2. **Sparse Rewards** — Queen-surrounding reward only fires ~5-10% of transitions in early training. Consider shaped rewards or win/loss penalties.

3. **Simplified Game** — Win condition is 3 pieces around opponent's queen (instead of 6 in full game). Easier for RL but still requires strategy.

4. **Button-Driven UI** — No more blocking sleep calls or mouse-wiggling for AI vs AI. Each click advances one turn.

5. **Arena Agents are Fresh** — Tournament creates new agent instances; they don't retain state from training. Each game is independent.

### Development Tips

- **Debug Reward Calculations**: Use `--debug` flag in training to trace reward signals
- **Check Win Rate**: Always save/evaluate models by win rate, not intermediate metrics
- **Hyperparameter Tuning**: `gamma=0.8`, `lr=1e-4`, `epsilon=0.95` are good starting points
- **Reduced Features**: Use `--reduced` for 13-dim features instead of 25-dim (faster training)
- **Simplified Rules**: Use `--simplified_game` for easier learning task

---

## File Dependencies

```
play.py
  ├─ GUI/GUI.py
  ├─ game/board.py
  └─ AI/agents.py

arena.py
  ├─ game/board.py
  └─ AI/agents.py

self_play_train_vs_random.py
  ├─ AI/DQL/networks.py
  ├─ AI/DQL/rl_helper.py
  └─ AI/agents.py

GUI/GUI.py
  ├─ game/board.py
  ├─ AI/agents.py (for type hints)
  └─ GUI/gui_pieces.py, drawing.py
```

---

## Testing & Validation

### Unit Tests
- `arena.py` — quick sanity check with `python arena.py --games 5`
- GUI — manually test with `python play.py --player1 random --player2 random`

### Training Diagnostics
- Check reward trends at iteration 1000, 10000, 50000, etc.
- Win rate should trend upward if learning is working
- If stuck at ~50%, agent may not be learning anything useful
- Use `--debug` to verify rewards are being calculated correctly

### Model Evaluation
```bash
# Test a saved model against random
python arena.py --player1 dqn --player2 random --games 100 --model /path/to/model.pt
```

---

## Quick Start

```bash
# 1. Train vs random (simplified, 50k iterations)
cd HIVE/py
python -m AI.DQL.self_play_train_vs_random --simplified_game --max_iter 50000

# 2. Evaluate best model
python arena.py --player1 dqn --player2 random --games 20 --simplified

# 3. Play against it in GUI
python play.py --player2 dqn --simplified

# 4. Clean up old checkpoints
python delete_models.py --prefix vs_random --dry-run
```
