from src.student import Student
from src.asm import auto_asm
import os
from pathlib import Path
from shutil import copyfile
import json
import logging
import subprocess
import re

def ln_s(src, dest):
    os.system(f"rm -rf {dest}")
    os.symlink(Path(src).resolve(), dest)

def folder_name_from_git(link):
    return re.sub(r"^.*\/(.*)\.git$", r"\1", link)

def clone_mouli(link):
    if Path(folder_name_from_git(link)).exists():
        return
    res = subprocess.run(f"git clone {link}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if res.returncode != 0:
        logging.error(f"mouli clone error:\n{res.stdout.decode('utf-8')}")
        raise Exception()

def docker_build():
    if Path("Dockerfile").exists():
        return
    logging.info("docker build")
    ln_s("docker/Dockerfile", "Dockerfile")
    res = subprocess.run(f"sudo docker build -t moulinette .", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if res.returncode != 0:
        logging.error(f"docker build error:\n{res.stdout.decode('utf-8')}")
        raise Exception()

def clone_mouli_and_conf(link, root_path):
    os.chdir(root_path)
    if not Path("moulinettes").exists():
        os.mkdir("moulinettes")
    os.chdir("moulinettes")
    clone_mouli(link)
    os.chdir(folder_name_from_git(link))
    docker_build()
    os.chdir(root_path)
    return

def mouli_init(aa: auto_asm):
    logging.info("mouli init")
    link = aa.config["tps"][aa.archi].get("mouli", None)
    if link == None:
        logging.error("Moulinette git link not configured")
        return 0

    clone_mouli_and_conf(link, aa.root)
    os.chdir(Path("moulinettes") / folder_name_from_git(link))
    ln_s(f"../../tps/{aa.archi}", "students")
    os.chdir(aa.root)
    return 1

def set_color(trace):
    val = 0
    if (trace["data"] == ''):
        for t in trace["childs"]:
            val += set_color(t)
        if len(trace["childs"]):
            val /= len(trace["childs"])
        if val == 0:
            trace["color"] = "green"
        elif val == 1:
            trace["color"] = "red"
        else:
            trace["color"] = "orange"
    else:
        val = 1
        trace["color"] = "red";
    return val

def run_mouli(stu: Student, tp_num):
    logging.info(f"mouli run {stu.login}")
    glob_path = f"../../moulinettes/*{tp_num}*"
    mouli_path = list(Path('.')\
        .glob(glob_path))
    os.chdir(mouli_path[0])
    # start
    logging.info(f"mouli rm old stuff {stu.login}")
    res = subprocess.run(f"sudo rm -rf {mouli_path[0]}/results/{str(Path(stu.project_dir).name)}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if res.returncode != 0:
        logging.error(f"rm -rf error {stu.login}:\n{res.stdout.decode('utf-8')}")
        raise Exception("rm prev results")
    
    logging.info(f"mouli start.sh {stu.login}")
    res = subprocess.run(f"sudo ./start.sh students/{str(Path(stu.project_dir).name)}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if res.returncode != 0:
        logging.error(f"start error {stu.login}:\n{res.stdout.decode('utf-8')}")
        raise Exception("start")
    
    logging.info(f"mouli chown {stu.login}")
    res = subprocess.run(f"sudo chown \"$USER:$USER\" -R results/{str(Path(stu.project_dir).name)}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if res.returncode != 0:
        logging.error(f"chown error {stu.login}:\n{res.stdout.decode('utf-8')}")
        raise Exception("chown")
    os.chdir("results")
    
    logging.info(f"mouli gen trace {stu.login}")
    res = subprocess.run(f"../docker/generate_traces_json.py {str(Path(stu.project_dir).name)}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    # if res.returncode != 0:
    #     logging.error(f"./generate_traces_json.py error {stu.login}:\n{res.stdout.decode('utf-8')}")
    #     raise Exception()

def moulinette(stu: Student):
    if not stu.has_dir:
        stu.trace = "no_dir"
        return stu
    os.chdir(stu.root_folder)
    tp_num = Path(stu.root_folder).stem[2:]
    stu_dir = str(Path(stu.project_dir).name)
    
    run_mouli(stu, tp_num)
    os.chdir(stu.root_folder)
    logging.info(f"mouli run {stu.login} done")
    glob_path = f"../../moulinettes/*{tp_num}*/results/{stu_dir}/*.json"
    json_path = list(Path('.')\
        .glob(glob_path))
    if (len(json_path) != 1):
        stu.trace ={"name": "trace not found", "data": "", "childs": []} 
        logging.warn(f"moulinette trace path problem: {json_path}")
        return stu
    json_path = str(json_path[0])
    logging.debug(f"trace found: {json_path}")
    with open(json_path, "r") as f:
        stu.trace = json.loads(f.read())
        set_color(stu.trace)
    logging.info(f"stored traces for {stu.login}")
    return stu
