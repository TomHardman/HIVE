#pragma once
#include "Game.h"

/**
 * Controller: Handles user input and coordinates between Model and View
 * 
 * DESIGN DECISION: Minimal implementation for now as requested.
 * Will expand as you integrate Qt and OpenGL.
 * 
 * Responsibilities (when fully implemented):
 * - Process mouse/keyboard events from Qt
 * - Translate screen coordinates to board positions
 * - Validate user actions
 * - Update Model (Game)
 * - Trigger View updates
 */
class Controller {
public:
    /**
     * Constructor takes a reference to the game model
     * 
     * DESIGN DECISION: Using reference rather than pointer to express
     * that Controller must always have a valid Game instance.
     */
    explicit Controller(Game& game);
    
    // TODO: Add event handlers when integrating Qt
    // void onMouseClick(int screen_x, int screen_y);
    // void onTileSelected(const Position& pos);
    // void onPlacementRequested(Insect insect, const Position& pos);
    // etc.
    
private:
    Game& game_;  // Reference to model (non-owning)
};

