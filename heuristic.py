from rl_helper import RewardCalculator
from dataclasses import dataclass
from random import randint


@dataclass
class Params:
    queen_surrounding_reward: float
    ownership_reward: float
    win_reward: float
    mp_reward: float


def evaluate(state: dict, player: int, params: Params, ran_test=True) -> float:
    """
    Evaluates game state for given player - to be used in minimax search
    """
    reward_calc = RewardCalculator(None)
    value = 0
    
    # Queen surrounding reward
    qs_reward = params.queen_surrounding_reward
    n_s_self = reward_calc.pieces_around_queen(player, state)
    n_s_opp = reward_calc.pieces_around_queen(3 - player, state)
    net_surrounding = n_s_opp - n_s_self
    value += net_surrounding * qs_reward

    # Win reward
    win_reward = params.win_reward
    if state['winner'] == player:
        value += win_reward
    elif state['winner'] == 3 - player:
        value -= win_reward
    
    # Queen ownership reward
    own_queen = reward_calc.queen_ownership(player, state)
    opp_queen = reward_calc.queen_ownership(3 - player, state)
    net = own_queen - opp_queen
    value += net * params.ownership_reward

    # Moveable pieces reward
    mp_reward = params.mp_reward
    nmp_self = reward_calc.moveable_pieces(player, state)
    nmp_opp = reward_calc.moveable_pieces(3 - player, state)
    net_mp = nmp_self - nmp_opp
    value += net_mp * mp_reward

    return value