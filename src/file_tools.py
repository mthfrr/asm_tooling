import logging
import os
import subprocess
import re
from src.student import Student


def get_file_list(stu: Student):
    if not stu.has_dir:
        stu.file_list = []
        return stu
    os.chdir(stu.project_dir)
    res = subprocess.run(f"git ls-files", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if res.returncode != 0:
        raise Exception(f"ls-file error for {stu.login}")
    output = res.stdout.decode("utf-8").strip()
    if output != "":
        stu.file_list = output.split("\n")
    return stu

def get_tree(stu: Student):
    if not stu.has_dir:
        stu.tree = "no_dir"
        return stu
    os.chdir(stu.project_dir)
    res = subprocess.run(f"tree -a -I .git", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if res.returncode != 0:
        raise Exception(f"tree error for {stu.login}\n{res.stdout.decode('utf-8').strip()}")
    stu.tree = res.stdout.decode("utf-8").strip()
    return stu

def check_archi(stu: Student):
    if not stu.has_dir or stu.is_empty:
        return stu
    os.chdir(stu.project_dir)
    missing_files = set(stu.archi_file_list).difference(stu.file_list)
    trash_files = set(stu.file_list).difference(stu.archi_file_list)

    # whitelist
    trash_files.difference_update(stu.global_allowed_files)
    
    trash_files = filter(lambda x: "readme" not in x.lower(), trash_files)

    trash_files = list(trash_files)
    missing_files = list(missing_files)
    trash_files.sort()
    missing_files.sort()

    if len(trash_files) != 0:
        stu.trash_files = trash_files
    if len(missing_files) != 0:
        stu.missing_files = missing_files
    return stu

def count_empty_or_missing(stu: Student):
    if not stu.has_dir or stu.is_empty:
        stu.empty_or_missing_files = stu.archi_file_list
        return stu
    os.chdir(stu.project_dir)
    
    stu.empty_or_missing_files = [] if stu.missing_files is None else list(stu.missing_files) # adding missing
    for filename in set(stu.file_list).intersection(stu.archi_file_list):
        try:
            with open(filename, "r") as f:
                if f.read() == "": # adding empty
                    stu.empty_or_missing_files.append(filename)
        except UnicodeDecodeError:
            pass
        except Exception as e:
            logging.error(f"checking content of {filename} failed\n{e}")
    return stu

def load_files_to_exos(stu: Student):
    existing_valid_files = set(stu.file_list).intersection(stu.archi_file_list)
    for i in range(len(stu.exos)):
        files = stu.exos[i]["files"]
        loaded_files = []
        for regex in files:
            for filename in filter(lambda x: re.match(regex, x) is not None, existing_valid_files):
                os.chdir(stu.project_dir)
                logging.debug(f"loading file: {filename}")
                with open(filename, "r") as f:
                    loaded_files.append(f"// {filename} //\n{f.read()}")
        stu.exos[i]["files"] = loaded_files
    return stu