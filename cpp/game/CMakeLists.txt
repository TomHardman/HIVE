# ── Core game library ─────────────────────────────────────────────────────────
add_library(HiveGame
    Game.cpp
    MoveFetcher.cpp
)

# Export this directory so dependents can #include "Game.h" etc. directly
target_include_directories(HiveGame PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(HiveGame PRIVATE fmt::fmt)

# ── Example executable ────────────────────────────────────────────────────────
add_executable(HiveExample example.cpp)
target_link_libraries(HiveExample PRIVATE HiveGame fmt::fmt)

# ── pybind11 Python extension → hive_engine ───────────────────────────────────
pybind11_add_module(hive_engine bindings.cpp)
target_link_libraries(hive_engine PRIVATE HiveGame fmt::fmt)

# Output .so directly into py2/ so `import hive_engine` works without
# adding the build directory to PYTHONPATH.
set_target_properties(hive_engine PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/../py2"
)
