"""This module implements the CNN, it defines the
 architecture, defined by the state from the CNN module."""


from torch import nn
import numpy as np
import torch

class conv_net(nn.Module):

    def __init__(self, conv_layers, input_size=32, prev_channels=3, n_class=10, device = 'cuda'):
        super(conv_net, self).__init__()

        self.input_size = input_size
        self.n_class = n_class
        self.device = device

        layers = []
        img_dim = input_size

        "Add Convolution Layers, Activation, and BatchNorm"
        for kernel_size, stride, n_channels, pooling, pooling_size in [conv_layers[x:x+5] for x in range(0, len(conv_layers)-1, 5)]:
            n = img_dim
            p = int(np.ceil(((n-1)*stride - n + kernel_size)/2))
            layers += [
                nn.Conv2d(int(prev_channels), int(n_channels), int(kernel_size), stride=int(stride), padding=p),
                nn.ELU(),
                nn.BatchNorm2d(int(n_channels))
            ]
            "Update Image_dim, used to compute self.prev_fc_size "
            img_dim = self.update_size(img_dim, int(kernel_size), int(stride), p)

            " Add Pooling Options ! pooling =0 is max_pool, 1 is avg_pool and 2 is no_pool"
            if pooling==0:
                layers += [
                    nn.MaxPool2d(kernel_size=pooling_size, stride=1, padding=0),
                    nn.Dropout(0.1)
                ]
                img_dim = self.update_size(img_dim, pooling_size, 1, 0)
            if pooling==1:
                layers += [
                        nn.AvgPool2d(kernel_size = pooling_size, stride=1, padding=0),
                        nn.Dropout(0.1)
                ]
                "Update Image_dim, used to compute self.prev_fc_size "
                img_dim = self.update_size(img_dim, pooling_size, 1, 0)

            prev_channels = n_channels

        self.prev_fc_size = int(int(prev_channels) * img_dim * img_dim)


        "The Classification head, that transforms features into classficiation outputs" \
        "Apply some drop out, 2 linear layers with ELU activation"
        layers += [nn.Dropout(0.2),
                   nn.Linear(self.prev_fc_size, 256),
                   nn.ELU(),
                   nn.Linear(256, n_class)
                   ]
        self.layers = layers
        self.layers = nn.ModuleList(layers)

    "Update Image Size"
    def update_size(self, image_size, kernel_size, stride, padding):
        return int((image_size - kernel_size + 2*padding)/stride + 1)

    "Define the forward pass for the CNN"
    def forward(self, x):
        x = x.to(self.device)
        "For each layer, pass x through the layer!"
        for i,layer in enumerate(self.layers):
            "Flatten before the Linear Layers!"
            if(i==len(self.layers)-4):
                x = x.flatten(1,-1)
            x = layer(x)

        return x

