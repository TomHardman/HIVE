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

Pure-Python beam-search minimax with alpha-beta pruning. Uses `game.apply_action` / `game.undo` for in-place tree traversal — no deep copy of game state.

```python
class MinimaxAgent(Agent):
    def __init__(self, depth: int, beam_width: int, params: MinimaxParams) -> None:
        ...

    def select_action(self, game: hive_engine.Game) -> Action | None:
        player = game.get_current_player()
        _, best = _beam_minimax(game, self.depth, True, player, self.params,
                                -math.inf, math.inf, self.beam_width)
        if best is None:
            return None
        return Action(tile_idx=best.tile_idx, to=(best.to.q, best.to.r))
```

**`MinimaxParams`** — configurable heuristic weights (defaults match py arena):
```python
@dataclass
class MinimaxParams:
    queen_surrounding_reward: float = 1.0
    ownership_reward: float = 3.0
    win_reward: float = 100.0
    mp_reward: float = 0.5
```

**Beam search** (two phases per node):
1. Apply every legal action shallowly, score with the heuristic, undo. Keep top-`beam_width` candidates.
2. Run full alpha-beta minimax only on those candidates.

Reduces effective branching factor from ~20–40 moves down to `beam_width` per level.

**Heuristic** (`_evaluate`) — four differential components (own advantage − opponent advantage):

| Component | Implementation |
|-----------|---------------|
| Win/loss | ±`win_reward` from `check_game_over()` |
| Queen surrounding | Count occupied hex neighbours of each queen |
| Queen ownership | Opponent piece on top of own queen's stack |
| Mobility | Distinct pieces (by insect+id) with ≥1 valid move |

- `depth`: search depth (3 is the practical limit in pure Python)
- `beam_width`: candidates retained per node (default 3)

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

## MVP Architecture

This is a **Model-View-Presenter** pattern, not plain MVC. The key distinction: the View is fully passive — it never observes the Model directly and contains no game logic. All decisions about what to display flow through the Presenter (`GameController`), which queries the Model, formats the data (building `TileState` objects from pybind11 C++ types), and pushes the result to the View via an explicit API.

```
┌─────────────────────────────────────────┐
│  View (Python/Qt)                       │
│  HiveGUI, BoardCanvas, SelectionCanvas  │
│  — passive renderer                     │
│  — emits Qt signals for user input      │
│  — exposes a push API (set_*, show_*)   │
├─────────────────────────────────────────┤
│  Presenter (Python)                     │
│  GameController                         │
│  — subscribes to view signals           │
│  — queries Model, transforms data       │
│  — pushes formatted state to the view   │
│  — drives agent turns                   │
├─────────────────────────────────────────┤
│  Model (C++ via pybind11)               │
│  hive_engine.Game                       │
│  — game state, rules, move generation   │
│  — minimax search (get_best_move)       │
└─────────────────────────────────────────┘
```

The View never holds a reference to the game object. The Presenter owns both and mediates all communication.

### GameController (Presenter)

```python
class GameController:
    def __init__(self, game: hive_engine.Game, view: HiveGUI,
                 player1: Agent | None, player2: Agent | None) -> None:
        self.game = game
        self.view = view
        self.players = {1: player1, 2: player2}

        view.tray_clicked.connect(self.on_tray_clicked)
        view.board_tile_clicked.connect(self.on_board_tile_clicked)
        view.whitespace_clicked.connect(self.on_whitespace_clicked)
        view.placement_requested.connect(self.on_placement_requested)
        view.move_requested.connect(self.on_move_requested)
        view.ai_turn_requested.connect(self.on_ai_turn_requested)

    def on_ai_turn_requested(self) -> None:
        player = self.game.get_current_player()
        agent = self.players.get(player)
        if agent is None:
            return
        action = agent.select_action(self.game)
        if action is None:
            return
        self.game.apply_action(_cpp_action(action.tile_idx, action.to))
        self._refresh_view()

    def _refresh_view(self) -> None:
        """Push current game state to the view and check for game over."""
        self.view.clear_highlights()
        self._board_state = self._build_board_state()   # C++ → TileState dicts
        self.view.set_board_state(self._board_state)
        player = self.game.get_current_player()
        self.view.set_player_turn(player)
        self.view.set_pieces_remaining(self._build_pieces_remaining(player))
        self.view.set_ai_turn_enabled(self.players.get(player) is not None)
        turns = self.game.get_player_turns()
        queen_positions = self.game.get_queen_positions()
        queen_forced = (turns[player - 1] >= 2 and queen_positions[player - 1] is None)
        self.view.set_queen_forced(queen_forced)
        if winner := self.game.check_game_over():
            self.view.show_game_over(winner)
```

**Human placement flow:**
1. User clicks a piece in the tray → view emits `tray_clicked(insect)`
2. Presenter calls `game.get_valid_placements(insect)`, tells view to highlight them
3. User clicks a valid hex → view emits `placement_requested(tile_idx, pos)`
4. Presenter calls `game.apply_action(...)`, calls `_refresh_view()`

**Human move flow:**
1. User clicks a board tile → view emits `board_tile_clicked(pos)`
2. Presenter calls `game.get_valid_moves(pos)`, tells view to highlight them
3. User clicks a valid destination → view emits `move_requested(tile_idx, to_pos)`
4. Presenter calls `game.apply_action(...)`, calls `_refresh_view()`

**AI turn flow:**
1. User clicks "Next Turn" → view emits `ai_turn_requested`
2. Presenter calls `agent.select_action(game)` to get an `Action`
3. Presenter calls `game.apply_action(action)`, calls `_refresh_view()`

### GUI (View Layer)

`HiveGUI` is a `QMainWindow` that owns `BoardCanvas` and `SelectionCanvas` (Qt/OpenGL widgets). It forwards child signals up to the unified signal set that the Presenter connects to, and proxies the Presenter's push API down to the relevant child canvas. The View never calls game methods directly.

**Signals emitted by the view:**

| Signal | Trigger |
|--------|---------|
| `tray_clicked(insect: str)` | User clicks a piece button in the selection tray |
| `board_tile_clicked(pos: tuple)` | User clicks a placed tile on the board |
| `whitespace_clicked()` | User clicks a blank area in either canvas |
| `placement_requested(tile_idx: int, pos: tuple)` | User clicks a valid placement hex |
| `move_requested(tile_idx: int, to_pos: tuple)` | User clicks a valid move destination |
| `ai_turn_requested()` | User clicks "Next Turn" button |

**Methods called on the view by the presenter:**

| Method | Purpose |
|--------|---------|
| `set_board_state(board_state)` | Re-render the board from `TileState` dicts |
| `highlight_placements(positions, tile_idx, insect)` | Show valid placement hexes |
| `highlight_moves(positions, tile_idx, insect, player, source_pos)` | Show valid move destinations |
| `clear_highlights()` | Remove all overlays |
| `set_player_turn(player)` | Update turn indicator |
| `set_pieces_remaining(remaining)` | Update the selection tray counts |
| `set_queen_forced(forced)` | Restrict tray to queen-only when rule applies |
| `set_ai_turn_enabled(enabled)` | Enable/disable "Next Turn" button |
| `show_game_over(winner)` | Display result dialog |

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
