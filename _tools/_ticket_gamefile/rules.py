"""Internal category and naming rules; not an entry point.

Shared by TicketFromGamefile.py and TicketToGamefile.py.
"""

import re
import subprocess
import unicodedata


# JP is the source column, not a selectable translation mode.
lang_names = ("JP", "CN", "EN", "KO", "RU", "TH")

# Normalize ASCII width only; do not merge unrelated Japanese names via NFKC.
WIDTH_TABLE = str.maketrans({**{chr(n): chr(n - 0xfee0) for n in range(0xff01, 0xff5f)}, '　': ' '})


# Json files to update for each item category
# (files of "wp" are the weapon keys of equipment_types)
json_paths = {
    "mo": ["Item_Stack_MotionChange.txt"],
    "bp": ["Item_Stack_CS_Material_Ticket1.txt", "Item_Stack_CS_Material_Ticket2.txt", "Item_Stack_CS_Material_Ticket3.txt"],
    "ph": ["Item_Stack_CS_Effect.txt", "Item_Stack_CS_Room_Goods.txt", "Item_Stack_CS_Stickers.txt"],
    "bg": ["Item_Stack_Arkscard_BG.txt"],
    "aug": ["Item_Stack_ElementCapsule.txt"],
    "ou": ["Item_Stack_OuterWearM.txt", "Item_Stack_OuterWearF.txt"],
    "cp": ["Item_Stack_ArmPartsM.txt", "Item_Stack_BodyPartsM.txt", "Item_Stack_LegPartsM.txt",
           "Item_Stack_ArmPartsF.txt", "Item_Stack_BodyPartsF.txt", "Item_Stack_LegPartsF.txt"],
    "mou": ["Item_Stack_Tooth.txt"],
    "ear": ["Item_Stack_Ear.txt"],
    "horn": ["Item_Stack_Horn.txt"],
    "body": ["Item_Stack_Skin.txt"],
    "ba": ["Item_BaseWear_Male.txt", "Item_BaseWear_Female.txt"],
    "in": ["Item_InnerWear_Male.txt", "Item_InnerWear_Female.txt"],
    "bpa": ["Item_Stack_BodyPaint.txt"],
    "stk": ["Item_Stack_Sticker.txt"],
    "eye": ["Item_Stack_Eye.txt"],
    "brow": ["Item_Stack_EyeBrow.txt"],
    "lash": ["Item_Stack_EyeLash.txt"],
    "fpa": ["Item_Stack_FacePaint.txt"],
    "hair": ["Item_Stack_Hairstyle.txt"],
    "head": ["Item_Stack_Headparts.txt"],
    "face": ["Item_FacePattern.txt"],
    "ac": ["Item_Stack_Accessory.txt"],
    # "md": ["Item_Stack_Music.txt"],
    "ca": ["Item_Stack_Duel_Card_Ticket.txt"],
    "ma": ["Item_Stack_Duel_Card_Play_Mat.txt"],
    "sv": ["Item_Stack_Duel_Card_Sleeve.txt"],
    "ha": ["Item_Stack_LobbyAction.txt"],
    "vo": ["Item_Stack_Voice.txt"],
    "un": ["Item_Addon_Unit.txt"],
    "rg": ["Item_NGSRing1.txt", "Item_NGSRing2.txt"],
    "rl": ["Item_RingL.txt"],
    "rr": ["Item_RingR.txt"],
    "pa": ["Item_Disk_PAAssaultRifle.txt", "Item_Disk_PACompoundbow.txt", "Item_Disk_PADoubleSaber.txt",
           "Item_Disk_PADualBlade.txt", "Item_Disk_PAGunSlash.txt", "Item_Disk_PAJetBoots.txt",
           "Item_Disk_PAKatana.txt", "Item_Disk_PAKnuckle.txt", "Item_Disk_PALauncher.txt",
           "Item_Disk_PAPartizan.txt", "Item_Disk_PASword.txt", "Item_Disk_PATwinDagger.txt",
           "Item_Disk_PATwinMachineGun.txt", "Item_Disk_PAWiredLance.txt"],
    "pac": ["Item_Disk_PACustAssaultRifle.txt", "Item_Disk_PACustCompoundbow.txt", "Item_Disk_PACustDoubleSaber.txt",
            "Item_Disk_PACustDualBlade.txt", "Item_Disk_PACustGunSlash.txt", "Item_Disk_PACustJetBoots.txt",
            "Item_Disk_PACustKatana.txt", "Item_Disk_PACustKnuckle.txt", "Item_Disk_PACustLauncher.txt",
            "Item_Disk_PACustPartizan.txt", "Item_Disk_PACustSword.txt", "Item_Disk_PACustTwinDagger.txt",
            "Item_Disk_PACustTwinMachineGun.txt", "Item_Disk_PACustWiredLance.txt"],
    "tec": ["Item_Disk_TECDark.txt", "Item_Disk_TECFire.txt", "Item_Disk_TECIce.txt", "Item_Disk_TECLight.txt",
            "Item_Disk_TECThunder.txt", "Item_Disk_TECWind.txt", "Item_Disk_TECMultiple.txt"],
    "tecc": ["Item_Disk_TECCustDark.txt", "Item_Disk_TECCustFire.txt", "Item_Disk_TECCustIce.txt",
             "Item_Disk_TECCustLight.txt", "Item_Disk_TECCustThunder.txt", "Item_Disk_TECCustWind.txt"],
    "co_m": ["Item_Costume_Male.txt"],
    "co_f": ["Item_Costume_Female.txt"],
    "ou_m": ["Item_Outer_Male.txt"],
    "ou_f": ["Item_Outer_Female.txt"],
    "arm_m": ["Item_Parts_ArmMale.txt"],
    "arm_f": ["Item_Parts_ArmFemale.txt"],
    "bod_m": ["Item_Parts_BodyMale.txt"],
    "bod_f": ["Item_Parts_BodyFemale.txt"],
    "leg_m": ["Item_Parts_LegMale.txt"],
    "leg_f": ["Item_Parts_LegFemale.txt"],
    "um": ["Item_Stack_Tool.txt"]
}

# Columns: JP, CN, EN, KO, RU, TH; None means no translation in that language's JSON.
# KO/RU/TH: MotionChange default entries, equipment Prim/Gold Prim entries,
# NGSRing1/2 types, Stack_Tool materials, and Duel_Card_Ticket elements.
# Categories of items
mo_itypes = {
    "Idle": ("待機", "待機", "Idle", "대기", None, "Idle"),
    "Jump": ("ジャンプ", "跳躍", "Jump", "점프", None, "Jump"),
    "Landing": ("着地", "落地", "Land", "착지", None, "Land"),
    "Move": ("移動", "移動", "Move", "이동", None, "Move"),
    "Sprint": ("ダッシュ", "衝刺", "Dash", "대시", None, "Dash"),
    "Glide": ("グライド", "滑翔", "Glide", "글라이드", None, "Glide"),
    "Swim": ("泳ぐ", "游泳", "Swim", "헤엄치기", None, "Swim")}

# Types of weapons and units (keyed by json file)
equipment_types = {
    "Item_Weapon_AssaultRifle.txt": ("ライフル", "步槍", "Rifle", "라이플", "Rifle", "Rifle"),
    "Item_Weapon_Compoundbow.txt": ("ボウ", "強弓", "Bow", "보우", "Bow", "Bow"),
    "Item_Weapon_DoubleSaber.txt": ("セイバー", "雙頭劍", "Saber", "세이버", "Saber", "Saber"),
    "Item_Weapon_DualBlade.txt": ("ブレード", "飛翔劍", "Blades", "블레이드", "Blades", "Blades"),
    "Item_Weapon_GunSlash.txt": ("スラッシュ", "槍刃", "Slash", "슬래시", "Slash", "Slash"),
    "Item_Weapon_JetBoots.txt": ("ブーツ", "魔裝腳", "Boots", "부츠", "Boots", "Boots"),
    "Item_Weapon_Katana.txt": ("カタナ", "拔劍", "Katana", "카타나", "Katana", "Katana"),
    "Item_Weapon_Knuckle.txt": ("ナックル", "鋼拳", "Knuckles", "너클", "Knuckles", "Knuckles"),
    "Item_Weapon_Launcher.txt": ("ランチャー", "大炮", "Launcher", "런처", "Launcher", "Launcher"),
    "Item_Weapon_Partizan.txt": ("スピア", "長槍", "Spear", "스피어", "Spear", "Spear"),
    "Item_Weapon_Rod.txt": ("ロッド", "長杖", "Rod", "로드", "Rod", "Rod"),
    "Item_Weapon_Sword.txt": ("ソード", "大劍", "Sword", "소드", "Sword", "Sword"),
    "Item_Weapon_Tact.txt": ("タクト", "奏具", "Takt", "택트", "Takt", "Takt"),
    "Item_Weapon_Talis.txt": ("タリス", "導具", "Talis", "탈리스", "Talis", "Talis"),
    "Item_Weapon_TwinDagger.txt": ("ダガー", "雙小劍", "Daggers", "대거", "Daggers", "Daggers"),
    "Item_Weapon_TwinMachineGun.txt": ("マシンガン", "雙機槍", "Machineguns", "머신건", "Machineguns", "Machineguns"),
    "Item_Weapon_Wand.txt": ("ウォンド", "短杖", "Wand", "완드", "Wand", "Wand"),
    "Item_Weapon_WiredLance.txt": ("ワイヤー", "自在槍", "Wire", "와이어", "Wire", "Wire"),
    "Item_Addon_Unit.txt": ("アーマ", "防具", "Armor", "아머", "Armor", "Armor")}

json_paths["wp"] = [path for path in equipment_types if path.startswith("Item_Weapon_")]

json_paths["wc"] = [path.replace("Item_Weapon_", "Item_AvatarWPN_") for path in json_paths["wp"]]

equipment_types.update(dict.fromkeys(json_paths["wc"], ("アルマティ", "武具", "Armati", "아르마티", "Armati", "Armati")))

# Common suffixes of equipment names except roman numerals (e.g. "トワル・シュメッターソードAT")
equipment_common_suffixes = {
    "AT": ("AT", "AT", "AT", "AT", "AT", "AT")}

# Separators of equipment names (with "・" in JP / without "・" in JP) and parentheses of type
equipment_dot_translations = ("・", "·", " ", " ", " ", " ")

equipment_space_translations = ("", "", " ", " ", " ", " ")

equipment_parentheses_translations = (("（", "）"), ("（", "）"), ("(", ")"),
                                     ("（", "）"), ("(", ")"), ("(", ")"))
# KO materials retain their attached Roman numerals (Stack_Tool: 37010109).
equipment_suffix_separators = ("", "", " ", "", " ", " ")

# Types and separators of rings
ring_type_translations = {
    "タイプ1": ("タイプ1", "類型1", "Type 1", "타입1", None, "Type 1"),
    "タイプ2": ("タイプ2", "類型2", "Type 2", "타입2", None, "Type 2")}

ring_slash_translations = ("／", "/", "/", "／", None, "/")

ring_hand_translations = {
    "rl": ("左", "左", "Left", "왼손", "левую", "มือซ้าย"),
    "rr": ("右", "右", "Right", "오른손", "правую", "มือขวา")}

# Types of equipment upgrade materials (series names come from item_series_name)
upgrade_material_types = {
    "ヴォルト": ("ヴォルト", "變轉零件", "volt", "볼트", None, "volt"),
    "ヴァンス": ("ヴァンス", "進階零件", "vance", "반스", None, "vance"),
    "キューブ": ("キューブ", "方塊", "Cube", "큐브", "Cube", "Cube"),
    "インテグラ": ("インテグラ", "元件", "Integra", "인테그라", "Integra", "Integra")}

# EN/TH attach volt/vance to the series; Cube/Integra remain separate words.
upgrade_material_en_separators = {"ヴォルト": "", "ヴァンス": ""}
upgrade_material_type_separators = ({}, {}, upgrade_material_en_separators,
                                    {}, {}, upgrade_material_en_separators)

# Card element translations; costs and rarity markers are retained from Stack text.
ca_itype_translations = {
    "炎": ("炎", "炎", "Fire", "염", None, "Fire"),
    "氷": ("氷", "冰", "Ice", "빙", None, "Ice"),
    "風": ("風", "風", "Wind", "풍", None, "Wind"),
    "雷": ("雷", "雷", "Lightning", "뇌", None, "Lightning"),
    "光": ("光", "光", "Light", "광", None, "Light"),
    "闇": ("闇", "暗", "Dark", "암", None, "Dark")}

# Only update items with assign of these digits or more (NGS equipment)
min_assign_digits = {
    "wp": 8,
    "wc": 9,
    "un": 8}

# Only update items from the item of this assign (NGS music discs)
start_assigns = {
    "md": "319010000"}

# Classic clothing is excluded from both tools in CN mode.
cn_excluded_prefixes = ("co_m", "co_f", "ou_m", "ou_f", "arm_m", "arm_f",
                        "bod_m", "bod_f", "leg_m", "leg_f")

# Reboot selector and path relative to the CN repository root.
source_files = {
    "common": (True, "UI/common.text.ini"),
    "actor_name": (False, "UI/actor_name.text.ini"),
    "ui_accessories_text": (False, "UI/ui_accessories_text.text.ini"),
    "ui_charamake_parts": (False, "UI/ui_charamake_parts.text.ini"),
    "item_element_name_reb": (False, "UI/item_element_name_reb.text.ini"),
    "lineduel_text": (True, "Unsorted/ngs/lineduel_text.text.ini"),
    "item_series_name": (False, "UI/item_series_name.text.ini"),
    "ui_item": (True, "UI/ui_item.text.ini"),
    "ui_bgmlist_text": (True, "UI/ui_bgmlist_text.text.ini"),
}

# Translated CSV directories relative to each language checkout, not JP Files/.
csv_directories = {
    "EN": ("UI", "Translated/UI"),
    "KO": ("UI", "UI"),
    "RU": ("translated files/UI", "Reboot/UI"),
    "TH": ("UI", "Translated/UI"),
}
csv_directory_overrides = {
    ("KO", "lineduel_text"): "Linestrike",
    ("EN", "actor_name"): "Misc",
    ("KO", "actor_name"): "Misc",
    ("RU", "actor_name"): "translated files/Misc",
    ("TH", "actor_name"): "Misc"}

source_for_prefix = {'mo': 'common',
 'bp': 'ui_accessories_text',
 'ph': 'ui_accessories_text',
 'bg': 'ui_charamake_parts',
 'aug': 'item_element_name_reb',
 'ou': 'ui_charamake_parts',
 'cp': 'ui_charamake_parts',
 'mou': 'ui_charamake_parts',
 'ear': 'ui_charamake_parts',
 'horn': 'ui_charamake_parts',
 'body': 'ui_charamake_parts',
 'ba': 'ui_charamake_parts',
 'in': 'ui_charamake_parts',
 'bpa': 'ui_charamake_parts',
 'stk': 'ui_charamake_parts',
 'eye': 'ui_charamake_parts',
 'brow': 'ui_charamake_parts',
 'lash': 'ui_charamake_parts',
 'fpa': 'ui_charamake_parts',
 'hair': 'ui_charamake_parts',
 'head': 'ui_charamake_parts',
 'face': 'ui_charamake_parts',
 'ac': 'ui_accessories_text',
 'md': 'ui_bgmlist_text',
 'ca': 'lineduel_text',
 'ma': 'lineduel_text',
 'sv': 'lineduel_text',
 'ha': 'common',
 'vo': 'ui_charamake_parts',
 'pa': 'actor_name',
 'pac': 'actor_name',
 'tec': 'actor_name',
 'tecc': 'actor_name',
 'rl': 'ui_item',
 'rr': 'ui_item',
 'co_m': 'ui_charamake_parts',
 'co_f': 'ui_charamake_parts',
 'ou_m': 'ui_charamake_parts',
 'ou_f': 'ui_charamake_parts',
 'arm_m': 'ui_charamake_parts',
 'arm_f': 'ui_charamake_parts',
 'bod_m': 'ui_charamake_parts',
 'bod_f': 'ui_charamake_parts',
 'leg_m': 'ui_charamake_parts',
 'leg_f': 'ui_charamake_parts'}

# Classic PA/TEC actor ID families; ordinary and custom disks share #0 names.
disk_actor_prefixes = {
    "PAAssaultRifle": "RiflePA", "PACompoundbow": "CompoundBowPA",
    "PADoubleSaber": "DsaberPA", "PADualBlade": "DbladePA",
    "PAGunSlash": "GunslashPA", "PAJetBoots": "JetBootsPA",
    "PAKatana": "KatanaPA", "PAKnuckle": "KnucklePA",
    "PALauncher": "LauncherPA", "PAPartizan": "PartisanPA",
    "PASword": "SwordPA", "PATwinDagger": "TdaggerPA",
    "PATwinMachineGun": "MachinegunPA", "PAWiredLance": "WlancePA",
    "TECDark": "Dark", "TECFire": "Fire", "TECIce": "Ice",
    "TECLight": "Light", "TECThunder": "Thunder", "TECWind": "Wind",
    "TECMultiple": "Multi(?:WT|FD|IL)"}

disk_prefixes = ("pa", "pac", "tec", "tecc")

# Normalize JP lookup keys without changing the stored item names.
classic_prefixes = disk_prefixes + ("rl", "rr", "co_m", "co_f", "ou_m", "ou_f",
                                    "arm_m", "arm_f", "bod_m", "bod_f", "leg_m", "leg_f")

# These categories read independent description data from the matching #1 field.
explain_prefixes = ("pa", "tec", "rl", "rr")

# Names and texts of items (plain_formats if not defined; texts of cards are formed by form_card_texts)
plain_formats = ["{jp_text}"] + ["{tr_text}"] * 5

mo_names = ["{jp_itype}：{jp_text}", "{tr_itype}：{tr_text}", "{tr_itype}: {tr_text}",
            "{tr_itype}：{tr_text}", None, "{tr_itype}: {tr_text}"]

mo_texts = [
    "Mo「{jp_itype}：{jp_text}」", "Mo「{tr_itype}：{tr_text}」", "Mo \"{tr_itype}: {tr_text}\"",
    "Mo「{tr_itype}：{tr_text}」", None, "Mo \"{tr_itype}: {tr_text}\""]

bp_texts = [
    "BP「{jp_text}」",  "BP「{tr_text}」", "BP \"{tr_text}\"",
    "BP「{tr_text}」", None, "BP \"{tr_text}\""]

ph_texts = [
    "PH「{jp_text}」",  "PH「{tr_text}」", "PH \"{tr_text}\"",
    "PH「{tr_text}」", None, "PH \"{tr_text}\""]

bg_texts = [
    "Bg「{jp_text}」",  "Bg「{tr_text}」", "Bg \"{tr_text}\"",
    "Bg「{tr_text}」", None, "Bg \"{tr_text}\""]

aug_texts = [
    "C/{jp_text}", "C/{tr_text}", "C/{tr_text}", "C/{tr_text}", "C/{tr_text}", "C/{tr_text}"]

ca_texts = [
    "Ca「{tr_itype}{cost}：{tr_text}」", "Ca「{tr_itype}{cost}：{tr_text}」",
    "Ca \"{tr_itype} {cost}: {tr_text}\"", "Ca「{tr_itype}{cost}：{tr_text}」", None,
    "Ca \"{tr_itype} {cost}: {tr_text}\""]

ma_texts = [
    "Ma「{jp_text}」", "Ma「{tr_text}」", "Ma \"{tr_text}\"",
    "Ma「{tr_text}」", None, "Ma \"{tr_text}\""]

sv_texts = [
    "Sv「{jp_text}」", "Sv「{tr_text}」", "Sv \"{tr_text}\"",
    "Sv「{tr_text}」", None, "Sv \"{tr_text}\""]

ha_texts = [
    "Ha「{jp_text}」",  "Ha「{tr_text}」", "Ha \"{tr_text}\"",
    "Ha「{tr_text}」", None, "Ha \"{tr_text}\""]

rl_texts = ["Ｌ／{jp_text}"] + ["L/{tr_text}"] * 5

rr_texts = ["Ｒ／{jp_text}"] + ["R/{tr_text}"] * 5

pac_texts = ["{jp_text}／Ｃ"] + ["{tr_text}/C"] * 5

tecc_texts = ["{jp_text}／カスタム", "{tr_text}/自定義", "{tr_text}/Custom",
              "{tr_text}/커스텀", "{tr_text}/Custom", "{tr_text}/Custom"]

# Explains of items, only for information from game files
# (other explains are translated by TicketDescriptions.py, existing ones are retained)
no_explains = [""] * 6

vo_explains = [
    "",
    "使用後，可選用新的語音。\nCV：{cv_tr_name}",
    "Allows a new voice to be selected.\nUsable by all characters.\nCV: {cv_tr_name}",
    "사용하면 새로운 보이스를\n선택할 수 있다.\nCV: {cv_tr_name}",
    "Позволяет выбрать новый голос.\nДоступно всем персонажам.\nCV: {cv_tr_name}",
    "เมื่อใช้งาน จะสามารถเลือก Voice ใหม่ได้กับทุกตัวละครในไอดี\nCV: {cv_tr_name}"]

rl_explains = rr_explains = [
    "{jp_itype}手用。装備中は以下のスキルが有効。\n「{jp_explain}」\n<yellow>※装備中に敵撃破でリングＥＸＰ獲得<c>",
    "{tr_itype}手用。裝備中會生效以下技能。\n「{tr_explain}」\n<yellow>※裝備中擊敗敵人獲得戒指EXP<c>",
    'Equipment for the {tr_itype} Hand.\n"{tr_explain}"\n<yellow>※Equipped rings gain EXP as you do.<c>',
    "{tr_itype}용. 장비 중에는 다음 스킬이 활성화된다.\n「{tr_explain}」\n<yellow>※장비 중 적을 격파하면 링 EXP 획득<c>",
    'Экипируется на {tr_itype} руку.\n"{tr_explain}"\n<yellow>※Надетые кольца получают EXP\nкак и вы.<c>',
    'อุปกรณ์สําหรับ{tr_itype} ขณะสวมใส่จะมีผลของสกิลต่อไปนี้:\n"{tr_explain}"\n<yellow>※ได้รับ Ring EXP จากการกําจัดศัตรูขณะสวมใส่<c>']

pa_explains = tec_explains = ["{jp_explain}"] + ["{tr_explain}"] * 5

# Stack_Voice: 31800, 318012, 318026, 3180148, 3180132 in KO/TH.
# These are name decorations only; actor names always come from JSON.
vo_name_parts = {
    "male": (None, None, "Male", "남성", None, "Male"),
    "female": (None, None, "Female", "여성", None, "Female"),
    "all": (None, None, "All ", "", None, "All "),
    "common": (None, None, r"(?:C |Common )", r"(?:Ｃ\s*|C\s*|공용\s+)", None, r"(?:C |Common )"),
    "voice": (None, None, r"Voice|Vo", "보이스", None, r"Voice|Vo"),
    "extra": (None, None, "Extra Voice", "추가 보이스", None, "Extra Voice"),
    "ex": (None, None, r"(?:EX|\[EX\]) Voice", r"(?:［ＥＸ］|\[EX\]) 보이스", None, r"(?:EX|\[EX\]) Voice"),
}


# [FUNCTION] Resolve an explicit mode or the branch of the script's repository.
def resolve_language(language, repository):
    if language is None:
        try:
            language = subprocess.check_output(
                ['git', '-C', str(repository), 'symbolic-ref', '--quiet', '--short', 'HEAD'],
                stderr=subprocess.PIPE, text=True).strip()
        except (OSError, subprocess.CalledProcessError):
            language = 'unknown branch or detached HEAD'
        language = {'CN-update': 'CN', 'KO-update': 'KO'}.get(language, language)
    elif isinstance(language, int) and 0 < language < len(lang_names):
        language = lang_names[language]
    if language not in lang_names[1:]:
        raise ValueError(f'Unsupported language/branch: {language}. '
                         f'Select a language manually with --lang {"/".join(lang_names[1:])}')
    return language


# [FUNCTION] Use the same translated CSV location for online reads and local writes.
def csv_path(name, language):
    directory = csv_directory_overrides.get((language, name))
    if directory is None:
        directory = csv_directories[language][source_files[name][0]]
    return f'{directory}/{name}.csv'


# [FUNCTION] Select the same JSON scope for dispatch, loading and candidate collection.
def get_json_paths(language, forward):
    # TicketFromGamefile.py generates HA/VO only in CN; TicketToGamefile.py also supports CSV voice recovery.
    return {prefix: paths for prefix, paths in json_paths.items()
            if not (language == "CN" and prefix in cn_excluded_prefixes)
            and not (forward and language != "CN" and prefix in ("ha", "vo"))}


# [FUNCTION] Normalize ASCII width for matching without rewriting the name.
def width_key(text):
    return text.translate(WIDTH_TABLE)


# [FUNCTION] Read the effective translation, including the green name prefix used by CN.
def effective_name(item, lang):
    # Tradable CN items retain JP in tr_text; their translation lives in this prefix.
    name = item['tr_text']
    if lang == 'CN':
        match = re.match(r'^<green>“([^\n]*)”<c>\n', item['tr_explain'])
        if match:
            if name and width_key(name) != width_key(item['jp_text']) and name != match[1]:
                raise ValueError('green_note_conflicts_with_name')
            name = match[1]
    return name


# [FUNCTION] Generate string with a different width
def width_process_string(string):
    result_string = ""
    for char in string:
        try:
            # Determine if a character is full-width or half-width
            if unicodedata.east_asian_width(char) in ('F', 'W'):
                # If character is full-width, convert it to half-width
                result_string += chr(ord(char) - 0xfee0)
            elif unicodedata.east_asian_width(char) in ('H', 'Na'):
                # If character is half-width, convert it to full-width
                result_string += chr(ord(char) + 0xfee0)
            else:
                # Keep the other charactesr the same
                result_string += char
        except ValueError:
            # If character encoding exceeds the Unicode range
            result_string += char
    return result_string


# [FUNCTION] Get the number of id for the order of ids (lineduel_text is ordered by number)
def numeric_order(base_id):
    return int(base_id) if base_id.isdigit() else -1


# [FUNCTION] Get JP target lines of the table from the starting line
# Game files consist of tables ordered by ids (by string if order_key is str), a table ends where the order resets
# If start_id is (start_id, start_refer_id), the referred texts of the same ids are added to lines
def get_table_jp_target_lines(lines, start_id, id_pattern="", order_key=str):
    if isinstance(start_id, (list, tuple)):
        text_lines = get_table_jp_target_lines(lines, start_id[0], id_pattern, order_key)
        refer_lines = get_table_jp_target_lines(lines, start_id[1], id_pattern, order_key)
        refer_lookup = {text_id.split('#')[0]: jp_text for text_id, jp_text in refer_lines}
        return [(text_id, jp_text, refer_lookup.get(text_id.split('#')[0], ""))
                for text_id, jp_text in text_lines]

    table_lines = []
    for text_id, jp_text in lines:
        if table_lines or text_id == start_id:
            order = order_key(text_id.split('#')[0])
            if table_lines and order <= prev_order:
                break
            table_lines.append((text_id, jp_text))
            prev_order = order
    return [(text_id, jp_text) for text_id, jp_text in table_lines if re.match(id_pattern, text_id)]


# [FUNCTION] Remove the lines of dummy texts
def remove_dummy_lines(lines):
    return [line for line in lines if not line[1].startswith(("￥", "text_"))]


# [FUNCTION] Form names of voice (only compatible with CN)
def form_vo_names(text_id, jp_fulltext, tr_fulltext):
    # Split the full text to get vo name and cv name
    # (voices without cv name are voiced by the characters themselves, e.g. "でびでび・でびる")
    vo_jp_name = jp_fulltext.split("/")[0]
    vo_tr_name, cv_tr_name = tr_fulltext.split("/") if "/" in tr_fulltext else (tr_fulltext, tr_fulltext)
    vo_tr_name, cv_tr_name = vo_tr_name.strip(), cv_tr_name.strip()

    # Determine version and gender of the voice based on text id
    # NGS voices: "11_voice_cman9xx"/"11_voice_cwoman9xx", then "11_voice_3xxxxx"/"11_voice_4xxxxx"
    new_id = re.match(r'11_voice_([34])\d{5}#', text_id)
    vo_ver = "ngs" if new_id or re.match(r'.*9\d{2}#0', text_id) else "o2"
    is_male = new_id.group(1) == "3" if new_id else text_id.startswith("11_voice_cman")
    if vo_ver == "o2":
        vo_gender = "男性" if is_male else "女性"
    elif vo_ver == "ngs":
        vo_gender = "T1" if is_male else "T2"

    # Initialize
    vo_jp_type = vo_tr_type = [""]
    vo_jp_number = vo_tr_number = ""
    vo_jp_suffix = vo_tr_suffix = [""]
    vo_jp_suffix2 = vo_tr_suffix2 = ""

    # Generate all remaining parts of the final text
    if vo_ver == "ngs":
        vo_jp_suffix, vo_tr_suffix = ["ボイス"], ["語音"]
        if re.match(r'^T\d.*\d{3}$', vo_jp_name):
            vo_jp_number = vo_jp_name[-3:]
            vo_tr_number = vo_tr_name[-3:]
            vo_jp_name = vo_jp_name[2:-3]
            vo_tr_name = vo_tr_name[2:-3]
    elif vo_ver == "o2":
        vo_jp_type, vo_tr_type = ["", "Ｃ", "共通"], ["", "C", "共通"]
        if vo_jp_name.startswith(("追加ボイス", "［ＥＸ］ボイス")):
            vo_jp_suffix = vo_tr_suffix = [""]
        elif re.search(r'.{6,}', vo_jp_name):
            if re.search(r"[Ａ-Ｚ]$", vo_jp_name):
                vo_jp_suffix, vo_tr_suffix = ["", "ボイス", "Ｖｏ", "　Ｖｏ"], ["", "語音", "語音", "語音"]
            else:
                vo_jp_suffix, vo_tr_suffix = ["", "ボイス","Ｖｏ"], ["", "語音","語音"]
        else:
            vo_jp_suffix, vo_tr_suffix = ["", "ボイス"], ["", "語音"]

    # For the B/C/D... voices (only compatible with CN)
    if (match_trans := re.search(r"^(.*[\u4e00-\u9fa5])([A-Z])$", vo_tr_name)):
        match_jp = re.search(r"^(.*)([Ａ-Ｚ]|[A-Z])$", vo_jp_name)
        vo_jp_name, vo_jp_suffix2 = match_jp.group(1), match_jp.group(2)
        vo_tr_name, vo_tr_suffix2 = match_trans.group(1), match_trans.group(2)

    # Combine
    # 男性/女性/T1/T2/ + Ｃ/共通 + name + ボイス/Ｖｏ/　Ｖｏ + number + /B/C/D...
    jp_texts = [f"{vo_gend}{vo_jp_typ}{vo_jp_nam}{vo_jp_suff}{vo_jp_num}{vo_jp_suff2}"
        for vo_gend in [vo_gender]
        for vo_jp_typ in vo_jp_type
        for vo_jp_nam in [vo_jp_name]
        for vo_jp_num in [vo_jp_number]
        for vo_jp_suff in vo_jp_suffix
        for vo_jp_suff2 in [vo_jp_suffix2]]
    tr_texts = [f"{vo_gend}{vo_tr_typ}{' ' if re.match(r'^[a-zA-Z]', vo_tr_name) and (vo_ver == 'ngs' or vo_tr_typ == 'C') else ''}{vo_tr_nam}{vo_tr_suff}{vo_tr_num}{vo_tr_suff2}"
        for vo_gend in [vo_gender]
        for vo_tr_typ in vo_tr_type
        for vo_tr_nam in [vo_tr_name]
        for vo_tr_num in [vo_tr_number]
        for vo_tr_suff in vo_tr_suffix
        for vo_tr_suff2 in [vo_tr_suffix2]]

    return jp_texts, tr_texts, cv_tr_name


# [FUNCTION] Remove "シリーズ" and "(原名:...)" from series name
def strip_series_suffix(text):
    text = re.sub(r"[（(]\s*原名[:：].*?[）)]", "", text).strip()
    # "シ?" also covers the typo "ゼネスリーズ" in game files
    text = re.sub(r"^Серия\s+", "", text)
    return re.sub(r"(?:シ?リーズ|系列|\s+Series|\s+시리즈)$", "", text).strip()


# [FUNCTION] Split the common suffix (AT, roman numerals, etc.) from the end of equipment name
def split_common_suffix(jp_text):
    for jp_suffix in sorted(equipment_common_suffixes, key=len, reverse=True):
        if jp_text.endswith(jp_suffix) and len(jp_text) > len(jp_suffix):
            return jp_text[:-len(jp_suffix)], jp_suffix
    # Roman numerals from "Ⅰ" to "Ⅻ" (e.g. "レジェスソードⅡ")
    if len(jp_text) > 1 and "Ⅰ" <= jp_text[-1] <= "Ⅻ":
        return jp_text[:-1], jp_text[-1]
    return jp_text, ""


# [FUNCTION] Split the type in parentheses from equipment name (e.g. "マルチウェポン代用材（ソード）")
def split_type_parentheses(jp_text, jp_type):
    for left, right in (("（", "）"), ("(", ")")):
        type_part = f"{left}{jp_type}{right}"
        if jp_text.endswith(type_part) and len(jp_text) > len(type_part):
            return jp_text[:-len(type_part)], True
    return jp_text, False


# [FUNCTION] Get all possible structures of equipment name
# Each structure: series record for translation ("record") and the full series record ("series_record"),
# small series before type ("pre"), whether type exists ("has_type"), small series after type ("post")
# Small series: (parent_base, small_name, has_dot)
def iter_equipment_structures(jp_text, jp_type, series_records, records_by_base):
    for record in series_records:
        jp_base = record["jp_base"]

        # Series + type + [・]small series + [・]suffix (e.g. "プリムソード・リブラ")
        if "・" in jp_base:
            series_root, small_name = jp_base.split("・", 1)
            root_record = records_by_base.get(series_root)
            for separator in ("・", ""):
                reordered_prefix = f"{series_root}{jp_type}{separator}{small_name}"
                if root_record and jp_text.startswith(reordered_prefix):
                    post = [(series_root, small_name, separator == "・")]
                    trailing_text = jp_text[len(reordered_prefix):]
                    if trailing_text:
                        post.append((jp_base, trailing_text.lstrip("・"), trailing_text.startswith("・")))
                    yield {"record": root_record, "series_record": record, "pre": [], "has_type": True, "post": post}

        if not jp_text.startswith(jp_base):
            continue
        remainder = jp_text[len(jp_base):]
        has_dot = remainder.startswith("・")
        # Series only (e.g. "マルチウェポン代用材")
        if not remainder:
            yield {"record": record, "series_record": record, "pre": [], "has_type": False, "post": []}
        # Series + type + [・]suffix (e.g. "カイゼラムソード試製壱型")
        elif remainder.startswith(jp_type):
            suffix = remainder[len(jp_type):]
            post = [(jp_base, suffix.lstrip("・"), suffix.startswith("・"))] if suffix else []
            yield {"record": record, "series_record": record, "pre": [], "has_type": True, "post": post}
        # Series + [・]small series + type (e.g. "トワル・シュメッターソード", "シュヴァルゼストアーマ")
        if remainder.endswith(jp_type) and len(remainder.lstrip("・")) > len(jp_type):
            small_name = remainder.lstrip("・")[:-len(jp_type)]
            yield {"record": record, "series_record": record, "pre": [(jp_base, small_name, has_dot)], "has_type": True, "post": []}
        # Series + [・]small series (e.g. "レリク・エンドイフ")
        if remainder.lstrip("・"):
            yield {"record": record, "series_record": record, "pre": [(jp_base, remainder.lstrip("・"), has_dot)], "has_type": False, "post": []}


# [FUNCTION] Special item texts of special items
def edit_special_text(prefix, jp_text, tr_text, jp_refer, lang):
    jp_refer = jp_refer[0] if jp_refer else ""

    if prefix == "rr" and jp_text == "テックアーツJAPPセイブ":
        jp_text = "テックアーツＪＡＰＰＳ"
    elif prefix == "ca" and jp_text == "アルクェイド・ブリュンスタッド":
        sp_texts = ["アルクェイド", "愛爾奎特", "Arcueid", "알퀘이드", None, "Arcueid"]
        jp_text = sp_texts[0]
        tr_text = sp_texts[lang]
    elif prefix == "ca" and jp_refer == "サマーバケーション"and "せんとらるっ！" not in jp_text:
        # KO retains the two existing suffixes (card assigns 3104010364/3104010531).
        ko_suffix = "（서머）" if jp_text == "エルミル" else "（여름）"
        sp_texts = ["（サマー）", "（夏季）", " (Summer)", ko_suffix, None, None]
        jp_text += sp_texts[0]
        tr_text = tr_text + sp_texts[lang] if sp_texts[lang] is not None else None
    elif prefix == "ca" and jp_refer == "ハッピーホリデイ":
        sp_texts = ["（ホリデイ）", "（假日）", " (Holiday)", "（휴일）", None, None]
        jp_text += sp_texts[0]
        tr_text = tr_text + sp_texts[lang] if sp_texts[lang] is not None else None
    elif prefix == "ca" and jp_refer == "超・夢幻祭":
        sp_texts = ["（夢幻祭）", "（夢幻祭）", " (Super Phantasy Festival)", "（몽환제）", None, None]
        jp_text += sp_texts[0]
        tr_text = tr_text + sp_texts[lang] if sp_texts[lang] is not None else None
    elif prefix == "ca" and jp_text == "先代ダークファルス 【若人】":
        sp_texts = ["先代DF【若人】", "前代DF【若人】", "Previous DF [Apprentice]", "선대 DF【약인】", None, None]
        jp_text = sp_texts[0]
        tr_text = sp_texts[lang]
    elif prefix == "ca" and jp_refer == "スクルル":
        sp_texts = ["（スクルル）", "（學園風尚）", " (Schoolu)", "（스쿠루루）", None, None]
        jp_text += sp_texts[0]
        tr_text = tr_text + sp_texts[lang] if sp_texts[lang] is not None else None
    elif prefix == "ca" and "せんとらるっ！　" in jp_text:
        sp_char = "！"
        jp_text = jp_text.replace(sp_char + "　", sp_char)
    # Voices voiced by the characters themselves, whose cv names are written differently
    elif prefix == "vo" and jp_text == "五十嵐梨花":
        # KO/TH: Stack_Voice assigns 318010357 and 318010359, CV text.
        sp_texts = ["/五十嵐 梨花", "/五十嵐 梨花", "/Rika Igarashi", "/이가라시 리카", None, "/Rika Igarashi"]
        jp_text += sp_texts[0]
        tr_text = tr_text + sp_texts[lang] if sp_texts[lang] is not None else None
    elif prefix == "vo" and jp_text == "倉持めると":
        sp_texts = ["/倉持 めると", "/倉持 妹路特", "/Meruto Kuramochi", "/쿠라모치 메루토", None, "/Meruto Kuramochi"]
        jp_text += sp_texts[0]
        tr_text = tr_text + sp_texts[lang] if sp_texts[lang] is not None else None

    return jp_text, tr_text


def format_common_suffix(jp_suffix, lang):
    if jp_suffix in equipment_common_suffixes:
        return equipment_common_suffixes[jp_suffix][lang]
    ascii_numeral = unicodedata.normalize('NFKC', jp_suffix)
    roman_numerals = (jp_suffix, str(int(unicodedata.numeric(jp_suffix))),
                      ascii_numeral, jp_suffix, ascii_numeral, ascii_numeral)
    return roman_numerals[lang]


def contains_japanese(text):
    return bool(re.search(r'[\u3040-\u30ff\u4e00-\u9fff]', text))


# [FUNCTION] Read the independent body or skill-name component from a gamefile description.
def get_explain_text(prefix, text):
    if prefix in ("pa", "tec"):
        return text.replace("<br>", "\n").strip()
    return text.split("<br>", 1)[0].strip()


# [FUNCTION] Match description data first, then a ring's own name when the quote uses it.
def get_explain_source(prefix, explain, jp_name, jp_reference):
    sources = [(1, get_explain_text(prefix, jp_reference))]
    hand = ""
    if prefix in ring_hand_translations:
        hand = ring_hand_translations[prefix][0]
        sources.append((0, jp_name))
    for field, text in sources:
        expected = globals()[prefix + "_explains"][0].format(jp_itype=hand, jp_explain=text)
        if width_key(explain.strip()) == width_key(expected):
            return field
    return None


# [FUNCTION] Limit a disk file to its own weapon/technique actor family.
def disk_matches_file(path, text_id):
    family = path[len("Item_Disk_"):-len(".txt")].replace("Cust", "", 1)
    return re.fullmatch(disk_actor_prefixes[family] + r"\d+#0", text_id) is not None


def get_target_lines(sources):
    # Find target JP lines
    mo_jp_target_lines = [
        (text_id, jp_text) for text_id, jp_text in sources["common"]
        if text_id.startswith("Substitute_") and not jp_text.startswith("￥")]
    bp_jp_target_lines = [
        (text_id, jp_text) for text_id, jp_text in sources["ui_accessories_text"]
        if text_id.startswith(("ob_1", "ob_6")) and not jp_text.startswith(("￥", "text_"))]
    ph_jp_target_lines = [
        (text_id, jp_text) for text_id, jp_text in sources["ui_accessories_text"]
        if text_id.startswith("ob_7") and not jp_text.startswith(("￥", "text_"))]
    bg_jp_target_lines = remove_dummy_lines(
        get_table_jp_target_lines(sources["ui_charamake_parts"], "10#0", r'^\d{1,3}#'))
    aug_jp_target_lines = [
        (text_id, jp_text) for text_id, jp_text in sources["item_element_name_reb"]
        if not jp_text.startswith(("ダミー", "レガロ・", "セズン・", "EX", "ウェポンコネクタ", "￥", "-"))
        or re.search(r"(EX.*A$)", jp_text)]
    ou_jp_target_lines = [
        (text_id, jp_text) for text_id, jp_text in sources["ui_charamake_parts"]
        if re.match(r'^No\d{6}#', text_id)
        and jp_text.endswith("[Ou]")
        and not jp_text.startswith(("￥", "text_")) and "NPC" not in jp_text]
    cp_jp_target_lines = [
        (text_id, jp_text) for text_id, jp_text in sources["ui_charamake_parts"]
        if re.match(r'^No[34]\d{5}#', text_id)
        and any(keyword in jp_text for keyword in ("・アーム", "・ボディ", "・レッグ"))
        and not jp_text.startswith(("￥", "text_")) and "NPC" not in jp_text]
    mou_jp_target_lines = get_table_jp_target_lines(sources["ui_charamake_parts"], "No100010#10", r'^No1\d{5}#')
    ear_jp_target_lines = get_table_jp_target_lines(sources["ui_charamake_parts"], "No100000#4", r'^No1\d{5}#')
    horn_jp_target_lines = get_table_jp_target_lines(sources["ui_charamake_parts"], "No100000#5", r'^No1\d{5}#')
    body_jp_target_lines = [
        (text_id, jp_text) for text_id, jp_text in
        get_table_jp_target_lines(sources["ui_charamake_parts"], "No100000#6", r'^No\d{6}#')
        if not jp_text.startswith(("￥", "text_")) and "NPC" not in jp_text]
    ba_jp_target_lines = remove_dummy_lines(get_table_jp_target_lines(sources["ui_charamake_parts"], "No100010#0"))
    in_jp_target_lines = remove_dummy_lines(get_table_jp_target_lines(sources["ui_charamake_parts"], "No100010#8"))
    bpa_jp_target_lines = remove_dummy_lines(get_table_jp_target_lines(sources["ui_charamake_parts"], "1250#0"))
    stk_jp_target_lines = remove_dummy_lines(get_table_jp_target_lines(sources["ui_charamake_parts"], "No00000#2"))
    eye_jp_target_lines = remove_dummy_lines(get_table_jp_target_lines(sources["ui_charamake_parts"], "243#0"))
    brow_jp_target_lines = remove_dummy_lines(get_table_jp_target_lines(sources["ui_charamake_parts"], "10780#0"))
    lash_jp_target_lines = remove_dummy_lines(get_table_jp_target_lines(sources["ui_charamake_parts"], "10750#0"))
    fpa_jp_target_lines = remove_dummy_lines(get_table_jp_target_lines(sources["ui_charamake_parts"], "No00000#5"))
    # Hairstyles and head parts share a table; cast head parts are also in the table of cast parts
    hair_jp_target_lines = remove_dummy_lines(
        get_table_jp_target_lines(sources["ui_charamake_parts"], "50670#0", r'^No([01]\d{4}|1\d{5})#'))
    head_jp_target_lines = remove_dummy_lines(
        get_table_jp_target_lines(sources["ui_charamake_parts"], "50670#0", r'^No(5\d{4}|3\d{5})#')
        + get_table_jp_target_lines(sources["ui_charamake_parts"], "-#0", r'^cast_'))
    # Face variations are in the table of face variations and the table of voices
    face_jp_target_lines = remove_dummy_lines(
        get_table_jp_target_lines(sources["ui_charamake_parts"], "No100000#2", r'^No[12]\d{5}#')
        + get_table_jp_target_lines(sources["ui_charamake_parts"], "11_voice_201000#0", r'^No\d{6}#'))
    ac_jp_target_lines = remove_dummy_lines(get_table_jp_target_lines(sources["ui_accessories_text"], "No00000#0"))
    md_jp_target_lines = remove_dummy_lines(sources["ui_bgmlist_text"])
    ca_jp_target_lines = get_table_jp_target_lines(sources["lineduel_text"], ("10#0", "10#1"), order_key=numeric_order)
    ma_jp_target_lines = get_table_jp_target_lines(sources["lineduel_text"], "0#2", order_key=numeric_order)
    sv_jp_target_lines = get_table_jp_target_lines(sources["lineduel_text"], "0#3", order_key=numeric_order)
    ha_jp_target_lines = [
        (text_id, jp_text) for text_id, jp_text in sources["common"]
        if text_id.startswith("LobbyAction_")]
    vo_jp_target_lines = [
        (text_id, jp_text) for text_id, jp_text in sources["ui_charamake_parts"]
        if re.match(r'11_voice_(c|[34]\d{5}#)', text_id)]

    pa_pattern = "(?:" + "|".join(value for family, value in disk_actor_prefixes.items()
                                  if family.startswith("PA")) + r")\d+#0"
    tec_pattern = "(?:" + "|".join(value for family, value in disk_actor_prefixes.items()
                                   if family.startswith("TEC")) + r")\d+#0"
    actor_explains = dict(sources["actor_name"])
    pa_jp_target_lines = remove_dummy_lines([
        (text_id, jp_text, actor_explains.get(text_id[:-1] + "1", "")) for text_id, jp_text in sources["actor_name"]
        if re.fullmatch(pa_pattern, text_id)])
    tec_jp_target_lines = remove_dummy_lines([
        (text_id, jp_text, actor_explains.get(text_id[:-1] + "1", "")) for text_id, jp_text in sources["actor_name"]
        if re.fullmatch(tec_pattern, text_id)])
    ring_explains = dict(sources["ui_item"])
    old_ring_jp_target_lines = remove_dummy_lines([
        (text_id, jp_text, ring_explains.get(text_id[:-1] + "1", "")) for text_id, jp_text in sources["ui_item"]
        if text_id.startswith("ring_") and text_id.endswith("#0")])
    # Classic costumes include CAST looks; the leg table contains both #2 and #3 IDs.
    co_m_jp_target_lines = remove_dummy_lines(
        get_table_jp_target_lines(sources["ui_charamake_parts"], "No00003#1", r'^No[04]\d{4}#'))
    co_f_jp_target_lines = remove_dummy_lines(
        get_table_jp_target_lines(sources["ui_charamake_parts"], "No10002#1", r'^No[15]\d{4}#'))
    ou_m_jp_target_lines = remove_dummy_lines(
        get_table_jp_target_lines(sources["ui_charamake_parts"], "No20021#1", r'^No2\d{4}#'))
    ou_f_jp_target_lines = remove_dummy_lines(
        get_table_jp_target_lines(sources["ui_charamake_parts"], "No30020#1", r'^No3\d{4}#'))
    arm_m_jp_target_lines = remove_dummy_lines(
        get_table_jp_target_lines(sources["ui_charamake_parts"], "No40001#0", r'^No4\d{4}#'))
    arm_f_jp_target_lines = remove_dummy_lines(
        get_table_jp_target_lines(sources["ui_charamake_parts"], "No50001#0", r'^No5\d{4}#'))
    bod_m_jp_target_lines = remove_dummy_lines(
        get_table_jp_target_lines(sources["ui_charamake_parts"], "No40001#1", r'^No4\d{4}#'))
    bod_f_jp_target_lines = remove_dummy_lines(
        get_table_jp_target_lines(sources["ui_charamake_parts"], "No50001#1", r'^No5\d{4}#'))
    leg_m_jp_target_lines = remove_dummy_lines(
        get_table_jp_target_lines(sources["ui_charamake_parts"], "No40001#3", r'^No4\d{4}#'))
    leg_f_jp_target_lines = remove_dummy_lines(
        get_table_jp_target_lines(sources["ui_charamake_parts"], "No50001#3", r'^No5\d{4}#'))

    return {
        "mo": mo_jp_target_lines,
        "bp": bp_jp_target_lines,
        "ph": ph_jp_target_lines,
        "bg": bg_jp_target_lines,
        "aug": aug_jp_target_lines,
        "ou": ou_jp_target_lines,
        "cp": cp_jp_target_lines,
        "mou": mou_jp_target_lines,
        "ear": ear_jp_target_lines,
        "horn": horn_jp_target_lines,
        "body": body_jp_target_lines,
        "ba": ba_jp_target_lines,
        "in": in_jp_target_lines,
        "bpa": bpa_jp_target_lines,
        "stk": stk_jp_target_lines,
        "eye": eye_jp_target_lines,
        "brow": brow_jp_target_lines,
        "lash": lash_jp_target_lines,
        "fpa": fpa_jp_target_lines,
        "hair": hair_jp_target_lines,
        "head": head_jp_target_lines,
        "face": face_jp_target_lines,
        "ac": ac_jp_target_lines,
        "md": md_jp_target_lines,
        "ca": ca_jp_target_lines,
        "ma": ma_jp_target_lines,
        "sv": sv_jp_target_lines,
        "ha": ha_jp_target_lines,
        "vo": vo_jp_target_lines,
        "pa": pa_jp_target_lines,
        "pac": pa_jp_target_lines,
        "tec": tec_jp_target_lines,
        "tecc": tec_jp_target_lines,
        "rl": old_ring_jp_target_lines,
        "rr": old_ring_jp_target_lines,
        "co_m": co_m_jp_target_lines,
        "co_f": co_f_jp_target_lines,
        "ou_m": ou_m_jp_target_lines,
        "ou_f": ou_f_jp_target_lines,
        "arm_m": arm_m_jp_target_lines,
        "arm_f": arm_f_jp_target_lines,
        "bod_m": bod_m_jp_target_lines,
        "bod_f": bod_f_jp_target_lines,
        "leg_m": leg_m_jp_target_lines,
        "leg_f": leg_f_jp_target_lines,
    }
