import json


class Step:
    """Represents single cmd execution, runnable
    by Workers
    """
    def __init__(self, json_data):
        self.cmd = json_data['cmd']
        self.name = json_data['name']
        if 'timeout' in json_data:
            self.timeout = json_data['timeout']
        else:
            self.timeout = 0

    def as_json(self, to_str=False):
        object_json = {
            'cmd': self.cmd,
            'timeout': self.timeout,
            'name': self.name
        }
        if to_str:
            return json.dumps(object_json, indent=4)
        return object_json
