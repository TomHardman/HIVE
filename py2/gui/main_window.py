from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal

from .board_canvas import BoardCanvas
from typing import Optional
from .selection_canvas import SelectionCanvas


class HiveGUI(QtWidgets.QMainWindow):
    """
    Top-level window.  Owns BoardCanvas and SelectionCanvas, wires their
    signals to the unified set exposed here, and provides the controller API.

    The GameController connects to these signals and calls these methods —
    it never touches BoardCanvas or SelectionCanvas directly.
    """

    # ── Signals forwarded from child canvases (controller connects here) ──
    tray_clicked        = pyqtSignal(str)            # insect name clicked in tray
    board_tile_clicked  = pyqtSignal(tuple)          # (q, r) of board tile clicked
    whitespace_clicked  = pyqtSignal()               # blank area clicked in either canvas
    move_requested      = pyqtSignal(int, tuple)     # tile_idx, to_pos
    placement_requested = pyqtSignal(int, tuple)     # tile_idx, to_pos
    ai_turn_requested   = pyqtSignal()               # "Next Turn" button

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('HIVE')
        self.resize(1000, 850)

        # ── Child widgets ──
        self.board_canvas = BoardCanvas(self)
        self.selection_canvas = SelectionCanvas(self)

        # Give board_canvas a reference so placement_requested can bubble up
        self.board_canvas.parent = self

        splitter = QtWidgets.QSplitter(Qt.Vertical)
        splitter.addWidget(self.board_canvas)
        splitter.addWidget(self.selection_canvas)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        self.setCentralWidget(splitter)

        # ── Toolbar ──
        toolbar = self.addToolBar("Controls")
        self._next_turn_btn = QtWidgets.QAction("Next Turn", self)
        self._next_turn_btn.setEnabled(False)
        self._next_turn_btn.triggered.connect(self.ai_turn_requested)
        toolbar.addAction(self._next_turn_btn)

        # ── Forward child signals ──
        self.selection_canvas.tray_clicked.connect(self.tray_clicked)
        self.board_canvas.board_tile_clicked.connect(self.board_tile_clicked)
        self.board_canvas.whitespace_clicked.connect(self.whitespace_clicked)
        self.selection_canvas.whitespace_clicked.connect(self.whitespace_clicked)
        self.board_canvas.move_requested.connect(self.move_requested)

    # ── Controller-facing API ──

    def set_board_state(self, board_state: dict):
        """board_state: (q,r) → list[TileState]"""
        self.board_canvas.set_board_state(board_state)

    def highlight_moves(self, positions: list, tile_idx: int):
        self.board_canvas.highlight_moves(positions, tile_idx)

    def highlight_placements(self, positions: list, tile_idx: int = None,
                             insect: Optional[str] = None):
        self.board_canvas.highlight_placements(positions, tile_idx, insect)

    def clear_highlights(self):
        self.board_canvas.clear_highlights()

    def set_player_turn(self, player: int):
        self.board_canvas._player_turn = player
        self.selection_canvas.set_player_turn(player)

    def set_pieces_remaining(self, remaining: dict):
        """remaining: insect → count for the current player."""
        self.selection_canvas.set_pieces_remaining(remaining)

    def set_ai_turn_enabled(self, enabled: bool):
        self._next_turn_btn.setEnabled(enabled)

    def show_game_over(self, winner: int):
        if winner == 0:
            msg = "Draw!"
        else:
            msg = f"Player {winner} wins!"
        QtWidgets.QMessageBox.information(self, "Game Over", msg)
