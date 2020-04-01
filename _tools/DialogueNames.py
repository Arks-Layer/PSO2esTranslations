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
    "研究員": "Researcher", "セイガーソード": "Seiga Sword", #Seiga
    "セイガーシールド": "Seiga Shield", "セイガージャベリン": "Seiga Javelin",
    "セイガーズ": "Seigas", "セイガーランチャー": "Seiga Launcher",
    "セイガーアーチャー": "Seiga Archer", "スカルシュクター": "Skull Schecter",
    "スカルソーサラー": "Skull Sorcerer", "スカルフェジサー": "Skull Feschieser",
    "男性客": "Male Customer",
    "ドラゴンスレイヤー": "Dragon Slayer", "ナスヨテリ": "Nasuyoteri", #Side stories
    "恋鳳凰": "Koi Houou", "アダマンの杖": "Mace of Adaman",
    "ブレイドダンス": "Blade Dance", "ブレイドダンス＆ジェネ": "Blade Dance & Gene",
    "モア＆セラフィ": "More & Seraphy", "ブレイドダンス・ジェネ": "Blade Dance & Gene",
    "ヤミガラス": "Yamigarasu", "バイオトライナー": "Bio Triner",
    "テンイムソウ": "Tenimusou", "ストライクブルート": "Strike Brute",
    "Ｈ４４ミズーリＴ": "H44 Missouri T", "セイメイキカミ": "Seimei Kikami",
    "インペリアルピック": "Imperial Pick", "レッドスコルピオ": "Red Scorpio",
    "ニョイボウ": "Monkey King Bar", "ロゼフロッツ": "Rose Flotz",
    "曙": "Akebono", "？？？（前にいる女の子）": "??? (Girl in front)",
    "？？？（後ろの女の子）": "??? (Girl in back)", "シャットラウンダー": "Shut Rounder",
    "ガンコ": "Gun-ko", "ディエスリュウ": "Dies Ryu",
    "ラビットウォンド": "Rabbit Wand", "グロリアスウィング": "Glorious Wing",
    "モタブの預言書": "Motav Prophecy", "レントオーナム": "Rentaunam",
    "ジャッジメントハーツ": "Judgment Hearts", "ノワルミラーズ": "Noire Mirrors",
    "紅葉姫": "Momijihime", "アネット・紅葉姫": "Annette & Momijihime",
    "ニレンカムイ": "Twin Kamui", "サイコウォンド": "Psycho Wand",
    "ブルージーレクイエム": "Bluesy Requiem", "ノクスディナス": "Nox Dinas",
    "サルスパニッシャー": "Sarce Punisher", "ジェネ総帥": "General Gene",
    "モア８号": "More #8", "モア１９号": "More #19",
    "村人A": "Villager A", "華散王": "Kazanou",
    "セイクリッドダスター": "Sacred Duster", "タービュラス": "Turbulas",
    "リンドクレイ": "Lindcray", "ブラオレット": "Vraolet",
    "ブラスハウル": "Brass Haul", "マインバンカー": "Mine Bunker",
    "パラティーゼル": "Paratizel", "ナールクレセント": "Narl Crescent",
    "トールマリンカ": "Tourmalinca", "バイオベルド": "Bio Beld",
    "ビスケドロプ": "Biskedrop", "アヴェンジャー": "Avenger",
    "レイディアント": "Radiant", "フレイフィオーラ": "Frey Fiora",
    "ミリオブライト": "Millioblight", "イデアルシザーズ": "Ideal Scissors",
    "ディオティグリドル": "Dio Tigredor", "インペリアルピック-NT": "Imperial Pick-NT",
    "ウェドルパーク": "Weddle Park", "スサノショウハ": "Susano Shouha",
    "スサノシナリ": "Susano Shinari", "ゴッドハンド": "God Hand",
    "アストラルライザー": "Astral Riser", "流星棍": "Meteor Cudgel",
    "エリュシオン": "Elysion", "スプレッドニードル": "Spread Needle",
    "マダムノアマガサ": "Madam's Umbrella", "イデアルデュオス": "Ideal Duos",
    "Tヤスミノコフ2000H": "Twin Yasminkov 2000H", "フリートマリンカ": "Fleetmalinca",
    "シルフマリンカ": "Sylphmalinca", "ロックナックル": "Rock Knuckle",
    "ヴォルカノメイス": "Volcano Mace", "夕雁渡": "Yuukari Watashi",
    "ホローギムレット": "Hollow Gimlet", "フブキトウシュウ": "Fubuki Toushuu",
    "ミヤビセン": "Miyabisen", "セイントフェザー": "Saint Feather",
    "ライブステイド": "Live Staid", "ルーライラ": "Rulyra",
    "オーバーテイル": "Overtail", "パンプキンロッド": "Pumpkin Rod",
    "ファイアーアームズ": "Firearms", "リンドブルム": "Lindwurm",
    "フラウディア": "Flowdia", "エグパスカ": "Egg Paska",
    "ジェネ＆モア": "Gene & More", "ヴェルトバズ": "Vert Buzz",
    "ギフトサック": "Gift Sack", "ダールワイグル": "Darl Weigle",
    "セラータクレイン": "Serata Crane", "ザンバ": "Zanba",
    "シューティングドライブ": "Shooting Drive", "ガーンデーヴァ": "Gandiva",
    "オプトレリート": "Optrelieto", "リグガヴエル": "Riggavuel",
    "クイーンヴィエラ": "Queen Viera", "ヴィヴィアン": "Vivienne",
    "クラーリタ・ヴィサス": "Clarita Visas", "エビルカースト": "Evil Curst",
    "ギガススピナー": "Gigas Spinner", "カルデスタ": "Cardesta",
    "ラヴィス＝ブレイド": "Lavis Blade", "ガルウィンド": "Gal Wind",
    "ガルド・ミラ": "Guld Milla", "ビューレイアール": "Beuray Earl",
    "モア・ジェネ": "More & Gene", "フラドール": "Fradoll",
    "ファイナルインパクト": "Final Impact", "ギリハート": "Giri Heart",
    "ルフネシア": "Lufnesia", "ウィンドミル": "Windmill",
    "ファーレングリフ": "Fahrenglyph", "ノクスカディナ": "Nox Cadina",
    "ライトニングエスパーダ": "Lightning Espada", "ヤシャ": "Yasha",
    "エンシェントクォーツ": "Ancient Quartz", "ケイトレイター": "Kae Traitor",
    "パオジェイド": "Pao Jade", "リカウテリ": "Rikauteri",
    "禍蹴ピリカネト": "Evil Pirikanet", "ルチルス": "Lutyrus",
    "ジェネ＆アネット": "Gene & Annette", "アサシンクロー": "Assassin Claw",
    "クラフトプロジオン": "Craft Plosion", "アークフラン": "Ark Flan",
    "新光小槌": "Pristine Small Hammer", "アーディロウ": "Ardillo",
    "ファニーブーケライフル": "Funny Bouquet Rifle", "グラヴィリオス": "Gravilios",
    "トライデントクラッシャー": "Trident Crusher", "ＳＳＰＮランチャー": "SSPN Launcher",
    "モア&ジェネ": "More & Gene", "シェーンフリサ": "Shanefrisa",
    "アギト": "Agito", "オロチアギト": "Orochiagito",
    "ニレンアギト（兄）": "Twin Agito (Older Brother)", "ニレンアギト（妹）": "Twin Agito (Younger Sister)",
    "ニレンアギト": "Twin Agito", "ニレンオロチ（姉）": "Twin Orochi (Older Sister)",
    "ニレンオロチ（弟）": "Twin Orochi (Younger Brother)", "ニレンオロチ": "Twin Orochi",
    "新光装脚": "Pristine Footwear", "新光兜槍": "Pristine Helmet Partizan",
    "ローズセイバー": "Rose Saber", "アモーレローズ": "Amore Rose",
    "ヤスミノコフ３０００Ｒ": "Yasminkov 3000R", "ヤスミノコフ８０００Ｃ": "Yasminkov 8000C",
    "Ｔヤスミノコフ２０００Ｈ": "Twin Yasminkov 2000H", "ヤスミノコフ４０００Ｆ": "Yasminkov 4000F",
    "ヤスミノコフ７０００Ｖ": "Yasminkov 7000V", "ヤスミノコフ５０００ＳＤ": "Yasminkov 5000SD",
    "イブリスブラッド": "Iblis Blood", "ブレードスタビライザー-NT": "Blade Stabilizer-NT",
    "レイデュプル": "Ray Duplex", "アネット＆ブルーノ": "Annette & Bruno",
    "子供たち": "Children", "アネット&ジェネ": "Annette & Gene",
    "屋台の店員": "Food Stand Attendant", "屋台の店員Ａ": "Food Stand Attendant A",
    "屋台の店員Ｂ": "Food Stand Attendant B", "イベント客": "Event Customer",
    "イベント客Ａ": "Event Customer A", "イベント客Ｂ": "Event Customer B",
    "セイガーブレード": "Seiga Blade", "タルナーダ": "Tarnada",
    "ファイティングビート": "Fighting Beat", "ファルコフリント": "Falco Flint",
    "フレイムビジット": "Flame Visit", "エリュシオーヌ": "Ely-Sion",
    "バルディッシュ": "Bardiche", "ヒャッカリョウラン": "Hyakka Ryouran",
    "エルデトロス": "Eldetross", "クオツリトス": "Quotz Lithos",
    "レイボウ": "Ray Bow", "剣影": "Kenei",
    "テイトウツヅミ": "Teitou Tsuzumi", "アキシオン": "Axeon",
    "記録音声・Ra-C-0017": "Recording: Ra-C-0017", "記録音声・Hu-H-0028": "Recording: Hu-H-0028",
    "カジューシース": "Caduceus", "ホワイトディナー": "White Dinner",
    "スケイスズミ": "Sukei Suzumi", "ヒュージカッター": "Huge Cutter",
    "フォルニスフィジス": "Fornis Physis", "ジス": "Sis",
    "フィジ": "Phys", "フィジ＆ジス": "Phys & Sis",
    "血槍ヴラド・ブラム": "Bloodspear Vlad Bram", "スペース・ツナ": "Space Tuna",
    "中トロ号": "Mr. Fishy", "スペースツナ": "Space Tuna",
    "ユニオンＤブレード": "Union Dual Blade", "ユニオンＤブレード&モア": "Union Dual Blade & More",
    "Ｈ１０ミズーリＴ": "H10 Missouri", "雷咬タガミコウガ": "Thunder Bite Tagamikouga",
    "スチームナックル": "Steam Knuckle", "バレットクナイ": "Bullet Kunai",
    "デュアルバード": "Dual Bird", "スカル様": "Lord Skull",
    "清掃業者": "Janitor", "作業員": "Operator",
    "スカルダイショウグン": "The Great Skull Shogun", "獅子咬": "Shishigami",
    "テスト": "", "全員": "Everyone",
    "モア＆ブルーノ": "More & Bruno", "新光燈砲": "Pristine Lamp Launcher",
    "館内放送": "PA Announcer", "ヤスミノコフ７０００V": "Yasminkov 7000V",
    "ホーリーレイ": "Holy Ray", "グッバイファイア": "Goodbye Fire",
    "フリーズ・ツナ": "Freeze Tuna", "ソリッドストレート": "Solid Straight",
    "フウガナギナタ": "Fuuga Naginata", "ハイパーレインボー": "Hyper Rainbow",
    "イミディエイトフェザー": "Immediate Feather", "アステユニコン": "Aste Unicorn",
    "エルキュリア": "Elcuria", "プリメラ・フィオーレ": "Primera Fiore",
    "インヴェイドガラン": "Invade Galland", "エルダーペイン": "Elder Pain",
    "神杖アマテラス": "Divine Amaterasu", "ゼッシュウ": "Zeshuu",
    "神撃ライコウ": "Divine Raikou", "フロウレイザー": "Flow Razor",
    "オプトレイオン": "Optreion", "フォルニスオジェンド": "Fornis Ogend",
    "対アンドロイドライフル": "Anti Android Rifle", "オフスティアガラン": "Austere Galland",
    "ヤスミノコフチーム": "Yasminkov Team", "ワルキューレＲ２５": "Valkyrie R25",
    "ノクスシャリオ": "Nox Chario", "パオホウオウ": "Pao Houou",
    "フローズンシューター": "Frozen Shooter", "サイカ・ヒョウリ": "Saika Hyouri",
    "イグニス": "Ignis", "チュロスタ": "Churroster",
    "カラミティ＆シュトラ": "Calamity & Stra", "リュロ": "Ryuro",
    "ジェネ＆シューティングドライブ": "Gene & Shooting Drive", "": "",
    "ファニーブーケライフル＆アネット": "Funny Bouquet Rifle & Annette",
    "アフタル＆ジェネ": "Akhtar & Gene", "スウィートキャンディ": "Sweet Candy",
    "たまたま近くにいた男性アークス": "Passerby ARKS",
    "もっとたまたま近くにいた女性アークス": "Passing Female ARKS",
    "水着三人娘": "Annette, Gene and Bluesy", "カラミテイ": "Calamity", #Seasonal scenes
    "ジェネ＆アネット＆シューティングドライブ": "Gene, Annette and Shooting Drive",
    "ヴェルドバズ": "Vert Buzz", "アフタル＆ジェネ＆アネット": "Akhtar, Gene & Annette",
    "Tヤスミノコフ２０００Ｈ": "Twin Yasminkov 2000H", "サンタソ・レー": "Santa Sleigh",
    "サンタ包囲網作戦メンバー": "Operation: Catch Santa Members", "サンタクロース": "Santa Claus",
    "神杖ツクヨミ": "Divine Tsukuyomi", "アリスティン": "Aristin",
    "禍杖ノチウハウ": "Evil Nochiuhau", "ドリームマスター": "Dream Master",
    "華天狼": "Katen Rou", "カザミノタチ": "Kazami-no-tachi",
    "グランディア": "Grandia", "シェルオプス": "Shell Opus",
    "ジェネ＆仲間たち": "Gene & Friends",
    "ナレーション": "Narration", "？？？": "???" #Generics
    }

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
