#include "Game.h"
#include <iostream>
#include <fmt/format.h>

/**
 * Example usage of the Hive game engine
 * Demonstrates the MVC architecture
 */

int main() {
    fmt::print("=== Hive C++ Game Engine ===\n\n");
    
    // Create the Model (Game)
    Game game;
    fmt::print("Game initialized\n");
    fmt::print("Current player: {}\n", game.getCurrentPlayer());
    
    // Access game state
    const auto& hands = game.getPlayerHands();
    fmt::print("Player 1 hand size: {}\n", hands[0].size());
    fmt::print("Player 2 hand size: {}\n", hands[1].size());
    
    // Example: Place Player 1's Queen at origin
    fmt::print("\nPlacing Player 1's Queen at (0, 0)...\n");
    Action queen_action{0, Position{0, 0}};  // tile_idx 0 = queen
    game.apply_action(queen_action);
    fmt::print("Current player after placement: {}\n", game.getCurrentPlayer());

    const auto& queen_positions = game.getQueenPositions();
    if (queen_positions[0].has_value()) {
        auto pos = queen_positions[0].value();
        fmt::print("Player 1 Queen position: ({}, {})\n", pos.q, pos.r);
    }
    
    // Display board state
    fmt::print("\nBoard state:\n");
    const auto& tile_positions = game.getTilePositions();
    if (tile_positions.empty()) {
        fmt::print("  Board is empty\n");
    } else {
        for (const auto& [pos, tiles] : tile_positions) {
            fmt::print("  Position ({}, {}): {} tile(s)\n", 
                      pos.q, pos.r, tiles.size());
            for (const auto& tile : tiles) {
                const char* insect_name;
                switch (tile.insect) {
                    case Insect::QUEEN: insect_name = "Queen"; break;
                    case Insect::ANT: insect_name = "Ant"; break;
                    case Insect::BEETLE: insect_name = "Beetle"; break;
                    case Insect::GRASSHOPPER: insect_name = "Grasshopper"; break;
                    case Insect::SPIDER: insect_name = "Spider"; break;
                }
                fmt::print("    Player {} {}\n", tile.player, insect_name);
            }
        }
    }
    
    fmt::print("\n=== Architecture Features ===\n");
    fmt::print("✓ Pure data tiles: No position duplication\n");
    fmt::print("✓ Single source of truth: Position in Game only\n");
    fmt::print("✓ Namespace utilities: MoveFetcher\n");
    
    return 0;
}

