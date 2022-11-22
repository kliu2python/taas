from abc import ABC, abstractmethod


class Updater(ABC):
    @abstractmethod
    def update(self, req_id, data):
        """
        this is a abstruct class for update
        upload image / ips / av /engine etc to device
        """
        raise NotImplementedError
