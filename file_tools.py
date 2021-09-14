import os
import subprocess
from student import Student


def get_file_list(stu: Student):
    os.chdir(stu.project_dir)
    res = subprocess.run(f"git ls-files", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if res.returncode != 0:
        raise Exception(f"ls-file error for {stu.login}")
    output = res.stdout.decode("utf-8").strip()
    if output != "":
        stu.file_list = output.split("\n")
    return stu

def check_archi(stu: Student):
    if stu.is_empty:
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