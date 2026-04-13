cmake_minimum_required(VERSION 3.20)
project(HIVE_CPP VERSION 1.0 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Find fmt library
find_package(fmt REQUIRED)

# Hive Game Library (core game logic)
add_library(HiveGame
    Game.cpp
    MoveFetcher.cpp
)

target_link_libraries(HiveGame PRIVATE fmt::fmt)

# Experimentation executable (for testing)
add_executable(Experimentation
    Experimentation.cpp
)

target_link_libraries(Experimentation PRIVATE fmt::fmt HiveGame)

# Example executable (demonstrates architecture)
add_executable(HiveExample
    example.cpp
)

target_link_libraries(HiveExample PRIVATE fmt::fmt HiveGame)

# ── pybind11 Python extension ─────────────────────────────────────────────
find_package(pybind11 REQUIRED)

pybind11_add_module(hive_engine bindings.cpp)
target_link_libraries(hive_engine PRIVATE HiveGame fmt::fmt)

# Output the .so directly into py2/ so `import hive_engine` works without
# adding the build directory to PYTHONPATH.
set_target_properties(hive_engine PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/../py2"
)
