from dataclasses import dataclass
from typing import Optional

import hive_engine

# Insect enum value → display string mapping.
# Matches the C++ Insect enum order: ANT=0, BEETLE=1, GRASSHOPPER=2, SPIDER=3, QUEEN=4
INSECT_NAMES = {0: 'ant', 1: 'beetle', 2: 'grasshopper', 3: 'spider', 4: 'queen'}

# tile_idx → insect name (matches C++ TILE_IDX_MAP)
TILE_IDX_TO_INSECT = {
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
    position: tuple  # (q, r)


class GameController:
    """
    Mediates between the C++ game engine and the Qt view.

    Responsibilities:
    - Connect view signals to game operations
    - Drive agent turns
    - Push updated state to the view after each action
    """

    def __init__(self, game, view, player1=None, player2=None):
        """
        game    : hive_engine.Game instance
        view    : HiveGUI instance
        player1 : Agent | None (None = human)
        player2 : Agent | None (None = human)
        """
        self.game = game
        self.view = view
        self.players = {1: player1, 2: player2}

        # Connect view signals
        view.tray_clicked.connect(self.on_tray_clicked)
        view.board_tile_clicked.connect(self.on_board_tile_clicked)
        view.whitespace_clicked.connect(self.on_whitespace_clicked)
        view.placement_requested.connect(self.on_placement_requested)
        view.move_requested.connect(self.on_move_requested)
        view.ai_turn_requested.connect(self.on_ai_turn_requested)

        # Human interaction state
        self._selected_piece_idx: Optional[int] = None   # tile_idx of piece being placed
        self._selected_tile_pos: Optional[tuple] = None  # board pos of tile being moved
        self._board_state: dict = {}   # (q,r) → list[TileState]; kept in sync by _refresh_view

        self._refresh_view()

    # ============= Signal handlers =============

    def on_tray_clicked(self, insect: str):
        """User clicked a piece button in the selection canvas."""
        self._selected_tile_pos = None
        tile_idx = self._resolve_placement_tile_idx(insect)
        self._selected_piece_idx = tile_idx
        placements = self._get_valid_placements_for_idx(tile_idx)
        self.view.highlight_placements(placements, tile_idx, insect)

    def on_whitespace_clicked(self):
        """User clicked a blank area in either canvas — clear any active selection."""
        self._selected_piece_idx = None
        self._selected_tile_pos = None
        self.view.clear_highlights()

    def on_board_tile_clicked(self, pos: tuple):
        """User clicked a tile on the board canvas. pos is the (q, r) hex coordinate."""
        self._selected_piece_idx = None
        self._selected_tile_pos = pos

        tile_states = self._board_state.get(pos, [])
        tile_idx = tile_states[-1].tile_idx if tile_states else None

        moves = [(p.q, p.r) for p in self.game.get_valid_moves(_pos(pos))]
        if moves:
            self.view.highlight_moves(moves, tile_idx)
        else:
            self._selected_tile_pos = None
            self.view.clear_highlights()

    def on_placement_requested(self, tile_idx: int, pos: tuple):
        """User clicked a valid placement hex."""
        if tile_idx is None:
            return
        self.game.apply_action(_cpp_action(tile_idx, pos))
        self._selected_piece_idx = None
        self._refresh_view()

    def on_move_requested(self, tile_idx: int, to_pos: tuple):
        """User clicked a valid move destination."""
        if tile_idx is None:
            return
        self.game.apply_action(_cpp_action(tile_idx, to_pos))
        self._selected_tile_pos = None
        self._refresh_view()

    def on_ai_turn_requested(self):
        """User clicked Next Turn — execute one AI move."""
        player = self.game.get_current_player()
        agent = self.players.get(player)
        if agent is None:
            return
        action = agent.select_action(self.game)
        if action is None:
            return
        self.game.apply_action(_cpp_action(action.tile_idx, action.to))
        self._refresh_view()

    # ============= Internal helpers =============

    def _refresh_view(self):
        """Push current game state to the view and check for game over."""
        self.view.clear_highlights()
        self._board_state = self._build_board_state()
        self.view.set_board_state(self._board_state)
        player = self.game.get_current_player()
        self.view.set_player_turn(player)
        self.view.set_pieces_remaining(self._build_pieces_remaining(player))

        # Update Next Turn button: enabled iff current player is an AI
        self.view.set_ai_turn_enabled(self.players.get(player) is not None)

        if winner := self.game.check_game_over():
            self.view.show_game_over(winner)

    def _build_board_state(self) -> dict:
        """
        Convert C++ tile_positions into a dict of (q,r) → list[TileState].
        Isolates the view from pybind11 objects.
        """
        result = {}
        for pos, tiles in self.game.get_tile_positions().items():
            coord = (pos.q, pos.r)
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

    def _build_pieces_remaining(self, player: int) -> dict:
        """Return insect → count for tiles still in the given player's hand."""
        hand = self.game.get_player_hands()[player - 1]
        counts: dict = {}
        for tile in hand:
            name = INSECT_NAMES.get(int(tile.insect), 'unknown')
            counts[name] = counts.get(name, 0) + 1
        return counts

    def _resolve_placement_tile_idx(self, insect: str) -> Optional[int]:
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

    def _get_valid_placements_for_idx(self, tile_idx: int) -> list:
        insect_str = TILE_IDX_TO_INSECT.get(tile_idx, '')
        insect_enum = _insect_name_to_enum(insect_str)
        positions = self.game.get_valid_placements(insect_enum)
        return [(p.q, p.r) for p in positions]


# ============= Module-level helpers =============

# TILE_IDX_MAP (mirrors C++ TILE_IDX_MAP)
_TILE_IDX_MAP = [
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

def _tile_to_idx(insect_enum, tile_id: int) -> int:
    insect_int = int(insect_enum)   # works for both plain int and hive_engine.Insect
    for i, (ie, tid) in enumerate(_TILE_IDX_MAP):
        if ie == insect_int and tid == tile_id:
            return i
    return -1

_INSECT_NAME_TO_ENUM = {
    'ant':         hive_engine.Insect.ANT,
    'beetle':      hive_engine.Insect.BEETLE,
    'grasshopper': hive_engine.Insect.GRASSHOPPER,
    'spider':      hive_engine.Insect.SPIDER,
    'queen':       hive_engine.Insect.QUEEN,
}

def _insect_name_to_enum(name: str) -> hive_engine.Insect:
    return _INSECT_NAME_TO_ENUM.get(name)

def _pos(coord: tuple) -> hive_engine.Position:
    return hive_engine.Position(coord[0], coord[1])

def _cpp_action(tile_idx: int, to: tuple) -> hive_engine.Action:
    return hive_engine.Action(tile_idx, hive_engine.Position(to[0], to[1]))
