#pragma once
#include <cstdint>


enum class Insect : std::uint8_t {
    ANT,
    BEETLE,
    GRASSHOPPER,
    SPIDER,
    QUEEN,
};


struct HiveTile {
    int player;      // 1 or 2
    Insect insect;
    
    HiveTile(int player, Insect insect) : player(player), insect(insect) {}
    
    bool operator==(const HiveTile& other) const {
        return player == other.player && insect == other.insect;
    }
};

// Tag types for compile-time dispatch (zero-size types)
// These enable overloading without storing type-specific data
struct AntTag {};
struct BeetleTag {};
struct GrasshopperTag {};
struct SpiderTag {};
struct QueenTag {};
