Engine to play the strategy board game HIVE. Game is playable with GUI in player vs player or player vs computer modes.
Experimented with trying to train an agent to play by representing the game as a graph and using deep Q learning with a GCN or GAN 
as the Q-network but this did not prove successful. The minimax-based bot is very limited in how deep it can search due the very high 
branching factor and complexity of generating all legal moves at each game node.