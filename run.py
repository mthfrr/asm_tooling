#!/usr/bin/python3
import argparse
import os
from posixpath import join
import yaml
from lib import *

# go to the scripts folder
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

parser = argparse.ArgumentParser(description='Clone git')
parser.add_argument('-nb', type=int, required=True, help='tp number')
parser.add_argument('-c', '--config', type=Path, required=True, help='.yaml config file')
parser.add_argument('-s', '--students', type=Path, required=True, help='.yaml students list')
args = parser.parse_args()

with open(args.config, "r") as f:
    config = yaml.safe_load(f)
with open(args.students, "r") as f:
    config.update(yaml.safe_load(f))

ag = auto_git(config, args.nb)
ag.clone_repos()
ag.foreach_student(ag.is_empty_repo)
ag.foreach_student(ag.check_AUTHORS)
ag.foreach_student(ag.check_archi)

ag.generate_report()