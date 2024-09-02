from networks import DQN
from agents import RLAgent
from board import HiveBoard
from rl_helper import ExperienceReplay, RewardCalculator, get_graph_from_state, Transition, REWARDS_DICT

import copy
import torch
import argparse


def update(q_network, target_network, experience_replay, batch_size,
           gamma, optimizer, criterion):
    """
    Update q_network params using double q learning
    """
    if len(experience_replay) < batch_size:
        return
    
    transitions = experience_replay.sample(batch_size)
    predictions = []
    tgts = []
    with torch.no_grad():
        for transition in transitions:
            s, s_prime, action, r = transition.s, transition.s_prime, transition.action, transition.reward
            
            if action:
                q_values = q_network(s)
                pred = q_values[s.pos_node_mapping[action[0]], action[1]]
                
                # use online network to get action and target network to evaluate it 
                q_values_prime = q_network(s_prime)
                next_action_idx = torch.argmax(q_values_prime).item()
                q_values_tgt = target_network(s_prime)
                q_tgt = q_values_tgt[next_action_idx//11, next_action_idx % 11]
                
                y = r + gamma * q_tgt

                predictions.append(pred)
                tgts.append(y)
    
    # Convert lists to tensors for computing loss
    predictions = torch.stack(predictions)
    tgts = torch.stack(tgts)
    
    optimizer.zero_grad() 
    loss = criterion(predictions, tgts)
    optimizer.step()

    return loss.item()


def main(args):
    replay = ExperienceReplay(args.capacity)
    reward_calc = RewardCalculator(REWARDS_DICT)

    dqn = DQN(25)
    tgt_qn = DQN(25)
    
    if args.model_path:
        state_dict = torch.load(args.model_path)
        dqn.load_state_dict(state_dict)
        tgt_qn.load_state_dict(state_dict)
    else:
        tgt_qn = copy.deepcopy(dqn)
    
    rl_agent1 = RLAgent(1, dqn, args.epsilon)
    rl_agent2 = RLAgent(2, tgt_qn, args.epsilon)

    optimizer = torch.optim.Adam(dqn.parameters(), lr=args.learning_rate)
    criterion = torch.nn.MSELoss()

    i = 0
    game_n = 1

    while i < args.max_iter:
        print(f'Game: {game_n}, Iteration: {i}')
        board = HiveBoard(max_turns=100) 
        prev_state = board.get_game_state(1)

        rl_agent1.set_board(board)
        rl_agent2.set_board(board)

        while (result := board.game_over()) == False and i < args.max_iter:
            action = rl_agent1.sample_action()
            if result == False: # only sample p2 action if game is not over
                rl_agent2.sample_action()
            
            current_state = board.get_game_state(1)
            s = get_graph_from_state(prev_state, 1)
            s_prime = get_graph_from_state(current_state, 1)
            reward = reward_calc(1, prev_state, current_state)
            if action:
                transition = Transition(s, s_prime, action, reward)
                replay.push(transition)
            prev_state = copy.deepcopy(current_state)
            i += 1

            if i % args.DQN_update_freq == 0:
                print(f'Updating DQN iteration {i}')
                loss =update(dqn, tgt_qn, replay, args.batch_size, args.gamma, optimizer, criterion)
                print(f'Loss: {loss}')
            
            if i % args.target_update_freq == 0:
                tgt_qn.load_state_dict(dqn.state_dict())
            
            if i % 20000 == 0:
                torch.save(dqn.state_dict(), args.save_path + 'day' + str(i+60000) + '.pt')
                rl_agent1.epsilon = max(0.1, rl_agent1.epsilon - 0.03)
                rl_agent2.epsilon = max(0.1, rl_agent1.epsilon - 0.03)
        
        game_n += 1
        print(f'Game Over: {result} wins!')

    torch.save(dqn.state_dict(), args.save_path + 'dqn_' + str(i) + '.pt')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train a DQN agent to play Hive')
    parser.add_argument('--batch_size', type=str, default=50, help='path to the pretrained model')
    parser.add_argument('--model_path', type=str, default='/Users/tomhardman/Documents/Engineering/Summer_24/HIVE/models/overnight_60000.pt')
    parser.add_argument('--max_updates', type=str, default='')
    parser.add_argument('--DQN_update_freq', type=int, default=25)
    parser.add_argument('--target_update_freq', type=int, default=2000)
    parser.add_argument('--gamma', type=float, default=0.9)
    parser.add_argument('--learning_rate', type=float, default=1e-4)
    parser.add_argument('--epsilon', type=float, default=0.9)
    parser.add_argument('--capacity', type=float, default=10000)
    parser.add_argument('--max_iter', type=float, default=300000)
    parser.add_argument('--save_path', type=str, default='models/')

    args = parser.parse_args()
    main(args)

