from dataclasses import dataclass

HEX_NEIGHBORS: list[tuple[int, int]] = [(0, 1), (1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1)]


@dataclass
class MinimaxParams:
    depth: int = 3
    beam_width: int = 3
    queen_surrounding_reward: float = 1.0
    ownership_reward: float = 3.0
    win_reward: float = 100.0
    mp_reward: float = 0.5