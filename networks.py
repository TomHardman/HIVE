import torch
import torch.nn.functional as F

from torch_geometric.nn import GCNConv, GATConv
from torch_geometric.data import Data, Batch
from torch_geometric.loader import DataLoader

from rl_helper import GraphState

from torch_geometric.utils import add_self_loops, degree

class DQN(torch.nn.Module):
    def __init__(self, input_dim, hidden_dim=22, output_dim=11, alt=False):
        super().__init__()
        self.conv1 = GCNConv(input_dim, hidden_dim, add_self_loops=True)
        self.conv2 = GCNConv(hidden_dim, hidden_dim, add_self_loops=True)
        self.conv3 = GCNConv(hidden_dim, hidden_dim, add_self_loops=True)
        self.conv4 = GCNConv(hidden_dim, output_dim, add_self_loops=True)
        self.linear = torch.nn.Linear(22, hidden_dim)

        self.alt = alt
        self.linear_alt = torch.nn.Linear(11, 1)
    
    def forward_batch(self, batch):
        x, edge_index, edge_attr = batch.x, batch.edge_index, batch.edge_attr
        u = batch.global_feature_vector
        action_mask = batch.action_mask

        x = F.relu(self.conv1(x, edge_index, edge_attr))
        x = x + F.relu(self.linear(u))
        x = F.relu(self.conv2(x, edge_index, edge_attr))
        x = F.relu(self.conv3(x, edge_index, edge_attr))
        x = (self.conv4(x, edge_index, edge_attr))

        nan_mask = torch.isnan(x)
        contains_nan = torch.any(nan_mask)
    
        if contains_nan:
            print('Contains NaN')
    
        return x + (action_mask - 1) * 1000

    def forward(self, data: Data):
        x, edge_index, edge_attr = data.x, data.edge_index, data.edge_attr
        u = data.u
        action_mask = data.action_mask

        x = F.relu(self.conv1(x, edge_index, edge_attr))
        x = x + F.relu(self.linear(u))
        x = F.relu(self.conv2(x, edge_index, edge_attr))
        x = F.relu(self.conv3(x, edge_index, edge_attr))
        x = (self.conv4(x, edge_index, edge_attr))

        nan_mask = torch.isnan(x)
        contains_nan = torch.any(nan_mask)
    
        if contains_nan:
            print('Contains NaN')

        if self.alt:
            x = self.linear_alt(x)
            x = F.softmax(x, dim=0)
            return x
    
        return x + (action_mask - 1) * 1000


class DQN_gat(torch.nn.Module):
    def __init__(self, input_dim, hidden_dim=22, output_dim=11, num_heads=4, dropout=0.3):
        super().__init__()
        self.gat1 = GATConv(input_dim, hidden_dim, heads=num_heads, dropout=dropout)
        self.gat2 = GATConv(hidden_dim * num_heads, hidden_dim, heads=num_heads, dropout=dropout)
        self.gat3 = GATConv(hidden_dim * num_heads, hidden_dim, heads=num_heads, dropout=dropout)
        self.gat4 = GATConv(hidden_dim * num_heads, output_dim, heads=1, dropout=dropout)  # Only 1 head in final layer
        self.linear = torch.nn.Linear(22, hidden_dim)
    

    def forward(self, data: Data):
        x, edge_index = data.x, data.edge_index
        u = data.u
        action_mask = data.action_mask

        x = F.relu(self.gat1(x, edge_index))
        #x = x + F.relu(self.linear(u))
        x = F.relu(self.gat2(x, edge_index))
        x = F.relu(self.gat3(x, edge_index))
        x = self.gat4(x, edge_index)

        nan_mask = torch.isnan(x)
        contains_nan = torch.any(nan_mask)
    
        if contains_nan:
            print('Contains NaN')
    
        return x + (action_mask - 1) * 1000