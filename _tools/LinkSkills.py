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

skill_names = {
    "特定操作時ＣＰ回復": "Action CP Recovery",
    "特定操作時ＨＰ回復": "Action HP Recovery",
    "発動率アップ": "Activation Rate Up",
    "追加ダメージ付与": "Additional Damage",
    "チップパラメータ増加": "Chip Parameter Boost",
    "発動ＣＰダウン": "CP Consumption Down",
    "ＣＰ消費量軽減": "CP Usage Reduced",
    "ダメージカット付与": "Damage Taken Down",
    "ダメージアップ": "Damage Up",
    "敵状態異常時ダメージアップ": "Damage Up Vs. Status",
    "属性ダメージアップ": "Element Damage Up",
    "効果時間延長": "Extend Effect Time",
    "ＨＰ自動回復": "HP Regeneration",
    "ダウン・のけぞり無効付与": "Knockdown/Flinch Immune",
    "属性値上限アップ": "Maximum Element Up",
    "技・法終了時パラメータＵＰ": "PA/Tech JA Parameters Up",
    "プレイヤーパラメータ加算": "Player Parameter Increase",
    "プレイヤーパラメータ増加": "Player Parameters Up",
    "ラッシュアーツダメージアップ": "Rush Arts Damage Up",
    "シールド": "Shield"
    }

skill_effects = {
    "Action CP Recovery": lambda x: x.replace("スライド操作時 に\\nＣＰが ", "Slide Actions have a chance to recover ").
                                          replace(" 回復する。(発動確率： 小 )", " CP.\\n(Activation rate: Low)"),
    "Action HP Recovery": lambda x: x.replace("スライド操作時 に\\nＨＰが ", "Slide Actions have a chance to recover ").
                                          replace("％ 回復する。(発動確率： 小 )", "% HP.\\n(Activation rate: Low)"),
    }

unknowns = []

for skill in skills:
    if skill["jp_explainShort"] != "" and skill["tr_explainShort"] == "":
        if skill["jp_explainShort"] in skill_names:
            skill["tr_explainShort"] = skill_names[skill["jp_explainShort"]]
        else:
            if skill["jp_explainShort"] not in unknowns:
                print("Unknown short description in {0}: {1}".format(skills_file_name, skill["jp_explainShort"]))
                unknowns.append(skill["jp_explainShort"])
    
    if skill["jp_explainLong"] != "" and skill["tr_explainLong"] == "":
        skill_text = skill["jp_explainLong"]

        if skill["tr_explainShort"] in skill_effects:
            skill_text = skill_effects[skill["tr_explainShort"]](skill_text)
            skill["tr_explainLong"] = skill_text

skills_file = codecs.open(os.path.join(json_loc, skills_file_name),
                          mode = 'w', encoding = 'utf-8')
json.dump(skills, skills_file, ensure_ascii=False, indent="\t", sort_keys=False)
skills_file.write("\n")
skills_file.close()
