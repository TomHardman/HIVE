"""
Type stubs for minimax_engine — the C++ beam-minimax search exposed via pybind11.

These stubs exist solely for static analysis (Pylance / Pyright).
The actual implementation lives in minimax_engine.cpython-*.so.

Requires hive_engine to be imported first (Game and Action types must be
registered before minimax_select_action can return them).
"""

from __future__ import annotations

from hive_engine import Action, Game

# ---------------------------------------------------------------------------
# MinimaxParams
# ---------------------------------------------------------------------------

class MinimaxParams:
    depth: int
    beam_width: int
    queen_surrounding_reward: float
    ownership_reward: float
    win_reward: float
    mp_reward: float

    def __init__(self) -> None: ...
    def __repr__(self) -> str: ...

# ---------------------------------------------------------------------------
# minimax_select_action
# ---------------------------------------------------------------------------

def minimax_select_action(game: Game, params: MinimaxParams) -> Action | None:
    """Run beam-search minimax from the current game state.

    Returns the best Action for the current player, or None if there are no
    legal moves.

    The game object is mutated during search (apply_action / undo) but is
    always restored to its original state before returning.
    """
    ...
