#!/usr/bin/env python3
# coding=utf8
import codecs
import json
import os
import shutil

json_loc = os.path.join("..", "json")

file_names = ["Season1", "Season2", "Season3",
              "Arles", "Nemesis", "Orbit", "Seiga",
              "Side", "Special"]

character_names = {
    }

try:
    chips_file = codecs.open(os.path.join(json_loc, "Name_Chip_SPArksName.txt"),
                             mode = 'r', encoding = 'utf-8')
    chips = json.load(chips_file)
    print("Chip names loaded")
    chips_file.close()
    
except FileNotFoundError:
    print("\t{0} not found.".format(items_file_name))

for name in file_names:
    items_file_name = name + "_Text" + ".txt"
    
    try:
        items_file = codecs.open(os.path.join(json_loc, items_file_name),
                                 mode = 'r', encoding = 'utf-8')
    except FileNotFoundError:
        print("\t{0} not found.".format(items_file_name))
        continue
    
    items = json.load(items_file)
    print("{0} loaded.".format(items_file_name))
    
    items_file.close()

    unknowns = []
    for item in items:
        if item["jp_name"] != "" and item["jp_name"] != "-" and item["tr_name"] == "":
            if chips:
                for c in chips:
                    if c["jp_text"] == item["jp_name"]:
                        item["tr_name"] = c["tr_text"]
                        break
            
            if item["tr_name"] != "": continue
            
            if item["jp_name"] in character_names:
                item["tr_name"] = character_names[item["jp_name"]]
            else:
                if item["jp_name"] not in unknowns:
                    print("Unknown character name in {0}: {1}".format(name, item["jp_name"]))
                    unknowns.append(item["jp_name"])

    items_file = codecs.open(os.path.join(json_loc, items_file_name),
                             mode = 'w', encoding = 'utf-8')
    json.dump(items, items_file, ensure_ascii=False, indent="\t", sort_keys=False)
    items_file.write("\n")
    items_file.close()
