

----------------------- Model --------------------------
Game - main model class
{

Members:

  // members that define game state
  player_hands - pair of unordered sets
  queen_positions - pair of positions (Struct int x int y)
  tile_positions - unordered map mapping position to list (stack) of HiveTiles
  player_turns - pair of ints
   

Public Methods:
    std::vector<Position> getValidPlacements() - gets valid placements for current player
    std::vector<Position> getValidMoves() - I think this should wrap a static call to MoveFetcher.getMoves(position, TypeOf(tile_positions)&) but feel free to implement differently
    getLegalActions() - gets all legal actions. Unsure exactly what this will entail but will be somewhat similar to python implmentation and allow an agent to fetch entire action space
    void place(tile, position) - puts a tile in a position and updates game state
    void move(tile, position) - moves a tile to a position and updates game state

}

MoveFetcher - class that is purely used in a static context for fetching moves for a given tile. If it makes more sense to use a namespace here then do this
{
    public methods:
    std::vector<Position> getValidMoves(position, tile_positions) - uses tag dispatch to select correct overload depending on insect type (enum) PLEASE IMPLEMENT THIS

    private methods:
     std::vector<Position> getValidMoves(position, tile_positions AntTag{}) etc.
     will contain other private methods for common move validation logic - add method for anything you see in the Python code
}

Pieces: structure already defined in pieces.h - separate struct type for each insect that just stores player and insect type


----------------------- View ------------------------
Should only have access to game as model. Renders based on tile positions. Separate class / namespace for rendering logic using tag dispatch
ß

--------------------- Controller ----------------------
Implement just a constructor for now