#include <string>

enum Insect {
    ANT,
    BEETLE,
    GRASSHOPPER,
    SPIDER,
    QUEEN,
}

struct Position {
    int x;
    int y;
}

class HiveTile {
    public:
        int player;
        *HiveBoard board;
}