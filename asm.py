from pathlib import Path
from multiprocessing import Pool
import subprocess
import os
import time
import logging
import yaml
import json
import itertools
from student import Student
import git_tools
from file_tools import get_file_list

class Encode(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Path):
            return str(Path)
        return json.JSONEncoder.default(self, obj)

def print_dic(d):
    print(json.dumps(d, indent=4, cls=Encode))

class auto_asm:
    def __init__(self, config, tp_num):
        self.tp_num = tp_num
        self.root_folder = Path(config["path"].format(nb=tp_num)).absolute()
        self.tp_subfolders = []
        Path(self.root_folder).mkdir(parents=True, exist_ok=True)
        self.config = config
        self.archi = self.root_folder.stem
        self.archi_file_list = list_files_in_archi(config["tps"][self.archi]["archi"])
        self.students : dict(str, Student) = {}
        for stu in self.config["students"]:
            tmp = {
                "login": stu,
                "gitpath": str(self.config["gitpath"].format(**self.config, nb=self.tp_num, student=stu)),
                "project_dir": str((self.root_folder / self.config["project_dir"].format(nb=self.tp_num, student=stu)).absolute()),
                "archi_file_list": self.archi_file_list
            }
            self.students[stu] = Student(**tmp,
                                         root_folder=self.root_folder,
                                         global_allowed_files=config.get("global_allowed_files", []))
        self.foreach_student(get_file_list)
        self.global_report_filter = ["repo_empty", "AUTHORS", "trash_files", "missing_files"]
        self.report_filter = ["repo_empty", "AUTHORS", "trash_files", "missing_files", "commits"]
    
    def get_or_update_repos(self):
        with Pool(processes=6) as pool:
            res = pool.map(git_tools.clone_process, filter(lambda x: not x.has_dir, self.students.values()))
            
        with Pool(processes=6) as pool:
            pool.map(git_tools.pull_process, filter(lambda x: x.has_dir, self.students.values()))

        for student in res:
            self.students[student.login] = student

        if len(res) != 0:
            time.sleep(5) # HUMM
        self.foreach_student(get_file_list)

    def foreach_student(self, f):
        with Pool() as pool:
            res = pool.map(f, self.students.values())
        for student in res:
            self.students[student.login] = student

    def generate_report(self):
        os.chdir(self.root_folder)
        output = {}
        output["_no_clone"] = []
        for stu in self.students.values():
            # save in each dir
            output[stu.login] = {}
            for k in self.report_filter:
                if k in stu.__dict__ and stu.__dict__[k] != None:
                    output[stu.login][k] = stu.__dict__[k]
            if output[stu.login] != {} and stu.has_dir:
                with open(f"{stu.project_dir}/report.yaml", "w") as f:
                    f.write(yaml.safe_dump(output[stu.login], indent=4))
            
            # only in global report
            output[stu.login] = {}
            for k in self.global_report_filter:
                if k in stu.__dict__ and stu.__dict__[k] != None:
                    output[stu.login][k] = stu.__dict__[k]
            if not stu.has_cloned:
                output["_no_clone"].append(stu.login)
            if output[stu.login] == {}:
                del output[stu.login]
                
        # output["_all_good"] = []
        # for stu in self.students.keys():
        #     if stu not in output:
        #         print(stu)
        #         output["_all_good"].append(stu)
        # print(output["_all_good"])
        self.add_stats(output)
        
        # save commit messages in one file
        sorted_student = list(self.students.values())
        sorted_student.sort(key=lambda x: x.login)
        with open(f"commits.txt", "w") as f:
            f.write("\n----\n".join("\n".join(s.commits) for s in sorted_student))
            f.write("\n")

        text_output = yaml.safe_dump(output, indent=4)
        logging.info(f'### Stat ###\n{yaml.safe_dump(output["__stat"], indent=4)}')
        with open(f"report.yaml", "w") as f:
            f.write(text_output)
        return output
    
    def pb_stat_builder(self, name, res, total_students, flt):
        logins = set(map(lambda x: x.login, filter(flt, self.students.values())))
        val = len(logins)
        res[name] = (val, f"{val/total_students*100:.2f}%")
        return logins
    
    def add_stats(self, output):
        res = {}
        total_students = len(self.config["students"])
        
        pb_stu = set()
        
        pb_stu = pb_stu.union(self.pb_stat_builder("student_w_no_clone", res, total_students, lambda x: not x.has_dir))
        pb_stu = pb_stu.union(self.pb_stat_builder("student_w_no_push", res, total_students, lambda x: x.is_empty))
        pb_stu = pb_stu.union(self.pb_stat_builder("student_w_trash_files", res, total_students, lambda x: x.trash_files))
        pb_stu = pb_stu.union(self.pb_stat_builder("student_w_missing_files", res, total_students, lambda x: x.missing_files))
        pb_stu = pb_stu.union(self.pb_stat_builder("student_w_AUTHORS_error", res, total_students, lambda x: x.AUTHORS))
        
        val = total_students - len(pb_stu)
        res["all_good"] = (val, f"{val/total_students*100:.2f}%")
        
        val = sum(map(lambda x: len(self.archi_file_list) if (not x.has_dir) else (len(x.missing_files) if x.missing_files is not None else 0), self.students.values()))
        res["missing_files_per_student"] = round(val/total_students, 2)
        
        val = sum(map(lambda x: len(x.trash_files), filter(lambda x: x.trash_files, self.students.values())))
        res["trash_files_per_student"] = round(val/total_students, 2)
        
        val = sum(map(lambda x: len(x.empty_or_missing_files), self.students.values())) / total_students
        res["empty_or_missing_file_per_student"] = (f"{round(val,2)}/{len(self.archi_file_list)}", f"{val/len(self.archi_file_list)*100:.2f}%")
        
        output["__stat"] = res
        output["_all_good"] = sorted(list(set(self.students.keys()).difference(pb_stu)))

def list_files_in_archi(archi, start_path='', res=None):
    if res == None:
        res = []
    extract = lambda x: list(x.items())[0]
    for el in archi:
        if isinstance(el, dict):
            d, cont = extract(el)
            list_files_in_archi(cont, f"{start_path}/{d}", res)
            # res.append(f"{start_path}/{d}")
        else:
            res.append(f"{start_path}/{el}")
    return list(map(lambda x: x[1:], res))