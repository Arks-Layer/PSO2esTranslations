#!/usr/bin/env python3
# coding=utf8
import codecs
import json
import os
import shutil

json_loc = os.path.join("..", "json")

# load JSON from file
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
    "効果時間延長": "Effect Duration Extended",
    "ＨＰ自動回復": "HP Regeneration",
    "ダウン・のけぞり無効付与": "Knockdown/Flinch Immune",
    "属性値上限アップ": "Maximum Element Up",
    "技・法終了時パラメータＵＰ": "Params Up After PA/Tech",
    "プレイヤーパラメータ加算": "Player Parameter Increase",
    "プレイヤーパラメータ増加": "Player Parameter Boost",
    "ラッシュアーツダメージアップ": "Rush Arts Damage Up",
    "シールド": "Shield",
    "状態異常回復": "Status Recovery",
    "ダメージ軽減": "Damage Reduction",
    "戦闘不能回避": "Prevents Incapacitation",
    }

skill_effects = { # dictionary of lambdas because there's no such thing as switch-case in python
    "Action CP Recovery":           lambda x:   x.replace("スライド操作時 に\\nＣＰが ",
                                                          "Slide Actions have a chance to recover ")
                                                 .replace(" 回復する。(発動確率： 小 )",
                                                          " CP.\\n(Activation rate: Low)"),
    "Action HP Recovery":           lambda x:   x.replace("スライド操作時 に\\nＨＰが ",
                                                          "Slide Actions have a chance to recover ")
                                                 .replace("％ 回復する。(発動確率： 小 )",
                                                          "% HP.\\n(Activation rate: Low)"),
    "Activation Rate Up":           lambda x:   x.replace("装備したサポートチップの発動率が ",
                                                          "Increases linked Support Chip's\\nactivation rate by ")
                                                 .replace("％ 上昇する。",
                                                          "%."),
    "Additional Damage":            lambda x:   x.replace("装備した必殺技・法術がヒットした時に\\n追加で ",
                                                          "Deals an additional ")
                                                 .replace("％ のダメージを与える。",
                                                          "% damage when\\nhitting with the linked PA/Tech.\\n"
                                                          "<color=yellow>[Chase]</color>"),
    "Chip Parameter Boost":         lambda x:   x.replace("装備したチップの ",
                                                          "Boosts linked chip's ")
                                                 .replace(" を ",
                                                          " by ")
                                                 .replace("％",
                                                          "%")
                                                 .replace(" 増加する。",
                                                          ".")
                                                 .replace("\\n",
                                                          "\\nand boosts its "),
    "CP Consumption Down":          lambda x:   x.replace("装備したアクティブチップの消費ＣＰが ",
                                                          "Reduces the CP consumption of a linked\\nActive Chip by ")
                                                 .replace("％ 減少する。",
                                                          "%."),
    "CP Usage Reduced":             lambda x:   x.replace("装備したチップの消費ＣＰを ",
                                                          "Reduces the linked chip's CP consumption by ")
                                                 .replace("％ 軽減する。",
                                                          "%."),
    "Damage Taken Down":            lambda x:   x.replace("装備した必殺技・法術発動中は\\n受けるダメージを ",
                                                          "While using the linked PA/Tech, reduces\\n"
                                                          "damage taken by ")
                                                 .replace("％ 軽減する。",
                                                          "%."),
    "Damage Up":                    lambda x:   x.replace("装備した必殺技・法術のダメージ量を ",
                                                          "Boosts the damage of the linked PA/Tech by ")
                                                 .replace("％ 増加する。",
                                                          "%."),
    "Damage Up Vs. Status":         lambda x:   x.replace("状態異常の敵に対して、装備した必殺技・法術の\\nダメージ量を ",
                                                          "Boosts the damage of the linked PA/Tech by ")
                                                 .replace("％ 増加する。",
                                                          "%\\nagainst enemies affected by a status effect."),
    "Element Damage Up":            lambda x:   "Boosts " + x
                                                 .replace(" が弱点の敵に対し\\nその属性によるダメージを ",
                                                          " damage by ")
                                                 .replace("％ 増加する。",
                                                          "%\\nagainst enemies weak to it.\\n"
                                                          "<color=yellow>[S-Frame]</color>"),
    "Effect Duration Extended":     lambda x:   x.replace("装備したチップのアビリティ効果時間を ",
                                                          "Extends the linked chip's effect duration\\nby ")
                                                 .replace("秒 延長する。",
                                                          " seconds."),
    "HP Regeneration":              lambda x:   x.replace("定期的にＨＰを ",
                                                          "Recovers ")
                                                 .replace("％ 回復する。\\nアビリティレベルに応じて回復するタイミングが早くなる。",
                                                          "% of max HP at regular intervals.\\n"
                                                          "Recovery speed increases based on this chip's\\nability level."),
    "Knockdown/Flinch Immune":      lambda x:   x.replace("装備した必殺技・法術発動時に、一定時間\\n"
                                                          "ダウン・のけぞり無効となる効果を付与する。\\n"
                                                          "（必殺技・法術終了時に効果も終了する）",
                                                          "Makes you immune to knockdown and\\n"
                                                          "flinching while you perform the linked\\n"
                                                          "PA/Technique. (Effect ends when the\\n"
                                                          "PA/Technique does.)"),
    "Maximum Element Up":           lambda x:   "Increases your maximum " + x
                                                 .replace(" の上限値が ",
                                                          " by ")
                                                 .replace(" 上昇する。",
                                                          "."),
    "Parameters Up After PA/Tech":  lambda x:   x.replace("装備先のチップ発動後\\n"
                                                          "ジャストアタック可能なタイミングから\\n一定時間、 ",
                                                          "Boosts ")
                                                 .replace("攻撃力全般 を ",
                                                          "ATK by ")
                                                 .replace("防御力全般 を ",
                                                          "DEF by ")
                                                 .replace("％ 増加する。",
                                                          "% for 10 seconds when\\n"
                                                          "the Just Attack ring appears after\\n"
                                                          "using the linked PA/Tech."),
    "Player Parameter Boost":       lambda x:   x.replace("プレイヤーの 攻撃力全般 を ",
                                                          "Boosts player ATK by ")
                                                 .replace("％ 増加する。",
                                                          "%."),
    "Player Parameter Increase":    lambda x:   x.replace("プレイヤーの HP を ",
                                                          "Increases player HP by ")
                                                 .replace(" 上昇する。\\nさらにアビリティレベルに応じて、上昇量が増える。",
                                                          " + 10 x this chip's\\nability level."),
    "Rush Arts Damage Up":          lambda x:   x.replace("ラッシュアーツのダメージ量を ",
                                                          "Boosts Rush Arts damage by ")
                                                 .replace("％ 増加する。",
                                                          "%."),
    "Shield":                       lambda x:   x.replace("ＨＰの最大値の ",
                                                          "Grants you a shield that prevents damage up to\\n")
                                                 .replace("％ 分のダメージを\\n防ぐ効果をＨＰに上乗せする。\\n"
                                                          "さらにアビリティレベルに応じて、上乗せする値が増える。",
                                                          "% of your maximum HP + 1% x this chip's\\n"
                                                          "ability level."),
    "Status Recovery":              lambda x:   x.replace("スライド操作時 に\\n状態異常 が回復する。(発動確率： 小＋  )\\nアビリティレベルが上昇すると発動確率が上昇する。",
                                                          "Slide Actions have a chance to remove status\\neffects. (Activation rate: Low+)\\nActivation rate increases with ability level."),
    "Damage Reduction":             lambda x:   x.replace("受けるダメージを ",
                                                          "Reduces damage taken by ")
                                                 .replace("％ 軽減する。\\nさらにアビリティレベルに応じて、軽減する値が増える。",
                                                          "%.\\nDamage reduction increases with ability level."),
    "Prevents Incapacitation":      lambda x:   x.replace("ＨＰが ",
                                                          "Once per battle, keeps you from being incapacitated\\nwhile at or above ")
                                                 .replace("％ 以上残っている場合、\\n一度だけ戦闘不能にならない。\\nアビリティレベルが上昇すると\\n効果発動するためのＨＰの残り％が減る。",
                                                          "% HP.\\nHP threshold decreases as ability level increases.")
    }

unknowns = []

for skill in skills:
    # translate short descriptions
    if skill["jp_explainShort"] != "" and skill["tr_explainShort"] == "":
        if skill["jp_explainShort"] in skill_names:
            skill["tr_explainShort"] = skill_names[skill["jp_explainShort"]]
        else:
            if skill["jp_explainShort"] not in unknowns:
                print("Unknown short description in {0}: {1}".format(skills_file_name, skill["jp_explainShort"]))
                unknowns.append(skill["jp_explainShort"])
    
    # translate long descriptions
    if skill["jp_explainLong"] != "" and skill["tr_explainLong"] == "":
        skill_text = skill["jp_explainLong"]

        if skill["tr_explainShort"] in skill_effects:
            # elements are used in multiple skill types
            skill_text = skill_text.replace("炎属性", "Fire Element")
            skill_text = skill_text.replace("氷属性", "Ice Element")
            skill_text = skill_text.replace("雷属性", "Lightning Element")
            skill_text = skill_text.replace("風属性", "Wind Element")
            skill_text = skill_text.replace("光属性", "Light Element")
            skill_text = skill_text.replace("闇属性", "Dark Element")
            # translation depends on skill type, so:
            skill_text = skill_effects[skill["tr_explainShort"]](skill_text)
            skill["tr_explainLong"] = skill_text

# write JSON back to file
skills_file = codecs.open(os.path.join(json_loc, skills_file_name),
                          mode = 'w', encoding = 'utf-8')
json.dump(skills, skills_file, ensure_ascii=False, indent="\t", sort_keys=False)
skills_file.write("\n")
skills_file.close()
