#pragma once
#include <functional>

/**
 * Position struct for hexagonal grid coordinates using axial coordinate system
 * (q, r). q aligned (low left to up right) diagonal, r aligned with vertical
 * TODO: These are non-standard but setup to be consistent with python implementation
 *       will change
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

