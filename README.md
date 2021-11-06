# asm_tooling
tooling to clone and analyse SPE repositories

## How to use
### Setup
Create a file containing your students logins:
```
login1
login2
```

### Run
Execute `run.py`
```sh
$ ./run.py
usage: run.py [-h] -nb NB -c CONFIG -s STUDENTS [-u] [-m] [-log LOG]
```
### Arguments
NB: number of the tp
CONFIG: config.json
STUDENTS: file containing student logins
-u : clone or pull repos
-m : clone / run moulinette and generate outputs

### Use results
Open in any browser the html file in `output/`

Left column:
- you can use `<` and `>` to navigate between students and execices.
- commit messages.
- info about AUTHORS, trashfiles and missing files
- tree of the repo

Middle:
- source code of the current execise

Right:
- Moulinette results (click to open)