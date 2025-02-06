#!/usr/bin/env python3
# coding=utf8
import codecs
import json
import os
import regex
import shutil

# This is Dabir's PSO2es item set description auto-translator script.
# This script will not translate:
#   Set names (would like to get around to it eventually, though)
#   Lobby actions
#   Items that haven't been translated yet
#   The older way SEGA described eyelash colours
#   A bunch of weird old one-offs like the 3 colours of socks sets
#   Items that are still in the leftovers file
#   Items that don't actually exist
#   Anything I didn't think they'd put in an item set

json_loc = os.path.join("..", "json")

try:
    print("Backing up and loading ItemBags file.")
    itembags_file = codecs.open(
        shutil.copyfile(os.path.join(json_loc,
                                     'Item_Stack_ItemBag.txt'),
                        os.path.join(json_loc,
                                     'Item_Stack_ItemBag.txt.old')),
        mode='r', encoding='utf-8')
except FileNotFoundError:
    print("No ItemBags file found, quitting.")
    raise SystemExit

itembags = itembags_file.read()
itembags_file.close()

print("  ItemBags file loaded and backed up.\n\
  If an error occurs during this script's execution,\n\
  replace Item_Stack_ItemBag.txt with Item_Stack_ItemBag.txt.old\n\
  before taking any other action.")

output_file = codecs.open(os.path.join(json_loc, 'Item_Stack_ItemBag.txt'),
                          mode='w', encoding='utf-8')

print("Performing pre-translation formatting.")
# Copy JP text into TR text
itembags = regex.sub('"jp_explain": "(.+)",(\r)?\n\t\t"tr_explain": ""',
                     r'"jp_explain": "\1",\2\n\t\t"tr_explain": "\1"',
                     itembags)
print("  JP text copied into TR text")
# Replace stock phrase at the start of each description
itembags = regex.sub('"tr_explain": "以下のアイテムを獲得する。',
                     '"tr_explain": "Use to receive the following items:',
                     itembags)
# Replace the *other* stock phrase just for eyelashes
itembags = regex.sub('"tr_explain": "以下のアイテム４種を獲得する。',
                     '"tr_explain": "Use to receive the following 4 items:',
                     itembags)
print("  Stock description beginnings translated")

# Replace JP quotes with EN brackets
# Have to do it 4 separate times otherwise the pre-match parts overlap
# and it only replaces one of each
for x in range(4):
    itembags = regex.sub('"tr_explain": ".+?\K「',
                         r'[',
                         itembags)
    itembags = regex.sub('"tr_explain": ".+?\K」',
                         r']',
                         itembags)
print("  Japanese quotes around item names replaced with English brackets")

# Replace the stock phrases for when there's 4+ items
itembags = regex.sub('\](他一種|他１種)',
                     '] +1 other',
                     itembags)
itembags = regex.sub('\]１０個',
                     '] x10',
                     itembags)
print("  Stock oversized set endings translated")

# Replace eyelash colours with (4 colors)
itembags = regex.sub('／青／茶／白]',
                     '] (4 colors)',
                     itembags)
itembags = regex.sub('／紺／茶／白]',
                     '] (4 colors)',
                     itembags)
print("  Eyelash colours handled")

# Prepare Cast part sets for translation
itembags = regex.sub('\[(.+)ＧＶ\]シリーズ',
                     r'[\1・ボディＧＶ] parts',
                     itembags)
itembags = regex.sub('\[(.+)ＣＶ\]シリーズ',
                     r'[\1・ボディＣＶ] parts',
                     itembags)
itembags = regex.sub('\[(.+)\]シリーズ',
                     r'[\1・ボディ] parts',
                     itembags)
print("  Cast part sets handled")

# Separate adjacent items
itembags = regex.sub('\]\[',
                     '] [',
                     itembags)
print("  Items on same line separated")

print("\nLoading and translating item names.")
contents_files = ("Costume_Female", "Costume_Male",
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
                  "FacePattern")
for contents_file_name in contents_files:
    contents_file_name = "Item_" + contents_file_name + ".txt"
    try:
        contents_file = codecs.open(os.path.join(json_loc, contents_file_name),
                                    mode='r', encoding='utf-8')
    except FileNotFoundError:
        print("\t{0} not found.".format(contents_file_name))
        continue

    contents = json.load(contents_file)
    print("{0} loaded.".format(contents_file_name))

    repcount = 0  # Number of items in ItemBags translated from this file
    for item in contents:
        name_en = item["tr_text"]
        if name_en != "":
            name_jp = regex.escape(item["jp_text"])  # Escape [] in In/Ba/Ou
            repcount += len(regex.findall("\[" + name_jp + "\]", itembags))
            itembags = regex.sub("\[" + name_jp + "\]",
                                 "[" + name_en + "]",
                                 itembags)
    print("  Translated {0} item name{1}."
          .format(repcount,
                  "" if repcount == 1 else "s"))
    contents_file.close()
    print("{0} closed.".format(contents_file_name))

# Clean up eyelash colours and Cast parts
itembags = regex.sub('Black\] \(4 colors\)',
                     '(4 colors)]',
                     itembags)
itembags = regex.sub('Black (.+)\] \(4 colors\)',
                     r'\1 (4 colors)]',
                     itembags)
itembags = regex.sub('\[(.+) Body\] parts',
                     r'\1 parts',
                     itembags)
itembags = regex.sub('\[(.+) Body CV\] parts',
                     r'\1 CV parts',
                     itembags)
itembags = regex.sub('\[(.+) Body GV\] parts',
                     r'\1 GV parts',
                     itembags)

print("All contents files checked.\nSaving item sets.")
output_file.write(itembags)
output_file.close()
print("Item sets saved. Exiting script.")
