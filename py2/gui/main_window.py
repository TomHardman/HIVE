from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal

from .board_canvas import BoardCanvas
from .selection_canvas import SelectionCanvas
from .side_panel import SidePanel

from controller.game_controller import TileState


class HiveGUI(QtWidgets.QMainWindow):
    """
    Top-level window.  Owns BoardCanvas, SelectionCanvas, and SidePanel, wires
    their signals to the unified set exposed here, and provides the controller API.

    The GameController connects to these signals and calls these methods —
    it never touches child widgets directly.
    """

    # ── Signals forwarded from child widgets (controller connects here) ──
    tray_clicked        = pyqtSignal(str)            # insect name clicked in tray
    board_tile_clicked  = pyqtSignal(tuple)          # (q, r) of board tile clicked
    whitespace_clicked  = pyqtSignal()               # blank area clicked in either canvas
    move_requested      = pyqtSignal(int, tuple)     # tile_idx, to_pos
    placement_requested = pyqtSignal(int, tuple)     # tile_idx, to_pos
    ai_turn_requested   = pyqtSignal()               # "Next Turn" button

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle('HIVE')
        self.resize(1200, 850)

        # ── Child widgets ──
        self.board_canvas = BoardCanvas(self)
        self.selection_canvas = SelectionCanvas(self)
        self.side_panel = SidePanel(self)

        # Vertical splitter: board on top, selection tray below
        game_splitter = QtWidgets.QSplitter(Qt.Vertical)
        game_splitter.addWidget(self.board_canvas)
        game_splitter.addWidget(self.selection_canvas)
        game_splitter.setStretchFactor(0, 1)
        game_splitter.setStretchFactor(1, 0)

        # Horizontal splitter: game area left, side panel right
        main_splitter = QtWidgets.QSplitter(Qt.Horizontal)
        main_splitter.addWidget(game_splitter)
        main_splitter.addWidget(self.side_panel)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 0)
        self.setCentralWidget(main_splitter)

        # ── Forward child signals ──
        self.selection_canvas.tray_clicked.connect(self.tray_clicked)
        self.board_canvas.board_tile_clicked.connect(self.board_tile_clicked)
        self.board_canvas.whitespace_clicked.connect(self.whitespace_clicked)
        self.selection_canvas.whitespace_clicked.connect(self.whitespace_clicked)
        self.board_canvas.move_requested.connect(self.move_requested)
        self.board_canvas.placement_requested.connect(self.placement_requested)
        self.side_panel.next_turn_clicked.connect(self.ai_turn_requested)

    # ── Controller-facing API ──

    def set_board_state(self, board_state: dict[tuple[int, int], list[TileState]]) -> None:
        """board_state: (q,r) → list[TileState]"""
        self.board_canvas.set_board_state(board_state)

    def highlight_moves(self, positions: list[tuple[int, int]], tile_idx: int,
                        insect: str | None = None, player: int | None = None,
                        source_pos: tuple[int, int] | None = None) -> None:
        self.board_canvas.highlight_moves(positions, tile_idx, insect, player, source_pos)

    def highlight_placements(self, positions: list[tuple[int, int]], tile_idx: int | None = None,
                             insect: str | None = None) -> None:
        self.board_canvas.highlight_placements(positions, tile_idx, insect)
        if insect:
            self.board_canvas.set_drag_piece(insect, self.board_canvas._player_turn)

    def clear_highlights(self) -> None:
        self.board_canvas.clear_highlights()

    def set_player_turn(self, player: int) -> None:
        self.board_canvas._player_turn = player
        self.selection_canvas.set_player_turn(player)

    def set_pieces_remaining(self, remaining: dict[str, int]) -> None:
        """remaining: insect → count for the current player."""
        self.selection_canvas.set_pieces_remaining(remaining)

    def set_queen_forced(self, forced: bool) -> None:
        self.selection_canvas.set_queen_forced(forced)

    def set_ai_turn_enabled(self, enabled: bool) -> None:
        self.side_panel.set_next_turn_enabled(enabled)

    def add_turn_entry(self, player: int, elapsed: float) -> None:
        self.side_panel.add_turn_entry(player, elapsed)

    def show_game_over(self, winner: int) -> None:
        if winner == 0:
            msg = "Draw!"
        else:
            msg = f"Player {winner} wins!"
        QtWidgets.QMessageBox.information(self, "Game Over", msg)
