# Python Architecture (py2)

This is the Python layer that sits on top of the C++ game engine (`hive_engine`). Python is responsible for agents, the GUI, and DQL training. All game logic and minimax search live in C++.

---

## Action Representation

All agents use a single unified action type — a `(tile_idx, dest_pos)` pair:

- `tile_idx` is an integer 0–10 identifying a specific piece instance, matching the ACTIONSPACE mapping used by the DQL network:

  | tile_idx | Piece |
  |----------|-------|
  | 0 | queen |
  | 1 | spider1 |
  | 2 | spider2 |
  | 3 | beetle1 |
  | 4 | beetle2 |
  | 5 | ant1 |
  | 6 | ant2 |
  | 7 | ant3 |
  | 8 | grasshopper1 |
  | 9 | grasshopper2 |
  | 10 | grasshopper3 |

- `dest_pos` is the destination hex coordinate `(q, r)`.

Whether the action is a placement or movement is determined at runtime by the engine — if the piece identified by `tile_idx` is in the player's hand, it is placed; if it is on the board, it is moved. This distinction does not need to be encoded in the action itself.

This representation is native to both the DQL network (which outputs Q-values indexed by tile_idx per graph node) and the C++ minimax (which returns the same `Action` type from `getBestMove`).

---

## Game Engine Interface

The C++ engine is imported as a Python module via pybind11:

```python
import hive_engine

game = hive_engine.Game(max_turns=-1, simplified_game=False)
```

The `game` object is a handle to the underlying C++ `Game` instance. All agents interact with it through this handle.

| Method | Returns | Used by |
|--------|---------|---------|
| `game.get_legal_actions()` | `list[Action]` | Random, DQL |
| `game.get_game_state()` | `dict` | DQL (graph construction) |
| `game.get_valid_placements(insect)` | `list[pos]` | GUI |
| `game.get_valid_moves(pos)` | `list[pos]` | GUI |
| `game.apply_action(action)` | `pos \| None` | Controller |
| `game.check_game_over()` | `int` | Controller |
| `game.get_current_player()` | `int` | Controller, GUI |
| `hive_engine.get_best_move(game, depth, beam_width, params)` | `Action` | Minimax agent |

`apply_action` returns the tile's original board position if the action was a movement (used by minimax for undo), or `None` if it was a placement. The controller does not need this return value — it is only used internally by the C++ minimax.

`get_best_move` takes the `game` handle directly. pybind11 passes the underlying C++ reference through — no state is extracted into Python and passed back in.

---

## Agents

All agents share a common base class and return the unified `Action` type:

```python
class Agent(ABC):
    @abstractmethod
    def select_action(self, game: hive_engine.Game) -> Action:
        """Return the chosen action without applying it to the game."""
        pass
```

The controller is responsible for applying the returned action. Agents only decide — they never mutate game state.

### RandomAgent

```python
class RandomAgent(Agent):
    def select_action(self, game):
        return random.choice(game.get_legal_actions())
```

### MinimaxAgent

Passes the game handle directly into C++. The entire search runs inside C++ — beam evaluation, alpha-beta pruning, parallel branch exploration. From Python's perspective this is a single blocking call that returns an `Action`.

```python
class MinimaxAgent(Agent):
    def __init__(self, depth: int, beam_width: int, params: hive_engine.HeuristicParams):
        self.depth = depth
        self.beam_width = beam_width
        self.params = params

    def select_action(self, game):
        return hive_engine.get_best_move(game, self.depth, self.beam_width, self.params)
```

- `depth`: search depth (odd values preferred — finishes on the agent's own turn)
- `beam_width`: number of candidates kept per level
- `params`: `HeuristicParams(queen_surrounding_reward, ownership_reward, win_reward, mp_reward)`

### DQLAgent

Uses tile_idx internally for the network's output space, but returns the same `Action` type as all other agents.

```python
class DQLAgent(Agent):
    def __init__(self, q_network: DQN, epsilon: float, player: int):
        self.q_network = q_network
        self.epsilon = epsilon
        self.player = player

    def select_action(self, game):
        if random.random() < self.epsilon:
            return random.choice(game.get_legal_actions())

        state = game.get_game_state()
        graph = get_graph_from_state(state, self.player)
        with torch.no_grad():
            q_values = self.q_network(graph)  # per-node, per-tile_idx Q-values

        # argmax over (node × tile_idx) space → (dest_pos, tile_idx) → Action
        action_idx = torch.argmax(q_values).item()
        dest_pos = graph.pos_node_mapping_rev[action_idx // 11]
        tile_idx = action_idx % 11
        return Action(tile_idx=tile_idx, to=dest_pos)
```

`get_game_state()` is the only call that extracts C++ data into Python, and it is unavoidable since PyTorch lives in Python.

---

## MVC Architecture

```
┌─────────────────────────────────────────┐
│  View (Python/Qt)                       │
│  BoardCanvas, SelectionCanvas           │
│  — renders state, emits Qt signals      │
├─────────────────────────────────────────┤
│  Controller (Python)                    │
│  GameController                         │
│  — connects signals to game actions     │
│  — drives agent turns                   │
│  — calls agent.select_action(game)      │
│  — applies returned action via          │
│    game.apply_action(action)            │
├─────────────────────────────────────────┤
│  Model (C++ via pybind11)               │
│  hive_engine.Game                       │
│  — game state, rules, move generation   │
│  — minimax search (get_best_move)       │
└─────────────────────────────────────────┘
```

The view never touches the game object. The controller mediates everything.

### GameController

```python
class GameController:
    def __init__(self, game: hive_engine.Game, view: HiveGUI,
                 player1: Agent | None, player2: Agent | None):
        self.game = game
        self.view = view
        self.players = {1: player1, 2: player2}

        view.placement_requested.connect(self.on_placement_requested)
        view.move_requested.connect(self.on_move_requested)
        view.piece_selected.connect(self.on_piece_selected)
        view.ai_turn_requested.connect(self.on_ai_turn_requested)

    def on_ai_turn_requested(self):
        player = self.game.get_current_player()
        agent = self.players[player]
        if agent is None:
            return
        action = agent.select_action(self.game)
        self.game.apply_action(action)
        self.view.set_board_state(self.game.get_tile_positions())
        if winner := self.game.check_game_over():
            self.view.show_game_over(winner)
```

**Human turn flow:**
1. User clicks a piece in the tray → view emits `piece_selected(insect)`
2. Controller calls `game.get_valid_placements(insect)`, tells view to highlight them
3. User clicks a valid position → view emits `placement_requested(tile_idx, pos)`
4. Controller calls `game.apply_action(Action(tile_idx, pos))`, refreshes view

**AI turn flow:**
1. User clicks "Next Turn" → view emits `ai_turn_requested`
2. Controller calls `agent.select_action(game)` to get an `Action`
3. Controller calls `game.apply_action(action)`, refreshes view

### GUI (View Layer)

`BoardCanvas` and `SelectionCanvas` are Qt/OpenGL widgets. They render board state passed in by the controller and emit signals for user interactions — never calling game methods directly.

**Signals emitted by the view:**

| Signal | Trigger |
|--------|---------|
| `piece_selected(insect: str)` | User clicks a piece in the tray |
| `placement_requested(tile_idx: int, pos: tuple)` | User clicks a valid placement hex |
| `tile_clicked(pos: tuple)` | User clicks a placed tile on the board |
| `move_requested(tile_idx: int, to_pos: tuple)` | User clicks a valid move destination |
| `ai_turn_requested()` | User clicks "Next Turn" button |

**Methods called on the view by the controller:**

| Method | Purpose |
|--------|---------|
| `set_board_state(tile_positions)` | Re-render the board |
| `highlight_placements(positions)` | Show valid placement hexes in green |
| `highlight_moves(positions)` | Show valid move destinations in green |
| `clear_highlights()` | Remove all green overlays |
| `set_player_turn(player)` | Update turn indicator |
| `show_game_over(winner)` | Display result |

---

## File Structure

```
py2/
├── ARCHITECTURE.md          # This file
├── main.py                  # Entry point — wires game, controller, view, agents
├── agents/
│   ├── __init__.py
│   ├── base.py              # Agent ABC
│   ├── random_agent.py
│   ├── minimax_agent.py
│   └── dql_agent.py
├── controller/
│   ├── __init__.py
│   └── game_controller.py
├── gui/
│   ├── __init__.py
│   ├── main_window.py       # HiveGUI (QMainWindow)
│   ├── board_canvas.py      # BoardCanvas (QGLWidget)
│   ├── selection_canvas.py  # SelectionCanvas (QGLWidget)
│   ├── drawing.py           # OpenGL drawing utilities
│   └── gui_pieces.py        # BoardPiece, ButtonPiece
└── training/
    ├── dql/
    │   ├── networks.py      # DQN, DQN_gat, DQN_simple
    │   ├── rl_helper.py     # Graph construction, reward calculation
    │   └── train.py         # Training loop
    └── arena.py             # Tournament runner
```

---

## Wiring Example

```python
# main.py
import hive_engine
from agents import MinimaxAgent, RandomAgent
from controller import GameController
from gui import HiveGUI

game = hive_engine.Game(simplified_game=True)
view = HiveGUI()

params = hive_engine.HeuristicParams(
    queen_surrounding_reward=1.0,
    ownership_reward=3.0,
    win_reward=100.0,
    mp_reward=0.5
)
player1 = MinimaxAgent(depth=5, beam_width=3, params=params)
player2 = RandomAgent()

controller = GameController(game, view, player1, player2)
view.show()
```
