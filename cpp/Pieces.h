#pragma once
#include <cstdint>
#include <functional>

/**
 * Insect types in Hive
 */
enum class Insect : std::uint8_t {
    ANT,
    BEETLE,
    GRASSHOPPER,
    SPIDER,
    QUEEN,
};

/**
 * HiveTile: Pure data structure representing a game piece
 * 
 * Each piece is uniquely identified by player + insect + id:
 * - Player 1 has Ant #1, Ant #2, Ant #3
 * - Player 2 has Ant #1, Ant #2, Ant #3
 * etc.
 */
struct HiveTile {
    int player;      // 1 or 2
    Insect insect;   // Type of insect
    int id;          // Unique ID per (player, insect) combination
    
    HiveTile(int player, Insect insect, int id) 
        : player(player), insect(insect), id(id) {}
    
    bool operator==(const HiveTile& other) const {
        return player == other.player 
            && insect == other.insect 
            && id == other.id;
    }
};

/**
 * TODO: think about best way to hash HiveTile
 */
namespace std {
    template <>
    struct hash<HiveTile> {
        std::size_t operator()(const HiveTile& tile) const {
            // Combine all three fields with bit shifting to avoid collisions
            std::size_t h1 = std::hash<int>()(tile.player);
            std::size_t h2 = std::hash<int>()(static_cast<int>(tile.insect));
            std::size_t h3 = std::hash<int>()(tile.id);
            
            return h1 ^ (h2 << 1) ^ (h3 << 2);
        }
    };
}

