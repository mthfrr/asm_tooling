from src.student import Student
from src.asm import auto_asm
import os
from pathlib import Path
import json
import logging
import subprocess
import re

def folder_name_from_git(link):
    return re.sub(r"^.*/(.*)\\.git$", r"\\1", link)

def clone_mouli_and_conf(link, root_path):
    os.chdir(root_path)
    if not (Path(os.curdir) / "moulinettes").exists():
        os.mkdir("moulinettes")
    os.chdir("moulinettes")
    res = subprocess.run(f"git clone {link}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if res.returncode != 0:
        logging.error(f"mouli clone error:\n{res.stdout.decode('utf-8')}")
        return 1
    return

def mouli_init(aa: auto_asm):
    link = aa.config["tps"][aa.archi].get("mouli", None)
    if link == None:
        logging.error("Moulinette git link not configured")
        raise Exception()
    print(folder_name_from_git(link))
    exit(1)
    clone_mouli_and_conf(link, aa.root)
    
    return 0

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