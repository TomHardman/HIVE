from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import hive_engine

from .base import Agent, Action

if TYPE_CHECKING:
    pass


_HEX_NEIGHBORS: list[tuple[int, int]] = [(0, 1), (1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1)]


@dataclass
class MinimaxParams:
    depth: int = 3
    beam_width: int = 3
    queen_surrounding_reward: float = 1.0
    ownership_reward: float = 3.0
    win_reward: float = 100.0
    mp_reward: float = 0.5


def _evaluate(game: hive_engine.Game, player: int, params: MinimaxParams) -> float:
    """
    Heuristic evaluation of the current game state from `player`'s perspective.

    Returns a positive score when `player` is advantaged and a negative score
    when the opponent is advantaged.  Four components (all differential):
      - Win/loss detection
      - Queen surrounding (pieces adjacent to each queen)
      - Queen ownership (opponent piece on top of own queen)
      - Mobility (distinct pieces with at least one legal move)
    """
    winner = game.check_game_over()
    if winner == player:
        return params.win_reward
    if winner != 0:
        return -params.win_reward

    tile_positions = game.get_tile_positions()
    queen_positions = game.get_queen_positions()  # [p1_pos | None, p2_pos | None]
    opp = 3 - player

    # ── Queen surrounding ──────────────────────────────────────────────────
    def _count_surrounding(queen_pos: hive_engine.Position | None) -> int:
        if queen_pos is None:
            return 0
        count = 0
        for dq, dr in _HEX_NEIGHBORS:
            neighbour = hive_engine.Position(queen_pos.q + dq, queen_pos.r + dr)
            if neighbour in tile_positions:
                count += 1
        return count

    own_surrounded = _count_surrounding(queen_positions[player - 1])
    opp_surrounded = _count_surrounding(queen_positions[opp - 1])
    value = (opp_surrounded - own_surrounded) * params.queen_surrounding_reward

    # ── Queen ownership (any opponent piece on top of own queen's stack) ───
    def _is_owned_by_opp(queen_pos: hive_engine.Position | None, owner: int) -> bool:
        if queen_pos is None:
            return False
        stack = tile_positions.get(queen_pos)
        if stack and len(stack) > 1 and stack[-1].player != owner:
            return True
        return False

    own_owned = 1 if _is_owned_by_opp(queen_positions[player - 1], player) else 0
    opp_owned = 1 if _is_owned_by_opp(queen_positions[opp - 1], opp) else 0
    value += (opp_owned - own_owned) * params.ownership_reward

    # ── Mobility (distinct pieces with ≥1 valid move) ─────────────────────
    def _count_moveable(p: int) -> int:
        moveable: set[tuple] = set()
        for pos, stack in tile_positions.items():
            if stack and stack[-1].player == p:
                if game.get_valid_moves(pos):
                    top = stack[-1]
                    moveable.add((int(top.insect), top.id))
        return len(moveable)

    value += (_count_moveable(player) - _count_moveable(opp)) * params.mp_reward

    return value


def _beam_minimax(
    game: hive_engine.Game,
    depth: int,
    is_maximizing: bool,
    player: int,
    params: MinimaxParams,
    alpha: float,
    beta: float,
    beam_width: int,
) -> tuple[float, hive_engine.Action | None]:
    """
    Beam-search minimax with alpha-beta pruning.

    Two-phase per node:
      1. Shallow-evaluate all legal actions to select top-`beam_width` candidates.
      2. Recurse only on those candidates with full alpha-beta search.

    Uses game.apply_action / game.undo for in-place tree traversal — no deep copy.
    """
    winner = game.check_game_over()
    if winner != 0 or depth == 0:
        return _evaluate(game, player, params), None

    legal = game.get_legal_actions()
    if not legal:
        return _evaluate(game, player, params), None

    # ── Phase 1: shallow evaluation of all moves ───────────────────────────
    scored: list[tuple[float, hive_engine.Action]] = []
    for a in legal:
        orig = game.apply_action(a)
        score = _evaluate(game, player, params)
        game.undo(a, orig)
        scored.append((score, a))

    # ── Phase 2: select top-k candidates ──────────────────────────────────
    if is_maximizing:
        candidates = heapq.nlargest(beam_width, scored, key=lambda x: x[0])
    else:
        candidates = heapq.nsmallest(beam_width, scored, key=lambda x: x[0])

    # ── Phase 3: recursive alpha-beta on candidates ────────────────────────
    best_action: hive_engine.Action | None = None

    if is_maximizing:
        best_val = -math.inf
        for _, a in candidates:
            orig = game.apply_action(a)
            val, _ = _beam_minimax(game, depth - 1, False, player, params, alpha, beta, beam_width)
            game.undo(a, orig)
            if val > best_val:
                best_val = val
                best_action = a
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return best_val, best_action

    else:
        best_val = math.inf
        for _, a in candidates:
            orig = game.apply_action(a)
            val, _ = _beam_minimax(game, depth - 1, True, player, params, alpha, beta, beam_width)
            game.undo(a, orig)
            if val < best_val:
                best_val = val
                best_action = a
            beta = min(beta, val)
            if beta <= alpha:
                break
        return best_val, best_action


class MinimaxAgentPy(Agent):
    """
    Depth-limited beam-search minimax agent.

    All configuration (depth, beam_width, heuristic weights) is held in params.
    """

    def __init__(self, params: MinimaxParams) -> None:
        self.params = params

    def select_action(self, game: hive_engine.Game) -> Action | None:
        player = game.get_current_player()
        _, best = _beam_minimax(
            game, self.params.depth, True, player, self.params,
            -math.inf, math.inf, self.params.beam_width,
        )
        if best is None:
            return None
        return Action(tile_idx=best.tile_idx, to=(best.to.q, best.to.r))
