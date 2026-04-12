# AI Agents

Three agent types are implemented, all sharing the `Agent` ABC defined in `agents.py`.

---

## RandomAgent (`agents.py`)

Uniformly samples from the legal action set each turn. Zero lookahead, no state evaluation. Used as a baseline opponent during training and as a sanity-check in the arena.

---

## HeuristicAgent (`agents.py` + `minimax/`)

The strongest agent. Uses `beam_minimax()` with alpha-beta pruning to search the game tree.

### How it works

`sample_action()` calls `beam_minimax(board, depth, ...)` on a deep copy of the board. The search returns the best move found up to the given depth.

**`beam_minimax` (minimax.py)** — two-phase search per node:
1. **Beam selection**: apply every legal move shallowly, score with `evaluate()`, keep only the top-k by heuristic score (`beam_width`, default 3).
2. **Recursive search**: run full alpha-beta minimax only on those top-k moves.

This reduces the effective branching factor from ~20–40 legal moves down to `beam_width` per level. Combined with alpha-beta pruning, depth 3 is tractable in pure Python.

**`minimax` (minimax.py)** — standard alpha-beta without beam pruning. Explores all legal moves at each node. Only used directly if called from outside `HeuristicAgent`; the agent uses `beam_minimax`.

### Heuristic evaluation (`minimax/heuristic.py`)

`evaluate(state, player, params)` returns a scalar advantage for `player`:

| Component | Formula | Weight |
|-----------|---------|--------|
| Queen surrounding | `opp_pieces_around_queen − own_pieces_around_queen` | `queen_surrounding_reward` |
| Win/loss | `+win_reward` if winner, `−win_reward` if loser | `win_reward` |
| Queen ownership | net beetle-on-queen control | `ownership_reward` |
| Mobility | `own_moveable_pieces − opp_moveable_pieces` | `mp_reward` |

Typical weights from `arena.py`:
```python
Params(queen_surrounding_reward=1, win_reward=100, ownership_reward=3, mp_reward=0.5)
```

### Configuration

```python
HeuristicAgent(player=1, depth=3, params=Params(...), board=board)
```

- `depth`: search depth (3 is the practical limit in raw Python)
- `beam_width`: passed inside `sample_action` to `beam_minimax` (default 3)

---

## DQLAgent (`agents.py` + `DQL/`)

Uses a Graph Convolutional Network (GCN or GAT) to estimate Q-values for each (position, piece) pair, with an epsilon-greedy action selection policy.

### How it works

`sample_action()` converts the board to a PyTorch Geometric graph via `get_graph_from_state()`, runs a forward pass through the Q-network, masks illegal actions, and picks the action with the highest Q-value.

**Epsilon-greedy**: with probability `epsilon` the agent takes a random legal action instead.

### State representation (`DQL/rl_helper.py`)

The board is converted to a graph each turn:
- **Nodes**: one per on-board tile + adjacent empty spaces + valid placement targets
- **Node features** (25-dim full / 13-dim reduced): one-hot piece type for own and opponent pieces, flags for empty/valid-placement/ownership
- **Edges**: hex adjacency (bidirected) + valid move edges (directed from source to target)
- **Global features** (22-dim): count of each piece type remaining in each player's hand
- **Action mask**: per-node 11-element boolean; illegal actions are masked to −1000 before argmax

### Networks (`DQL/networks.py`)

| Class | Architecture | Use |
|-------|-------------|-----|
| `DQN` | 4-layer GCN, global features injected after layer 1 | Default training |
| `DQN_gat` | 4-layer GAT (4-head → 1-head), same global injection | Attention-based alternative |
| `DQN_simple` | 1-layer GCN | Fast experimentation |

All output 11 Q-values per node (one per piece type in ACTIONSPACE).

### Training (`DQL/self_play_train_vs_random.py`, `self_play_train.py`)

- Double Q-learning with a frozen target network
- Experience replay with 50/50 reward/random sampling
- Reward signal driven by `REWARDS_DICT` weights (default: queen-surrounding only)

---

## Shared Utilities

### `minimax/minimax.py`

| Function | Purpose |
|----------|---------|
| `make_move(board, action)` | Applies a `(pos, tile_idx)` action; returns original position for undo |
| `undo_move(board, action, og_pos)` | Restores board after search step |
| `create_action_list(actions)` | Converts boolean action mask dict → list of `(pos, tile_idx)` tuples |

### `DQL/rl_helper.py`

| Class/Function | Purpose |
|----------------|---------|
| `RewardCalculator` | Computes heuristic reward components from game state dict |
| `get_graph_from_state()` | Builds PyTorch Geometric `Data` object from board state |
| `ReplayMemory` | Fixed-size deque for experience replay |

---

## Agent Comparison

| Agent | Lookahead | Strength | Speed |
|-------|-----------|----------|-------|
| RandomAgent | None | Weakest | Instant |
| HeuristicAgent (depth 3) | 3 ply (beam=3) | Strongest | ~1–5s/move |
| DQLAgent | None (single forward pass) | Moderate (depends on training) | Fast |
