#include "Game.h"
#include <algorithm>

// ============= Constructor =============

Game::Game(int max_turns, bool simplified_game)
    : max_turns_(max_turns)
    , simplified_game_(simplified_game)
    , player_turns_{0, 0}
    , queen_positions_{std::nullopt, std::nullopt}
{
    initializeHands();
}

// ============= Private Initialization =============

void Game::initializeHands() {
    for (int player = 1; player <= 2; player++) {
        auto& hand = player_hands_.at(player - 1);
        for (int i = 1; i <= 3; ++i) hand.insert(HiveTile(player, Insect::ANT,         i));
        for (int i = 1; i <= 3; ++i) hand.insert(HiveTile(player, Insect::GRASSHOPPER, i));
        for (int i = 1; i <= 2; ++i) hand.insert(HiveTile(player, Insect::BEETLE,      i));
        for (int i = 1; i <= 2; ++i) hand.insert(HiveTile(player, Insect::SPIDER,      i));
        hand.insert(HiveTile(player, Insect::QUEEN, 1));
    }
}

// ============= Game State Queries =============

int Game::getCurrentPlayer() const {
    return (player_turns_.at(0) == player_turns_.at(1)) ? 1 : 2;
}

bool Game::hasPlacedQueen(int player) const {
    return queen_positions_.at(player - 1).has_value();
}

std::vector<Position> Game::getValidPlacements(Insect insect) const {
    // TODO: Implement valid placement logic
    return {};
}

std::vector<Position> Game::getValidMoves(const Position& position) const {
    auto it = tile_positions_.find(position);
    if (it == tile_positions_.end() || it->second.empty()) return {};

    const HiveTile& tile = it->second.back();
    if (tile.player != getCurrentPlayer()) return {};
    if (!hasPlacedQueen(tile.player)) return {};
    if (MoveFetcher::isCovered(position, tile, tile_positions_)) return {};

    return MoveFetcher::getValidMoves(position, tile, tile_positions_);
}

std::vector<Action> Game::getLegalActions() const {
    int player = getCurrentPlayer();
    std::vector<Action> actions;

    // --- Placement actions ---
    // For each insect type in hand, use the instance with the highest id.
    // This matches the Python pieces_remaining convention where the tile placed
    // is always the last remaining instance of that type.
    std::unordered_map<Insect, int> max_id_in_hand;
    for (const auto& tile : player_hands_.at(player - 1)) {
        auto it = max_id_in_hand.find(tile.insect);
        if (it == max_id_in_hand.end() || tile.id > it->second)
            max_id_in_hand[tile.insect] = tile.id;
    }

    for (const auto& [insect, max_id] : max_id_in_hand) {
        // Queen placement rule: must place queen by turn 4 (0-indexed turn 3)
        if (player_turns_.at(player - 1) == 3 && !hasPlacedQueen(player) && insect != Insect::QUEEN)
            continue;

        int tile_idx = tileToIdx(insect, max_id);
        for (const auto& pos : getValidPlacements(insect))
            actions.push_back(Action{tile_idx, pos});
    }

    // --- Movement actions ---
    for (const auto& [pos, tiles] : tile_positions_) {
        if (tiles.empty()) continue;
        const HiveTile& top = tiles.back();
        if (top.player != player) continue;

        int tile_idx = tileToIdx(top.insect, top.id);
        for (const auto& dest : getValidMoves(pos))
            actions.push_back(Action{tile_idx, dest});
    }

    return actions;
}

int Game::checkGameOver() const {
    // TODO: Implement win condition checking
    // - Queen surrounded by 6 pieces = loss (3 in simplified mode)
    // - Both queens surrounded simultaneously = draw
    // - max_turns_ reached: fewer surrounding pieces wins
    return 0;
}

// ============= Game Actions =============

std::optional<Position> Game::apply_action(const Action& action) {
    auto [insect, id] = TILE_IDX_MAP[action.tile_idx];
    int player = getCurrentPlayer();
    HiveTile tile(player, insect, id);
    auto& hand = player_hands_.at(player - 1);

    if (hand.count(tile)) {
        // Placement
        placeTile(tile, action.to);
        player_turns_.at(player - 1)++;
        return std::nullopt;
    } else {
        // Movement: find the tile's current position on the board
        // The board is small (~10-20 tiles) so linear scan is acceptable
        Position original_pos{0, 0};
        for (const auto& [pos, tiles] : tile_positions_) {
            if (!tiles.empty() && tiles.back() == tile) {
                original_pos = pos;
                break;
            }
        }
        moveTile(tile, original_pos, action.to);
        player_turns_.at(player - 1)++;
        return original_pos;
    }
}

void Game::undo(const Action& action, const std::optional<Position>& original_pos) {
    // The player who made the move is the one whose turn count we decrement.
    // After apply_action, getCurrentPlayer() returns the OTHER player, so we use 3 - current.
    int player = 3 - getCurrentPlayer();
    auto [insect, id] = TILE_IDX_MAP[action.tile_idx];
    HiveTile tile(player, insect, id);

    if (original_pos.has_value()) {
        // Was a movement: move tile back to its original position
        moveTile(tile, action.to, *original_pos);
    } else {
        // Was a placement: remove from board and return to hand
        auto& stack = tile_positions_.at(action.to);
        stack.pop_back();
        if (stack.empty()) tile_positions_.erase(action.to);
        player_hands_.at(player - 1).insert(tile);
        if (insect == Insect::QUEEN)
            queen_positions_.at(player - 1) = std::nullopt;
    }

    player_turns_.at(player - 1)--;
}

// ============= Private Helpers =============

void Game::placeTile(const HiveTile& tile, const Position& pos) {
    tile_positions_[pos].push_back(tile);
    player_hands_.at(tile.player - 1).erase(tile);
    if (tile.insect == Insect::QUEEN)
        queen_positions_.at(tile.player - 1) = pos;
}

void Game::moveTile(const HiveTile& tile, const Position& from, const Position& to) {
    auto& from_stack = tile_positions_.at(from);
    from_stack.pop_back();
    if (from_stack.empty()) tile_positions_.erase(from);
    tile_positions_[to].push_back(tile);
    if (tile.insect == Insect::QUEEN)
        queen_positions_.at(tile.player - 1) = to;
}

int Game::tileToIdx(Insect insect, int id) {
    for (int i = 0; i < 11; i++) {
        if (TILE_IDX_MAP[i].first == insect && TILE_IDX_MAP[i].second == id) return i;
    }
    return -1;
}

bool Game::isValidPlacement(const Position& pos, int player) const {
    // TODO: Implement placement validation
    return true;
}

int Game::countSurroundingPieces(const Position& pos) const {
    int count = 0;
    for (const auto& neighbor : MoveFetcher::getNeighbors(pos)) {
        if (tile_positions_.find(neighbor) != tile_positions_.end()) count++;
    }
    return count;
}
