import datetime
import json

from UnrealBS.Common.Steps import Step


class Recipe:
    """Step-by-step blueprint for cooks"""

    def __init__(self, recipe_data):
        self.target = recipe_data['target']

        self.steps = [Step(x) for x in recipe_data['steps']]

        self._repeat_times = None
        if 'repeat-times' in recipe_data.keys():
            self._repeat_times = recipe_data['repeat-times']
        if self._repeat_times is not None:
            self._repeat_times = [datetime.datetime.now().replace(hour=int(x.split(':')[0]),
                                                                  minute=int(x.split(':')[1]),
                                                                  second=0, microsecond=0)
                                  for x in self._repeat_times]

        self.start_step = Step(recipe_data['start-step'])
        self.failure_step = Step(recipe_data['failure-step'])
        self.success_step = Step(recipe_data['success-step'])

        # for repeat
        self._last_cook_time = datetime.datetime.now()

    def is_time(self):
        time_now = datetime.datetime.now()
        for time in self._repeat_times:
            if time_now > time and self._last_cook_time < time:
                return True
        return False

    def reset_time(self):
        self._last_cook_time = datetime.datetime.now()

    def as_json(self, to_str=False):
        object_json = {
            "target": self.target,

            "start-step": self.start_step.as_json(),
            "failure-step": self.failure_step.as_json(),
            "success-step": self.success_step.as_json(),

            "steps": [x.as_json() for x in self.steps],
        }
        if to_str:
            return json.dumps(object_json, indent=4)
        return object_json
