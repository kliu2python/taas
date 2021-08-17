from cassandra.cqlengine import columns
from cassandra.cqlengine.usertype import UserType


class Command(UserType):
    type = columns.Text()
    category = columns.Text()
    commands = columns.List(columns.Text)

    def serialize(self):
        return {
            "type": self.type,
            "category": self.category,
            "commands": self.commands
        }
