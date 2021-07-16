# pylint: disable=no-name-in-module
import os
import uuid

import numpy as np
import torch
from PIL import Image

import model.classes as model_classes
from model.base import ModelBase
from model.data import get_data_loader, DataType
from utils.threads import thread


class ImageClassifier(ModelBase):
    def __init__(self, model_config):
        super().__init__(model_config, model_classes.Resnet18)

    def inference(self, data_in):
        data_loader = get_data_loader(DataType.IMAGE, data_in)
        predicts = []
        raw_data = []
        for data in data_loader:
            with torch.no_grad():
                o = self.model(data)
                o = getattr(o, "logits", o)
                o = torch.nn.functional.softmax(o, dim=1)
                pred = o.argmax(dim=1)
                pred = pred.numpy()
            predicts.extend(pred.tolist())
            raw_data.append(data)
        class_mapping = self.config_dict.get("class_mapping")
        predicts = [class_mapping[idx] for idx in predicts]
        self.save_outputs(predicts, raw_data)
        return predicts

    @thread
    def save_outputs(self, predictions, raw_data):
        save_path = self.config_dict.get("result_save_path")
        if save_path is not None:
            for pred, raw in zip(predictions, raw_data):
                save_path_pred = os.path.join(
                    save_path, pred
                )
                os.makedirs(save_path_pred, exist_ok=True)
                save_path_pred = os.path.join(
                    save_path_pred, f"{pred}_{uuid.uuid4()}.png"
                )
                Image.fromarray(
                    (
                        raw.squeeze().permute(1, 2, 0).numpy() * 255
                    ).astype(np.uint8)
                ).save(save_path_pred)
