import torch
from torchvision import models
from torch import nn


class Resnet18(nn.Module):
    def __init__(self, num_classes, pretrained=True):
        super().__init__()

        resnet18 = models.resnet18(pretrained=pretrained)
        self.features = nn.ModuleList(resnet18.children())[:-1]
        self.features = nn.Sequential(*self.features)

        self.fc = nn.Linear(512 * 1, num_classes)
        torch.nn.init.xavier_normal_(self.fc.weight, gain=1)

    def forward(self, input_imgs):
        x = self.features(input_imgs)
        x = torch.flatten(x, 1)
        x = self.fc(x)

        return x
