from __future__ import annotations

from typing import TYPE_CHECKING
from .minimax_utils import MinimaxParams

import hive_engine

from .base import Agent, Action


class MinimaxAgentCpp(Agent):
    """
    Wrapper around native C++ minimax search
    """
    def __init__(self, params: MinimaxParams) -> None:
        self.params = params
    
    def select_action(self, game: hive_engine.Game) -> Action | None:
        raise NotImplementedError('Not yet implemented')