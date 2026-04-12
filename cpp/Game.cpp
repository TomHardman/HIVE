#include "Game.h"

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
        
        // Add 3 ants (id: 1, 2, 3)
        for (int i = 1; i <= 3; ++i) {
            hand.insert(HiveTile(player, Insect::ANT, i));
        }
        
        // Add 3 grasshoppers (id: 1, 2, 3)
        for (int i = 1; i <= 3; ++i) {
            hand.insert(HiveTile(player, Insect::GRASSHOPPER, i));
        }
        
        // Add 2 beetles (id: 1, 2)
        for (int i = 1; i <= 2; ++i) {
            hand.insert(HiveTile(player, Insect::BEETLE, i));
        }
        
        // Add 2 spiders (id: 1, 2)
        for (int i = 1; i <= 2; ++i) {
            hand.insert(HiveTile(player, Insect::SPIDER, i));
        }
        
        // Add 1 queen (id: 1)
        hand.insert(HiveTile(player, Insect::QUEEN, 1));
    }
}

// ============= Game State Queries =============

int Game::getCurrentPlayer() const {
    // Player whose turn it is
    return (player_turns_.at(0) == player_turns_.at(1)) ? 1 : 2;
}

bool Game::hasPlacedQueen(int player) const {
    return queen_positions_.at(player - 1).has_value();
}

std::vector<Position> Game::getValidPlacements(Insect insect) const {
    // TODO: Implement valid placement logic
    // Should handle:
    // - First turn: anywhere (conventionally (0,0))
    // - Second player first turn: adjacent to first tile
    // - Subsequent turns: adjacent to own pieces only
    // - Queen placement rule: must place queen by turn 4
    return {};
}

std::vector<Position> Game::getValidMoves(const Position& position) const {
    // Check if there's a tile at this position
    auto it = tile_positions_.find(position);
    if (it == tile_positions_.end() || it->second.empty()) {
        return {};  // No tile to move
    }
    
    const HiveTile& tile = it->second.back();  // Top tile
    
    // Check if tile belongs to current player
    if (tile.player != getCurrentPlayer()) {
        return {};
    }
    
    // Check if queen has been placed (can't move until queen is placed)
    if (!hasPlacedQueen(tile.player)) {
        return {};
    }
    
    // Check if tile is covered (can't move covered tiles)
    if (MoveFetcher::isCovered(position, tile, tile_positions_)) {
        return {};
    }
    
    // Delegate to MoveFetcher
    return MoveFetcher::getValidMoves(position, tile, tile_positions_);
}

int Game::checkGameOver() const {
    // TODO: Implement win condition checking
    // - Queen surrounded by 6 pieces = loss
    // - Both queens surrounded = draw
    // - Simplified game: 3+ pieces around queen
    // - Max turns reached: compare pieces around queens
    return 0;  // Game not over
}

// ============= Game Actions =============

bool Game::place(Insect insect, const Position& position) {
    int player = getCurrentPlayer();
    auto& hand = player_hands_.at(player - 1);
    
    // Find first available piece of this type in hand
    HiveTile* tile_ptr = nullptr;
    for (auto& tile : hand) {
        if (tile.insect == insect) {
            tile_ptr = const_cast<HiveTile*>(&tile);
            break;
        }
    }
    
    if (!tile_ptr) {
        return false;  // No piece of this type in hand
    }
    
    HiveTile tile = *tile_ptr;
    
    // Check if placement is valid
    if (!isValidPlacement(position, player)) {
        return false;
    }
    
    // Queen placement rule: must place queen by turn 3 (4th turn)
    if (player_turns_.at(player - 1) == 3 && !hasPlacedQueen(player) && insect != Insect::QUEEN) {
        return false;  // Must place queen now
    }
    
    // Place the tile
    tile_positions_[position].push_back(tile);
    hand.erase(tile);
    
    // Update queen position if placing queen
    if (insect == Insect::QUEEN) {
        queen_positions_.at(player - 1) = position;
    }
    
    // Increment turn
    player_turns_.at(player - 1)++;
    
    return true;
}

bool Game::move(const Position& from_position, const Position& to_position) {
    // Check if move is valid
    auto valid_moves = getValidMoves(from_position);
    if (std::find(valid_moves.begin(), valid_moves.end(), to_position) == valid_moves.end()) {
        return false;  // Invalid move
    }
    
    // Get the tile
    auto it = tile_positions_.find(from_position);
    if (it == tile_positions_.end() || it->second.empty()) {
        return false;
    }
    
    HiveTile tile = it->second.back();
    
    // Remove from old position
    it->second.pop_back();
    if (it->second.empty()) {
        tile_positions_.erase(it);
    }
    
    // Add to new position
    tile_positions_[to_position].push_back(tile);
    
    // Update queen position if moving queen
    if (tile.insect == Insect::QUEEN) {
        queen_positions_.at(tile.player - 1) = to_position;
    }
    
    // Increment turn
    int player = getCurrentPlayer();
    player_turns_.at(player - 1)++;
    
    return true;
}

// ============= Private Helpers =============

bool Game::isValidPlacement(const Position& pos, int player) const {
    // TODO: Implement placement validation
    // - First turn: anywhere (conventionally (0,0))
    // - Second player first turn: must be adjacent to opponent's tile
    // - Subsequent turns: must be adjacent to own pieces, not adjacent to opponent
    return true;  // Placeholder
}

int Game::countSurroundingPieces(const Position& pos) const {
    int count = 0;
    auto neighbors = MoveFetcher::getNeighbors(pos);
    
    for (const auto& neighbor : neighbors) {
        if (tile_positions_.find(neighbor) != tile_positions_.end()) {
            count++;
        }
    }
    
    return count;
}

