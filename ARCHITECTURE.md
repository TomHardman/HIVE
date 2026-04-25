# HIVE — System Architecture

## Overview

HIVE is a digital implementation of the Hive board game. It consists of three layers:

- **C++ game engine** — all game logic, rules, and move generation, exposed to Python via pybind11
- **Python GUI and controller** — Qt/OpenGL front-end and the presenter that mediates between the view and the engine
- **Python agents** — AI players that read directly from the engine and return actions for the controller to apply

---

## Layer Diagram

```
┌─────────────────────────────────────────────────────┐
│  View  (Qt / OpenGL)                                │
│  HiveGUI · BoardCanvas · SelectionCanvas            │
│  — passive renderer, emits signals on user input    │
│  — exposes a push API (set_*, show_*, highlight_*)  │
└──────────────────────┬──────────────────────────────┘
                       │  Qt signals (up) / push API (down)
┌──────────────────────▼──────────────────────────────┐
│  Presenter  (Python)                                │
│  GameController                                     │
│  — subscribes to view signals                       │
│  — queries Model, translates C++ types to TileState │
│  — pushes formatted state to the view               │
│  — decides when to invoke an agent                  │
│  — applies the action the agent returns             │
└───────────┬──────────────────────────┬──────────────┘
            │  apply_action / undo     │  select_action(game)
            │  (write)                 │  (trigger)
┌───────────▼──────────┐   ┌──────────▼──────────────┐
│  Model  (C++)         │◄──│  Agent  (Python)         │
│  hive_engine.Game     │   │  RandomAgent             │
│  — game state         │   │  MinimaxAgentPy          │
│  — rules & move gen   │   │  DQLAgent                │
│  — apply / undo       │   │                          │
└───────────────────────┘   │  reads Model directly    │
                            │  via get_legal_actions,  │
                            │  get_tile_positions, etc │
                            └──────────────────────────┘
```

---

## MVP Pattern

The GUI layer follows **Model-View-Presenter**: the View is fully passive and contains no game logic. It only renders what it is told to render and emits signals when the user acts. The Presenter (`GameController`) owns all decision-making — it subscribes to view signals, queries the model, translates C++ types into view-friendly `TileState` objects, and pushes the result back to the view.

The View never holds a reference to the game object.

---

## Agent Interaction

Agents sit outside the MVP triad. The flow for an AI turn:

1. The user clicks "Next Turn" → View emits `ai_turn_requested`
2. **Presenter** receives the signal and calls `agent.select_action(game)`, passing the live `hive_engine.Game` handle
3. **Agent** reads the model directly — calling `game.get_legal_actions()`, `game.get_tile_positions()`, etc. — and returns a Python `Action(tile_idx, to)` without mutating the game
4. **Presenter** translates the action and calls `game.apply_action(...)` to commit it, then pushes the new state to the view

The agent decides; the presenter applies. Agents never call `apply_action` themselves.

Agents that need to search (minimax) use `game.apply_action` / `game.undo` internally during tree traversal, but always leave the game in its original state before returning.

---

## Directory Structure

```
HIVE/
├── ARCHITECTURE.md          # This file
├── cpp/                     # C++ game engine (see cpp/ARCHITECTURE.md)
│   └── ARCHITECTURE.md
├── py/                      # Legacy Python implementation (see py/CLAUDE.md)
└── py2/                     # Active Python layer (see py2/ARCHITECTURE.md)
    └── ARCHITECTURE.md
```

See each subdirectory's `ARCHITECTURE.md` for detailed file structure, engine API reference, and agent implementations.
