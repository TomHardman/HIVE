from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Action:
    """
    Unified action type returned by all agents.

    tile_idx identifies a specific piece instance (0-10) via the TILE_IDX_MAP
    defined in the C++ engine:
      queen=0, spider1=1, spider2=2, beetle1=3, beetle2=4,
      ant1=5, ant2=6, ant3=7, grasshopper1=8, grasshopper2=9, grasshopper3=10

    to is the destination hex coordinate (q, r).

    Whether the action is a placement or movement is determined at runtime by
    the engine — if the piece is in hand it is placed, if on the board it is moved.
    """
    tile_idx: int
    to: tuple


class Agent(ABC):
    """Base class for all Hive agents."""

    @abstractmethod
    def select_action(self, game) -> Action:
        """
        Return the chosen action without applying it to the game.
        The controller is responsible for calling game.apply_action(action).
        """
        pass
