# asm_tooling
tooling to clone and analyse SPE repositories

## How to use
Create a file containing your students logins:
```
login1
login2
```

Execute `run.py`

## Moulinette integration
```sh
mkdir moulinette
cd moulinette
git clone git@...
cp ../run.sh .
ln -s ../tps/tpXX students
./run.sh
```