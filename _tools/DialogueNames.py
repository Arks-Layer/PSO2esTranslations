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
    # Season 1
    "ザッカード": "Zackard", "レヴィ": "Levi",
    #Season 2
    "泣いてる女性": "Crying Woman", "若い研究員": "Younger Researcher",
    "老年の研究員": "Older Researcher", "次席と呼ばれた女性": "His \"Lovely Assistant\"",
    "アネット&ブルーノ": "Annette & Bruno", "ヘイズ・ドラール": "Haze Draal",
    "研究者": "Researcher",
    #Season 3
    "アフタル&ホルシード": "Akhtar & Khorshid", "艦内放送": "Shipwide Announcement",
    "アークス戦闘員": "ARKS Soldier", "バハール": "Bahar",
    "ロクサーナー": "Roxana", "エルジマルト軍人": "Erzimarut Soldiers",
    "市民": "Citizen", "アークス隊員": "ARKS Member",
    "アークス救助隊": "ARKS Rescue Team", "ソルーシュ（ナレーション）": "Soroush (Narrating)",
    "瀕死の研究員": "Drowning Researcher",     "ソルーシュの妻": "Soroush's Wife",
    "アレーズ": "Arez", "闇の残滓": "Dark Remnant",
    "アークス警備員　Ａ": "ARKS Guard A", "アークス警備員　Ｂ": "ARKS Guard B",
    "アフタル＆ホルシード": "Akhtar & Khorshid", "　【残影】　": " [Haddaj] ",
    "【残影】": "[Haddaj]",
    #Ares
    "女性チップ研究員": "Female Chip Researcher", "チップ研究所　管理官": "Chip Laboratory Officer",
    "パルチザン&ソード": "Partizan & Sword", "ブーツ&バスター": "Boots & Buster",
    "バスター＆ソード": "Buster & Sword", "ランス＆パルチザン＆ブーツ": "Lance, Partizan & Boots",
    "ライフル＆リュウガ": "Rifle & Ryuuga", "第１６防衛中隊": "16th Defense Company",
    "第２地質調査隊": "2nd Geological Survey Squad", "第１２防衛中隊": "12th Defense Company",
    "ア―レスネスト": "Ares Nest", #Note incorrect ― character, should be ー
    #Nemesis
     "研究所職員A": "Laboratory Staff Member A", "研究所職員B": "Laboratory Staff Member B",
     "研究職員C": "Laboratory Staff Member C", "市民Ａ": "Citizen A",
    "アークス隊員Ａ": "ARKS Member A", "アークス隊員B": "ARKS Member B",
    #Orbit
    "カブラカン": "Cabracan", "トライヴィン＆エイトライ": "Tryvin & Eightrei",
    "トライヴィン＆エイトライ＆ヴィトル": "Tryvin, Eightrei & Vitol",
    "レイニール＆ガイルズ": "Reinier & Gaels", "ガイルズ&エイトライ&ヴィトル": "Gaels, Eightrei & Vitol",
    "ガイルズ＆レイニール＆トライヴィン": "Gaels, Reinier & Tryvin",
    "ガイルズ＆トライヴィン＆レイニール": "Gaels, Tryvin & Reinier",
    #Seiga
    "研究員": "Researcher",  "セイガーズ": "Seigas",
    "男性客": "Male Customer",
    #Side
    "ブレイドダンス＆ジェネ": "Blade Dance & Gene", "モア＆セラフィ": "More & Seraphy",
    "ブレイドダンス・ジェネ": "Blade Dance & Gene",
    "？？？（前にいる女の子）": "??? (Girl in front)", "？？？（後ろの女の子）": "??? (Girl in back)",
    "ガンコ": "Gun-ko",
    "アネット・紅葉姫": "Annette & Momijihime",
    "ジェネ総帥": "General Gene", "モア８号": "More #8",
    "モア１９号": "More #19", "村人A": "Villager A",
    "パラティーゼル": "Paratizel",
    "Tヤスミノコフ2000H": "Twin Yasminkov 2000H",
    "Tヤスミノコフ２０００H": "Twin Yasminkov 2000H",
    "Tヤスミノコフ２０００Ｈ": "Twin Yasminkov 2000H",
    "ヤスミノコフ３０００R": "Yasminkov 3000R",
    "ヤスミノコフ４０００F": "Yasminkov 4000F",
    "ヤスミノコフ５０００SD": "Yasminkov 5000SD",
    "ヤスミノコフ７０００V": "Yasminkov 7000V",
    "ヤスミノコフ８０００C": "Yasminkov 8000C",
    "ヤスミノコフ９０００M": "Yasminkov 9000M",
    "ヤスミノコフチーム": "Yasminkov Team",
    "研究所職員": "Laboratory Staff", "アナウンス": "Announcement",
    "ニレンアギト（兄）": "Twin Agito (Older Brother)", "ニレンアギト（妹）": "Twin Agito (Younger Sister)",
    "ニレンオロチ（姉）": "Twin Orochi (Older Sister)", "ニレンオロチ（弟）": "Twin Orochi (Younger Brother)",
    "華やかな女子たち": "Gorgeous Girl",
    "システムメッセージ": "System Message", "アークス処理班": "ARKS Processing Team",
    "子供たち": "Children",
    "屋台の店員": "Food Stand Attendant", "屋台の店員Ａ": "Food Stand Attendant A",
    "屋台の店員Ｂ": "Food Stand Attendant B", "イベント客": "Event Customer",
    "イベント客Ａ": "Event Customer A", "イベント客Ｂ": "Event Customer B",
    "記録音声・Ra-C-0017": "Recording: Ra-C-0017", "記録音声・Hu-H-0028": "Recording: Hu-H-0028",
    "フィジ": "Phys", "ジス": "Sis", "フィジ＆ジス": "Phys & Sis",
    "中トロ号": "Mr. Fishy", "スペースツナ": "Space Tuna",
    "非公式記録（ナレーション）": "Unofficial Record (Narration)", "エッジ？": "Edge?",
    "ユニオンＤブレード&モア": "Union Dual Blade & More",
    "自称・龍の王": "Self-Declared Dragon King",
    "エネミーの群れ": "Enemy Swarm",
    "逃げてきたアークス": "Escaped ARKS", 
    "不機嫌そうなアークス": "Grumpy ARKS",
    "見知らぬアークス": "Strange ARKS",
    "スカル様": "Lord Skull", "清掃業者": "Janitor",
    "作業員": "Operator",
    "スカルダイショウグン": "Great Shogun Skull",
    "怪盗シロクロー": "Phantom Thief Shiro Claw", "怪盗ビアクロー": "Phantom Thief Bear Claw",
    "怪盗ミケクロー": "Phantom Thief Kitty Claw", "怪盗三姉妹": "Phantom Thief Sisters",
    "黒髪の美女": "Black-Haired Beauty",
    "大サンタ": "Great Santa",
    "館内放送": "PA Announcer",
    "セイガーズ　－1": "Other Seigas", "ショーの観客たち": "Spectators",
    "ナレーション(手紙)": "Narration (Letter)",
    "男性ウェポノイド陣": "Male Weaponoids",
    "女性客": "Female Customer",
    "ガラの悪い男性アークス": "Vulgar Male ARKS",
    "リュロ": "Ryuro",
    "ジェネ＆シューティングドライブ": "Gene & Shooting Drive",
    "ファニーブーケライフル＆アネット": "Funny Bouquet Rifle & Annette",
    "アフタル＆ジェネ": "Akhtar & Gene",
    "たまたま近くにいた男性アークス": "Passerby ARKS", "もっとたまたま近くにいた女性アークス": "Passing Female ARKS",
    "モア&ウェポノイドたち": "More & Weaponoids", "人間の声": "Human Voice",
    "招待客": "Guests", "大トロ号": "Sir Fishy",
    "中トロ号＆大トロ号": "Mr. Fishy & Sir Fishy", "護衛のアークス": "ARKS Escort",
    "ナレーション（フウガナギナタ）": "Narration (Fuuga Naginata)",
    "ナレーション（セラフィ）": "Narration (Seraphy)",
    "仮面ストライク１号": "Masked Striker No.1", "仮面ストライク２号": "Masked Striker No.2",
    "魔球王": "King Fastball",
    "マリオネット": "Marionette", "強面のアークス": "Intimidating ARKS",
    "アークス管理官": "ARKS Administrator",
    "ヴォル・ドラゴン": "Vol Dragon", "オービット聖歌隊": "Orbit Choir",
    "デュナ・モア・ジェネ": "Duna/More/Gene", "魔女デステロイド": "Destroid Witch",
    "闇の魔王": "Dark Lord", "街頭ディスプレイ": "Street Display",
    #Special
    "水着三人娘": "Annette, Gene and Bluesy",
    "ジェネ＆アネット＆シューティングドライブ": "Gene, Annette and Shooting Drive",
    "ヴェルドバズ": "Vert Buzz", "アフタル＆ジェネ＆アネット": "Akhtar, Gene & Annette",
    "サンタ包囲網作戦メンバー": "Operation: Catch Santa Members", "サンタクロース": "Santa Claus",
    "ジェネ＆仲間たち": "Gene & Friends", "セラフィと最高の友人たち": "Seraphy and her Friends",
    "子供": "Child", "レッツゴーシャイニー": "Let's Go Shiny",
    #Generics
    "テスト": "", "？？？": "???",
    "アナウンス": "Announcement", "ナレーション": "Narration",
    "ナレーション（ジェネ）": "Narration (Gene)", "ジェネ（ナレーション）": "Gene (Narrating)",
    "ジェネ・モア": "Gene & More", "ジェネ＆モア": "Gene & More",
    "モア・ジェネ": "More & Gene", "モア&ジェネ": "More & Gene",
    "ジェネ＆アネット": "Gene & Annette", "アネット&ジェネ": "Annette & Gene",
    "アネット・モア": "Annette & More", "モア＆ブルーノ": "More & Bruno",
    "アネット・ブルーノ": "Annette & Bruno", "アネット＆ブルーノ": "Annette & Bruno",
    "カラミテイ": "Calamity", "カラミティ＆シュトラ": "Calamity & Stra",
    "ダーカーバスターズ": "Darker Busters", "アークス": "ARKS",
    "全員": "Everyone", "みんな": "Everyone",
    "アークスの男性": "Male ARKS", "女性アークス": "Female ARKS",
    "青年アークス": "Young ARKS", "女の子": "Girl",
    "リリーパ族": "Lillipan",
    "ダーカー": "Darker", "原生種": "Native",
    "機甲種": "Mech", "海王種": "Oceanid"
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
