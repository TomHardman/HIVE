# Hive C++ Architecture

## Design Decisions Summary

This document outlines the key architectural decisions made in the C++ implementation of Hive.

### 1. MVC Pattern

**Model-View-Controller separation:**
- **Model** (`Game.h/cpp`): Pure game logic, no GUI dependencies
- **View** (`View.h`, `TileRenderer` namespace): Rendering only, reads from model
- **Controller** (`Controller.h/cpp`): Handles user input, coordinates Model and View

### 2. Data vs Behavior Separation

**HiveTile is pure data:**
```cpp
struct HiveTile {
    int player;
    Insect insect;
};
```
- No methods, no position storage, no board reference
- Maximum reusability and testability
- Behavior lives in separate classes/namespaces

### 3. Single Source of Truth

**Position stored only in Game class:**
- `tile_positions_` map is the authoritative source
- No duplicate position data in tiles or view
- Prevents synchronization bugs

### 4. Tag Dispatch Pattern

**Compile-time polymorphism for move calculation:**
```cpp
namespace MoveFetcher {
    std::vector<Position> getValidMoves(pos, positions, AntTag{});
    std::vector<Position> getValidMoves(pos, positions, BeetleTag{});
    // etc...
}
```
- Zero runtime overhead
- Type-safe dispatch based on insect enum
- Each insect's logic is isolated

### 5. Namespace vs Class for Utilities

**Using namespaces for stateless utilities:**
- `MoveFetcher` - Movement validation
- `TileRenderer` - Rendering functions

**Rationale:** More idiomatic C++ for pure functions, clearer intent (no state)

### 6. Type Safety Choices

**Strong typing for safety:**
- `enum class Insect` - Prevents implicit conversions
- `std::array<T, 2>` - Fixed-size player data (compile-time size)
- `std::optional<Position>` - Explicit "not placed yet" state
- `const references` - Read-only access to model from view

### 7. Hexagonal Coordinates

**Using axial (q, r) coordinates:**
- More memory-efficient than cube (q, r, s)
- Sufficient for Hive's needs
- Standard in hex grid implementations

### 8. Error Handling

**Returning bool for game actions:**
```cpp
bool place(Insect insect, const Position& position);
bool move(const Position& from, const Position& to);
```
- More efficient for AI move validation (no exceptions)
- Clearer control flow
- Exceptions reserved for truly exceptional cases

### 9. Memory Layout

**Vector for tile stacks:**
```cpp
std::unordered_map<Position, std::vector<HiveTile>> tile_positions_;
```
- Efficient for small stacks (usually 1-2 tiles)
- Beetles can climb, requiring stack support
- Vector gives O(1) top access (back())

### 10. Header Organization

**Minimal includes in headers:**
- Forward declarations where possible
- Include only what's needed
- Reduces compilation time and dependencies

## File Structure

```
cpp/
├── Position.h              # Position struct + hash
├── Pieces.h                # HiveTile + tag types
├── MoveFetcher.h/cpp       # Move validation logic
├── Game.h/cpp              # Main model class
├── Controller.h/cpp        # Input handling (minimal)
├── View.h                  # Rendering (placeholder)
├── CMakeLists.txt          # Build configuration
└── ARCHITECTURE.md         # This file
```

## Future Considerations

### TODO Items Marked in Code:

1. **MoveFetcher.cpp**: Implement specific move algorithms
   - Ant: BFS around hive
   - Beetle: Climbing logic
   - Grasshopper: Straight-line jumping
   - Spider: Exactly 3 spaces
   - Queen: One space movement

2. **Game.cpp**: Implement placement validation
   - First turn logic
   - Adjacency rules
   - Queen placement deadline

3. **Game.cpp**: Implement win condition checking
   - Queen surrounded detection
   - Simplified game rules
   - Draw conditions

4. **Game.h**: Define action representation for `getLegalActions()`
   - Decide on return type structure
   - Consider AI agent needs

5. **View.h**: Qt/OpenGL integration
   - Inherit from QOpenGLWidget
   - Implement coordinate transformations
   - Add rendering functions

6. **Controller.h**: Event handling
   - Mouse/keyboard events
   - Screen to board coordinate conversion

### Open Questions:

1. **Tile Identity**: Current HiveTile only has player + insect. Do we need unique IDs to distinguish multiple ants/beetles of same player?

2. **Action Representation**: How should `getLegalActions()` represent the action space for AI agents?

3. **Undo/Redo**: Will you need move history and undo functionality? (Useful for AI training)

4. **Serialization**: Do you need save/load game state to files?

5. **Network Play**: Future consideration for multiplayer?

## Testing Strategy

Recommended testing approach:

1. **Unit Tests** for MoveFetcher
   - Test each insect type's moves in isolation
   - Test edge cases (one-hive rule, stacking, etc.)

2. **Integration Tests** for Game
   - Test full game flow
   - Test win conditions
   - Test rule enforcement

3. **Property Tests**
   - Invariant: Hive always connected after valid moves
   - Invariant: Only valid moves succeed

## Performance Considerations

- **Move Validation**: Most expensive operation (BFS/DFS)
  - Consider caching for AI lookahead
  - Profile before optimizing

- **Memory**: Current design is memory-efficient
  - ~22 HiveTile structs (2 bytes each)
  - Position map grows with board (typically <50 positions)

- **Rendering**: Separate concern from game logic
  - Game can run headless for AI training
  - Multiple view implementations possible

## Comparison to Python Implementation

### Improvements:
- ✅ No circular dependencies (tile ↔ board)
- ✅ No tile.position duplication
- ✅ Cleaner separation of concerns
- ✅ Type safety (compile-time checking)
- ✅ Better performance (no GIL, compiled)

### Maintained Features:
- Similar API surface for AI agents
- Same game rules and logic
- Compatible action space representation

