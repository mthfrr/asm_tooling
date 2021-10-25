# asm_tooling
tooling to clone and analyse SPE repositories

## How to use
Create a file containing your students logins:
```
login1
login2
```

Execute `run.py`

## Moulinette integration (requiered)
```sh
mkdir moulinette
cd moulinette
git clone git@...
cd pw_moui_folder
cp ../run.sh .
ln -s ../tps/tpXX students
./run.sh
```

## TODO

- [] rm result before running moulinette