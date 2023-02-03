import uuid
import json
from enum import Enum, IntEnum


class Step:
    """Represents single cmd execution, runnable
    by Workers
    """
    def __init__(self, json_data):
        self.cmd = json_data['cmd']
        if 'timeout' in json_data:
            self.timeout = json_data['timeout']
        else:
            self.timeout = 0

    def as_json(self):
        return json.dumps({
            'cmd': self.cmd,
            'timeout': self.timeout
        }, indent=4)


class Recipe:
    """Step-by-step blueprint for cooks"""
    def __init__(self, json_data):
        self.target = json_data['target']

        try:
            self.steps = [Step(x) for x in json_data['steps']]

            self.start_step = Step(json_data['start-step'])
            self.failure_step = Step(json_data['failure-step'])
            self.success_step = Step(json_data['success-step'])
        except:
            self.steps = [Step(json.loads(x)) for x in json_data['steps']]

            self.start_step = Step(json.loads(json_data['start-step']))
            self.failure_step = Step(json.loads(json_data['failure-step']))
            self.success_step = Step(json.loads(json_data['success-step']))

    def as_json(self):
        return json.dumps({
            "target": self.target,

            "start-step": self.start_step.as_json(),
            "failure-step": self.failure_step.as_json(),
            "success-step": self.success_step.as_json(),

            "steps": [x.as_json() for x in self.steps],
        }, indent=4)

class OrderStatus(Enum):
    WAITING = 0,
    IN_PROGRESS = 1,
    FAILED = 2,
    COOKED = 3
class Order:
    """Order for a recipe to be cooked"""
    def __init__(self, recipe, json_data):
        self.id = f'{recipe.target}-{str(uuid.uuid4().hex)[:5]}'
        self.status = OrderStatus.WAITING
        self.current_step = -1

        self.recipe = recipe
        self.client = json_data['client']

    def as_json(self):
        return json.dumps({
            "recipe": self.recipe.as_json(),
            "order": {
                "client": self.client
            }
        }, indent=4)
