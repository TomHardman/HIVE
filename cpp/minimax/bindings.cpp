#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "MinimaxSearch.h"

namespace py = pybind11;

PYBIND11_MODULE(minimax_engine, m) {
    m.doc() = "HIVE minimax search engine — C++ beam minimax exposed via pybind11";

    py::module_::import("hive_engine");
}
