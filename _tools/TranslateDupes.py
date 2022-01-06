#!/usr/bin/env python3
# coding=utf8
import codecs
from collections import OrderedDict
import fnmatch
import json
import os
import shutil

json_loc = os.path.join("..", "json")

file_names = fnmatch.filter(os.listdir(json_loc), 'Item_Stack_*.txt')
file_names += fnmatch.filter(os.listdir(json_loc), 'Item_*Wear_*.txt')

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

    dupes = 0
    
    for item in items:
        for item2 in items:
            if (item["jp_text"] == item2["jp_text"]
            and item ["tr_text"] == "" and item2 ["tr_text"] != ""):
                item["tr_text"] = item2["tr_text"]
                dupes += 1
            continue
        continue

    print("\t{0} duplicate item names translated.".format(dupes))
    
    items_file = codecs.open(os.path.join(json_loc, file_name),
                             mode = 'w', encoding = 'utf-8')
    json.dump(items, items_file, ensure_ascii=False, indent="\t", sort_keys=False)
    items_file.write("\n")
    items_file.close()
