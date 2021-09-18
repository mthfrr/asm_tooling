from pathlib import Path
import json

class Encode(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Path):
            return str(obj)
        return json.JSONEncoder.default(self, obj)

def json_dumps(d, indent=4):
    return json.dumps(d, indent=indent, cls=Encode)

def print_dic(d, indent=4):
    print(json.dumps(d, indent=indent, cls=Encode))