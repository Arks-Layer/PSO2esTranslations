#!/usr/bin/env python3
# coding=utf8
import codecs
import json
import os
import regex
import shutil
import argparse

json_loc = os.path.join("..", "json")

parser = argparse.ArgumentParser(description = "Translates ticket item descriptions.")
# Switch for language.
LANGS = {-1: "JP",
         0: "EN",
         1: "KR"}
# Add more later.
parser.add_argument("-l", type = int, dest = "lang", action = "store",
                    choices = [0, 1], default = 0, metavar = "N",
                    help = "Set a language to translate into. Available options are 0 (EN) and 1 (KR). Defaults to EN.")
# Switch for retranslating all descriptions.
parser.add_argument("-r", dest = "redo", action = "store_true",
                    help = "Force all ticket descriptions to be processed, even if already translated.")

args = parser.parse_args()
LANG, REDO_ALL = args.lang, args.redo

# Translate layered wear

layered_wear_types = {"In": ["innerwear", "이너웨어"],
                      "Ba": ["basewear", "베이스웨어"],
                      "Se": ["setwear", "setwear_KR"],
                      "Fu": ["full setwear", "fullwear_KR"],
                      "Ou": ["outerwear", "outerwear_KR"]} # This one probably won't be used, but you never know.

layer_desc_formats = ["Unlocks the new {itype}\n\"{iname}\".", # Must include itype and iname variables.
                      "사용하면 새로운 {itype}인\n\"{iname}\"\n의 사용이 가능해진다."]

layer_sex_locks = {"n": ["", ""],
                   "m": ["\nOnly usable on male characters.",
                         " 남성만 가능."],
                   "f": ["\nOnly usable on female characters.",
                         " 여성만 가능."]}

nlayer_desc_formats = ["Unlocks a new {itype} for use.\n<yellow>※Type: {typelock}<c>"]

ntype_locks = {"a": ["All", ""],
                "a1": ["Type 1"],
                "a2": ["Type 2"],
                "h1": ["Human Type 1"],
                "h2": ["Human Type 2"],
                "c1": ["Cast Type 1"],
                "c2": ["Cast Type 2"]}

layer_hide_inners = ["※Hides innerwear when worn.",
                     "※착용 시 이너웨어는 표시하지 않음."]

def translate_layer_desc(item, file_name):
    if item["tr_text"] == "": # No name to put in description
        return -1
    
    elif item["tr_explain"] != "" and REDO_ALL == False: # Description already present, leave it alone
        return -2

    # Some items are locked to one sex or the other.
    sex = "n"
    if "女性のみ使用可能。" in item["jp_explain"]:
        sex = "f"
    elif "男性のみ使用可能。" in item["jp_explain"]:
        sex = "m"
    
    # Some items hide your innerwear (these are mostly swimsuits).
    hideinner = False
    if "着用時はインナーが非表示になります。" in item["jp_explain"]:
        hideinner = True
    
    # Translate the description.
    item["tr_explain"] = (layer_desc_formats[LANG] + "{sexlock}{hidepanties}").format(
        itype = layered_wear_types[item["tr_text"].split("[", )[1][0:2]][LANG] if item["tr_text"].endswith("]")
                # Exception for default layered wear since it doesn't have [In], [Ba] etc
                else layered_wear_types[file_name.split("_")[0][0:2]][LANG],
        iname = item["tr_text"],
        sexlock = layer_sex_locks[sex][LANG] if sex != "n" else "",
        hidepanties = "\n<yellow>" + layer_hide_inners[LANG] + "<c>" if hideinner == True else "")
    
    return 0

def translate_nlayer_desc(item, file_name):
    if item["tr_text"] == "": # No name to put in description
        return -1
    
    elif item["tr_explain"] != "" and REDO_ALL == False: # Description already present, leave it alone
        return -2
    
    # Some items are locked to one race and/or type.
    types = "a"
    if "：ヒト" in item["jp_explain"]:
        types = "h"
    elif "：キャスト" in item["jp_explain"]:
        types = "c"
        
    if "タイプ1<c>" in item["jp_explain"]:
        types += "1"
    elif "タイプ2<c>" in item["jp_explain"]:
        types += "2"

    # Some items hide your innerwear (these are mostly swimsuits).
    hideinner = False
    if "着用時はインナーが非表示になります。" in item["jp_explain"]:
        hideinner = True

    # Translate the description.
    item["tr_explain"] = (nlayer_desc_formats[LANG] + "{hidepanties}").format(
        itype = layered_wear_types[item["tr_text"].split("[", )[1][0:2]][LANG] if item["tr_text"].endswith("]")
                # Exception for default layered wear since it doesn't have [In], [Ba] etc
                else layered_wear_types[file_name.split("_")[0][0:2]][LANG],
        typelock = ntype_locks[types][LANG],
        hidepanties = "\n<yellow>" + layer_hide_inners[LANG] + "<c>" if hideinner == True else "")
    
    return 0

layered_file_names = ["Basewear_Female",
                      "Basewear_Male",
                      "Innerwear_Female",
                      "Innerwear_Male"]

for name in layered_file_names:
    items_file_name = "Item_" + name + ".txt"
    
    try:
        items_file = codecs.open(os.path.join(json_loc, items_file_name),
                                 mode = 'r', encoding = 'utf-8')
    except FileNotFoundError:
        print("\t{0} not found.".format(items_file_name))
        continue
    
    items = json.load(items_file)
    print("{0} loaded.".format(items_file_name) + " {")
    
    items_file.close()

    newtranslations = False
    
    for item in items:
        problem = translate_nlayer_desc(item, name) if "選択可能になる。" in item["jp_explain"] else translate_layer_desc(item, name)

        if problem == 0:
            print("\tTranslated description for {0}".format(item["tr_text"]))
            newtranslations = True

    if newtranslations == False:
        print("\tNo new translations.")
    
    print("}")
    
    items_file = codecs.open(os.path.join(json_loc, items_file_name),
                             mode = 'w', encoding = 'utf-8')
    json.dump(items, items_file, ensure_ascii=False, indent="\t", sort_keys=False)
    items_file.write("\n")
    items_file.close()

# Translate other cosmetics

cosmetic_file_names = [
    "Accessory", "BodyPaint",
    "Eye", "EyeBrow",
    "EyeLash", "FacePaint",
    "Hairstyle", "Sticker"
    ]

cosmetic_types = {
    "Accessory": ["accessory", "악세서리"],
    "BodyPaint": ["body paint", "바디 페인트"],
    "Eye": ["eyes", "눈동자"],
    "EyeBrow": ["eyebrows", "눈썹"],
    "EyeLash": ["eyelashes", "속눈썹"],
    "FacePaint": ["makeup", "메이크업"],
    "Hairstyle": ["hairstyle", "헤어스타일"],
    "Sticker": ["sticker", "스티커"]
    }

cosmetic_desc_formats = ["Unlocks the {sexlock}{itype}\n\"{iname}\"\nfor use in the Beauty Salon.",
                         "사용하면 새로운 {sexlock}{itype}\n\"{iname}\"\n의 사용이 가능해진다."]

cosmetic_sex_locks = {"m": ["male-only ", "남성 전용 "],
                      "f": ["female-only ", "여성 전용 "]}

cosmetic_size_locks = ["Size cannot be adjusted.",
                       "size_locked_KR"]

no_sticker_desc = ["Unlocks the ability to not display a\nsticker in the Beauty Salon.",
                   "no_sticker_KR"]

def translate_cosmetic_desc(item, file_name):
    if item["tr_text"] == "": # No name to put in description
        return -1
    
    elif item["tr_explain"] != "" and REDO_ALL == False: # Description already present, leave it alone
        return -2
    
    elif item["jp_text"] == "ステッカーなし": # Exception for "no sticker" sticker
        item["tr_explain"] = no_sticker_desc[LANG]
        return 0
        
    item_name = item["tr_text"]
    
    # Some stickers have different names in-game from their tickets.
    # The in-game name is in the tickets' descriptions.
    # Extract it here.
    if file_name == "Sticker":
        description_name = regex.search(
            r'(?<=ステッカーの\n)(.+[ＡＢＣ]?)(?=が選択可能。)',
            item["jp_explain"]).group(0)

        if (description_name != item["jp_text"]):
            item_name = item_name.replace(" Sticker", "")
    
    # Some items are locked to one sex or the other.
    sex = "n"
    if "女性のみ使用可能。" in item["jp_explain"]:
        sex = "f"
    elif "男性のみ使用可能。" in item["jp_explain"]:
        sex = "m"
    
    # Some items cannot be resized.
    sizelocked = False
    
    if "サイズ調整はできません。" in item["jp_explain"]:
        sizelocked = True
    
    # Translate the description.
    item["tr_explain"] = (cosmetic_desc_formats[LANG] + "{sizelock}").format(
        sexlock = cosmetic_sex_locks[sex][LANG] if sex != "n" else "",
        itype = item_type,
        iname = item_name, 
        sizelock = "\n<yellow>" + cosmetic_size_locks[LANG] + "<c>" if sizelocked == True else "")
    
    # Hello Kitty item copyright notice
    if item["jp_text"] == "ハローキティチェーン":
        item["tr_explain"] += "\nc'76,'15 SANRIO APPR.NO.S564996"
    
    return 0

for file_name in cosmetic_file_names:
    items_file_name = "Item_Stack_" + file_name + ".txt"
    item_type = cosmetic_types[file_name][LANG]
    
    try:
        items_file = codecs.open(os.path.join(json_loc, items_file_name),
                                 mode = 'r', encoding = 'utf-8')
    except FileNotFoundError:
        print("\t{0} not found.".format(items_file_name))
        continue
    
    items = json.load(items_file)
    print("{0} loaded.".format(items_file_name) + " {")
    
    items_file.close()

    newtranslations = False
    
    for item in items:
        if translate_cosmetic_desc(item, file_name) == 0:
            print("\tTranslated description for {0}".format(item["tr_text"]))
            newtranslations = True

    if newtranslations == False:
        print("\tNo new translations.")
    
    print("}")

    items_file = codecs.open(os.path.join(json_loc, items_file_name),
                             mode = 'w', encoding = 'utf-8')
    json.dump(items, items_file, ensure_ascii=False, indent="\t", sort_keys=False)
    items_file.write("\n")
    items_file.close()

# Translate voices

try:
    items_file = codecs.open(os.path.join(json_loc, "Item_Stack_Voice.txt"),
                             mode = 'r', encoding = 'utf-8')
except FileNotFoundError:
    print("\tItem_Stack_Voice.txt not found.")

items = json.load(items_file)
print("Item_Stack_Voice.txt loaded. {")
    
items_file.close()

cv_names = {
    "ゆかな": ["Yukana Nogami", ""],
    "チョー": ["Cho", "쵸"],
    "ポポナ": ["Popona", ""],
    "下野 紘": ["Hiro Shimono", "시모노 히로"],
    "中原 麻衣": ["Mai Nakahara", "나카하라 마이"],
    "中尾 隆聖": ["Ryusei Nakao", "나카오 류세이"],
    "中村 悠一": ["Yuichi Nakamura", "유이치 나카무라"],
    "中田 譲治": ["Joji Nakata", "나카타 조지"],
    "中西 茂樹": ["Shigeki Nakanishi", ""],
    "久野 美咲": ["Misaki Kuno", ""],
    "井上 和彦": ["Kazuhiko Inoue", ""],
    "井上 喜久子": ["Kikuko Inoue", ""],
    "井上 麻里奈": ["Marina Inoue", ""],
    "井口 裕香": ["Yuka Iguchi", ""],
    "今井 麻美": ["Asami Imai", ""],
    "伊瀬 茉莉也": ["Mariya Ise", ""],
    "伊藤 静": ["Shizuka Ito", ""],
    "会 一太郎": ["Ichitaro Ai", ""],
    "住友 優子": ["Yuko Sumitomo", ""],
    "佐倉 綾音": ["Ayane Sakura", ""],
    "佐武 宇綺": ["Uki Satake", ""],
    "佐藤 利奈": ["Rina Sato", ""],
    "佐藤 友啓": ["Tomohiro Sato", ""],
    "佐藤 聡美": ["Satomi Sato", ""],
    "佳村 はるか": ["Haruka Yoshimura", ""],
    "保志 総一朗": ["Soichiro Hoshi", ""],
    "光吉 猛修": ["Takenobu Mitsuyoshi", ""],
    "内田 真礼": ["Maaya Uchida", ""],
    "千本木 彩花": ["Sayaka Senbongi", ""],
    "古賀 葵": ["Aoi Koga", ""],
    "吉野 裕行": ["Hiroyuki Yoshino", ""],
    "名塚 佳織": ["Kaori Nazuka", ""],
    "喜多村 英梨": ["Eri Kitamura", ""],
    "坂本 真綾": ["Maaya Sakamoto", ""],
    "堀川 りょう": ["Ryo Horikawa", ""],
    "堀江 由衣": ["Yui Horie", ""],
    "増田 俊樹": ["Toshiki Masuda", ""],
    "天野 名雪": ["Nayuki Amano", ""],
    "子安 武人": ["Takehito Koyasu", ""],
    "安元 洋貴": ["Hiroki Yasumoto", ""],
    "安済 知佳": ["Chika Anzai", ""],
    "寺島 拓篤": ["Takuma Terashima", ""],
    "小倉 唯": ["Yui Ogura", ""],
    "小原 莉子": ["Riko Kohara", ""],
    "小山 茉美": ["Mami Koyama", ""],
    "小松 未可子": ["Mikako Komatsu", ""],
    "小林 ゆう": ["Yu Kobayashi", ""],
    "小清水 亜美": ["Ami Koshimizu", ""],
    "小西 克幸": ["Katsuyuki Konishi", ""],
    "小野 大輔": ["Daisuke Ono", ""],
    "小野坂 昌也": ["Masaya Onosaka", ""],
    "山岡 ゆり": ["Yuri Yamaoka", ""],
    "岡本 信彦": ["Nobuhiko Okamoto", ""],
    "岩下 読男": ["Moai Iwashita", ""],
    "島本 須美": ["Sumi Shimamoto", ""],
    "島﨑 信長": ["Nobunaga Shimazaki", ""],
    "川村 万梨阿": ["Maria Kawamura", ""],
    "川澄 綾子": ["Ayako Kawasumi", ""],
    "市来 光弘": ["Mitsuhiro Ichiki", ""],
    "引坂 理絵": ["Rie Hikisaka", ""],
    "悠木 碧": ["Aoi Yuki", ""],
    "戸松 遥": ["Haruka Tomatsu", "토마츠 하루카"],
    "斉藤 壮馬": ["Soma Saito", ""],
    "斉藤 朱夏": ["Shuka Saito", ""],
    "斎藤 千和": ["Chiwa Saito", "사이토 치와"],
    "新田 恵海": ["Emi Nitta", ""],
    "日笠 陽子": ["Yoko Hikasa", ""],
    "早見 沙織": ["Saori Hayami", ""],
    "木村 珠莉": ["Juri Kimura", ""],
    "木村 良平": ["Ryohei Kimura", ""],
    "本渡 楓": ["Kaede Hondo", ""],
    "杉田 智和": ["Tomokazu Sugita", ""],
    "村川 梨衣": ["Rie Murakawa", ""],
    "東山 奈央 ": ["Nao Toyama", "토야마 나오"],
    "松岡 禎丞": ["Yoshitsugu Matsuoka", "마츠오카 요시츠구"],
    "柿原 徹也": ["Tetsuya Kakihara", "카키하라 테츠야"],
    "桃井 はるこ": ["Haruko Momoi", ""],
    "桑島 法子": ["Houko Kuwashima", ""],
    "梶 裕貴": ["Yuki Kaji", ""],
    "森久保 祥太郎": ["Showtaro Morikubo", ""],
    "植田 佳奈": ["Kana Ueda", ""],
    "榊原 良子": ["Yoshiko Sakakibara", ""],
    "榎本 温子": ["Atsuko Enomoto", ""],
    "横山 智佐": ["Chisa Yokoyama", ""],
    "橘田 いずみ": ["Izumi Kitta", ""],
    "櫻井 孝宏": ["Takahiro Sakurai", ""],
    "水樹 奈々": ["Nana Mizuki", ""],
    "水橋 かおり": ["Kaori Mizuhashi", ""],
    "江口 拓也": ["Takuya Eguchi", ""],
    "沢城 みゆき": ["Miyuki Sawashiro", ""],
    "沼倉 愛美": ["Manami Numakura", ""],
    "洲崎 綾": ["Aya Suzaki", ""],
    "清水 彩香": ["Ayaka Shimizu", ""],
    "渡辺 久美子": ["Kumiko Watanabe", ""],
    "潘 めぐみ": ["Megumi Han", ""],
    "瀬戸 麻沙美": ["Asami Seto", ""],
    "玄田 哲章": ["Tessho Genda", ""],
    "生天目 仁美": ["Hitomi Nabatame", ""],
    "田中 理恵": ["Rie Tanaka", ""],
    "田村 ゆかり": ["Yukari Tamura", ""],
    "田辺 留依": ["Rui Tanabe", "타나베 루이"],
    "甲斐田 裕子": ["Yuko Kaida", ""],
    "白石 涼子": ["Ryoko Shiraishi", ""],
    "白鳥 哲": ["Tetsu Shiratori", ""],
    "皆口 裕子": ["Yuko Minaguchi", "미나구치 유코"],
    "矢島 晶子": ["Akiko Yajima", ""],
    "石田 彰": ["Akira Ishida", ""],
    "神原 大地": ["Daichi Kanbara", ""],
    "神谷 浩史": ["Hiroshi Kamiya", ""],
    "福山 潤": ["Jun Fukuyama", ""],
    "秋元 羊介": ["Yosuke Akimoto", ""],
    "秦 佐和子": ["Sawako Hata", ""],
    "種田 梨沙": ["Risa Taneda", "타네다 리사"],
    "立木 文彦": ["Fumihiko Tachiki", "타치키 후미히코"],
    "立花 理香": ["Rika Tachibana", ""],
    "竹達 彩奈": ["Ayana Taketatsu", ""],
    "細谷 佳正": ["Yoshimasa Hosoya", ""],
    "紲星 あかり": ["Kizuna Akari", ""],
    "結月 ゆかり": ["Yuzuki Yukari", ""],
    "緑川 光": ["Hikaru Midorikawa", ""],
    "緒方 恵美": ["Megumi Ogata", ""],
    "能登 麻美子": ["Mamiko Noto", ""],
    "花江 夏樹": ["Natsuki Hanae", ""],
    "花澤 香菜": ["Kana Hanazawa", ""],
    "若本 規夫": ["Norio Wakamoto", ""],
    "茅野 愛衣": ["Ai Kayano", ""],
    "草尾 毅": ["Takeshi Kusao", ""],
    "菊地 美香": ["Mika Kikuchi", ""],
    "蒼井 翔太": ["Shouta Aoi", ""],
    "藤本 結衣": ["Yui Fujimoto", ""],
    "藤田 曜子": ["Yoko Fujita", ""],
    "藤田 茜": ["Akane Fujita", ""],
    "諏訪 彩花": ["Ayaka Suwa", ""],
    "諏訪部 順一": ["Junichi Suwabe", ""],
    "豊口 めぐみ": ["Megumi Toyoguchi", ""],
    "豊崎 愛生": ["Aki Toyosaki", ""],
    "近藤 佳奈子": ["Kanako Kondo", ""],
    "速水 奨": ["Sho Hayami", ""],
    "那須 晃行": ["Akiyuki Nasu", ""],
    "金元 寿子": ["Hisako Kanemoto", ""],
    "金田 アキ": ["Aki Kanada", ""],
    "釘宮 理恵": ["Rie Kugimiya", ""],
    "鈴村 健一": ["Kenichi Suzumura", "스즈무라 켄이치"],
    "銀河 万丈": ["Banjo Ginga", ""],
    "長谷川 唯": ["Yui Hasegawa", ""],
    "門脇 舞以": ["Mai Kadowaki", ""],
    "関 智一": ["Tomokazu Seki", ""],
    "阿澄 佳奈": ["Kana Asumi", ""],
    "陶山 章央": ["Akio Suyama", ""],
    "雨宮 天": ["Sora Amamiya", ""],
    "飛田 展男": ["Nobuo Tobita", ""],
    "飯田 友子": ["Yuko Iida", "이이다 유우코"],
    "高木 友梨香": ["Yurika Takagi", ""],
    "高橋 未奈美": ["Minami Takahashi", ""],
    "高橋 李依": ["Rie Takahashi", ""],
    "高野 麻里佳": ["Marika Kono", ""],
    "黒沢 ともよ": ["Tomoyo Kurosawa", ""],
    "こおろぎさとみ": ["Satomi Korogi", "코오로기 사토미"],
    "三宅 健太": ["Kenta Miyake", ""],
    "諸星 すみれ": ["Sumire Morohoshi", ""],
    "Ｍ・Ａ・Ｏ": ["M・A・O", "M・A・O"],
    "？？？": ["???", "???"],
    "": ["Unknown", "알 수 없는"]
    }

# What language to fall back to if a name hasn't been translated into your language.
# -1: Prefer falling back to JP over any other language
name_fallbacks = {0: -1,
                  1: -1}

voice_desc_formats = ["Allows a new voice to be selected.",
                      "사용하면 새로운 보이스 사용 가능."]

def translate_voice(item):
    if item["tr_text"] == "": # No name to put in description
        return -1
    
    elif (item["tr_explain"] != "" and REDO_ALL == False # Description already present, leave it alone
    and "Salon" not in item["tr_explain"]): # Catch old format descriptions that keep creeping in somehow.
        return -2
    else:
        # Strings for race/sex combo restrictions
        restrictions = {
        "hm": ["Non-Cast male characters only.",
               "인간 남성만 사용 가능."],
        "hf": ["Non-Cast female characters only.",
               "인간 여성만 사용 가능."],
        "cm": ["Male Casts only.",
               "캐스트 남성만 사용 가능."],
        "cf": ["Female Casts only.",
               "캐스트 여성만 사용 가능."],
        "am": ["Male characters only (all races).",
               "남성만 사용 가능."],
        "af": ["Female characters only (all races).",
               "여성만 사용 가능."],
        "an": ["Usable by all characters.",
               "모두 사용 가능."]}
        
        # Detect ticket's race/sex restriction.
        # Default to no restriction.
        racensex= "an"
        
        if "人間男性のみ使用可能。" in item["jp_explain"]:
            racensex= "hm"
        elif "人間女性のみ使用可能。" in item["jp_explain"]:
            racensex= "hf"
        elif "キャスト男性のみ使用可能。" in item["jp_explain"]:
            racensex= "cm"
        elif "キャスト女性のみ使用可能。" in item["jp_explain"]:
            racensex= "cf"
        elif "男性のみ使用可能。" in item["jp_explain"]:
            racensex= "am"
        elif "女性のみ使用可能。" in item["jp_explain"]:
            racensex= "af"
        
        # Find out if we know the voice actor's name
        jp_cv_name = item["jp_explain"].split("ＣＶ")[1]
        
        if jp_cv_name in cv_names: # We do, so use it, or keep falling back to best available option if we don't have a translation.
            cv_name = ""
            curr_lang = LANG
            
            while cv_name == "":
                if curr_lang == -1: # We've fallen back to JP, so just use the JP name and stop there
                    cv_name = jp_cv_name
                    break
                else:
                    cv_name = cv_names[jp_cv_name][curr_lang]
                    if cv_name == "":
                        print("\tWARNING: No translation for {jp} in {curr}, falling back to {next}".format(jp = jp_cv_name, curr = LANGS[curr_lang], next = LANGS[name_fallbacks[curr_lang]]))
                    curr_lang = name_fallbacks[curr_lang]
            
        else:
            # We don't, so report it.
            print("Voice ticket {0} has a new voice actor: {1}"
                  .format(item["tr_text"], jp_cv_name))
        
        # Translate the description
        item["tr_explain"] = voice_desc_formats[LANG] + "\n{restriction}\nCV: {actorname}".format(
            restriction = restrictions[racensex][LANG],
            actorname = cv_name)
        
    return 0

for item in items:
    
    if translate_voice(item) == 0:
        print("\tTranslated description for {0}".format(item["tr_text"]))
        newtranslations = True

if newtranslations == False:
    print("\tNo new translations.")

print("}")       

items_file = codecs.open(os.path.join(json_loc, "Item_Stack_Voice.txt"),
                         mode = 'w', encoding = 'utf-8')
json.dump(items, items_file, ensure_ascii=False, indent="\t", sort_keys=False)
items_file.write("\n")
items_file.close()

print ("Ticket translation complete.")
