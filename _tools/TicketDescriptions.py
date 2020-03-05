#!/usr/bin/env python3
# coding=utf8
import codecs
import json
import os
import regex
import shutil

json_loc = os.path.join("..", "json")

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
        if item["tr_text"] != "" and item["tr_explain"] == "":
            item["tr_explain"] = "Unlocks the "
            
            if len(regex.findall("女性のみ使用可能。", item["jp_explain"])) > 0:
                item["tr_explain"] += "female-only "
            elif len(regex.findall("男性のみ使用可能。", item["jp_explain"])) > 0:
                item["tr_explain"] += "male-only "

            #Some stickers have different names in-game from their tickets.
            #The in-game name is in the tickets' descriptions.
            #Extract it here.
            cosmetic_name = item["tr_text"]
            if name[1] == "sticker":
                description_name = regex.search(
                    r'(?<=ステッカーの\n)(.+[ＡＢＣ]?)(?=が選択可能。)',
                    item["jp_explain"]).group(0)

                if (description_name != item["jp_text"]):
                    cosmetic_name = regex.sub(" Sticker", "", cosmetic_name)
            
            item["tr_explain"] += (item_type + "\n\""
                                   + cosmetic_name + "\"\n"
                                   + "for use in the Beauty Salon.")

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
        if item["tr_text"] != "" and item["tr_explain"] == "":
            item["tr_explain"] = "Unlocks the new " + item_type + "\n\"" + item["tr_text"] + "\"."
            
            if len(regex.findall("女性のみ使用可能。", item["jp_explain"])) > 0:
                item["tr_explain"] += "\nOnly usable on female characters."
            elif len(regex.findall("男性のみ使用可能。", item["jp_explain"])) > 0:
                item["tr_explain"] += "\nOnly usable on male characters."

            if len(regex.findall("着用時はインナーが非表示になります。", item["jp_explain"])) > 0:
                item["tr_explain"] += '\n<yellow>※Hides innerwear when worn.<c>'

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
    "ポポナ": "Popona",
    "？？？": "???", "Ｍ・Ａ・Ｏ": "M・A・O"
    }

for item in items:
    if (item["tr_text"] != ""
    and (len(regex.findall("Salon", item["tr_explain"])) > 0
         or item["tr_explain"] == "")):
        item["tr_explain"] = "Allows a new voice to be selected.\n"
    
        if len(regex.findall("人間男性のみ使用可能。", item["jp_explain"])) > 0:
            item["tr_explain"] += "Non-Cast male characters only."
        elif len(regex.findall("人間女性のみ使用可能。", item["jp_explain"])) > 0:
            item["tr_explain"] += "Non-Cast female characters only."
        elif len(regex.findall("キャスト男性のみ使用可能。", item["jp_explain"])) > 0:
            item["tr_explain"] += "Male Casts only."
        elif len(regex.findall("キャスト女性のみ使用可能。", item["jp_explain"])) > 0:
            item["tr_explain"] += "Female Casts only."
        elif len(regex.findall("男性のみ使用可能。", item["jp_explain"])) > 0:
            item["tr_explain"] += "Male characters only (all races)."
        elif len(regex.findall("女性のみ使用可能。", item["jp_explain"])) > 0:
            item["tr_explain"] += "Female characters only (all races)."
        else:
            item["tr_explain"] += "Usable by all characters."

        jp_cv_name = item["jp_explain"].split("ＣＶ")[1]
        if jp_cv_name in cv_names:
            tr_cv_name = cv_names[jp_cv_name]
            item["tr_explain"] += "\nCV: " + tr_cv_name
            print("Translated description for {0}".format(item["tr_text"]))
        else:
            item["tr_explain"] += "\nCV:" + jp_cv_name
            print("Voice ticket {0} has a new voice actor: {1}"
                  .format(item["tr_text"], jp_cv_name))

items_file = codecs.open(os.path.join(json_loc, "Item_Stack_Voice.txt"),
                         mode = 'w', encoding = 'utf-8')
json.dump(items, items_file, ensure_ascii=False, indent="\t", sort_keys=False)
items_file.write("\n")
items_file.close()
