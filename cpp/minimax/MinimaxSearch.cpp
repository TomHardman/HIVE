#include "MinimaxSearch.h"
#include "MoveFetcher.h"
#include <algorithm>
#include <limits>
#include <set>

// ── Internal helpers (not part of the public API) ────────────────────────────
namespace {

int countSurrounding(
    const std::optional<Position>& queen_pos,
    const MoveFetcher::TilePositions& tile_positions
) {
    if (!queen_pos) return 0;
    int count = 0;
    for (const auto& neighbour : MoveFetcher::getNeighbors(*queen_pos)) {
        if (tile_positions.count(neighbour) != 0U) ++count;
    }
    return count;
}

bool isOwnedByOpp(
    const std::optional<Position>& queen_pos,
    int owner,
    const MoveFetcher::TilePositions& tile_positions
) {
    if (!queen_pos) return false;
    auto it = tile_positions.find(*queen_pos);
    if (it == tile_positions.end()) return false;
    const auto& stack = it->second;
    return stack.size() > 1 && stack.back().player != owner;
}

// Count distinct pieces belonging to `player` that have at least one legal move.
int countMoveable(int player, Game& game) {
    const auto& tile_positions = game.getTilePositions();
    std::set<std::pair<int, int>> moveable;
    for (const auto& [pos, stack] : tile_positions) {
        if (stack.empty() || stack.back().player != player) continue;
        if (!game.getValidMoves(pos).empty()) {
            const auto& top = stack.back();
            moveable.insert({static_cast<int>(top.insect), top.id});
        }
    }
    return static_cast<int>(moveable.size());
}

/**
 * Heuristic evaluation of the current game state from `player`'s perspective.
 * Positive scores favour `player`; negative scores favour the opponent.
 *
 * Components (all differential):
 *   - Win / loss detection
 *   - Queen surrounding (pieces adjacent to each queen)
 *   - Queen ownership  (opponent piece on top of own queen)
 *   - Mobility         (distinct pieces with ≥1 legal move)
 */
float evaluate(Game& game, int player, const MinimaxParams& params) {
    int winner = game.checkGameOver();
    if (winner == player) return  params.win_reward;
    if (winner != 0)      return -params.win_reward;

    const auto& tile_positions  = game.getTilePositions();
    const auto& queen_positions = game.getQueenPositions();
    int opp = 3 - player;

    // Queen surrounding
    int own_surrounded = countSurrounding(queen_positions[player - 1], tile_positions);
    int opp_surrounded = countSurrounding(queen_positions[opp    - 1], tile_positions);
    float value = static_cast<float>(opp_surrounded - own_surrounded)
                  * params.queen_surrounding_reward;

    // Queen ownership (opponent beetle sitting on top of own queen)
    int own_owned = isOwnedByOpp(queen_positions[player - 1], player, tile_positions) ? 1 : 0;
    int opp_owned = isOwnedByOpp(queen_positions[opp    - 1], opp,    tile_positions) ? 1 : 0;
    value += static_cast<float>(opp_owned - own_owned) * params.ownership_reward;

    // Mobility
    value += static_cast<float>(countMoveable(player, game) - countMoveable(opp, game))
             * params.mp_reward;

    return value;
}

/**
 * Beam-search minimax with alpha-beta pruning.
 *
 * Two phases per node:
 *   1. Shallow-evaluate all legal actions and keep top-beam_width candidates.
 *   2. Recurse with full alpha-beta only on those candidates.
 *
 * Uses game.apply_action / game.undo for in-place tree traversal — no copies.
 */
std::pair<float, std::optional<Action>> beamMinimax(
    Game& game,
    int depth,
    bool is_maximizing,
    int player,
    const MinimaxParams& params,
    float alpha,
    float beta
) {
    int winner = game.checkGameOver();
    if (winner != 0 || depth == 0)
        return {evaluate(game, player, params), std::nullopt};

    auto legal = game.getLegalActions();
    if (legal.empty())
        return {evaluate(game, player, params), std::nullopt};

    // ── Phase 1: shallow evaluation of all legal moves ────────────────────
    std::vector<std::pair<float, Action>> scored;
    scored.reserve(legal.size());
    for (const auto& action : legal) {
        auto orig    = game.apply_action(action);
        float score  = evaluate(game, player, params);
        game.undo(action, orig);
        scored.push_back({score, action});
    }

    // ── Phase 2: keep top-k candidates ───────────────────────────────────
    int k = std::min(params.beam_width, static_cast<int>(scored.size()));
    if (is_maximizing) {
        std::partial_sort(scored.begin(), scored.begin() + k, scored.end(),
            [](const auto& x, const auto& y) { return x.first > y.first; });
    } else {
        std::partial_sort(scored.begin(), scored.begin() + k, scored.end(),
            [](const auto& x, const auto& y) { return x.first < y.first; });
    }
    scored.resize(k);

    // ── Phase 3: recursive alpha-beta on candidates ───────────────────────
    std::optional<Action> best_action;

    if (is_maximizing) {
        float best_val = -std::numeric_limits<float>::infinity();
        for (const auto& candidate : scored) {
            const Action& action = candidate.second;
            auto orig = game.apply_action(action);
            float val = beamMinimax(game, depth - 1, false, player, params, alpha, beta).first;
            game.undo(action, orig);
            if (val > best_val) { best_val = val; best_action = action; }
            alpha = std::max(alpha, val);
            if (beta <= alpha) break;
        }
        return {best_val, best_action};
    }

    float best_val = std::numeric_limits<float>::infinity();
    for (const auto& candidate : scored) {
        const Action& action = candidate.second;
        auto orig = game.apply_action(action);
        float val = beamMinimax(game, depth - 1, true, player, params, alpha, beta).first;
        game.undo(action, orig);
        if (val < best_val) { best_val = val; best_action = action; }
        beta = std::min(beta, val);
        if (beta <= alpha) break;
    }
    return {best_val, best_action};
}

} // anonymous namespace

// ── Public API ────────────────────────────────────────────────────────────────
namespace MinimaxSearch {

std::optional<Action> selectAction(Game& game, const MinimaxParams& params) {
    int player = game.getCurrentPlayer();
    return beamMinimax(
        game, params.depth, /*is_maximizing=*/true, player, params,
        -std::numeric_limits<float>::infinity(),
         std::numeric_limits<float>::infinity()
    ).second;
}

} // namespace MinimaxSearch
