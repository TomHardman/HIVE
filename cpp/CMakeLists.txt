cmake_minimum_required(VERSION 3.20)
project(HIVE_CPP VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

find_package(fmt      REQUIRED)
find_package(pybind11 REQUIRED)

add_subdirectory(game)
add_subdirectory(experimentation)
