import enum
import os

import yaml
from singleton_decorator.decorator import singleton

import model.models as models


class ModelType(enum.Enum):
    """
    Supported model types
    """
    IMAGECLASSIFIER = "ImageClassifier"


@singleton
class ModelManager:
    """
    Manger different models and inference operations.
    """
    def __init__(self):
        self.models = {}
        self.load_models()

    @staticmethod
    def load_config(config_file):
        if os.path.exists(config_file):
            with open(config_file) as F:
                config_dict = yaml.safe_load(F)
            return config_dict

    def load_models(self):
        curr_path = os.path.dirname(__file__)
        config_path = os.path.join(curr_path, "configs")
        config_file_list = os.listdir(config_path)
        for config_file in config_file_list:
            config = self.load_config(os.path.join(config_path, config_file))
            model_type = config.get("model_type")
            model_class = getattr(models, model_type)
            if model_class:
                print(f"Loading model {model_type}")
                model = model_class(config)
                self.models[model_type] = model
            else:
                raise ValueError("model type is missing or not valided")

    def inference(self, model_type, inputs, **kwargs):
        if isinstance(model_type, ModelType):
            return self.models.get(model_type.value).inference(inputs, **kwargs)
        supported_types = [model_type.value for model_type in ModelType]
        raise ValueError(f"We only support those model types:"
                         f"{supported_types}")
