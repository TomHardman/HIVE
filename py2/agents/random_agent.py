import random
from .base import Agent, Action


class RandomAgent(Agent):
    """Selects uniformly at random from legal actions."""

    def select_action(self, game) -> Action:
        actions = game.get_legal_actions()
        if not actions:
            return None
        a = random.choice(actions)
        # pybind11 exposes Action as an object with .tile_idx and .to
        return Action(tile_idx=a.tile_idx, to=(a.to.q, a.to.r))
