#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/operators.h>

#include "Game.h"
#include "Position.h"
#include "Pieces.h"

namespace py = pybind11;

PYBIND11_MODULE(hive_engine, m) {
    m.doc() = "HIVE game engine — C++ backend exposed via pybind11";

    // ── Position ──────────────────────────────────────────────────────────
    py::class_<Position>(m, "Position")
        .def(py::init<int, int>(), py::arg("q"), py::arg("r"))
        .def_readwrite("q", &Position::q)
        .def_readwrite("r", &Position::r)
        .def(py::self == py::self)
        .def("__hash__", [](const Position& p) {
            return std::hash<Position>{}(p);
        })
        .def("__repr__", [](const Position& p) {
            return "Position(" + std::to_string(p.q) + ", " + std::to_string(p.r) + ")";
        });

    // ── Insect enum ───────────────────────────────────────────────────────
    py::enum_<Insect>(m, "Insect")
        .value("ANT",         Insect::ANT)
        .value("BEETLE",      Insect::BEETLE)
        .value("GRASSHOPPER", Insect::GRASSHOPPER)
        .value("SPIDER",      Insect::SPIDER)
        .value("QUEEN",       Insect::QUEEN)
        .export_values();

    // ── HiveTile ──────────────────────────────────────────────────────────
    py::class_<HiveTile>(m, "HiveTile")
        .def(py::init<int, Insect, int>(),
             py::arg("player"), py::arg("insect"), py::arg("id"))
        .def_readwrite("player", &HiveTile::player)
        .def_readwrite("insect", &HiveTile::insect)
        .def_readwrite("id",     &HiveTile::id)
        .def(py::self == py::self)
        .def("__hash__", [](const HiveTile& t) {
            return std::hash<HiveTile>{}(t);
        })
        .def("__repr__", [](const HiveTile& t) {
            return "HiveTile(player=" + std::to_string(t.player) +
                   ", insect=" + std::to_string(static_cast<int>(t.insect)) +
                   ", id="     + std::to_string(t.id) + ")";
        });

    // ── Action ────────────────────────────────────────────────────────────
    py::class_<Action>(m, "Action")
        .def(py::init<int, Position>(), py::arg("tile_idx"), py::arg("to"))
        .def_readwrite("tile_idx", &Action::tile_idx)
        .def_readwrite("to",       &Action::to)
        .def(py::self == py::self)
        .def("__repr__", [](const Action& a) {
            return "Action(tile_idx=" + std::to_string(a.tile_idx) +
                   ", to=Position(" + std::to_string(a.to.q) +
                   ", " + std::to_string(a.to.r) + "))";
        });

    // ── Game ──────────────────────────────────────────────────────────────
    py::class_<Game>(m, "Game")
        .def(py::init<int, bool>(),
             py::arg("max_turns") = -1,
             py::arg("simplified_game") = false)

        // Queries
        .def("get_valid_placements", &Game::getValidPlacements,
             py::arg("insect"),
             "Returns valid placement positions for the current player and insect type.")
        .def("get_valid_moves", &Game::getValidMoves,
             py::arg("position"),
             "Returns valid move destinations for the top tile at position.")
        .def("get_legal_actions", &Game::getLegalActions,
             "Returns all legal actions for the current player.")
        .def("check_game_over", &Game::checkGameOver,
             "Returns 0 (ongoing), 1 (player 1 wins), or 2 (player 2 wins).")
        .def("get_current_player", &Game::getCurrentPlayer,
             "Returns the current player (1 or 2).")

        // Mutations
        .def("apply_action", &Game::apply_action,
             py::arg("action"),
             "Applies action; returns original Position if movement, None if placement.")
        .def("undo", &Game::undo,
             py::arg("action"), py::arg("original_pos"),
             "Undoes a previously applied action.")

        // State access
        .def("get_tile_positions", &Game::getTilePositions,
             py::return_value_policy::reference_internal,
             "Returns dict mapping Position → list[HiveTile] (bottom-to-top stacks).")
        .def("get_player_hands", &Game::getPlayerHands,
             py::return_value_policy::reference_internal,
             "Returns [player1_hand, player2_hand], each a set of HiveTile.")
        .def("get_queen_positions", &Game::getQueenPositions,
             py::return_value_policy::reference_internal,
             "Returns [p1_queen_pos, p2_queen_pos], each Optional[Position].")
        .def("get_player_turns", &Game::getPlayerTurns,
             py::return_value_policy::reference_internal,
             "Returns [p1_turns, p2_turns] — moves made by each player so far.");
}
