""" This module has to build the child architecture
and save the current architecture
    It has to implement:
    - build_child_arch(action, previous_state)
"""
import torch
from torch import nn
import torch.optim as optim
from src.conv_net import conv_net
import numpy as np

max_layers = 10

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class cnn():

    def __init__(self, max_layers, image_size, prev_channels, num_classes, epochs=25):
        #TODO
        # size of filter, stride, channels, maxpool(boolean), max_pool_size
        # Droput? Use same padding for now. 
        # (We may have to change the image_size if we use same)
        # initial_state = list([[3,1,32,2,2]*max_layers][0])#*max_layers #0 means yes to max_pool
        initial_state = [3, 1, 32, 2, 2,
                         3, 1, 32, 0, 2,
                         3, 1, 64, 2, 2,
                         3, 1, 64, 2, 2,
                         3, 1, 64, 0, 2,
                         3, 1, 128, 2, 2,
                         3, 1, 128, 2, 2,
                         3, 1, 128, 2, 2,
                         3, 1, 128, 0, 2,
                         3, 1, 128, 2, 2,
                         3, 1, 128, 2, 2,
                         3, 1, 128, 2, 2,
                         3, 1, 128, 0, 2,
                         3, 1, 128, 2, 2,
                         3, 1, 128, 0, 2]
        self.state = initial_state
        self.image_size = image_size
        self.original_image_size = image_size
        self.prev_channels = prev_channels
        self.num_classes = num_classes
        self.max_layers= max_layers
        self.op_add = [lambda x: x+1 , lambda x: x, lambda x: x-1]
        self.op_mul = [lambda x: x*2, lambda x: x, lambda x: x/2]
        self.epochs = epochs
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        return

    @staticmethod
    def update_size(image_size, kernel_size, stride, padding):
        return int((image_size - kernel_size + 2*padding)/stride + 1)

    @staticmethod
    def get_padding(image_size, kernel_size, stride):
        return np.ceil(((kernel_size - 1) * image_size - stride + kernel_size) / 2)

    def update_image_size(self, state):
        n = self.image_size
        if state[3]==2:
            return n
        k = state[4]  # filter_size
        s = 1  # stride
        return (n-k)/s + 1
    

    def build_child_arch(self, action):
        #TODO
        #max_pool, cnn or avg_pool
        state = []
        self.image_size=self.original_image_size
        for layer in range(self.max_layers):
            action0 = action[0+layer*5]
            action1 = action[1+layer*5]
            action2 = action[2+layer*5]
            action3 = action[3+layer*5]
            action4 = action[4+layer*5]
            state0 = self.op_add[action0](self.state[0+layer*5])
            state1 = self.op_add[action1](self.state[1+layer*5])
            state2 = self.op_mul[action2](self.state[2+layer*5])
            state3 = action3
            state4 = self.op_add[action4](self.state[4+layer*5])
            layer_state = [state0,state1,state2,state3,state4]
            layer_state, _ = self.check_state(layer_state, layer)
            state.extend(layer_state)
            padding = self.get_padding(self.image_size, state[0], state[1])
            #convolution
            self.image_size = self.update_size(self.image_size, state[0], state[1], padding)
            #pooling
            if state[3]!=2:
                self.image_size = self.update_size(self.image_size, state[4], 1, 0)

        self.net = conv_net(state, input_size=self.original_image_size, prev_channels = self.prev_channels, n_class=self.num_classes,device = self.device)
        self.net = self.net.to(device)

        self.state = state
        return self.state
    
    def check_state(self, state, layer):
        count = 0
        padding = self.get_padding(self.image_size, state[0], state[1])
        # 0:size of filter, 1:stride, 2:channels, 3:maxpool(boolean), 4:max_pool_size
        # We must be careful about everything except 3: maxpool(boolean)
        if (state[0]<1 or state[0]>self.image_size):
            state[0] = 1
            count = count+1
        if (state[1]<1 or state[1]>self.image_size + padding - state[0]): # add later
            state[1] = 1
            count = count+1
        if (state[2]<1 or state[2] > 128): # later, penalty for the running time
            state[2] = self.state[2+layer*5]
            count = count+1
        # reducing image size for convolution
        padding = self.get_padding(self.image_size, state[0], state[1])
        image_size = self.update_size(self.image_size, state[0], state[1], padding)
        if (state[4]<1 or state[4] >= image_size):
            state[3] = 2
            count = count+1
        
        return state, count

    def get_reward(self, data_loader):
        data_loader_train, data_loader_test = data_loader
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.SGD(self.net.parameters(), lr=0.005, weight_decay = 0.0005, momentum=0.9, nesterov= True)
        #optimizer = torch.optim.RMSprop(self.net.parameters(), lr = 0.003, momentum = 0.9, eps= 1.e-07)
        schedular = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.8)
        #training_batches =  len(data_loader_train)/3       FOR TQDM!
        for epoch in range(self.epochs):  # loop over the dataset multiple times
            running_loss = 0.0
            for i, data in enumerate(data_loader_train,0):
                # get the inputs; data is a list of [inputs, labels]
                inputs, labels = data
                inputs, labels = inputs.to(device), labels.to(device)
                # zero the parameter gradients
                optimizer.zero_grad()
                # forward + backward + optimize
                outputs = self.net(inputs)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                running_loss += loss.item()
                if i % 800 == 799:
                    break
            schedular.step()

        print('Finished Training')
        
        # class_correct = list(0. for i in range(self.num_classes))
        # class_total = list(0. for i in range(self.num_classes))
        correct = 0
        total = 0
        with torch.no_grad():
            for data in data_loader_test:
                images, labels = data
                images, labels = images.to(device), labels.to(device)
                outputs = self.net(images)
                _, predicted = torch.max(outputs, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
                # c = (predicted == labels).squeeze()
                # for i in range(64):
                #     label = labels[i]
                #     class_correct[label] += c[i].item()
                #     class_total[label] += 1


        reward = correct / total
        #reward = sum(class_correct)/sum(class_total)
        
        return reward

