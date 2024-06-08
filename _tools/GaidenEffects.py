#!/usr/bin/env python3
# coding=utf8
import codecs
import json
import os
import shutil

json_loc = os.path.join("..", "json")


effect_names_file_name = "UI_Weaponoid_BondsEffect.txt"
effect_descriptions_file_name = "UI_Weaponoid_ReleaseAbility.txt"

# load JSON from effect names file
try:
    effect_names_file = codecs.open(os.path.join(json_loc, effect_names_file_name),
                             mode = 'r', encoding = 'utf-8')
except FileNotFoundError:
    print("\t{0} not found.".format(effect_names_file_name))
effect_names = json.load(effect_names_file)
print("{0} loaded.".format(effect_names_file_name))
effect_names_file.close()

# load JSON from effect descriptions file
try:
    effect_descriptions_file = codecs.open(os.path.join(json_loc, effect_descriptions_file_name),
                             mode = 'r', encoding = 'utf-8')
except FileNotFoundError:
    print("\t{0} not found.".format(effect_descriptions_file_name))
effect_descriptions = json.load(effect_descriptions_file)
print("{0} loaded.".format(effect_descriptions_file_name))
effect_descriptions_file.close()

effect_types = {
    "発動率アップ": "Activation Rate Up",
    "ボーナス属性": "Bonus Element",
    "効果発動変更": "Change Trigger",
    "チップコストダウン": "Chip Cost Down",
    "消費ＣＰダウン": "CP Usage Down",
    "効果適用拡大": "Effect Broadened",
    "効果時間延長": "Effect Extended",
    "パラメータアップ": "Parameters Up",
    "継続パラメータ回復": "Recovery Over Time",
    "特定状態異常付与": "Inflicts Status Effect",
    }

effect_effects = { # dictionary of lambdas because there's no such thing as switch-case in python
    "Activation Rate Up":   lambda x:   x.replace("このチップのアビリティの発動率が",
                                                  "This chip's activation rate is increased by ")
                                         .replace("％上昇する。",
                                                  "%."),
    "Bonus Element":        lambda x:   x.replace("このチップを装備した時のElement値上昇を\n",
                                                  "This chip's element value is also added\nto the ")
                                         .replace("に対しても適用する。",
                                                  " when equipped."),
    "Change Trigger":       lambda x:   x.replace("このチップの効果の発動を攻撃ヒット時に変更する。",
                                                  "This chip's activation condition changes to\n"
                                                  "'when you successfully hit with an attack'."),
    "Chip Cost Down":       lambda x:   x.replace("このチップのコストが",
                                                  "This chip's equip cost is reduced by ")
                                         .replace("減少する。",
                                                  "."),
    "CP Usage Down":        lambda x:   x.replace("このチップのアビリティの消費ＣＰが",
                                                  "This chip's CP consumption is reduced by ")
                                         .replace("減少する。",
                                                  "."),
    "Effect Broadened":     lambda x:   x.replace("このチップのアビリティの効果の対象に\n",
                                                  "This chip's ability now also covers\nthe ")
                                         .replace("このチップのアビリティ①の効果の対象に\n",
                                                  "This chip's 1st ability now also covers\nthe ")
                                         .replace("このチップのアビリティ②の効果の対象に\n",
                                                  "This chip's 2nd ability now also covers\nthe ")
                                         .replace("を追加する。",
                                                  "."),
    "Effect Extended":      lambda x:   x.replace("このチップのアビリティの効果時間を",
                                                  "Ability's Effect Duration is extended by ")
                                         .replace("秒延長する。",
                                                  " seconds."),
    "Parameters Up":        lambda x:   x.replace("が＋",
                                                  " increases by ")
                                         .replace("上昇する。",
                                                  " when equipped."),
    "Recovery Over Time":   lambda x:   x.replace("戦闘中、一定時間毎にHPが",
                                                  "Recovers your HP by ")
                                         .replace("％回復する。",
                                                  "% at regular intervals during battle.")
                                         .replace("戦闘中、一定時間毎にＣＰが",
                                                  "Recovers your CP by ")
                                         .replace("回復する。",
                                                  " at regular intervals during battle."),
    "Inflicts Status Effect":   lambda x: x.replace("チップ発動時に一定確率で\n敵全体に",
                                                  "This chip's activation has a chance\nto inflict ")
                                         .replace("の状態異常を付与する。",
                                                  " on enemies.")
    }

unknowns = []

for effect in effect_names:
    effect_assign = effect["assign"]
    
    #effect_text = list(filter(lambda effect: effect["assign"] == effect_assign, effect_descriptions))[0]["jp_text"] #disgusting
    if effect["jp_text"] != "":
        if effect["jp_text"] in effect_types:
            effect["tr_text"] = effect_types[effect["jp_text"]] # translate effect name

            for description in effect_descriptions:
                if description["assign"] == effect_assign:
                    effect_text = description["jp_text"]
            
                    # some things are used in multiple effect types
                    effect_text = effect_text.replace("ＨＰ", "HP")
                    effect_text = effect_text.replace("法術", "Techs")
                    effect_text = effect_text.replace("炎", "Fire ")
                    effect_text = effect_text.replace("氷", "Ice ")
                    effect_text = effect_text.replace("雷", "Lightning ")
                    effect_text = effect_text.replace("風", "Wind ")
                    effect_text = effect_text.replace("光", "Light ")
                    effect_text = effect_text.replace("闇", "Dark ")
                    effect_text = effect_text.replace("属性", "Element")
                    effect_text = effect_text.replace("パニック", "Panic")
                    # translation depends on effect type, so:
                    effect_text = effect_effects[effect["tr_text"]](effect_text)
                    description["tr_text"] = effect_text
        else:
            if effect["jp_text"] not in unknowns:
                print("Unknown short description in {0}: {1}".format(effect_names_file_name, effect["jp_text"]))
                unknowns.append(effect["jp_text"])

# write JSON back to files
effect_names_file = codecs.open(os.path.join(json_loc, effect_names_file_name),
                          mode = 'w', encoding = 'utf-8')
json.dump(effect_names, effect_names_file, ensure_ascii=False, indent="\t", sort_keys=False)
effect_names_file.write("\n")
effect_names_file.close()

effect_descriptions_file = codecs.open(os.path.join(json_loc, effect_descriptions_file_name),
                          mode = 'w', encoding = 'utf-8')
json.dump(effect_descriptions, effect_descriptions_file, ensure_ascii=False, indent="\t", sort_keys=False)
effect_descriptions_file.write("\n")
effect_descriptions_file.close()
