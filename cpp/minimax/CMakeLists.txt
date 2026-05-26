# ── Minimax search library ────────────────────────────────────────────────────
add_library(HiveMinimax
    MinimaxSearch.cpp
)

# PUBLIC: consumers of HiveMinimax also get HiveGame's include directories,
# so #include "Game.h" works in both MinimaxSearch.cpp and its dependents.
target_link_libraries(HiveMinimax PUBLIC HiveGame)

# ── pybind11 Python extension → minimax_engine ────────────────────────────────
pybind11_add_module(minimax_engine bindings.cpp)
target_link_libraries(minimax_engine PRIVATE HiveMinimax)

# Output .so directly into py2/ so `import minimax_engine` works without
# adding the build directory to PYTHONPATH.
set_target_properties(minimax_engine PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/../py2"
)
