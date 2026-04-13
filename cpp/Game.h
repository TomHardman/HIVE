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
 * Maps tile_idx (0-10) to (Insect type, instance id).
 * This is the single unified action representation used by all agents.
 *
 * Matches Python ACTIONSPACE:
 *   queen=0, spider1=1, spider2=2, beetle1=3, beetle2=4,
 *   ant1=5, ant2=6, ant3=7, grasshopper1=8, grasshopper2=9, grasshopper3=10
 *
 * For placements: the highest-id instance of that insect type remaining in hand
 * is always used (matching the Python pieces_remaining convention).
 * For movements: tile_idx identifies the specific piece on the board to move.
 */
inline constexpr std::array<std::pair<Insect, int>, 11> TILE_IDX_MAP = {{
    {Insect::QUEEN,       1},  // 0
    {Insect::SPIDER,      1},  // 1
    {Insect::SPIDER,      2},  // 2
    {Insect::BEETLE,      1},  // 3
    {Insect::BEETLE,      2},  // 4
    {Insect::ANT,         1},  // 5
    {Insect::ANT,         2},  // 6
    {Insect::ANT,         3},  // 7
    {Insect::GRASSHOPPER, 1},  // 8
    {Insect::GRASSHOPPER, 2},  // 9
    {Insect::GRASSHOPPER, 3},  // 10
}};

/**
 * Unified action type used by all agents and returned by getBestMove.
 *
 * tile_idx identifies the specific piece instance via TILE_IDX_MAP.
 * to is the destination position for both placements and movements.
 *
 * Whether the action is a placement or movement is determined at runtime
 * by checking if the piece is currently in hand or on the board.
 */
struct Action {
    int tile_idx;  // 0-10
    Position to;

    bool operator==(const Action& other) const {
        return tile_idx == other.tile_idx && to == other.to;
    }
};


/**
 * Game: Main model class managing game state.
 *
 * All mutation goes through apply_action/undo, which use tile_idx as the
 * primary action representation. This keeps the interface consistent with
 * the DQL network's output space and the minimax search's action type.
 */
class Game {
public:
    // ============= Constructor =============

    Game(int max_turns = -1, bool simplified_game = false);

    // ============= Game State Queries =============

    /**
     * Gets valid placement positions for the current player for a given insect type.
     */
    std::vector<Position> getValidPlacements(Insect insect) const;

    /**
     * Gets valid move destinations for the tile at the given position.
     * Returns empty if: no tile there, wrong player, queen not placed, or tile is covered.
     */
    std::vector<Position> getValidMoves(const Position& position) const;

    /**
     * Returns all legal actions for the current player.
     * For placements, uses the highest-id instance of each insect type in hand.
     * For movements, uses the tile_idx of the top tile at each occupied position.
     */
    std::vector<Action> getLegalActions() const;

    /**
     * Returns 0 if game is ongoing, 1 if player 1 wins, 2 if player 2 wins.
     */
    int checkGameOver() const;

    /**
     * Returns the current player (1 or 2).
     */
    int getCurrentPlayer() const;

    // ============= Game Actions =============

    /**
     * Applies an action to the game state.
     *
     * Returns the tile's original board position if the action was a movement
     * (needed to undo it), or std::nullopt if it was a placement.
     *
     * Behaviour is undefined if the action is not in getLegalActions().
     */
    std::optional<Position> apply_action(const Action& action);

    /**
     * Undoes a previously applied action.
     * original_pos must be the exact value returned by apply_action for that action.
     */
    void undo(const Action& action, const std::optional<Position>& original_pos);

    // ============= State Access =============

    const std::unordered_map<Position, std::vector<HiveTile>>& getTilePositions() const {
        return tile_positions_;
    }
    const std::array<std::unordered_set<HiveTile>, 2>& getPlayerHands() const {
        return player_hands_;
    }
    const std::array<std::optional<Position>, 2>& getQueenPositions() const {
        return queen_positions_;
    }
    const std::array<int, 2>& getPlayerTurns() const {
        return player_turns_;
    }

private:
    // ============= State =============

    std::array<std::unordered_set<HiveTile>, 2> player_hands_;
    std::array<std::optional<Position>, 2> queen_positions_;
    std::unordered_map<Position, std::vector<HiveTile>> tile_positions_;
    std::array<int, 2> player_turns_;
    int max_turns_;
    bool simplified_game_;

    // ============= Private Helpers =============

    void initializeHands();
    bool isValidPlacement(const Position& pos, int player) const;
    bool hasPlacedQueen(int player) const;
    int countSurroundingPieces(const Position& pos) const;

    // Low-level primitives used by apply_action and undo (no turn increment)
    void placeTile(const HiveTile& tile, const Position& pos);
    void moveTile(const HiveTile& tile, const Position& from, const Position& to);

    // Returns tile_idx for a given (insect, id) pair, or -1 if not found
    static int tileToIdx(Insect insect, int id);
};
