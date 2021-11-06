from string import Template
from pathlib import Path
from src.student import Student
from src.tools import *
from src.file_tools import load_files_to_exos

def template_html(students: Student, config):
    with open(config["template_file"], "r") as f:
        template = Template(f.read())

    for login, stu in students.items():
        stu = load_files_to_exos(stu)
        res = template.safe_substitute(
            stu=json_dumps(stu.__dict__),
            login=login,
            logins=list(students.keys()),
            char80="0"*80,
            exo_index=0
        )
        yield login, res
    return