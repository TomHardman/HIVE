#pragma once
#include "Position.h"
#include "Pieces.h"
#include "MoveFetcher.h"
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include <array>
#include <optional>

/**
 * Game: Main model class managing game state
 * 
 * DESIGN DECISIONS:
 * 1. Using std::array<T, 2> for player-specific data (index 0 = player 1, index 1 = player 2)
 *    - More type-safe than raw arrays
 *    - Bounds checking in debug mode
 *    - Clear intent: exactly 2 players
 * 
 * 2. Using std::optional<Position> for queen positions
 *    - Handles "queen not yet placed" case explicitly
 *    - More expressive than nullptr or sentinel values
 * 
 * 3. Tile positions map uses vector<HiveTile> for stacks
 *    - Beetles can climb, so positions can have multiple tiles
 *    - Vector is efficient for small stacks (usually 1-2 tiles)
 * 
 * 4. Player hands are unordered_set<HiveTile>
 *    - Fast lookup and removal
 *    - No duplicates (each tile is unique)
 */
class Game {
public:
    // ============= Constructor =============
    
    /**
     * Initialize game with starting pieces in hands
     * 
     * DESIGN DECISION: Taking max_turns and simplified_game as optional parameters
     * to match Python implementation for AI training scenarios
     */
    Game(int max_turns = -1, bool simplified_game = false);
    
    // ============= Game State Queries =============
    
    /**
     * Gets valid placement positions for current player
     * Takes into account queen placement rules and adjacency requirements
     * 
     * @param insect Type of insect being placed
     * @return Vector of valid positions
     */
    std::vector<Position> getValidPlacements(Insect insect) const;
    
    /**
     * Gets valid moves for a tile at given position
     * 
     * DESIGN DECISION: This wraps MoveFetcher but adds game-context checks:
     * - Queen must be placed before moving
     * - Tile must belong to current player
     * - Tile must not be covered
     * 
     * @param position Position of tile to move
     * @return Vector of valid destination positions
     */
    std::vector<Position> getValidMoves(const Position& position) const;
    
    /**
     * Gets all legal actions for current player
     * Used by AI agents to explore action space
     * 
     * DESIGN DECISION: Return type to be determined based on how you want to
     * represent actions. Options:
     * - vector<pair<Position, HiveTile>> for placements + moves
     * - Custom Action struct
     * - Map<Position, vector<Insect>> similar to Python
     * 
     * TODO: Clarify desired return type and structure
     */
    // std::vector<Action> getLegalActions() const;  // Placeholder
    
    /**
     * Checks if game is over and returns winner
     * 
     * @return 0 if game not over, 1 if player 1 wins, 2 if player 2 wins
     */
    int checkGameOver() const;
    
    /**
     * Gets current player (1 or 2)
     */
    int getCurrentPlayer() const;
    
    // ============= Game Actions =============
    
    /**
     * Places a tile from hand onto the board
     * Updates game state: removes from hand, adds to board, increments turn
     * 
     * @param insect Type of insect to place
     * @param position Where to place it
     * @return true if placement was valid and successful
     * 
     * DESIGN DECISION: Returns bool for success/failure rather than throwing
     * exceptions for invalid moves. This is more efficient for AI move validation.
     */
    bool place(Insect insect, const Position& position);
    
    /**
     * Moves a tile from one position to another
     * Updates game state and increments turn
     * 
     * @param from_position Current tile position
     * @param to_position Destination position
     * @return true if move was valid and successful
     */
    bool move(const Position& from_position, const Position& to_position);
    
    // ============= State Access (for View/Controller) =============
    
    /**
     * Get read-only access to tile positions
     * View layer needs this for rendering
     */
    const std::unordered_map<Position, std::vector<HiveTile>>& getTilePositions() const {
        return tile_positions_;
    }
    
    /**
     * Get player hands (read-only)
     */
    const std::array<std::unordered_set<HiveTile>, 2>& getPlayerHands() const {
        return player_hands_;
    }
    
    /**
     * Get queen positions
     */
    const std::array<std::optional<Position>, 2>& getQueenPositions() const {
        return queen_positions_;
    }
    
    /**
     * Get player turns
     */
    const std::array<int, 2>& getPlayerTurns() const {
        return player_turns_;
    }
    
private:
    // ============= Game State =============
    
    // Player hands: pieces not yet placed
    std::array<std::unordered_set<HiveTile>, 2> player_hands_;
    
    // Queen positions (optional because queens may not be placed yet)
    std::array<std::optional<Position>, 2> queen_positions_;
    
    // Board state: position -> stack of tiles (vector for beetles climbing)
    std::unordered_map<Position, std::vector<HiveTile>> tile_positions_;
    
    // Turn counters for each player
    std::array<int, 2> player_turns_;
    
    // Game configuration
    int max_turns_;
    bool simplified_game_;
    
    // ============= Private Helper Methods =============
    
    /**
     * Initializes player hands with starting pieces
     * 3 ants, 3 grasshoppers, 2 beetles, 2 spiders, 1 queen per player
     */
    void initializeHands();
    
    /**
     * Checks if a placement position is valid for given player
     * Handles adjacency rules and first-turn special cases
     */
    bool isValidPlacement(const Position& pos, int player) const;
    
    /**
     * Checks if player has placed their queen
     */
    bool hasPlacedQueen(int player) const;
    
    /**
     * Counts pieces surrounding a position (for win condition)
     */
    int countSurroundingPieces(const Position& pos) const;
};

/**
 * Hash function for HiveTile to use in unordered_set
 * 
 * DESIGN DECISION: Hashing based on player and insect type.
 * Since there are multiple ants/beetles per player, you might want to add
 * a unique ID field to HiveTile if you need to distinguish between them.
 * For now, assuming piece type + player is sufficient as identifier.
 */
namespace std {
    template <>
    struct hash<HiveTile> {
        std::size_t operator()(const HiveTile& tile) const {
            return std::hash<int>()(tile.player) ^ 
                   (std::hash<int>()(static_cast<int>(tile.insect)) << 1);
        }
    };
}

