#pragma once
#include "Position.h"
#include "Pieces.h"
#include <vector>
#include <unordered_map>
#include <unordered_set>

/**
 * MoveFetcher: Stateless class for computing valid moves
 * 
 * DESIGN DECISION: Using a namespace instead of a class with static methods.
 * This is more idiomatic C++ for pure utility functions and makes it clear
 * there's no state to manage.
 * 
 * Uses tag dispatch pattern to select correct move algorithm at compile time
 * based on insect type.
 */
namespace MoveFetcher {
    
    // Type alias for tile positions map (read-only access)
    using TilePositions = std::unordered_map<Position, std::vector<HiveTile>>;
    
    /**
     * Main entry point: Gets valid moves for a tile at given position
     * Dispatches to appropriate overload based on insect type
     * 
     * @param position Current position of the tile
     * @param tile The tile to get moves for
     * @param tile_positions Current board state (read-only)
     * @return Vector of valid destination positions
     */
    std::vector<Position> getValidMoves(
        const Position& position,
        const HiveTile& tile,
        const TilePositions& tile_positions
    );
    
    // ============= Private helper functions =============
    // DESIGN DECISION: These are in the namespace but documented as "internal"
    // In a larger project, these might go in a detail:: sub-namespace
    
    /**
     * Gets the 6 neighboring positions in hexagonal grid
     */
    std::array<Position, 6> getNeighbors(const Position& pos);
    
    /**
     * Checks if there's space to slide into a neighboring position
     * Based on the "slide rule" in Hive where pieces can't squeeze through gaps
     * 
     * @param current_pos Current position
     * @param neighbors Array of 6 neighbor positions (clockwise from top)
     * @param target_idx Index (0-5) of the target neighbor
     * @param tile_positions Board state
     * @return true if sliding is possible
     */
    bool canSlideInto(
        const Position& current_pos,
        const std::array<Position, 6>& neighbors,
        int target_idx,
        const TilePositions& tile_positions
    );
    
    /**
     * Tests if removing a tile from its position would break the hive
     * (one-hive rule: all pieces must remain connected)
     * 
     * @param position Position to test removal from
     * @param tile_positions Board state
     * @return true if removal would break connectivity
     */
    bool wouldBreakHive(
        const Position& position,
        const TilePositions& tile_positions
    );
    
    /**
     * Checks if the hive is connected (used by wouldBreakHive)
     * 
     * @param tile_positions Board state
     * @param dummy_pos Optional position to ignore (for hypothetical removal)
     * @return true if disconnected, false if connected
     */
    bool isDisconnected(
        const TilePositions& tile_positions,
        const Position* dummy_pos = nullptr
    );
    
    /**
     * Checks if a tile is covered by another tile (beetle on top)
     * 
     * @param position Position to check
     * @param tile The tile to check if covered
     * @param tile_positions Board state
     * @return true if tile is not on top of stack
     */
    bool isCovered(
        const Position& position,
        const HiveTile& tile,
        const TilePositions& tile_positions
    );
    
    // ============= Move calculation per insect type (tag dispatch) =============
    
    /**
     * Ant: Can move unlimited spaces around the hive perimeter
     * Uses BFS to explore all reachable positions
     */
    std::vector<Position> getValidMoves(
        const Position& position,
        const TilePositions& tile_positions,
        AntTag
    );
    
    /**
     * Beetle: Can move one space and climb on top of other pieces
     * Special slide rules when on top of hive
     */
    std::vector<Position> getValidMoves(
        const Position& position,
        const TilePositions& tile_positions,
        BeetleTag
    );
    
    /**
     * Grasshopper: Jumps in straight line over continuous pieces
     * Lands on first empty space
     */
    std::vector<Position> getValidMoves(
        const Position& position,
        const TilePositions& tile_positions,
        GrasshopperTag
    );
    
    /**
     * Spider: Must move exactly 3 spaces around hive perimeter
     * Cannot backtrack
     */
    std::vector<Position> getValidMoves(
        const Position& position,
        const TilePositions& tile_positions,
        SpiderTag
    );
    
    /**
     * Queen: Can move one space around hive perimeter
     */
    std::vector<Position> getValidMoves(
        const Position& position,
        const TilePositions& tile_positions,
        QueenTag
    );
    
} // namespace MoveFetcher

