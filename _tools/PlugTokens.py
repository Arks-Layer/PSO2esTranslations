#!/usr/bin/env python3
# coding=utf8
import codecs
import json
import os
import shutil

json_loc = os.path.join("..", "json")


tokens_file_name = "Awakening_Skill_Explain_Token.txt"

# load JSON from tokens file
try:
    tokens_file = codecs.open(os.path.join(json_loc, tokens_file_name),
                             mode = 'r', encoding = 'utf-8')
except FileNotFoundError:
    print("\t{0} not found.".format(tokens_file_name))
tokens = json.load(tokens_file)
print("{0} loaded.".format(tokens_file_name))
tokens_file.close()

token_dict = {
    "炎属性": "Fire Element",
    "氷属性": "Ice Element",
    "風属性": "Wind Element",
    "雷属性": "Lightning Element",
    "光属性": "Light Element",
    "闇属性": "Dark Element",
    "攻撃ヒット時": "landing an attack",
    "ＪＡ成功時もしくはスライド操作時": "successful JA or Slide Action"
    }

numtable = "".maketrans("０１２３４５６７８９％", "0123456789%")

for token in tokens:
    if token["jp_token"] in token_dict:
        token["tr_token"] = token_dict[token["jp_token"]]
    else:
        token["tr_token"] = token["jp_token"].translate(numtable)

# write JSON back to files
tokens_file = codecs.open(os.path.join(json_loc, tokens_file_name),
                          mode = 'w', encoding = 'utf-8')
json.dump(tokens, tokens_file, ensure_ascii=False, indent="\t", sort_keys=False)
tokens_file.write("\n")
tokens_file.close()

