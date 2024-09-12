from .networks import DQN, DQN_gat
from AI.agents import DQLAgent
from game import HiveBoard
from .rl_helper import ExperienceReplay, RewardCalculator, get_graph_from_state, Transition, REWARDS_DICT, LossBuffer

import copy
import torch
import argparse

torch.autograd.set_detect_anomaly(True)


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
    for transition in transitions:
        s, s_prime, action, r = transition.s, transition.s_prime, transition.action, transition.reward
        
        if action:
            q_values = q_network(s)
            pred = q_values[s.pos_node_mapping[action[0]], action[1]]
       
            with torch.no_grad():
                # use online network to get action and target network to evaluate it 
                q_values_prime = q_network(s_prime)
                next_action_idx = torch.argmax(q_values_prime).item()
                q_values_tgt = target_network(s_prime)
                q_tgt = q_values_tgt[next_action_idx//11, next_action_idx % 11]
            
            y = r + gamma * q_tgt

            predictions.append(pred)
            tgts.append(y)

            """optimizer.zero_grad() 
            loss = criterion(pred, y)
            loss.backward()
            optimizer.step()"""
    
    # Convert lists to tensors for computing loss
    predictions = torch.stack(predictions)
    tgts = torch.stack(tgts)
    
    optimizer.zero_grad() 
    loss = criterion(predictions, tgts)
    loss.backward()
    optimizer.step()

    return loss.item()


def udpate_alt(alt_network, experience_replay, batch_size, optimizer, criterion):
    """
    Update step for alternative network that tries to predict queen positition
    """
    if len(experience_replay) < batch_size:
        return
    
    transitions = experience_replay.sample(batch_size)
    predictions = []
    tgts = []

    for transition in transitions:
        s = transition.s
        queen_pos = s.queen_positions[0]
        
        if queen_pos:
            queen_idx = s.pos_node_mapping[queen_pos]
            preds = alt_network(s)
            tgt_tensor = torch.zeros(preds.shape, dtype=torch.float32, requires_grad=True)
            tgt_tensor = tgt_tensor.clone()
            tgt_tensor[queen_idx, :] = 1

            torch.autograd.set_detect_anomaly(True)
            optimizer.zero_grad()
            loss = criterion(preds, tgt_tensor)
            loss.backward()
            optimizer.step()
            predictions.append(preds)
            tgts.append(tgt_tensor)

    return loss.item()


def main(args):
    replay = ExperienceReplay(args.capacity)
    reward_calc = RewardCalculator(REWARDS_DICT)
    loss_buffer = LossBuffer()

    if args.reduced:
        input_dim = 13
    else:
        input_dim = 25

    dqn = DQN_gat(input_dim)
    alt_network = DQN(input_dim, alt=True) # to test if we can successfully predict the position of the queen bee
    tgt_qn = DQN_gat(input_dim)
    
    if args.model_path:
        state_dict = torch.load(args.model_path)
        dqn.load_state_dict(state_dict)
        tgt_qn.load_state_dict(state_dict)
    else:
        tgt_qn = copy.deepcopy(dqn)
    
    rl_agent1 = DQLAgent(1, dqn, args.epsilon, reduced=args.reduced)
    rl_agent2 = DQLAgent(2, tgt_qn, args.epsilon, reduced=args.reduced)

    optimizer = torch.optim.Adam(dqn.parameters(), lr=args.learning_rate)
    criterion = torch.nn.MSELoss()

    i = 0
    game_n = 1

    while i < args.max_iter:
        #print(f'Game: {game_n}, Iteration: {i}')
        board = HiveBoard(max_turns=100, simplified_game=args.simplified_game) 
        prev_state = board.get_game_state(1)

        rl_agent1.set_board(board)
        rl_agent2.set_board(board)

        while (result := board.game_over()) == False and i < args.max_iter:
            action = rl_agent1.sample_action()
            if result == False: # only sample p2 action if game is not over
                rl_agent2.sample_action()
            
            current_state = board.get_game_state(1)
            s = get_graph_from_state(prev_state, 1, reduced=args.reduced)
            s_prime = get_graph_from_state(current_state, 1, reduced=args.reduced)
            reward = reward_calc(1, prev_state, current_state)
            done = board.game_over() != False
            if action:
                transition = Transition(s, s_prime, action, reward, done)
                replay.push(transition)
            prev_state = copy.deepcopy(current_state)
            i += 1

            if i % args.DQN_update_freq == 0:
                print(f'Updating DQN iteration {i}')
                loss = update(dqn, tgt_qn, replay, args.batch_size, args.gamma, optimizer, criterion)
                #alt_loss = udpate_alt(alt_network, replay, args.batch_size, optimizer_alt, criterion)
                loss_buffer.push(loss)
                print(f'Loss: {loss}, Avg Loss: {loss_buffer.avg}')
                #print(f'Alt Loss: {alt_loss}')
            
            if i % args.target_update_freq == 0:
                tgt_qn.load_state_dict(dqn.state_dict())
            
            if i % 10000 == 0:
                torch.save(dqn.state_dict(), args.save_path + 'simplified3_at' + str(i) + '.pt')
                rl_agent1.epsilon = max(0.1, rl_agent1.epsilon - 0.03)
                rl_agent2.epsilon = max(0.1, rl_agent1.epsilon - 0.03)
        
        game_n += 1
        #print(f'Game Over: {result} wins!')

    torch.save(dqn.state_dict(), args.save_path + 'dqn_' + str(i) + '.pt')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train a DQN agent to play Hive')
    parser.add_argument('--batch_size', type=str, default=25, help='path to the pretrained model')
    parser.add_argument('--model_path', type=str, default='')
    parser.add_argument('--max_updates', type=str, default='')
    parser.add_argument('--DQN_update_freq', type=int, default=25)
    parser.add_argument('--target_update_freq', type=int, default=10000)
    parser.add_argument('--gamma', type=float, default=0)
    parser.add_argument('--learning_rate', type=float, default=1e-3)
    parser.add_argument('--epsilon', type=float, default=0.9)
    parser.add_argument('--capacity', type=float, default=10000)
    parser.add_argument('--max_iter', type=float, default=300000)
    parser.add_argument('--save_path', type=str, default='models/')
    parser.add_argument('--simplified_game', type=bool, default=True)
    parser.add_argument('--reduced', type=bool, default=False)

    args = parser.parse_args()
    main(args)

