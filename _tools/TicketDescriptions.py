#!/usr/bin/env python3
# coding=utf8
import codecs
import json
import os
import regex
import argparse

json_loc = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "json")

parser = argparse.ArgumentParser(
    description = "Translates ticket item descriptions.")

#Switch for description on untranslated names
parser.add_argument("-a", dest = "all", action = "store_true",
                    help = ("Translate descriptions even for items "
                            "with no translated names."))

# Switch for language.
LANGS = {-1: "JP",
         0: "EN",
         1: "KO",
         2: "RU",
         3: "CN"}
# Add more later.
parser.add_argument("-l", type = int, dest = "lang", action = "store",
                    choices = [0, 1, 2, 3], default = 3, metavar = "N",
                    help = ("Set a language to translate into. "
                            "Available options are 0 (EN), 1 (KO), 2 (RU) and 3 (CN). "
                            "Defaults to EN."))

# Switch for retranslating all descriptions.
parser.add_argument("-r", dest = "redo", action = "store_true",
                    help = ("Force all ticket descriptions to be processed, "
                            "even if already translated. "
                            "Always on for CN."))

args = parser.parse_args()
TRANS_ALL, LANG, REDO_ALL = args.all, args.lang, args.redo

# Always retranslate all descriptions for CN.
if LANG == 3:
    REDO_ALL = True

# Full width character transtable
chartable = [
    "".maketrans("０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ　＝－＋／．＆（）：！",
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz =-+/.&():!"),

    "".maketrans("０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ　＝－＋／．＆（）：！",
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz =-+/.&():!"),

    "".maketrans("０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ　＝－＋／．＆（）：！",
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz =-+/.&():!"),

    "".maketrans("",
    "")]

# Split the name ("<green>“...”<c>\n") added by TicketGenerateFromGamefile from the description
def split_name_prefix(item):
    name_prefix = regex.match(r'<green>“[^\n]*”<c>\n', item["tr_explain"])
    name_prefix = name_prefix.group(0) if name_prefix else ""
    item["tr_explain"] = item["tr_explain"][len(name_prefix):]
    return name_prefix

# For CN, copy the JP name into any empty tr_text
def fill_cn_name(item):
    if LANG == 3 and item["tr_text"] == "":
        item["tr_text"] = item["jp_text"]

# For CN, put the name back as it was if the item still has no description
def unfill_cn_name(item, tr_text):
    if LANG == 3 and item["tr_explain"] == "":
        item["tr_text"] = tr_text

# The translated name of an item: the translated name first, then the name in the green prefix.
# Returns None if the name isn't translated.
def get_item_name(item, name_prefix):
    if item["tr_text"] != "" and item["tr_text"] != item["jp_text"]:
        return item["tr_text"]

    prefix_name = regex.match(r"<green>“(.+)”<c>\n", name_prefix)
    if prefix_name:
        return prefix_name.group(1)

    return None

####################################################################################################

# Translate layered wear

layered_file_names = ["Basewear_Female",
                      "Basewear_Male",
                      "Innerwear_Female",
                      "Innerwear_Male",
                      "Stack_OuterWearF",
                      "Stack_OuterWearM"]

layered_wear_types = {"In": ["innerwear", "이너웨어", "внутреннюю одежду (In)", "內衣"],
                      "Ba": ["basewear", "베이스웨어", "верхнюю одежду (Ba)", "底衣"],
                      "Se": ["setwear", "세트 웨어", "комплектную одежду (Se)", "套服"],
                      "Fu": ["full setwear", "풀세트 웨어", "полн.компл.одежду (Fu)", "全身套服"],
                      "Ou": ["outerwear", "아우터 웨어", "внешнюю одежду (Ou)", "外套"],
                      "To": ["totalwear", "", "", "完整裝扮"]}

# Old layered wear format. Must include itype and iname variables.
# JP text: 
    # 使用すると、新しい{itype}の\n
    # {iname}が選択可能。
layer_desc_formats = [("Unlocks the new {itype}\n"
                       "\"{iname}\"."),
                      ("사용하면 새로운 {itype}인\n"
                       "\"{iname}\"\n"
                       "의 사용이 가능해진다."),
                      ("Разблокирует новую\n"
                       "{itype}\n"
                       "\"{iname}\"."),
                      ("使用後，可選用新的{itype}\n"
                       "{iname}。")]

# JP text unavailable.
layer_sex_locks = {"n": ["", "", "", ""],
                   "m": ["\nOnly usable on male characters.",
                         " 남성만 가능.",
                         "\nТолько для мужских персонажей.",
                         "\n僅限男性使用。"],
                   "f": ["\nOnly usable on female characters.",
                         " 여성만 가능.",
                         "\nТолько для женских персонажей.",
                         "\n僅限女性使用。"]}

# New cosmetics format. Must include itype variable.
# JP text: 
    # 使用すると新しい{itype}が\n
    # 選択可能になる。
ndesc_n_formats = ["Unlocks {a}new {itype} for use.",
                 "사용하면 새로운 {itype}\n선택이 가능해집니다.",
                 "Разблок {itype}.",
                 "使用後可選用新的{itype}。"]

# JP text: 
    # 使用すると新しい{itype}が\n
    # 全キャラクターで選択可能になる。
ndesc_allcharacters_formats = ["A {itype} that unlocks for all\ncharacters on your account.",
                 "사용하면 새로운 {itype} 아이템을\n모든 캐릭터에 선택할 수 있게 됩니다.",
                 "{itype}, разблок. для\nвсех персонажей аккаунта.",
                 "使用後所有角色均可選用新的{itype}。"]

# JP text: 
    # 使用すると新しい{itype}パターンが\n
    # 選択可能になる。
ndesc_pattern_formats = ["Unlocks {a}new {itype} for use.",
                 "사용하면 새로운 {itype}\n선택이 가능해집니다.",
                 "Разблок {itype}.",
                 "使用後可選用新的{itype}種類。"]

# JP text: 対応：
ntype_statements = ["Type: ",
                    "대응: ",
                    "Тип: ",
                    "適用於："]

# JP text:
    # ヒト型
    # キャスト
    # ヒト型/キャスト
    # タイプ1
    # タイプ2<c>
# No longer used.
ntype_locks = {"a": ["All", "KO_All", "Все", "CN_All"],
                "a1": ["Human/Cast Type 1", "인간형/캐스트타입1", "Человек/CAST (тип1)", "人類/機人類型1"],
                "a2": ["Human/Cast Type 2", "인간형/캐스트타입2", "Человек/CAST (тип2)", "人類/機人類型2"],
                "h1": ["Human Type 1", "인간형 타입1", "Человек (тип1)", "人類類型1"],
                "h2": ["Human Type 2", "인간형 타입2", "Человек (тип2)", "人類類型2"],
                "c1": ["Cast Type 1", "캐스트 타입1", "CAST (тип1)", "機人類型1"],
                "c2": ["Cast Type 2", "캐스트 타입2", "CAST (тип2)", "機人類型2"]}

# JP text:
    # ※着用時はインナーが非表示になります。
# No longer used.
layer_hide_inners = ["※Hides innerwear when worn.",
                     "※착용 시 이너웨어는 표시하지 않음.",
                     "※При экипировке скрывает In.",
                     "※穿著時不會顯示內衣。"]

# JP text:
    # ※一部[In]カラー同期
# No longer used.
layer_sync_inners = ["※Synchronizes with [In] color.",
                     "※일부 [In]컬러 동기화",
                     "※Цвета некоторых [In] синхр-ся.",
                     "※與一部分[In]同步顏色"]

# JP text: 
    # ※アクセサリー表示非対応
layer_hide_accessories = ["※Hides accessories when worn.",
                          "※악세서리 표시 불가",
                          "※Скрывает аксессуары.",
                          "※不適用於飾品的顯示"]

# JP text: 
    # ※カラー変更非対応
ncosmetic_color_locks = ["※Color cannot be changed",
                        "※컬러 변경 불가",
                        "※Цвет нельзя изменить",
                        "※不適用於顏色的變更"]

# JP text: 
    # ※『PSO2』ブロック非対応
ngs_locks = ["※Not available in [PSO2] Blocks.",
             "※『PSO2』블록 비대응",
             "※Нельзя использовать в блоке PSO2",
             "※不適用於『PSO2』"]

# JP text:
    # 武器装備反映／\n
    # 『PSO2』ブロック非対応
weapon_ngs_locks = ["※Shows equipped weapons.\n"
                    "Not available in [PSO2] Blocks.",
                    "※지원 기능: 무기 장비 반영\n"
                    "『PSO2』블록 비대응",
                    "※Показывает экип-е оружие.\n"
                    "Нельзя использовать в блоке PSO2",
                    "※適用功能：顯示裝備武器\n"
                    "不適用於『PSO2』"
                    ]

# JP text: 
    # ※一部の顔、ヘッドパーツ非対応
ngsface_locks = ["※Not compatible with some heads/faces.",
                 "",
                 "※",
                 "※不適用於部分面部、頭部部件"]

# JP text: 
    # ※『PSO2』ではLv.100以上の\n
    # 　マグにのみ使用可能
mag_device_lv100 = [("※Must be used in PSO2 on a Mag\n"
                     "which has reached Lv.100 or above."),
                    ("※『PSO2』에선 Lv.100이상의\n"
                    "마그에서만 사용 가능"),
                    ("※Только на MAG'e PSO2\n"
                    "достигшем 100ур.+"),
                    ("※在『PSO2』中僅可對\n"
                    "　Lv.100或以上的瑪古使用")]

# JP text: 
    # ※『NGS』でのみ使用可能
mag_device_ngs = ["※Only usable in NGS.",
                  "※『NGS』에서만 사용 가능",
                  "※Только для NGS.",
                  "※僅可在『NGS』中使用"]

# JP text: 
    # ※武器の構え位置自動調整
weapon_posture = [("※Uses adjusted weapon positions."),
                  (""),
                  ("※Исп. скоррект. положение."),
                  ("※自動調整武器架勢的位置")]

# JP text:
    # アイテムラボの“強化素材交換”で\n
    # 特定のカプセルとの交換にも用いられる。
capsule_exchange = [("Can also be exchanged for specific\n"
                     "capsules at the Item Lab."),
                    (""),
                    (""),
                    ("也可在道具實驗室的“交換強化素材”處\n"
                     "用於交換特定的膠囊。")]

# JP text:
    # ★７以上のEX特殊能力は１つのみ追加可能
capsule_ex_limit = [("Only 1 EX Special Ability of\n"
                     "7★ or above can be added"),
                    (""),
                    (""),
                    ("僅可追加1個★7或以上的EX特殊能力")]

def translate_layer_desc(item, file_name, name_prefix):
    item_name = ""

    # Decide what name we're working with
    if TRANS_ALL:
        item_name = item["tr_text"] or item["jp_text"]
    else:
        if item["tr_text"] == "":
            # No translated name so skip this one (except CN)
            if LANG != 3:
                return -1
            # No translated name so copy the JP name (for CN)
            else:
                item["tr_text"] = item["jp_text"]
                item_name = item["tr_text"]
        else:
            item_name = item["tr_text"]

    # Tradable items keep the JP name in CN, their translated name is in the green prefix
    item_name = get_item_name(item, name_prefix) or item_name
    
    # Description already present, leave it alone
    if REDO_ALL == False and item["tr_explain"] != "":
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
        itype = layered_wear_types[item_name[-3:-1]][LANG] if item_name.endswith("]")
                # Exception for defaults since they don't have [In], [Ba] etc
                else layered_wear_types[file_name.split("_")[0][0:2]][LANG],
        iname = item_name,
        sexlock = layer_sex_locks[sex][LANG] if sex != "n" else "",
        hidepanties = "\n<yellow>" + layer_hide_inners[LANG] + "<c>" if hideinner == True else "")

    item["tr_explain"] = item["tr_explain"].translate(chartable[LANG])
    
    return 0

def get_type_restrictions(item):
    types = "a"

    if "：ヒト型" in item["jp_explain"] and "/キャスト" not in item["jp_explain"]:
        types = "h"
    elif "：キャスト" in item["jp_explain"]:
        types = "c"
        
    if "タイプ1<c>" in item["jp_explain"]:
        types += "1"
    elif "タイプ2<c>" in item["jp_explain"]:
        types += "2"
    
    return types

def translate_nlayer_desc(item, file_name, name_prefix):
    item_name = ""

    # Decide what name we're working with
    if TRANS_ALL:
        item_name = item["tr_text"] or item["jp_text"]
    else:
        if item["tr_text"] == "":
            # No translated name so skip this one (except CN)
            if LANG != 3:
                return -1
            # No translated name so copy the JP name (for CN)
            else:
                item["tr_text"] = item["jp_text"]
                item_name = item["tr_text"]
        else:
            item_name = item["tr_text"]

    # Tradable items keep the JP name in CN, their translated name is in the green prefix
    item_name = get_item_name(item, name_prefix) or item_name

    # Description already present, leave it alone
    if REDO_ALL == False and item["tr_explain"] != "":
        return -2

    # Some basewears partially synchronise their colour with your innerwear
    syncinner = False
    if "一部[In]カラー同期" in item["jp_explain"]:
        syncinner = True
        
    # Some items are locked to one race and/or type.
    types = get_type_restrictions(item)

    # Some items hide your innerwear (these are mostly swimsuits).
    hideinner = False
    if "着用時はインナーが非表示になります。" in item["jp_explain"]:
        hideinner = True

    # Some setwears are incompatible with accessories.
    hideaccess = False
    if "アクセサリー表示非対応" in item["jp_explain"]:
        hideaccess = True

    # Some ngs items cannot be recolored.
    ncolorlocked = False
    if "カラー変更非対応" in item["jp_explain"]:
        ncolorlocked = True

    # Translate the description.
    item["tr_explain"] = (ndesc_n_formats[LANG] + "{syncpanties}" + "{typelock}" + "{hidepanties}" + "{noaccessories}" + "{ncolorlock}").format(
        itype = layered_wear_types[item_name[-3:-1]][LANG] if item_name.endswith("]")
                # Exception for default layered wear since it doesn't have [In], [Ba] etc
                else layered_wear_types[file_name.split("_")[0][0:2]][LANG],
        # Ugly hack
        a = "a ",
        syncpanties = "\n<yellow>" + layer_sync_inners[LANG] + "<c>" if syncinner == True else "",
        typelock = "" if types == "a" else "\n<yellow>※{0}{1}<c>".format(ntype_statements[LANG], ntype_locks[types][LANG]),
        hidepanties = "\n<yellow>" + layer_hide_inners[LANG] + "<c>" if hideinner == True else "",
        noaccessories = "\n<yellow>" + layer_hide_accessories[LANG] + "<c>" if hideaccess == True else "",
        ncolorlock = "\n<yellow>" + ncosmetic_color_locks[LANG] + "<c>" if ncolorlocked == True else "")

    item["tr_explain"] = item["tr_explain"].translate(chartable[LANG])
    
    return 0

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
        tr_text = item["tr_text"]
        fill_cn_name(item)
        name_prefix = split_name_prefix(item)
        problem = translate_nlayer_desc(item, name, name_prefix) if "選択可能になる。" in item["jp_explain"] else translate_layer_desc(item, name, name_prefix)
        item["tr_explain"] = name_prefix + item["tr_explain"]
        unfill_cn_name(item, tr_text)

        if problem == 0:
            print("\tTranslated description for {0}".format(item["tr_text"] or item["jp_text"]))
            newtranslations = True

    if newtranslations == False:
        print("\tNo new translations.")
    
    print("}")
    
    items_file = codecs.open(os.path.join(json_loc, items_file_name),
                             mode = 'w', encoding = 'utf-8')
    json.dump(items, items_file, ensure_ascii=False, indent="\t", sort_keys=False)
    items_file.write("\n")
    items_file.close()

####################################################################################################

# Translate other cosmetics

cosmetic_file_names = [
    "Stack_Accessory",
    "Stack_Arkscard_BG",
    "Stack_BodyPaint",
    "Stack_CS_Effect",
    "Stack_CS_Room_Goods",
    "Stack_CS_Stickers",
    "Stack_Duel_Card_Play_Mat",
    "Stack_Duel_Card_Sleeve",
    "Stack_Duel_Card_Ticket",
    "Stack_Ear",
    "Stack_Eye",
    "Stack_EyeBrow",
    "Stack_EyeLash",
    "Stack_FacePaint",
    "Stack_Hairstyle",
    "Stack_Horn",
    "Stack_MotionChange",
    "Stack_Stamp",
    "Stack_Sticker",
    "Stack_Tooth",
    "Stack_Vital_Gauge"
    ]

cosmetic_types = {
    "Stack_Accessory": ["accessory", "악세서리", "аксессуар", "飾品"],
    "Stack_Arkscard_BG": ["background for your ARKS\nCard", "", "", "\nARKS名片背景"],
    "Stack_BodyPaint": ["body paint", "바디 페인트", "рис. тела", "身體彩繪"],
    "Stack_CS_Effect": ["Portable Hologram", "", "", "\n便攜全息投影"],
    "Stack_CS_Room_Goods": ["Portable Hologram", "", "", "\n便攜全息投影"],
    "Stack_CS_Stickers": ["Portable Hologram", "", "", "\n便攜全息投影"],
    "Stack_Duel_Card_Play_Mat": ["playmat", "", "", "牌桌墊"],
    "Stack_Duel_Card_Sleeve": ["card sleeve", "", "", "牌套"],
    "Stack_Duel_Card_Ticket": ["card", "", "", "卡牌"],
    "Stack_Ear": ["ear shape", "귀", "форма ушей", "耳朵"],
    "Stack_Eye": ["eye pattern", "눈동자", "глаза", "瞳孔"],
    "Stack_EyeBrow": ["eyebrow type", "눈썹", "брови", "眉毛"],
    "Stack_EyeLash": ["eyelash type", "속눈썹", "ресницы", "睫毛"],
    "Stack_FacePaint": ["makeup", "메이크업", "макияж", "妝容"],
    "Stack_Hairstyle": ["hairstyle", "헤어스타일", "причёску", "髪型"],
    "Stack_Horn": ["horn type", "뿔", "тип рога", "角"],
    "Stack_MotionChange": ["motion", "모션", "движение", "行動方式"],
    "Stack_Stamp": ["stamp", "스탬프", "штамп", "表情圖"],
    "Stack_Sticker": ["sticker", "스티커", "стикер", "貼紙"],
    "Stack_Tooth": ["teeth and tongue\nset", "치아/혀", "зубы и язык", "牙齒、舌頭"],
    "Stack_Vital_Gauge": ["Vital Gauge BG", "", "", "\n體征槽背景"]
    }

# JP text: 
    # 使用すると、新しい{itype}の\n
    # {iname}が選択可能。
# {sexlock} unavailable.
cosmetic_desc_use_new_formats = [("Unlocks the {sexlock}{itype}\n"
                          "\"{iname}\"\n"
                          "for use in the Beauty Salon."),
                         ("사용하면 새로운 {sexlock}{itype}\n"
                          "\"{iname}\"\n"
                          "의 사용이 가능해진다."),
                         ("Разблок-т {itype} {sexlock}\n"
                          "\"{iname}\"\n"
                          "для использования в салоне."),
                         ("使用後，可選用新的{sexlock}{itype}\n"
                          "{iname}。")]

# JP text: 
    # チケットを使用すると、{itype}\n
    # {iname}が選択可能。
# {sexlock} unavailable.
cosmetic_desc_ticket_formats = [("Unlocks the {sexlock}{itype}\n"
                          "\"{iname}\"\n"
                          "for use in the Beauty Salon."),
                         ("사용하면 새로운 {sexlock}{itype}\n"
                          "\"{iname}\"\n"
                          "의 사용이 가능해진다."),
                         ("Разблок-т {itype} {sexlock}\n"
                          "\"{iname}\"\n"
                          "для использования в салоне."),
                         ("使用票券後，可選用{sexlock}{itype}\n"
                          "{iname}。")]

# JP text: 
    # チケットを使用すると、新しい{itype}の\n
    # {iname}が選択可能。
# {sexlock} unavailable.
cosmetic_desc_ticket_new_formats = [("Unlocks the {sexlock}{itype}\n"
                          "\"{iname}\"\n"
                          "for use in the Beauty Salon."),
                         ("사용하면 새로운 {sexlock}{itype}\n"
                          "\"{iname}\"\n"
                          "의 사용이 가능해진다."),
                         ("Разблок-т {itype} {sexlock}\n"
                          "\"{iname}\"\n"
                          "для использования в салоне."),
                         ("使用票券後，可選用新的{sexlock}{itype}\n"
                          "{iname}。")]

# JP text: 
    # 特定ステッカーの装着許可チケット。\n
    # 使用すると、新しい{itype}の\n
    # {iname}が選択可能。
# {sexlock} unavailable.
cosmetic_desc_sticker_use_new_formats = [("Unlocks the {sexlock}{itype}\n"
                          "\"{iname}\"\n"
                          "for use in the Beauty Salon."),
                         ("사용하면 새로운 {sexlock}{itype}\n"
                          "\"{iname}\"\n"
                          "의 사용이 가능해진다."),
                         ("Разблок-т {itype} {sexlock}\n"
                          "\"{iname}\"\n"
                          "для использования в салоне."),
                         ("許可著裝特定貼紙的票券。\n"
                          "使用後，可選用新的{sexlock}{itype}\n"
                          "{iname}。")]

# JP text unavailable.
cosmetic_sex_locks = {"m": ["male-only ", "남성 전용 ", "только для М", "男性專用"],
                      "f": ["female-only ", "여성 전용 ", "только для Ж", "女性專用"]}

# JP text: 
    # ※サイズ調整はできません。
cosmetic_size_locks = ["※Size cannot be adjusted.",
                       "※사이즈 조정은 할 수 없습니다.",
                       "※Нельзя отрегулировать размер.",
                       "※無法調整尺寸。"]

# JP text: 
    # ※カラーは変更できません
cosmetic_color_locks = ["※Color cannot be changed",
                        "※색상은 변경할 수 없습니다",
                        "※Цвет нельзщя изменить.",
                        "※無法變更顏色"]

# JP text: 
    # 特定ステッカーの非表示許可チケット。\n
    # 使用すると、ステッカーの\n非表示が選択可能。
no_sticker_desc = [("Unlocks the ability to not display a\n"
                    "sticker in the Beauty Salon."),
                   ("특정 스티커 숨김 허가 티켓.\n"
                    "사용하면 스티커의\n"
                    "숨김이 선택 가능해집니다."),
                   ("Разблокирует возможность\n"
                    "не отображать стикер в салоне."),
                   ("許可不顯示特定貼紙的票券。\n"
                    "使用後可以選擇不顯示貼紙。")]

# New cosmetic tickets use the formats we defined earlier for new layer wear

def translate_cosmetic_desc(item, file_name, name_prefix):
    item_name = ""

    # Decide what name we're working with
    if TRANS_ALL:
        item_name = item["tr_text"] or item["jp_text"]
    else:
        if item["tr_text"] == "":
            # No translated name so skip this one (except CN)
            if LANG != 3:
                return -1
            # No translated name so copy the JP name (for CN)
            else:
                item["tr_text"] = item["jp_text"]
                item_name = item["tr_text"]
        else:
            item_name = item["tr_text"]

    # Tradable items keep the JP name in CN, their translated name is in the green prefix
    item_name = get_item_name(item, name_prefix) or item_name

    # Description already present, leave it alone
    if REDO_ALL == False and item["tr_explain"] != "":
        return -2

    # Exception for "no sticker" sticker
    elif item["jp_text"] == "ステッカーなし":
        item["tr_explain"] = no_sticker_desc[LANG]
        return 0
    
    # Some stickers have different names in-game from their tickets.
    # The in-game name is in the tickets' descriptions.
    # Extract it here.
    if file_name == "Stack_Sticker":
        description_name = regex.search(
            r'(?<=ステッカーの\n)(.+[ＡＢＣ]?)(?=が選択可能。)',
            item["jp_explain"]).group(0)

        if (description_name != item["jp_text"]):
            item_name = item_name.replace(" Sticker", "")
            item_name = item_name.replace("ステッカー", "")

    # Sort the description format
    desc_sort = "use_new"
    if item["jp_explain"].startswith("チケットを使用すると、新しい"):
        desc_sort = "ticket_new"
    elif item["jp_explain"].startswith("チケットを使用すると、"):
        desc_sort = "ticket"
    elif item["jp_explain"].startswith("特定ステッカーの装着許可チケット。"):
        desc_sort = "sticker_use_new"
    
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

    # Some items cannot be recolored.
    colorlocked = False
    
    if "カラーは変更できません" in item["jp_explain"]:
        colorlocked = True

    # Some ngs items cannot be recolored.
    ncolorlocked = False
    
    if "カラー変更非対応" in item["jp_explain"]:
        ncolorlocked = True
    
    # Combine the variable name.
    desc_format_name = "cosmetic_desc_" + desc_sort + "_formats"

    # Translate the description.
    item["tr_explain"] = (eval(desc_format_name)[LANG] + "{sizelock}" + "{colorlock}" + "{ncolorlock}").format(
        sexlock = cosmetic_sex_locks[sex][LANG] if sex != "n" else "",
        itype = item_type,
        iname = item_name,
        sizelock = "\n<yellow>" + cosmetic_size_locks[LANG] + "<c>" if sizelocked == True else "",
        colorlock = "\n<yellow>" + cosmetic_color_locks[LANG] + "<c>" if colorlocked == True else "",
        ncolorlock = "\n<yellow>" + ncosmetic_color_locks[LANG] + "<c>" if ncolorlocked == True else "")
    
    # Hello Kitty item copyright notice
    if item["jp_text"] == "ハローキティチェーン":
        item["tr_explain"] += "\nc'76,'15 SANRIO APPR.NO.S564996"

    item["tr_explain"] = item["tr_explain"].translate(chartable[LANG])
    
    return 0

def translate_ncosmetic_desc(item, file_name):
    # Name isn't translated and we're not working in CN, skip this one
    if TRANS_ALL == False and item["tr_text"] == "" and LANG != 3:
        return -1

    # Description already present, leave it alone
    if REDO_ALL == False and item["tr_explain"] != "":
        return -2
    
    # Sort the description format
    desc_sort = "n"
    if "全キャラクターで選択可能になる。" in item["jp_explain"]:
        desc_sort = "allcharacters"
    elif "パターンが\n選択可能になる。" in item["jp_explain"]:
        desc_sort = "pattern"

    # Some items are locked to one race and/or type.
    types = get_type_restrictions(item)

    # Some items hide your innerwear (these are mostly swimsuits).
    hideinner = False
    if "着用時はインナーが非表示になります。" in item["jp_explain"]:
        hideinner = True

    # Some items show weapons and can't be used in PSO2 blocks.
    # Others don't but still can't be used in PSO2 blocks.
    ngslockedweapon = False
    ngslocked = False
    if "武器装備反映／\n『PSO2』ブロック非対応" in item["jp_explain"]:
        ngslockedweapon = True
    elif "『PSO2』ブロック非対応" in item["jp_explain"]:
        ngslocked = True
    
    # Some ngs items cannot be used on PSO2 face patterns.
    ngsfacelocked = False
    if "一部の顔、ヘッドパーツ非対応" in item["jp_explain"]:
        ngsfacelocked = True
    
    # Combine the variable name.
    ndesc_format_name = "ndesc_" + desc_sort + "_formats"

    # Translate the description.
    item["tr_explain"] = (eval(ndesc_format_name)[LANG] + "{typelock}" + "{ngslock}" + "{ngsfacelock}").format(
        itype = item_type,
        a = "a ",
        typelock = "" if types == "a" else "\n<yellow>※{0}{1}<c>".format(ntype_statements[LANG], ntype_locks[types][LANG]),
        hidepanties = "\n<yellow>" + layer_hide_inners[LANG] + "<c>" if hideinner == True else "",
        ngslock = "\n<yellow>" + weapon_ngs_locks[LANG] + "<c>" if ngslockedweapon == True else "\n<yellow>" + ngs_locks[LANG] + "<c>" if ngslocked == True else "",
        ngsfacelock = "\n<yellow>" + ngsface_locks[LANG] + "<c>" if ngsfacelocked == True else "")

    item["tr_explain"] = item["tr_explain"].translate(chartable[LANG])
    
    return 0

for file_name in cosmetic_file_names:
    items_file_name = "Item_" + file_name + ".txt"
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
        tr_text = item["tr_text"]
        fill_cn_name(item)
        name_prefix = split_name_prefix(item)
        problem = translate_ncosmetic_desc(item, file_name) if "選択可能になる。" in item["jp_explain"] else translate_cosmetic_desc(item, file_name, name_prefix)
        item["tr_explain"] = name_prefix + item["tr_explain"]
        unfill_cn_name(item, tr_text)

        if problem == 0:
            print("\tTranslated description for {0}".format(item["tr_text"] or item["jp_text"]))
            newtranslations = True

    if newtranslations == False:
        print("\tNo new translations.")
    
    print("}")

    items_file = codecs.open(os.path.join(json_loc, items_file_name),
                             mode = 'w', encoding = 'utf-8')
    json.dump(items, items_file, ensure_ascii=False, indent="\t", sort_keys=False)
    items_file.write("\n")
    items_file.close()

####################################################################################################

# Translate build parts

# JP text: 
    # アクセスすると\n
    # 座れるビルドパーツ。
build_parts_sittable = [("This Build Part can be accessed\n"
                         "to sit on it."),
                        (""),
                        (""),
                        ("交互後\n即可坐下的建造部件。")]
# JP text:
    # アクセスすると\n
    # 座れるビルドパーツだが……。
build_parts_sittable_unwise = [("This Build Part can be accessed\n"
                                "to sit on it, but..."),
                               (""),
                               (""),
                               ("交互後\n即可坐下的建造部件，但……")]
# JP text:
    # アクセスすると\n
    # 横になれるビルドパーツ。
build_parts_layable = [("This Build Part can be accessed\n"
                         "to lie down on it."),
                        (""),
                        (""),
                        ("交互後\n即可躺下的建造部件。")]
# JP text:
    # アクセスすると\n
    # 入浴できるビルドパーツ。
build_parts_bathable = [("This Build Part can be accessed\n"
                         "to take a bath."),
                        (""),
                        (""),
                        ("交互後\n即可入浴的建造部件。")]
# JP text:
    # アクセスすると\n
    # シャワーを浴びられるビルドパーツ。
build_parts_showerable = [("This Build Part can be accessed\n"
                           "to take a shower."),
                          (""),
                          (""),
                          ("交互後\n即可淋浴的建造部件。")]
# JP text:
    # アクセスすると\n
    # 開閉できるビルドパーツ。
build_parts_isadoor = [("This Build Part can be accessed\n"
                        "to open and close it."),
                       (""),
                       (""),
                       ("交互後\n即可開閉的建造部件。")]
# JP text:
    # 攻撃すると\n
    # 破壊できるビルドパーツ。
build_parts_smashable = [("This Build Part can be destroyed\n"
                          "by attacking it."),
                         (""),
                         (""),
                         ("攻擊後\n即可破壞的建造部件。")]
# JP text:
    # アクセスすると\n
    # 獲れるビルドパーツ。
build_parts_grabbable = [("This Build Part can be accessed\n"
                          "to collect it."),
                         (""),
                         (""),
                         ("交互後\n即可捕獲的建造部件。")]
# JP text:
    # 触れると\n
    # 取れるビルドパーツ。
build_parts_collectable = [("This Build Part can be collected by\n"
                            "touching it."),
                           (""),
                           (""),
                           ("觸碰後\n即可拿取的建造部件。")]
# JP text:
    # アクセスすると\n
    # 設定したメッセージを表示する\n
    # ビルドパーツ。
build_parts_messagepack = [("This Build Part can be accessed\n"
                            "to read the message it contains."),
                           (""),
                           (""),
                           ("交互後\n就會顯示設置好的訊息的\n建造部件。")]
# JP text:
    # アクセスすると\n
    # オンオフが切り替わる\n
    # ビルドパーツ。
build_parts_usebutton = [("This Build Part acts as a switch\n"
                          "that toggles on/off when accessed."),
                         (""),
                         (""),
                         ("交互後\n就會切換開關的建造部件。")]
# JP text:
    # 上に乗ると\n
    # スイッチがオンになる\n
    # ビルドパーツ。
build_parts_stepbutton = [("This Build Part acts as a switch\n"
                           "that turns on when stepped on."),
                          (""),
                          (""),
                          ("踩在上面後\n開關就會設為開的建造部件。")]
# JP text:
    # 触れると\n
    # 爆発して吹き飛ばされる\n
    # ビルドパーツ。
build_parts_touchbomb = [("This Build Part explodes on contact,\n"
                          "blasting players away."),
                         (""),
                         (""),
                         ("觸碰後\n就會爆炸把人炸飛的建造部件。")]
# JP text:
    # フォトングライド中に\n
    # 乗ると移動できる\n
    # ビルドパーツ。
build_parts_updrafter = [("This Build Part lets you ascend by\n"
                          "riding it while Photon Gliding."),
                         (""),
                         (""),
                         ("在光子滑翔中乘上後\n即可進行移動的建造部件。")]
# JP text:
    # アクセスすると\n
    # 対応する番号のテレポーターに\n
    # 移動できるビルドパーツ。
build_parts_teleporter = [("This Build Part can be accessed\n"
                           "to teleport to another Teleporter\n"
                           "with a matching ID."),
                          (""),
                          (""),
                          ("交互後\n即可移動到相應號碼傳送器的\n建造部件。")]
# JP text:
    # エリア内に接触すると\n
    # 次のギミックパーツに\n
    # コネクトを送信するビルドパーツ。
build_parts_persondetector = [("When this Build Part detects that a\n"
                               "player has entered its assigned area,\n"
                               "it sends a signal to its connected parts."),
                              (""),
                              (""),
                              ("碰撞到區域內後\n就會向下一個機關部件\n發送智聯信號的建造部件。")]
# JP text:
    # コネクトを受信すると\n
    # タイマーのカウントアップを開始する\n
    # ビルドパーツ。
build_parts_timerup = [("When this Build Part receives a signal,\n"
                        "it starts a timer that counts up from 0."),
                       (""),
                       (""),
                       ("接收智聯信號後\n就會開始計時器正數的建造部件。")]
# JP text:
    # コネクトを受信すると\n
    # タイマーのカウントダウンを開始する\n
    # ビルドパーツ。
build_parts_timerdown = [("When this Build Part receives a signal,\n"
                          "it starts a timer that counts down to 0."),
                         (""),
                         (""),
                         ("接收智聯信號後\n就會開始計時器倒數的建造部件。")]
# JP text:
    # エリア内で指定したアクションを行うと\n
    # 次のギミックパーツに\n
    # コネクトを送信するビルドパーツ。
build_parts_motiondetector = [("When this Build Part detects a specific\n"
                               "player action within its assigned area,\n"
                               "it sends a signal to its connected parts."),
                              (""),
                              (""),
                              ("在區域內執行指定動作後\n就會向下一個機關部件\n發送智聯信號的建造部件。")]
# JP text:
    # コネクトを受信すると\n
    # 設定したテキスト演出を再生する\n
    # ビルドパーツ。
build_parts_displaytext = [("When this Build Part receives a signal,\n"
                            "it displays a set text string."),
                            (""),
                            (""),
                            ("接收智聯信號後\n就會播放設置好的文字演出的\n建造部件。")]
# JP text:
    # コネクトを受信すると\n
    # 設定したサウンドを再生する\n
    # ビルドパーツ。
build_parts_soundbox = [("When this Build Part receives a signal,\n"
                         "it plays a specified sound effect."),
                        (""),
                        (""),
                        ("接收智聯信號後\n就會播放設置好的聲音的\n建造部件。")]
# JP text:
    # 2つのコネクトを受信すると\n
    # 次のギミックパーツに\n
    # コネクトを送信するビルドパーツ。
build_parts_logicalandy = [("When this Build Part receives 2 signals,\n"
                           "it sends a signal to its connected parts."),
                           (""),
                           (""),
                           ("接收2個智聯信號後\n就會向下一個機關部件\n發送智聯信號的建造部件。")]
# JP text:
    # コネクトを受信すると\n
    # カウントを1つ増やす\n
    # ビルドパーツ。
build_parts_countup = [("When this Build Part receives a signal,\n"
                        "it increases its internal counter by 1."),
                       (""),
                       (""),
                       ("接收智聯信號後\n計數就會增加1的建造部件。")]
# JP text:
    # コネクトを受信してから\n
    # 一定時間後に次のギミックパーツに\n
    # コネクトを送信するビルドパーツ。
build_parts_delayer = [("When this Build Part receives a signal,\n"
                        "it waits for a set amount of time, then\n"
                        "sends a signal to its connected parts."),
                       (""),
                       (""),
                       ("接收智聯信號一定時間後\n就會向下一個機關部件\n發送智聯信號的建造部件。")]
# JP text:
    # コネクトを受信すると\n
    # 指定したギミックパーツのいずれかに\n
    # コネクトを送信するビルドパーツ。
build_parts_randomiser = [("When this Build Part receives a signal,\n"
                           "it sends a signal on to one of its\n"
                           "connected parts, chosen at random."),
                          (""),
                          (""),
                          ("接收智聯信號後\n就會向任意的指定機關部件\n發送智聯信號的建造部件。")]
# JP text:
    # アクセスするとアークス拠点に\n
    # 移動できるビルドパーツ。\n
    # Ｃスペース内の初期位置にもなる。
build_parts_startpoint = [("This Build Part can be accessed to\n"
                           "return to the ARKS Base. It is also\n"
                           "where you first arrive in C. Space."),
                          (""),
                          (""),
                          ("交互後即可移動到\nARKS據點的建造部件。\n也會成為創造空間內的初始位置。")]
# JP text:
    # アクセスすると\n
    # 自身のキャラクターを投影する\n
    # ビルドパーツ。
build_parts_mannequin = [("This Build Part can be accessed\n"
                          "to display the image of a character."),
                         (""),
                         (""),
                         ("交互後\n就會投影出自己角色的建造部件。")]
# JP text:
    # 上に乗っているあいだだけ\n
    # スイッチがオンになる\nビルドパーツ。
build_parts_pressureplate = [("This Build Part acts as a switch\n"
                              "that turns on only while stood on."),
                             (""),
                             (""),
                             ("僅在踩在上面的時間裡\n開關會設為開的建造部件。")]
# JP text:
    # アクセスすると\n
    # 設計図の登録、取得ができる\n
    # ビルドパーツ。
build_parts_blueprinter = [("This Build Part can be accessed\n"
                            "to create and download Blueprints."),
                           (""),
                           (""),
                           ("交互後\n即可登錄、獲取設計圖的建造部件。")]
# JP text:
    # アクセスすると\n
    # ジェネシスポイントが獲得できる\n
    # ビルドパーツ。
build_parts_gptree = [("This Build Part can be accessed\n"
                       "to obtain Genesis Points."),
                      (""),
                      (""),
                      ("交互後\n即可獲得創世點數的建造部件。")]
# JP text:
    # くぐると\n
    # 加速するビルドパーツ。
build_parts_dashring = [("This Build Part makes you accelerate\n"
                         "when you pass through it."),
                        (""),
                        (""),
                        ("穿過後\n就會加速的建造部件。")]
# JP text:
    # 触れると\n
    # 大きくジャンプするビルドパーツ。
build_parts_spring = [("This Build Part launches you a great\n"
                       "distance when you touch it."),
                      (""),
                      (""),
                      ("觸碰後\n就會大幅跳躍的建造部件。")]
# JP text:
    # アクセスすると\n
    # Ｃスペースメニューを操作できる\n
    # ビルドパーツ。
build_parts_csterminal = [("This Build Part can be accessed\n"
                           "to open the Creative Space Menu."),
                          (""),
                          (""),
                          ("交互後\n即可操作創造空間菜單的\n建造部件。")]
# JP text:
    # アクセスすると\n
    # チームコマンドを操作できる\n
    # ビルドパーツ。
build_parts_teamterminal = [("This Build Part can be accessed\n"
                             "to open the Team Commands Menu."),
                            (""),
                            (""),
                            ("交互後\n即可操作公會指令的\n建造部件。")]
# JP text:
    # アクセスすると\n
    # チーム掲示板を操作できる\n
    # ビルドパーツ。
build_parts_teambb = [("This Build Part can be accessed\n"
                       "to open the Team Bulletin Board."),
                      (""),
                      (""),
                      ("交互後\n即可操作公會佈告欄的\n建造部件。")]
# JP text:
    # アクセスすると\n
    # チームスペースメニューを操作できる\n
    # ビルドパーツ。
build_parts_tsterminal = [("This Build Part can be accessed\n"
                           "to open the Team Space Menu."),
                          (""),
                          (""),
                          ("交互後\n即可操作公會空間菜單的\n建造部件。")]
# JP text:
    # アクセスしてジェネシスポイントを\n
    # 使用すると、ブーストを発生させられる\n
    # ビルドパーツ。
build_parts_teammag = [("This Build Part can be accessed\n"
                        "to spend Genesis Points to\n"
                        "trigger various boost effects."),
                       (""),
                       (""),
                       ("交互並使用創世點數後\n即可發動各種增益的\n建造部件。")]
# JP text:
    # アクセスすると\n
    # ラインストライクで\n
    # 対戦できるビルドパーツ。
build_parts_linestrike = [("This Build Part can be accessed\n"
                           "to engage in a Line Strike Duel."),
                          (""),
                          (""),
                          ("交互後\n即可在戰線牌鬥中對戰的\n建造部件。")]
# JP text:
    # アクセスすると\n
    # 対応する番号の転移門に\n
    # 移動できるビルドパーツ。
build_parts_transition = [("This Build Part can be accessed\n"
                           "to teleport to another Transition\n"
                           "Gate with a matching ID."),
                          (""),
                          (""),
                          ("交互後\n即可移動到相應號碼傳送門的\n建造部件。")]
# JP text:
    # アクセスすると\n
    # 登録したクリエイティブスペースに\n
    # 移動できるビルドパーツ。
build_parts_cswarp = [("This Build Part can be accessed\n"
                       "to teleport to another specified\n"
                       "Creative Space."),
                      (""),
                      (""),
                      ("交互後\n即可移動到已登錄創造空間的\n建造部件。")]
# JP text:
    # コネクトを受信すると\n
    # クレーンを操作できる\n
    # ビルドパーツ。
build_parts_crane = [("When this Build Part receives a signal,\n"
                      "its crane arm moves around."),
                     (""),
                     (""),
                     ("接收智聯信號後\n即可操作勾爪的建造部件。")]
# JP text:
    # 上から入ると\n
    # 泳げるビルドパーツ。
build_parts_swimmable = [("This Build Part can be swum in\n"
                         "if entered through its top face."),
                        (""),
                        (""),
                         ("從上方進入後\n即可游泳的建造部件。")]

def translate_part_desc(part):
    # Name isn't translated and we're not working in CN, skip this one
    if TRANS_ALL == False and part["tr_text"] == "" and LANG != 3:
        return -1

    # Description already present, leave it alone
    if REDO_ALL == False and part["tr_explain"] != "":
        return -2

    # No description to translate
    if part["jp_explain"] == "":
        return -3

    part_functions = {
        # Some items can be sat on
        "アクセスすると\n座れるビルドパーツ。": "sittable",
        # Some items can be sat on, but shouldn't
        "アクセスすると\n座れるビルドパーツだが……。": "sittable_unwise",
        # Some items can be lain on
        "アクセスすると\n横になれるビルドパーツ。": "layable",
        # Some items are baths
        "アクセスすると\n入浴できるビルドパーツ。": "bathable",
        # Some items are showers
        "アクセスすると\nシャワーを浴びられるビルドパーツ。": "showerable",
        # Some items are doors
        "アクセスすると\n開閉できるビルドパーツ。": "isadoor",
        # Some items can be smashed
        "攻撃すると\n破壊できるビルドパーツ。": "smashable",
        # Some items can be collected by accessing
        "アクセスすると\n獲れるビルドパーツ。": "grabbable",
        # Some items can be collected by touching
        "触れると\n取れるビルドパーツ。": "collectable",
        # Some items are message packs
        "アクセスすると\n設定したメッセージを表示する\nビルドパーツ。": "messagepack",
        # Some items are usable buttons
        "アクセスすると\nオンオフが切り替わる\nビルドパーツ。": "usebutton",
        # Some items are steppable buttons
        "上に乗ると\nスイッチがオンになる\nビルドパーツ。": "stepbutton",
        # Some items are bombs
        "触れると\n爆発して吹き飛ばされる\nビルドパーツ。": "touchbomb",
        # Some items are updrafters
        "フォトングライド中に\n乗ると移動できる\nビルドパーツ。": "updrafter",
        # Some items are teleporters
        "アクセスすると\n対応する番号のテレポーターに\n移動できるビルドパーツ。": "teleporter",
        # Some items detect the player's presence
        "エリア内に接触すると\n次のギミックパーツに\nコネクトを送信するビルドパーツ。": "persondetector",
        # Some items time up
        "コネクトを受信すると\nタイマーのカウントアップを開始する\nビルドパーツ。": "timerup",
        # Some items time down
        "コネクトを受信すると\nタイマーのカウントダウンを開始する\nビルドパーツ。": "timerdown",
        # Some items detect the player's moves
        "エリア内で指定したアクションを行うと\n次のギミックパーツに\nコネクトを送信するビルドパーツ。": "motiondetector",
        # Some items display text
        "コネクトを受信すると\n設定したテキスト演出を再生する\nビルドパーツ。": "displaytext",
        # Some items play sounds
        "コネクトを受信すると\n設定したサウンドを再生する\nビルドパーツ。": "soundbox",
        # Some items wait for two signals
        "2つのコネクトを受信すると\n次のギミックパーツに\nコネクトを送信するビルドパーツ。": "logicalandy",
        # Some items count up
        "コネクトを受信すると\nカウントを1つ増やす\nビルドパーツ。": "countup",
        # Some items delay a signal
        "コネクトを受信してから\n一定時間後に次のギミックパーツに\nコネクトを送信するビルドパーツ。": "delayer",
        # Some items randomise their output
        "コネクトを受信すると\n指定したギミックパーツのいずれかに\nコネクトを送信するビルドパーツ。": "randomiser",
        # Some items are where you arrive
        "アクセスするとアークス拠点に\n移動できるビルドパーツ。\nＣスペース内の初期位置にもなる。": "startpoint",
        # Some items display characters
        "アクセスすると\n自身のキャラクターを投影する\nビルドパーツ。": "mannequin",
        # Some items are pressure plates
        "上に乗っているあいだだけ\nスイッチがオンになる\nビルドパーツ。": "pressureplate",
        # Some items are blueprint makers
        "アクセスすると\n設計図の登録、取得ができる\nビルドパーツ。": "blueprinter",
        # Some items are the GP tree
        "アクセスすると\nジェネシスポイントが獲得できる\nビルドパーツ。": "gptree",
        # Some items gotta go fast
        "くぐると\n加速するビルドパーツ。": "dashring",
        # Some items are springs, from Sonic
        "触れると\n大きくジャンプするビルドパーツ。": "spring",
        # Some items are the CS terminal
        "アクセスすると\nＣスペースメニューを操作できる\nビルドパーツ。": "csterminal",
        # Some items are the Team Command terminal
        "アクセスすると\nチームコマンドを操作できる\nビルドパーツ。": "teamterminal",
        # Some items are the Team BB
        "アクセスすると\nチーム掲示板を操作できる\nビルドパーツ。": "teambb",
        # Some items are the Team Space terminal
        "アクセスすると\nチームスペースメニューを操作できる\nビルドパーツ。": "tsterminal",
        # Some items are the Team Mag
        "アクセスしてジェネシスポイントを\n使用すると、ブーストを発生させられる\nビルドパーツ。": "teammag",
        # Some items let you play cards
        "アクセスすると\nラインストライクで\n対戦できるビルドパーツ。": "linestrike",
        # Some items are also teleporters
        "アクセスすると\n対応する番号の転移門に\n移動できるビルドパーツ。": "transition",
        # Some items send you to totally different spaces
        "アクセスすると\n登録したクリエイティブスペースに\n移動できるビルドパーツ。": "cswarp",
        # Some items are a crane
        "コネクトを受信すると\nクレーンを操作できる\nビルドパーツ。": "crane",
        # Some items can be swum in
        "上から入ると\n泳げるビルドパーツ。": "swimmable",
        # Some items can be templated
        #"thejapanesetext": "function",
        }

    # Translate the description.
    part["tr_explain"] = ("{function}").format(
        function = eval("build_parts_" +
                        part_functions[part["jp_explain"]])[LANG] if part["jp_explain"] in part_functions else "")

    if part["tr_explain"] == "":
        return -4

    return 0

build_parts_file_names = [
    "Stack_CS_Material_Ticket1",
    "Stack_CS_Material_Ticket2",
    "Stack_CS_Material_Ticket3"
    ]

for file_name in build_parts_file_names:
    parts_file_name = "Item_" + file_name + ".txt"

    try:
        parts_file = codecs.open(os.path.join(json_loc, parts_file_name),
                             mode = 'r', encoding = 'utf-8')
    except FileNotFoundError:
        print("\t{0} not found.".format(parts_file_name))
        continue
    
    parts = json.load(parts_file)
    print("{0} loaded.".format(parts_file_name) + " {")

    parts_file.close()

    newtranslations = False

    for part in parts:
        tr_text = part["tr_text"]
        fill_cn_name(part)
        name_prefix = split_name_prefix(part)
        problem = translate_part_desc(part)
        part["tr_explain"] = name_prefix + part["tr_explain"]
        unfill_cn_name(part, tr_text)

        if problem == 0:
            print("\tTranslated description for {0}".format(part["tr_text"] or part["jp_text"]))
            newtranslations = True
        elif problem == -4:
            print("\t{0} has a new kind of description".format(part["tr_text"] or part["jp_text"]))

    if newtranslations == False:
        print("\tNo new translations.")

    print("}")

    parts_file = codecs.open(os.path.join(json_loc, parts_file_name),
                             mode = 'w', encoding = 'utf-8')
    json.dump(parts, parts_file, ensure_ascii=False, indent="\t", sort_keys=False)
    parts_file.write("\n")
    parts_file.close()

####################################################################################################

# Translate LAs
try:
    items_file = codecs.open(os.path.join(json_loc, "Item_Stack_LobbyAction.txt"),
                             mode = 'r', encoding = 'utf-8')
except FileNotFoundError:
    print("\tItem_Stack_LobbyAction.txt not found.")

items = json.load(items_file)
print("Item_Stack_LobbyAction.txt loaded. {")

items_file.close()

# JP text: 
    # ロビアク『{iname}』\n
    # を全キャラクターで使用可能になる。
la_formats = [("Unlocks the new Lobby Action\n"
               "\"{iname}\"."),
              ("『{iname}』 로비 액션을\n"
               "모든 캐릭터에 등록한다."),
              ("Разблокирует новый лобби-экшн:\n"
               "\"{iname}\"."),
              ("所有角色均可選用大廳動作\n"
               "『{iname}』。")]

# JP text: 
    # 使用すると新しいロビーアクションが\n
    # 全キャラクターで選択可能になる。
nla_formats = [("Unlocks a new Lobby Action for use by\n"
                "all characters on your account."),
               ("사용하면 새로운 로비 액션이\n"
                "모든 캐릭터에서 사용 가능해진다."),
               ("Разблокирует новый лобби-экшн\n"
                "для всех персонажей вашего акка."),
               ("使用後所有角色均可選用新的大廳動作。")]

la_extras = {
            # JP text: 
                # ※対応機能：ボタン派生/一部表示適用外\n
                # 対応服指可動/『PSO2』ブロック非対応
            "*actnopreviewfingersngs": [
                ("※Extra actions (cannot preview).\n"
                 "Finger motion by outfit. Not in [PSO2]."),
                ("※지원 기능: 버튼 파생/일부 표시 적용 제외\n"
                 "대응 복장 손가락 움직임/『PSO2』 블록 미지원"),
                ("※Доп. действие (нет превью).\n"
                 "Движ. пальцев огранич. Не в [PSO2]."),
                ("※適用功能：按鍵衍生/不適用一部分顯示\n"
                 "適用服裝可動手指/不適用於『PSO2』")
                ],
            
            # JP text: 
                # ※対応機能：ボタン派生／\n
                # 対応服指可動／『PSO2』ブロック非対応
            "*actfingersngs": [
                ("Has button actions/Finger motion\n"
                 "outfit-limited/Can't use in [PSO2]."),
                ("대응 기능: 버튼 파생/대응 복장\n"
                 "손가락 가동/『PSO2』 블록 비지원"),
                ("Есть действия/Движен. пальцев\n"
                 "огранич./Недоступно в [PSO2]."),
                ("※適用功能：按鍵衍生/\n"
                 "適用服裝可動手指/不適用於『PSO2』")
                ],

            # JP text: 
                # ※対応機能：ボタン派生／\n
                # 『PSO2』ブロック非対応<c>",
            "*actngs": [
                ("Has button actions/\n"
                 "Can't use in [PSO2]."),
                ("대응 기능: 버튼 파생/\n"
                 "『PSO2』 블록 비지원"),
                ("\n"
                 ""),
                ("※適用功能：按鍵衍生/\n"
                 "不適用於『PSO2』")
                ],

            # JP text: 
                # ※対応機能：ボタン派生／ランダム／\n
                # 対応服指可動
            "*actrandomfingers": [
                ("※Has button actions/randomness.\n"
                 "Finger motion limited based on outfit."),
                ("지원 기능: 버튼 파생/랜덤\n"
                 "대응복 손가락 가동"),
                ("Есть кнопка действия/рандом.\n"
                 "Одежда влияет на движ-е пальцев"),
                ("※適用功能：按鍵衍生/隨機動作/\n"
                 "適用服裝可動手指")
                ],

            # JP text: 
                # ※対応機能：ボタン派生／\n
                # 対応服指可動
            "*actfingers": [
                ("※Use action buttons for extra actions.\n"
                 "Finger motion limited based on outfit."),
                ("지원 기능: 버튼 파생\n"
                 "대응복 손가락 가동"),
                ("Доступно доп действие.\n"
                 "Одежда влияет на движ-е пальцев"),
                ("※適用功能：按鍵衍生/\n"
                 "適用服裝可動手指")
                ],

            # JP text: 
                # ※対応機能：リアクション／\n
                # 対応服指可動／『PSO2』ブロック非対応
            "*reactfingersngs": [
                ("Has reactions/Finger motion\n"
                 "outfit-limited/Can't use in [PSO2]."),
                (""),
                ("С реакцией/Движ. пальц.\n"
                 "огранич./Не для [PSO2]."),
                ("※適用功能：反應動作/\n"
                 "適用服裝可動手指/不適用於『PSO2』")
                ],

            # JP text: 
                # ※対応機能：対応服指可動／\n
                # 武器装備反映／『PSO2』ブロック非対応
            "*fingersweaponsngs": [
                ("※Finger motion outfit limited. Shows\n"
                 "equipment. Cannot perform in [PSO2]."),
                ("※지원 기능: 대응복 손가락 가동/\n"
                 "무기 장비 반영/『PSO2』블록 비대응"),
                ("※Движ. завис-т от одежды| Отображ.\n"
                 "экип. оружие| Только для NGS."),
                ("※適用功能：適用服裝可動手指/\n"
                 "顯示裝備武器/不適用於『PSO2』")
                ],

            # JP text: 
                # ※対応機能：対応服指可動／\n
                # 『PSO2』ブロック非対応
            "*fingersngs": [
                ("※Finger motion limited based on outfit.\n"
                 "Cannot perform in [PSO2] Blocks."),
                ("※지원 기능: 대응복 손가락 가동<c>\n"
                 "『PSO2』블록 비대응"),
                ("※Одежда влияет на движ-е пальцев\n"
                 "Нельзя использовать в блоке PSO2"),
                ("※適用功能：適用服裝可動手指/\n"
                 "不適用於『PSO2』")
                ],

            # JP text: 
                # ※対応機能：対応服指可動
            "*fingers": [
                ("※Finger motion limited based on outfit."),
                ("※지원 기능: 대응복 손가락 가동"),
                ("※Одежда влияет на движ-е пальцев"),
                ("※適用功能：適用服裝可動手指")
                ],

            # JP text: 
                # 対応機能：ボタン派生\n
                # <yellow>対象服のみ指も可動<c>
            # Only on a dummy LA but the script crashes when run with -a if not included
            "actfingers": [
                ("※Use action buttons for extra actions.\n"
                 "Finger motion limited based on outfit."),
                ("지원 기능: 버튼 파생\n"
                 "대응복 손가락 가동"),
                ("Доступно доп действие.\n"
                 "Одежда влияет на движ-е пальцев"),
                ("適用功能：按鍵衍生\n"
                 "<yellow>適用服裝可動手指<c>")
                ],

            # JP text: 
                # 対応機能：ボタン派生／武器装備反映\n
                # <yellow>一部武器反映不可<c>
            "actweapons": [
                ("Shows equipment, has extra actions.\n"
                 "<yellow>Doesn't show some weapons.<c>"),
                ("지원 기능: 버튼 파생/무기 장비 반영\n"
                 "<yellow>일부 무기 반영 불가<c>"),
                ("Отображ. оружие; доп действие.\n"
                 "<yellow>Не показывает некоторое оружие.<c>"),
                ("適用功能：按鍵衍生/顯示裝備武器\n"
                 "<yellow>無法顯示一部分武器<c>")
                ],
                     
            # JP text: 
                # 対応機能：ボタン派生／ランダム
            "actrandom": [
                ("Has button actions/randomness."),
                ("지원 기능: 버튼 파생/랜덤"),
                ("Есть кнопка действия/рандом."),
                ("適用功能：按鍵衍生/隨機動作")
                ],
                     
            # JP text: 
                # 対応機能：ボタン派生
            "act": [
                ("Use action buttons for extra actions."),
                ("지원 기능: 버튼 파생"),
                ("Доступно доп действие."),
                ("適用功能：按鍵衍生")
                ],
                     
            # JP text: 
                # 対応機能：武器装備反映\n
                # <yellow>一部武器反映不可<c>
            "weapons": [
                ("Shows equipped weapons.\n"
                 "<yellow>Doesn't show some weapons.<c>"),
                ("지원 기능: 무기 장비 반영\n"
                 "<yellow>일부 무기 반영 불가<c>"),
                ("Показывает экип-е оружие.\n"
                 "<yellow>Не показывает некоторое оружие.<c>"),
                ("適用功能：顯示裝備武器\n"
                 "<yellow>無法顯示一部分武器<c>")
                ],

            # JP text: 
                # 対応機能：リアクション
            "react": [
                ("Reaction has extra actions."),
                ("지원 기능: 리액션"),
                ("Есть доп действие реакцией."),
                ("適用功能：反應動作")
                ]
            }

extras_names = {
    "ボタン派生/一部表示適用外\n対応服指可動/『PSO2』ブロック非対応<c>": "*actnopreviewfingersngs",
    "ボタン派生／\n対応服指可動／『PSO2』ブロック非対応<c>": "*actfingersngs",
    "ボタン派生／対応服指可動／\n『PSO2』ブロック非対応<c>": "*actfingersngs",
    "ボタン派生／\n『PSO2』ブロック非対応<c>": "*actngs",
    "ボタン派生／ランダム／\n対応服指可動<c>": "*actrandomfingers",
    "ボタン派生／\n対応服指可動<c>": "*actfingers",
    "リアクション／\n対応服指可動／『PSO2』ブロック非対応<c>": "*reactfingersngs",
    "対応服指可動／\n武器装備反映／『PSO2』ブロック非対応<c>": "*fingersweaponsngs",
    "対応服指可動／\n『PSO2』ブロック非対応<c>": "*fingersngs",
    "対応服指可動<c>": "*fingers",
    "ボタン派生\n<yellow>対象服のみ指も可動<c>": "actfingers",
    "ボタン派生／武器装備反映\n<yellow>一部武器反映不可<c>": "actweapons",
    "ボタン派生／ランダム": "actrandom",
    "ボタン派生": "act",
    "武器装備反映\n<yellow>一部武器反映不可<c>": "weapons",
    "リアクション":"react"
    }

# JP text: 
    # 使用すると新しい手のポーズが\n全キャラクターで選択可能になる。\n
    # <yellow>※一部ロビーアクション非対応／\n
    # 『PSO2』ブロック非対応<c>
ha_formats = [("When used, allows you to select a\n"
               "new hand pose for all characters.\n"
               "<yellow>※Does not support all Lobby Actions.\n"
               "※Cannot perform in [PSO2] Blocks.<c>"),
              ("사용하면 새로운 손가락 포즈가\n"
               "모든 캐릭터로 선택할 수 있게 된다.\n"
               "<yellow>※일부 로비 액션 미지원/\n"
               "『PSO2』블록 비대응<c>"),
              ("Даёт возможность использовать\n"
               "версию с двигающимися пальцами.\n"
               "<yellow>※Поддерж-т не все лобби-экшены.\n"
               "※Нельзя использовать в блоке PSO2<c>"),
              ("使用後所有角色均可選用新的手部姿勢。\n"
               "<yellow>※不適用於一部分大廳動作/\n"
               "不適用於『PSO2』<c>")]

def translate_la_desc(item, name_prefix):
    item_name = ""

    # Decide what name we're working with
    if TRANS_ALL:
        item_name = item["tr_text"] or item["jp_text"]
    else:
        if item["tr_text"] == "":
            # No translated name so skip this one (except CN)
            if LANG != 3:
                return -1
            # No translated name so copy the JP name (for CN)
            else:
                item["tr_text"] = item["jp_text"]
                item_name = item["tr_text"]
        else:
            item_name = item["tr_text"]

    # Tradable items keep the JP name in CN, their translated name is in the green prefix
    item_name = get_item_name(item, name_prefix) or item_name

    # Description already present, leave it alone
    if REDO_ALL == False and item["tr_explain"] != "":
        return -2

    # Figure out what extra stuff to put at the end of the description
    extras = "n"
    # Split off the bit that changes and use it as the key to a dictionary of codenames    
    if "対応機能：" in item["jp_explain"]:
        extras_jp = item["jp_explain"].split("対応機能：")[1]
        extras = extras_names[extras_jp]
    elif "※『PSO2』ブロック非対応" in item["jp_explain"]:
        extras = "ngs_locks"

    # Translate old LAs
    if "ロビアク『" in item["jp_explain"]:
        # Split LA name from number.
        splits = regex.split("[\"「」]", item_name)
        
        item["tr_explain"] = (la_formats[LANG] + "{extrastuff}").format(
            # Remember Photon Chairs have no number
            iname = splits[1] if len(splits) > 1 else splits[0],
            extrastuff = "" if extras == "n" else "\n" + la_extras[extras][LANG])
    
    # Translate hand poses    
    elif "使用すると新しい手のポーズが" in item["jp_explain"]:
        item["tr_explain"] = ha_formats[LANG]

    # Translate new LAs
    else:
        item["tr_explain"] = (nla_formats[LANG] + "{extrastuff}").format(
            extrastuff = ("" if extras == "n"
                          else "\n" + "<yellow>" + ngs_locks[LANG] + "<c>" if extras == "ngs_locks"
                          else "\n" + "<yellow>" + la_extras[extras][LANG] + "<c>"
                          )
                      )

    item["tr_explain"] = item["tr_explain"].translate(chartable[LANG])
    
    return 0    

for item in items:
    tr_text = item["tr_text"]
    fill_cn_name(item)
    name_prefix = split_name_prefix(item)
    problem = translate_la_desc(item, name_prefix)
    item["tr_explain"] = name_prefix + item["tr_explain"]
    unfill_cn_name(item, tr_text)

    if problem == 0:
        print("\tTranslated description for {0}".format(item["tr_text"] or item["jp_text"]))
        newtranslations = True

if newtranslations == False:
    print("\tNo new translations.")

print("}")       

items_file = codecs.open(os.path.join(json_loc, "Item_Stack_LobbyAction.txt"),
                         mode = 'w', encoding = 'utf-8')
json.dump(items, items_file, ensure_ascii=False, indent="\t", sort_keys=False)
items_file.write("\n")
items_file.close()

####################################################################################################

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
    "ゆかな": ["Yukana Nogami", "", "Ногами Юкана", "尤加奈"],
    "チョー": ["Cho", "쵸", "Чо", "長"],
    "ポポナ": ["Popona", "", "Попона", "波波娜"],
    "下野 紘": ["Hiro Shimono", "시모노 히로", "Хиро Симоно", "下野 紘"],
    "中原 麻衣": ["Mai Nakahara", "나카하라 마이", "Маи Накахара", "中原 麻衣"],
    "中尾 隆聖": ["Ryusei Nakao", "나카오 류세이", "Рюсэй Накао", "中尾 隆聖"],
    "中村 悠一": ["Yuichi Nakamura", "유이치 나카무라", "Юичи Накамура", "中村 悠一"],
    "中田 譲治": ["Joji Nakata", "나카타 조지", "Дзёдзи Наката", "中田 讓治"],
    "中西 茂樹": ["Shigeki Nakanishi", "", "Сигэки Наканиши", "中西 茂樹"],
    "久野 美咲": ["Misaki Kuno", "", "Мисаки Куно", "久野 美咲"],
    "井上 和彦": ["Kazuhiko Inoue", "", "Казухико Иноэ", "井上 和彥"],
    "井上 喜久子": ["Kikuko Inoue", "", "Кикуко Иноуэ", "井上 喜久子"],
    "井上 麻里奈": ["Marina Inoue", "", "Марина Иноуэ", "井上 麻里奈"],
    "井口 裕香": ["Yuka Iguchi", "", "Юка Игути", "井口 裕香"],
    "今井 麻美": ["Asami Imai", "", "Асами Имаи", "今井 麻美"],
    "伊瀬 茉莉也": ["Mariya Ise", "", "Мария Исэ", "伊瀨 茉莉也"],
    "伊藤 静": ["Shizuka Ito", "", "Сидзука Ито", "伊藤 靜"],
    "会 一太郎": ["Ichitaro Ai", "", "Ичитаро Ай", "會 一太郎"],
    "住友 優子": ["Yuko Sumitomo", "", "Юко Сумитомо", "住友 優子"],
    "佐倉 綾音": ["Ayane Sakura", "", "Аянэ Сакура", "佐倉 綾音"],
    "佐武 宇綺": ["Uki Satake", "", "Уки Сатакэ", "佐武 宇綺"],
    "佐藤 利奈": ["Rina Sato", "", "Рина Сато", "佐藤 利奈"],
    "佐藤 友啓": ["Tomohiro Sato", "", "Томохиро Сато", "佐藤 友啓"],
    "佐藤 聡美": ["Satomi Sato", "", "Сатоми Сато", "佐藤 聰美"],
    "佳村 はるか": ["Haruka Yoshimura", "", "Харука Ёсимура", "佳村 遙"],
    "保志 総一朗": ["Soichiro Hoshi", "", "Соичиро Хоши", "保志 總一朗"],
    "光吉 猛修": ["Takenobu Mitsuyoshi", "", "Такэнобу Мицуёши", "光吉 猛修"],
    "内田 真礼": ["Maaya Uchida", "", "Маая Утида", "內田 真禮"],
    "千本木 彩花": ["Sayaka Senbongi", "", "Саяка Сэмбонги", "千本木 彩花"],
    "古賀 葵": ["Aoi Koga", "", "Аой Кога", "古賀 葵"],
    "吉野 裕行": ["Hiroyuki Yoshino", "", "Хироюки Ёшино", "吉野 裕行"],
    "名塚 佳織": ["Kaori Nazuka", "", "Каори Надзука", "名塚 佳織"],
    "喜多村 英梨": ["Eri Kitamura", "", "Эри Китамура", "喜多村 英梨"],
    "坂本 真綾": ["Maaya Sakamoto", "", "Маая Сакамото", "坂本 真綾"],
    "堀川 りょう": ["Ryo Horikawa", "", "Рё Хорикава", "堀川 亮"],
    "堀江 由衣": ["Yui Horie", "", "Юи Хориэ", "堀江 由衣"],
    "増田 俊樹": ["Toshiki Masuda", "", "Тошики Масуда", "增田 俊樹"],
    "天野 名雪": ["Nayuki Amano", "", "Наюки Амано", "天野 名雪"],
    "子安 武人": ["Takehito Koyasu", "", "Такэхито Коясу", "子安 武人"],
    "安元 洋貴": ["Hiroki Yasumoto", "", "Хироки Ясумото", "安元 洋貴"],
    "安済 知佳": ["Chika Anzai", "", "Чика Андзаи", "安濟 知佳"],
    "寺島 拓篤": ["Takuma Terashima", "", "Такума Тэрашима", "寺島 拓篤"],
    "小倉 唯": ["Yui Ogura", "", "Юй Огура", "小倉 唯"],
    "小原 莉子": ["Riko Kohara", "", "Рико Кохара", "小原 莉子"],
    "小山 茉美": ["Mami Koyama", "", "Мами Кояма", "小山 茉美"],
    "小松 未可子": ["Mikako Komatsu", "", "Микако Комацу", "小松 未可子"],
    "小林 ゆう": ["Yu Kobayashi", "", "Ю Кобаяши", "小林 優"],
    "小清水 亜美": ["Ami Koshimizu", "", "Ами Косимидзу", "小清水 亞美"],
    "小西 克幸": ["Katsuyuki Konishi", "", "Кацуюки Кониши", "小西 克幸"],
    "小野 大輔": ["Daisuke Ono", "", "Дайсукэ Оно", "小野 大輔"],
    "小野坂 昌也": ["Masaya Onosaka", "", "Масая Оносака", "小野坂 昌也"],
    "山岡 ゆり": ["Yuri Yamaoka", "", "Юри Ямаока", "山岡 百合"],
    "岡本 信彦": ["Nobuhiko Okamoto", "", "Нобухико Окамото", "岡本 信彥"],
    "岩下 読男": ["Moai Iwashita", "", "Моаи Ивасита", "岩下 讀男"],
    "島本 須美": ["Sumi Shimamoto", "", "Суми Симамото", "島本 須美"],
    "島﨑 信長": ["Nobunaga Shimazaki", "", "Нобунага Симадзаки", "島崎 信長"],
    "川村 万梨阿": ["Maria Kawamura", "", "Мария Кавамура", "川村 萬梨阿"],
    "川澄 綾子": ["Ayako Kawasumi", "", "Аяко Кавасуми", "川澄 綾子"],
    "市来 光弘": ["Mitsuhiro Ichiki", "", "Мицухиро Ичики", "市來 光弘"],
    "引坂 理絵": ["Rie Hikisaka", "", "Рие Хирисака", "引坂 理繪"],
    "悠木 碧": ["Aoi Yuki", "", "Аои Юки", "悠木 碧"],
    "戸松 遥": ["Haruka Tomatsu", "토마츠 하루카", "Харука Томацу", "戶松 遙"],
    "斉藤 壮馬": ["Soma Saito", "", "Сома Сайто", "齊藤 壯馬"],
    "斉藤 朱夏": ["Shuka Saito", "", "Шюка Саито", "齊藤 朱夏"],
    "斎藤 千和": ["Chiwa Saito", "사이토 치와", "Тива Сайто", "齋藤 千和"],
    "新田 恵海": ["Emi Nitta", "", "Эми Нитта", "新田 惠海"],
    "日笠 陽子": ["Yoko Hikasa", "", "Ёко Хикаса", "日笠 陽子"],
    "早見 沙織": ["Saori Hayami", "", "Саори Хаями", "早見 沙織"],
    "木村 珠莉": ["Juri Kimura", "", "Дзюри Кимура", "木村 珠莉"],
    "木村 良平": ["Ryohei Kimura", "", "Рёхэй Кимура", "木村 良平"],
    "本渡 楓": ["Kaede Hondo", "", "Каэдэ Хондо", "本渡 楓"],
    "杉田 智和": ["Tomokazu Sugita", "", "Томокадзу Сугита", "杉田 智和"],
    "村川 梨衣": ["Rie Murakawa", "", "Риэ Муракава", "村川 梨衣"],
    "東山 奈央 ": ["Nao Toyama", "토야마 나오", "Нао Тояма", "東山 奈央"],
    "松岡 禎丞": ["Yoshitsugu Matsuoka", "마츠오카 요시츠구", "Ёсицугу Мацуока", "松岡 禎丞"],
    "柿原 徹也": ["Tetsuya Kakihara", "카키하라 테츠야", "Тэцуя Какихара", "柿原 徹也"],
    "桃井 はるこ": ["Haruko Momoi", "", "Харуко Момои", "桃井 晴子"],
    "桑島 法子": ["Houko Kuwashima", "", "Хоко Кувасима", "桑島 法子"],
    "梶 裕貴": ["Yuki Kaji", "", "Юки Кадзи", "梶 裕貴"],
    "森久保 祥太郎": ["Showtaro Morikubo", "", "Сётаро Морикубо", "森久保 祥太郎"],
    "植田 佳奈": ["Kana Ueda", "", "Кана Уэда", "植田 佳奈"],
    "榊原 良子": ["Yoshiko Sakakibara", "", "Ёсико Сакакибара", "榊原 良子"],
    "榎本 温子": ["Atsuko Enomoto", "", "Ацуко Эномото", "榎本 溫子"],
    "横山 智佐": ["Chisa Yokoyama", "", "Тиса Ёкояма", "橫山 智佐"],
    "橘田 いずみ": ["Izumi Kitta", "", "Идзуми Китта", "橘田 泉"],
    "櫻井 孝宏": ["Takahiro Sakurai", "", "Такахиро Сакураи", "櫻井 孝宏"],
    "水樹 奈々": ["Nana Mizuki", "", "Нана Мидзуки", "水樹 奈奈"],
    "水橋 かおり": ["Kaori Mizuhashi", "", "Каори Мидзухаси", "水橋 香織"],
    "江口 拓也": ["Takuya Eguchi", "", "Такуя Эгучи", "江口 拓也"],
    "沢城 みゆき": ["Miyuki Sawashiro", "", "Миюки Саваширо", "澤城 美雪"],
    "沼倉 愛美": ["Manami Numakura", "", "Манами Нумакура", "沼倉 愛美"],
    "洲崎 綾": ["Aya Suzaki", "", "Ая Судзаки", "洲崎 綾"],
    "清水 彩香": ["Ayaka Shimizu", "", "Аяка Симидзу", "清水 彩香"],
    "渡辺 久美子": ["Kumiko Watanabe", "", "Кумико Ватанабэ", "渡邊 久美子"],
    "潘 めぐみ": ["Megumi Han", "", "Мэгуми Хан", "潘 惠美"],
    "瀬戸 麻沙美": ["Asami Seto", "", "Асами Сэто", "瀨戶 麻沙美"],
    "玄田 哲章": ["Tessho Genda", "", "Тэссё Гэнда", "玄田 哲章"],
    "生天目 仁美": ["Hitomi Nabatame", "", "Хитоми Набатамэ", "生天目 仁美"],
    "田中 理恵": ["Rie Tanaka", "", "Риэ Танака", "田中 理惠"],
    "田村 ゆかり": ["Yukari Tamura", "", "Юкари Тамура", "田村 由香里"],
    "田辺 留依": ["Rui Tanabe", "타나베 루이", "Руи Танабэ", "田邊 留依"],
    "甲斐田 裕子": ["Yuko Kaida", "", "Юко Каида", "甲斐田 裕子"],
    "白石 涼子": ["Ryoko Shiraishi", "", "Рёко Сираиси", "白石 涼子"],
    "白鳥 哲": ["Tetsu Shiratori", "", "Тэцу Сиратори", "白鳥 哲"],
    "皆口 裕子": ["Yuko Minaguchi", "미나구치 유코", "Юко Минагучи", "皆口 裕子"],
    "矢島 晶子": ["Akiko Yajima", "", "Юко Минагучи", "矢島 晶子"],
    "石田 彰": ["Akira Ishida", "", "Акира Исида", "石田 彰"],
    "神原 大地": ["Daichi Kanbara", "", "Даичи Камбара", "神原 大地"],
    "神谷 浩史": ["Hiroshi Kamiya", "", "Хироши Камия", "神谷 浩史"],
    "福山 潤": ["Jun Fukuyama", "", "Дзюн Фукуяма", "福山 潤"],
    "秋元 羊介": ["Yosuke Akimoto", "", "Ёсукэ Акимото", "秋元 羊介"],
    "秦 佐和子": ["Sawako Hata", "", "Савако Хата", "秦 佐和子"],
    "種田 梨沙": ["Risa Taneda", "타네다 리사", "Риса Танеда", "種田 梨沙"],
    "立木 文彦": ["Fumihiko Tachiki", "타치키 후미히코", "Фумихико Тачики", "立木 文彥"],
    "立花 理香": ["Rika Tachibana", "", "Рика Тачибана", "立花 理香"],
    "竹達 彩奈": ["Ayana Taketatsu", "", "Аяна Такэтацу", "竹達 彩奈"],
    "細谷 佳正": ["Yoshimasa Hosoya", "", "Ёшимаса Хосоя", "細谷 佳正"],
    "紲星 あかり": ["Kizuna Akari", "", "Кизуна Акари", "紲星 燈"],
    "結月 ゆかり": ["Yuzuki Yukari", "", "Юзуки Акари", "結月 緣"],
    "緑川 光": ["Hikaru Midorikawa", "", "Хикару Мидорикава", "綠川 光"],
    "緒方 恵美": ["Megumi Ogata", "", "Мэгуми Огата", "緒方 惠美"],
    "能登 麻美子": ["Mamiko Noto", "", "Мамико Ното", "能登 麻美子"],
    "花江 夏樹": ["Natsuki Hanae", "", "Нацуки Ханаэ", "花江 夏樹"],
    "花澤 香菜": ["Kana Hanazawa", "", "Кана Ханадзава", "花澤 香菜"],
    "若本 規夫": ["Norio Wakamoto", "", "Норио Вакамото", "若本 規夫"],
    "茅野 愛衣": ["Ai Kayano", "", "Аи Каяно", "茅野 愛衣"],
    "草尾 毅": ["Takeshi Kusao", "", "Такэши Кусао", "草尾 毅"],
    "菊地 美香": ["Mika Kikuchi", "", "Мика Кикучи", "菊地 美香"],
    "蒼井 翔太": ["Shouta Aoi", "", "Сёта Аои", "蒼井 翔太"],
    "藤本 結衣": ["Yui Fujimoto", "", "Юи Фудзимото", "藤本 結衣"],
    "藤田 曜子": ["Yoko Fujita", "", "Ёко Фудзита", "藤田 曜子"],
    "藤田 茜": ["Akane Fujita", "", "Аканэ Фудзита", "藤田 茜"],
    "諏訪 彩花": ["Ayaka Suwa", "", "Аяка Сува", "諏訪 彩花"],
    "諏訪部 順一": ["Junichi Suwabe", "", "Дзюнъичи Сувабэ", "諏訪部 順一"],
    "豊口 めぐみ": ["Megumi Toyoguchi", "", "Мэгуми Тоёгучи", "豐口 惠"],
    "豊崎 愛生": ["Aki Toyosaki", "", "Аки Тоёсаки", "豐崎 愛生"],
    "近藤 佳奈子": ["Kanako Kondo", "", "Канако Кондо", "近藤 佳奈子"],
    "速水 奨": ["Sho Hayami", "", "Сё Хаями", "速水 獎"],
    "那須 晃行": ["Akiyuki Nasu", "", "Акаюки Насу", "那須 晃行"],
    "金元 寿子": ["Hisako Kanemoto", "", "Хисако Канэмото", "金元 壽子"],
    "金田 アキ": ["Aki Kanada", "", "Аки Канада", "金田 晶"],
    "釘宮 理恵": ["Rie Kugimiya", "", "Риэ Кугимия", "釘宮 理惠"],
    "鈴村 健一": ["Kenichi Suzumura", "스즈무라 켄이치", "Кэнъити Судзумура", "鈴村 健一"],
    "銀河 万丈": ["Banjo Ginga", "", "Бандзё Гинга", "銀河 萬丈"],
    "長谷川 唯": ["Yui Hasegawa", "", "Юи Хасэгава", "長谷川 唯"],
    "門脇 舞以": ["Mai Kadowaki", "", "Маи Кадоваки", "門脇 舞以"],
    "関 智一": ["Tomokazu Seki", "", "Томокадзу Сэки", "關 智一"],
    "阿澄 佳奈": ["Kana Asumi", "", "Кана Асуми", "阿澄 佳奈"],
    "陶山 章央": ["Akio Suyama", "", "Акио Суяма", "陶山 章央"],
    "雨宮 天": ["Sora Amamiya", "", "Сора Амамия", "雨宮 天"],
    "飛田 展男": ["Nobuo Tobita", "", "Нобуо Тобита", "飛田 展男"],
    "飯田 友子": ["Yuko Iida", "이이다 유우코", "Юко Иида", "飯田 友子"],
    "高木 友梨香": ["Yurika Takagi", "", "Юрика Такаги", "高木 友梨香"],
    "高橋 未奈美": ["Minami Takahashi", "", "Минами Такахаши", "高橋 未奈美"],
    "高橋 李依": ["Rie Takahashi", "", "Риэ Такахаши", "高橋 李依"],
    "高野 麻里佳": ["Marika Kono", "", "Марика Коно", "高野 麻里佳"],
    "黒沢 ともよ": ["Tomoyo Kurosawa", "", "Томоё Куросава", "黑澤 朋世"],
    "こおろぎさとみ": ["Satomi Korogi", "코오로기 사토미", "Сатоми Короги", "興梠 里美"],
    "三宅 健太": ["Kenta Miyake", "", "Кэнта Миякэ", "三宅 健太"],
    "諸星 すみれ": ["Sumire Morohoshi", "", "Сумирэ Морохоси", "諸星 堇"],
    "宮本 侑芽": ["Yume Miyamoto", "", "Юмэ Миямото", "宮本 侑芽"],
    "川島 得愛": ["Tokuyoshi Kawashima", "", "Токуёси Кавасима", "川島 得愛"],
    "田所 あずさ": ["Azusa Tadokoro", "", "Адзуса Тадокоро", "田所 梓"],
    "森田 順平": ["Junpei Morita", "", "Дзюмпэи Морита", "森田 順平"],
    "上田 麗奈": ["Reina Ueda", "", "Уэда Рэйна", "上田 麗奈"],
    "入野 自由": ["Miyu Irino", "", "Ирино Мию", "入野 自由"],
    "梅原 裕一郎": ["Yuichiro Umehara", "", "Умэхара Юитиро", "梅原 裕一郎"],
    "逢坂 良太": ["Ryota Osaka", "", "Осака Рёта", "逢坂 良太"],
    "小原 好美": ["Konomi Kohara", "", "Кохара Кономи", "小原 好美"],
    "白上 フブキ": ["Shirakami Fubuki", "", "Шираками Фубуки", "白上 吹雪"],
    "影山 シエン": ["Kageyama Shien", "", "Шиэн Кагеяма", "影山 紫炎"],
    "一 伊那尓栖": ["Ninomae Ina'nis", "", "Ина'нис Ниномае", "一 伊那爾棲"],
    "日野 聡": ["Satoshi Hino", "", "Хино Сатоси", "日野 聰"],
    "原 由実": ["Yumi Hara", "", "Хара Юми", "原 由實"],
    "闇ノ シュウ": ["Shu Yamino", "", "Ямино Сю", "Shu Yamino"],
    "星川 サラ": ["Hoshikawa Sara", "", "Сара Хошикава", "星川 莎拉"],
    "葉加瀬 冬雪": ["Hakase Fuyuki", "", "Фуюки Хакасе", "葉加瀨 冬雪"],
    "甲斐田 晴": ["Haru Kaida", "", "Каида Хару", "甲斐田 晴"],
    "津田 健次郎": ["Kenjiro Tsuda", "", "Цуда Кенджо", "津田 健次郎"],
    "鬼頭 明里": ["Akari Kito", "", "Кито Акари", "鬼頭 明里"],
    "Ｍ・Ａ・Ｏ": ["M・A・O", "M・A・O", "M・A・O", "M·A·O"],
    "山口 勝平": ["Kappei Yamaguchi", "", "Каппэй Ямагути", "山口 勝平"],
    "楠 大典": ["Taiten Kusunoki", "", "Таитэн Кусуноки", "楠 大典"],
    "小澤 亜李": ["Ari Ozawa", "", "Ари Одзава", "小澤 亞李"],
    "天宮 こころ": ["Amamiya Kokoro", "", "", "天宮 心"],
    "長尾 景": ["Nagao Kei", "", "", "長尾 景"],
    "魔使 マオ": ["Matsukai Mao", "", "", "魔使 真央"],
    "夜見 れな": ["Yorumi Rena", "", "", "夜見 蕾娜"],
    "石見 舞菜香": ["Manaka Iwami", "", "", "石見 舞菜香"],
    "山下 誠一郎": ["Seiichiro Yamashita", "", "", "山下 誠一郎"],
    "水瀬 いのり": ["Inori Minase", "", "", "水瀨 祈"],
    "内田 雄馬": ["Yuma Uchida", "", "", "內田 雄馬"],
    "和氣 あず未": ["Azumi Waki", "", "", "和氣 杏未"],
    "小市 眞琴": ["Makoto Koichi", "", "", "小市 真琴"],
    "福西 勝也": ["Masaya Fukunishi", "", "", "福西 勝也"],
    "加藤 渉": ["Wataru Kato", "", "", "加藤 涉"],
    "河西 健吾": ["Kengo Kawanishi", "", "", "河西 健吾"],
    "福原 綾香": ["Ayaka Fukuhara", "", "", "福原 綾香"],
    "ファイルーズ あい": ["Ai Fairouz", "", "", "菲魯茲·藍"],
    "種﨑 敦美": ["Atsumi Tanezaki", "", "", "種崎 敦美"],
    "市ノ瀬 加那": ["Kana Ichinose", "", "", "市之瀨 加那"],
    "小林 千晃": ["Chiaki Kobayashi", "", "", "小林 千晃"],
    "阿部 敦": ["Atsushi Abe", "", "", "阿部 敦"],
    "ささき のぞみ": ["Nozomi Sasaki", "", "", "佐佐木 望"],
    "でびでび・でびる": ["Debidebi Debiru", "", "", "德比德比·德比魯"],
    "アルス・アルマル": ["Ars Almal", "", "", "阿露絲·阿爾瑪"],
    "ニュイ・ソシエール": ["Nui Sociere", "", "", "紐伊·索西艾瑞"],
    "竜胆 尊": ["Mikoto Rindou", "", "", "龍膽 尊"],
    "岡咲 美保": ["Miho Okasaki", "", "", "岡咲 美保"],
    "日高 里菜": ["Rina Hidaka", "", "", "日高 里菜"],
    "永瀬 アンナ": ["Anna Nagase", "", "", "永瀨 安奈"],
    "五十嵐 梨花": ["Rika Igarashi", "", "", "五十嵐 梨花"],
    "倉持 めると": ["Meruto Kuramochi", "", "", "倉持 妹路特"],
    "ソフィア・ヴァレンタイン": ["Sophia Valentine", "", "", "蘇菲婭·瓦綸玎"],
    "狂蘭 メロコ": ["Meloco Kyoran", "", "", "Meloco Kyoran"],
    "伊藤 ゆいな": ["Yuina Ito", "", "", "伊藤 結衣奈"],
    "花守 ゆみり": ["Yumiri Hanamori", "", "", "花守 由美里"],
    "？？？": ["???", "???", "???", "？？？"],
    "": ["Unknown", "알 수 없는", "Неизвестно", ""]
    }

cv_title = ["CV: ", "CV: ", "CV: ", "CV："]

# What to fall back to if a name hasn't been translated into your language.
# -1: Prefer falling back to JP over any other language
name_fallbacks = {0: -1,
                  1: -1,
                  2: 0,
                  3: -1}

# JP text: 
    # 使用すると、新しいボイスが選択可能。
voice_desc_formats = ["Allows a new voice to be selected.",
                      "사용하면 새로운 보이스 사용 가능.",
                      "Позволяет выбрать новый голос.",
                      "使用後，可選用新的語音。"]

def translate_voice(item, name_prefix):
    item_name = ""

    # Decide what name we're working with
    if TRANS_ALL:
        item_name = item["tr_text"] or item["jp_text"]
    else:
        if item["tr_text"] == "":
            # No translated name so skip this one (except CN)
            if LANG != 3:
                return -1
            # No translated name so copy the JP name (for CN)
            else:
                item["tr_text"] = item["jp_text"]
                item_name = item["tr_text"]
        else:
            item_name = item["tr_text"]

    # Tradable items keep the JP name in CN, their translated name is in the green prefix
    item_name = get_item_name(item, name_prefix) or item_name

    # No JP description so skip this one
    if item["jp_explain"] == "":
            return -1
    
    # Description already present, leave it alone
    if (REDO_ALL == False and item["tr_explain"] != ""
          # Catch old format descriptions that keep creeping in somehow.
          and "Salon" not in item["tr_explain"]): 
        return -2

    # Strings for race/sex combo restrictions
    # JP text unavailable.
    restrictions = {
    "hm": ["\nNon-Cast male characters only.",
           "\n인간 남성만 사용 가능.",
           "\nТолько для М не CAST'ов.",
           "\n僅限非機人男性使用。"],
    "hf": ["\nNon-Cast female characters only.",
           "\n인간 여성만 사용 가능.",
           "\nТолько для Ж не CAST'ов.",
           "\n僅限非機人女性使用。"],
    "cm": ["\nMale Casts only.",
           "\n캐스트 남성만 사용 가능.",
           "\nТолько для М CAST'ов.",
           "\n僅限男性機人使用。"],
    "cf": ["\nFemale Casts only.",
           "\n캐스트 여성만 사용 가능.",
           "\nТолько для Ж CAST'ов.",
           "\n僅限女性機人使用。"],
    "am": ["\nMale characters only (all races).",
           "\n남성만 사용 가능.",
           "\nТолько М персонажей (все расы).",
           "\n僅限男性使用。"],
    "af": ["\nFemale characters only (all races).",
           "\n여성만 사용 가능.",
           "\nТолько Ж персонажей (все расы).",
           "\n僅限女性使用。"],
    "an": ["\nUsable by all characters.",
           "\n모두 사용 가능.",
           "\nДоступно всем персонажам.",
           ""]}
    
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
    cv_name = ""

    # We do, so try to translate it
    if jp_cv_name in cv_names: 
        curr_lang = LANG
        
        while cv_name == "":
            # We've fallen back to JP. Nowhere else to fall back to so break
            if curr_lang == -1:
                cv_name = jp_cv_name
                break
            else:
                cv_name = cv_names[jp_cv_name][curr_lang]
                if cv_name == "":
                    print("\tWARNING: No translation for {jp} in {currlang}, falling back to {nextlang}".format(
                        jp = jp_cv_name,
                        currlang = LANGS[curr_lang],
                        nextlang = LANGS[name_fallbacks[curr_lang]]))
                curr_lang = name_fallbacks[curr_lang]
        
    else:
        # We don't, so report it.
        print("Voice ticket {0} has a new voice actor: {1}"
              .format(item_name, jp_cv_name))
        cv_name = jp_cv_name
    
    # Translate the description
    item["tr_explain"] = voice_desc_formats[LANG] + "{restriction}\n{cv}{actorname}".format(
        restriction = restrictions[racensex][LANG],
        cv = cv_title[LANG],
        actorname = cv_name)

    item["tr_explain"] = item["tr_explain"].translate(chartable[LANG])
        
    return 0

for item in items:
    
    tr_text = item["tr_text"]
    
    fill_cn_name(item)
    name_prefix = split_name_prefix(item)
    problem = translate_voice(item, name_prefix)
    item["tr_explain"] = name_prefix + item["tr_explain"]
    unfill_cn_name(item, tr_text)

    if problem == 0:
        print("\tTranslated description for {0}".format(item["tr_text"] or item["jp_text"]))
        newtranslations = True

if newtranslations == False:
    print("\tNo new translations.")

print("}")       

items_file = codecs.open(os.path.join(json_loc, "Item_Stack_Voice.txt"),
                         mode = 'w', encoding = 'utf-8')
json.dump(items, items_file, ensure_ascii=False, indent="\t", sort_keys=False)
items_file.write("\n")
items_file.close()

####################################################################################################

# Translate other things

# JP text: 
    # マグの見た目を変更するデバイス。
magd_evol_formats = ["A device that changes a Mag's form.",
                            "마그의 외형을 변경하는 디바이스.",
                            "Изменяет форму Mag'а.",
                            "變更瑪古外觀的裝置。"]

# JP text: 
    # マグのレベルや支援機能をリセットし\n
    # マグを初期の状態に戻すデバイス。
magd_reset_formats = [("Resets a Mag's appearance, stats,\n"
                                "and support functions back to its \n"
                                "default state."),
                                ("마그의 레벨과 지원 기능을 재설정 하고\n"
                                "마그를 초기 상태로 되롤릴 수 있는 장치"),
                                ("Сбрасывает внещний вид, хар-ки,\n"
                                "и функции поддержки Mag'а до\n"
                                "состояния по умолчанию."),
                                ("重置瑪古的等級與支援功能\n"
                                "並使瑪古變回初始狀態的裝置。")]

# JP text:
    # 特殊能力を\n
    # 武器、防具に追加するカプセル。
capsule_formats = [("A capsule that adds a Special Ability\n"
                    "to a weapon or piece of armor."),
                   (""),
                   (""),
                   ("為武器、防具追加特殊能力的膠囊。")]

# JP text:
    # EX特殊能力を\n
    # 武器に追加するカプセル。
capsule_ex_formats = [("A capsule that adds an EX Special\n"
                       "Ability to a weapon."),
                      (""),
                      (""),
                      ("為武器追加EX特殊能力的膠囊。")]

# Translate the files that can be sorted by description or item name.
def translate_cosmeticsorted_desc(item, file_name, name_prefix):
    item_name = ""

    # Decide what name we're working with
    if TRANS_ALL:
        item_name = item["tr_text"] or item["jp_text"]
    else:
        if item["tr_text"] == "":
            # No translated name so skip this one (except CN)
            if LANG != 3:
                return -1
            # No translated name so copy the JP name (for CN)
            else:
                item["tr_text"] = item["jp_text"]
                item_name = item["tr_text"]
        else:
            item_name = item["tr_text"]

    # Tradable items keep the JP name in CN, their translated name is in the green prefix
    item_name = get_item_name(item, name_prefix) or item_name
    
    # Description already present, leave it alone
    if REDO_ALL == False and item["tr_explain"] != "":
        return -2

    # Sort the description format
    desc_sort = "use_new"
    if item["jp_explain"].startswith("チケットを使用すると、新しい"):
        desc_sort = "ticket_new"

    # Some Mag devices can only be used for mags that are lv.100 or above in PSO2.
    magdlv100 = False
    if "『PSO2』ではLv.100以上の" in item["jp_explain"]:
        magdlv100 = True

    # Some Mag devices can only be used in NGS.
    magdngs = False
    if "『NGS』でのみ使用可能" in item["jp_explain"]:
        magdngs = True

    # Some capsules can be exchanged at the Item Lab.
    capsuleexchange = False
    if "“強化素材交換”" in item["jp_explain"]:
        capsuleexchange = True

    # Sort the type.
    item_type = "n"
    if "新しい頭部" in item["jp_explain"]:
        item_type = "Head"
    elif "パートナーカード（ＰＣ）" in item["jp_explain"]:
        item_type = "Personalcard"
    elif "マグの見た目を変更するデバイス" in item["jp_explain"]:
        item_type = "MagDeviceEvol"
    elif "マグのレベルや支援機能をリセットし" in item["jp_explain"]:
        item_type = "MagDeviceReset"
    elif item["jp_explain"].startswith("EX特殊能力を"):
        item_type = "CapsuleEX"
    elif item["jp_explain"].startswith("特殊能力を"):
        item_type = "Capsule"

    # Combine the variable name.
    desc_format_name = "cosmetic_desc_" + desc_sort + "_formats"

    # Translate the description.
    if item_type == "Personalcard":
        # Need to expand if needed
        return -1
    elif item_type.startswith("MagDevice"):
        item["tr_explain"] = ("{magd_format}" + "{magd_lv100limit}" + "{magd_ngslimit}").format(
        magd_format = (magd_evol_formats[LANG] if item_type == "MagDeviceEvol" else magd_reset_formats[LANG]),
        magd_lv100limit = "\n<yellow>" + mag_device_lv100[LANG] + "<c>" if magdlv100 == True else "",
        magd_ngslimit = "\n<yellow>" + mag_device_ngs[LANG] + "<c>" if magdngs == True else "")
    elif item_type.startswith("Capsule"):
        item["tr_explain"] = ("{capsule_format}" + "{exchange}" + "{exlimit}").format(
        capsule_format = (capsule_ex_formats[LANG] if item_type == "CapsuleEX" else capsule_formats[LANG]),
        exchange = "\n" + capsule_exchange[LANG] if capsuleexchange == True else "",
        exlimit = "\n<yellow>" + capsule_ex_limit[LANG] + "<c>" if item_type == "CapsuleEX" else "")
    else:
        item["tr_explain"] = (eval(desc_format_name)[LANG]).format(
            itype = cosmeticsorted_types[item_type][LANG],
            iname = item_name,
            sexlock = "")

    item["tr_explain"] = item["tr_explain"].translate(chartable[LANG])
    
    return 0

def translate_ncosmeticsorted_desc(item, file_name, name_prefix):
    item_name = ""

    # Decide what name we're working with
    if TRANS_ALL:
        item_name = item["tr_text"] or item["jp_text"]
    else:
        if item["tr_text"] == "":
            # No translated name so skip this one (except CN)
            if LANG != 3:
                return -1
            # No translated name so copy the JP name (for CN)
            else:
                item["tr_text"] = item["jp_text"]
                item_name = item["tr_text"]
        else:
            item_name = item["tr_text"]

    # Tradable items keep the JP name in CN, their translated name is in the green prefix
    item_name = get_item_name(item, name_prefix) or item_name
    
    # Description already present, leave it alone
    if REDO_ALL == False and item["tr_explain"] != "":
        return -2

    # Sort the type.
    item_type = "n"
    if "新しい顔バリエーション" in item["jp_explain"]:
        item_type = "Facetype"
    elif "新しいヘッドパーツ" in item["jp_explain"]:
        item_type = "Headparts"
    elif "・ボディ" in item["jp_text"]:
        item_type = "Bodyparts"
    elif "・アーム" in item["jp_text"]:
        item_type = "Armparts"
    elif "・レッグ" in item["jp_text"]:
        item_type = "Legparts"
    elif "パートナーカード（ＰＣ）" in item["jp_explain"]:
        item_type = "Personalcard"
    
    # Some parts will change the posture.
    weaponposition = False
    if "武器の構え位置自動調整" in item["jp_explain"]:
        weaponposition = True
    
    # Translate the description.
    if item_type == "Personalcard":
        # Need to expand if needed
        return -1
    else: 
        item["tr_explain"] = (ndesc_n_formats[LANG] + "{weaponposture}").format(
            itype = cosmeticsorted_types[item_type][LANG],
            # Ugly hack
            a = "" if item_type.endswith("s") else "a ",
            iname = item_name,
            weaponposture = "\n<yellow>" + weapon_posture[LANG] + "<c>" if weaponposition == True else "")

    item["tr_explain"] = item["tr_explain"].translate(chartable[LANG])
    
    return 0

cosmeticsorted_file_names = [
    "FacePattern",
    "Stack_ArmPartsF",
    "Stack_BodyPartsF",
    "Stack_LegPartsF",
    "Stack_ArmPartsM",
    "Stack_BodyPartsM",
    "Stack_LegPartsM",
    "Stack_DeviceHT",
    "Stack_ElementCapsule",
    "Stack_Headparts"
    ]

cosmeticsorted_types = {
    "Head": ["head", "헤드 파츠", "голова", "頭部"],
    "Facetype": ["face type", "얼굴 바리에이션", "тип лица", "臉部類型"],
    "Headparts": ["head parts", "헤드 파츠", "части головы", "頭部部件"],
    "Bodyparts": ["body parts", "바디 파츠", "части тела", "身體部件"],
    "Armparts": ["arm parts", "암 파츠", "части рук", "臂部部件"],
    "Legparts": ["leg parts", "레그 파츠", "части ног", "腿部部件"]
    }

for file_name in cosmeticsorted_file_names:
    items_file_name = "Item_" + file_name + ".txt"
    
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
        tr_text = item["tr_text"]
        fill_cn_name(item)
        name_prefix = split_name_prefix(item)
        problem = translate_ncosmeticsorted_desc(item, file_name, name_prefix) if "選択可能になる。" in item["jp_explain"] or item["jp_explain"] == "" else translate_cosmeticsorted_desc(item, file_name, name_prefix)
        item["tr_explain"] = name_prefix + item["tr_explain"]
        unfill_cn_name(item, tr_text)

        if problem == 0:
            print("\tTranslated description for {0}".format(item["tr_text"] or item["jp_text"]))
            newtranslations = True

    if newtranslations == False:
        print("\tNo new translations.")
    
    print("}")

    items_file = codecs.open(os.path.join(json_loc, items_file_name),
                             mode = 'w', encoding = 'utf-8')
    json.dump(items, items_file, ensure_ascii=False, indent="\t", sort_keys=False)
    items_file.write("\n")
    items_file.close()

####################################################################################################

# Helpers for the sections below

# Half width numbers for the captured values (the CN chartable leaves them alone).
# Full width spaces are kept as they are.
def to_halfwidth(text):
    text = "　".join(part.translate(chartable[0]) for part in text.split("　"))
    return text.replace("＃", "#").replace("％", "%")

# Translate the values captured from a description.
# Values with a dictionary are looked up, the rest are made half width.
# Returns None if a value isn't in its dictionary.
def translate_values(values, value_names):
    for key, value in values.items():
        value = value or ""

        if key in value_names:
            # Keys are looked up as they are, then in half width
            if value not in value_names[key]:
                value = to_halfwidth(value)
            if value not in value_names[key]:
                return None
            values[key] = value_names[key][value][LANG]
        else:
            values[key] = to_halfwidth(value)

    return values

# Take a part of the description from the item's name, translated as the name is
# (or left in JP if the name isn't translated).
# jp_pattern captures the part in the JP name, patterns ([EN, KO, RU, CN]) in the translated name,
# the groups that matched joined together. An empty pattern means names in that language
# don't hold the part.
# Returns None if the part can't be taken from the name.
def get_name_part(item, name_prefix, jp_pattern, patterns, jp_part):
    jp_match = regex.fullmatch(jp_pattern, item["jp_text"])
    if jp_match is None or "".join(group for group in jp_match.groups() if group) != jp_part:
        return None

    name = get_item_name(item, name_prefix)
    if name is None:
        return jp_part

    if patterns[LANG] == "":
        return None

    match = regex.fullmatch(patterns[LANG], name)
    if match is None:
        return None

    return "".join(group for group in match.groups() if group)

# Ordinal numbers, used in names of anniversary items
name_ordinals = {
    "1": ["1st", "", "", "1"],
    "2": ["2nd", "", "", "2"],
    "3": ["3rd", "", "", "3"],
    "4": ["4th", "", "", "4"],
    "5": ["5th", "", "", "5"],
    "6": ["6th", "", "", "6"],
    "7": ["7th", "", "", "7"],
    "8": ["8th", "", "", "8"],
    "9": ["9th", "", "", "9"],
    "10": ["10th", "", "", "10"],
    "11": ["11th", "", "", "11"],
    "12": ["12th", "", "", "12"],
    "13": ["13th", "", "", "13"],
    "14": ["14th", "", "", "14"],
    "15": ["15th", "", "", "15"],
    "16": ["16th", "", "", "16"],
    "17": ["17th", "", "", "17"],
    "18": ["18th", "", "", "18"],
    "19": ["19th", "", "", "19"],
    "20": ["20th", "", "", "20"],
    "21": ["21st", "", "", "21"],
    "22": ["22nd", "", "", "22"],
    "23": ["23rd", "", "", "23"],
    "24": ["24th", "", "", "24"],
    "25": ["25th", "", "", "25"]
    }

# Translate the name of an item with the patterns, formats and value dictionaries of its file.
# Tradable items keep the JP name in CN, their translated name goes in the green prefix instead.
# Returns the name prefix, updated if the name went there.
def translate_name(item, name_prefix, name_patterns, formats_prefix, value_names):
    # Name already present, leave it alone
    if REDO_ALL == False and item["tr_text"] != "" and item["tr_text"] != item["jp_text"]:
        return name_prefix

    # Sort the name format
    name_sort = ""
    for pattern in name_patterns:
        match = regex.fullmatch(pattern, item["jp_text"])
        if match:
            name_sort = name_patterns[pattern]
            break

    if name_sort == "":
        return name_prefix

    # Combine the variable name.
    name_format = eval(formats_prefix + name_sort + "_formats")[LANG]

    # No translation for this language
    if name_format == "":
        return name_prefix

    values = translate_values(match.groupdict(), value_names)

    # A part of the name we can't translate
    if values is None or "" in values.values():
        return name_prefix

    name = name_format.format(**values)

    if LANG == 3 and name_prefix != "":
        return "<green>“{0}”<c>\n".format(name)

    item["tr_text"] = name
    return name_prefix

####################################################################################################

# Translate weapon camos

avatar_weapon_file_names = [
    "AvatarWPN_AssaultRifle",
    "AvatarWPN_Compoundbow",
    "AvatarWPN_DoubleSaber",
    "AvatarWPN_DualBlade",
    "AvatarWPN_GunSlash",
    "AvatarWPN_JetBoots",
    "AvatarWPN_Katana",
    "AvatarWPN_Knuckle",
    "AvatarWPN_Launcher",
    "AvatarWPN_Partizan",
    "AvatarWPN_Rod",
    "AvatarWPN_Sword",
    "AvatarWPN_Tact",
    "AvatarWPN_Talis",
    "AvatarWPN_TwinDagger",
    "AvatarWPN_TwinMachineGun",
    "AvatarWPN_Wand",
    "AvatarWPN_WiredLance"
    ]

avatar_weapon_types = {
    "ソード": ["Sword", "", "", "大劍"],
    "ワイヤードランス": ["Wired Lance", "", "", "自在槍"],
    "パルチザン": ["Partizan", "", "", "長槍"],
    "ツインダガー": ["Twin Daggers", "", "", "雙小劍"],
    "ダブルセイバー": ["Double Saber", "", "", "雙頭劍"],
    "ナックル": ["Knuckles", "", "", "鋼拳"],
    "カタナ": ["Katana", "", "", "拔劍"],
    "デュアルブレード": ["Dual Blades", "", "", "飛翔劍"],
    "ガンスラッシュ": ["Gunslash", "", "", "槍刃"],
    "アサルトライフル": ["Assault Rifle", "", "", "步槍"],
    "ランチャー": ["Launcher", "", "", "大炮"],
    "ツインマシンガン": ["Twin Machineguns", "", "", "雙機槍"],
    "バレットボウ": ["Bullet Bow", "", "", "強弓"],
    "ロッド": ["Rod", "", "", "長杖"],
    "タリス": ["Talis", "", "", "導具"],
    "ウォンド": ["Wand", "", "", "短杖"],
    "ジェットブーツ": ["Jet Boots", "", "", "魔裝腳"],
    "タクト": ["Takt", "", "", "奏具"]
    }

# JP text: ／
avatar_weapon_separators = ["/", "", "", "/"]

# JP text:
    # 装備の見た目を変更する武器迷彩。\n
    # <yellow>※対応：{weapons}<c>
avatar_weapon_formats = [("Weapon camouflage that changes the\n"
                          "appearance of your equipment.\n"
                          "<yellow>Type: {weapons}<c>"),
                         (""),
                         (""),
                         ("變更裝備外觀的武器迷彩。\n"
                          "<yellow>※適用於：{weapons}<c>")]

# JP text:
    # 装備の見た目を変更する武器迷彩。\n
    # <yellow>※対応：{weapons}　ほか<c>
avatar_weapon_others_formats = [("Weapon camouflage that changes the\n"
                                 "appearance of your equipment.\n"
                                 "<yellow>Type: {weapons}\n"
                                 "and others<c>"),
                                (""),
                                (""),
                                ("變更裝備外觀的武器迷彩。\n"
                                 "<yellow>※適用於：{weapons}　等<c>")]

def translate_avatar_weapon_desc(item):
    # Name isn't translated and we're not working in CN, skip this one
    if TRANS_ALL == False and item["tr_text"] == "" and LANG != 3:
        return -1

    # Description already present, leave it alone
    if REDO_ALL == False and item["tr_explain"] != "":
        return -2

    # Weapons are split by "／" and sometimes a line break.
    # A few descriptions are missing their closing <c>, one has it twice.
    match = regex.fullmatch(r"装備の見た目を変更する武器迷彩。\n<yellow>※対応：(.+?)(　ほか)?(?:<c>)*",
                            item["jp_explain"], flags = regex.S)

    # Old camos only have flavour text, leave them alone
    if match is None:
        return -3

    weapons = [weapon for weapon in regex.split(r"[／\n]", match.group(1)) if weapon != ""]

    for weapon in weapons:
        if weapon not in avatar_weapon_types:
            return -4

    # Sort the description format
    desc_format = avatar_weapon_others_formats if match.group(2) else avatar_weapon_formats

    # No translation for this language
    if desc_format[LANG] == "":
        return -1

    # Translate the description.
    item["tr_explain"] = desc_format[LANG].format(
        weapons = avatar_weapon_separators[LANG].join(avatar_weapon_types[weapon][LANG] for weapon in weapons))

    return 0

for file_name in avatar_weapon_file_names:
    items_file_name = "Item_" + file_name + ".txt"

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
        tr_text = item["tr_text"]
        fill_cn_name(item)
        name_prefix = split_name_prefix(item)
        problem = translate_avatar_weapon_desc(item)
        item["tr_explain"] = name_prefix + item["tr_explain"]
        unfill_cn_name(item, tr_text)

        if problem == 0:
            print("\tTranslated description for {0}".format(item["tr_text"] or item["jp_text"]))
            newtranslations = True
        elif problem == -4:
            print("\t{0} has a new kind of description".format(item["tr_text"] or item["jp_text"]))

    if newtranslations == False:
        print("\tNo new translations.")

    print("}")

    items_file = codecs.open(os.path.join(json_loc, items_file_name),
                             mode = 'w', encoding = 'utf-8')
    json.dump(items, items_file, ensure_ascii=False, indent="\t", sort_keys=False)
    items_file.write("\n")
    items_file.close()

####################################################################################################

# Translate boosts

boost_duration_units = {
    "分間": ["minutes", "", "", "分"],
    "時間": ["hours", "", "", "小時"],
    "日間": ["days", "", "", "日"]
    }

boost_targets = {
    "レアドロップ倍率": ["Rare Drop Rate", "", "", "稀有道具掉落率"],
    "獲得経験値": ["EXP gained", "", "", "獲得經驗值"],
    "獲得N-メセタ": ["N-Meseta earned", "", "", "獲得N-美賽達"],
    "獲得N-メセタ、獲得経験値、\nレアドロップ倍率": ["EXP/RDR/N-Meseta", "", "", "獲得N-美賽達、獲得經驗值、\n稀有道具掉落率"],
    "獲得経験値、\nレアドロップ倍率": ["EXP and Rare Drop Rate", "", "", "獲得經驗值、\n稀有道具掉落率"]
    }

boost_notes = {
    # JP text: ※他ブーストアイテムと効果累積
    "\n<yellow>※他ブーストアイテムと効果累積<c>": ["\n<yellow>※Stacks with normal boosts<c>", "", "", "\n<yellow>※與其他增益道具積累效果<c>"],
    # JP text: ※ログアウト中も効果時間減少
    "\n<yellow>※ログアウト中も効果時間減少<c>": ["\n<yellow>※Timer counts down while logged out<c>", "", "", "\n<yellow>※登出期間也會減少效果時間<c>"]
    }

# JP text: ※{event}イベント期間限定
boost_event_formats = ["\n<yellow>※Only applies during {event}<c>", "", "", "\n<yellow>※{event}活動期間限定<c>"]

boost_value_names = {
    "unit": boost_duration_units,
    "target": boost_targets
    }

# Parts of the description that come from the item's name:
# (value, pattern in the JP name, patterns in the translated name)
boost_name_parts = {
    # {event}Ｓポイント＋{p}%
    "seasonal": ("event", r"(.+?)Ｓポイント[＋+].+",
                 [r"(.+?) (?:SP|S Point) ?[＋+].+", r"", r"", r"(.+?)季節點數[＋+].+"]),
    # 追加{item}＋{k}
    "drop": ("item", r"追加(.+?)[＋+]\d+",
             [r"", r"", r"", r"追加(.+?)[＋+]\d+"])
    }

# JP text:
    # 使用してから<yellow>{n}{unit}<c>\n
    # {target}が<yellow>{p}%アップ<c>する。{notes}
boost_desc_ngs_formats = [("Boosts {target} by <yellow>{p}%<c>\n"
                           "for <yellow>{n} {unit}<c> after use.{notes}"),
                          (""),
                          (""),
                          ("在使用後<yellow>{n}{unit}內<c>\n"
                           "<yellow>提升{p}%<c>{target}。{notes}")]

# JP text:
    # 使用してから<yellow>{n}{unit}<c>\n
    # 低温ダメージ耐性が<yellow>{p}%アップ<c>する。{notes}
boost_desc_cold_formats = [("Grants Cold Damage Resistance by\n"
                            "<yellow>{p}%<c> for <yellow>{n} {unit}<c> upon use.{notes}"),
                           (""),
                           (""),
                           ("在使用後<yellow>{n}{unit}內<c>\n"
                            "<yellow>提升{p}%<c>低溫傷害抗性。{notes}")]

# JP text:
    # 使用してから<yellow>{n}{unit}<c>\n
    # 獲得ジェネシスポイントが\n
    # <yellow>{p}%アップ<c>する。{notes}
boost_desc_genesis_formats = [("Boosts Genesis Points earned by\n"
                               "<yellow>{p}%<c> for <yellow>{n} {unit}<c>.{notes}"),
                              (""),
                              (""),
                              ("在使用後<yellow>{n}{unit}內<c>\n"
                               "<yellow>提升{p}%<c>獲得創世點數。{notes}")]

# JP text:
    # 使用してから<yellow>{n}分間<c>、エネミー撃破時の\n
    # 獲得シーズナルポイントが<yellow>{p}%アップ<c>。{notes}\n
    # <yellow>※{event}イベント期間限定<c>
boost_desc_seasonal_formats = [("Boosts Seasonal Points from killing\n"
                                "enemies by <yellow>{p}%<c> for <yellow>{n} minutes<c>.{notes}{event}"),
                               (""),
                               (""),
                               ("在使用後<yellow>{n}分內<c>，<yellow>提升{p}%<c>\n"
                                "擊敗敵人時獲得的季節點數。{notes}{event}")]

# JP text:
    # レアドロップ上昇のブーストアイテム。\n
    # 使用してから【{n}分】の間だけ\n
    # レアドロップの倍率を{p}％アップ。
boost_desc_raredrop_formats = [("Boosts Rare Drop Rate by {p}%.\n"
                                "Duration lasts for {n} minutes\n"
                                "on the field."),
                               (""),
                               (""),
                               ("提升稀有道具掉落率的增益道具。\n"
                                "僅在使用後【{n}分】內\n"
                                "提升{p}%稀有道具掉落率。")]

# JP text:
    # 獲得経験値上昇のブーストアイテム。\n
    # 使用してから【{n}分】の間だけ\n
    # 獲得経験値を{p}％アップさせる。
boost_desc_exp_formats = [("Boosts EXP gained by {p}%.\n"
                           "Duration lasts for {n} minutes\n"
                           "on the field."),
                          (""),
                          (""),
                          ("提升獲得經驗値的增益道具。\n"
                           "僅在使用後【{n}分】內\n"
                           "提升{p}%獲得經驗値。")]

# JP text:
    # 獲得メセタ上昇のブーストアイテム。\n
    # 使用してから【{n}分】の間だけ\n
    # 獲得メセタを{p}％アップさせる。
boost_desc_meseta_formats = [("Boosts Meseta dropped by {p}%.\n"
                              "Duration lasts for {n} minutes\n"
                              "on the field."),
                             (""),
                             (""),
                             ("提升獲得美賽達的增益道具。\n"
                              "僅在使用後【{n}分】內\n"
                              "提升{p}%獲得美賽達。")]

# JP text:
    # 三種複合のブーストアイテム。\n
    # 獲得メセタ、経験値、レアドロップが\n
    # {p}％アップ。
boost_desc_tri_formats = [("Boosts three items.\n"
                           "Meseta boost, EXP gained and\n"
                           "Rare Drop Rate +{p}%."),
                          (""),
                          (""),
                          ("三項複合的增益道具。\n"
                           "提升{p}%\n"
                           "獲得美賽達、經驗値、稀有道具掉落率。")]

# JP text:
    # 三種複合のブーストアイテム。\n
    # 獲得メセタ、経験値、レアドロップが\n
    # 【{n}分】の間だけ{p}％アップ。
boost_desc_tri_timed_formats = [("Boost item that boosts Rare Drop\n"
                                 "Rate, Meseta, and EXP by {p}%.\n"
                                 "Lasts {n} minutes."),
                                (""),
                                (""),
                                ("三項複合的增益道具。\n"
                                 "僅在【{n}分】內提升{p}%\n"
                                 "獲得美賽達、經驗値、稀有道具掉落率。")]

# JP text:
    # 三種複合のブーストアイテム。\n
    # レアドロップの倍率が{a}％アップ。\n
    # 獲得メセタ、経験値が{b}％アップ。
boost_desc_tri_raredrop_formats = [("Boosts three items.\n"
                                    "Rare Drop Rate +{a}%\n"
                                    "Meseta and EXP gained +{b}%."),
                                   (""),
                                   (""),
                                   ("三項複合的增益道具。\n"
                                    "提升{a}%稀有道具掉落率。\n"
                                    "提升{b}%獲得美賽達、經驗値。")]

# JP text:
    # 三種複合のブーストアイテム。\n
    # 獲得経験値が{a}％アップ。\n
    # 獲得メセタ、レアドロップが{b}％アップ。
boost_desc_tri_exp_formats = [("Boosts three items.\n"
                               "EXP gained +{a}%\n"
                               "Meseta and Rare Drop Rate +{b}%."),
                              (""),
                              (""),
                              ("三項複合的增益道具。\n"
                               "提升{a}%獲得經驗値。\n"
                               "提升{b}%獲得美賽達、稀有道具掉落率。")]

# JP text:
    # 三種複合のブーストアイテム。\n
    # 獲得メセタが{a}％アップ。\n
    # 経験値、レアドロップが{b}％アップ。
boost_desc_tri_meseta_formats = [("Boosts three items.\n"
                                  "Meseta boost +{a}%\n"
                                  "Rare Drop Rate and EXP +{b}%."),
                                 (""),
                                 (""),
                                 ("三項複合的增益道具。\n"
                                  "提升{a}%獲得美賽達。\n"
                                  "提升{b}%獲得經驗値、稀有道具掉落率。")]

# JP text:
    # 「{item}」が対象。\n
    # 使用してから【{n}分】の間だけ\n
    # 対象アイテムのドロップ数を＋{k}する。
boost_desc_drop_formats = [("Target item \"{item}\".\n"
                            "[{n} Min]Increases the target\n"
                            "item drop by +{k}."),
                           (""),
                           (""),
                           ("對象為「{item}」。\n"
                            "僅在使用後【{n}分】內\n"
                            "使對象道具的掉落數量+{k}。")]

boost_desc_patterns = {
    r"使用してから<yellow>(?P<n>\d+)(?P<unit>分間|時間|日間)<c>\n低温ダメージ耐性が\n?<yellow>(?P<p>\d+)[%％]アップ<c>する。(?P<notes>(?:\n<yellow>※[^\n]*<c>)*)": "cold",
    r"使用してから<yellow>(?P<n>\d+)(?P<unit>分間|時間|日間)<c>\n獲得ジェネシスポイントが\n?<yellow>(?P<p>\d+)[%％]アップ<c>する。(?P<notes>(?:\n<yellow>※[^\n]*<c>)*)": "genesis",
    r"使用してから<yellow>(?P<n>\d+)(?P<unit>分間|時間|日間)<c>\n(?P<target>.+?)が\n?<yellow>(?P<p>\d+)[%％]アップ<c>する。(?P<notes>(?:\n<yellow>※[^\n]*<c>)*)": "ngs",
    r"使用してから<yellow>(?P<n>\d+)分間<c>、エネミー撃破時の\n獲得シーズナルポイントが\n?<yellow>(?P<p>\d+)[%％]アップ<c>(?:する)?。(?P<notes>(?:\n<yellow>※ログアウト中も効果時間減少<c>)?)\n<yellow>※?(?P<event>.+?)(?:イベント期間)?限定<c>": "seasonal",
    r"レアドロップ上昇のブーストアイテム。\n使用してから【(?P<n>\d+)分】の間だけ\nレアドロップの倍率を(?P<p>\d+)％アップ。": "raredrop",
    r"獲得経験値上昇のブーストアイテム。\n使用してから【(?P<n>\d+)分】の間だけ\n獲得経験値を(?P<p>\d+)％アップさせる。": "exp",
    r"獲得メセタ上昇のブーストアイテム。\n使用してから【(?P<n>\d+)分】の間だけ\n獲得メセタを(?P<p>\d+)％アップさせる。": "meseta",
    r"三種複合のブーストアイテム。\n獲得メセタ、経験値、レアドロップが\n(?P<p>\d+)％アップ。": "tri",
    r"三種複合のブーストアイテム。\n獲得メセタ、経験値、レアドロップが\n【(?P<n>\d+)分】の間だけ(?P<p>\d+)％アップ。": "tri_timed",
    r"三種複合のブーストアイテム。\nレアドロップの倍率が(?P<a>\d+)％アップ。\n獲得メセタ、経験値が(?P<b>\d+)％アップ。": "tri_raredrop",
    r"三種複合のブーストアイテム。\n獲得経験値が(?P<a>\d+)％アップ。\n獲得メセタ、レアドロップが(?P<b>\d+)％アップ。": "tri_exp",
    r"三種複合のブーストアイテム。\n獲得メセタが(?P<a>\d+)％アップ。\n経験値、レアドロップが(?P<b>\d+)％アップ。": "tri_meseta",
    r"「(?P<item>.+)」が対象。\n使用してから【(?P<n>\d+)分】の間だけ\n対象アイテムのドロップ数を＋(?P<k>\d+)する。": "drop"
    }

# Boost names

boost_name_targets = {
    "レアドロップ倍率": ["Rare Drop Rate", "", "", "稀有道具掉落率"],
    "獲得経験値": ["Experience Gained", "", "", "獲得經驗值"],
    "獲得メセタ": ["Meseta Boost", "", "", "獲得美賽達"],
    "トライブースト": ["Tri-Boost", "", "", "三項增益"]
    }

boost_name_ex_targets = {
    "レアドロップ倍率": ["Rare Drop Rate", "", "", "稀有道具掉落率"],
    "獲得経験値": ["Experience Gained", "", "", "獲得經驗値"],
    "獲得メセタ": ["Meseta Boost", "", "", "獲得美賽達"],
    "トライブースト": ["Tri-Boost", "", "", "三項增益"]
    }

boost_name_old_targets = {
    "レアドロップ倍率": ["Rare Drop Rate Boost", "", "", "稀有道具掉落率"],
    "獲得経験値": ["Experience Gained", "", "", "獲得經驗値"],
    "獲得メセタ": ["Meseta Boost", "", "", "獲得美賽達"],
    "トライブースト": ["Tri-Boost", "", "", "三項增益"],
    "低温ダメージ耐性": ["Cold Damage Resistance", "", "", "低溫傷害抗性"],
    "獲得ジェネシスポイント": ["Genesis Points Earned", "", "", "獲得創世點數"]
    }

boost_name_events = {
    "スプリング": ["Spring", "", "", "春季"],
    "オータム": ["Autumn", "", "", "秋季"],
    "ハロウィン": ["Halloween", "", "", "萬聖夜"],
    "ウィンター": ["Winter", "", "", "冬季"],
    "お月見": ["Otsukimi", "", "", "賞月"],
    "超・創世祭": ["Super Genesis Festival", "", "", "超·創世祭"],
    "超・星譚祭": ["Super Origin Festival", "", "", "超·星譚祭"],
    "超・夢幻祭": ["Super Phantasy Festival", "", "", "超·夢幻祭"],
    "真・超星譚祭": ["Shin Super Origin Festival", "", "", "真·超星譚祭"]
    }

boost_name_drop_items = {
    "エクスキューブ": ["Cube", "", "", "極限方塊"],
    "バッヂ２０２０": ["Badge 2020", "", "", ""]
    }

boost_name_value_names = {
    "target": boost_name_targets,
    "ex_target": boost_name_ex_targets,
    "old_target": boost_name_old_targets,
    "event": boost_name_events,
    "n": name_ordinals,
    "item": boost_name_drop_items
    }

# JP text: N-{target}＋{p}%
boost_name_ngs_formats = ["N-{target} +{p}%", "", "", "N-{target}+{p}%"]

# JP text: N-{target}[{t}{unit}]＋{p}%
boost_name_ngs_timed_formats = ["N-{target} [{t}{unit}] +{p}%", "", "", "N-{target}[{t}{unit}]+{p}%"]

# JP text: N-EX{target}＋{p}%
boost_name_ngs_ex_formats = ["N-EX {target} +{p}%", "", "", "N-EX{target}+{p}%"]

# JP text: N-EX{target}[{t}{unit}]＋{p}%
boost_name_ngs_ex_timed_formats = ["N-EX {target} [{t}{unit}] +{p}%", "", "", "N-EX{target}[{t}{unit}]+{p}%"]

# JP text: ＥＸ{target}＋{p}％
boost_name_ex_formats = ["EX {ex_target} +{p}%", "", "", "EX{ex_target}+{p}%"]

# JP text: {target}＋{p}％
boost_name_old_formats = ["{old_target} +{p}%", "", "", "{old_target}+{p}%"]

# JP text: {target}＋{p}％Ｓ
boost_name_old_s_formats = ["{old_target} +{p}% S", "", "", "{old_target}+{p}%S"]

# JP text: {event}Ｓポイント＋{p}%
boost_name_seasonal_formats = ["{event} SP +{p}%", "", "", "{event}季節點數+{p}%"]

# JP text: {event}'{year}Ｓポイント＋{p}%
boost_name_seasonal_year_formats = ["{event} '{year} SP +{p}%", "", "", "{event}'{year}季節點數+{p}%"]

# JP text: 『NGS』{n}周年記念Ｓポイント＋{p}%
boost_name_seasonal_ngs_formats = ["[NGS] {n} Anniversary SP +{p}%", "", "", "『NGS』{n}週年紀念季節點數+{p}%"]

# JP text: 『PSO2』{n}周年Ｓポイント＋{p}%
boost_name_seasonal_pso2_formats = ["[PSO2] {n} Anniv. SP +{p}%", "", "", "『PSO2』{n}週年季節點數+{p}%"]

# JP text: 追加{item}＋{k}
boost_name_drop_formats = ["Extra {item} +{k}", "", "", "追加{item}+{k}"]

boost_name_patterns = {
    # More specific patterns first
    r"N-EX(?P<target>[^\[＋]+)\[(?P<t>\d+)(?P<unit>[hm])\]＋(?P<p>\d+)[%％]": "ngs_ex_timed",
    r"N-EX(?P<target>[^\[＋]+)＋(?P<p>\d+)[%％]": "ngs_ex",
    r"N-(?P<target>[^\[＋]+)\[(?P<t>\d+)(?P<unit>[hm])\]＋(?P<p>\d+)[%％]": "ngs_timed",
    r"N-(?P<target>[^\[＋]+)＋(?P<p>\d+)[%％]": "ngs",
    r"ＥＸ(?P<ex_target>[^＋]+)＋(?P<p>\d+)[%％]": "ex",
    r"『NGS』(?P<n>\d+)周年記念Ｓポイント＋(?P<p>\d+)[%％]": "seasonal_ngs",
    r"『PSO2』(?P<n>\d+)周年Ｓポイント＋(?P<p>\d+)[%％]": "seasonal_pso2",
    r"(?P<event>[^']+)'(?P<year>\d+(?:-'\d+)?)Ｓポイント＋(?P<p>\d+)[%％]": "seasonal_year",
    r"(?P<event>[^']+)Ｓポイント＋(?P<p>\d+)[%％]": "seasonal",
    r"追加(?P<item>.+?)＋(?P<k>\d+)": "drop",
    r"(?P<old_target>[^＋]+)＋(?P<p>\d+)[%％]Ｓ": "old_s",
    r"(?P<old_target>[^＋]+)＋(?P<p>\d+)[%％]": "old"
    }

def translate_boost_name(item, name_prefix):
    return translate_name(item, name_prefix, boost_name_patterns, "boost_name_", boost_name_value_names)

def translate_boost_desc(item, name_prefix):
    # Name isn't translated and we're not working in CN, skip this one
    if TRANS_ALL == False and item["tr_text"] == "" and LANG != 3:
        return -1

    # Description already present, leave it alone
    if REDO_ALL == False and item["tr_explain"] != "":
        return -2

    # Sort the description format
    desc_sort = ""
    for pattern in boost_desc_patterns:
        match = regex.fullmatch(pattern, item["jp_explain"], flags = regex.S)
        if match:
            desc_sort = boost_desc_patterns[pattern]
            break

    if desc_sort == "":
        return -4

    # No translation for this language
    if eval("boost_desc_" + desc_sort + "_formats")[LANG] == "":
        return -1

    values = translate_values(match.groupdict(), boost_value_names)

    if values is None:
        return -4

    # Notes after the description
    if "notes" in values:
        notes = regex.findall(r"\n<yellow>[^\n]*<c>", match.group("notes"))

        for note in notes:
            if note not in boost_notes:
                return -4

        values["notes"] = "".join(boost_notes[note][LANG] for note in notes)

    # Parts that come from the item's name
    if desc_sort in boost_name_parts:
        key, jp_pattern, patterns = boost_name_parts[desc_sort]
        values[key] = get_name_part(item, name_prefix, jp_pattern, patterns, match.group(key))

        if values[key] is None:
            return -4

    # Seasonal events
    if desc_sort == "seasonal":
        values["event"] = boost_event_formats[LANG].format(event = values["event"])

    # Combine the variable name.
    desc_format_name = "boost_desc_" + desc_sort + "_formats"

    # Translate the description.
    item["tr_explain"] = eval(desc_format_name)[LANG].format(**values)

    return 0

try:
    items_file = codecs.open(os.path.join(json_loc, "Item_Stack_Boost.txt"),
                             mode = 'r', encoding = 'utf-8')
except FileNotFoundError:
    print("\tItem_Stack_Boost.txt not found.")

items = json.load(items_file)
print("Item_Stack_Boost.txt loaded. {")

items_file.close()

newtranslations = False

for item in items:
    tr_text = item["tr_text"]
    fill_cn_name(item)
    name_prefix = split_name_prefix(item)
    name_prefix = translate_boost_name(item, name_prefix)
    problem = translate_boost_desc(item, name_prefix)
    item["tr_explain"] = name_prefix + item["tr_explain"]
    unfill_cn_name(item, tr_text)

    if problem == 0:
        print("\tTranslated description for {0}".format(item["tr_text"] or item["jp_text"]))
        newtranslations = True
    elif problem == -4:
        print("\t{0} has a new kind of description".format(item["tr_text"] or item["jp_text"]))

if newtranslations == False:
    print("\tNo new translations.")

print("}")

items_file = codecs.open(os.path.join(json_loc, "Item_Stack_Boost.txt"),
                         mode = 'w', encoding = 'utf-8')
json.dump(items, items_file, ensure_ascii=False, indent="\t", sort_keys=False)
items_file.write("\n")
items_file.close()

####################################################################################################

# Translate gacha trade passes. These have no JP description, so go by the name.

# JP text unavailable.
gacha_trade_pass_formats = [("During the target scratch, one gift\n"
                             "can be selected and exchanged.\n"
                             "<yellow>Target Scratch:\n"
                             "{gacha}<c>"),
                            (""),
                            (""),
                            ("可在對象轉蛋的販賣期間\n"
                             "自選交換1件獎品的票券。\n"
                             "<yellow>※對象轉蛋：\n"
                             "　{gacha}<c>")]

# {gacha}スペシャルセレクト券, {gacha}SPセレクト券
gacha_trade_pass_select_formats = ["{gacha} Scratch", "", "", "{gacha}轉蛋"]

# {gacha}セレクト券Vol.{n}
gacha_trade_pass_treasure_formats = ["{gacha} Scratch Vol.{n}", "", "", "{gacha}轉蛋{n}"]

# {gacha}景品交換券
gacha_trade_pass_exchange_formats = ["{gacha} Prize Exchange", "", "", "{gacha}"]

gacha_trade_pass_patterns = {
    r".*(?:スペシャル|SP)セレクト券": "select",
    r"トレジャーセレクト券Vol\.\d+": "treasure",
    r".+景品交換券": "exchange"
    }

# The gacha in the name of the pass: (pattern in the JP name, patterns in the translated name)
gacha_trade_pass_gacha_patterns = {
    "select": (r"(?P<gacha>.+?)セレクト券",
               [r"(?P<gacha>.+?) Select Ticket", r"", r"", r"(?P<gacha>.+?)自選券"]),
    "treasure": (r"(?P<gacha>.+?)セレクト券Vol\.(?P<n>\d+)",
                 [r"(?P<gacha>.+?) Select Ticket Vol\.(?P<n>\d+)", r"", r"", r"(?P<gacha>.+?)自選券Vol\.(?P<n>\d+)"]),
    "exchange": (r"(?P<gacha>.+?)景品交換券",
                 [r"(?P<gacha>.+?) Exchange Ticket", r"", r"", r"(?P<gacha>.+?)獎品交換券"])
    }

# Names of scratches, shared by gacha trade passes and paid passes

# Seasonal scratches, followed by their year
scratch_name_events = {
    "春": ["Spring", "", "", "春"],
    "秋": ["Autumn", "", "", "秋"],
    "冬": ["Winter", "", "", "冬"],
    "ハロウィン": ["Halloween", "", "", "萬聖夜"],
    "超・創世祭": ["Super Genesis", "", "", "超·創世祭"],
    "超・星譚祭": ["Super Star", "", "", "超·星譚祭"],
    "超・夢幻祭": ["Super Phantasy", "", "", "超·夢幻祭"],
    "真・超星譚祭": ["Shin Super Star", "", "", ""]
    }

# Other scratches
scratch_name_series = {
    "アニバーサリー": ["Anniversary", "", "", "週年"],
    "オラクルメモリーズ": ["Oracle Memories", "", "", "神諭回憶"],
    "超・夢幻祭": ["Super Phantasy Festival", "", "", "超·夢幻祭"],
    "ソニックコラボ": ["Sonic Collab", "", "", "索尼克聯動"],
    "ずんだもんコラボ": ["Zundamon Collab", "", "", ""],
    "ドン・キホーテコラボ": ["Don Quijote Collab", "", "", ""]
    }

scratch_name_kinds = {
    "スペシャル": ["Special", "", "", "特殊"],
    "SP": ["SP", "", "", "SP"]
    }

scratch_name_games = {
    "NGS": ["NGS", "", "", "NGS"],
    "PSO2": ["PSO2", "", "", "PSO2"]
    }

# Gacha trade pass names

gacha_trade_pass_name_series = {
    "サンクフル": ["Thankful", "", "", "感謝"],
    "メモリーズ": ["Memories", "", "", "回憶"]
    }

gacha_trade_pass_name_value_names = {
    "event": scratch_name_events,
    "series": scratch_name_series,
    "kind": scratch_name_kinds,
    "game": scratch_name_games,
    "n": name_ordinals,
    "prize_series": gacha_trade_pass_name_series
    }

# JP text: {event}'{year}{kind}セレクト券
gacha_trade_pass_name_select_year_formats = ["{event} '{year} {kind} Select Ticket", "", "", "{event}'{year}{kind}自選券"]

# JP text: {series}{kind}セレクト券
gacha_trade_pass_name_select_series_formats = ["{series} {kind} Select Ticket", "", "", "{series}{kind}自選券"]

# JP text: 『{game}』{n}周年{kind}セレクト券
gacha_trade_pass_name_select_anniv_formats = ["{game} {n} Anniv. {kind} Select Ticket", "", "", "『{game}』{n}週年{kind}自選券"]

# JP text: {kind}セレクト券
gacha_trade_pass_name_select_formats = ["{kind} Select Ticket", "", "", "{kind}自選券"]

# JP text: トレジャーセレクト券Vol.{n}
gacha_trade_pass_name_treasure_formats = ["Treasure Select Ticket Vol.{v}", "", "", "寶物自選券Vol.{v}"]

# JP text: {n}周年{series}景品交換券
gacha_trade_pass_name_exchange_formats = ["{n} Anniv. {prize_series} Exchange Ticket", "", "", "{n}週年{prize_series}獎品交換券"]

# JP text: {n}周年{series}{month}景品交換券
gacha_trade_pass_name_exchange_month_formats = ["", "", "", "{n}週年{prize_series}{month}獎品交換券"]

gacha_trade_pass_name_patterns = {
    r"(?P<event>[^']+)'(?P<year>\d+(?:-'\d+)?)(?P<kind>スペシャル|SP)セレクト券": "select_year",
    r"『(?P<game>NGS|PSO2)』(?P<n>\d+)周年(?P<kind>スペシャル|SP)セレクト券": "select_anniv",
    r"(?P<kind>スペシャル|SP)セレクト券": "select",
    r"(?P<series>.+?)(?P<kind>スペシャル|SP)セレクト券": "select_series",
    r"トレジャーセレクト券Vol\.(?P<v>\d+)": "treasure",
    r"(?P<n>\d+)周年(?P<prize_series>サンクフル|メモリーズ)景品交換券": "exchange",
    r"(?P<n>\d+)周年(?P<prize_series>サンクフル|メモリーズ)(?P<month>[A-Z][a-z]+)景品交換券": "exchange_month"
    }

def translate_gacha_trade_pass_name(item, name_prefix):
    return translate_name(item, name_prefix, gacha_trade_pass_name_patterns, "gacha_trade_pass_name_", gacha_trade_pass_name_value_names)

def translate_gacha_trade_pass_desc(item, name_prefix):
    # Name isn't translated and we're not working in CN, skip this one
    if TRANS_ALL == False and item["tr_text"] == "" and LANG != 3:
        return -1

    # Description already present, leave it alone
    if REDO_ALL == False and item["tr_explain"] != "":
        return -2

    # Sort the pass by its name
    desc_sort = ""
    for pattern in gacha_trade_pass_patterns:
        if regex.fullmatch(pattern, item["jp_text"]):
            desc_sort = gacha_trade_pass_patterns[pattern]
            break

    # No description we know of for the other passes, leave them alone
    if desc_sort == "":
        return -3

    # No translation for this language
    if gacha_trade_pass_formats[LANG] == "":
        return -1

    # Take the gacha from the item's name, or the JP name if it isn't translated
    jp_pattern, patterns = gacha_trade_pass_gacha_patterns[desc_sort]
    name = get_item_name(item, name_prefix)

    if name is None:
        match = regex.fullmatch(jp_pattern, item["jp_text"])
    elif patterns[LANG] != "":
        match = regex.fullmatch(patterns[LANG], name)
    else:
        match = None

    if match is None:
        return -4

    # Combine the variable name.
    gacha_format_name = "gacha_trade_pass_" + desc_sort + "_formats"

    # Translate the description.
    item["tr_explain"] = gacha_trade_pass_formats[LANG].format(
        gacha = eval(gacha_format_name)[LANG].format(**match.groupdict()))

    return 0

try:
    items_file = codecs.open(os.path.join(json_loc, "Item_Stack_GachaTradePass.txt"),
                             mode = 'r', encoding = 'utf-8')
except FileNotFoundError:
    print("\tItem_Stack_GachaTradePass.txt not found.")

items = json.load(items_file)
print("Item_Stack_GachaTradePass.txt loaded. {")

items_file.close()

newtranslations = False

for item in items:
    tr_text = item["tr_text"]
    fill_cn_name(item)
    name_prefix = split_name_prefix(item)
    name_prefix = translate_gacha_trade_pass_name(item, name_prefix)
    problem = translate_gacha_trade_pass_desc(item, name_prefix)
    item["tr_explain"] = name_prefix + item["tr_explain"]
    unfill_cn_name(item, tr_text)

    if problem == 0:
        print("\tTranslated description for {0}".format(item["tr_text"] or item["jp_text"]))
        newtranslations = True
    elif problem == -4:
        print("\t{0} has a new kind of description".format(item["tr_text"] or item["jp_text"]))

if newtranslations == False:
    print("\tNo new translations.")

print("}")

items_file = codecs.open(os.path.join(json_loc, "Item_Stack_GachaTradePass.txt"),
                         mode = 'w', encoding = 'utf-8')
json.dump(items, items_file, ensure_ascii=False, indent="\t", sort_keys=False)
items_file.write("\n")
items_file.close()

####################################################################################################

# Translate music discs

# Games in the label of old discs. An empty name keeps the JP abbreviation.
music_game_names = {
    "ＰＳＯ": ["Phantasy Star Online", "", "", ""],
    "ＰＳＯ２": ["Phantasy Star Online 2", "", "", ""],
    "ＰＳＯ２ｅｓ": ["Phantasy Star Online 2 es", "", "", ""],
    "ＰＳＵ": ["Phantasy Star Universe", "", "", ""],
    "ＰＳＰｏ１": ["Phantasy Star Portable", "", "", ""],
    "ＰＳＰｏ２": ["Phantasy Star Portable 2", "", "", ""],
    "ＰＳＰｏ２ｉ": ["Phantasy Star Portable 2 Infinity", "", "", ""],
    "ＰＳＰｏ２ｉＯＳＴ": ["Phantasy Star Portable 2i OST", "", "", ""],
    "ＰＳＺ": ["Phantasy Star Zero", "", "", ""],
    "ＰＳＮｏｖａ": ["Phantasy Star Nova", "", "", ""],
    "ＰＳＯ２ＶＤ": ["PSO2 Vocal Disc", "", "", ""],
    "ＰＳＯ２ＣＳ０１": ["PSO2 Character Song", "", "", ""],
    "ＰＳＯ２ＣＳ０２": ["PSO2 Character Song 2", "", "", ""],
    "ＰＳＯ２ＣＳ０３": ["PSO2 Character Song 3", "", "", ""],
    "ＰＳＯ２ＣＳ０４": ["PSO2 Character Song 4", "", "", ""],
    "ＰＳＯ２ＣＳＢ": ["PSO2 Character Song B", "", "", ""],
    "ＰＳＯ２ＡＮＩ": ["PSO2 the Animation", "", "", ""],
    "ＰＳＯ２ＡＮＩＣＳ": ["PSO2 the Anime Character Song", "", "", ""],
    "ＰＳＯ２ＡＮＩＣＳ２": ["PSO2 the Anime Chara Song 2", "", "", ""],
    "ＰＳＯ２ＡＮＩＣＳＣＢ": ["PSO2 the Anime Chara Song B", "", "", ""],
    "ＰＳＯ２ＣＯＭＩ": ["Pusoni Comic", "", "", ""],
    "ＰＳＯ２ＰＱＭ": ["PSO2 Phantastic QM", "", "", ""],
    "ＰＳＯ２ＥＯ": ["PSO2 Episode Oracle", "", "", ""],
    "ＰＳＯ２ＯＳ": ["PSO2 On Stage", "", "", ""],
    "ＮｉＧＨＴＳ": ["NiGHTS", "", "", ""],
    "ＢＲ": ["Burning Rangers", "", "", ""],
    "ＳＧ": ["Sonic Generations", "", "", ""],
    "ＳＣ５": ["Space Channel 5", "", "", ""],
    "ＳＣ５ｐ２": ["Space Channel 5 Part 2", "", "", ""],
    "ＫＭＳＮ": ["Feel the Magic: XY/XX", "", "", ""],
    "ＡＫＤＫ": ["The Rub Rabbits!", "", "", ""],
    "ＶＡＬ１": ["Valkyria Chronicles", "", "", ""],
    "ＢＬＡＺＥ": ["Blazer Drive", "", "", ""],
    "ＲｏＮ": ["Rise of Nightmares", "", "", ""],
    "ＳＢ": ["Shining Blade", "", "", ""],
    "ＢＥＹＯ": ["Bayonetta", "", "", ""],
    "ＲＨＹＴＨＭ": ["Rhythm Thief", "", "", ""],
    "ＲＹＵ１": ["Yakuza", "", "", ""],
    "ＲＹＵ２": ["Yakuza 2", "", "", ""],
    "ＲＹＵ３": ["Yakuza 3", "", "", ""],
    "ＲＹＵ４": ["Yakuza 4", "", "", ""],
    "ＲＹＵ５": ["Yakuza 5", "", "", ""],
    "ＲＹＵＩ": ["Yakuza Ishin", "", "", ""],
    "ＢＤ": ["Binary Domain", "", "", ""],
    "ＫＣ": ["Kingdom Conquest", "", "", ""],
    "ＥＡ": ["Skies of Arcadia", "", "", ""],
    "ＳＡ２": ["Sonic Adventure 2", "", "", ""],
    "ＳＡＤＸ": ["Sonic Adventure DX", "", "", ""],
    "ＳＣＯ": ["Sonic Colors", "", "", ""],
    "ＳＬＷ": ["Sonic Lost World", "", "", ""],
    "７ＤＲ": ["7th Dragon", "", "", ""],
    "７ＤＲ３": ["7th Dragon III Code: VFD", "", "", ""],
    "ＰＹＯ": ["Puyo Puyo", "", "", ""],
    "ＢＢ": ["Border Break", "", "", ""],
    "ＢＢＣＰ": ["BlazBlue: Chrono Phantasma", "", "", ""],
    "ＭＡＩ": ["maimai", "", "", ""],
    "ＭＪ": ["SEGANET Mahjong MJ", "", "", ""],
    "ＶＯＣＬ": ["Vocaloid", "", "", ""],
    "ＶＯ４": ["Virtual-On Force", "", "", ""],
    "ＶＯＯＴ": ["Virtual-On: Oratorio Tangram", "", "", ""],
    "ＴＶＯ": ["A Certain Magical Virtual-On", "", "", ""],
    "ＳＦＣ": ["Shining Force Cross", "", "", ""],
    "ＤＦＣ": ["Dengeki Bunko: Fighting Climax", "", "", ""],
    "ＳＲ": ["Shining Resonance", "", "", ""],
    "ＰＤＳＳ": ["Panzer Dragoon", "", "", ""],
    "GGXrd": ["Guilty Gear Xrd", "", "", ""],
    "ＳＨＧ": ["Sega Hard Girls", "", "", ""],
    "ＤＡＹ": ["Daytona USA", "", "", ""],
    "ＦＺ": ["Fantasy Zone", "", "", ""],
    "ＡＭＩＧＯ": ["Samba de Amigo", "", "", ""],
    "ＯＲ２": ["OutRun 2", "", "", ""],
    "ＳＫＲ": ["Sakura Wars", "", "", ""],
    "ＳＫＲ２": ["Sakura Wars 2", "", "", ""],
    "ＮＳＫＲ": ["Shin Sakura Wars", "", "", ""],
    "ＰＥＲ５": ["Persona 5", "", "", ""],
    "ＰＥＲ４Ｇ": ["Persona 4 Golden", "", "", ""],
    "ＰＥＲＱ": ["Persona Q", "", "", ""],
    "ＰＥＲＱ２": ["Persona Q2", "", "", ""],
    "Ｐ３Ｄ": ["Persona 3: Dancing in Moonlight", "", "", ""],
    "Ｐ５Ｄ": ["Persona 5: Dancing in Starlight", "", "", ""],
    "ＮＩＥＲ": ["NieR: Automata", "", "", ""],
    "ＤＮＫ": ["Don Quijote", "", "", ""],
    "ＦＡＧＩＲＬ": ["Frame Arms Girl", "", "", ""],
    "ＡＴＬ": ["Atelier", "", "", ""],
    "ＤＯＡ": ["Dead or Alive", "", "", ""],
    "ＹＫＲ": ["Yuzuki Yukari", "", "", ""],
    "ＡＫＲ": ["Kizuna Akari", "", "", ""],
    "ＭＨＦ": ["Monster Hunter Frontier", "", "", ""],
    "ＩＤＬ": ["IDOLA: Phantasy Star Saga", "", "", ""]
    }

# JP text: （曲調変更可）
# Kept in the label for the languages that note it there.
music_old_tune_notes = ["", "", "", "（可變更曲調）"]

# Song titles in the current translation
music_title_patterns = [r"\"(.+)\"", r"", r"", r"『(.+)』"]

# JP text:
    # ジュークボックス用音楽再生ディスク。\n
    # {label}『{title}』{tail}
music_old_formats = [("A music disc for your jukebox.\n"
                      "{label}\"{title}\"{tail}"),
                     (""),
                     (""),
                     ("點唱機專用的音樂播放光盤。\n"
                      "{label}『{title}』{tail}")]

# JP text:
    # ジュークボックス用音楽再生ディスク。\n
    # {label}（曲調変更可）『{title}』{tail}
music_old_tune_formats = [("A multi-track disc for your jukebox.\n"
                           "{label}\"{title}\"{tail}"),
                          (""),
                          (""),
                          ("點唱機專用的音樂播放光盤。\n"
                           "{label}『{title}』{tail}")]

# JP text:
    # 使用すると新しいミュージックが\n
    # 再生可能になるディスク。\n
    # 『{title}』{tail}
music_new_formats = [("A disc that you can use to play new\n"
                      "music tracks.\n"
                      "\"{title}\"{tail}"),
                     (""),
                     (""),
                     ("使用後可以播放新音樂的光盤。\n"
                      "『{title}』{tail}")]

# JP text:
    # 使用すると新しいミュージックが\n
    # 再生可能になるディスク。<yellow>※曲調変更可<c>\n
    # 『{title}』{tail}
music_new_tune_formats = [("A disc that you can use to play new\n"
                           "music tracks. <yellow>※Multiple tracks.<c>\n"
                           "\"{title}\"{tail}"),
                          (""),
                          (""),
                          ("使用後可以播放新音樂的光盤。\n"
                           "<yellow>※可變更曲調<c>\n"
                           "『{title}』{tail}")]

# Abbreviations shared by more than one game, told apart by the JP song title
music_shared_game_names = {
    "ＳＨ": {
        "SONIC HEROES": ["Sonic Heroes", "", "", ""],
        "Shining Hearts": ["Shining Hearts", "", "", ""],
        "風疾る道": ["Shining Hearts", "", "", ""],
        "心に届く詩": ["Shining Hearts", "", "", ""]
        },
    "ＳＡ": {
        "チエノトビラ": ["Shining Arc", "", "", ""],
        "キェル・マーレ・セラ\n～はるかなる故郷へ～": ["Shining Arc", "", "", ""],
        "Open Your Heart": ["Sonic Adventure", "", "", ""],
        "Welcome to Station Square": ["Sonic Adventure", "", "", ""]
        }
    }

# The label of an old disc: the game and the track number.
# Returns None if the game can't be told from its abbreviation and song title.
def translate_music_label(label, jp_title):
    game = regex.match(r"[^\s＃（『]+", label)
    game_names = None

    if game and game.group(0) in music_shared_game_names:
        game_names = music_shared_game_names[game.group(0)].get(jp_title)
        if game_names is None:
            return None
    elif game and game.group(0) in music_game_names:
        game_names = music_game_names[game.group(0)]

    if game_names is not None and game_names[LANG] != "":
        label = game_names[LANG] + label[game.end():]

    return to_halfwidth(label).replace("(曲調変更可)", music_old_tune_notes[LANG])

# Song titles come from the item's name, or the JP title if the name isn't translated.
def translate_music_desc(item, name_prefix):
    # Name isn't translated and we're not working in CN, skip this one
    if TRANS_ALL == False and item["tr_text"] == "" and LANG != 3:
        return -1

    # Description already present, leave it alone
    if REDO_ALL == False and item["tr_explain"] != "":
        return -2

    # Old discs
    match = regex.fullmatch(r"ジュークボックス用音楽再生ディスク。\n(?P<label>.*?)『(?P<title>.+)』(?P<tail>.*)",
                            item["jp_explain"], flags = regex.S)
    if match:
        desc_format = music_old_tune_formats if "（曲調変更可）" in match.group("label") else music_old_formats

        # No translation for this language
        if desc_format[LANG] == "":
            return -1

        # Keep the title of the current translation if there is one
        title = None
        if music_title_patterns[LANG] != "":
            title = regex.search(music_title_patterns[LANG], item["tr_explain"], flags = regex.S)
        title = title.group(1) if title else get_item_name(item, name_prefix) or match.group("title")

        label = translate_music_label(match.group("label"), match.group("title"))

        if label is None:
            return -4

        item["tr_explain"] = desc_format[LANG].format(
            label = label,
            title = title,
            tail = match.group("tail"))

        return 0

    # New discs
    match = regex.fullmatch(r"使用すると新しいミュージックが\n再生可能になるディスク。(?P<tune><yellow>※曲調変更可<c>)?\n『(?P<title>.+)』(?P<tail>.*)",
                            item["jp_explain"], flags = regex.S)
    if match:
        desc_format = music_new_tune_formats if match.group("tune") else music_new_formats

        # No translation for this language
        if desc_format[LANG] == "":
            return -1

        item["tr_explain"] = desc_format[LANG].format(
            title = get_item_name(item, name_prefix) or match.group("title"),
            tail = match.group("tail"))

        return 0

    return -4

try:
    items_file = codecs.open(os.path.join(json_loc, "Item_Stack_Music.txt"),
                             mode = 'r', encoding = 'utf-8')
except FileNotFoundError:
    print("\tItem_Stack_Music.txt not found.")

items = json.load(items_file)
print("Item_Stack_Music.txt loaded. {")

items_file.close()

newtranslations = False

for item in items:
    tr_text = item["tr_text"]
    fill_cn_name(item)
    name_prefix = split_name_prefix(item)
    problem = translate_music_desc(item, name_prefix)
    item["tr_explain"] = name_prefix + item["tr_explain"]
    unfill_cn_name(item, tr_text)

    if problem == 0:
        print("\tTranslated description for {0}".format(item["tr_text"] or item["jp_text"]))
        newtranslations = True
    elif problem == -4:
        print("\t{0} has a new kind of description".format(item["tr_text"] or item["jp_text"]))

if newtranslations == False:
    print("\tNo new translations.")

print("}")

items_file = codecs.open(os.path.join(json_loc, "Item_Stack_Music.txt"),
                         mode = 'w', encoding = 'utf-8')
json.dump(items, items_file, ensure_ascii=False, indent="\t", sort_keys=False)
items_file.write("\n")
items_file.close()

####################################################################################################

# Translate paid passes

paid_pass_gathering = {
    "採取": ["Harvesting", "", "", "採獲"],
    "釣り": ["Fishing", "", "", "垂釣"]
    }

paid_pass_months = {
    "１": ["Jan", "", "", "1"],
    "２": ["Feb", "", "", "2"],
    "３": ["Mar", "", "", "3"],
    "４": ["Apr", "", "", "4"],
    "５": ["May", "", "", "5"],
    "６": ["Jun", "", "", "6"],
    "７": ["Jul", "", "", "7"],
    "８": ["Aug", "", "", "8"],
    "９": ["Sep", "", "", "9"],
    "１０": ["Oct", "", "", "10"],
    "１１": ["Nov", "", "", "11"],
    "１２": ["Dec", "", "", "12"]
    }

paid_pass_time_units = {
    "分": ["minutes", "", "", "分"],
    "時間": ["hours", "", "", "小時"]
    }

paid_pass_ticket_kinds = {
    "チケット": ["", "", "", "票券"],
    "メダル": ["", "", "", "獎章"]
    }

paid_pass_value_names = {
    "gather": paid_pass_gathering,
    "m": paid_pass_months,
    "unit": paid_pass_time_units,
    "kind": paid_pass_ticket_kinds
    }

# Parts of the description that come from the item's name:
# (value, pattern in the JP name, patterns in the translated name)
paid_pass_name_parts = {
    # Ｓ{n}追加：{ssa}, Ｓ{n}追加Ｒ：{ssa}
    "ssa": ("ssa", r"Ｓ\d+追加Ｒ?：(.+)",
            [r"S\d+ Add ?R?:(.+)", r"", r"", r"S\d+追加R?：(.+)"]),
    # 特殊能力追加（{ability}）
    "ability": ("ability", r".+?（(.+)）",
                [r"", r"", r"", r".+?（(.+)）"]),
    "ability_desc": ("ability", r".+?（(.+)）",
                     [r"", r"", r"", r".+?（(.+)）"]),
    # 強化値上限＋１／{weapon}
    "ngrind_weapon_cap": ("weapon", r".+／(.+)",
                          [r".+/(.+)", r"", r"", r".+/(.+)"]),
    # 属性変化（{element}属性）
    "element_change": ("element", r".+?（(.+?)属性）",
                       [r".+?\((.+)\)", r"", r"", r".+?（(.+?)屬性）"]),
    # クラス追加（{cls}）
    "extend_class": ("cls", r".+?（(.+)）",
                     [r".+?\((.+)\)", r"", r"", r".+?（(.+)）"]),
    # 装備条件変更（{condition}）
    "extend_condition": ("condition", r".+?（(.+)）",
                         [r".+?\((.+)\)", r"", r"", r".+?（(.+)）"]),
    # {gacha}券{suffix}, {gacha}券Vol.{n}, {gacha}メダル{suffix}
    "scratch": ("gacha", r"(.+?)(?:券|メダル)(?:Vol\.)?(.*)",
                [r"(.+?) (?:Ticket|Medal)(.*)", r"", r"", r"(.+?)(?:券|獎章)(?:Vol\.)?(.*)"]),
    "scratch_old": ("gacha", r"(.+?)(?:券|メダル)(?:Vol\.)?(.*)",
                    [r"(.+?) (?:Ticket|Medal)(.*)", r"", r"", r"(.+?)(?:券|獎章)(?:Vol\.)?(.*)"]),
    # {gacha}補助券
    "scratch_pieces": ("gacha", r"(.+)補助券",
                       [r"(.+) Voucher", r"", r"", r"(.+)輔助券"]),
    "scratch_exchange": ("gacha", r"(.+)補助券",
                         [r"(.+) Voucher", r"", r"", r"(.+)輔助券"]),
    "scratch_exchange_some": ("gacha", r"(.+)補助券",
                              [r"(.+) Voucher", r"", r"", r"(.+)輔助券"])
    }

# JP text:
    # アイテムの限界突破時に\n
    # レアリティ★{r}アイテムの\n
    # 強化限界値を{a}から{b}にするための\n
    # 必要素材アイテムを不要にする。
paid_pass_desc_limitbreak_formats = [("Removes the material requirement\n"
                                      "to raise the Grind Limit of a ★{r} item\n"
                                      "from {a} to {b}."),
                                     (""),
                                     (""),
                                     ("免除道具界限突破時\n"
                                      "將稀有度★{r}道具的\n"
                                      "強化界限值從{a}提升至{b}\n"
                                      "所需的素材道具。")]

# JP text:
    # アイテムの限界突破時に\n
    # レアリティ★{r}以下のアイテムの\n
    # 強化限界値を{a}から{b}にするための\n
    # 必要素材アイテムを不要にする。
paid_pass_desc_limitbreak_below_formats = [("Removes the material requirement\n"
                                            "to raise the Grind Limit of a ★{r} or\n"
                                            "lower item from {a} to {b}."),
                                           (""),
                                           (""),
                                           ("免除道具界限突破時\n"
                                            "將稀有度★{r}或以下道具的\n"
                                            "強化界限值從{a}提升至{b}\n"
                                            "所需的素材道具。")]

# JP text:
    # アイテムの限界突破時に\n
    # 強化限界値を{a}から{b}にするための\n
    # 必要素材アイテムを不要にする。
paid_pass_desc_nlimitbreak_formats = [("Substitutes the material\n"
                                       "requirements to break the limit\n"
                                       "past +{a} on a single item."),
                                      (""),
                                      (""),
                                      ("免除道具界限突破時\n"
                                       "將強化界限值從{a}提升至{b}\n"
                                       "所需的素材道具。")]

# JP text:
    # レアリティ★{r}アイテムの\n
    # 潜在能力をLv.{n}にするための\n
    # 必要素材アイテムを不要にする。
paid_pass_desc_potential_formats = [("Removes the material requirement\n"
                                     "to unlock Potential Ability Lv.{n} on a\n"
                                     "★{r} item."),
                                    (""),
                                    (""),
                                    ("免除將稀有度★{r}道具的\n"
                                     "潛在能力提升至Lv.{n}所需的素材道具。")]

# JP text:
    # レアリティ★{r}以下のアイテムの\n
    # 潜在能力をLv.{n}にするための\n
    # 必要素材アイテムを不要にする。
paid_pass_desc_potential_below_formats = [("Removes the material requirement\n"
                                           "to unlock Potential Ability Lv.{n} on a\n"
                                           "★{r} or lower item."),
                                          (""),
                                          (""),
                                          ("免除將稀有度★{r}或以下道具的\n"
                                           "潛在能力提升至Lv.{n}所需的素材道具。")]

# JP text:
    # アイテムの潜在能力を\n
    # Lv.{n}にするための\n
    # 必要素材アイテムを不要にする。
paid_pass_desc_npotential_formats = [("Substitutes the material\n"
                                      "requirements to unlock the\n"
                                      "Potential Ability Lv.{n} on a single item."),
                                     (""),
                                     (""),
                                     ("免除將道具的潛在能力\n"
                                      "提升至Lv.{n}所需的素材道具。")]

# JP text:
    # アイテム強化スキップで\n
    # 限界突破の上限値を基準として\n
    # レアリティ★{r}以下の武器の\n
    # 強化値を最大{n}にする。
paid_pass_desc_skip_weapon_formats = [("Allows you to skip grinding a ★{r} or\n"
                                       "lower weapon to up to +{n}, subject\n"
                                       "to its current Grind Limit."),
                                      (""),
                                      (""),
                                      ("通過跳過強化的方式\n"
                                       "以界限突破的上限值為基準\n"
                                       "將稀有度★{r}或以下武器的\n"
                                       "強化值提升至最大{n}。")]

# JP text:
    # アイテム強化スキップで\n
    # 限界突破の上限値を基準として\n
    # レアリティ★{r}以下の防具の\n
    # 強化値を最大{n}にする。
paid_pass_desc_skip_armor_formats = [("Allows you to skip grinding ★{r} or\n"
                                      "lower armor to up to +{n}, subject\n"
                                      "to its current Grind Limit."),
                                     (""),
                                     (""),
                                     ("通過跳過強化的方式\n"
                                      "以界限突破的上限值為基準\n"
                                      "將稀有度★{r}或以下防具的\n"
                                      "強化值提升至最大{n}。")]

# JP text:
    # プリセット能力の\n
    # 強化成功率を上昇させる。\n
    # <yellow>※プリセット能力の追加でも使用可能<c>
paid_pass_desc_preset_formats = [("Increases the success rate of\n"
                                  "Preset Ability Upgrade."),
                                 (""),
                                 (""),
                                 ("提升預設能力的強化成功率。\n"
                                  "<yellow>※也可用於追加預設能力<c>")]

# JP text:
    # Lv.{n}のプリセット能力の\n
    # いずれかを装備に追加する。\n
    # <yellow>※プリセット能力の追加でも使用可能<c>
paid_pass_desc_preset_add_formats = [("Adds a Lv.{n} Preset Ability to\n"
                                      "a piece of equipment."),
                                     (""),
                                     (""),
                                     ("為裝備追加任意Lv.{n}的預設能力。\n"
                                      "<yellow>※也可用於追加預設能力<c>")]

# JP text:
    # プリセット能力の強化失敗時に\n
    # 素材アイテムが消費されるのを防止する。\n
    # ベースアイテムのプリセット能力レベルが\n
    # 表示レベル以下の場合のみ使用可能。
paid_pass_desc_preset_protect_formats = [("Prevents material item consumption\n"
                                          "if Preset Ability Upgrade fails. Only\n"
                                          "usable if base item's Preset Ability\n"
                                          "level is at or below the displayed level."),
                                         (""),
                                         (""),
                                         ("防止強化預設能力失敗時素材道具被消耗。\n"
                                          "僅可在基底道具的預設能力\n"
                                          "為顯示的等級或以下時使用。")]

# JP text:
    # プリセット能力の強化を{n}％成功させ\n
    # 必要素材アイテムを不要にする。\n
    # ベースアイテムのプリセット能力レベルが\n
    # 表示レベル以下の場合のみ使用可能。
paid_pass_desc_preset_success_formats = [("Success Rate {n}% & material\n"
                                          "requirement removed for Enhancing\n"
                                          "Preset Abilities. Only works if the\n"
                                          "item's level is equal or lower."),
                                         (""),
                                         (""),
                                         ("使強化預設能力{n}%成功\n"
                                          "並免除所需的素材道具。\n"
                                          "僅可在基底道具的預設能力\n"
                                          "為顯示的等級或以下時使用。")]

# JP text:
    # ギャザラー用に開発された栄養剤。\n
    # {gather}スタミナが{n}回復する。
paid_pass_desc_stamina_formats = [("Nutritional Supplement that\n"
                                   "was developed for Gathering.\n"
                                   "Recovers {n} Stamina."),
                                  (""),
                                  (""),
                                  ("專為採集者開發的營養劑。\n"
                                   "回復{n}{gather}體力。")]

# JP text:
    # ギャザリングで{gather}を行える。\n
    # レア{gather}発生率＋{n}％
paid_pass_desc_gathering_formats = [("A tool for {gather}.\n"
                                     "Rare {gather} Rate +{n}%"),
                                    (""),
                                    (""),
                                    ("可在採集中進行{gather}。\n"
                                     "稀有{gather}發生率+{n}%")]

# JP text:
    # ギャザリングで\n
    # ボーナス付き{gather}を行える。\n
    # レア{gather}発生率＋{n}％\n
    # <yellow>有効期限／{y}年{m}月{d}日{h}時{mi}分<c>
paid_pass_desc_gathering_bonus_formats = [("A tool for {gather}.\n"
                                           "Rare {gather} Rate +{n}%\n"
                                           "<yellow>Expires {m} {d}, {y} {h}:{mi} JST<c>"),
                                          (""),
                                          (""),
                                          ("可在採集中進行帶加成的{gather}。\n"
                                           "稀有{gather}發生率+{n}%\n"
                                           "<yellow>有效期限/{y}年{m}月{d}日{h}時{mi}分<c>")]

# JP text:
    # トレジャーショップの陳列更新パス。\n
    # ＳＧで購入するトレジャーショップの\n
    # 陳列を変更し購入上限をリセットする。
paid_pass_desc_treasure_shop_sg_formats = [("Chooses a new selection of items for\n"
                                            "the SG Treasure Shop and resets any\n"
                                            "purchase limits for those items."),
                                           (""),
                                           (""),
                                           ("更新寶物商店陳列的票證。\n"
                                            "變更以SG購買的寶物商店陳列\n"
                                            "並重置購買上限。")]

# JP text:
    # トレジャーショップの陳列更新パス。\n
    # メセタで購入するトレジャーショップの\n
    # 陳列を変更し購入上限をリセットする。
paid_pass_desc_treasure_shop_meseta_formats = [("Chooses a new selection of items for\n"
                                                "the Meseta Treasure Shop and resets\n"
                                                "any purchase limits for those items."),
                                               (""),
                                               (""),
                                               ("更新寶物商店陳列的票證。\n"
                                                "變更以美賽達購買的寶物商店陳列\n"
                                                "並重置購買上限。")]

# JP text:
    # 特殊能力追加用の補助素材。\n
    # 特殊能力追加時に使用することで\n
    # 成功率を{n}％上昇させる。
paid_pass_desc_affix_rate_formats = [("Used when adding Special Abilities\n"
                                      "on your equipment.\n"
                                      "Boosts success rate by {n}%."),
                                     (""),
                                     (""),
                                     ("追加特殊能力專用的輔助素材。\n"
                                      "在追加特殊能力時使用後\n"
                                      "會提升{n}%成功率。")]

# JP text:
    # 特殊能力追加用の補助素材。\n
    # 特殊能力追加時に使用することで\n
    # 確実に成功させる。
paid_pass_desc_affix_sure_formats = [("Used when adding Special Abilities\n"
                                      "on your equipment.\n"
                                      "Boosts success rate by 100%."),
                                     (""),
                                     (""),
                                     ("追加特殊能力專用的輔助素材。\n"
                                      "在追加特殊能力時使用後\n"
                                      "一定會使其成功。")]

# JP text:
    # アイテムの特殊能力追加時に\n
    # 追加が成功する確率を\n
    # 上昇させる。
paid_pass_desc_naffix_rate_formats = [("Increases the chance of successfully\n"
                                       "adding Special Abilities to an item."),
                                      (""),
                                      (""),
                                      ("提升追加道具的特殊能力時的\n"
                                       "追加成功概率。")]

# JP text:
    # 特殊能力追加に失敗時、素材アイテムと\n
    # 特殊能力追加アイテムが返却される。\n
    # <yellow>対象：追加予定リストが{n}スロット以下<c>
paid_pass_desc_affix_return_formats = [("Returns the Special Abilities that\n"
                                        "were lost from synthesis.\n"
                                        "<yellow>Only works on {n} slots or lower.<c>"),
                                       (""),
                                       (""),
                                       ("在追加特殊能力失敗時，\n"
                                        "會返還素材道具與追加特殊能力的道具。\n"
                                        "<yellow>對象：預定追加的列表為{n}槽或以下<c>")]

# JP text:
    # カスタマイズ実行時に\n
    # カスタムタイプ{t}の効果値を\n
    # {n}％向上させる。
paid_pass_desc_customize_formats = [("Used during customization crafts.\n"
                                     "Custom Type {t} effect boosted\n"
                                     "by {n}%."),
                                    (""),
                                    (""),
                                    ("在執行自定義時\n"
                                     "將自定義類型{t}的效果値提升{n}%。")]

# JP text:
    # テクニックカスタマイズ実行時に\n
    # メリットの下限値を\n
    # {n}％上昇させる。
paid_pass_desc_tech_merit_formats = [("Increases the merit value by {n}%\n"
                                      "when customizing Techniques."),
                                     (""),
                                     (""),
                                     ("在執行法術自定義時\n"
                                      "將有利效果的下限値提升{n}%。")]

# JP text:
    # テクニックカスタマイズ実行時に\n
    # デメリットの上限値を\n
    # {n}％軽減させる。
paid_pass_desc_tech_demerit_formats = [("Decreases the demerit value by -{n}%\n"
                                        "when customizing Techniques."),
                                       (""),
                                       (""),
                                       ("在執行法術自定義時\n"
                                        "將不利效果的上限値減輕{n}%。")]

# JP text:
    # ペットの合成回数が{a}回増加する。\n
    # 増加した合成回数の間は、\n
    # 合成経験値が２倍になる。
paid_pass_desc_pet_formats = [("Increases your available Pet Synthesis\n"
                               "by {a}. Doubles EXP gained from these\n"
                               "increased Synthesis uses."),
                              (""),
                              (""),
                              ("增加{a}次寵物的合成次數。\n"
                               "在使用增加的合成次數期間，\n"
                               "合成經驗値會變為2倍。")]

# JP text:
    # コレクトゲージの授与申請チケット。\n
    # 使用したコレクトシートのゲージを\n
    # 【{n}％】獲得可能。
paid_pass_desc_collect_gauge_formats = [("Increases the Collect File gauge.\n"
                                         "Raises the CF gauge by {n}%."),
                                        (""),
                                        (""),
                                        ("申請授予收集進度槽的票券。\n"
                                         "使用的收集單可獲得\n"
                                         "【{n}%】的進度槽。")]

# JP text:
    # コレクトシートの最大所持枚数を\n
    # 拡張するパス。使用することで\n
    # 最大所持枚数が１枚追加される。
paid_pass_desc_collect_sheet_formats = [("Expands the Collect File Sheet\n"
                                         "by a single slot."),
                                        (""),
                                        (""),
                                        ("擴充收集單最多持有張數的票證。\n"
                                         "使用後會追加1張最多持有張數。")]

# JP text: 追加のクエスト報酬を得られる。
paid_pass_desc_quest_reward_formats = [("Additional quest rewards can be\n"
                                        "obtained."),
                                       (""),
                                       (""),
                                       ("可獲得追加的任務報酬。")]

# JP text:
    # アイテム強化時に\n
    # 強化が大成功になる確率を\n
    # 上昇させる。
paid_pass_desc_ngrind_great_formats = [("Increases the chance of a Great\n"
                                        "Success when enhancing an item."),
                                       (""),
                                       (""),
                                       ("提升強化道具時的強化大成功概率。")]

# JP text:
    # 旧式武器、防具、キャンディー用の\n
    # 強化補助素材。強化時に使用することで\n
    # 成功率を{n}％上昇させる。
paid_pass_desc_grind_rate_formats = [("Increase the success rate\n"
                                      "by {n}% when grinding equipment."),
                                     (""),
                                     (""),
                                     ("舊式武器、防具、糖果專用的\n"
                                      "強化輔助素材。在強化時使用後\n"
                                      "會提升{n}%成功率。")]

# JP text:
    # 旧式武器、防具、キャンディー用の\n
    # 強化補助素材。強化時に使用することで\n
    # 確実に成功させる。
paid_pass_desc_grind_sure_formats = [("Support item for grinding equipment.\n"
                                      "Guarantees that one grind will be\n"
                                      "successful."),
                                     (""),
                                     (""),
                                     ("舊式武器、防具、糖果專用的\n"
                                      "強化輔助素材。在強化時使用後\n"
                                      "一定會使其成功。")]

# JP text:
    # 旧式武器、ユニット用の強化補助素材。\n
    # 強化値が＋{a}以下の時に使用すると\n
    # ＋{b}まで一気に強化することができる。
paid_pass_desc_grind_jump_formats = [("Instantly grinds to +{b} when the item\n"
                                      "grinding is +{a} or lower. Cannot be\n"
                                      "traded or sold to other players."),
                                     (""),
                                     (""),
                                     ("舊式武器、防具專用的強化輔助素材。\n"
                                      "在強化値為+{a}或以下時使用後\n"
                                      "可直接強化至+{b}。")]

# JP text:
    # 旧式武器、ユニット用の原型保護素材。\n
    # 強化時に使用することで\n
    # 強化失敗時のリスクを{n}段階低減する。
paid_pass_desc_grind_protect_formats = [("Used when grinding equipment.\n"
                                         "Decreases grinding risk by {n}."),
                                        (""),
                                        (""),
                                        ("舊式武器、防具專用的原型保護素材。\n"
                                         "在強化時使用後\n"
                                         "會降低{n}段強化失敗時的風險。")]

# JP text:
    # 属性強化用の強化補助素材。\n
    # 属性強化時に使用することで\n
    # 属性値を{n}％底上げする。
paid_pass_desc_element_rate_formats = [("Used when grinding attributes.\n"
                                        "Increases weapon attribute by {n}%."),
                                       (""),
                                       (""),
                                       ("屬性強化專用的強化輔助素材。\n"
                                        "在屬性強化時使用後\n"
                                        "會提升{n}%屬性値。")]

# JP text:
    # 属性強化用の強化変成素材。\n
    # 属性強化時に使用することで\n
    # 【{element}】属性へと変化させる。
paid_pass_desc_element_change_formats = [("Used when grinding attributes.\n"
                                          "Changes weapon attribute to \"{element}\"."),
                                         (""),
                                         (""),
                                         ("屬性強化專用的強化變質素材。\n"
                                          "在屬性強化時使用後\n"
                                          "會將其變化為【{element}】屬性。")]

# JP text:
    # 新世武器用の強化補助素材。\n
    # 強化時に使用することで\n
    # 大成功確率を{n}％上昇させる。
paid_pass_desc_ngrind_rate_formats = [("Material used on NT Weapons.\n"
                                       "During weapon grinding, success\n"
                                       "probability rate boosted by {n}%."),
                                      (""),
                                      (""),
                                      ("新世武器專用的強化輔助素材。\n"
                                       "在強化時使用後\n"
                                       "會提升{n}%大成功概率。")]

# JP text:
    # 新世武器用の強化補助素材。\n
    # 強化時に使用することで\n
    # 確実に大成功を発生させる。
paid_pass_desc_ngrind_sure_formats = [("Material used on NT Weapons.\n"
                                       "During weapon grinding, success\n"
                                       "probability rate boosted by 100%."),
                                      (""),
                                      (""),
                                      ("新世武器專用的強化輔助素材。\n"
                                       "在強化時使用後一定會使其大成功。")]

# JP text:
    # 新世武器用の強化補助素材。\n
    # 強化時に使用することで\n
    # 強化値の上限を{n}上昇させる。
paid_pass_desc_ngrind_cap_formats = [("Material used on NT Weapons. During\n"
                                      "weapon grinding, the grind cap is\n"
                                      "boosted by +{n}."),
                                     (""),
                                     (""),
                                     ("新世武器專用的強化輔助素材。\n"
                                      "在強化時使用後\n"
                                      "會將強化値的上限提升{n}。")]

# JP text:
    # 新世武器用の強化補助素材。\n
    # 『{weapon}』の強化時に使用することで\n
    # 強化値の上限を{n}上昇させる。
paid_pass_desc_ngrind_weapon_cap_formats = [("Material used on NT Weapons. During\n"
                                             "weapon grinding, {weapon} grind cap is\n"
                                             "boosted by +{n}."),
                                            (""),
                                            (""),
                                            ("新世武器專用的強化輔助素材。\n"
                                             "在強化『{weapon}』時使用後\n"
                                             "會將強化値的上限提升{n}。")]

# JP text:
    # 特定レアリティ武器の購入パス。\n
    # マイショップで【★{r}】武器を\n
    # 購入する際に消費される。
paid_pass_desc_purchase_weapon_formats = [("A pass that grants the purchase\n"
                                           "of {r}★ weapons from My Shop."),
                                          (""),
                                          (""),
                                          ("購買特定稀有度武器的票證。\n"
                                           "會在個人商店購買\n"
                                           "【★{r}】武器時消費。")]

# JP text:
    # 特定レアリティユニットの購入パス。\n
    # マイショップで【★{r}】ユニットを\n
    # 購入する際に消費される。
paid_pass_desc_purchase_unit_formats = [("A pass that grants the purchase\n"
                                         "of {r}★ units from My Shop."),
                                        (""),
                                        (""),
                                        ("購買特定稀有度防具的票證。\n"
                                         "會在個人商店購買\n"
                                         "【★{r}】防具時消費。")]

# JP text:
    # 武装エクステンド実行時に\n
    # 装備条件を{n}％緩和する。
paid_pass_desc_extend_ease_formats = [("Decreases the required stat of\n"
                                       "the extended equipment by {n}%."),
                                      (""),
                                      (""),
                                      ("在執行武裝擴張時\n"
                                       "放緩{n}%的裝備條件。")]

# JP text:
    # 武装エクステンド実行時に\n
    # {cls}のクラス追加が\n
    # 必ず発生するようになる。
paid_pass_desc_extend_class_formats = [("Adds the class \"{cls}\"\n"
                                        "to equipment when extended."),
                                       (""),
                                       (""),
                                       ("在執行武裝擴張時\n"
                                        "必定會追加{cls}職業。")]

# JP text:
    # 武装エクステンド実行時に\n
    # 装備条件を{condition}に\n
    # 変更する。
paid_pass_desc_extend_condition_formats = [("Swaps the equipment requirement\n"
                                            "when used during equipment\n"
                                            "extension with {condition}."),
                                           (""),
                                           (""),
                                           ("在執行武裝擴張時\n"
                                            "將裝備條件變更為{condition}。")]

# JP text:
    # 時限能力インストール実行時に\n
    # データの効果時間を{n}日\n
    # 延長させる。
paid_pass_desc_install_time_formats = [("Extends the expiration of\n"
                                        "a Timed Ability by {n} days."),
                                       (""),
                                       (""),
                                       ("在執行時限能力安裝時\n"
                                        "將資料的效果時間延長{n}日。")]

# JP text:
    # 選択したクラフトエネルギーを\n
    # {n}{unit}回復させる。
paid_pass_desc_craft_energy_formats = [("Reduces the cooldown of a craft\n"
                                        "line by {n} {unit}."),
                                       (""),
                                       (""),
                                       ("將選擇的鍛造能量回復{n}{unit}。")]

# JP text:
    # 現在所持している全ての\n
    # クラフトエネルギーを\n
    # {n}時間回復させる。
paid_pass_desc_craft_energy_all_formats = [("Reduces the cooldown of all craft\n"
                                            "lines by {n} hours."),
                                           (""),
                                           (""),
                                           ("將當前持有的所有鍛造能量回復{n}小時。")]

# JP text:
    # エステカウンターの機能利用パス。\n
    # サポートパートナーにも使用可能。\n
    # 利用するたびにパスは消費される。
paid_pass_desc_salon_formats = [("Allows you to use restricted options\n"
                                 "in the Beauty Salon. Pass is used\n"
                                 "after saving changes."),
                                (""),
                                (""),
                                ("使用美容院櫃檯功能的票證。\n"
                                 "也可用於支援夥伴。\n"
                                 "每次使用都會消費票證。")]

# JP text: {abbr}クラスレベル{n}化
paid_pass_desc_class_level_formats = [("{abbr} Class Lv.{n}"),
                                      (""),
                                      (""),
                                      ("{abbr}職業等級升至{n}")]

# JP text: {abbr}クラスレベル{n}化＆適正装備セット
paid_pass_desc_class_level_set_formats = [("{abbr} Class Lv.{n} & Equipment Set"),
                                          (""),
                                          (""),
                                          ("{abbr}職業等級升至{n}&適配裝備套裝")]

# JP text: クラスレベル{n}化
paid_pass_desc_all_class_level_formats = [("Class Lv.{n}"),
                                          (""),
                                          (""),
                                          ("職業等級升至{n}")]

# JP text: クラスレベル{n}化＆適正装備セット
paid_pass_desc_all_class_level_set_formats = [("Class Lv.{n} & Equipment Set"),
                                              (""),
                                              (""),
                                              ("職業等級升至{n}&適配裝備套裝")]

# JP text:
    # 特殊能力合成用の能力付与素材。\n
    # 特殊能力合成時に使用することで\n
    # Ｓ{n}：{ssa}を付与。
paid_pass_desc_ssa_formats = [("Material used in SSA Synthesis.\n"
                               "Grants \"S{n}:{ssa}\"\n"
                               "when used in Ability Synthesis."),
                              (""),
                              (""),
                              ("合成特殊能力專用的能力賦予素材。\n"
                               "在合成特殊能力時使用後\n"
                               "會追加S{n}：{ssa}。")]

# JP text:
    # 特殊能力合成用の能力付与素材。\n
    # 特殊能力合成時に使用することで\n
    # 【{ability}】の特殊能力を追加する。
paid_pass_desc_ability_desc_formats = [("Material for Special Ability Synthesis.\n"
                                        "Grants \"{ability}\"\n"
                                        "when used in Ability Synthesis."),
                                       (""),
                                       (""),
                                       ("合成特殊能力專用的能力賦予素材。\n"
                                        "在合成特殊能力時使用後\n"
                                        "會追加【{ability}】的特殊能力。")]

# JP text:
    # 特殊能力合成用の能力付与素材。\n
    # 特殊能力合成時に使用することで\n
    # 【{ability}】を追加。
paid_pass_desc_ability_formats = [("Material for Special Ability Synthesis.\n"
                                   "Grants \"{ability}\"\n"
                                   "when used in Ability Synthesis."),
                                  (""),
                                  (""),
                                  ("合成特殊能力專用的能力賦予素材。\n"
                                   "在合成特殊能力時使用後\n"
                                   "會追加【{ability}】。")]

# JP text:
    # アイテムパックに所持しておくことで\n
    # <yellow>{gacha}<c>に\n
    # {n}回挑戦できる{kind}。
paid_pass_desc_scratch_formats = [("Allows you one chance at the\n"
                                   "<yellow>{gacha}<c>\n"
                                   "just by having it in your inventory."),
                                  (""),
                                  (""),
                                  ("放在道具背包內即可挑戰{n}次\n"
                                   "<yellow>{gacha}<c>的{kind}。")]

# JP text:
    # アイテムパックに所持しておくことで\n
    # {k}枚で{n}回、<yellow>{gacha}<c>に\n
    # 挑戦できるチケット。
paid_pass_desc_scratch_pieces_formats = [("Allows you one chance at the\n"
                                          "<yellow>{gacha}<c> just by having\n"
                                          "{k} of these in your inventory."),
                                         (""),
                                         (""),
                                         ("放在道具背包內即可用{k}張挑戰{n}次\n"
                                          "<yellow>{gacha}<c>的票券。")]

# JP text:
    # {k}枚集めることで\n
    # アイテムリサイクルで\n
    # <yellow>{gacha}券<c>\n
    # と交換できるチケット。
paid_pass_desc_scratch_exchange_formats = [("A ticket which can be recycled in\n"
                                            "batches of {k} to obtain\n"
                                            "<yellow>{gacha} Tickets<c>"),
                                           (""),
                                           (""),
                                           ("集齊{k}張即可在道具回收中\n"
                                            "交換<yellow>{gacha}券<c>的票券。")]

# JP text:
    # 一定枚数集めることで\n
    # アイテムリサイクルで\n
    # <yellow>{gacha}<c>\n
    # と交換できるチケット。
paid_pass_desc_scratch_exchange_some_formats = [(""),
                                                (""),
                                                (""),
                                                ("集齊一定張數即可在道具回收中\n"
                                                 "交換<yellow>{gacha}<c>的票券。")]

# JP text:
    # {gacha}の利用券。\n
    # 持っていると{gacha}に\n
    # {n}回挑戦することができる。
paid_pass_desc_scratch_old_formats = [("{gacha} Tickets.\n"
                                       "With this ticket, you can try\n"
                                       "{gacha} once per ticket."),
                                      (""),
                                      (""),
                                      ("{gacha}的使用券。\n"
                                       "持有時可以挑戰{n}次{gacha}。")]

paid_pass_desc_patterns = {
    r"アイテムの限界突破時に\nレアリティ★(?P<r>\d+)アイテムの\n強化限界値を(?P<a>\d+)から(?P<b>\d+)にするための\n必要素材アイテムを不要にする。": "limitbreak",
    r"アイテムの限界突破時に\nレアリティ★(?P<r>\d+)以下のアイテムの\n強化限界値を(?P<a>\d+)から(?P<b>\d+)にするための\n必要素材アイテムを不要にする。": "limitbreak_below",
    r"アイテムの限界突破時に\n強化限界値を(?P<a>\d+)から(?P<b>\d+)にするための\n必要素材アイテムを不要にする。": "nlimitbreak",
    r"レアリティ★(?P<r>\d+)アイテムの\n潜在能力をLv\.(?P<n>\d+)にするための\n必要素材アイテムを不要にする。": "potential",
    r"レアリティ★(?P<r>\d+)以下のアイテムの\n潜在能力をLv\.(?P<n>\d+)にするための\n必要素材アイテムを不要にする。": "potential_below",
    r"アイテムの潜在能力を\nLv\.(?P<n>\d+)にするための\n必要素材アイテムを不要にする。": "npotential",
    r"アイテム強化スキップで\n限界突破の上限値を基準として\nレアリティ★(?P<r>\d+)以下の武器の\n強化値を最大(?P<n>\d+)にする。": "skip_weapon",
    r"アイテム強化スキップで\n限界突破の上限値を基準として\nレアリティ★(?P<r>\d+)以下の防具の\n強化値を最大(?P<n>\d+)にする。": "skip_armor",
    r"プリセット能力の\n強化成功率を上昇させる。\n<yellow>※プリセット能力の追加でも使用可能<c>": "preset",
    r"Lv\.(?P<n>\d+)のプリセット能力の\nいずれかを装備に追加する。\n<yellow>※プリセット能力の追加でも使用可能<c>": "preset_add",
    r"プリセット能力の強化失敗時に\n素材アイテムが消費されるのを防止する。\nベースアイテムのプリセット能力レベルが\n表示レベル以下の場合のみ使用可能。": "preset_protect",
    r"プリセット能力の強化を(?P<n>\d+)％成功させ\n必要素材アイテムを不要にする。\nベースアイテムのプリセット能力レベルが\n表示レベル以下の場合のみ使用可能。": "preset_success",
    r"ギャザラー用に開発された栄養剤。\n(?P<gather>採取|釣り)スタミナが(?P<n>\d+)回復する。": "stamina",
    r"ギャザリングで(?P<gather>採取|釣り)を行える。\nレア(?:採取|釣り)発生率＋(?P<n>\d+)％": "gathering",
    r"ギャザリングで\nボーナス付き(?P<gather>採取|釣り)を行える。\nレア(?:採取|釣り)発生率＋(?P<n>\d+)％\n<yellow>有効期限／(?P<y>\d+)年(?P<m>\d+)月(?P<d>\d+)日(?P<h>\d+)時(?P<mi>\d+)分<c>": "gathering_bonus",
    r"トレジャーショップの陳列更新パス。\nＳＧで購入するトレジャーショップの\n陳列を変更し購入上限をリセットする。": "treasure_shop_sg",
    r"トレジャーショップの陳列更新パス。\nメセタで購入するトレジャーショップの\n陳列を変更し購入上限をリセットする。": "treasure_shop_meseta",
    r"特殊能力追加用の補助素材。\n特殊能力追加時に使用することで\n成功率を(?P<n>\d+)％上昇させる。": "affix_rate",
    r"特殊能力追加用の補助素材。\n特殊能力追加時に使用することで\n確実に成功させる。": "affix_sure",
    r"アイテムの特殊能力追加時に\n追加が成功する確率を\n上昇させる。": "naffix_rate",
    r"特殊能力追加に失敗時、素材アイテムと\n特殊能力追加アイテムが返却される。\n<yellow>対象：追加予定リストが(?P<n>\d+)スロット以下<c>": "affix_return",
    r"カスタマイズ実行時に\nカスタムタイプ(?P<t>\d+)の効果値を\n(?P<n>\d+)％向上させる。": "customize",
    r"テクニックカスタマイズ実行時に\nメリットの下限値を\n(?P<n>\d+)％上昇させる。": "tech_merit",
    r"テクニックカスタマイズ実行時に\nデメリットの上限値を\n(?P<n>\d+)％軽減させる。": "tech_demerit",
    r"ペットの合成回数が(?P<a>\d+)回増加する。\n増加した合成回数の間は、\n合成経験値が２倍になる。": "pet",
    r"コレクトゲージの授与申請チケット。\n使用したコレクトシートのゲージを\n【(?P<n>\d+)％】獲得可能。": "collect_gauge",
    r"コレクトシートの最大所持枚数を\n拡張するパス。使用することで\n最大所持枚数が１枚追加される。": "collect_sheet",
    r"追加のクエスト報酬を得られる。": "quest_reward",
    r"アイテム強化時に\n強化が大成功になる確率を\n上昇させる。": "ngrind_great",
    r"旧式武器、防具、キャンディー用の\n強化補助素材。強化時に使用することで\n成功率を(?P<n>\d+)％上昇させる。": "grind_rate",
    r"旧式武器、防具、キャンディー用の\n強化補助素材。強化時に使用することで\n確実に成功させる。": "grind_sure",
    r"旧式武器、ユニット用の強化補助素材。\n強化値が＋(?P<a>\d+)以下の時に使用すると\n＋(?P<b>\d+)まで一気に強化することができる。": "grind_jump",
    r"旧式武器、ユニット用の原型保護素材。\n強化時に使用することで\n強化失敗時のリスクを(?P<n>\d+)段階低減する。": "grind_protect",
    r"属性強化用の強化補助素材。\n属性強化時に使用することで\n属性値を(?P<n>\d+)％底上げする。": "element_rate",
    r"属性強化用の強化変成素材。\n属性強化時に使用することで\n【(?P<element>.)】属性へと変化させる。": "element_change",
    r"新世武器用の強化補助素材。\n強化時に使用することで\n大成功確率を(?P<n>\d+)％上昇させる。": "ngrind_rate",
    r"新世武器用の強化補助素材。\n強化時に使用することで\n確実に大成功を発生させる。": "ngrind_sure",
    r"新世武器用の強化補助素材。\n強化時に使用することで\n強化値の上限を(?P<n>\d+)上昇させる。": "ngrind_cap",
    r"新世武器用の強化補助素材。\n『(?P<weapon>.+)』の強化時に使用することで\n強化値の上限を(?P<n>\d+)上昇させる。": "ngrind_weapon_cap",
    r"特定レアリティ武器の購入パス。\nマイショップで【★(?P<r>\d+)】武器を\n購入する際に消費される。": "purchase_weapon",
    r"特定レアリティユニットの購入パス。\nマイショップで【★(?P<r>\d+)】ユニットを\n購入する際に消費される。": "purchase_unit",
    r"武装エクステンド実行時に\n装備条件を(?P<n>\d+)％緩和する。": "extend_ease",
    r"武装エクステンド実行時に\n(?P<cls>.+)のクラス追加が\n必ず発生するようになる。": "extend_class",
    r"武装エクステンド実行時に\n装備条件を(?P<condition>.+)に\n変更する。": "extend_condition",
    r"時限能力インストール実行時に\nデータの効果時間を(?P<n>\d+)日\n延長させる。": "install_time",
    r"選択したクラフトエネルギーを\n(?P<n>\d+)(?P<unit>分|時間)回復させる。": "craft_energy",
    r"現在所持している全ての\nクラフトエネルギーを\n(?P<n>\d+)時間回復させる。": "craft_energy_all",
    r"エステカウンターの機能利用パス。\nサポートパートナーにも使用可能。\n利用するたびにパスは消費される。\s*": "salon",
    r"(?P<abbr>[A-Za-z]+)クラスレベル(?P<n>\d+)化": "class_level",
    r"(?P<abbr>[A-Za-z]+)クラスレベル(?P<n>\d+)化＆適正装備セット": "class_level_set",
    r"クラスレベル(?P<n>\d+)化": "all_class_level",
    r"クラスレベル(?P<n>\d+)化＆適正装備セット": "all_class_level_set",
    r"特殊能力合成用の能力付与素材。\n特殊能力合成時に使用することで\nＳ(?P<n>\d+)：(?P<ssa>.+)を付与。": "ssa",
    r"特殊能力合成用の能力付与素材。\n特殊能力合成時に使用することで\n【(?P<ability>.+)】の特殊能力を追加する。": "ability_desc",
    r"特殊能力合成用の能力付与素材。\n特殊能力合成時に使用することで\n【(?P<ability>.+)】を追加(?:する)?。": "ability",
    r"アイテムパックに所持しておくことで\n<yellow>(?P<gacha>[^<]+)<c>に\n(?P<n>\d+)回挑戦できる(?P<kind>チケット|メダル)。": "scratch",
    r"アイテムパックに所持しておくことで\n(?P<k>\d+)枚で(?P<n>\d+)回、<yellow>(?P<gacha>[^<]+)<c>に\n挑戦できるチケット。": "scratch_pieces",
    r"(?P<k>\d+)枚集めることで\nアイテムリサイクルで\n<yellow>(?P<gacha>[^<]+)券<c>\nと交換できるチケット。": "scratch_exchange",
    r"一定枚数集めることで\nアイテムリサイクルで\n<yellow>(?P<gacha>[^<]+)<c>\nと交換できるチケット。": "scratch_exchange_some",
    r"(?P<gacha>.+)の利用券。\n持っていると(?P=gacha)に\n(?P<n>\d+)回挑戦することができる。": "scratch_old"
    }

# Paid pass names

paid_pass_name_elements = {
    "炎": ["Fire", "", "", "炎"],
    "氷": ["Ice", "", "", "冰"],
    "雷": ["Lightning", "", "", "雷"],
    "風": ["Wind", "", "", "風"],
    "光": ["Light", "", "", "光"],
    "闇": ["Dark", "", "", "暗"]
    }

paid_pass_name_classes = {
    "ハンター": ["Hunter", "", "", "獵人"],
    "レンジャー": ["Ranger", "", "", "遊俠"],
    "フォース": ["Force", "", "", "法師"],
    "ファイター": ["Fighter", "", "", "鬥士"],
    "ガンナー": ["Gunner", "", "", "鷹眼"],
    "テクター": ["Techter", "", "", "元素使"],
    "ブレイバー": ["Braver", "", "", "武士"],
    "バウンサー": ["Bouncer", "", "", "凌客"],
    "サモナー": ["Summoner", "", "", "召喚師"]
    }

paid_pass_name_conditions = {
    "打撃": ["S-ATK", "", "", "打擊"],
    "射撃": ["R-ATK", "", "", "射擊"],
    "法撃": ["T-ATK", "", "", "法擊"],
    "技量": ["DEX", "", "", "技量"],
    "打撃防御": ["S-DEF", "", "", "打擊防禦"],
    "射撃防御": ["R-DEF", "", "", "射擊防禦"],
    "法撃防御": ["T-DEF", "", "", "法擊防禦"]
    }

paid_pass_name_weapons = {
    "大剣": ["Sword", "", "", "大劍"],
    "自在槍": ["Wired Lance", "", "", "自在槍"],
    "長槍": ["Partizan", "", "", "長槍"],
    "双小剣": ["Twin Dagger", "", "", "雙小劍"],
    "両剣": ["Double Saber", "", "", "雙頭劍"],
    "鋼拳": ["Knuckles", "", "", "鋼拳"],
    "銃剣": ["Gunslash", "", "", "槍刃"],
    "長銃": ["Assault Rifle", "", "", "步槍"],
    "大砲": ["Launcher", "", "", "大炮"],
    "双機銃": ["Twin Machineguns", "", "", "雙機槍"],
    "長杖": ["Rod", "", "", "長杖"],
    "導具": ["Talis", "", "", "導具"],
    "短杖": ["Wand", "", "", "短杖"],
    "抜剣": ["Katana", "", "", "拔劍"],
    "強弓": ["Bullet Bow", "", "", "強弓"],
    "魔装脚": ["Jet Boots", "", "", "魔裝腳"],
    "飛翔剣": ["Dual Blade", "", "", "飛翔劍"],
    "奏具": ["Takt", "", "", "奏具"]
    }

paid_pass_name_bosses = {
    "エイジス": ["Aegis", "", "", "神盾"],
    "ソウラス": ["Solus", "", "", "索剌斯"],
    "ダリオン": ["Dalion", "", "", "怛林"],
    "ヴァエル": ["Vael", "", "", "巴耶爾"],
    "ルーサー": ["Loser", "", "", "敗者"]
    }

paid_pass_name_bigbang_kinds = {
    "ゴールド": ["Gold", "", "", "金"],
    "シルバー": ["Silver", "", "", "銀"],
    "フィーバー": ["Fever", "", "", "狂熱"]
    }

paid_pass_name_value_names = {
    "element": paid_pass_name_elements,
    "cls": paid_pass_name_classes,
    "condition": paid_pass_name_conditions,
    "weapon": paid_pass_name_weapons,
    "boss": paid_pass_name_bosses,
    "bigbang": paid_pass_name_bigbang_kinds,
    "event": scratch_name_events,
    "series": scratch_name_series,
    "kind": scratch_name_kinds,
    "game": scratch_name_games,
    "n": name_ordinals
    }

# JP text: N-★{r}限界突破代用材/限界値{v}
paid_pass_name_limitbreak_formats = ["N-★{r} Limit Break Substitution/{v}", "", "", "N-★{r}界限突破代用材/界限值{v}"]

# JP text: N-限界突破代用材/限界値{v}
paid_pass_name_nlimitbreak_formats = ["N-Limit Break Substitution/{v}", "", "", "N-界限突破代用材/界限值{v}"]

# JP text: N-★{r}潜在能力解放代用材/Lv.{v}
paid_pass_name_potential_formats = ["N-★{r} Potential Subsitution/Lv.{v}", "", "", "N-★{r}潛在能力解放代用材/Lv.{v}"]

# JP text: N-潜在能力解放代用材/Lv.{v}
paid_pass_name_npotential_formats = ["N-Potential Subsitution/Lv.{v}", "", "", "N-潛在能力解放代用材/Lv.{v}"]

# JP text: ★{r}武器強化スキップ＋{v}
paid_pass_name_skip_weapon_formats = ["★{r} Weapon Grind Skip +{v}", "", "", "★{r}武器強化跳過+{v}"]

# JP text: ★{r}防具強化スキップ＋{v}
paid_pass_name_skip_armor_formats = ["★{r} Armor Grind Skip +{v}", "", "", "★{r}防具強化跳過+{v}"]

# JP text: プリセット能力強化成功率＋{v}％
paid_pass_name_preset_formats = ["Preset Ability Success +{v}%", "", "", "預設能力強化成功率+{v}%"]

# JP text: プリセット能力強化アイテム保護/Lv.{v}
paid_pass_name_preset_protect_formats = ["Preset Ability Protection/Lv.{v}", "", "", "預設能力強化道具保護/Lv.{v}"]

# JP text: プリセット能力強化成功＆代用材/Lv.{v}
paid_pass_name_preset_success_formats = ["Preset Ability & Material Cost Substitution/Lv.{v}", "", "", "預設能力強化成功&代用材/Lv.{v}"]

# JP text: 能力追加成功率＋{v}％
paid_pass_name_affix_rate_formats = ["Ability Success Rate +{v}%", "", "", "能力追加成功率+{v}%"]

# JP text: 能力追加成功（{v}％）
paid_pass_name_affix_sure_formats = ["Ability Success Rate +{v}%", "", "", "能力追加成功（{v}%）"]

# JP text: N-特殊能力追加成功率＋{v}%
paid_pass_name_naffix_rate_formats = ["N-Ability Success +{v}%", "", "", "N-特殊能力追加成功率+{v}%"]

# JP text: 特殊能力保護（{v}枠以下）
paid_pass_name_affix_return_formats = ["Ability Protection ({v}s or lower)", "", "", "特殊能力保護（{v}項或以下）"]

# JP text: カスタムタイプ{t}＋{v}％
paid_pass_name_customize_formats = ["Custom Type {t} +{v}%", "", "", "自定義類型{t}+{v}%"]

# JP text: メリット値＋{v}％
paid_pass_name_tech_merit_formats = ["Merit Value +{v}%", "", "", "有利效果値+{v}%"]

# JP text: デメリット値－{v}％
paid_pass_name_tech_demerit_formats = ["Demerit Value -{v}%", "", "", "不利效果値-{v}%"]

# JP text: 合成可能数回復{v}
paid_pass_name_pet_formats = ["Pet Synthesis Recovery {v}", "", "", "可合成次數回復{v}"]

# JP text: 採取スタドリ{v}
paid_pass_name_harvest_stamina_formats = ["Collect Stam. Drink {v}", "", "", "採獲體力飲料{v}"]

# JP text: 釣りスタドリ{v}
paid_pass_name_fishing_stamina_formats = ["Fishing Stam. Drink {v}", "", "", "垂釣體力飲料{v}"]

# JP text: ＳＧトレジャー更新{v}
paid_pass_name_treasure_shop_sg_formats = ["SG Treasure Update {v}", "", "", "SG寶物更新{v}"]

# JP text: メセタトレジャー更新{v}
paid_pass_name_treasure_shop_meseta_formats = ["Meseta Shop Update {v}", "", "", "美賽達寶物更新{v}"]

# JP text: スキルリング強化代用材/＋{v}
paid_pass_name_skill_ring_formats = ["Ring Material Subsitution/+{v}", "", "", "技能戒指強化代用材/＋{v}"]

# JP text: N-強化大成功率＋{v}%
paid_pass_name_ngrind_great_formats = ["N-Grind Great Success +{v}%", "", "", "N-強化大成功率+{v}%"]

# JP text: 強化成功率＋{v}％
paid_pass_name_grind_rate_formats = ["Grind Success Rate +{v}%", "", "", "強化成功率+{v}%"]

# JP text: 強化成功（{v}％）
paid_pass_name_grind_sure_formats = ["Grind Success ({v}%)", "", "", "強化成功（{v}%）"]

# JP text: 強化スキップ（→{v}）
paid_pass_name_grind_jump_formats = ["Grind Skip (→{v})", "", "", "強化跳過（→{v}）"]

# JP text: 強化リスク軽減（＋{v}）
paid_pass_name_grind_protect_formats = ["Grind Risk Reduction (+{v})", "", "", "強化風險減輕（+{v}）"]

# JP text: 属性強化＋{v}％
paid_pass_name_element_rate_formats = ["Attribute Enhance +{v}%", "", "", "屬性強化+{v}%"]

# JP text: 強化大成功確率＋{v}％
paid_pass_name_ngrind_rate_formats = ["Great Grind Success +{v}%", "", "", "強化大成功概率+{v}%"]

# JP text: 強化大成功（{v}％）
paid_pass_name_ngrind_sure_formats = ["Great Grind Success ({v}%)", "", "", "強化大成功（{v}%）"]

# JP text: 強化値上限＋{v}
paid_pass_name_ngrind_cap_formats = ["Grind Cap +{v}", "", "", "強化値上限+{v}"]

# JP text: ★{r}武器購入パス
paid_pass_name_purchase_weapon_formats = ["{r}★ Weapon Exchange Pass", "", "", "★{r}武器購買票證"]

# JP text: ★{r}ユニット購入パス
paid_pass_name_purchase_unit_formats = ["{r}★ Unit Exchange Pass", "", "", "★{r}防具購買票證"]

# JP text: 装備条件緩和＋{v}％
paid_pass_name_extend_ease_formats = ["Relax Equip. Conditions +{v}%", "", "", "裝備條件放緩+{v}%"]

# JP text: 効果時間延長＋{v}日
paid_pass_name_install_time_formats = ["Timed Effect Extension +{v} Days", "", "", "效果時間延長+{v}日"]

# JP text: シート所持数拡張{v}
paid_pass_name_collect_sheet_formats = ["Expansion Sheet {v}", "", "", "收集單持有數量擴充{v}"]

# JP text: クエスト報酬獲得{v}
paid_pass_name_quest_reward_formats = ["Quest Reward {v}", "", "", "任務報酬獲得{v}"]

# JP text: {abbr}クラスレベル{v}化
paid_pass_name_class_level_formats = ["{abbr} Class Level {v}", "", "", "{abbr}職業等級升至{v}"]

# JP text: {abbr}クラスレベル{v}化＆適正装備セット
paid_pass_name_class_level_set_formats = ["{abbr} Class Lv.{v} & Equipment Set", "", "", "{abbr}職業等級升至{v}&適配裝備套裝"]

# JP text: クラスレベル{v}化
paid_pass_name_all_class_level_formats = ["Class Level {v}", "", "", "職業等級升至{v}"]

# JP text: クラスレベル{v}化＆適正装備セット
paid_pass_name_all_class_level_set_formats = ["Class Lv.{v} & Equipment Set", "", "", "職業等級升至{v}&適配裝備套裝"]

# JP text: 属性変化（{element}属性）
paid_pass_name_element_change_formats = ["Attribute Change ({element})", "", "", "屬性變化（{element}屬性）"]

# JP text: クラス追加（{cls}）
paid_pass_name_extend_class_formats = ["Add Class ({cls})", "", "", "職業追加（{cls}）"]

# JP text: 装備条件変更（{condition}）
paid_pass_name_extend_condition_formats = ["Equip. Condition Swap ({condition})", "", "", "裝備條件變更（{condition}）"]

# JP text: 強化値上限＋{v}／{weapon}
paid_pass_name_ngrind_weapon_cap_formats = ["Grind Cap +{v}/{weapon}", "", "", "強化値上限+{v}/{weapon}"]

# JP text: {event}'{year}{kind}スクラッチ券
paid_pass_name_scratch_year_formats = ["{event} '{year} {kind} Scratch Ticket", "", "", "{event}'{year}{kind}轉蛋券"]

# JP text: {series}{kind}スクラッチ券
paid_pass_name_scratch_series_formats = ["{series} {kind} Scratch Ticket", "", "", "{series}{kind}轉蛋券"]

# JP text: 『{game}』{n}周年{kind}スクラッチ券
paid_pass_name_scratch_anniv_formats = ["[{game}] {n} Anniv. {kind} Scratch Ticket", "", "", "『{game}』{n}週年{kind}轉蛋券"]

# JP text: {kind}スクラッチ券
paid_pass_name_scratch_formats = ["{kind} Scratch Ticket", "", "", "{kind}轉蛋券"]

# JP text: {event}'{year}{kind}スクラッチ補助券
paid_pass_name_voucher_year_formats = ["{event} '{year} {kind} Scratch Voucher", "", "", "{event}'{year}{kind}轉蛋輔助券"]

# JP text: {series}{kind}スクラッチ補助券
paid_pass_name_voucher_series_formats = ["{series} {kind} Scratch Voucher", "", "", "{series}{kind}轉蛋輔助券"]

# JP text: {kind}スクラッチ補助券
paid_pass_name_voucher_formats = ["{kind} Scratch Voucher", "", "", "{kind}轉蛋輔助券"]

# JP text: トレジャースクラッチ券Vol.{v}
paid_pass_name_treasure_scratch_formats = ["Treasure Scratch Ticket Vol.{v}", "", "", "寶物轉蛋券Vol.{v}"]

# JP text: {n}周年サンクフルスクラッチ券{month}
paid_pass_name_thankful_scratch_formats = ["{n} Anniv. Thankful Scratch {month} Ticket", "", "", "{n}週年感謝轉蛋券{month}"]

# JP text: ビッグバンスクラッチ・{bigbang}券
paid_pass_name_bigbang_formats = ["Big Bang Scratch {bigbang} Ticket", "", "", "大爆炸轉蛋·{bigbang}券"]

# JP text: ビッグバンスクラッチ・{bigbang}券{month}'{year}
paid_pass_name_bigbang_month_formats = ["Big Bang Scratch {bigbang} {month} '{year} Ticket", "", "", "大爆炸轉蛋·{bigbang}券{month}'{year}"]

# JP text: N-メセタスクラッチ券{month}'{year}
paid_pass_name_meseta_scratch_month_formats = ["N-Meseta Scratch {month} '{year} Ticket", "", "", "N-美賽達轉蛋券{month}'{year}"]

# JP text: リワードボックスメダル{month}'{year}
paid_pass_name_medal_month_formats = ["Reward Box Medal {month} '{year}", "", "", "獎品盒獎章{month}'{year}"]

# JP text: リワードボックスメダル・{boss}
paid_pass_name_medal_boss_formats = ["Reward Box Medal {boss}", "", "", "獎品盒獎章·{boss}"]

# JP text: リワードボックスメダル・{boss}'{year}
paid_pass_name_medal_boss_year_formats = ["Reward Box Medal {boss} '{year}", "", "", "獎品盒獎章·{boss}'{year}"]

paid_pass_name_patterns = {
    r"N-★(?P<r>\d+)限界突破代用材/限界値(?P<v>\d+)": "limitbreak",
    r"N-限界突破代用材/限界値(?P<v>\d+)": "nlimitbreak",
    r"N-★(?P<r>\d+)潜在能力解放代用材/Lv\.(?P<v>\d+)": "potential",
    r"N-潜在能力解放代用材/Lv\.(?P<v>\d+)": "npotential",
    r"★(?P<r>\d+)武器強化スキップ＋(?P<v>\d+)": "skip_weapon",
    r"★(?P<r>\d+)防具強化スキップ＋(?P<v>\d+)": "skip_armor",
    r"プリセット能力強化成功率＋(?P<v>\d+)％": "preset",
    r"プリセット能力強化アイテム保護/Lv\.(?P<v>\d+)": "preset_protect",
    r"プリセット能力強化成功＆代用材/Lv\.(?P<v>\d+)": "preset_success",
    r"能力追加成功率＋(?P<v>\d+)％": "affix_rate",
    r"能力追加成功（(?P<v>\d+)％）": "affix_sure",
    r"N-特殊能力追加成功率＋(?P<v>\d+)[%％]": "naffix_rate",
    r"特殊能力保護（(?P<v>\d+)枠以下）": "affix_return",
    r"カスタムタイプ(?P<t>\d+)＋(?P<v>\d+)％": "customize",
    r"メリット値＋(?P<v>\d+)％": "tech_merit",
    r"デメリット値－(?P<v>\d+)％": "tech_demerit",
    r"合成可能数回復(?P<v>\d+)": "pet",
    r"採取スタドリ(?P<v>\d+)": "harvest_stamina",
    r"釣りスタドリ(?P<v>\d+)": "fishing_stamina",
    r"ＳＧトレジャー更新(?P<v>\d+)": "treasure_shop_sg",
    r"メセタトレジャー更新(?P<v>\d+)": "treasure_shop_meseta",
    r"スキルリング強化代用材/＋(?P<v>\d+)": "skill_ring",
    r"N-強化大成功率＋(?P<v>\d+)[%％]": "ngrind_great",
    r"強化成功率＋(?P<v>\d+)％": "grind_rate",
    r"強化成功（(?P<v>\d+)％）": "grind_sure",
    r"強化スキップ（→(?P<v>\d+)）": "grind_jump",
    r"強化リスク軽減（＋(?P<v>\d+)）": "grind_protect",
    r"属性強化＋(?P<v>\d+)％": "element_rate",
    r"強化大成功確率＋(?P<v>\d+)％": "ngrind_rate",
    r"強化大成功（(?P<v>\d+)％）": "ngrind_sure",
    r"強化値上限＋(?P<v>\d+)": "ngrind_cap",
    r"★(?P<r>\d+)武器購入パス": "purchase_weapon",
    r"★(?P<r>\d+)ユニット購入パス": "purchase_unit",
    r"装備条件緩和＋(?P<v>\d+)％": "extend_ease",
    r"効果時間延長＋(?P<v>\d+)日": "install_time",
    r"シート所持数拡張(?P<v>\d+)": "collect_sheet",
    r"クエスト報酬獲得(?P<v>\d+)": "quest_reward",
    r"(?P<abbr>[A-Za-z]+)クラスレベル(?P<v>\d+)化": "class_level",
    r"(?P<abbr>[A-Za-z]+)クラスレベル(?P<v>\d+)化＆適正装備セット": "class_level_set",
    r"クラスレベル(?P<v>\d+)化": "all_class_level",
    r"クラスレベル(?P<v>\d+)化＆適正装備セット": "all_class_level_set",
    r"属性変化（(?P<element>.)属性）": "element_change",
    r"クラス追加（(?P<cls>.+)）": "extend_class",
    r"装備条件変更（(?P<condition>.+)）": "extend_condition",
    r"強化値上限＋(?P<v>\d+)／(?P<weapon>.+)": "ngrind_weapon_cap",
    r"トレジャースクラッチ券Vol\.(?P<v>\d+)": "treasure_scratch",
    r"(?P<n>\d+)周年サンクフルスクラッチ券(?P<month>[A-Z][a-z]+)": "thankful_scratch",
    r"ビッグバンスクラッチ・(?P<bigbang>[^券]+)券": "bigbang",
    r"ビッグバンスクラッチ・(?P<bigbang>[^券]+)券(?P<month>[A-Z][a-z]+)'(?P<year>\d+)": "bigbang_month",
    r"N-メセタスクラッチ券(?P<month>[A-Z][a-z]+)'(?P<year>\d+)": "meseta_scratch_month",
    r"(?P<event>[^']+)'(?P<year>\d+(?:-'\d+)?)(?P<kind>スペシャル|SP)スクラッチ券": "scratch_year",
    r"『(?P<game>NGS|PSO2)』(?P<n>\d+)周年(?P<kind>スペシャル|SP)スクラッチ券": "scratch_anniv",
    r"(?P<kind>スペシャル|SP)スクラッチ券": "scratch",
    r"(?P<series>.+?)(?P<kind>スペシャル|SP)スクラッチ券": "scratch_series",
    r"(?P<event>[^']+)'(?P<year>\d+(?:-'\d+)?)(?P<kind>スペシャル|SP)スクラッチ補助券": "voucher_year",
    r"(?P<kind>スペシャル|SP)スクラッチ補助券": "voucher",
    r"(?P<series>.+?)(?P<kind>スペシャル|SP)スクラッチ補助券": "voucher_series",
    r"リワードボックスメダル(?P<month>[A-Z][a-z]+)'(?P<year>\d+)": "medal_month",
    r"リワードボックスメダル・(?P<boss>[^']+)": "medal_boss",
    r"リワードボックスメダル・(?P<boss>[^']+)'(?P<year>\d+)": "medal_boss_year"
    }

def translate_paid_pass_name(item, name_prefix):
    return translate_name(item, name_prefix, paid_pass_name_patterns, "paid_pass_name_", paid_pass_name_value_names)

def translate_paid_pass_desc(item, name_prefix):
    # Name isn't translated and we're not working in CN, skip this one
    if TRANS_ALL == False and item["tr_text"] == "" and LANG != 3:
        return -1

    # Description already present, leave it alone
    if REDO_ALL == False and item["tr_explain"] != "":
        return -2

    # Placeholder text, nothing to translate
    if item["jp_explain"] in ["仮テキスト", "仮設定"]:
        return -3

    # Sort the description format
    desc_sort = ""
    for pattern in paid_pass_desc_patterns:
        match = regex.fullmatch(pattern, item["jp_explain"], flags = regex.S)
        if match:
            desc_sort = paid_pass_desc_patterns[pattern]
            break

    if desc_sort == "":
        return -4

    # No translation for this language
    if eval("paid_pass_desc_" + desc_sort + "_formats")[LANG] == "":
        return -1

    values = translate_values(match.groupdict(), paid_pass_value_names)

    if values is None:
        return -4

    # Parts that come from the item's name
    if desc_sort in paid_pass_name_parts:
        key, jp_pattern, patterns = paid_pass_name_parts[desc_sort]
        values[key] = get_name_part(item, name_prefix, jp_pattern, patterns, match.group(key))

        if values[key] is None:
            return -4

    # Combine the variable name.
    desc_format_name = "paid_pass_desc_" + desc_sort + "_formats"

    # Translate the description.
    item["tr_explain"] = eval(desc_format_name)[LANG].format(**values)

    return 0

try:
    items_file = codecs.open(os.path.join(json_loc, "Item_Stack_PaidPass.txt"),
                             mode = 'r', encoding = 'utf-8')
except FileNotFoundError:
    print("\tItem_Stack_PaidPass.txt not found.")

items = json.load(items_file)
print("Item_Stack_PaidPass.txt loaded. {")

items_file.close()

newtranslations = False

for item in items:
    tr_text = item["tr_text"]
    fill_cn_name(item)
    name_prefix = split_name_prefix(item)
    name_prefix = translate_paid_pass_name(item, name_prefix)
    problem = translate_paid_pass_desc(item, name_prefix)
    item["tr_explain"] = name_prefix + item["tr_explain"]
    unfill_cn_name(item, tr_text)

    if problem == 0:
        print("\tTranslated description for {0}".format(item["tr_text"] or item["jp_text"]))
        newtranslations = True
    elif problem == -4:
        print("\t{0} has a new kind of description".format(item["tr_text"] or item["jp_text"]))

if newtranslations == False:
    print("\tNo new translations.")

print("}")

items_file = codecs.open(os.path.join(json_loc, "Item_Stack_PaidPass.txt"),
                         mode = 'w', encoding = 'utf-8')
json.dump(items, items_file, ensure_ascii=False, indent="\t", sort_keys=False)
items_file.write("\n")
items_file.close()

####################################################################################################

# Translate tools

# Classes
tool_classes = {
    "ハンター": ["Hunters", "", "", "獵人(Hu)"],
    "レンジャー": ["Rangers", "", "", "遊俠(Ra)"],
    "フォース": ["Forces", "", "", "法師(Fo)"],
    "ファイター": ["Fighters", "", "", "鬥士(Fi)"],
    "ガンナー": ["Gunners", "", "", "鷹眼(Gu)"],
    "テクター": ["Techters", "", "", "元素使(Te)"],
    "ブレイバー": ["Bravers", "", "", "武士(Br)"],
    "バウンサー": ["Bouncers", "", "", "凌客(Bo)"],
    "サモナー": ["Summoners", "", "", "召喚師(Su)"],
    "ヒーロー": ["Heroes", "", "", "英雄(Hr)"],
    "ファントム": ["Phantoms", "", "", "幻影(Ph)"],
    "エトワール": ["Etoiles", "", "", "閃星(Et)"],
    "ラスター": ["Lusters", "", "", "輝刃(Lu)"],
    "ウェイカー": ["Wakers", "", "", "喚士(Wa)"],
    "スレイヤー": ["Slayers", "", "", "殺手(Sl)"]
    }

# Item Trader menus. Menus named after the item ({name}交換) come from its name.
# An empty menu has no translation in that language.
tool_trader_menus = {
    "遠征準備特別票交換": ["", "", "", "遠征準備特別票交換"],
    "開発準備特別票交換": ["Development Prep. Special Emblem Exchange", "", "", "開發準備特別票交換"],
    "レガシーアイテム交換": ["Legacy Item Exchange", "", "", "經典道具交換"],
    "N-ウェポンズバッヂ交換": ["N-Weapons Badge Exchange", "", "", "N-武器徽章交換"],
    "装備アップグレード": ["Equipment Upgrade", "", "", "裝備升級"],
    "装備アップグレードⅡ": ["Equipment Upgrade II", "", "", "裝備升級2"],
    "レジェンダリー３武器へ強化": ["Legendary 3 Weapon Upgrade", "", "", "強化至傳奇3武器"],
    "フォルタス防具強化": ["Fortas Armor Upgrade", "", "", "進步(原名:フォルタス)防具強化"],
    "スプラディオ武器強化": ["Sproudio Weapon Upgrade", "", "", "秘芽(原名:スプラディオ)武器強化"],
    "エヴァルト防具強化": ["Exalt Armor Upgrade", "", "", ""],
    "コウゲンセイ武器強化": ["Kougensei Weapon Upgrade", "", "", ""],
    "レアレンス武器交換": ["Learenz Weapon Exchange", "", "", ""],
    "レアレンス武器強化": ["Learenz Weapon Upgrade", "", "", ""],
    "カイズ武器強化": ["Kyz Weapon Upgrade", "", "", ""]
    }

# JP text: {name}交換
tool_trader_name_menu_formats = ["{name} Exchange", "", "", "{name}交換"]

# First line of the descriptions of items exchanged at the Item Trader
tool_trader_item_descs = {
    "活躍したアークスに贈られる証。": ["Insignia given to accomplished ARKS.", "", "", "賜予活躍ARKS的證明。"],
    "活躍したアークスに贈られるバッヂ。": ["Badge given to accomplished ARKS.", "", "", "贈予活躍ARKS的徽章。"],
    "ダークファルス・エイジスの基幹部品。": ["A keystone component of Dark Falz Aegis.", "", "", "黑暗法爾斯·神盾的基礎部件。"],
    "ギガンティクスなどの複合装甲の一部。": ["A fragment of plating from a Gigantix.", "", "", "絕巨體等敵人複合裝甲的一部分。"],
    "ルシエル内部で入手可能な複合素材の一部。": ["Composite material found in Leciel.", "", "", "可於天堡內部獲得的複合素材的一部分。"],
    "ルシエルなどで入手可能な複合素材の一部。": ["Composite material found in Leciel.", "", "", "可於天堡等處獲得的複合素材的一部分。"],
    "表面に特徴的な紋章が刻印されたバッヂ。": ["A badge bearing a distinctive crest.", "", "", "正面銘刻著獨特紋章的徽章。"]
    }

tool_equipment = {
    "武器": ["weapons", "", "", "武器"],
    "防具": ["armor", "", "", "防具"],
    "装備": ["equipment", "", "", "裝備"]
    }

tool_material_uses = {
    "強化": ["upgrading", "", "", "強化"],
    "入手と強化": ["upgrading", "", "", "獲得與強化"],
    "入手": ["upgrading", "", "", "獲得"]
    }

tool_trigger_colors = {
    "イエロー": ["Yellow", "", "", "黃"],
    "パープル": ["Purple", "", "", "紫"]
    }

tool_badge_metals = {
    "金": ["gold", "", "", "金"],
    "銀": ["silver", "", "", "銀"]
    }

tool_badge_colors = {
    "青": ["blue", "", "", "藍"],
    "橙": ["orange", "", "", "橙"],
    "黄": ["yellow", "", "", "黃"],
    "緑": ["green", "", "", "綠"],
    "白": ["white", "", "", "白"],
    "赤": ["red", "", "", "紅"],
    "桃": ["pink", "", "", "粉"]
    }

tool_disc_weapons = {
    "打撃": ["striking", "", "", "打擊"],
    "射撃": ["shooting", "", "", "射擊"],
    "法撃": ["Tech", "", "", "法擊"],
    "すべての": ["all", "", "", "所有"]
    }

tool_value_names = {
    "desc": tool_trader_item_descs,
    "equip": tool_equipment,
    "equip2": tool_equipment,
    "use": tool_material_uses,
    "color": tool_trigger_colors,
    "cls": tool_classes,
    "metal": tool_badge_metals,
    "badge_color": tool_badge_colors,
    "weapon": tool_disc_weapons
    }

# Parts of the description that come from the item's name:
# (value, pattern in the JP name, patterns in the translated name)
tool_name_parts = {
    # Qトリガー/{quest}
    "quest_trigger": ("quest", r"Qトリガー/(.+)",
                      [r"Q\. Trigger/(.+)", r"", r"", r"Q觸發器/(.+)"])
    }

# Menus named after the item ({name}交換)
tool_trader_name_patterns = [r"(.+)", r"(.+)", r"(.+)", r"(.+)"]

# JP text:
    # アイテムトレーダーの\n
    # “{menu}”で\n
    # アイテムと交換できる。
tool_desc_trader_formats = [("Can be traded for items at the\n"
                             "{menu}."),
                            (""),
                            (""),
                            ("可在道具交易商的\n"
                             "“{menu}”處交換道具。")]

# JP text:
    # {desc}\n
    # アイテムトレーダーの\n
    # “{menu}”で\n
    # アイテムと交換できる。
tool_desc_trader_desc_formats = [("{desc}\n"
                                  "Can be traded for items at the\n"
                                  "{menu}."),
                                 (""),
                                 (""),
                                 ("{desc}\n"
                                  "可在道具交易商的\n"
                                  "“{menu}”處交換道具。")]

# JP text:
    # {desc}\n
    # アイテムトレーダーの\n
    # “{menu}”で\n
    # ★{rank}武器などと交換できる。
tool_desc_trader_rank_weapons_formats = [("{desc}\n"
                                          "Can be exchanged for items like\n"
                                          "{rank}-star weapons at Item Traders."),
                                         (""),
                                         (""),
                                         ("{desc}\n"
                                          "可在道具交易商的\n"
                                          "“{menu}”處\n"
                                          "交換★{rank}武器等。")]

# JP text:
    # {desc}\n
    # アイテムトレーダーの\n
    # “{menu}”で\n
    # 武器などと交換できる。
tool_desc_trader_weapons_formats = [("{desc}\n"
                                     "Can be exchanged for items at the\n"
                                     "{menu}."),
                                    (""),
                                    (""),
                                    ("{desc}\n"
                                     "可在道具交易商的\n"
                                     "“{menu}”處\n"
                                     "交換武器等。")]

# JP text:
    # 特定の{equip}の{use}に必要な素材。\n
    # アイテムトレーダーの\n
    # “{menu}”で\n
    # {equip}の交換に用いる。
tool_desc_upgrade_formats = [("Material for {use} specific {equip}.\n"
                              "Used when exchanging items at the Item\n"
                              "Lab with \"{menu}\"."),
                             (""),
                             (""),
                             ("{use}特定{equip}所必須的素材。\n"
                              "在道具交易商的\n"
                              "“{menu}”處{menu_break}用於交換{equip2}。")]

# JP text:
    # クエストカウンターで用いるトリガー。\n
    # “想定演習：\n
    # {quest}”の\n
    # クリア時に消費される。
tool_desc_quest_trigger_formats = [("Trigger used at Quest Counters.\n"
                                    "Consumed upon clearing the Quest\n"
                                    "\"Simulation:\n"
                                    "{quest}\"."),
                                   (""),
                                   (""),
                                   ("在任務櫃檯處使用的觸發器。\n"
                                    "會在完成“設想演習: \n"
                                    "{quest}”時消耗。")]

# JP text:
    # アイテムリサイクルで\n
    # “Bトリガー/コモン{color}“\n
    # と交換できる。\n
    # <yellow>※Bトリガーとしては使用不可<c>
tool_desc_battle_trigger_formats = [("Can be exchanged for \"B. Trigger/\n"
                                     "Common {color}\" at Item Recycling.\n"
                                     "<yellow>※Cannot be used as a Battle Trigger.<c>"),
                                    (""),
                                    (""),
                                    ("可在道具回收中\n"
                                     "交換“B觸發器/通用{color}”。\n"
                                     "<yellow>※不可作為B觸發器使用<c>")]

# JP text:
    # {cls}クラスの求道者に\n
    # 与えられる特殊な結晶体。\n
    # クラスカウンターで\n
    # アドオンスキルの取得に用いる。
tool_desc_excube_formats = [("A special crystal given to {cls}\n"
                             "who seek strength. Used at Class\n"
                             "Counters to create Add-On Skills."),
                            (""),
                            (""),
                            ("一種特殊的結晶體，會賦予給\n"
                             "{cls}職業的求道者。\n"
                             "在職業櫃檯中用於獲得附件技能。")]

# JP text:
    # {cls}を極めし者に与えられる\n
    # 特殊な結晶体。提示することで\n
    # さらなる力を得ることができる。
tool_desc_old_excube_formats = [("A special crystal given to extreme\n"
                                 "{cls}. By trading this item, more\n"
                                 "power can be obtained."),
                                (""),
                                (""),
                                ("一種特殊的結晶體，會賦予給\n"
                                 "將{cls}登峰造極之人。\n"
                                 "出示後可獲得更為強大的力量。")]

# JP text:
    # 特別な条件を満たした者だけが\n
    # 手にすることができるアークスの\n
    # ロゴが彫り込まれた{badge_color}色のバッヂ。
tool_desc_arks_badge_formats = [("Used as currency at the Badge Shop."),
                                (""),
                                (""),
                                ("雕刻著ARKS徽標的{badge_color}色徽章。\n"
                                 "只有滿足了特別條件之人\n"
                                 "才可獲得。")]

# JP text:
    # 表面に特徴的な紋章、裏面に謎の年号が\n
    # 刻印されたバッヂ。提示することで\n
    # 様々なアイテムと交換可能。
tool_desc_badge_formats = [("An emblem with an engraved design.\n"
                            "A mysterious year is printed on the\n"
                            "back. Can be traded for prizes."),
                           (""),
                           (""),
                           ("正面銘刻著獨特紋章，\n"
                            "背面銘刻著神秘年號的徽章。\n"
                            "出示後可交換各種各樣的道具。")]

# JP text:
    # 表面に特徴的な紋章、裏面に謎の年号が\n
    # 刻印された{metal}バッヂ。提示することで\n
    # 様々なアイテムと交換可能。
tool_desc_metal_badge_formats = [("A {metal} emblem with an engraved\n"
                                  "design. A mysterious year is printed\n"
                                  "on the back. Can be traded for prizes."),
                                 (""),
                                 (""),
                                 ("正面銘刻著獨特紋章，\n"
                                  "背面銘刻著神秘年號的{metal}徽章。\n"
                                  "出示後可交換各種各樣的道具。")]

# JP text:
    # {n}周年記念に作られた、特徴的な紋章が\n
    # 刻印されたバッヂ。提示することで\n
    # 様々なアイテムと交換可能。
tool_desc_anniversary_badge_formats = [("A badge that was engraved with a\n"
                                        "crest in commemoration of the {n}th\n"
                                        "Anniv. Can be exchanged for prizes."),
                                       (""),
                                       (""),
                                       ("為{n}週年紀念而製作的，\n"
                                        "銘刻著獨特紋章的徽章。\n"
                                        "出示後可交換各種各樣的道具。")]

# JP text:
    # 条件を達成した者に与えられる証書。\n
    # ゲートエリアのレオンティーナに渡すと\n
    # 強力な★{r}武器などを入手できる。
tool_desc_certificate_formats = [("A certificate handed out under\n"
                                  "special conditions. Give it to\n"
                                  "Leontina for powerful ★{r} items."),
                                 (""),
                                 (""),
                                 ("賦予給達成條件之人的證書。\n"
                                  "交給出發區域的雷歐緹娜後\n"
                                  "可獲得強力的★{r}武器等。")]

# JP text:
    # なんらかの機械の動力炉。\n
    # <yellow>{n}万<c>N-メセタで\n
    # 売却することができる。
tool_desc_reactor_formats = [(""),
                             (""),
                             (""),
                             ("某種機械的動力爐。\n"
                              "可以出售為<yellow>{n}萬<c>N-美賽達。")]

# JP text:
    # 武器や防具の加工強化に用いる素材。\n
    # 強化を行うことで、限界以上の性能を\n
    # 引き出すことができる。
tool_desc_grinder_formats = [("Material used to improve equipment.\n"
                              "The performance of equipment\n"
                              "can be pushed beyond its limit."),
                             (""),
                             (""),
                             ("用於武器與防具加工強化的素材。\n"
                              "通過強化，可以發揮出\n"
                              "超出界限的性能。")]

# JP text:
    # 自律起動の自己復活用アイテム。\n
    # 所持者が戦闘不能になった際に\n
    # 一度だけ身代わりになってくれる。
tool_desc_doll_formats = [("A self-revival item. When you\n"
                           "become incapacitated, you can use\n"
                           "this substitute instead of yourself."),
                          (""),
                          (""),
                          ("自動起效的自我復活道具。\n"
                           "在持有者無法戰鬥時\n"
                           "會僅限一次成為替身。")]

# JP text:
    # 励起状態のフォトン結晶。\n
    # 周囲のフォトンに働きかけ\n
    # 対象の励起反応を促進させる素材。
tool_desc_excited_photon_formats = [("Photon Crystals in an excited state.\n"
                                     "Surrounding Photon activity in\n"
                                     "certain weapons cause a reaction."),
                                    (""),
                                    (""),
                                    ("激發狀態光子的結晶。\n"
                                     "會影響周圍的光子，\n"
                                     "是促進對象產生激發反應的素材。")]

# JP text:
    # バスタークエストで協力した証。\n
    # 提示することによって\n
    # 様々なアイテムと交換可能。
tool_desc_buster_formats = [("Proof that one participated in a\n"
                             "Buster Quest. You can trade it\n"
                             "in for various prizes."),
                            (""),
                            (""),
                            ("協助了攻城任務的證明。\n"
                             "出示後可交換各種各樣的道具。")]

# JP text:
    # 表面に特徴的な絵が描かれている\n
    # 何らかの記憶媒体。内部データから\n
    # 楽しいものが作れそう。
tool_desc_memory_media_formats = [("A storage device with a distinctive\n"
                                   "image on its surface. The data inside\n"
                                   "could be used to make fun things."),
                                  (""),
                                  (""),
                                  ("正面畫著獨特圖畫的某種記錄媒體。\n"
                                   "用內部的資料似乎能\n"
                                   "製作出些有意思的東西。")]

# JP text:
    # 様々な戦場で活躍したアークスの証。\n
    # 提示することで、ジグの持つ\n
    # 貴重なアイテムと交換ができる。
tool_desc_zieg_formats = [("Proof of an ARKS who took part in\n"
                           "many great battles. Can be traded\n"
                           "to Zieg in exchange for items."),
                          (""),
                          (""),
                          ("活躍在種種戰場上的ARKS的證明。\n"
                           "出示後可交換\n"
                           "奇格所擁有的貴重道具。")]

# JP text:
    # 戦闘セクションなどで入手可能な\n
    # 複合装甲のかけら。精錬することで\n
    # アームズリファイナーに加工される。
tool_desc_armor_fragment_formats = [("A fragment of composite plating\n"
                                     "found in Combat Areas. Can be\n"
                                     "refined into an Arms Refiner."),
                                    (""),
                                    (""),
                                    ("可在戰鬥區域等地獲得的\n"
                                     "複合裝甲的碎片。\n"
                                     "精煉後會被加工為武裝精煉塊。")]

# JP text:
    # エンシェントエネミーなどから\n
    # 入手可能な謎めいたエネルギー物質。\n
    # クヴァリスのレソに提示することで\n
    # 様々なアイテムと交換できる。
tool_desc_energy_matter_formats = [("A form of condensed energy from\n"
                                    "Ancient Enemies in Kvaris. Used for\n"
                                    "trading with Leso at Kvaris Camp."),
                                   (""),
                                   (""),
                                   ("可以從遠古型敵人等處獲得的\n"
                                    "神秘能量物質。\n"
                                    "向克瓦利斯的萊索出示後\n"
                                    "便可交換各種各樣的道具。")]

# JP text:
    # クラスカウンターで{weapon}武器の\n
    # テックアーツカスタマイズに用いる。
tool_desc_ta_disc_formats = [("Used at the Class Counter to perform\n"
                              "Tech Arts Customization for {weapon}\n"
                              "weapons."),
                             (""),
                             (""),
                             ("在職業櫃檯中用於對{weapon}武器\n"
                              "進行法術PA自定義。")]

# JP text:
    # クラスカウンターで{weapon}武器の\n
    # 高度なテックアーツカスタマイズに用いる。
tool_desc_ta_disc_advanced_formats = [("Used at the Class Counter to perform\n"
                                       "advanced Tech Arts Customization for\n"
                                       "{weapon} weapons."),
                                      (""),
                                      (""),
                                      ("在職業櫃檯中用於對{weapon}武器\n"
                                       "進行高度的法術PA自定義。")]

# JP text:
    # クラスカウンターで{weapon}武器の\n
    # さらに高度なテックアーツカスタマイズに\n
    # 用いる。
tool_desc_ta_disc_very_advanced_formats = [("Used at the Class Counter to perform\n"
                                            "very advanced Tech Arts Customization\n"
                                            "for {weapon} weapons."),
                                           (""),
                                           (""),
                                           ("在職業櫃檯中用於對{weapon}武器\n"
                                            "進行更為高度的法術PA自定義。")]

tool_desc_patterns = {
    r"アイテムトレーダーの\n“(?P<menu>[^”]+)”で\nアイテムと交換できる。": "trader",
    r"(?P<desc>[^\n]+)\nアイテムトレーダーの\n“(?P<menu>[^”]+)”で\nアイテムと交換できる。": "trader_desc",
    r"(?P<desc>[^\n]+)\nアイテムトレーダーの\n“(?P<menu>[^”]+)”で\n★(?P<rank>\d+)武器などと交換できる。": "trader_rank_weapons",
    r"(?P<desc>[^\n]+)\nアイテムトレーダーの\n“(?P<menu>[^”]+)”で\n武器などと交換できる。": "trader_weapons",
    r"特定の(?P<equip>武器|防具|装備)の(?P<use>入手と強化|強化|入手)に必要な素材。\nアイテムトレーダーの\n“(?P<menu>[^”]+)”で\n(?P<equip2>武器|防具|装備)の交換に用いる。": "upgrade",
    r"クエストカウンターで用いるトリガー。\n“想定演習：\n(?P<quest>.+)”の\nクリア時に消費される。": "quest_trigger",
    r"アイテムリサイクルで\n“Bトリガー/コモン(?P<color>イエロー|パープル)“\nと交換できる。\n<yellow>※Bトリガーとしては使用不可<c>": "battle_trigger",
    r"(?P<cls>.+)クラスの求道者に\n与えられる特殊な結晶体。\nクラスカウンターで\nアドオンスキルの取得に用いる。": "excube",
    r"(?P<cls>.+)を極めし者に与えられる\n特殊な結晶体。提示することで\nさらなる力を得ることができる。": "old_excube",
    r"特別な条件を満たした者だけが\n手にすることができるアークスの\nロゴが彫り込まれた(?P<badge_color>.)色のバッヂ。": "arks_badge",
    r"表面に特徴的な紋章、裏面に謎の年号が\n刻印されたバッヂ。提示することで\n様々なアイテムと交換可能。": "badge",
    r"表面に特徴的な紋章、裏面に謎の年号が\n刻印された(?P<metal>金|銀)バッヂ。提示することで\n様々なアイテムと交換可能。": "metal_badge",
    r"(?P<n>\d+)周年記念に作られた、特徴的な紋章が\n刻印されたバッヂ。提示することで\n様々なアイテムと交換可能。": "anniversary_badge",
    r"条件を達成した者に与えられる証書。\nゲートエリアのレオンティーナに渡すと\n強力な★(?P<r>\d+)武器などを入手できる。": "certificate",
    r"なんらかの機械の動力炉。\n<yellow>(?P<n>\d+)万<c>N-メセタで\n売却することができる。": "reactor",
    r"武器や防具の加工強化に用いる素材。\n強化を行うことで、限界以上の性能を\n引き出すことができる。": "grinder",
    r"自律起動の自己復活用アイテム。\n所持者が戦闘不能になった際に\n一度だけ身代わりになってくれる。": "doll",
    r"励起状態のフォトン結晶。\n周囲のフォトンに働きかけ\n対象の励起反応を促進させる素材。": "excited_photon",
    r"バスタークエストで協力した証。\n提示することによって\n様々なアイテムと交換可能。": "buster",
    r"表面に特徴的な絵が描かれている\n何らかの記憶媒体。内部データから\n楽しいものが作れそう。": "memory_media",
    r"様々な戦場で活躍したアークスの証。\n提示することで、ジグの持つ\n貴重なアイテムと交換ができる。": "zieg",
    r"戦闘セクションなどで入手可能な\n複合装甲のかけら。精錬することで\nアームズリファイナーに加工される。": "armor_fragment",
    r"エンシェントエネミーなどから\n入手可能な謎めいたエネルギー物質。\nクヴァリスのレソに提示することで\n様々なアイテムと交換できる。": "energy_matter",
    r"クラスカウンターで(?P<weapon>打撃|射撃|法撃|すべての)武器の\nテックアーツカスタマイズに用いる。": "ta_disc",
    r"クラスカウンターで(?P<weapon>打撃|射撃|法撃|すべての)武器の\n高度なテックアーツカスタマイズに用いる。": "ta_disc_advanced",
    r"クラスカウンターで(?P<weapon>打撃|射撃|法撃|すべての)武器の\nさらに高度なテックアーツカスタマイズに\n用いる。": "ta_disc_very_advanced"
    }

def translate_tool_desc(item, name_prefix):
    # Name isn't translated and we're not working in CN, skip this one
    if TRANS_ALL == False and item["tr_text"] == "" and LANG != 3:
        return -1

    # Description already present, leave it alone
    if REDO_ALL == False and item["tr_explain"] != "":
        return -2

    # Sort the description format
    desc_sort = ""
    for pattern in tool_desc_patterns:
        match = regex.fullmatch(pattern, item["jp_explain"], flags = regex.S)
        if match:
            desc_sort = tool_desc_patterns[pattern]
            break

    if desc_sort == "":
        return -4

    # No translation for this language
    if eval("tool_desc_" + desc_sort + "_formats")[LANG] == "":
        return -1

    values = translate_values(match.groupdict(), tool_value_names)

    if values is None:
        return -4

    # Item Trader menus, from the item's name if the menu is named after it
    if "menu" in values:
        menu = match.group("menu")
        name = get_name_part(item, name_prefix, r"(.+)", tool_trader_name_patterns, menu[:-len("交換")]) if menu.endswith("交換") else None

        if name is not None:
            values["menu"] = tool_trader_name_menu_formats[LANG].format(name = name)
        elif menu in tool_trader_menus and tool_trader_menus[menu][LANG] != "":
            values["menu"] = tool_trader_menus[menu][LANG]
        else:
            return -4

    # Long menu names push the rest of the sentence onto the next line
    if desc_sort == "upgrade":
        values["menu_break"] = "\n" if len(values["menu"]) > 10 else ""

    # Parts that come from the item's name
    if desc_sort in tool_name_parts:
        key, jp_pattern, patterns = tool_name_parts[desc_sort]
        values[key] = get_name_part(item, name_prefix, jp_pattern, patterns, match.group(key))

        if values[key] is None:
            return -4

    # Combine the variable name.
    desc_format_name = "tool_desc_" + desc_sort + "_formats"

    # Translate the description.
    item["tr_explain"] = eval(desc_format_name)[LANG].format(**values)

    return 0

try:
    items_file = codecs.open(os.path.join(json_loc, "Item_Stack_Tool.txt"),
                             mode = 'r', encoding = 'utf-8')
except FileNotFoundError:
    print("\tItem_Stack_Tool.txt not found.")

items = json.load(items_file)
print("Item_Stack_Tool.txt loaded. {")

items_file.close()

newtranslations = False

for item in items:
    tr_text = item["tr_text"]
    fill_cn_name(item)
    name_prefix = split_name_prefix(item)
    problem = translate_tool_desc(item, name_prefix)
    item["tr_explain"] = name_prefix + item["tr_explain"]
    unfill_cn_name(item, tr_text)

    if problem == 0:
        print("\tTranslated description for {0}".format(item["tr_text"] or item["jp_text"]))
        newtranslations = True
    elif problem == -4:
        print("\t{0} has a new kind of description".format(item["tr_text"] or item["jp_text"]))

if newtranslations == False:
    print("\tNo new translations.")

print("}")

items_file = codecs.open(os.path.join(json_loc, "Item_Stack_Tool.txt"),
                         mode = 'w', encoding = 'utf-8')
json.dump(items, items_file, ensure_ascii=False, indent="\t", sort_keys=False)
items_file.write("\n")
items_file.close()

print ("Ticket translation complete.")
