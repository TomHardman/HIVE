#pragma once
#include "Game.h"
#include <optional>

/**
 * Parameters controlling the beam-minimax search.
 * Mirrors MinimaxParams in py2/agents/minimax_utils.py — keep in sync.
 */
struct MinimaxParams {
    int   depth                    = 3;
    int   beam_width               = 3;
    float queen_surrounding_reward = 1.0F;
    float ownership_reward         = 3.0F;
    float win_reward               = 100.0F;
    float mp_reward                = 0.5F;
};

namespace MinimaxSearch {

    /**
     * Run beam-search minimax from the current game state and return the best
     * Action for the current player, or std::nullopt if there are no legal moves.
     *
     * The game object is mutated during search (apply_action / undo) but is
     * always restored to its original state before this function returns.
     */
    std::optional<Action> selectAction(Game& game, const MinimaxParams& params);

} // namespace MinimaxSearch