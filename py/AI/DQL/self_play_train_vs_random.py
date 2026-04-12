from .networks import DQN, DQN_gat, DQN_simple
from AI.agents import DQLAgent, RandomAgent
from game import HiveBoard
from .rl_helper import ExperienceReplay, RewardCalculator, get_graph_from_state, Transition, REWARDS_DICT, LossBuffer

import copy
import torch
import argparse

torch.autograd.set_detect_anomaly(True)


def update(q_network, target_network, experience_replay, batch_size,
           gamma, optimizer, criterion, debug=False):
    """
    Update q_network params using double q learning
    """
    if len(experience_replay) < batch_size:
        return

    transitions = experience_replay.sample(batch_size)
    predictions = []
    tgts = []
    debug_info = {
        'action_node_mappings': [],
        'pred_q_values': [],
        'target_q_values': [],
        'rewards': [],
        'action_mask_coverage': []
    }

    for i, transition in enumerate(transitions):
        s, s_prime, action, r = transition.s, transition.s_prime, transition.action, transition.reward

        if action:
            # Check if action position exists in mapping
            action_pos = action[0]
            if action_pos not in s.pos_node_mapping:
                if debug:
                    print(f'WARNING: Action position {action_pos} not in pos_node_mapping')
                continue

            node_idx = s.pos_node_mapping[action_pos]
            piece_idx = action[1]

            q_values = q_network(s)
            pred = q_values[node_idx, piece_idx]

            with torch.no_grad():
                # use online network to get action and target network to evaluate it
                q_values_prime = q_network(s_prime)
                next_action_idx = torch.argmax(q_values_prime).item()
                q_values_tgt = target_network(s_prime)
                q_tgt = q_values_tgt[next_action_idx//11, next_action_idx % 11]

            y = r + gamma * q_tgt

            predictions.append(pred)
            tgts.append(y)

            if debug and i < 3:  # Log first 3 transitions
                debug_info['action_node_mappings'].append((action_pos, node_idx, piece_idx))
                debug_info['pred_q_values'].append(pred.item())
                debug_info['target_q_values'].append(q_tgt.item())
                debug_info['rewards'].append(r)
                debug_info['action_mask_coverage'].append(s.action_mask[node_idx, piece_idx].item())

    if not predictions:
        return None

    # Convert lists to tensors for computing loss
    predictions = torch.stack(predictions)
    tgts = torch.stack(tgts)

    if debug:
        print(f'  Batch stats:')
        print(f'    Num valid transitions: {len(predictions)}')
        print(f'    Pred Q-values: min={predictions.min():.4f}, max={predictions.max():.4f}, mean={predictions.mean():.4f}')
        print(f'    Target Q-values: min={tgts.min():.4f}, max={tgts.max():.4f}, mean={tgts.mean():.4f}')
        print(f'    First 3 transitions:')
        for i in range(min(3, len(debug_info['pred_q_values']))):
            pos, node, piece = debug_info['action_node_mappings'][i]
            print(f'      Action: pos={pos}, node={node}, piece={piece} | '
                  f'Pred Q={debug_info["pred_q_values"][i]:.4f}, '
                  f'Target Q={debug_info["target_q_values"][i]:.4f}, '
                  f'Reward={debug_info["rewards"][i]:.4f}, '
                  f'Action mask={debug_info["action_mask_coverage"][i]}')

    optimizer.zero_grad()
    loss = criterion(predictions, tgts)
    loss.backward()

    # Check for NaN gradients
    has_nan_grad = False
    for param in q_network.parameters():
        if param.grad is not None and torch.isnan(param.grad).any():
            has_nan_grad = True
            break

    if debug and has_nan_grad:
        print('  WARNING: NaN gradients detected!')

    optimizer.step()

    return loss.item()


def main(args):
    replay = ExperienceReplay(args.capacity)
    reward_calc = RewardCalculator(REWARDS_DICT, debug=args.debug)
    loss_buffer = LossBuffer()

    if args.reduced:
        input_dim = 13
    else:
        input_dim = 25

    dqn = DQN_simple(input_dim)
    tgt_qn = DQN_simple(input_dim)

    if args.model_path:
        state_dict = torch.load(args.model_path)
        dqn.load_state_dict(state_dict)
        tgt_qn.load_state_dict(state_dict)
    else:
        tgt_qn = copy.deepcopy(dqn)

    rl_agent = DQLAgent(1, dqn, args.epsilon, reduced=args.reduced)
    random_agent = RandomAgent(2)

    optimizer = torch.optim.Adam(dqn.parameters(), lr=args.learning_rate)
    criterion = torch.nn.MSELoss()

    i = 0
    game_n = 1

    # Reward tracking
    reward_history = []
    results = []
    nonzero_reward_count = 0
    best_avg_reward = float('-inf')

    while i < args.max_iter:
        board = HiveBoard(max_turns=100, simplified_game=args.simplified_game)
        prev_state = board.get_game_state(1)

        rl_agent.set_board(board)
        random_agent.set_board(board)

        game_reward = 0
        game_steps = 0

        while (result := board.game_over()) == False and i < args.max_iter:
            # DQN agent plays as player 1
            action = rl_agent.sample_action()

            # Random agent plays as player 2
            if result == False:  # only sample p2 action if game is not over
                random_agent.sample_action()

            current_state = board.get_game_state(1)
            s = get_graph_from_state(prev_state, 1, reduced=args.reduced)
            s_prime = get_graph_from_state(current_state, 1, reduced=args.reduced)
            reward = reward_calc(1, prev_state, current_state)
            done = board.game_over() != False

            if action:
                transition = Transition(s, s_prime, action, reward, done)
                replay.push(transition)
                game_reward += reward
                if reward != 0:
                    nonzero_reward_count += 1
                reward_history.append(reward)

            prev_state = copy.deepcopy(current_state)
            game_steps += 1
            i += 1

            if i % args.DQN_update_freq == 0:
                #debug_update = (i % (args.DQN_update_freq * 10) == 0)  # Debug every 10 updates
                debug_update = False
                loss = update(dqn, tgt_qn, replay, args.batch_size, args.gamma, optimizer, criterion, debug=debug_update)
                if debug_update and loss:
                    print(f'  Total Loss: {loss}')

            if i % args.target_update_freq == 0:
                tgt_qn.load_state_dict(dqn.state_dict())

            if i % 1000 == 0:
                rl_agent.epsilon = max(0.1, rl_agent.epsilon - 0.004)

                # Log reward statistics
                avg_reward = sum(reward_history) / len(reward_history) if reward_history else 0
                nonzero_pct = 100 * nonzero_reward_count / len(reward_history) if reward_history else 0
                win_rate = (results.count(1) / len(results)) if results else 0.0
                print(f'=== Iteration {i} ===')
                print(f'Avg reward per transition: {avg_reward:.4f}')
                print(f'Games Played: {len(results)}')
                print(f'Win rate: {win_rate:.1%}')
                print(f'Non-zero rewards: {nonzero_pct:.1f}% ({nonzero_reward_count}/{len(reward_history)})')
                print(f'Epsilon: {rl_agent.epsilon:.3f}')
                print(f'Loss: {loss}, Avg Loss: {loss_buffer.avg}')

                # Save model if new best average reward
                if avg_reward > best_avg_reward:
                    best_avg_reward = avg_reward
                    torch.save(
                        dqn.state_dict(),
                        args.save_path + '_vs_random_gamma_' + str(args.gamma) + '_it_' + str(i) + '_avg_reward_' + str(round(avg_reward, 4)) + '.pt'
                    )
                    print(f'✓ New best! Saved model (avg_reward: {avg_reward:.4f})')
                else:
                    print(f'  (No save - best is still {best_avg_reward:.4f})')

                reward_history = []
                results = []
                nonzero_reward_count = 0

        game_n += 1
        results.append(result)

    torch.save(dqn.state_dict(), args.save_path + 'vs_random_final_' + str(i) + '.pt')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train a DQN agent to play Hive against a random opponent')
    parser.add_argument('--batch_size', type=int, default=25, help='Batch size for updates')
    parser.add_argument('--model_path', type=str, default='models/simplified_sur_only_vs_random_gamma_0.8_it_284000_winrate_0.9192.pt', help='Path to pretrained model')
    parser.add_argument('--DQN_update_freq', type=int, default=25, help='Update frequency')
    parser.add_argument('--target_update_freq', type=int, default=10000, help='Target network update frequency')
    parser.add_argument('--gamma', type=float, default=0.9, help='Discount factor')
    parser.add_argument('--learning_rate', type=float, default=5e-4, help='Learning rate')
    parser.add_argument('--epsilon', type=float, default=0.9, help='Initial epsilon for epsilon-greedy')
    parser.add_argument('--capacity', type=int, default=10000, help='Replay buffer capacity')
    parser.add_argument('--max_iter', type=int, default=10000000, help='Maximum iterations')
    parser.add_argument('--save_path', type=str, default='models/', help='Path to save models')
    parser.add_argument('--simplified_game', action='store_true', help='Use simplified game rules')
    parser.add_argument('--reduced', action='store_true', help='Use reduced feature set')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging for rewards')

    args = parser.parse_args()
    main(args)
