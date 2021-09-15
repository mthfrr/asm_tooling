import os
from student import Student

def check_AUTHORS(stu: Student):
    if not stu.has_dir or stu.is_empty:
        return stu
    os.chdir(stu.project_dir)
    authors_path = next(filter(lambda x: "AUTHORS" in x, stu.archi_file_list))
    if not os.path.isfile(authors_path):
        stu.AUTHORS = "no authors"
        return stu
    
    with open(authors_path, "r") as f:
        lines = f.readlines()
        content = "".join(lines)
        if len(lines) == 0:
            stu.AUTHORS = "empty"
            return stu
        if content[-1] != '\n':
            stu.AUTHORS = "last char not \\n"
            return stu
        if len(content)>2 and content[-2:] == '\n\n':
            stu.AUTHORS = "ends with \\n\\n"
            return stu
        if len(lines) > 4:
            stu.AUTHORS = "more than 4 lines"
            return stu
        if len(lines) < 4:
            stu.AUTHORS = "less than 4 lines"
            return stu
        elif lines[2] != f"{stu.login}\n" or lines[3] != f"{stu.login}@epita.fr\n":
            stu.AUTHORS = "login or email error"
            return stu
    return stu