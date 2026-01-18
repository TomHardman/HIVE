cmake_minimum_required(VERSION 3.20)
project(HIVE_CPP VERSION 1.0 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Find fmt library
find_package(fmt REQUIRED)

# Experimentation executable
add_executable(Experimentation
    Experimentation.cpp
)

target_link_libraries(Experimentation PRIVATE fmt::fmt)

