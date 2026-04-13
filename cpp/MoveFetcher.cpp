#include "MoveFetcher.h"
#include <queue>
#include <deque>

namespace MoveFetcher {

// ============= Main dispatcher =============

std::vector<Position> getValidMoves(
    const Position& position,
    const HiveTile& tile,
    const TilePositions& tile_positions
) {
    switch (tile.insect) {
        case Insect::ANT:         return getAntMoves(position, tile_positions);
        case Insect::BEETLE:      return getBeetleMoves(position, tile_positions);
        case Insect::GRASSHOPPER: return getGrasshopperMoves(position, tile_positions);
        case Insect::SPIDER:      return getSpiderMoves(position, tile_positions);
        case Insect::QUEEN:       return getQueenMoves(position, tile_positions);
    }
    
    // Should never reach here, but return empty vector for safety
    return {};
}

// ============= Helper Functions =============

std::array<Position, 6> getNeighbors(const Position& pos) {
    // Hexagonal grid neighbors in axial coordinates (clockwise from top)
    return {
        Position(pos.q, pos.r + 1),      // Top
        Position(pos.q + 1, pos.r),      // Top-right
        Position(pos.q + 1, pos.r - 1),  // Bottom-right
        Position(pos.q, pos.r - 1),      // Bottom
        Position(pos.q - 1, pos.r),      // Bottom-left
        Position(pos.q - 1, pos.r + 1)   // Top-left
    };
}

bool canSlideInto(
    const Position& current_pos,
    const std::array<Position, 6>& neighbors,
    int target_idx,
    const TilePositions& tile_positions
) {
    // Check if either adjacent neighbor is empty (allows sliding)
    int prev_idx = (target_idx - 1 + 6) % 6;
    int next_idx = (target_idx + 1) % 6;
    
    bool prev_empty = tile_positions.find(neighbors[prev_idx]) == tile_positions.end();
    bool next_empty = tile_positions.find(neighbors[next_idx]) == tile_positions.end();
    
    // Can slide if at least one adjacent position is empty
    return prev_empty || next_empty;
}

bool isCovered(
    const Position& position,
    const HiveTile& tile,
    const TilePositions& tile_positions
) {
    auto it = tile_positions.find(position);
    if (it == tile_positions.end() || it->second.empty()) {
        return false;  // No tiles at position
    }
    
    // Tile is covered if it's not the top tile in the stack
    return it->second.back() != tile;
}

bool isDisconnected(
    const TilePositions& tile_positions,
    const Position* dummy_pos
) {
    if (tile_positions.empty()) {
        return false;  // Empty board is "connected"
    }
    
    // Start DFS from first position (that's not dummy_pos)
    std::unordered_set<Position> seen;
    std::vector<Position> stack;
    
    // Find starting position
    for (const auto& [pos, tiles] : tile_positions) {
        if (dummy_pos && pos == *dummy_pos) {
            continue;
        }
        stack.push_back(pos);
        break;
    }
    
    if (stack.empty()) {
        return false;  // All positions are dummy
    }
    
    // DFS to find all connected positions
    while (!stack.empty()) {
        Position current = stack.back();
        stack.pop_back();
        
        if (seen.find(current) != seen.end()) {
            continue;
        }
        
        seen.insert(current);
        
        // Check all neighbors
        auto neighbors = getNeighbors(current);
        for (const auto& neighbor : neighbors) {
            if (dummy_pos && neighbor == *dummy_pos) {
                continue;  // Skip dummy position
            }
            
            if (tile_positions.find(neighbor) != tile_positions.end() &&
                seen.find(neighbor) == seen.end()) {
                stack.push_back(neighbor);
            }
        }
    }
    
    // Check if we visited all positions (excluding dummy)
    size_t expected_count = tile_positions.size();
    if (dummy_pos) {
        expected_count -= 1;
    }
    
    return seen.size() != expected_count;
}

bool wouldBreakHive(
    const Position& position,
    const TilePositions& tile_positions
) {
    if (tile_positions.size() < 2) {
        return false;  // Can't break hive if only one tile
    }
    
    // Create hypothetical board state without this tile
    TilePositions test_positions = tile_positions;
    
    auto it = test_positions.find(position);
    if (it != test_positions.end()) {
        it->second.pop_back();  // Remove top tile
        if (it->second.empty()) {
            test_positions.erase(it);
        }
    }
    
    return isDisconnected(test_positions, nullptr);
}

// ============= Move Calculations per Insect Type =============

std::vector<Position> getAntMoves(
    const Position& position,
    const TilePositions& tile_positions
) {
    // TODO: Implement ant movement (unlimited distance around hive via BFS)
    return {};
}

std::vector<Position> getBeetleMoves(
    const Position& position,
    const TilePositions& tile_positions
) {
    // TODO: Implement beetle movement (one space, can climb)
    return {};
}

std::vector<Position> getGrasshopperMoves(
    const Position& position,
    const TilePositions& tile_positions
) {
    // TODO: Implement grasshopper movement (jump in straight line)
    return {};
}

std::vector<Position> getSpiderMoves(
    const Position& position,
    const TilePositions& tile_positions
) {
    // TODO: Implement spider movement (exactly 3 spaces)
    return {};
}

std::vector<Position> getQueenMoves(
    const Position& position,
    const TilePositions& tile_positions
) {
    // TODO: Implement queen movement (one space around hive)
    return {};
}

} // namespace MoveFetcher

