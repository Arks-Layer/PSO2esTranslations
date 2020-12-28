#!/usr/bin/env python3
# coding=utf8
import codecs
import json
import os
import shutil

json_loc = os.path.join("..", "json")

# load JSON from file
notes_file_name = "SeraphyRoom_SeraphyNote.txt"
try:
    notes_file = codecs.open(os.path.join(json_loc, notes_file_name),
                             mode = 'r', encoding = 'utf-8')
except FileNotFoundError:
    print("\t{0} not found.".format(notes_file_name))
notes = json.load(notes_file)
print("{0} loaded.".format(notes_file_name))
notes_file.close()

generic_lines = {
    "": ""
    }

unknowns = {}

for note in notes:
    # translate generic lines
    if note["jp_text"] != "" and note["tr_text"] == "":
        if note["jp_text"] in generic_lines:
            note["tr_text"] = generic_lines[note["jp_text"]]
        else:
            if note["jp_text"] in unknowns:
                count = unknowns[note["jp_text"]]
                unknowns.update({note["jp_text"]: count + 1})
            else:
                unknowns.update({note["jp_text"]: 1})

# write JSON back to file
notes_file = codecs.open(os.path.join(json_loc, notes_file_name),
                          mode = 'w', encoding = 'utf-8')
json.dump(notes, notes_file, ensure_ascii=False, indent="\t", sort_keys=False)
notes_file.write("\n")
notes_file.close()

sorted_unknowns = {}

sorted_keys = sorted(unknowns, key=unknowns.get, reverse=True)
for key in sorted_keys:
    sorted_unknowns[key] = unknowns[key]

lines = sorted_unknowns.keys()
for line in lines:
    if sorted_unknowns[line] >= 2:
        print("{0} counts of unknown line: {1}".format(sorted_unknowns[line], line.replace("\n", "\\n")))
