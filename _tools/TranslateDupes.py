#!/usr/bin/env python3
# coding=utf8
import codecs
from collections import OrderedDict
import fnmatch
import json
import os
import shutil
import argparse

json_loc = os.path.join("..", "json")

parser = argparse.ArgumentParser(
    description = "Translates duplicate item names and descriptions.")

parser.add_argument("-f", type = str, dest = "file", action = "store",
                    default = "", help = ("Designate a specific file to translate."
                                          "Do not include the file extension. (.txt)"))

args = parser.parse_args()

print(args)

if args.file != "":
    file_names = fnmatch.filter(os.listdir(json_loc), args.file + '.txt')
else:
    file_names = fnmatch.filter(os.listdir(json_loc), 'Item_Stack_*.txt')
    file_names += fnmatch.filter(os.listdir(json_loc), 'Item_*Wear_*.txt')
    file_names += fnmatch.filter(os.listdir(json_loc), 'Item_Facepattern.txt')

for file_name in file_names:
    try:
        items_file = codecs.open(os.path.join(json_loc, file_name),
                                 mode = 'r', encoding = 'utf-8')
    except FileNotFoundError:
        print("\t{0} not found.".format(file_name))
        continue
    
    items = json.load(items_file)
    print("{0} loaded.".format(file_name))
    items_file.close()

    dupes1 = 0
    dupes2 = 0
    
    for item in items:
        for item2 in items:
            if (item["jp_text"] == item2["jp_text"]
            and item ["tr_text"] == "" and item2 ["tr_text"] != ""):
                item["tr_text"] = item2["tr_text"]
                dupes1 += 1
            if (item["jp_explain"] == item2["jp_explain"]
            and item ["tr_explain"] == "" and item2 ["tr_explain"] != ""):
                item["tr_explain"] = item2["tr_explain"]
                dupes2 += 1
            continue
        continue

    print("\t{0} duplicate item names translated.".format(dupes1))
    print("\t{0} duplicate item descriptions translated.".format(dupes2))
    
    items_file = codecs.open(os.path.join(json_loc, file_name),
                             mode = 'w', encoding = 'utf-8')
    json.dump(items, items_file, ensure_ascii=False, indent="\t", sort_keys=False)
    items_file.write("\n")
    items_file.close()
