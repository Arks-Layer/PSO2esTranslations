#!/usr/bin/env python3
# coding=utf8
import codecs
import json
import os
import regex
import shutil

json_loc = os.path.join("..", "json")

skills_file_name = "ChipExplain_BoostSkillExplain.txt"
try:
    skills_file = codecs.open(os.path.join(json_loc, skills_file_name),
                             mode = 'r', encoding = 'utf-8')
except FileNotFoundError:
    print("\t{0} not found.".format(skills_file_name))
skills = json.load(skills_file)
print("{0} loaded.".format(skills_file_name))
skills_file.close()

unknowns = []

skills_file = codecs.open(os.path.join(json_loc, skills_file_name),
                         mode = 'w', encoding = 'utf-8')
json.dump(skills, skills_file, ensure_ascii=False, indent="\t", sort_keys=False)
skills_file.write("\n")
skills_file.close()
