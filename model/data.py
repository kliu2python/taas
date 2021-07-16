"""
Data for inferencing
"""

import base64
import enum
import os
from io import BytesIO

from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms


class ImageData(Dataset):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.transform = transforms.Compose([transforms.ToTensor()])

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        data = self.data[index]
        if not os.path.isabs(data):
            data = BytesIO(base64.b64decode(data))
        img = Image.open(data)
        img = img.convert("RGB")
        img = self.transform(img)
        return img


class DataType(enum.Enum):
    IMAGE = ImageData


def get_data_loader(data_type, input_data):
    data_class = data_type.value
    data = data_class(input_data)
    return DataLoader(dataset=data)
