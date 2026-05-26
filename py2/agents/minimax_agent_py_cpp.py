from __future__ import annotations

import heapq
import math
from typing import TYPE_CHECKING
from .minimax_utils import HEX_NEIGHBORS, MinimaxParams

import hive_engine

from .base import Agent, Action


class MinimaxAgentPyCpp(Agent):
    """
    Python agent that achieves parallelism with python multithreading, using python
    bindings that release the GIL to achieve true concurrency
    """
    def __init__(self, params: MinimaxParams) -> None:
        self.params = params
    
    def select_action(self, game: hive_engine.Game) -> Action | None:
        raise NotImplementedError('Not yet implemented')