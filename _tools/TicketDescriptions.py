#!/usr/bin/env python3
# coding=utf8
import codecs
import json
import os
import regex
import shutil

json_loc = os.path.join("..", "json")

REDO_ALL = False # Change to True to recheck all ticket descriptions, even ones already translated.

file_names = [["Accessory", "accessory"], ["BodyPaint", "body paint"],
              ["Eye", "eyes"], ["EyeBrow", "eyebrows"],
              ["EyeLash", "eyelashes"], ["FacePaint", "makeup"],
              ["Hairstyle", "hairstyle"], ["Sticker", "sticker"]]


for name in file_names:
    items_file_name = "Item_Stack_" + name[0] + ".txt"
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
    
    for item in items:
        if item["tr_text"] != "" and (item["tr_explain"] == "" or REDO_ALL == True):
            
            item_name = item["tr_text"]
            
            # Some stickers have different names in-game from their tickets.
            # The in-game name is in the tickets' descriptions.
            # Extract it here.
            if name[0] == "Sticker":
                description_name = regex.search(
                    r'(?<=ステッカーの\n)(.+[ＡＢＣ]?)(?=が選択可能。)',
                    item["jp_explain"]).group(0)

                if (description_name != item["jp_text"]):
                    item_name = regex.sub(" Sticker", "", item_name)
            
            # Some items are locked to one sex or the other.
            sex = "n"
            if len(regex.findall("女性のみ使用可能。", item["jp_explain"])) > 0:
                sex = "f"
            elif len(regex.findall("男性のみ使用可能。", item["jp_explain"])) > 0:
                sex = "m"
            
            # Some items cannot be resized.
            sizelocked = False
            
            if len(regex.findall("サイズ調整はできません。", item["jp_explain"])) > 0:
                sizelocked = True
            
            # Translate the description.
            item["tr_explain"] = "Unlocks the {sexlock}{type}\n\"{name}\"\nfor use in the Beauty Salon.{sizelock}".format(
                sexlock = "female-only " if sex == "f" else "male-only " if sex == "m" else "", 
                type = item_type, name = item_name, 
                sizelock = "\n<yellow>Size cannot be adjusted.<c>" if sizelocked == True else "")

            print("Translated description for {0}".format(item["tr_text"]))

    items_file = codecs.open(os.path.join(json_loc, items_file_name),
                             mode = 'w', encoding = 'utf-8')
    json.dump(items, items_file, ensure_ascii=False, indent="\t", sort_keys=False)
    items_file.write("\n")
    items_file.close()
    
layered_file_names = [["Basewear_Female", "basewear"],
                      ["Basewear_Male", "basewear"],
                      ["Innerwear_Female", "innerwear"],
                      ["Innerwear_Male", "innerwear"]]
        
for name in layered_file_names:
    items_file_name = "Item_" + name[0] + ".txt"
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
    
    for item in items:
        if item["tr_text"] != "" and (item["tr_explain"] == "" or REDO_ALL == True):
            
            # Some items are locked to one sex or the other.
            sex = "n"
            if len(regex.findall("女性のみ使用可能。", item["jp_explain"])) > 0:
                sex = "f"
            elif len(regex.findall("男性のみ使用可能。", item["jp_explain"])) > 0:
                sex = "m"
            
            # Some items hide your innerwear (these are mostly swimsuits).
            hideinner = False
            if len(regex.findall("着用時はインナーが非表示になります。", item["jp_explain"])) > 0:
                hideinner = True
            
            # Translate the description.
            item["tr_explain"] = "Unlocks the new {type}\n\"{name}\".{sexlock}{hidepanties}".format(
                type = item_type, name = item["tr_text"],
                sexlock = "\nOnly usable on female characters." if sex == "f"else "\nOnly usable on male characters." if sex == "m" else "",
                hidepanties = "\n<yellow>※Hides innerwear when worn.<c>" if hideinner == True else "")

            print("Translated description for {0}".format(item["tr_text"]))

    items_file = codecs.open(os.path.join(json_loc, items_file_name),
                             mode = 'w', encoding = 'utf-8')
    json.dump(items, items_file, ensure_ascii=False, indent="\t", sort_keys=False)
    items_file.write("\n")
    items_file.close()

try:
    items_file = codecs.open(os.path.join(json_loc, "Item_Stack_Voice.txt"),
                             mode = 'r', encoding = 'utf-8')
except FileNotFoundError:
    print("\tItem_Stack_Voice.txt not found.")

items = json.load(items_file)
print("Item_Stack_Voice.txt loaded.")
    
items_file.close()

cv_names = {
    "こおろぎさとみ": "Satomi Korogi", "チョー": "Cho",
    "下野 紘": "Hiro Shimono", "中原 麻衣": "Mai Nakahara",
    "中尾 隆聖": "Ryusei Nakao", "中村 悠一": "Yuichi Nakamura",
    "中田 譲治": "Joji Nakata", "中西 茂樹": "Shigeki Nakanishi",
    "久野 美咲": "Misaki Kuno", "井上 和彦": "Kazuhiko Inoue",
    "井上 喜久子": "Kikuko Inoue", "井上 麻里奈": "Marina Inoue",
    "井口 裕香": "Yuka Iguchi", "今井 麻美": "Asami Imai",
    "伊瀬 茉莉也": "Mariya Ise", "伊藤 静": "Shizuka Ito",
    "会 一太郎": "Ichitaro Ai", "住友 優子": "Yuko Sumitomo",
    "佐倉 綾音": "Ayane Sakura", "佐藤 利奈": "Rina Sato",
    "佐藤 聡美": "Satomi Sato", "佳村 はるか": "Haruka Yoshimura",
    "保志 総一朗": "Soichiro Hoshi", "光吉 猛修": "Takenobu Mitsuyoshi",
    "内田 真礼": "Maaya Uchida", "吉野 裕行": "Hiroyuki Yoshino",
    "名塚 佳織": "Kaori Nazuka", "喜多村 英梨": "Eri Kitamura",
    "坂本 真綾": "Maaya Sakamoto", "堀江 由衣": "Yui Horie",
    "子安 武人": "Takehito Koyasu", "寺島 拓篤": "Takuma Terashima",
    "小倉 唯": "Yui Ogura", "小原 莉子": "Riko Kohara",
    "小山 茉美": "Mami Koyama", "小林 ゆう": "Yu Kobayashi",
    "小清水 亜美": "Ami Koshimizu", "小西 克幸": "Katsuyuki Konishi",
    "小野 大輔": "Daisuke Ono", "小野坂 昌也": "Masaya Onosaka",
    "山岡 ゆり": "Yuri Yamaoka", "岡本 信彦": "Nobuhiko Okamoto",
    "岩下 読男": "Moai Iwashita", "島本 須美": "Sumi Shimamoto",
    "島﨑 信長": "Nobunaga Shimazaki", "川村 万梨阿": "Maria Kawamura",
    "川澄 綾子": "Ayako Kawasumi", "市来 光弘": "Mitsuhiro Ichiki",
    "悠木 碧": "Aoi Yuki", "戸松 遥": "Haruka Tomatsu",
    "斉藤 朱夏": "Shuka Saito", "斎藤 千和": "Chiwa Saito",
    "新田 恵海": "Emi Nitta", "日笠 陽子": "Yoko Hikasa",
    "早見 沙織": "Saori Hayami", "木村 珠莉": "Juri Kimura",
    "木村 良平": "Ryohei Kimura", "杉田 智和": "Tomokazu Sugita",
    "村川 梨衣": "Rie Murakawa", "東山 奈央 ": "Nao Toyama",
    "松岡 禎丞": "Yoshitsugu Matsuoka", "柿原 徹也": "Tetsuya Kakihara",
    "桃井 はるこ": "Haruko Momoi", "桑島 法子": "Houko Kuwashima",
    "梶 裕貴": "Yuki Kaji", "森久保 祥太郎": "Showtaro Morikubo",
    "植田 佳奈": "Kana Ueda", "榊原 良子": "Yoshiko Sakakibara",
    "榎本 温子": "Atsuko Enomoto", "横山 智佐": "Chisa Yokoyama",
    "橘田 いずみ": "Izumi Kitta", "櫻井 孝宏": "Takahiro Sakurai",
    "水樹 奈々": "Nana Mizuki", "水橋 かおり": "Kaori Mizuhashi",
    "江口 拓也": "Takuya Eguchi", "沢城 みゆき": "Miyuki Sawashiro",
    "沼倉 愛美": "Manami Numakura", "洲崎 綾": "Aya Suzaki",
    "渡辺 久美子": "Kumiko Watanabe", "潘 めぐみ": "Megumi Han",
    "瀬戸 麻沙美": "Asami Seto", "玄田 哲章": "Tessho Genda",
    "生天目 仁美": "Hitomi Nabatame", "田中 理恵": "Rie Tanaka",
    "田村 ゆかり": "Yukari Tamura", "甲斐田 裕子": "Yuko Kaida",
    "白石 涼子": "Ryoko Shiraishi", "白鳥 哲": "Tetsu Shiratori",
    "皆口 裕子": "Yuko Minaguchi", "石田 彰": "Akira Ishida",
    "神原 大地": "Daichi Kanbara", "神谷 浩史": "Hiroshi Kamiya",
    "福山 潤": "Jun Fukuyama", "秋元 羊介": "Yosuke Akimoto",
    "秦 佐和子": "Sawako Hata", "種田 梨沙": "Risa Taneda",
    "立木 文彦": "Fumihiko Tachiki", "立花 理香": "Rika Tachibana",
    "竹達 彩奈": "Ayana Taketatsu", "細谷 佳正": "Yoshimasa Hosoya",
    "結月 ゆかり": "Yuzuki Yukari", "緑川 光": "Hikaru Midorikawa",
    "緒方 恵美": "Megumi Ogata", "能登 麻美子": "Mamiko Noto",
    "花江 夏樹": "Natsuki Hanae", "花澤 香菜": "Kana Hanazawa",
    "若本 規夫": "Norio Wakamoto", "茅野 愛衣": "Ai Kayano",
    "草尾 毅": "Takeshi Kusao", "菊地 美香": "Mika Kikuchi",
    "蒼井 翔太": "Shouta Aoi", "諏訪 彩花": "Ayaka Suwa",
    "諏訪部 順一": "Junichi Suwabe", "豊口 めぐみ": "Megumi Toyoguchi",
    "豊崎 愛生": "Aki Toyosaki", "近藤 佳奈子": "Kanako Kondo",
    "速水 奨": "Sho Hayami", "那須 晃行": "Akiyuki Nasu",
    "金元 寿子": "Hisako Kanemoto", "釘宮 理恵": "Rie Kugimiya",
    "鈴村 健一": "Kenichi Suzumura", "銀河 万丈": "Banjo Ginga",
    "長谷川 唯": "Yui Hasegawa", "門脇 舞以": "Mai Kadowaki",
    "関 智一": "Tomokazu Seki", "阿澄 佳奈": "Kana Asumi",
    "陶山 章央": "Akio Suyama", "雨宮 天": "Sora Amamiya",
    "飛田 展男": "Nobuo Tobita", "飯田 友子": "Yuko Iida",
    "高木 友梨香": "Yurika Takagi", "高野 麻里佳": "Marika Kono",
    "安元 洋貴": "Hiroki Yasumoto", "高橋 未奈美": "Minami Takahashi",
    "黒沢 ともよ": "Tomoyo Kurosawa", "堀川 りょう": "Ryo Horikawa",
    "高橋 李依": "Rie Takahashi", "安済 知佳": "Chika Anzai",
    "金田 アキ": "Aki Kanada", "田辺 留依": "Rui Tanabe",
    "引坂 理絵": "Rie Hikisaka", "増田 俊樹": "Toshiki Masuda",
    "斉藤 壮馬": "Soma Saito", "藤田 茜": "Akane Fujita",
    "小松 未可子": "Mikako Komatsu", "本渡 楓": "Kaede Hondo",
    "ポポナ": "Popona", "清水 彩香": "Ayaka Shimizu",
    "藤本 結衣": "Yui Fujimoto", "古賀 葵": "Aoi Koga",
    "矢島 晶子": "Akiko Yajima", "藤田 曜子": "Yoko Fujita",
    "天野 名雪": "Nayuki Amano", "佐藤 友啓": "Tomohiro Sato",
    "千本木 彩花": "Sayaka Senbongi", "ゆかな": "Yukana Nogami",
    "佐武 宇綺": "Uki Satake", "紲星 あかり": "Kizuna Akari",
    "？？？": "???", "Ｍ・Ａ・Ｏ": "M・A・O",
    "": "Unknown"
    }

for item in items:
    if item["tr_text"] != "" and (item["tr_explain"] == "" or REDO_ALL == True
                                  # Check for generic wrong format descriptions that keep creeping in somehow.
                                  or len(regex.findall("Salon", item["tr_explain"])) > 0):
        
        # Strings for race/sex combo restrictions
        restrictions = {
        "hm": "Non-Cast male characters only.",
        "hf": "Non-Cast female characters only.",
        "cm": "Male Casts only.",
        "cf": "Female Casts only.",
        "am": "Male characters only (all races).",
        "af": "Female characters only (all races).",
        "an": "Usable by all characters."}
        
        # Detect ticket's race/sex restriction.
        # Default to no restriction.
        racensex= "an"
        
        if len(regex.findall("人間男性のみ使用可能。", item["jp_explain"])) > 0:
            racensex= "hm"
        elif len(regex.findall("人間女性のみ使用可能。", item["jp_explain"])) > 0:
            racensex= "hf"
        elif len(regex.findall("キャスト男性のみ使用可能。", item["jp_explain"])) > 0:
            racensex= "cm"
        elif len(regex.findall("キャスト女性のみ使用可能。", item["jp_explain"])) > 0:
            racensex= "cf"
        elif len(regex.findall("男性のみ使用可能。", item["jp_explain"])) > 0:
            racensex= "am"
        elif len(regex.findall("女性のみ使用可能。", item["jp_explain"])) > 0:
            racensex= "af"
        
        # Find out if we know the voice actor's name in English.
        jp_cv_name = item["jp_explain"].split("ＣＶ")[1]
        
        cv_name = jp_cv_name
        
        if jp_cv_name in cv_names:
            # We do, so use it.
            cv_name = cv_names[jp_cv_name]
        else:
            # We don't, so report it.
            print("Voice ticket {0} has a new voice actor: {1}"
                  .format(item["tr_text"], jp_cv_name))
        
        # Translate the description
        item["tr_explain"] = "Allows a new voice to be selected.\n{restriction}\nCV: {actorname}".format(
            restriction = restrictions[racensex], actorname = cv_name)
        
        print("Translated description for {0}".format(item["tr_text"]))

items_file = codecs.open(os.path.join(json_loc, "Item_Stack_Voice.txt"),
                         mode = 'w', encoding = 'utf-8')
json.dump(items, items_file, ensure_ascii=False, indent="\t", sort_keys=False)
items_file.write("\n")
items_file.close()
