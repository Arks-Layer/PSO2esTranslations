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
    "『ＰＳＯ２』や『ＰＳＯ２ｅｓ』に\n登場する方々の記憶や技術が込められた\nチップのようです。":
        "This seems to be a chip containing the\nmemories and skills of someone who\nappears in PSO2 or PSO2es.",
    "どのような効果なのでしょう……？\n<%CHARANAME>さんの\n入手情報、お待ちしております！":
        "What kind of effect is it...?\n<%CHARANAME>,\nwe need you to get your hands\non one so that we can find out!",
    "解放には\nこのようなチップが必要です。":
        "To release this chip, you will\nneed these material chips.",
    "素材チップは\n日替わりクエストなどで\n手に入りますよ！\nぜひ解放してみてくださいね！":
        "Material chips can be acquired from\nDaily Quests. Please gather materials\nand release this chip!",
    "チップが解放されアビリティが\n「<%abi>」に\nなりました！\n性能もより強化されていますよ！":
        "This chip has been released,\nand its ability has become\n\"<%abi>\"!\nIts performance can also be\nenhanced even further than before!",
    "『ＰＳＯ２』や『ＰＳＯ２ｅｓ』に\n登場する方々が描かれた\nイラストチップのようです。":
        "This seems to be an illustration\nchip featuring someone who\nappears in PSO2 or PSO2es.",
    "もしかしたら\nいつもと違う一面が見られるかも？\nぜひコレクションに加えてくださいね！":
        "Maybe you'll get to see\nanother side of them?\nPlease do your best to\nadd it to your collection!",
    "必殺技を記録した\nチップのようです。": 
        "This seems to be a Photon Art chip.",
    "装備したらどのような\n必殺技を繰り出せるのでしょう……！？\nすごく楽しみですね！":
        "What kind of Photon Art can you\nperform by equipping this...?!\nI look forward to finding out!",
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
