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
    "解放には\nこのようなチップが必要です。":
        "To release this chip, you will\nneed these material chips.",
    "素材チップは\n日替わりクエストなどで\n手に入りますよ！\nぜひ解放してみてくださいね！":
        "Material chips can be acquired from\nDaily Quests. Please gather materials\nand release this chip!",
    "チップが解放され\nアビリティ性能が高まりました！":
        "This chip has been released, and\nits ability has been enhanced!",
    "ますます強力になった効果を\nぜひ試してみてくださいね！":
        "Please, try using it again\nand see for yourself how\nmuch stronger it is!",
    "『ＰＳＯ２』や『ＰＳＯ２ｅｓ』に\n登場する方々の記憶や技術が込められた\nチップのようです。":
        "This seems to be a chip containing the\nmemories and skills of someone who\nappears in PSO2 or PSO2es.",
    "どのような効果なのでしょう……？\n<%CHARANAME>さんの\n入手情報、お待ちしております！":
        "What kind of effect is it...?\n<%CHARANAME>,\nwe need you to get your hands\non one so that we can find out!",
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
    "このチップは大剣専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Sword only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは自在槍専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Wired Lance only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは長槍専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Partizan only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは双小専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Twin Daggers only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは両剣専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Double Saber only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは鋼拳専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Knuckles only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは銃剣専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Gunslash only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは長銃専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Assault Rifle only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは大砲専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Launcher only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは双機専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Twin Machineguns only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは抜剣専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Katana only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは強弓専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Bullet Bow only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは魔装脚専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Jet Boots only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは 飛翔剣 専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Dual Blades only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは<%wep>専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for <%wep> only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "法術を記録した\nチップのようです。":
        "This seems to be\na Technique chip.",
    "装備したらどのような\n法術を繰り出せるのでしょう……！？\nすごく楽しみですね！":
        "What kind of Technique can you\nperform by equipping this...?!\nI look forward to finding out!",
    "アイテムの効用が記録された\nチップのようです。":
        "This seems to be a chip\ncontaining the effect of\nsome kind of utility item.",
    "どんな効果があるのか\nぜひ入手して確かめてみてください！":
        "Please get one so we can see\nwhat kind of effect it has!",
    "主に<%ele>属性のチップの解放に\n必要な素材チップとなります。\nＦＵＮチップスクラッチや\n日替わりのデイリークエストで\n入手可能ですよ。":
        "This is a Material Chip mostly used\nto release <%ele> chips.\nYou can obtain it from Daily Quests\nand from the FUN Chip Scratch.",
    "主にアークスのチップの解放に\n必要な素材チップとなります。\nＦＵＮチップスクラッチや\n日替わりのデイリークエストで\n入手可能ですよ。":
        "This is a Material Chip mostly used\nto release ARKS chips.\nYou can obtain it from Daily Quests\nand from the FUN Chip Scratch.",
    "様々なチップ解放に\n必要な素材チップとなります。\nＦＵＮチップスクラッチや\n各曜日の日替わりクエストで\n入手可能ですよ。":
        "This is a Material Chip used to\nrelease all kinds of chips.\nYou can obtain it from Daily Quests\nand from the FUN Chip Scratch.",
    "様々なチップ解放に\n必要な素材チップとなります。\n各曜日の日替わりクエストで\n入手可能ですよ。":
        "This is a Material Chip used to\nrelease all kinds of chips.\nYou can obtain it from Daily Quests.",
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
