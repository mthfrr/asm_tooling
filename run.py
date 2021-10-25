#!/usr/bin/env python3
import argparse
import os
import json
import logging
from pathlib import Path
from src.asm import *
from src.authors import check_AUTHORS
from src.git_tools import is_empty_repo, get_commits
from src.file_tools import check_archi, count_empty_or_missing, get_tree
from src.moulinette import moulinette, mouli_init


# go to the scripts folder
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

parser = argparse.ArgumentParser(description='Clone git')
parser.add_argument('-nb', type=int, required=True, help='tp number')
parser.add_argument('-c', '--config', type=Path, required=True, help='.json config file')
parser.add_argument('-s', '--students', type=Path, required=True, help='students login list')
parser.add_argument('-u', '--update', action='store_true', default=False, required=False, help='enable cloning/pulling')
parser.add_argument('-m', '--moulinette', action='store_true', default=False, required=False, help='get traces from moulinette')
parser.add_argument('-log', type=str, default="INFO", required=False, help='set logging level')
args = parser.parse_args()

numeric_level = getattr(logging, args.log.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError(f'Invalid log level: {args.log}')
logging.basicConfig(level=numeric_level)

with open(args.config, "r") as f:
    config = json.loads(f.read())

with open(args.students, "r") as f:
    config["students"] = f.read().strip().split()

ag = auto_asm(config, args.nb)
if args.update:
    ag.get_or_update_repos()
ag.foreach_student(is_empty_repo)
ag.foreach_student(git_clean)
ag.foreach_student(check_AUTHORS)
ag.foreach_student(check_archi)
ag.foreach_student(count_empty_or_missing)
ag.foreach_student(get_commits)
ag.foreach_student(get_tree)
if args.moulinette:
    mouli_init(ag)
    ag.foreach_student(moulinette)
ag.generate_html()
