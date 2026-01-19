#pragma once
#include <functional>

/**
 * Position struct for hexagonal grid coordinates using axial coordinate system
 * (q, r) where q is the column and r is the row
 * 
 * DESIGN DECISION: Using axial coordinates (q, r) instead of cube coordinates
 * because they're more memory-efficient (2 ints vs 3) and sufficient for Hive.
 */
struct Position {
    int q;  // column coordinate
    int r;  // row coordinate
    
    Position() : q(0), r(0) {}
    Position(int q, int r) : q(q), r(r) {}
    
    // Equality comparison (needed for unordered_map)
    bool operator==(const Position& other) const {
        return q == other.q && r == other.r;
    }
    
    bool operator!=(const Position& other) const {
        return !(*this == other);
    }
};

/**
 * Hash function for Position to use with unordered_map
 * 
 * TODO: Consider alternatives - e.g q and r as 16 bits and concatenate then hash
 */
namespace std {
    template <>
    struct hash<Position> {
        std::size_t operator()(const Position& pos) const {
            return std::hash<int>()(pos.q) ^ (std::hash<int>()(pos.r) << 1);
        }
    };
}

