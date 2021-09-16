#!/usr/bin/python3
import argparse
import os
from posixpath import join
import yaml
from asm import *
import logging
from authors import check_AUTHORS
from git_tools import is_empty_repo, get_commits
from file_tools import check_archi, count_empty_or_missing

# go to the scripts folder
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

parser = argparse.ArgumentParser(description='Clone git')
parser.add_argument('-nb', type=int, required=True, help='tp number')
parser.add_argument('-c', '--config', type=Path, required=True, help='.yaml config file')
parser.add_argument('-s', '--students', type=Path, required=True, help='.yaml students list')
parser.add_argument('-d', '--disable-update', action='store_true', default=False, required=False, help='disable the cloning/pulling')
parser.add_argument('-log', type=str, default="WARN", required=False, help='set logging level')
args = parser.parse_args()

numeric_level = getattr(logging, args.log.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError(f'Invalid log level: {args.log}')
logging.basicConfig(level=numeric_level)

with open(args.config, "r") as f:
    config = yaml.safe_load(f)
with open(args.students, "r") as f:
    config["students"] = f.read().strip().split()

ag = auto_asm(config, args.nb)
if not args.disable_update:
    ag.get_or_update_repos()
ag.foreach_student(is_empty_repo)
ag.foreach_student(check_AUTHORS)
ag.foreach_student(check_archi)
ag.foreach_student(count_empty_or_missing)
ag.foreach_student(get_commits)
ag.generate_report()