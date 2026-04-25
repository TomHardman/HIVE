import time
from dataclasses import dataclass

import hive_engine

from agents.base import Agent

# Insect enum value → display string mapping.
# Matches the C++ Insect enum order: ANT=0, BEETLE=1, GRASSHOPPER=2, SPIDER=3, QUEEN=4
INSECT_NAMES: dict[int, str] = {0: 'ant', 1: 'beetle', 2: 'grasshopper', 3: 'spider', 4: 'queen'}

# tile_idx → insect name (matches C++ TILE_IDX_MAP)
TILE_IDX_TO_INSECT: dict[int, str] = {
    0: 'queen',
    1: 'spider', 2: 'spider',
    3: 'beetle', 4: 'beetle',
    5: 'ant', 6: 'ant', 7: 'ant',
    8: 'grasshopper', 9: 'grasshopper', 10: 'grasshopper',
}


@dataclass
class TileState:
    """Lightweight rendering description of a tile — no C++ objects."""
    player: int
    insect: str   # 'ant', 'beetle', 'grasshopper', 'spider', 'queen'
    tile_idx: int
    position: tuple[int, int]


class GameController:
    """
    Mediates between the C++ game engine and the Qt view.

    Responsibilities:
    - Connect view signals to game operations
    - Drive agent turns
    - Push updated state to the view after each action
    """

    def __init__(self, game: hive_engine.Game, view, player1: Agent | None = None,
                 player2: Agent | None = None) -> None:
        """
        game    : hive_engine.Game instance
        view    : HiveGUI instance
        player1 : Agent | None (None = human)
        player2 : Agent | None (None = human)
        """
        self.game: hive_engine.Game = game
        self.view = view
        self.players: dict[int, Agent | None] = {1: player1, 2: player2}

        # Connect view signals
        view.tray_clicked.connect(self.on_tray_clicked)
        view.board_tile_clicked.connect(self.on_board_tile_clicked)
        view.whitespace_clicked.connect(self.on_whitespace_clicked)
        view.placement_requested.connect(self.on_placement_requested)
        view.move_requested.connect(self.on_move_requested)
        view.ai_turn_requested.connect(self.on_ai_turn_requested)

        # Human interaction state
        self._selected_piece_idx: int | None = None
        self._selected_tile_pos: tuple[int, int] | None = None
        self._board_state: dict[tuple[int, int], list[TileState]] = {}

        self._refresh_view()

    # ============= Signal handlers =============

    def on_tray_clicked(self, insect: str) -> None:
        """User clicked a piece button in the selection canvas."""
        self._selected_tile_pos = None
        tile_idx = self._resolve_placement_tile_idx(insect)
        self._selected_piece_idx = tile_idx
        placements = self._get_valid_placements_for_idx(tile_idx)
        self.view.highlight_placements(placements, tile_idx, insect)

    def on_whitespace_clicked(self) -> None:
        """User clicked a blank area in either canvas — clear any active selection."""
        self._selected_piece_idx = None
        self._selected_tile_pos = None
        self.view.clear_highlights()

    def on_board_tile_clicked(self, pos: tuple[int, int]) -> None:
        """User clicked a tile on the board canvas. pos is the (q, r) hex coordinate."""
        self._selected_piece_idx = None
        self._selected_tile_pos = pos

        tile_states = self._board_state.get(pos, [])
        tile_idx = tile_states[-1].tile_idx if tile_states else None
        insect = tile_states[-1].insect if tile_states else None
        player = tile_states[-1].player if tile_states else None

        moves = [(p.q, p.r) for p in self.game.get_valid_moves(_pos(pos))]
        if moves:
            self.view.highlight_moves(moves, tile_idx, insect, player, pos)
        else:
            self._selected_tile_pos = None
            self.view.clear_highlights()

    def on_placement_requested(self, tile_idx: int, pos: tuple[int, int]) -> None:
        """User clicked a valid placement hex."""
        if tile_idx is None:
            return
        self.game.apply_action(_cpp_action(tile_idx, pos))
        self._selected_piece_idx = None
        self._refresh_view()

    def on_move_requested(self, tile_idx: int, to_pos: tuple[int, int]) -> None:
        """User clicked a valid move destination."""
        if tile_idx is None:
            return
        self.game.apply_action(_cpp_action(tile_idx, to_pos))
        self._selected_tile_pos = None
        self._refresh_view()

    def on_ai_turn_requested(self) -> None:
        """User clicked Next Turn — execute one AI move."""
        player = self.game.get_current_player()
        agent = self.players.get(player)
        if agent is None:
            return
        t0 = time.perf_counter()
        action = agent.select_action(self.game)
        elapsed = time.perf_counter() - t0
        if action is None:
            return
        self.game.apply_action(_cpp_action(action.tile_idx, action.to))
        self.view.add_turn_entry(player, elapsed)
        self._refresh_view()

    # ============= Internal helpers =============

    def _refresh_view(self) -> None:
        """Push current game state to the view and check for game over."""
        self.view.clear_highlights()
        self._board_state = self._build_board_state()
        self.view.set_board_state(self._board_state)
        player = self.game.get_current_player()
        self.view.set_player_turn(player)
        self.view.set_pieces_remaining(self._build_pieces_remaining(player))

        # Update Next Turn button: enabled iff current player is an AI
        self.view.set_ai_turn_enabled(self.players.get(player) is not None)

        # Queen-must-be-placed rule: turn 3 (0-indexed) without queen → force queen only
        turns: list[int] = self.game.get_player_turns()
        queen_positions = self.game.get_queen_positions()
        queen_forced = (turns[player - 1] >= 2 and queen_positions[player - 1] is None)
        self.view.set_queen_forced(queen_forced)

        if winner := self.game.check_game_over():
            self.view.show_game_over(winner)

    def _build_board_state(self) -> dict[tuple[int, int], list[TileState]]:
        """
        Convert C++ tile_positions into a dict of (q,r) → list[TileState].
        Isolates the view from pybind11 objects.
        """
        result: dict[tuple[int, int], list[TileState]] = {}
        for pos, tiles in self.game.get_tile_positions().items():
            coord: tuple[int, int] = (pos.q, pos.r)
            result[coord] = []
            for tile in tiles:
                insect_name = INSECT_NAMES.get(int(tile.insect), 'unknown')
                tile_idx = _tile_to_idx(int(tile.insect), tile.id)
                result[coord].append(TileState(
                    player=tile.player,
                    insect=insect_name,
                    tile_idx=tile_idx,
                    position=coord,
                ))
        return result

    def _build_pieces_remaining(self, player: int) -> dict[str, int]:
        """Return insect → count for tiles still in the given player's hand."""
        hand = self.game.get_player_hands()[player - 1]
        counts: dict[str, int] = {}
        for tile in hand:
            name = INSECT_NAMES.get(int(tile.insect), 'unknown')
            counts[name] = counts.get(name, 0) + 1
        return counts

    def _resolve_placement_tile_idx(self, insect: str) -> int | None:
        """Return the tile_idx for a placement of the given insect type."""
        player = self.game.get_current_player()
        hand = self.game.get_player_hands()[player - 1]
        insect_enum = _insect_name_to_enum(insect)
        max_id = -1
        for tile in hand:
            if tile.insect == insect_enum:
                max_id = max(max_id, tile.id)
        if max_id == -1:
            return None
        return _tile_to_idx(insect_enum, max_id)

    def _get_valid_placements_for_idx(self, tile_idx: int | None) -> list[tuple[int, int]]:
        insect_str = TILE_IDX_TO_INSECT.get(tile_idx, '') if tile_idx is not None else ''
        insect_enum = _insect_name_to_enum(insect_str)
        positions = self.game.get_valid_placements(insect_enum)
        return [(p.q, p.r) for p in positions]


# ============= Module-level helpers =============

# TILE_IDX_MAP (mirrors C++ TILE_IDX_MAP)
_TILE_IDX_MAP: list[tuple[int, int]] = [
    (4, 1),  # 0 = queen   (Insect::QUEEN=4)
    (3, 1),  # 1 = spider1 (Insect::SPIDER=3)
    (3, 2),  # 2 = spider2
    (1, 1),  # 3 = beetle1 (Insect::BEETLE=1)
    (1, 2),  # 4 = beetle2
    (0, 1),  # 5 = ant1    (Insect::ANT=0)
    (0, 2),  # 6 = ant2
    (0, 3),  # 7 = ant3
    (2, 1),  # 8 = gh1     (Insect::GRASSHOPPER=2)
    (2, 2),  # 9 = gh2
    (2, 3),  # 10 = gh3
]

def _tile_to_idx(insect_enum: hive_engine.Insect | int, tile_id: int) -> int:
    insect_int = int(insect_enum)   # works for both plain int and hive_engine.Insect
    for i, (ie, tid) in enumerate(_TILE_IDX_MAP):
        if ie == insect_int and tid == tile_id:
            return i
    return -1

_INSECT_NAME_TO_ENUM: dict[str, hive_engine.Insect] = {
    'ant':         hive_engine.Insect.ANT,
    'beetle':      hive_engine.Insect.BEETLE,
    'grasshopper': hive_engine.Insect.GRASSHOPPER,
    'spider':      hive_engine.Insect.SPIDER,
    'queen':       hive_engine.Insect.QUEEN,
}

def _insect_name_to_enum(name: str) -> hive_engine.Insect:
    return _INSECT_NAME_TO_ENUM.get(name)

def _pos(coord: tuple[int, int]) -> hive_engine.Position:
    return hive_engine.Position(coord[0], coord[1])

def _cpp_action(tile_idx: int, to: tuple[int, int]) -> hive_engine.Action:
    return hive_engine.Action(tile_idx, hive_engine.Position(to[0], to[1]))
