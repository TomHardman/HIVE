# Standalone C++ experimentation executable — no game dependency
add_executable(Experimentation Experimentation.cpp)
target_link_libraries(Experimentation PRIVATE fmt::fmt)
