#!/usr/bin/env python3
# coding=utf8
import codecs
import json
import os
import regex
import argparse

json_loc = os.path.join("..", "json")

parser = argparse.ArgumentParser(description = "Translates ticket item descriptions.")
# Switch for language.
LANGS = {-1: "JP",
         0: "EN",
         1: "KR"}
# Add more later.
parser.add_argument("-l", type = int, dest = "lang", action = "store", choices = [0, 1], default = 0, metavar = "N", help = "Set a language to translate into. Available options are 0 (EN) and 1 (KR). Defaults to EN.")
# Switch for retranslating all descriptions.
parser.add_argument("-r", dest = "redo", action = "store_true", help = "Force all set descriptions to be processed, even if already translated.")

args = parser.parse_args()
LANG, REDO_ALL = args.lang, args.redo

def no_whitespace(string):
    return string.replace("　", "").replace(" ", "")

json_loc = os.path.join("..", "json")

items_file_names = ["Costume_Female", "Costume_Male",
                    "InnerWear_Female", "InnerWear_Male",
                    "BaseWear_Female", "BaseWear_Male",
                    "Outer_Female", "Outer_Male",
                    "Parts_BodyFemale", "Parts_BodyMale",
                    "Stack_Hairstyle", "Stack_HeadParts",
                    "Stack_Eye", "Stack_Voice",
                    "Stack_Bodypaint", "Stack_FacePaint",
                    "Stack_EyeBrow", "Stack_EyeLash",
                    "Stack_Accessory", "Stack_Sticker",
                    "Stack_PaidPass", "Stack_Roomgoods",
                    "AvatarWPN_AssaultRifle", "AvatarWPN_Compoundbow",
                    "AvatarWPN_DoubleSaber", "AvatarWPN_DualBlade",
                    "AvatarWPN_GunSlash", "AvatarWPN_Jetboots",
                    "AvatarWPN_Katana", "AvatarWPN_Knuckle",
                    "AvatarWPN_Launcher", "AvatarWPN_Partizan",
                    "AvatarWPN_Rod", "AvatarWPN_Sword",
                    "AvatarWPN_Tact", "AvatarWPN_Talis",
                    "AvatarWPN_TwinDagger", "AvatarWPN_TwinMachineGun",
                    "AvatarWPN_Wand", "AvatarWPN_WiredLance",
                    "Stack_DeviceHT", "Stack_DeviceAddTA",
                    "Stack_DeviceFD", "Stack_Reform",
                    "Stack_Music", "Stack_OrderItem",
                    "FacePattern", "Stack_LobbyAction"]

# Load contents files

items_dict = {}

for items_file_name in items_file_names:
    items_file_name = "Item_{0}.txt".format(items_file_name)
       
    try:
        items_file = codecs.open(os.path.join(json_loc, items_file_name),
                                 mode = 'r', encoding = 'utf-8')
    except FileNotFoundError:
        print("\t{0} not found.".format(items_file_name))
        continue

    items = json.load(items_file)
    print("{0} loaded.".format(items_file_name))

    items_file.close()
    
    # Add each item to the dict
    for item in items:
        if item["jp_text"] in items_dict:
            print("Error: Two items named {0}".format(item["jp_text"]))
        else:
            items_dict[no_whitespace(item["jp_text"])] = item["tr_text"]
        continue
    continue
    
set_first_lines = ["Use to receive the following items:",
                   ""]

set_other = [" +{0} other",
             ""]

# Translation function
def translate_set(set):
    if set["tr_explain"] != "" and REDO_ALL == False: # Description already present, leave it alone
        return -2
    
    jp_desc = set["jp_explain"]

    desc_format = "normal"
    
    # Decide what format the item set list is using
    if jp_desc.find("」シリーズ") > -1:
        desc_format = "cast"
        # Handle some cast set formatting here
        jp_desc = jp_desc.replace("」シリーズ", "シリーズ」")
        jp_desc = jp_desc.replace("ＣＶシリーズ", "・ボディＣＶ")
        jp_desc = jp_desc.replace("ＧＶシリーズ", "・ボディＧＶ")
        jp_desc = jp_desc.replace("シリーズ", "・ボディ")
    elif jp_desc.find("」「") > -1:
        desc_format = "2x2"
    elif regex.search(".／.／.／.", jp_desc):
        desc_format = "4color"
    elif regex.search(".／.／.", jp_desc):
        desc_format = "3color"        
    
    # Split off the first line to only get lines with items
    items_raw = jp_desc.split("\n", 1)[1]
    
    items_raw = items_raw.replace("\n", "")

    # Decide if there are unlisted
    other_strings = {
        "他１種": 1,
        "他一種": 1,
        "他二種": 2,
        "他三種": 3,
        "他四種": 4,
        "他五種": 5
        }

    others = 0
    
    for string in other_strings:
       if items_raw.find(string) > -1:
           items_raw = items_raw.replace(string, "")
           others = other_strings[string]

    # Handle multiples of items
    items_raw = regex.sub("」([０１２３４５６７８９]+)個", " x\g<1>」", items_raw)
        
    # Sort out lobby actions a bit

    # TODO: stop screaming and actually fix this

    # I AM SO FUCKING ANGRY
    items_raw = items_raw.replace("レべリオンマスク葉", "レベリオンマスク葉")
    
    # Pick the item entries out
    items = items_raw.split("「")
    items.pop(0)

    # Have to use a second item list because python is DUMB AS HELL
    tr_items = []
    
    # For each item in the list
    for item in items:
        # Remove formatting
        tr_item = item[:-1]

        # Handle multiples
        count = None
        
        if tr_item[-4:-2] == " x":
            count = tr_item[-4:]
            tr_item = tr_item[:-4]
        
        # Only find the first color variant for 3 or 4 color sets
        elif desc_format == "4color" or desc_format == "3color":
            tr_item = tr_item.split("／")[0]
        
        # Find the item in the item dictionary and translate it
        if no_whitespace(tr_item) in items_dict:
            tr_item = items_dict[no_whitespace(tr_item)]

        # Handle multiples again
        if count:
            tr_item += count
            nums = tr_item.maketrans("０１２３４５６７８９", "0123456789")
            tr_item = tr_item.translate(nums)
        
        # For cast parts, take "Body" back out
        if desc_format == "cast":
            tr_item = tr_item.replace("Body CV", "CV parts")
            tr_item = tr_item.replace("Body GV", "GV parts")
            tr_item = tr_item.replace("Body", "parts")

        # For eyelash sets, replace variant color with 4 colors
        elif desc_format == "4color":
            tr_item = tr_item.rsplit(" ", 1)[0] + " (4 colors)"
            
        # 3 color variant sets
        elif desc_format == "3color":
            tr_item = tr_item.rsplit(" ", 1)[0] + " (3 colors)"

        # A weird one-off
        tr_item = tr_item.replace("クラフト初級レシピ用素材", "Elementary Crafting Recipe Material")
        
        tr_items.append(tr_item)
    
    
    # Rebuild the items into the translated format
    tr_desc = set_first_lines[LANG]

    if desc_format == "2x2" and len(tr_items) > 3:
        #tr_desc += "\n・{0} ・{1}\n・{2} ・{3}".format(tr_items[0], tr_items[1],
        tr_desc += "\n[{0}] [{1}]\n[{2}] [{3}]".format(tr_items[0], tr_items[1],
                                                   tr_items[2], tr_items[3])
    else:
        for item in tr_items:
            #tr_desc += "\n・{0}".format(item)
            tr_desc += "\n[{0}]".format(item)
        
    if others > 0:
        tr_desc += set_other[LANG].format(others)

    set["tr_explain"] = tr_desc
    
    return 0

sets_file_name = "Item_Stack_ItemBag.txt"

# Load the item sets into memory
try:
    sets_file = codecs.open(os.path.join(json_loc, sets_file_name),
                            mode = 'r', encoding = 'utf-8')
except FileNotFoundError:
    print("\t{0} not found.".format(items_file_name))
    quit()
    
sets = json.load(sets_file)
print("{0} loaded.".format(sets_file_name) + " {")

sets_file.close()

newtranslations = False
    
for set in sets:
    if translate_set(set) == 0:
        print("\tTranslated {0}".format(set["tr_text"] if set["tr_text"] != ""
                                        else set["jp_text"]))
        newtranslations = True

if newtranslations == False:
    print("\tNo new translations.")

print("}")

sets_file = codecs.open(os.path.join(json_loc, sets_file_name),
                         mode = 'w', encoding = 'utf-8')
json.dump(sets, sets_file, ensure_ascii=False, indent="\t", sort_keys=False)
sets_file.write("\n")
sets_file.close()
