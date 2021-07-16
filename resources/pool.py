class ResourcePoolMixin:
    def prepare(self, **data):
        raise NotImplementedError("prepare function must be implementated")

    def clean(self, pool_id):
        raise NotImplementedError("clean function must be implementated")

    def recycle(self, **data):
        raise NotImplementedError("recycle should have be implemented")
