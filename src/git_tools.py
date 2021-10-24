import subprocess
import os
import logging
from src.student import Student

def clone_process(stu: Student):
    os.chdir(stu.root_folder)
    res = subprocess.run(f"git clone {stu.gitpath}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if res.returncode != 0:
        logging.debug(f"clone {stu.gitpath} failed,\n{res.stdout.decode('utf-8')}")
        stu.has_dir = False
        stu.has_cloned = False
        logging.info(f"clone {stu.login} failed")
    else:
        stu.has_dir = True
        stu.has_cloned = True
        logging.info(f"clone {stu.login} success")
    return stu

def pull_process(stu: Student):
    os.chdir(stu.project_dir)
    res = subprocess.run(f"git pull", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if res.returncode != 0:
        logging.error(f"pull {stu.login} failed,\n{res.stdout.decode('utf-8')}")
    else:
        logging.info(f"pull {stu.login} success")
        res = subprocess.run(f"git reset --hard", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if res.returncode != 0:
            logging.error(f"reset {stu.login} failed,\n{res.stdout.decode('utf-8')}")
        else:
            logging.info(f"reset {stu.login} success")
    return stu

def is_empty_repo(stu: Student):
    if not stu.has_dir:
        return stu
    os.chdir(stu.project_dir)
    files = set(stu.file_list).difference(["report.yaml"])

    if len(files) == 0:
        stu.is_empty = True
    return stu

def get_commits(stu: Student):
    if not stu.has_dir:
        return stu
    os.chdir(stu.project_dir)
    res = subprocess.run(f"git log --pretty=format:\"%ad %s\" --date=format:\"%d/%m/%Y %R\"", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if res.returncode != 0:
        logging.error(f"git log {stu.login} failed,\n{res.stdout.decode('utf-8')}")
    else:
        stu.commits = res.stdout.decode('utf-8').split("\n")
    
    return stu

def git_clean(stu: Student):
    if not stu.has_dir:
        return stu
    os.chdir(stu.project_dir)
    res = subprocess.run(f"git clean -f", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if res.returncode != 0:
        logging.error(f"git clean {stu.login} failed,\n{res.stdout.decode('utf-8')}")
    return stu