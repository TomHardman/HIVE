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
    return {};
}

// ============= Helper Functions =============

std::array<Position, 6> getNeighbors(const Position& pos) {
    return {
        Position(pos.q, pos.r + 1),
        Position(pos.q + 1, pos.r),
        Position(pos.q + 1, pos.r - 1),
        Position(pos.q, pos.r - 1),
        Position(pos.q - 1, pos.r),
        Position(pos.q - 1, pos.r + 1)
    };
}

bool canSlideInto(
    const Position& current_pos,
    const std::array<Position, 6>& neighbors,
    int target_idx,
    const TilePositions& tile_positions
) {
    int prev_idx = (target_idx - 1 + 6) % 6;
    int next_idx = (target_idx + 1) % 6;
    bool prev_empty = tile_positions.find(neighbors[prev_idx]) == tile_positions.end();
    bool next_empty = tile_positions.find(neighbors[next_idx]) == tile_positions.end();
    return prev_empty || next_empty;
}

bool isCovered(
    const Position& position,
    const HiveTile& tile,
    const TilePositions& tile_positions
) {
    auto it = tile_positions.find(position);
    if (it == tile_positions.end() || it->second.empty()) return false;
    return it->second.back() != tile;
}

bool isDisconnected(
    const TilePositions& tile_positions,
    const Position* dummy_pos
) {
    if (tile_positions.empty()) return false;

    std::unordered_set<Position> seen;
    std::vector<Position> stack;

    for (const auto& [pos, tiles] : tile_positions) {
        if (dummy_pos && pos == *dummy_pos) continue;
        stack.push_back(pos);
        break;
    }

    if (stack.empty()) return false;

    while (!stack.empty()) {
        Position current = stack.back();
        stack.pop_back();
        if (seen.count(current)) continue;
        seen.insert(current);
        for (const auto& neighbor : getNeighbors(current)) {
            if (dummy_pos && neighbor == *dummy_pos) continue;
            if (tile_positions.find(neighbor) != tile_positions.end() && !seen.count(neighbor))
                stack.push_back(neighbor);
        }
    }

    size_t expected = tile_positions.size() - (dummy_pos ? 1 : 0);
    return seen.size() != expected;
}

bool wouldBreakHive(
    const Position& position,
    const TilePositions& tile_positions
) {
    if (tile_positions.size() < 2) return false;
    TilePositions test = tile_positions;
    auto it = test.find(position);
    if (it != test.end()) {
        it->second.pop_back();
        if (it->second.empty()) test.erase(it);
    }
    return isDisconnected(test, nullptr);
}

// ============= Internal helpers =============

// Remove the top tile at `position` from a copy of tile_positions
static TilePositions boardWithoutTopTile(const Position& position, const TilePositions& tile_positions) {
    TilePositions board = tile_positions;
    auto it = board.find(position);
    if (it != board.end()) {
        it->second.pop_back();
        if (it->second.empty()) board.erase(it);
    }
    return board;
}

// True if `pos` is adjacent to any occupied cell in `tile_positions`
static bool isAdjacentToHive(const Position& pos, const TilePositions& tile_positions) {
    for (const auto& neighbor : getNeighbors(pos)) {
        if (tile_positions.find(neighbor) != tile_positions.end()) return true;
    }
    return false;
}

// ============= Move Calculations per Insect Type =============

std::vector<Position> getQueenMoves(
    const Position& position,
    const TilePositions& tile_positions
) {
    // Board state with queen removed (so slide checks ignore its original position)
    TilePositions board = boardWithoutTopTile(position, tile_positions);

    // If removing queen breaks the hive it cannot move
    if (isDisconnected(board, nullptr)) return {};

    auto neighbors = getNeighbors(position);
    std::vector<Position> valid_moves;

    for (int i = 0; i < 6; i++) {
        const Position& target = neighbors[i];

        // Target must be empty
        if (board.find(target) != board.end()) continue;

        // Slide rule: at least one flanking neighbor must be empty
        if (!canSlideInto(position, neighbors, i, board)) continue;

        // Connectivity: exactly one flanking neighbor occupied (not both empty)
        bool prev_occ = board.find(neighbors[(i - 1 + 6) % 6]) != board.end();
        bool next_occ = board.find(neighbors[(i + 1) % 6]) != board.end();
        if (!prev_occ && !next_occ) continue;

        valid_moves.push_back(target);
    }

    return valid_moves;
}

std::vector<Position> getAntMoves(
    const Position& position,
    const TilePositions& tile_positions
) {
    // Board with ant removed
    TilePositions board = boardWithoutTopTile(position, tile_positions);

    if (isDisconnected(board, nullptr)) return {};

    std::unordered_set<Position> visited;
    std::deque<Position> queue;
    queue.push_back(position);
    visited.insert(position);

    while (!queue.empty()) {
        Position current = queue.front();
        queue.pop_front();

        auto neighbors = getNeighbors(current);
        for (int i = 0; i < 6; i++) {
            const Position& target = neighbors[i];
            if (visited.count(target)) continue;
            if (board.find(target) != board.end()) continue; // occupied

            // Slide rule
            if (!canSlideInto(current, neighbors, i, board)) continue;

            // Stay connected to hive (not both flanking empty)
            bool prev_occ = board.find(neighbors[(i - 1 + 6) % 6]) != board.end();
            bool next_occ = board.find(neighbors[(i + 1) % 6]) != board.end();
            if (!prev_occ && !next_occ) continue;

            visited.insert(target);
            queue.push_back(target);
        }
    }

    visited.erase(position); // ant cannot stay in place
    return std::vector<Position>(visited.begin(), visited.end());
}

std::vector<Position> getBeetleMoves(
    const Position& position,
    const TilePositions& tile_positions
) {
    auto it = tile_positions.find(position);
    if (it == tile_positions.end()) return {};
    int stack_height = static_cast<int>(it->second.size());

    // Ground-level beetle cannot move if doing so breaks the hive
    if (stack_height == 1 && wouldBreakHive(position, tile_positions)) return {};

    auto neighbors = getNeighbors(position);
    std::vector<Position> candidates;

    for (int i = 0; i < 6; i++) {
        const Position& target = neighbors[i];
        auto target_it = tile_positions.find(target);
        bool target_occ = target_it != tile_positions.end();
        int target_height = target_occ ? static_cast<int>(target_it->second.size()) : 0;

        auto prev = neighbors[(i - 1 + 6) % 6];
        auto next_n = neighbors[(i + 1) % 6];
        auto prev_it = tile_positions.find(prev);
        auto next_it = tile_positions.find(next_n);
        int prev_height = (prev_it != tile_positions.end()) ? static_cast<int>(prev_it->second.size()) : 0;
        int next_height = (next_it != tile_positions.end()) ? static_cast<int>(next_it->second.size()) : 0;

        if (!target_occ) {
            // Moving to empty position
            if (stack_height == 1) {
                // Ground level: queen-like slide and connectivity rules
                if (canSlideInto(position, neighbors, i, tile_positions)) {
                    bool prev_occ = prev_height > 0;
                    bool next_occ = next_height > 0;
                    if (prev_occ || next_occ) candidates.push_back(target);
                }
            } else {
                // Elevated: slide rule applied at the beetle's current height
                // Can slide if at least one flanking is lower than beetle height
                if (prev_height < stack_height || next_height < stack_height)
                    candidates.push_back(target);
            }
        } else {
            // Climbing onto an occupied position
            // Gate rule: passage must be open at max(stack_height, target_height)
            int passage_height = std::max(stack_height, target_height);
            if (prev_height < passage_height || next_height < passage_height)
                candidates.push_back(target);
        }
    }

    // Connectivity check: for each candidate, verify hive stays connected after move
    TilePositions board = boardWithoutTopTile(position, tile_positions);
    std::vector<Position> valid_moves;
    for (const auto& target : candidates) {
        if (!isDisconnected(board, nullptr))
            valid_moves.push_back(target);
    }

    return valid_moves;
}

std::vector<Position> getGrasshopperMoves(
    const Position& position,
    const TilePositions& tile_positions
) {
    if (wouldBreakHive(position, tile_positions)) return {};

    // 6 axial directions matching getNeighbors order
    const std::array<std::pair<int, int>, 6> DIRECTIONS = {{
        {0, 1}, {1, 0}, {1, -1}, {0, -1}, {-1, 0}, {-1, 1}
    }};

    std::vector<Position> valid_moves;

    for (const auto& [dq, dr] : DIRECTIONS) {
        Position next{position.q + dq, position.r + dr};

        // Must jump over at least one piece
        if (tile_positions.find(next) == tile_positions.end()) continue;

        // Slide in direction until an empty cell is found
        while (tile_positions.find(next) != tile_positions.end())
            next = Position{next.q + dq, next.r + dr};

        valid_moves.push_back(next);
    }

    return valid_moves;
}

std::vector<Position> getSpiderMoves(
    const Position& position,
    const TilePositions& tile_positions
) {
    // Board with spider removed
    TilePositions board = boardWithoutTopTile(position, tile_positions);

    if (isDisconnected(board, nullptr)) return {};

    std::unordered_set<Position> valid_moves;

    // DFS tracking the current path (no backtracking within a path)
    struct State {
        Position pos;
        int depth;
        std::unordered_set<Position> path;
    };

    std::vector<State> dfs_stack;
    dfs_stack.push_back({position, 0, {position}});

    while (!dfs_stack.empty()) {
        State state = std::move(dfs_stack.back());
        dfs_stack.pop_back();

        if (state.depth == 3) {
            // Spider must move exactly 3 steps and cannot return to start
            if (state.pos != position)
                valid_moves.insert(state.pos);
            continue;
        }

        auto neighbors = getNeighbors(state.pos);
        for (int i = 0; i < 6; i++) {
            const Position& target = neighbors[i];
            if (state.path.count(target)) continue;       // no backtracking
            if (board.find(target) != board.end()) continue; // occupied

            // Same slide and connectivity rules as queen
            if (!canSlideInto(state.pos, neighbors, i, board)) continue;

            bool prev_occ = board.find(neighbors[(i - 1 + 6) % 6]) != board.end();
            bool next_occ = board.find(neighbors[(i + 1) % 6]) != board.end();
            if (!prev_occ && !next_occ) continue;

            auto new_path = state.path;
            new_path.insert(target);
            dfs_stack.push_back({target, state.depth + 1, std::move(new_path)});
        }
    }

    return std::vector<Position>(valid_moves.begin(), valid_moves.end());
}

} // namespace MoveFetcher
