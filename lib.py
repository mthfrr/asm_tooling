from pathlib import Path
from multiprocessing import Pool
import subprocess
import os
import time
import logging
import glob
import yaml
import json
import itertools

class Encode(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Path):
            return str(Path)
        return json.JSONEncoder.default(self, obj)

def print_dic(d):
    print(json.dumps(d, indent=4, cls=Encode))

class auto_git:
    def __init__(self, config, tp_num):
        self.tp_num = tp_num
        self.tp_folder = Path(config["path"].format(nb=tp_num)).absolute()
        self.tp_subfolders = []
        Path(self.tp_folder).mkdir(parents=True, exist_ok=True)
        self.config = config
        self.archi = self.tp_folder.stem
        self.archi_file_list = list_files_in_archi(config["tps"][self.archi]["archi"])
        self.students = {}
        for stu in self.config["students"]:
            self.students[stu] = {
                "login": stu,
                "gitpath": str(self.config["gitpath"].format(**self.config, nb=self.tp_num, student=stu)),
                "project_dir": str((self.tp_folder / self.config["project_dir"].format(nb=self.tp_num, student=stu)).absolute()),
                "archi_file_list": self.archi_file_list
            }
            if not self.students.get("clone_success", False):
                self.students[stu]["clone_success"] = os.path.isdir(self.students[stu]["project_dir"])
        self.foreach_student(self.get_file_list)
        self.report_filter = ["repo_empty", "AUTHORS", "trash_files", "missing_files"]
    
    def get_or_update_repos(self):
        with Pool(processes=6) as pool:
            res = pool.map(self.clone_process, filter(lambda x: not self.students[x]["clone_success"], self.config["students"]))
            
        with Pool(processes=6) as pool:
            pool.map(self.pull_process, filter(lambda x: self.students[x]["clone_success"], self.config["students"]))

        for student in res:
            self.students[student["login"]] = student

        if len(res) != 0:
            time.sleep(5) # HUMM
        self.foreach_student(self.get_file_list)

    def clone_process(self, name):
        os.chdir(self.tp_folder)
        student = self.students[name]
        git_path = student["gitpath"]
        res = subprocess.run(f"git clone {git_path}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if res.returncode != 0 and b"already exists and is not an empty directory" not in res.stdout:
            student["clone_success"] = False
        else:
            student["clone_success"] = True
        student["clone_msg"] = res.stdout.decode("utf-8")
        student["clone_code"] = res.returncode
        print(f"cloned {student['login']}")
        return student

    def pull_process(self, name):
        student = self.students[name]
        os.chdir(student["project_dir"])
        res = subprocess.run(f"git pull", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if res.returncode != 0:
            student["pull_success"] = False
        else:
            student["pull_success"] = True
        student["pull_msg"] = res.stdout.decode("utf-8")
        student["pull_code"] = res.returncode
        print(f"pulled {student['login']}")
        return student

    def foreach_student(self, f):
        with Pool(processes=6) as pool:
            res = pool.map(f, filter(lambda x: self.students[x]["clone_success"], self.config["students"]))
        for student in res:
            self.students[student["login"]] = student

    def get_file_list(self, login):
        self.students[login]["file_list"] = list(
            os.path.relpath(p, self.students[login]["project_dir"])
            for p in itertools.chain(glob.glob(str(self.students[login]["project_dir"] + '/**/*'), recursive=True),
                                     glob.glob(str(self.students[login]["project_dir"] + '/**/.*'), recursive=True))
        )
        return self.students[login]

    def check_AUTHORS(self, login):
        stu = self.students[login]
        if stu.get("repo_empty", False):
            return stu
        os.chdir(stu["project_dir"])
        authors_path = next(filter(lambda x: "AUTHORS" in x, stu["archi_file_list"]))
        if not os.path.isfile(authors_path):
            stu["AUTHORS"] = "no authors"
            return stu
        
        with open(authors_path, "r") as f:
            lines = f.readlines()
            content = "".join(lines)
            if len(lines) == 0:
                stu["AUTHORS"] = "empty"
                return stu
            if content[-1] != '\n':
                stu["AUTHORS"] = "last char not \\n"
                return stu
            if len(content)>2 and content[-2:] == '\n\n':
                stu["AUTHORS"] = "ends with \\n\\n"
                return stu
            if len(lines) > 4:
                stu["AUTHORS"] = "more than 4 lines"
                return stu
            if len(lines) < 4:
                stu["AUTHORS"] = "less than 4 lines"
                return stu
            elif lines[2] != f"{stu['login']}\n" or lines[3] != f"{stu['login']}@epita.fr\n":
                stu["AUTHORS"] = "login or email error"
                return stu
        return stu

    def check_archi(self, login):
        stu = self.students[login]
        if stu.get("repo_empty", False):
            return stu
        os.chdir(stu["project_dir"])
        missing_files = set(stu["archi_file_list"]).difference(stu["file_list"])
        trash_files = set(stu["file_list"]).difference(stu["archi_file_list"])

        # whitelist
        trash_files.difference_update(self.config["global_allowed_files"])
        
        trash_files = filter(lambda x: "README" not in x.upper(), trash_files)

        trash_files = list(trash_files)
        missing_files = list(missing_files)
        trash_files.sort()
        missing_files.sort()

        if len(trash_files) != 0:
            stu["trash_files"] = trash_files
        if len(missing_files) != 0:
            stu["missing_files"] = missing_files
        return stu
    
    def is_empty_repo(self, login):
        stu = self.students[login]
        os.chdir(stu["project_dir"])

        files = set(stu["file_list"]).difference([".git", "report.yaml"])

        if len(files) == 0:
            stu["repo_empty"] = True
        return stu

    def generate_report(self):
        os.chdir(self.tp_folder)
        output = {}
        output["_no_clone"] = []
        for stu in self.students.values():
            output[stu["login"]] = {}
            for k in self.report_filter:
                if k in stu:
                    output[stu["login"]][k] = stu[k]

            # save in each dir
            if output[stu["login"]] != {}:
                with open(f"{stu['project_dir']}/report.yaml", "w") as f:
                    f.write(yaml.safe_dump(output[stu["login"]], indent=4))
            # only in global report
            if not stu["clone_success"]:
                output["_no_clone"].append(stu["login"])
            if output[stu["login"]] == {}:
                del output[stu["login"]]
                
        output["_all_good"] = []
        for stu in self.students.keys():
            if stu not in output:
                output["_all_good"].append(stu)
        self.add_stats(output)
        text_output = yaml.safe_dump(output, indent=4)
        print(yaml.safe_dump(output["__stat"], indent=4))
        with open(f"report.yaml", "w") as f:
            f.write(text_output)
        return output
    
    def pb_stat_builder(self, name, res, total_students, flt):
        login = set(map(lambda x: x["login"], filter(flt, self.students.values())))
        val = len(login)
        res[name] = (val, f"{val/total_students*100:.2f}%")
        return login
    
    def add_stats(self, output):
        res = {}
        total_students = len(self.config["students"])
        total_pb = 0
        
        pb_stu = set()
        
        pb_stu = pb_stu.union(self.pb_stat_builder("no_clone", res, total_students, lambda x: not x.get("clone_success", True)))
        pb_stu = pb_stu.union(self.pb_stat_builder("no_push", res, total_students, lambda x: x.get("repo_empty", False)))
        pb_stu = pb_stu.union(self.pb_stat_builder("trash_files", res, total_students, lambda x: "trash_files" in x))
        pb_stu = pb_stu.union(self.pb_stat_builder("missing_files", res, total_students, lambda x: "missing_files" in x))
        pb_stu = pb_stu.union(self.pb_stat_builder("AUTHORS_error", res, total_students, lambda x: "AUTHORS" in x))
        
        val = total_students - len(pb_stu)
        res["all_good"] = (val, f"{val/total_students*100:.2f}%")
        
        val = sum(map(lambda x: len(x["missing_files"]), filter(lambda x: "missing_files" in x, self.students.values())))
        res["missing_files_per_student"] = round(val/total_students, 2)
        
        val = sum(map(lambda x: len(x["trash_files"]), filter(lambda x: "trash_files" in x, self.students.values())))
        res["trash_files_per_student"] = round(val/total_students, 2)
        
        output["__stat"] = res
        output["_all_good"] = list(set(map(lambda x: x["login"], self.students.values())).difference(pb_stu))

def list_files_in_archi(archi, start_path='', res=None):
    if res == None:
        res = []
    extract = lambda x: list(x.items())[0]
    for el in archi:
        if isinstance(el, dict):
            d, cont = extract(el)
            list_files_in_archi(cont, f"{start_path}/{d}", res)
            res.append(f"{start_path}/{d}")
        else:
            res.append(f"{start_path}/{el}")
    return list(map(lambda x: x[1:], res))