# C++ Engine Architecture

The C++ engine implements all game logic and is exposed to Python via pybind11 as the `hive_engine` module. Python never reimplements rules — it only calls into this layer.

---

## Component Diagram

```
┌──────────────────────────────────────────────────────┐
│  bindings.cpp  (pybind11 bridge)                     │
│  — exposes Game, Position, HiveTile, Action,         │
│    Insect to Python as the hive_engine module        │
└────────────────────────┬─────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────┐
│  Game  (Game.h / Game.cpp)                           │
│  — owns all mutable game state                       │
│  — apply_action / undo for tree search               │
│  — delegates move generation to MoveFetcher          │
└──────────────────┬───────────────────────────────────┘
                   │  read-only tile_positions reference
┌──────────────────▼───────────────────────────────────┐
│  MoveFetcher namespace  (MoveFetcher.h / .cpp)       │
│  — stateless, pure functions                         │
│  — dispatches to per-insect move functions           │
│  — shared validity helpers (slide rule, hive rule)   │
└──────────────────────────────────────────────────────┘

  Supporting types (header-only):
  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐
  │  Position   │  │  HiveTile   │  │  Insect (enum)  │
  │  (q, r)     │  │  player     │  │  ANT BEETLE     │
  │  hashable   │  │  insect     │  │  GRASSHOPPER    │
  │  comparable │  │  id         │  │  SPIDER QUEEN   │
  └─────────────┘  └─────────────┘  └─────────────────┘
```

---

## Game

`Game` is the only stateful class. All game state lives here:

| Member | Type | Description |
|--------|------|-------------|
| `tile_positions_` | `unordered_map<Position, vector<HiveTile>>` | Board stacks, bottom-to-top |
| `player_hands_` | `array<unordered_set<HiveTile>, 2>` | Unplaced pieces per player |
| `queen_positions_` | `array<optional<Position>, 2>` | Cached queen locations |
| `player_turns_` | `array<int, 2>` | Moves made by each player |
| `max_turns_` | `int` | Turn limit (-1 = unlimited) |
| `simplified_game_` | `bool` | 3-surrounding = loss instead of 6 |

**Mutation interface** — the only two methods that change state:

| Method | Returns | Purpose |
|--------|---------|---------|
| `apply_action(action)` | `optional<Position>` | Apply a placement or move. Returns original position for moves (needed to undo), `nullopt` for placements. |
| `undo(action, original_pos)` | `void` | Restore state exactly as it was before `apply_action`. |

This apply/undo pair is the mechanism minimax agents use for in-place tree traversal without copying the game object.

**Query interface** (all `const`, no mutation):

| Method | Returns |
|--------|---------|
| `getValidPlacements(insect)` | Positions where current player may place that insect |
| `getValidMoves(position)` | Destinations for the top tile at a position |
| `getLegalActions()` | All legal `Action`s for the current player |
| `checkGameOver()` | `0` ongoing, `1` p1 wins, `2` p2 wins |
| `getCurrentPlayer()` | `1` or `2` |
| `getTilePositions()` | Read-only reference to board stacks |
| `getPlayerHands()` | Read-only reference to both hands |
| `getQueenPositions()` | Read-only reference to queen positions |
| `getPlayerTurns()` | Read-only reference to turn counters |

---

## Action Representation

All actions — placements and movements — are represented as `Action { tile_idx, to }`.

`tile_idx` is a single integer (0–10) that identifies a specific piece instance via `TILE_IDX_MAP`:

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

Whether an action is a placement or movement is determined at runtime — if the identified piece is in the player's hand, it is placed; if it is on the board, it is moved.

This representation is shared across the C++ engine, the Python controller, and all agents.

---

## MoveFetcher

A stateless namespace of pure functions. `Game` calls `MoveFetcher::getValidMoves(position, tile, tile_positions)`, which dispatches to the appropriate per-insect function:

| Function | Movement rule |
|----------|--------------|
| `getQueenMoves` | Slide 1 space around the hive perimeter |
| `getAntMoves` | BFS to any reachable perimeter space |
| `getBeetleMoves` | 1 step; may climb onto occupied spaces |
| `getGrasshopperMoves` | Jump in a straight line over ≥1 piece, land on first empty space |
| `getSpiderMoves` | Exactly 3 perimeter steps without backtracking |

Shared validity helpers:

| Helper | Purpose |
|--------|---------|
| `wouldBreakHive(pos)` | One-hive rule: would removing this piece disconnect the board? |
| `canSlideInto(pos, neighbors, idx)` | Slide rule: is there enough space to enter the target hex? |
| `isCovered(pos, tile)` | Is this tile buried under a beetle? |
| `getNeighbors(pos)` | The 6 axial-coordinate neighbours of a hex |

---

## pybind11 Binding

`bindings.cpp` exposes `Game`, `Position`, `HiveTile`, `Action`, and `Insect` to Python. All C++ references returned from state accessors use `reference_internal` policy — Python receives a view into the C++ object, not a copy. Mutating game state from Python after calling a getter invalidates the reference.

---

## File Structure

```
cpp/
├── ARCHITECTURE.md      # This file
├── CMakeLists.txt       # Build configuration
├── bindings.cpp         # pybind11 bridge → hive_engine Python module
├── Game.h / Game.cpp    # Main game state and action interface
├── MoveFetcher.h / .cpp # Stateless move generation per insect
├── Pieces.h             # HiveTile struct and Insect enum
├── Position.h           # Position struct (q, r) with hash
└── example.cpp          # Standalone C++ usage example
```
