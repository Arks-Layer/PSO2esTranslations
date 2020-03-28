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
    "セラフィ": "Seraphy", "ジェネ": "Gene", #Season 1
    "モア": "More", "ザッカード": "Zackard",
    "ブルーノ": "Bruno", "リリーパ族": "Lillipan",
    "ダンテ": "Dante", "アネット": "Annette",
    "レヴィ": "Levi", "ジェネ・モア": "Gene & More",
    "アネット・モア": "Annette & More", "フェル": "Fel",
    "ロード": "Lord", "アネット・ブルーノ": "Annette & Bruno",
    "青年アークス": "Young ARKS", "女性アークス": "Female ARKS",
    "泣いてる女性": "Crying Woman", "ヘイド": "Hade", #Season 2
    "アナティス": "Anatis", "デュナ": "Duna",
    "若い研究員": "Younger Researcher", "老年の研究員": "Older Researcher",
    "シュトラ": "Stra", "カラミティ": "Calamity",
    "クシャネビュラ": "Kuscha Nebula", "次席と呼ばれた女性": "His \"Lovely Assistant\"",
    "クーナ": "Quna", "アネット&ブルーノ": "Annette & Bruno",
    "ヘイズ・ドラール": "Haze Draal", "研究者": "Researcher",
    "リーン": "Lien", "アフタル": "Akhtar", #Season 3
    "ホルシード": "Khorshid", "ソルーシュ": "Soroush",
    "ファルザード": "Falzad", "スレイマン": "Suleiman",
    "ナスリーン": "Nasreen", "アフタル&ホルシード": "Akhtar & Khorshid",
    "艦内放送": "Shipwide Announcement", "アークス戦闘員": "ARKS Soldier",
    "バハール": "Bahar", "ロクサーナー": "Roxana",
    "エルジマルト軍人": "Erzimarut Soldiers", "市民": "Citizen",
    "アークス隊員": "ARKS Member", "アークス救助隊": "ARKS Rescue Team",
    "ソルーシュ（ナレーション）": "Soroush (Narrating)", "瀕死の研究員": "Drowning Researcher",
    "ソルーシュの妻": "Soroush's Wife", "アレーズ": "Arez",
    "闇の残滓": "Dark Remnant", "アークス警備員　Ａ": "ARKS Guard A",
    "アークス警備員　Ｂ": "ARKS Guard B", "アフタル＆ホルシード": "Akhtar & Khorshid",
    "　【残影】　": " [Haddaj] ", "【残影】": "[Haddaj]",
    "女性チップ研究員": "Female Chip Researcher", "アーレスカイゼル": "Ares Kaiser", #Ares
    "アーレスパルチザン": "Ares Partizan", "アーレスランス": "Ares Lance",
    "アーレスソード": "Ares Sword", "チップ研究所　管理官": "Chip Laboratory Officer",
    "アーレスリュウガ": "Ares Ryuuga", "アーレスブーツ": "Ares Boots",
    "アーレスバスター": "Ares Buster", "アーレスネスト": "Ares Nest",
    "アーレスブレード": "Ares Blade", "ア―レスネスト": "Ares Nest",
    "アーレスランチャー": "Ares Launcher", "アーレスタリス": "Ares Talis",
    "パルチザン&ソード": "Partizan & Sword", "ブーツ&バスター": "Boots & Buster",
    "アーレスライフル": "Ares Rifle", "バスター＆ソード": "Buster & Sword",
    "ランス＆パルチザン＆ブーツ": "Lance, Partizan & Boots", "ライフル＆リュウガ": "Rifle & Ryuuga",
    "ネメシスシューズ": "Nemesis Shoes", "ネメシスデュアル": "Nemesis Dual", #Nemesis
    "ネメシスクーガ": "Nemesis Kuuga", "ネメシスキャリバー": "Nemesis Calibur",
    "ネメシスセイバー": "Nemesis Saber", "ネメシスチェイン": "Nemesis Chain",
    "アークスの男性": "Male ARKS", "スレイヴフェザー": "Slave Feather",
    "スレイヴバレット": "Slave Bullet", "スレイヴキャノン": "Slave Cannon",
    "スレイヴクーガ": "Slave Kuuga", "スレイヴセイバー": "Slave Saber",
    "研究所職員A": "Laboratory Staff Member A", "研究所職員B": "Laboratory Staff Member B",
    "研究職員C": "Laboratory Staff Member C",
    "レイニールオービット": "Reinier Orbit", "フロティアオービット": "Flotia Orbit", #Orbit
    "ガイルズオービット": "Gaels Orbit", "カブラカン": "Cabracan",
    "トライヴィンオービット": "Tryvin Orbit", "エイトライオービット": "Eightrei Orbit",
    "トライヴィン＆エイトライ": "Tryvin & Eightrei", "ヴィトルオービット": "Vitol Orbit",
    "トライヴィン＆エイトライ＆ヴィトル": "Tryvin, Eightrei & Vitol",
    "レイニール＆ガイルズ": "Reinier & Gaels", "ガイルズ&エイトライ&ヴィトル": "Gaels, Eightrei & Vitol",
    "ガイルズ＆レイニール＆トライヴィン": "Gaels, Reinier & Tryvin",
    "ガイルズ＆トライヴィン＆レイニール": "Gaels, Tryvin & Reinier",
    "ナレーション": "Narration", "？？？": "???",
    }

for name in file_names:
    items_file_name = name + "_Text" + ".txt"
    item_type = name[1]
    
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
