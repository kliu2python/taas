import os

import torch
import torchvision


class ModelBase:
    """
    Model Base, actual model must have inference implemented
    """

    class NotSupportedError(Exception):
        pass

    def __init__(self, model_config, model_constructor=None):
        """
        model init
        :param model_config:
        :param model_constructor: torch vision model or other method
        to return a model
        """
        self.config_dict = model_config
        self.model_class = model_constructor
        self.model = None
        self.construct_model(
            **self.config_dict.get("init_parameters")
        )
        self.load_model_weights()

    def construct_model(self, **kwargs):
        if self.model_class is None:
            self.model_class = getattr(
                torchvision.models, self.config_dict.get("model")
            )
            if self.model_class is None:
                raise ValueError("Please specify 'model' parameter "
                                 "in model config")
        self.model = self.model_class(**kwargs)

    def load_model_weights(self):
        weights_file = self.config_dict.get("weights_file")
        cuda_device = self.config_dict.get("cuda_device")
        if os.path.exists(weights_file):
            print(f"Loading model weights from {weights_file}")
            state = torch.load(
                weights_file,  map_location=torch.device(cuda_device)
            )
            self.model.load_state_dict(state.get("model_state_dict"))
            self.model.eval()
        else:
            raise IOError(f"Weights file {weights_file} not found")

    def inference(self, data_in, **kwargs):
        raise NotImplementedError

    def save_outputs(self, predictions, raw_data):
        raise NotImplementedError

    def train(self, *args, **kwargs):
        raise self.NotSupportedError(
            "This is not supported, we are not plan to train model with CPU, "
            "we are using google colab to trian models with powerful GPU"
        )
