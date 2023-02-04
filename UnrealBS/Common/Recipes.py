import json

from UnrealBS.Common.Steps import Step


class Recipe:
    """Step-by-step blueprint for cooks"""
    def __init__(self, recipe_data):
        self.target = recipe_data['target']

        self.steps = [Step(x) for x in recipe_data['steps']]

        self.start_step = Step(recipe_data['start-step'])
        self.failure_step = Step(recipe_data['failure-step'])
        self.success_step = Step(recipe_data['success-step'])

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
