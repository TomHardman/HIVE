#pragma once
#include "Game.h"

/**
 * View: Rendering layer (placeholder for Qt/OpenGL integration)
 * 
 * DESIGN DECISION: Keeping this minimal as you'll integrate Qt and OpenGL later.
 * The View should only READ from the Game model, never modify it.
 * 
 * When fully implemented with Qt:
 * - Inherit from QOpenGLWidget (similar to your Python BoardCanvas)
 * - Override paintGL() for rendering
 * - Use TileRenderer namespace for actual drawing
 */

/**
 * TileRenderer: Stateless rendering functions using tag dispatch
 * 
 * DESIGN DECISION: Using namespace instead of class (like MoveFetcher)
 * since these are pure functions with no state.
 * 
 * TODO: Implement rendering when integrating OpenGL
 * - renderTile(screen_x, screen_y, tile, z_index)
 * - renderHexagon(screen_x, screen_y, radius, color)
 * - renderInsect(screen_x, screen_y, insect_type)
 * Similar to your Python drawing.py
 */
namespace TileRenderer {
    // TODO: Add rendering functions
    // void renderTile(float x, float y, const HiveTile& tile, int z_index = 0);
    // void renderHexagon(float x, float y, float radius, bool filled = true);
    // Overloaded rendering per insect type using tag dispatch
}

/**
 * ViewState: GUI-specific state separate from game logic
 * 
 * DESIGN DECISION: Separating GUI state (pan, zoom, selection) from game state
 * following the MVC pattern we discussed.
 * 
 * Manages:
 * - Camera/viewport (pan, zoom)
 * - UI selection state (what tile is being dragged)
 * - Coordinate transformations (board <-> screen)
 */
class ViewState {
public:
    ViewState() : pan_x_(0), pan_y_(0), zoom_(1.0f) {}
    
    // TODO: Add coordinate transformation methods
    // Position screenToBoard(float screen_x, float screen_y) const;
    // std::pair<float, float> boardToScreen(const Position& board_pos) const;
    
private:
    float pan_x_;
    float pan_y_;
    float zoom_;
    
    // TODO: Selection state
    // std::optional<Position> selected_tile_pos_;
    // bool is_dragging_;
};

