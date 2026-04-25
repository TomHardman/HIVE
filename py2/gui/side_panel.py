from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont


class SidePanel(QtWidgets.QWidget):
    """
    Right-hand control panel.

    Contains the Next Turn button and a log of AI turn durations.
    The presenter calls set_next_turn_enabled and add_turn_entry — this
    widget never touches the game object directly.
    """

    next_turn_clicked = pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(200)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(8)

        # ── Next Turn button ──────────────────────────────────────────────
        self._next_turn_btn = QtWidgets.QPushButton("Next Turn")
        self._next_turn_btn.setEnabled(False)
        self._next_turn_btn.clicked.connect(self.next_turn_clicked)
        layout.addWidget(self._next_turn_btn)

        # ── Separator ─────────────────────────────────────────────────────
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(separator)

        # ── AI Timing header ──────────────────────────────────────────────
        header = QtWidgets.QLabel("AI Timing")
        font = QFont()
        font.setBold(True)
        header.setFont(font)
        layout.addWidget(header)

        # ── Turn log ──────────────────────────────────────────────────────
        self._log = QtWidgets.QListWidget()
        self._log.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self._log.setFocusPolicy(self._log.focusPolicy() & ~2)  # no keyboard focus
        layout.addWidget(self._log, stretch=1)

    # ── Controller-facing API ─────────────────────────────────────────────

    def set_next_turn_enabled(self, enabled: bool) -> None:
        self._next_turn_btn.setEnabled(enabled)

    def add_turn_entry(self, player: int, elapsed: float) -> None:
        """Prepend a new timing entry (newest at top)."""
        self._log.insertItem(0, f"P{player}  {elapsed:.2f}s")

    def clear_entries(self) -> None:
        self._log.clear()
