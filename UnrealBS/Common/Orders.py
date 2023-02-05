import datetime
import json
import uuid
from enum import IntEnum, auto


class OrderStatus(IntEnum):
    SCHEDULED = auto()
    WAITING = auto()
    IN_PROGRESS = auto()
    CANCELLED = auto()
    FAILED = auto()
    TIMEOUT = auto()
    COOKED = auto()


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

        self.schedule = None
        if 'schedule' in order_data.keys():
            self.schedule = order_data['schedule']
        self._schedule_time = datetime.datetime.now()

    def as_json(self, to_str=False):
        object_json = {
            "recipe": self.recipe.as_json(),
            "order": {
                "client": self.client,
                "id": self.id,
            },
            "schedule": self.schedule
        }
        if to_str:
            return json.dumps(object_json, indent=4)
        return object_json

    def api_json(self):
        json_dict = {
            'id': self.id,
            'recipe': self.recipe.target,
            'client': self.client,
            'status': self.status.name,
            'current_step': self.current_step
        }

        if self.schedule is not None:
            json_dict['schedule'] = str(self._schedule_time)

        return json_dict

    def set_schedule(self):
        hours, minutes = map(int, self.schedule.split(':'))
        self._schedule_time += datetime.timedelta(hours=hours, minutes=minutes)

    def is_time(self):
        return self._schedule_time < datetime.datetime.now()
