# Hive C++ Skeleton - Quick Reference

## Files Created

### Core Model
- **Position.h** - Hexagonal grid position type with hash function
- **Pieces.h** - HiveTile struct + tag types for dispatch
- **Game.h/cpp** - Main game model class
- **MoveFetcher.h/cpp** - Movement validation logic (namespace)

### MVC Components  
- **Controller.h/cpp** - Input handling (minimal skeleton)
- **View.h** - Rendering layer (placeholder for Qt/OpenGL)

### Build & Documentation
- **CMakeLists.txt** - Updated build configuration
- **ARCHITECTURE.md** - Complete design decisions documentation
- **example.cpp** - Usage demonstration

## Building the Project

```bash
cd /Users/tomhardman/Documents/Projects/HIVE/HIVE/cpp/build
cmake ..
make

# Run example
./HiveExample
```

## Design Highlights

### 1. **Pure Data Tiles**
```cpp
struct HiveTile {
    int player;      // 1 or 2
    Insect insect;   // ANT, BEETLE, etc.
};
```
No methods, no position - just data!

### 2. **Tag Dispatch for Move Validation**
```cpp
// Automatic dispatch based on insect type
auto moves = MoveFetcher::getValidMoves(pos, tile, board);

// Internally uses tag dispatch:
std::vector<Position> getValidMoves(pos, board, AntTag{});
std::vector<Position> getValidMoves(pos, board, BeetleTag{});
// etc.
```

### 3. **Single Source of Truth**
```cpp
class Game {
    // Position stored ONLY here:
    std::unordered_map<Position, std::vector<HiveTile>> tile_positions_;
    
    // No duplication in tiles or view!
};
```

### 4. **Type-Safe State**
```cpp
std::array<int, 2> player_turns_;                    // Fixed size
std::array<std::optional<Position>, 2> queen_positions_;  // Explicit "not placed"
std::array<std::unordered_set<HiveTile>, 2> player_hands_;  // Fast lookup
```

## API Usage Examples

### Creating a Game
```cpp
Game game;  // Auto-initializes with all pieces in hands
```

### Placing Pieces
```cpp
bool success = game.place(Insect::QUEEN, Position(0, 0));
if (success) {
    fmt::print("Queen placed!\n");
}
```

### Getting Valid Moves
```cpp
Position pos(0, 0);
auto moves = game.getValidMoves(pos);  // Returns vector<Position>
```

### Querying Game State
```cpp
int current_player = game.getCurrentPlayer();  // 1 or 2
const auto& board = game.getTilePositions();   // Read-only access
const auto& hands = game.getPlayerHands();     // Read-only access
int winner = game.checkGameOver();             // 0 = not over, 1/2 = winner
```

## What's Implemented

✅ Complete skeleton structure  
✅ Type-safe interfaces  
✅ Tag dispatch framework  
✅ Helper functions (getNeighbors, canSlideInto, etc.)  
✅ Game initialization  
✅ Basic place/move validation hooks  
✅ MVC separation  

## What Needs Implementation (TODO)

🔨 **MoveFetcher.cpp** - Specific insect movement algorithms:
   - `getValidMoves(..., AntTag)` - BFS around hive
   - `getValidMoves(..., BeetleTag)` - Climbing logic
   - `getValidMoves(..., GrasshopperTag)` - Straight-line jumping
   - `getValidMoves(..., SpiderTag)` - Exactly 3 spaces
   - `getValidMoves(..., QueenTag)` - One space

🔨 **Game.cpp** - Game rule validation:
   - `isValidPlacement()` - Adjacency rules, first turn logic
   - `checkGameOver()` - Win condition detection
   - `getValidPlacements()` - All valid placement positions

🔨 **View.h** - Qt/OpenGL integration:
   - Inherit from QOpenGLWidget
   - Coordinate transformations
   - Rendering functions

🔨 **Controller.h** - Event handling:
   - Mouse/keyboard events
   - Screen ↔ board coordinate conversion

## Key Principles Applied

1. **Data vs Behavior** - Tiles are data, logic is separate
2. **Single Responsibility** - Each class has one job
3. **Single Source of Truth** - Position stored once
4. **Compile-Time Dispatch** - Zero-overhead polymorphism
5. **Type Safety** - Strong types prevent errors
6. **MVC Separation** - Clean architecture boundaries

## Next Steps

1. Implement move algorithms in `MoveFetcher.cpp`
2. Implement placement validation in `Game.cpp`
3. Add win condition checking
4. Integrate Qt for rendering
5. Add unit tests

## Questions to Consider

1. **Tile Identity**: Do you need unique IDs to distinguish multiple ants/beetles?
2. **Action Space**: What format for `getLegalActions()` for AI?
3. **Undo/Redo**: Need move history?
4. **Serialization**: Save/load game state?

See `ARCHITECTURE.md` for complete design rationale and decisions.

