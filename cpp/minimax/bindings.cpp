#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "MinimaxSearch.h"

namespace py = pybind11;

PYBIND11_MODULE(minimax_engine, m) {
    m.doc() = "HIVE minimax search engine — C++ beam minimax exposed via pybind11";

    // Import hive_engine so that Game / Action / Position types are already
    // registered in pybind11's global type registry before we reference them
    // here.  This guarantees that actions returned by minimax_select_action
    // are recognised as hive_engine.Action objects on the Python side.
    py::module_::import("hive_engine");

    // ── MinimaxParams ─────────────────────────────────────────────────────
    py::class_<MinimaxParams>(m, "MinimaxParams")
        .def(py::init<>())
        .def_readwrite("depth",                    &MinimaxParams::depth)
        .def_readwrite("beam_width",               &MinimaxParams::beam_width)
        .def_readwrite("queen_surrounding_reward", &MinimaxParams::queen_surrounding_reward)
        .def_readwrite("ownership_reward",         &MinimaxParams::ownership_reward)
        .def_readwrite("win_reward",               &MinimaxParams::win_reward)
        .def_readwrite("mp_reward",                &MinimaxParams::mp_reward)
        .def("__repr__", [](const MinimaxParams& p) {
            return "MinimaxParams(depth="      + std::to_string(p.depth)
                 + ", beam_width="             + std::to_string(p.beam_width)
                 + ", queen_surrounding_reward=" + std::to_string(p.queen_surrounding_reward)
                 + ", ownership_reward="       + std::to_string(p.ownership_reward)
                 + ", win_reward="             + std::to_string(p.win_reward)
                 + ", mp_reward="              + std::to_string(p.mp_reward) + ")";
        });

    // ── minimax_select_action ─────────────────────────────────────────────
    m.def("minimax_select_action",
        &MinimaxSearch::selectAction,
        py::arg("game"),
        py::arg("params"),
        "Run beam-search minimax from the current game state.\n"
        "Returns the best hive_engine.Action for the current player, "
        "or None if there are no legal moves.\n\n"
        "The game object is mutated during search (apply_action / undo) but "
        "is always restored to its original state before returning.");
}
