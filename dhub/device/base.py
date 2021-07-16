class Device:
    def get_device(self):
        raise NotImplementedError

    def prepare_device(self, **kwargs):
        raise NotImplementedError

    def option_device(self, op_method, **kwargs):
        op_method = getattr(self, f"op_{op_method}")
        if op_method is None:
            return "Error: op_method does not exists"
        return op_method(**kwargs)

    def clean_device(self):
        raise NotImplementedError
