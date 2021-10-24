from src.student import Student
import os
from pathlib import Path
import json
import logging

def set_color(trace):
    if (trace["data"] == ''):
        trace["color"] = "green"
        for t in trace["childs"]:
            r = set_color(t)
            if (r == "red" or r == "orange"):
                trace["color"] = "orange"
    else:
        trace["color"] = "red";
    return trace["color"]

def moulinette(stu: Student):
    if not stu.has_dir:
        stu.trace = "no_dir"
        return stu
    os.chdir(stu.root_folder)
    tp_num = Path(stu.root_folder).stem[2:]
    stu_dir = str(Path(stu.project_dir).name)
    glob_path = f"../../moulinettes/*{tp_num}*/results/{stu_dir}/*.json"
    json_path = list(Path('.')\
        .glob(glob_path))
    if (len(json_path) != 1):
        stu.trace = "trace not found"
        logging.warn(f"json path problem: {json_path}")
        return stu
    json_path = str(json_path[0])
    logging.debug(f"trace found: {json_path}")
    with open(json_path, "r") as f:
        stu.trace = json.loads(f.read())
        set_color(stu.trace)
    return stu