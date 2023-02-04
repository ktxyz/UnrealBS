import json
import uuid
from enum import IntEnum


class OrderStatus(IntEnum):
    WAITING = 0,
    IN_PROGRESS = 1,
    FAILED = 2,
    COOKED = 3


class Order:
    """Order for a recipe to be cooked"""

    def __init__(self, recipe, order_data):
        if 'id' in order_data.keys():
            self.id = order_data['id']
        else:
            self.id = f'{recipe.target}-{str(uuid.uuid4().hex)[:5]}'
        self.status = OrderStatus.WAITING
        self.current_step = -1

        self.recipe = recipe
        self.client = order_data['client']

    def as_json(self, to_str=False):
        object_json = {
            "recipe": self.recipe.as_json(),
            "order": {
                "client": self.client,
                "id": self.id
            }
        }
        if to_str:
            return json.dumps(object_json, indent=4)
        return object_json
