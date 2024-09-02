import torch
import torch.nn.functional as F

from torch_geometric.nn import GCNConv
from torch_geometric.data import Data, Batch

from rl_helper import GraphState

from torch_geometric.utils import add_self_loops, degree

class DQN(torch.nn.Module):
    def __init__(self, input_dim, hidden_dim=22, output_dim=11):
        super().__init__()
        self.conv1 = GCNConv(input_dim, hidden_dim, add_self_loops=True)
        self.conv2 = GCNConv(hidden_dim, hidden_dim, add_self_loops=True)
        self.conv3 = GCNConv(hidden_dim, hidden_dim, add_self_loops=True)
        self.conv4 = GCNConv(hidden_dim, output_dim, add_self_loops=True)
        self.linear = torch.nn.Linear(22, hidden_dim)

    def forward(self, gs : GraphState):
        data = gs.data # gets PyTorch Geometric Data object
        x, edge_index, edge_attr = data.x, data.edge_index, data.edge_attr

        u = gs.global_feature_vector
        action_mask = gs.action_mask

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
    
    def forward2(self, gs: GraphState):
        data = gs.data  # Gets PyTorch Geometric Data object
        x, edge_index, edge_attr = data.x, data.edge_index, data.edge_attr
        u = gs.global_feature_vector
        action_mask = gs.action_mask

        # Check for NaNs in input data
        if torch.isnan(x).any():
            print("NaN detected in input node features x")
        if torch.isnan(edge_index).any():
            print("NaN detected in edge index")
        if edge_attr is not None and torch.isnan(edge_attr).any():
            print("NaN detected in edge attributes")
        if torch.isnan(u).any():
            print("NaN detected in global feature vector u")
        if torch.isnan(action_mask).any():
            print("NaN detected in action mask")

        # Degree normalization
        row, col = edge_index  # Unpack edges
        deg = degree(col, x.size(0), dtype=x.dtype)  # Calculate node degrees
        if torch.isnan(deg).any():
            print("NaN detected in degree computation")

        deg_inv_sqrt = deg.pow(-0.5)  # Compute D^{-1/2}
        deg_inv_sqrt[deg_inv_sqrt == float('inf')] = 0  # Handle inf

        if torch.isnan(deg_inv_sqrt).any():
            print("NaN detected in degree inverse square root")

        # Normalization term
        norm = deg_inv_sqrt[row] * deg_inv_sqrt[col]
        if torch.isnan(norm).any():
            print("NaN detected in normalization term")

        # First GCNConv layer
        x = self.conv1(x, edge_index, edge_attr)
        if torch.isnan(x).any():
            print("NaN detected after first GCNConv layer")

        x = F.relu(x)
        if torch.isnan(x).any():
            print("NaN detected after ReLU activation in first layer")

        # Linear layer for global feature vector
        u = F.relu(self.linear(u))
        if torch.isnan(u).any():
            print("NaN detected after linear layer")

        # Combine x and global features u
        x = x + u
        if torch.isnan(x).any():
            print("NaN detected after combining with global features")

        # Second GCNConv layer
        x = self.conv2(x, edge_index, edge_attr)
        if torch.isnan(x).any():
            print("NaN detected after second GCNConv layer")

        x = F.relu(x)
        if torch.isnan(x).any():
            print("NaN detected after ReLU activation in second layer")

        # Apply action mask
        x = x + (action_mask - 1) * 1000
        if torch.isnan(x).any():
            print("NaN detected after applying action mask")

        return x
