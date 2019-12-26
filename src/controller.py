""" The controller module will do what the old REINFORCE file did.
    It has to implement the following methods:
    - get_action(state)
    - update_policy(episode)
    
    Change the controller? Attention model or bidirectional RNN.
"""

# TODO: Take out -1 in policy_update, fix gradient descent with exploration, fix getting same architectures, parameters remain same over training
# TODO: Fixed gradient descent with exploration by using with torch.no_grad():
# TODO: Fix init of state for a new episode because same param and same input wont change much
# Get the warning with no exploration  UserWarning: To copy construct from a tensor, it is recommended to use sourceTensor.clone().detach() or sourceTensor.clone().detach().requires_grad_(True), r
# ather than torch.tensor(sourceTensor).
#output, hidden_states = cell(torch.tensor(state[i], dtype=torch.float).view(1, 1, 1), hidden_states)

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from torch.autograd import Variable

#constants##
GAMMA = 0.9

class controller(nn.Module):

    def __init__(self, max_layers): # x is a state
        #TODO: create controller architecture
        super(controller,self).__init__()
        
        cells = []
        cell1 = nn.LSTM(input_size = 1, hidden_size=3, num_layers=1)
        cell2 = nn.LSTM(input_size = 1, hidden_size=3, num_layers=1)
        cell3 = nn.LSTM(input_size = 1, hidden_size=3, num_layers=1)
        cell4 = nn.LSTM(input_size = 1, hidden_size=3, num_layers=1)
        cell5 = nn.LSTM(input_size = 1, hidden_size=3, num_layers=1)
        cells.append(cell1)
        cells.append(cell2)
        cells.append(cell3)
        cells.append(cell4)
        cells.append(cell5)
        cells=[cells*max_layers][0]

        self.cells = nn.ModuleList(cells) # better name: layers
        self.num_layers = 5*max_layers
        self.optimizer = optim.Adam(self.parameters(), lr=1e-3)
        self.exploration = 0.90
            
    def forward(self, state):
        logits = []
        softmax = nn.Softmax(1)
 
        for i,cell in enumerate(self.cells):
            # state_i = torch.tensor(state[i], dtype=torch.float).view(1,1,1)
            if(i==0):
                output, hidden_states = cell(torch.tensor(state[i], dtype=torch.float).view(1,1,1))
                # for element in hidden_states:
                #     element.clone().detach().requires_grad_(True)
            else:
                output, hidden_states = cell(torch.tensor(state[i], dtype=torch.float).view(1,1,1), hidden_states)
                # for element in hidden_states:
                #     element.clone().detach().requires_grad_(True)
            output = output.reshape(1,3) # this is the logit
            logit = softmax(output)
            logits.append(logit)
        return logits
    
    def add_layer(self):
        self.cells = self.cells.append(self.cells[0])
        self.cells = self.cells.append(self.cells[1])
        self.cells = self.cells.append(self.cells[2])
        self.cells = self.cells.append(self.cells[3])
        self.cells = self.cells.append(self.cells[4])

    def exponential_decayed_epsilon(self, step):
        # Decay every decay_steps interval
        decay_steps = 2
        decay_rate = 0.9
        return self.exploration * decay_rate ** (step / decay_steps)

    def get_action(self, state, ep): # state = sequence of length 5 times number of layers
        # if (np.random.random() < self.exponential_decayed_epsilon(ep)) and (ep > 0):
        if np.random.random() < self.exponential_decayed_epsilon(ep):
            logits = []
            random_logits = []
            for _ in range(len(state)):
                logit = torch.zeros((1, 3), requires_grad=True)
                with torch.no_grad():
                    logit[0, random.randrange(0, 3, 1)] = 1
                logits.append(logit)
            actions = [torch.argmax(logit) for logit in logits]
        else:
            logits = self.forward(state)
            actions = [torch.argmax(logit) for logit in logits]
        return actions, logits
    
    # REINFORCE
    def update_policy(self, rewards, logits):
        discounted_rewards = []

        for t in range(len(rewards)):
            Gt = 0 
            pw = 0
            for r in rewards[t:]:
                Gt = Gt + GAMMA**pw * r
                pw = pw + 1
            discounted_rewards.append(Gt)
            
        discounted_rewards = torch.tensor(discounted_rewards)
        #discounted_rewards = (discounted_rewards - discounted_rewards.mean()) / (discounted_rewards.std() + 1e-4) # normalize discounted rewards
    
        policy_gradient = []
        # logits = torch.tensor(logits)
        # logits = logits.flatten(1,-1)
        # logits is a list of lists where the outer contains all steps taken, the inner for a given step length  has 10 elements where each element is a tensor of length 3
        for logit, Gt in zip(logits, discounted_rewards):
            for element in logit:
                element = torch.max(element)
                policy_gradient.append(-1.0 * torch.log(element) * Gt)
                # for index in range(3):
                #     policy_gradient.append(-1.0 * torch.log(element[0, index].type(torch.float)) * Gt)
            # policy_gradient.append(-1*torch.tensor(logit) * torch.tensor(Gt))
        
        self.optimizer.zero_grad()
        policy_gradient = torch.stack(policy_gradient).sum() * (1 / len(logits))
        policy_gradient.backward()
        self.optimizer.step()
        














