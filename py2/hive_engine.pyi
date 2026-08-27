"""
Type stubs for hive_engine — the C++ game engine exposed via pybind11.

These stubs exist solely for static analysis (Pylance / Pyright).
The actual implementation lives in hive_engine.cpython-*.so.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Iterator

# ---------------------------------------------------------------------------
# Position
# ---------------------------------------------------------------------------

class Position:
    q: int
    r: int

    def __init__(self, q: int, r: int) -> None: ...
    def __eq__(self, other: object) -> bool: ...
    def __hash__(self) -> int: ...
    def __repr__(self) -> str: ...

# ---------------------------------------------------------------------------
# Insect
# ---------------------------------------------------------------------------

class Insect(IntEnum):
    # Members must be *assigned* (not just annotated) so static analysis types
    # `Insect.ANT` as `Insect` rather than a bare `int`. Values mirror the C++
    # Insect enum order.
    ANT = 0
    BEETLE = 1
    GRASSHOPPER = 2
    SPIDER = 3
    QUEEN = 4

# ---------------------------------------------------------------------------
# HiveTile
# ---------------------------------------------------------------------------

class HiveTile:
    player: int    # 1 or 2
    insect: Insect
    id: int        # unique per (player, insect) — e.g. Ant #1, Ant #2, Ant #3

    def __init__(self, player: int, insect: Insect, id: int) -> None: ...
    def __eq__(self, other: object) -> bool: ...
    def __hash__(self) -> int: ...
    def __repr__(self) -> str: ...

# ---------------------------------------------------------------------------
# Action
# ---------------------------------------------------------------------------

class Action:
    tile_idx: int   # 0–10, identifies a specific piece via TILE_IDX_MAP
    to: Position    # destination for placement or movement

    def __init__(self, tile_idx: int, to: Position) -> None: ...
    def __eq__(self, other: object) -> bool: ...
    def __repr__(self) -> str: ...

# ---------------------------------------------------------------------------
# Game
# ---------------------------------------------------------------------------

class Game:
    def __init__(
        self,
        max_turns: int = -1,
        simplified_game: bool = False,
    ) -> None: ...

    # --- Queries (all const, no mutation) ---

    def get_valid_placements(self, insect: Insect) -> list[Position]:
        """Valid placement positions for the current player and given insect type."""
        ...

    def get_valid_moves(self, position: Position) -> list[Position]:
        """Valid move destinations for the top tile at *position*.

        Returns an empty list if there is no tile there, it belongs to the
        wrong player, the queen has not yet been placed, or the tile is covered.
        """
        ...

    def get_legal_actions(self) -> list[Action]:
        """All legal actions for the current player."""
        ...

    def check_game_over(self) -> int:
        """Returns -1 (ongoing), 0 (draw), 1 (player 1 wins), or 2 (player 2 wins)."""
        ...

    def get_current_player(self) -> int:
        """Returns the current player (1 or 2)."""
        ...

    # --- Mutations ---

    def apply_action(self, action: Action) -> Position | None:
        """Apply *action* to the game state.

        Returns the tile's original board position if the action was a movement
        (required to call undo), or None if it was a placement.
        """
        ...

    def undo(self, action: Action, original_pos: Position | None) -> None:
        """Undo a previously applied action.

        *original_pos* must be the exact value returned by apply_action for
        that action.
        """
        ...

    # --- State access (reference_internal — do not hold after mutating game) ---

    def get_tile_positions(self) -> dict[Position, list[HiveTile]]:
        """Board stacks: Position → [bottom, ..., top].

        The returned dict is a view into the C++ object; do not hold a
        reference across an apply_action / undo call.
        """
        ...

    def get_player_hands(self) -> list[set[HiveTile]]:
        """[player_1_hand, player_2_hand] — unplaced pieces per player.

        A 2-element list (C++ std::array<..., 2> → Python list).
        """
        ...

    def get_queen_positions(self) -> list[Position | None]:
        """[p1_queen_pos, p2_queen_pos] — None if not yet placed.

        A 2-element list (C++ std::array<..., 2> → Python list).
        """
        ...

    def get_player_turns(self) -> list[int]:
        """[p1_turns, p2_turns] — moves made by each player so far.

        A 2-element list (C++ std::array<int, 2> → Python list).
        """
        ...
