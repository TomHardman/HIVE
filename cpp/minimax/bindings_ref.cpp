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

    // ── minimax_select_action ─────────────────────────────────────────────
    // Accepts a minimax_utils.MinimaxParams Python dataclass directly —
    // no separate C++ params type is exposed to Python.
    m.def("minimax_select_action",
        [](Game& game, const py::object& params) {
            MinimaxParams cpp_params;
            cpp_params.depth                    = params.attr("depth").cast<int>();
            cpp_params.beam_width               = params.attr("beam_width").cast<int>();
            cpp_params.queen_surrounding_reward = params.attr("queen_surrounding_reward").cast<float>();
            cpp_params.ownership_reward         = params.attr("ownership_reward").cast<float>();
            cpp_params.win_reward               = params.attr("win_reward").cast<float>();
            cpp_params.mp_reward                = params.attr("mp_reward").cast<float>();
            return MinimaxSearch::selectAction(game, cpp_params);
        },
        py::arg("game"),
        py::arg("params"),
        "Run beam-search minimax from the current game state.\n"
        "params should be a minimax_utils.MinimaxParams dataclass instance.\n"
        "Returns the best hive_engine.Action for the current player, "
        "or None if there are no legal moves.\n\n"
        "The game object is mutated during search (apply_action / undo) but "
        "is always restored to its original state before returning.");
}
