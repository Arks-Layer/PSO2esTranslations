#!/usr/bin/env python3
# coding=utf8

import json
import os
import regex
import argparse
import unicodedata
from _ticket_gamefile.rules import lang_names, resolve_language


# ——————————————————————————————
# LANGUAGE & PATH SETTING
# ——————————————————————————————

# This tool translates descriptions from the JP text already stored in JSON.
root_dir = os.path.dirname(os.path.abspath(__file__))
json_loc = os.path.join(root_dir, os.pardir, "json")

# Translation slots are EN, KO, RU, CN and TH; -1 is the JP voice-actor fallback.
# Follow each JP text label, retain fields/markup, and leave missing native translations empty.
LANGS = {-1: "JP",
         0: "EN",
         1: "KO",
         2: "RU",
         3: "CN",
         4: "TH"}

# Full width character transtable for EN/KO/RU; CN/TH keep full width.
chartable = [
    "".maketrans("０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ　＝－＋／．＆（）：！",
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz =-+/.&():!"),
] * 3 + [{}, {}]

# ——————————————————————————————
# BASIC FUNCTIONS
# ——————————————————————————————


# [FUNCTION] Override the branch language and enable log-only debugging.
def parse_arguments(argv=None):
    parser = argparse.ArgumentParser(
        description = "Translates ticket item descriptions.")

    # Switch for description on untranslated names
    parser.add_argument("-a", dest = "all", action = "store_true",
                        help = ("Translate descriptions even for items "
                                "with no translated names."))

    # Switch for language.
    parser.add_argument("-l", "--lang", choices = lang_names[1:],
                        help = "Override the current branch language")

    parser.add_argument("--debug", action = "store_true",
                        help = "Print normal logs without writing target files")

    # Switch for retranslating all descriptions.
    parser.add_argument("-r", dest = "redo", action = "store_true",
                        help = ("Force all ticket descriptions to be processed, "
                                "even if already translated. "
                                "Always on for CN."))
    arguments = parser.parse_args(argv)
    try:
        arguments.lang = resolve_language(arguments.lang, os.path.dirname(root_dir))
    except ValueError as error:
        parser.error(str(error))
    return arguments

# [FUNCTION] For CN, copy the JP name into any empty tr_text.
def fill_cn_name(item):
    if LANG == 3 and item["tr_text"] == "":
        item["tr_text"] = item["jp_text"]

# [FUNCTION] Detach the green name prefix added by TicketFromGamefile.
def split_name_prefix(item):
    name_prefix = regex.match(r'<green>“[^\n]*”<c>\n', item["tr_explain"])
    name_prefix = name_prefix.group(0) if name_prefix else ""
    item["tr_explain"] = item["tr_explain"][len(name_prefix):]
    return name_prefix

# [FUNCTION] Resolve the item name, preferring the CN translation in the green prefix.
def get_item_name(item, name_prefix):
    if LANG == 3 and name_prefix:
        return name_prefix[len('<green>“'):-len('”<c>\n')]
    return item["tr_text"] or (item["jp_text"] if TRANS_ALL or LANG == 3 else "")

# [FUNCTION] Extract native name fields without using an empty or JP-filled name.
def get_item_name_parts(item, name_prefix, patterns):
    item_name = get_item_name(item, name_prefix)
    if not patterns[LANG] or not item_name or item_name == item["jp_text"]:
        return None
    match = regex.fullmatch(patterns[LANG], item_name)
    return match.groupdict(default="") if match is not None else None

# [FUNCTION] Match existing note markers without requiring paired color tags.
def source_note_pattern(pattern):
    return r"(?:<yellow>)?" + pattern + r"(?:<c>)?"

# [FUNCTION] Read a native title between the fixed parts of an existing template.
def get_existing_description_field(item, template, field):
    before, after = template.split("{" + field + "}")
    match = regex.search(regex.escape(before) + r"(?P<value>[^\r\n<>]+)" + regex.escape(after),
                         item["tr_explain"])
    if (match is None
            or LANG in (0, 1) and regex.search(r"[\p{Hiragana}\p{Katakana}\p{Han}]", match["value"])):
        return None
    return match["value"]

# [FUNCTION] Select a Korean particle from the final consonant of the translated word.
def get_korean_particle(word, consonant, vowel):
    return consonant if (ord(word[-1]) - 0xAC00) % 28 else vowel

# ——————————————————————————————
# SHARED DESCRIPTION DATA
# ——————————————————————————————


# Type labels shared by layered wear, cosmetic tickets and character parts.

ntype_locks = {
    # No JP restriction text; this default does not add a type note.
    # JP text: ""
    "a": ["All", "", "Все", "CN_All", ""],
    # JP text: ヒト型/キャストタイプ1
    "a1": ["Human/Cast Type 1", "인간형/캐스트타입1", "Человек/CAST (тип1)", "人類/機人類型1", "มนุษย์/แคสต์ Type 1"],
    # JP text: ヒト型/キャストタイプ2
    "a2": ["Human/Cast Type 2", "인간형/캐스트타입2", "Человек/CAST (тип2)", "人類/機人類型2", "มนุษย์/แคสต์ Type 2"],
    # JP text: ヒト型タイプ1
    "h1": ["Human Type 1", "인간형 타입1", "Человек (тип1)", "人類類型1", "มนุษย์ Type 1"],
    # JP text: ヒト型タイプ2
    "h2": ["Human Type 2", "인간형 타입2", "Человек (тип2)", "人類類型2", "มนุษย์ Type 2"],
    # JP text: キャストタイプ1
    "c1": ["Cast Type 1", "캐스트 타입1", "CAST (тип1)", "機人類型1", "แคสต์ Type 1"],
    # JP text: キャストタイプ2
    "c2": ["Cast Type 2", "캐스트 타입2", "CAST (тип2)", "機人類型2", "แคสต์ Type 2"]
}

# NGS Hairstyle tickets also use these labels when their JP source identifies Headparts.

cosmeticsorted_types = {
    # JP text: 頭部
    "Head": ["head", "헤드 파츠", "голова", "頭部", " Head "],
    # JP text: 顔バリエーション
    "Facetype": ["face type", "얼굴 유형", "тип лица", "臉部類型", " Face Pattern\nรูปแบบ"],
    # JP text: ヘッドパーツ
    "Headparts": ["head parts", "헤드 파츠", "части головы", "頭部部件", "ชิ้นส่วน Head Parts "],
    # JP text: ボディパーツ
    "Bodyparts": ["body parts", "바디 파츠", "части тела", "身體部件", "ติดตั้ง Body Parts "],
    # JP text: アームパーツ
    "Armparts": ["arm parts", "암 파츠", "части рук", "臂部部件", "ติดตั้ง Arm Parts "],
    # JP text: レッグパーツ
    "Legparts": ["leg parts", "레그 파츠", "части ног", "腿部部件", "ติดตั้ง Leg Parts "]
    }

# Weapon-type terms shared by motion tickets and weapon camouflages.
motion_weapon_types = {
    # JP text: 大剣
    "大剣": ["Sword", "소드", "", "大劍", "Sword"],
    # JP text: 自在槍
    "自在槍": ["Wired Lance", "와이어드 랜스", "", "自在槍", "Wired Lance"],
    # JP text: 長槍
    "長槍": ["Partizan", "파르티잔", "", "長槍", "Partizan"],
    # JP text: 双小剣
    "双小剣": ["Twin Daggers", "트윈 대거", "", "雙小劍", "Twin Dagger"],
    # JP text: 両剣
    "両剣": ["Double Saber", "더블 세이버", "", "雙頭劍", "Double Saber"],
    # JP text: 鋼拳
    "鋼拳": ["Knuckles", "너클", "", "鋼拳", "Knuckle"],
    # JP text: 銃剣
    "銃剣": ["Gunslash", "건슬래시", "", "槍刃", "Gunslash"],
    # JP text: 長銃
    "長銃": ["Assault Rifle", "어설트 라이플", "", "步槍", "Assault Rifle"],
    # JP text: 大砲
    "大砲": ["Launcher", "런처", "", "大炮", "Launcher"],
    # JP text: 双機銃
    "双機銃": ["Twin Machineguns", "트윈 머신건", "", "雙機槍", "Twin Machine Gun"],
    # JP text: 長杖
    "長杖": ["Rod", "로드", "", "長杖", "Rod"],
    # JP text: 導具
    "導具": ["Talis", "탈리스", "", "導具", "Talis"],
    # JP text: 短杖
    "短杖": ["Wand", "완드", "", "短杖", "Wand"],
    # JP text: 抜剣
    "抜剣": ["Katana", "카타나", "", "拔劍", "Katana"],
    # JP text: 強弓
    "強弓": ["Bullet Bow", "불릿 보우", "", "強弓", "Compound Bow"],
    # JP text: 魔装脚
    "魔装脚": ["Jet Boots", "제트 부츠", "", "魔裝腳", "Jet Boots"],
    # JP text: 飛翔剣
    "飛翔剣": ["Dual Blades", "듀얼 블레이드", "", "飛翔劍", "Dual Blade"],
    # JP text: 奏具
    "奏具": ["Takt", "택트", "", "奏具", "Tact"],
}


ticket_months = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

# JP ticket names establish the relation to the description target, without enumerating titles.
ticket_target_source_formats = {
    "treasure": r"(?P<target>(?:超・)?トレジャースクラッチ)券Vol\.(?P<number>[0-9]+)",
    "anniversary": r"(?P<target>[0-9]+周年[^\r\n<>]+?)(?:(?:スクラッチ)?(?:チケット|券)(?P<month>[A-Z][a-z]+)?|(?P<month>[A-Z][a-z]+)?景品交換券)",
    "reward": r"(?P<target>(?:超)?リワードボックス)メダル(?P<suffix>[^\r\n<>]*)",
    "scratch": r"(?P<target>[^\r\n<>]+?スクラッチ[^\r\n<>]*?)(?:補助)?券(?P<suffix>(?:[A-Z][a-z]+)?(?:'[0-9]+)?)",
    "item": r"(?P<target>[^\r\n<>]+)補助券",
}

# Native names supply the complete title; only ticket/medal suffixes and metadata are separated.
ticket_target_name_patterns = {
    # JP text: {target}券Vol.{number}
    "treasure": [
        r"(?P<target>.+?) Ticket Vol\.(?P<number>[0-9]+)",
        r"(?P<target>.+?)(?: 티켓|권) ?Vol\.(?P<number>[0-9]+)",
        "",
        r"(?P<target>.+?)券Vol\.(?P<number>[0-9]+)",
        "(?P<target>.+?) Ticket Vol\\.(?P<number>[0-9]+)",
    ],
    # JP text: {target}チケット / {target}スクラッチ券{month} / {target}{month}景品交換券
    "anniversary": [
        r"(?P<target>.+?)(?: Scratch)?(?P<month> {month})?(?: Exchange)? Ticket",
        r"(?P<target>.+?)(?: 스크래치)?(?:(?: 티켓|권)(?P<month> ?{month})?|(?P<month> ?{month})? 경품 교환권)",
        "",
        r"(?P<target>.+?)(?:轉蛋)?(?:(?:票券|券)(?P<month>{month})?|(?P<month>{month})?獎品交換券)",
        "(?P<target>.+?)(?: Scratch)?(?P<month> {month})?(?: Exchange)? Ticket",
    ],
    # JP text: {target}メダル{suffix}
    "reward": [
        r"(?P<target>.+?) Medal(?: (?P<suffix>[^\r\n<>]+))?",
        r"(?P<target>.+?) 메달(?P<suffix>[^\r\n<>]*)",
        "",
        r"(?P<target>.+?)獎章(?P<suffix>[^\r\n<>]*)",
        "(?P<target>.+?) Medal(?: (?P<suffix>[^\\r\\n<>]+))?",
    ],
    # JP text: {target}券{suffix} / {target}補助券{suffix}
    "scratch": [
        r"(?P<target>[^\r\n<>]*?Scratch[^\r\n<>]*?)(?: (?:Ticket|Voucher))?(?P<suffix> (?:[A-Z][a-z]+)? ?'[0-9]+)?",
        r"(?P<target>.+?)(?: 티켓|(?: 보조)?권)(?P<suffix>(?: ?[A-Z][a-z]+)?(?:'[0-9]+)?)",
        "",
        r"(?P<target>.+?)(?:輔助|補助)?券(?P<suffix>(?:[A-Z][a-z]+)?(?:'[0-9]+)?)",
        "(?P<target>[^\\r\\n<>]*?Scratch[^\\r\\n<>]*?)(?: (?:Ticket|Voucher))?(?P<suffix> (?:[A-Z][a-z]+)? ?'[0-9]+)?",
    ],
    # JP text: {target}補助券
    "item": [
        r"(?P<target>.+?) (?:Ticket|Voucher)",
        r"(?P<target>.+?)(?: ?보조권| 티켓)",
        "",
        r"(?P<target>.+?)(?:輔助|補助)券",
        "(?P<target>.+?) (?:Ticket|Voucher)",
    ],
}

ticket_target_formats = {
    # JP text: {target}{number}
    "treasure": ["{target} Vol.{number}", "{target}{number}", "", "{target}{number}", "{target} Vol.{number}"],
    # JP text: {target}{month}
    "anniversary": ["{target} Scratch{month}", "{target}{month}", "", "{target}{month}", "{target} Scratch{month}"],
    # JP text: {target}{suffix}
    "reward": ["{suffix} {target}", "{target}{suffix}", "", "{target}{suffix}", "{suffix} {target}"],
    # JP text: {target}{suffix}
    "scratch": ["{target}{suffix}", "{target}{suffix}", "", "{target}{suffix}", "{target}{suffix}"],
    # JP text: {target}
    "item": ["{target}", "{target}", "", "{target}", "{target}"],
    # JP text: {target}券
    "ticket": ["{target} Tickets", "{target}권", "", "{target}券", "{target} Ticket"],
    # JP text: 超・{target}
    "super_treasure": ["Super {target}", "초 {target}", "", "超·{target}", "Super {target}"],
    # JP text: 超{target}
    "super_reward": ["Super {target}", "초 {target}", "", "超{target}", "Super {target}"],
    # JP text: 【チケット版】{target}
    "version": ["[Ticket] {target}", "【티켓판】{target}", "", "【票券版】{target}", ""],
}


cosmetic_desc_formats = {
    # JP text:
    # 使用すると、新しい{itype}の\n
    # {iname}が選択可能。
    # {sexlock} unavailable.
    "use_new": [
        ("Unlocks the {sexlock}{itype}\n"
         "\"{iname}\"\n"
         "for use in the Beauty Salon."),
        ("사용하면 새로운 {sexlock}{itype}인\n"
         "「{iname}」 항목을\n"
         "선택할 수 있다."),
        ("Разблок-т {itype} {sexlock}\n"
         "\"{iname}\"\n"
         "для использования в салоне."),
        ("使用後，可選用新的{sexlock}{itype}\n"
         "{iname}。"),
        ("เมื่อใช้งาน จะสามารถเลือก{sexlock}{itype}ใหม่ \"{iname}\" ได้"),
    ],
    # JP text:
    # チケットを使用すると、{itype}\n
    # {iname}が選択可能。
    # {sexlock} unavailable.
    "ticket": [
        ("Unlocks the {sexlock}{itype}\n"
         "\"{iname}\"\n"
         "for use in the Beauty Salon."),
        ("티켓을 사용하면 {sexlock}{itype}\n"
         "「{iname}」 항목을\n"
         "선택할 수 있다."),
        ("Разблок-т {itype} {sexlock}\n"
         "\"{iname}\"\n"
         "для использования в салоне."),
        ("使用票券後，可選用{sexlock}{itype}\n"
         "{iname}。"),
        ("เมื่อใช้งาน จะสามารถเลือก{sexlock}{itype}ใหม่ \"{iname}\" ได้"),
    ],
    # JP text:
    # チケットを使用すると、新しい{itype}の\n
    # {iname}が選択可能。
    # {sexlock} unavailable.
    "ticket_new": [
        ("Unlocks the {sexlock}{itype}\n"
         "\"{iname}\"\n"
         "for use in the Beauty Salon."),
        ("티켓을 사용하면 새로운 {sexlock}{itype}인\n"
         "「{iname}」 항목을\n"
         "선택할 수 있다."),
        ("Разблок-т {itype} {sexlock}\n"
         "\"{iname}\"\n"
         "для использования в салоне."),
        ("使用票券後，可選用新的{sexlock}{itype}\n"
         "{iname}。"),
        ("เมื่อใช้งาน จะสามารถเลือก{sexlock}{itype}ใหม่ \"{iname}\" ได้"),
    ],
    # JP text:
    # 特定ステッカーの装着許可チケット。\n
    # 使用すると、新しい{itype}の\n
    # {iname}が選択可能。
    # {sexlock} unavailable.
    "sticker_use_new": [
        ("Unlocks the {sexlock}{itype}\n"
         "\"{iname}\"\n"
         "for use in the Beauty Salon."),
        ("특정 스티커의 부착을 허용하는 티켓.\n"
         "사용하면 스티커 선택 항목에\n"
         "「{iname}」 항목이 추가된다."),
        ("Разблок-т {itype} {sexlock}\n"
         "\"{iname}\"\n"
         "для использования в салоне."),
        ("許可著裝特定貼紙的票券。\n"
         "使用後，可選用新的{sexlock}{itype}\n"
         "{iname}。"),
        ("เมื่อใช้งาน จะสามารถเลือก{sexlock}{itype}ใหม่ \"{iname}\" ได้"),
    ],
}

ndesc_formats = {
    # JP text:
    # 使用すると新しい{itype}が\n
    # 選択可能になる。
    "n": [
        ("Unlocks {a}new {itype} for use."),
        ("사용하면 새로운 {itype}{a}\n"
         "선택할 수 있게 된다."),
        ("Разблок {itype}."),
        ("使用後可選用新的{itype}。"),
        ("เมื่อใช้งาน จะสามารถเลือก{itype}ใหม่ได้"),
    ],
    # JP text:
    # 使用すると新しい{itype}が\n
    # 全キャラクターで選択可能になる。
    "allcharacters": [
        ("A {itype} that unlocks for all\n"
         "characters on your account."),
        ("사용하면 새로운 {itype}{a}\n"
         "모든 캐릭터에서 선택할 수 있게 된다."),
        ("{itype}, разблок. для\n"
         "всех персонажей аккаунта."),
        ("使用後所有角色均可選用新的{itype}。"),
        ("เมื่อใช้งาน จะสามารถเลือก{itype}ใหม่ได้กับทุกตัวละครในไอดี"),
    ],
    # JP text:
    # 使用すると新しい{itype}パターンが\n
    # 選択可能になる。
    "pattern": [
        ("Unlocks {a}new {itype} for use."),
        ("사용하면 새로운 {itype} 패턴을\n"
         "선택할 수 있게 된다."),
        ("Разблок {itype}."),
        ("使用後可選用新的{itype}種類。"),
        ("เมื่อใช้งาน จะสามารถเลือก{itype}ใหม่ได้"),
    ],
    # JP text:
    # 使用すると新しい{itype}が\n
    # 全キャラクターで選択可能になる。
    "account_item": [
        ("A {itype} that unlocks for all\n"
         "characters on your account."),
        ("사용하면 새로운 {itype}\n"
         "모든 캐릭터에서 선택할 수 있게 된다."),
        ("{itype}, разблок. для\n"
         "всех персонажей аккаунта."),
        ("使用後所有角色均可選用新的{itype}。"),
        ("เมื่อใช้งาน จะสามารถเลือก{itype}ใหม่ได้กับทุกตัวละครในไอดี"),
    ],
}

# Translated notes reused across categories; source recognizers still control which notes are allowed.

shared_extras = {
    # JP text: ※対応：{type}
    "type": [
        ("\n<yellow>※Type: {type}<c>"),
        ("\n<yellow>※대응: {type}<c>"),
        ("\n<yellow>※Тип: {type}<c>"),
        ("\n<yellow>※適用於：{type}<c>"),
        ("\n<yellow>※ประเภท: {type}<c>"),
    ],
    # JP text:
    # ※着用時はインナーが非表示になります。
    "hide_inner": [
        ("\n<yellow>※Hides innerwear when worn.<c>"),
        ("\n<yellow>※착용 시 이너웨어는 표시하지 않음.<c>"),
        ("\n<yellow>※При экипировке скрывает In.<c>"),
        ("\n<yellow>※穿著時不會顯示內衣。<c>"),
        (""),
    ],
    # JP text:
    # ※カラー変更非対応
    "color": [
        ("\n<yellow>※Color cannot be changed<c>"),
        ("<yellow>※색상을 변경할 수 없음<c>"),
        ("\n<yellow>※Цвет нельзя изменить<c>"),
        ("\n<yellow>※不適用於顏色的變更<c>"),
        ("\n<yellow>※ไม่สามารถเปลี่ยนสีได้<c>"),
    ],
    # JP text:
    # ※『PSO2』ブロック非対応
    "ngs": [
        ("\n<yellow>※Not available in [PSO2] Blocks.<c>"),
        ("\n<yellow>※『PSO2』 블록 미지원<c>"),
        ("\n<yellow>※Нельзя использовать в блоке PSO2<c>"),
        ("\n<yellow>※不適用於『PSO2』<c>"),
        ("\n<yellow>※ไม่รองรับการใช้งานในบล็อก \"PSO2\"<c>"),
    ],
}

cosmetic_extras = {
    # JP text:
    # ※一部の顔、ヘッドパーツ非対応
    "face": [
        ("\n<yellow>※Not compatible with some heads/faces.<c>"),
        ("\n<yellow>※일부 얼굴과 헤드 파츠 미지원<c>"),
        ("\n<yellow>※<c>"),
        ("\n<yellow>※不適用於部分面部、頭部部件<c>"),
        ("\n<yellow>※ไม่รองรับบางใบหน้าและชิ้นส่วน Head Parts<c>"),
    ],
    # No existing KO source for the weapon-position note.
    # JP text:
    # ※武器の構え位置自動調整
    "posture": [
        ("\n<yellow>※Uses adjusted weapon positions.<c>"),
        (""),
        ("\n<yellow>※Исп. скоррект. положение.<c>"),
        ("\n<yellow>※自動調整武器架勢的位置<c>"),
        ("\n<yellow>※ปรับตําแหน่งการถืออาวุธอัตโนมัติ<c>"),
    ],
    # JP text:
    # ※サイズ調整はできません。
    "size": [
        ("\n<yellow>※Size cannot be adjusted.<c>"),
        ("\n<yellow>※크기는 조절할 수 없습니다.<c>"),
        ("\n<yellow>※Нельзя отрегулировать размер.<c>"),
        ("\n<yellow>※無法調整尺寸。<c>"),
        ("\n<yellow>※ไม่สามารถปรับขนาดได้<c>"),
    ],
    # JP text:
    # ※カラーは変更できません
    "color": [
        ("\n<yellow>※Color cannot be changed<c>"),
        ("\n<yellow>※색상은 변경할 수 없다<c>"),
        ("\n<yellow>※Цвет нельзщя изменить.<c>"),
        ("\n<yellow>※無法變更顏色<c>"),
        ("\n<yellow>※ไม่สามารถเปลี่ยนสีได้<c>"),
    ],
}

# The complete JP source lines, including the SANRIO notice, are the dictionary keys.
ticket_extras = {
    # JP text: ※PS4表示不可
    "※PS4表示不可": [
        ("\n<yellow>※Cannot be used on PS4<c>"),
        ("\n<yellow>※PS4에서는 표시할 수 없음<c>"),
        (""),
        ("\n<yellow>※PS4不可顯示<c>"),
        ("\n<yellow>※ไม่สามารถแสดงผลบน PS4 ได้<c>"),
    ],
    # JP text: ※PS4表示可
    "※PS4表示可": [
        ("\n<yellow>※Can be displayed on PS4<c>"),
        ("\n<yellow>※PS4에서 표시 가능<c>"),
        (""),
        ("\n<yellow>※PS4可顯示<c>"),
        ("\n<yellow>※สามารถแสดงผลบน PS4 ได้<c>"),
    ],
    # JP text: ※アニメーションはしません。
    "※アニメーションはしません。": [
        ("\n※Does not animate."),
        ("\n※애니메이션 효과는 없다."),
        (""),
        ("\n※不會播放動畫。"),
        ("\n<yellow>※ไม่มีการเคลื่อนไหวแอนิเมชัน<c>"),
    ],
    # JP text: キャスト男性ボディ向け。
    "キャスト男性ボディ向け。": [
        ("\nSuited to male CAST bodies."),
        ("\n캐스트 남성 바디에 맞춘 액세서리."),
        (""),
        ("\n適合男性機人身體。"),
        ("\n<yellow>※สําหรับหุ่นแคสต์ชาย (Cast Type 1)<c>"),
    ],
    # JP text: c'76,'15 SANRIO APPR.NO.S564996
    "c'76,'15 SANRIO APPR.NO.S564996": [
        ("\nc'76,'15 SANRIO APPR.NO.S564996"),
        ("\nc'76,'15 SANRIO APPR.NO.S564996"),
        ("\nc'76,'15 SANRIO APPR.NO.S564996"),
        ("\nc'76,'15 SANRIO APPR.NO.S564996"),
        ("\nc'76,'15 SANRIO APPR.NO.S564996"),
    ],
}


cosmetic_source_formats = {
    "use_new": r"{intro}使用すると、新しい{itype}の\n(?P<iname>[^\r\n<>]+?)が選択可能。",
    "ticket_new": r"{intro}チケットを使用すると、新しい{itype}の\n(?P<iname>[^\r\n<>]+?)が選択可能。",
    "ticket": r"{intro}チケットを使用すると、{itype}\n(?P<iname>[^\r\n<>]+?)が選択可能。",
}

ncosmetic_source_formats = {
    "n": r"使用すると新しい{itype}が\n選択可能になる。",
    "allcharacters": r"使用すると新しい{itype}が\n全キャラクターで選択可能になる。",
    "pattern": r"使用すると新しい{itype}パターンが\n選択可能になる。",
}

shared_source_extras = {
    "sex": r"\n" + source_note_pattern(r"(?P<sex>男|女)性のみ使用可能。"),
    "type": r"\n(?:<yellow>)?※対応：(?P<race>ヒト型/キャスト|ヒト型|キャスト)タイプ(?P<number>[12])<c>",
    "hide_inner": r"\n" + source_note_pattern("※着用時はインナーが非表示になります。"),
    "ncolor": r"(?:\n)?" + source_note_pattern("※カラー変更非対応"),
    "ngs": r"\n" + source_note_pattern("※『PSO2』ブロック非対応"),
}

# Build ticket recognizers after ticket_extras, whose keys supply the recognized JP lines.
ticket_source_extras = {
    source: (r"\n[^\S\r\n]*" + regex.escape(source) + r"[^\S\r\n]*" if "SANRIO" in source else
             r"\n" + source_note_pattern(regex.escape(source)))
    for source in ticket_extras
}

# ——————————————————————————————
# SHARED DESCRIPTION FUNCTIONS
# ——————————————————————————————

# [FUNCTION] Match the entire JP source as a body plus allowed notes, rejecting unknown tails.
def match_description(item, formats, extra_formats, **fields):
    source = item["jp_explain"]
    for desc_sort, pattern in formats.items():
        body = regex.match(pattern.format(**fields), source)
        if body is None:
            continue
        position = body.end()
        extras = {}
        while position < len(source):
            for key, extra_pattern in extra_formats.items():
                extra = regex.match(extra_pattern, source, pos=position)
                if extra is not None:
                    if key in extras:
                        return None
                    extras[key] = extra.groupdict()
                    position = extra.end()
                    break
            else:
                break
        else:
            if all(note in extras for note in ("※PS4表示可", "※PS4表示不可")):
                return None
            return desc_sort, body.groupdict(), extras
    return None

# [FUNCTION] Translate common ticket notes in source order; None means a missing translation.
def get_ticket_extras(extras):
    translated = []
    for source in extras:
        if source in ticket_extras:
            if not ticket_extras[source][LANG]:
                return None
            translated.append(ticket_extras[source][LANG])
    return "".join(translated)

# [FUNCTION] Apply shared name/redo gates after the category has recognized its JP source.
def get_translation_problem(item, item_name=None, redo=False):
    if item_name == "":
        return -1
    # Callers that omit item_name retain their existing -a/CN eligibility check.
    if item_name is None and not TRANS_ALL and item["tr_text"] == "" and LANG != 3:
        return -1
    if not (REDO_ALL or redo) and item["tr_explain"] != "":
        return -2
    return 0

# [FUNCTION] Store the translated body and apply full-width character conversion.
# normalize=False preserves literal wording and line breaks.
def set_description(item, description, normalize=True):
    item["tr_explain"] = description.translate(chartable[LANG]) if normalize and LANG != 1 else description
    return 0

# [FUNCTION] Convert optional JP race/type restrictions to the existing translation-table keys.
def get_type_restrictions(extras):
    restriction = extras.get("type")
    if restriction is None:
        return "a"
    return {"ヒト型/キャスト": "a", "ヒト型": "h", "キャスト": "c"}[restriction["race"]] + restriction["number"]

# [FUNCTION] Derive a related ticket target from this item's native name and JP-only qualifiers.
def get_ticket_target_name(item, name_prefix, source):
    for target_type, pattern in ticket_target_source_formats.items():
        match = regex.fullmatch(pattern, item["jp_text"])
        if match is None:
            continue
        fields = match.groupdict(default="")
        month = fields.get("month", "")
        if month and month not in ticket_months:
            return None
        source_target = fields["target"] + fields.get("number", "") + month + fields.get("suffix", "")
        expected_target = source
        qualifier = ""
        if target_type in ("treasure", "reward"):
            prefix = "超・" if target_type == "treasure" else "超"
            source_target = source_target.removeprefix(prefix)
            expected_target = source.removeprefix(prefix)
            if source.startswith(prefix) and not item["jp_text"].startswith(prefix):
                qualifier = "super_" + target_type
        elif target_type == "anniversary":
            expected_target = source.removeprefix("【チケット版】")
            if source.startswith("【チケット版】"):
                qualifier = "version"
        elif target_type == "scratch":
            expected_target = source.removesuffix("券")
            if source.endswith("券"):
                qualifier = "ticket"
        if source_target != expected_target:
            continue

        patterns = [pattern.format(month=regex.escape(month))
                    for pattern in ticket_target_name_patterns[target_type]]
        parts = get_item_name_parts(item, name_prefix, patterns)
        if parts is None:
            return None
        if (target_type == "treasure" and parts["number"] != fields["number"]
                or target_type == "anniversary" and parts["month"].strip() != month):
            return None
        if target_type == "anniversary" and month and LANG in (0, 1):
            parts["month"] = " " + month
        parts["target"] = parts["target"].strip()
        if target_type == "scratch" and LANG == 0:
            kind = ("Special" if "スペシャルスクラッチ" in fields["target"] else
                    "SP" if "SPスクラッチ" in fields["target"] else "")
            if kind and not regex.search(r"\b(?:Special|SP) Scratch\b", parts["target"]):
                parts["target"] = parts["target"].replace("Scratch", kind + " Scratch", 1)
        template = ticket_target_formats[target_type][LANG]
        if not template:
            return None
        target = template.format(**parts).strip()
        if qualifier:
            template = ticket_target_formats[qualifier][LANG]
            if not template:
                return None
            target = template.format(target=target)
        return target
    return None

# ——————————————————————————————
# LAYERED WEAR RULES & TRANSLATION
# ——————————————————————————————


layered_file_names = ["BaseWear_Female",
                      "BaseWear_Male",
                      "InnerWear_Female",
                      "InnerWear_Male",
                      "Stack_OuterWearF",
                      "Stack_OuterWearM"]

layered_wear_types = {
    # JP text:
    # インナーウェア
    "In": ["innerwear", "이너웨어", "внутреннюю одежду (In)", "內衣", "สวมใส่ InnerWear "],
    # JP text:
    # ベースウェア
    "Ba": ["basewear", "베이스웨어", "верхнюю одежду (Ba)", "底衣", "สวมใส่ BaseWear "],
    # JP text:
    # セットウェア
    "Se": ["setwear", "세트웨어", "комплектную одежду (Se)", "套服", "สวมใส่ SetWear "],
    # JP text:
    # フルセットウェア
    "Fu": ["full setwear", "풀세트웨어", "полн.компл.одежду (Fu)", "全身套服", "สวมใส่ Full Setwear "],
    # JP text:
    # アウターウェア
    "Ou": ["outerwear", "아우터웨어", "внешнюю одежду (Ou)", "外套", "สวมใส่ Outerwear "],
    # JP text:
    # トータルウェア
    "To": ["totalwear", "토탈웨어", "", "完整裝扮", "สวมใส่ TotalWear "],
}

layer_source_types = {
    "In": "インナーウェア", "Ba": "ベースウェア", "Se": "セットウェア",
    "Fu": "フルセットウェア", "Ou": "アウターウェア", "To": "トータルウェア",
}

# Source kinds are independent of the name suffix used to render the translation.
layer_source_type_pattern = "(?:" + "|".join(map(regex.escape, layer_source_types.values())) + ")"


# Stop at the first template ending; the remaining source must be recognized extras.
layer_source_formats = {
    "old": r"使用すると、新しい{itype}の\n(?P<iname>[^\r\n<>]+?)が選択可能。",
    "new": r"使用すると新しい{itype}が\n選択可能になる。",
}

layer_source_extras = {
    "sex": shared_source_extras["sex"],
    "hide_inner": shared_source_extras["hide_inner"],
}

nlayer_source_extras = {
    "sync_inner": r"\n" + source_note_pattern(r"※一部\[In\]カラー同期"),
    "type": shared_source_extras["type"],
    "hide_inner": shared_source_extras["hide_inner"],
    "hide_accessories": r"\n" + source_note_pattern("※アクセサリー表示非対応"),
    "ncolor": shared_source_extras["ncolor"],
}


# JP text:
# 使用すると、新しい{itype}の\n
# {iname}が選択可能。
layer_desc_formats = [
    ("Unlocks the new {itype}\n"
     "\"{iname}\"."),
    ("사용하면 새로운 {itype}인\n"
     "「{iname}」 항목을\n"
     "선택할 수 있다."),
    ("Разблокирует новую\n"
     "{itype}\n"
     "\"{iname}\"."),
    ("使用後，可選用新的{itype}\n"
     "{iname}。"),
    ("เมื่อใช้งาน จะสามารถเลือก{itype}ใหม่ \"{iname}\" ได้"),
]

# Layered-wear notes include their own separators and color markup.
layer_extras = {
    # JP source has no sex restriction line; this extra is intentionally empty.
    # JP text: ""
    "n": ["", "", "", "", ""],
    # JP text:
    # 男性のみ使用可能。
    "m": [
        ("\nOnly usable on male characters."),
        (" 남성만 가능."),
        ("\nТолько для мужских персонажей."),
        ("\n僅限男性使用。"),
        (""),
    ],
    # JP text:
    # 女性のみ使用可能。
    "f": [
        ("\nOnly usable on female characters."),
        (" 여성만 가능."),
        ("\nТолько для женских персонажей."),
        ("\n僅限女性使用。"),
        (""),
    ],
    # JP text:
    # ※一部[In]カラー同期
    "sync_inner": [
        ("\n<yellow>※Synchronizes with [In] color.<c>"),
        ("\n<yellow>※일부 [In]컬러 동기화<c>"),
        ("\n<yellow>※Цвета некоторых [In] синхр-ся.<c>"),
        ("\n<yellow>※與一部分[In]同步顏色<c>"),
        (""),
    ],
    # JP text:
    # ※アクセサリー表示非対応
    "hide_accessories": [
        ("\n<yellow>※Hides accessories when worn.<c>"),
        ("\n<yellow>※액세서리 표시 미지원<c>"),
        ("\n<yellow>※Скрывает аксессуары.<c>"),
        ("\n<yellow>※不適用於飾品的顯示<c>"),
        ("\n<yellow>※ไม่รองรับการแสดงผลเครื่องประดับ<c>"),
    ],
}

# [FUNCTION] Translate layered wear, delegating matched NGS bodies to translate_nlayer_desc.
def translate_layer_desc(item, file_name, name_prefix):
    wear_type = item["jp_text"][-3:-1] if item["jp_text"].endswith("]") else file_name.replace("Stack_", "")[:2]
    description = match_description(
        item, {"old": layer_source_formats["old"]},
        {**ticket_source_extras, **layer_source_extras}, itype=layer_source_type_pattern)
    if description is None:
        description = match_description(
            item, {"new": layer_source_formats["new"]},
            {**ticket_source_extras, **nlayer_source_extras}, itype=layer_source_type_pattern)
        if description is None:
            return -4
        return translate_nlayer_desc(item, file_name, name_prefix, description)
    _, _, source_extras = description

    item_name = get_item_name(item, name_prefix)
    problem = get_translation_problem(item, item_name)
    if problem:
        return problem
    if wear_type not in layered_wear_types:
        return -5
    if not layered_wear_types[wear_type][LANG] or not layer_desc_formats[LANG]:
        return -5
    extras = get_ticket_extras(source_extras)
    if extras is None:
        return -5

    sex = {"男": "m", "女": "f"}.get(source_extras.get("sex", {}).get("sex"), "n")
    hideinner = "hide_inner" in source_extras
    if (sex != "n" and not layer_extras[sex][LANG]
            or hideinner and not shared_extras["hide_inner"][LANG]):
        return -5

    body = layer_desc_formats[LANG].format(
        itype = layered_wear_types[wear_type][LANG],
        iname = item_name,
    )
    description_extras = [
        layer_extras[sex][LANG] if sex != "n" else "",
        shared_extras["hide_inner"][LANG] if hideinner == True else ""
    ]
    return set_description(item, body + "".join(description_extras) + extras)

# [FUNCTION] Render an already matched NGS layered-wear body and its allowed notes.
def translate_nlayer_desc(item, file_name, name_prefix, description):
    wear_type = item["jp_text"][-3:-1] if item["jp_text"].endswith("]") else file_name.replace("Stack_", "")[:2]
    _, _, source_extras = description

    item_name = get_item_name(item, name_prefix)
    problem = get_translation_problem(item, item_name)
    if problem:
        return problem
    if wear_type not in layered_wear_types:
        return -5
    item_type = layered_wear_types[wear_type][LANG]
    if not item_type or not ndesc_formats["n"][LANG]:
        return -5
    extras = get_ticket_extras(source_extras)
    if extras is None:
        return -5

    syncinner = "sync_inner" in source_extras
    types = get_type_restrictions(source_extras)
    hideinner = "hide_inner" in source_extras
    hideaccess = "hide_accessories" in source_extras
    ncolorlocked = "ncolor" in source_extras
    if (types != "a" and (not shared_extras["type"][LANG] or not ntype_locks[types][LANG])
            or syncinner and not layer_extras["sync_inner"][LANG]
            or hideinner and not shared_extras["hide_inner"][LANG]
            or hideaccess and not layer_extras["hide_accessories"][LANG]
            or ncolorlocked and not shared_extras["color"][LANG]):
        return -5

    body = ndesc_formats["n"][LANG].format(
        itype = item_type,
        a = get_korean_particle(item_type, "을", "를") if LANG == 1 else "a ",
    )
    description_extras = [
        layer_extras["sync_inner"][LANG] if syncinner == True else "",
        "" if types == "a" else shared_extras["type"][LANG].format(type=ntype_locks[types][LANG]),
        shared_extras["hide_inner"][LANG] if hideinner == True else "",
        layer_extras["hide_accessories"][LANG] if hideaccess == True else "",
        shared_extras["color"][LANG] if ncolorlocked == True else ""
    ]
    return set_description(item, body + "".join(description_extras) + extras)

# ——————————————————————————————
# COSMETIC RULES & TRANSLATION
# ——————————————————————————————

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
    "Stack_Skin",
    "Stack_Stamp",
    "Stack_Sticker",
    "Stack_Tooth",
    "Stack_Vital_Gauge"
    ]

# These account item types use the complete KO object phrase from the source JSON.
account_item_types = {
    # JP text: アークスカードの背景
    "Stack_Arkscard_BG": [
        ("background for your ARKS\n"
         "Card"),
        ("아크스 카드 배경을"),
        (""),
        ("\nARKS名片背景"),
        ("ใช้พื้นหลัง ARKS Card "),
    ],
    # JP text: ポータブルホログラム
    **dict.fromkeys(
        ("Stack_CS_Effect", "Stack_CS_Room_Goods", "Stack_CS_Stickers"),
        [
            ("Portable Hologram"),
            ("포터블 홀로그램을"),
            (""),
            ("\n便攜全息投影"),
            ("ใช้ Portable Hologram (PH) "),
        ],
    ),
    # JP text: プレイマット
    "Stack_Duel_Card_Play_Mat": ["playmat", "플레이 매트를", "", "牌桌墊", "ใช้ Playmat "],
    # JP text: カードスリーブ
    "Stack_Duel_Card_Sleeve": ["card sleeve", "카드 슬리브를", "", "牌套", "ใช้ Card Sleeve "],
    # JP text: カード
    "Stack_Duel_Card_Ticket": ["card", "카드를", "", "卡牌", "ใช้ Card "],
    # JP text: バイタルゲージの背景
    "Stack_Vital_Gauge": [
        ("Vital Gauge BG"),
        ("바이탈 게이지 배경을"),
        (""),
        ("\n體征槽背景"),
        ("ใช้พื้นหลัง Vital Gauge "),
    ],
}

cosmetic_types = {
    **account_item_types,
    # JP text: アクセサリー
    "Stack_Accessory": ["accessory", "액세서리", "аксессуар", "飾品", "ใส่ Accessory "],
    # JP text: ボディペイント
    "Stack_BodyPaint": ["body paint", "바디 페인트", "рис. тела", "身體彩繪", "ใช้ Body Paint "],
    # JP text: 耳
    "Stack_Ear": ["ear shape", "귀", "форма ушей", "耳朵", "รูปทรงใบหู"],
    # JP text: 瞳
    "Stack_Eye": ["eye pattern", "눈동자", "глаза", "瞳孔", "ลวดลาย Eye Pattern "],
    # JP text: まゆ
    "Stack_EyeBrow": ["eyebrow type", "눈썹", "брови", "眉毛", "ทรง Eyebrow "],
    # JP text: まつげ
    "Stack_EyeLash": ["eyelash type", "속눈썹", "ресницы", "睫毛", "ทรง Eyelash "],
    # JP text: メイク
    "Stack_FacePaint": ["makeup", "메이크업", "макияж", "妝容", "ลวดลาย Face Paint "],
    # JP text: 髪型 / ヘアスタイル
    "Stack_Hairstyle": ["hairstyle", "헤어스타일", "причёску", "髪型", " Hairstyle "],
    # JP text: 角
    "Stack_Horn": ["horn type", "뿔", "тип рога", "角", "รูปทรงเขา"],
    # JP text: モーション
    "Stack_MotionChange": ["motion", "모션", "движение", "行動方式", "ใช้โมชัน"],
    # JP text: 肌
    "Stack_Skin": ["body type", "피부", "", "皮膚", ""],
    # JP text: スタンプ
    "Stack_Stamp": ["stamp", "스탬프", "штамп", "表情圖", "ใช้สแตมป์"],
    # JP text: ステッカー
    "Stack_Sticker": ["sticker", "스티커", "стикер", "貼紙", " Sticker "],
    # JP text: 歯・舌
    "Stack_Tooth": [
        ("teeth and tongue\n"
         "set"),
        ("치아 또는 혀"),
        ("зубы и язык"),
        ("牙齒、舌頭"),
        ("ลักษณะฟันและลิ้น"),
    ],
}

# Translated sex restrictions are type labels used by cosmetic_desc_formats.

cosmetic_sex_locks = {
    # JP text: 男性のみ
    "m": ["male-only ", "남성 전용 ", "только для М", "男性專用", ""],
    # JP text: 女性のみ
    "f": ["female-only ", "여성 전용 ", "только для Ж", "女性專用", ""]
}

# JP type terms and description recognizers; body formats live in the shared section.

# Old source term first, followed by accepted new source terms.
cosmetic_source_types = {
    "Stack_Accessory": ("アクセサリー", "アクセサリー"),
    "Stack_BodyPaint": ("ボディペイント", "ボディペイント"),
    "Stack_Arkscard_BG": ("アークスカードの背景", "アークスカードの背景"),
    **dict.fromkeys(("Stack_CS_Effect", "Stack_CS_Room_Goods", "Stack_CS_Stickers"),
                    ("ポータブルホログラム", "ポータブルホログラム")),
    "Stack_Duel_Card_Play_Mat": ("プレイマット", "プレイマット"),
    "Stack_Duel_Card_Sleeve": ("カードスリーブ", "カードスリーブ"),
    "Stack_Duel_Card_Ticket": ("カード", "カード"),
    "Stack_Ear": ("耳", "耳"), "Stack_Eye": ("瞳", "瞳"),
    "Stack_EyeBrow": ("まゆ", "まゆ"), "Stack_EyeLash": ("まつげ", "まつげ"),
    "Stack_FacePaint": ("メイク", "メイク"), "Stack_Hairstyle": ("髪型", "ヘアスタイル", "ヘッドパーツ"),
    "Stack_Horn": ("角", "角"), "Stack_MotionChange": ("モーション", "モーション"),
    "Stack_Skin": ("肌", "肌"), "Stack_Stamp": ("スタンプ", "スタンプ"),
    "Stack_Sticker": ("ステッカー", "ステッカー"), "Stack_Tooth": ("歯・舌", "歯・舌"),
    "Stack_Vital_Gauge": ("バイタルゲージの背景", "バイタルゲージの背景"),
}

sticker_source_formats = {
    "sticker_use_new": r"特定ステッカーの装着許可チケット。\n使用すると、新しいステッカーの\n(?P<iname>[^\r\n<>]+?)が選択可能。",
    "no_sticker": r"特定ステッカーの非表示許可チケット。\n使用すると、ステッカーの\n非表示が選択可能。",
}

cosmetic_source_extras = {
    "sex": shared_source_extras["sex"],
    "size": r"\n" + source_note_pattern("※サイズ調整はできません。"),
    "color": r"\n" + source_note_pattern("※カラーは変更できません"),
    "ncolor": shared_source_extras["ncolor"],
}

ncosmetic_source_extras = {
    "type": shared_source_extras["type"],
    "hide_inner": shared_source_extras["hide_inner"],
    "weapons": r"\n" + source_note_pattern(r"※武器装備反映(?:[（(](?P<weapon>[^）)\r\n<>]+)[）)])?／\s*『PSO2』ブロック非対応"),
    "ngs": shared_source_extras["ngs"],
    "face": r"\n" + source_note_pattern("※一部の顔、ヘッドパーツ非対応"),
    "ncolor": shared_source_extras["ncolor"],
}

# Translated-name extraction for scarf_intro_formats; this is not a JP-body rule.
# JP names use {owner}マフラー; translated names below supply the localized owner.
scarf_name_patterns = [r"(.+) Muffler", r"(.+) 머플러", "", r"(.+)圍巾", ""]


# JP text:
# 特定ステッカーの非表示許可チケット。\n
# 使用すると、ステッカーの\n非表示が選択可能。
no_sticker_desc = [
    ("Unlocks the ability to not display a\n"
     "sticker in the Beauty Salon."),
    ("스티커를 숨길 수 있게 해 주는 티켓.\n"
     "사용하면 스티커 설정에서\n"
     "숨김을 선택할 수 있다."),
    ("Разблокирует возможность\n"
     "не отображать стикер в салоне."),
    ("許可不顯示特定貼紙的票券。\n"
     "使用後可以選擇不顯示貼紙。"),
    ("เมื่อใช้งาน จะสามารถเลือกซ่อน Sticker (ไม่แสดงผล) ในร้านเสริมสวยได้"),
]

# JP text: {owner}愛用の赤いマフラー。
scarf_intro_formats = [
    ("{owner}'s favorite red muffler.\n"),
    ("{owner}이 즐겨 쓰는 붉은 머플러.\n"),
    (""),
    ("{owner}愛用的紅色圍巾。\n"),
    (""),
]

# Motion tickets use these notes; lobby actions keep their own feature rules below.

motion_extras = {
    # JP text:
    # 武器装備反映／\n
    # 『PSO2』ブロック非対応
    "weapons": [
        ("\n<yellow>※Shows equipped weapons.\n"
         "Not available in [PSO2] Blocks.<c>"),
        ("\n<yellow>※장비한 무기 반영／\n"
         "『PSO2』 블록 미지원<c>"),
        ("\n<yellow>※Показывает экип-е оружие.\n"
         "Нельзя использовать в блоке PSO2<c>"),
        ("\n<yellow>※適用功能：顯示裝備武器\n"
         "不適用於『PSO2』<c>"),
        ("\n<yellow>※แสดงผลตามอาวุธที่สวมใส่ / ไม่รองรับในบล็อก \"PSO2\"<c>"),
    ],
    # JP text: 武器装備反映（{weapon_type}）／\n『PSO2』ブロック非対応.
    "typed_weapons": [
        ("\n<yellow>※Shows equipped weapons ({weapon_type}).\n"
         "Not available in [PSO2] Blocks.<c>"),
        ("\n<yellow>※장비한 무기 반영（{weapon_type}）／\n"
         "『PSO2』 블록 미지원<c>"),
        (""),
        ("\n<yellow>※適用功能：顯示裝備武器（{weapon_type}）\n"
         "不適用於『PSO2』<c>"),
        ("\n<yellow>※แสดงผลตามอาวุธที่สวมใส่ ({weapon_type}) / ไม่รองรับในบล็อก \"PSO2\"<c>"),
    ],
}

# NGS cosmetic tickets reuse the shared ndesc_formats body templates.

# [FUNCTION] Translate cosmetic tickets using the old or NGS format recognized from the JP source.
def translate_cosmetic_desc(item, file_name, name_prefix):
    item_type = cosmetic_types[file_name][LANG]
    formats = dict(cosmetic_source_formats)
    if file_name == "Stack_Sticker":
        formats.update(sticker_source_formats)
    description = match_description(
        item, formats, {**ticket_source_extras, **cosmetic_source_extras},
        itype=regex.escape(cosmetic_source_types[file_name][0]),
        intro=r"(?:(?P<owner>[^\r\n<>]+)愛用の赤いマフラー。\n)?" if file_name == "Stack_Accessory" else "")
    if description is None:
        description = match_description(
            item, ncosmetic_source_formats, {**ticket_source_extras, **ncosmetic_source_extras},
            itype="(?P<itype>" + "|".join(map(regex.escape, cosmetic_source_types[file_name][1:])) + ")")
        if description is None:
            return -4
        return translate_ncosmetic_desc(item, file_name, description)
    desc_sort, fields, source_extras = description
    if ("color" in source_extras and "ncolor" in source_extras
            or (item["jp_text"] == "ステッカーなし") != (desc_sort == "no_sticker")
            or desc_sort == "no_sticker" and source_extras):
        return -4
    if fields.get("owner") and item["jp_text"] != fields["owner"] + "マフラー":
        return -4

    item_name = get_item_name(item, name_prefix)
    problem = get_translation_problem(item, item_name)
    if problem:
        return problem
    if not item_type:
        return -5
    extras = get_ticket_extras(source_extras)
    if extras is None:
        return -5
    if desc_sort == "no_sticker":
        if not no_sticker_desc[LANG]:
            return -5
        return set_description(item, no_sticker_desc[LANG], normalize=False)

    if not cosmetic_desc_formats[desc_sort][LANG]:
        return -5

    if file_name == "Stack_Sticker" and fields["iname"] != item["jp_text"]:
        item_name = item_name.replace(" Sticker", "")
        item_name = item_name.replace("ステッカー", "")
        item_name = item_name.replace(" 스티커", "")

    intro = ""
    if fields.get("owner"):
        if not scarf_intro_formats[LANG]:
            return -5
        owner = fields["owner"]
        if item_name != item["jp_text"]:
            translated_name = regex.fullmatch(scarf_name_patterns[LANG], item_name)
            if translated_name is None:
                return -5
            owner = translated_name.group(1)
        intro = scarf_intro_formats[LANG].format(owner=owner)

    sex = {"男": "m", "女": "f"}.get(source_extras.get("sex", {}).get("sex"), "n")
    sizelocked = "size" in source_extras
    colorlocked = "color" in source_extras
    ncolorlocked = "ncolor" in source_extras
    if (sex != "n" and not cosmetic_sex_locks[sex][LANG]
            or sizelocked and not cosmetic_extras["size"][LANG]
            or colorlocked and not cosmetic_extras["color"][LANG]
            or ncolorlocked and not shared_extras["color"][LANG]):
        return -5

    body = intro + cosmetic_desc_formats[desc_sort][LANG].format(
        sexlock = cosmetic_sex_locks[sex][LANG] if sex != "n" else "",
        itype = item_type,
        iname = item_name,
    )
    description_extras = [
        cosmetic_extras["size"][LANG] if sizelocked == True else "",
        cosmetic_extras["color"][LANG] if colorlocked == True else "",
        shared_extras["color"][LANG] if ncolorlocked == True else ""
    ]
    return set_description(item, body + "".join(description_extras) + extras)

# [FUNCTION] Render matched NGS cosmetics, including account unlocks and motion restrictions.
def translate_ncosmetic_desc(item, file_name, description):
    desc_sort, fields, source_extras = description
    item_type = (cosmeticsorted_types["Headparts"][LANG] if fields["itype"] == "ヘッドパーツ"
                 else cosmetic_types[file_name][LANG])
    if "weapons" in source_extras and "ngs" in source_extras:
        return -4
    weapon_type = source_extras.get("weapons", {}).get("weapon")
    if weapon_type and weapon_type not in motion_weapon_types:
        return -4

    problem = get_translation_problem(item)
    if problem:
        return problem
    if not item_type:
        return -5
    extras = get_ticket_extras(source_extras)
    if extras is None:
        return -5
    if desc_sort == "allcharacters" and file_name in account_item_types:
        desc_sort = "account_item"

    types = get_type_restrictions(source_extras)
    hideinner = "hide_inner" in source_extras
    ngslockedweapon = "weapons" in source_extras
    ngslocked = "ngs" in source_extras
    weapon_note = motion_extras["weapons"][LANG]
    if weapon_type:
        translations = motion_weapon_types[weapon_type]
        if not translations[LANG] or not motion_extras["typed_weapons"][LANG]:
            return -5
        weapon_note = motion_extras["typed_weapons"][LANG].format(weapon_type=translations[LANG])
    ncolorlocked = "ncolor" in source_extras
    ngsfacelocked = "face" in source_extras
    if (not ndesc_formats[desc_sort][LANG]
            or types != "a" and (not shared_extras["type"][LANG] or not ntype_locks[types][LANG])
            or hideinner and not shared_extras["hide_inner"][LANG]
            or ngslockedweapon and not weapon_note
            or ngslocked and not shared_extras["ngs"][LANG]
            or ngsfacelocked and not cosmetic_extras["face"][LANG]
            or ncolorlocked and not shared_extras["color"][LANG]):
        return -5

    body = ndesc_formats[desc_sort][LANG].format(
        itype = item_type,
        a = get_korean_particle(item_type, "을", "를") if LANG == 1 else "" if fields["itype"] == "ヘッドパーツ" else "a ",
    )
    description_extras = [
        "" if types == "a" else shared_extras["type"][LANG].format(type=ntype_locks[types][LANG]),
        shared_extras["hide_inner"][LANG] if hideinner == True else "",
        weapon_note if ngslockedweapon == True else shared_extras["ngs"][LANG] if ngslocked == True else "",
        cosmetic_extras["face"][LANG] if ngsfacelocked == True else "",
        shared_extras["color"][LANG] if ncolorlocked else ""
    ]
    return set_description(item, body + "".join(description_extras) + extras)

# ——————————————————————————————
# BUILD-PART RULES & TRANSLATION
# ——————————————————————————————

build_parts_file_names = [
    "Stack_CS_Material_Ticket1",
    "Stack_CS_Material_Ticket2",
    "Stack_CS_Material_Ticket3"
    ]

# Exact JP keys and complete translated values share one table; no separate recognizer is needed.
# Each dictionary key is the complete Japanese build-part description.
build_part_formats = {
    # JP text: アクセスすると
    # 座れるビルドパーツ。
    "アクセスすると\n座れるビルドパーツ。": [
        ("This Build Part can be accessed\n"
         "to sit on it."),
        ("액세스하면\n"
         "앉을 수 있는 빌드 파츠."),
        (""),
        ("交互後\n"
         "即可坐下的建造部件。"),
        ("Build Part ที่สามารถกดใช้งานเพื่อนั่งลงได้"),
    ],
    # JP text: アクセスすると
    # 座れるビルドパーツだが……。
    "アクセスすると\n座れるビルドパーツだが……。": [
        ("This Build Part can be accessed\n"
         "to sit on it, but..."),
        ("액세스하면\n"
         "앉을 수 있는 빌드 파츠지만……."),
        (""),
        ("交互後\n"
         "即可坐下的建造部件，但……"),
        ("Build Part ที่สามารถกดใช้งานเพื่อนั่งลงได้ แต่ว่า..."),
    ],
    # JP text: アクセスすると
    # 横になれるビルドパーツ。
    "アクセスすると\n横になれるビルドパーツ。": [
        ("This Build Part can be accessed\n"
         "to lie down on it."),
        ("액세스하면\n"
         "누울 수 있는 빌드 파츠."),
        (""),
        ("交互後\n"
         "即可躺下的建造部件。"),
        ("Build Part ที่สามารถกดใช้งานเพื่อเอนกายนอนลงได้"),
    ],
    # JP text: アクセスすると
    # 入浴できるビルドパーツ。
    "アクセスすると\n入浴できるビルドパーツ。": [
        ("This Build Part can be accessed\n"
         "to take a bath."),
        ("액세스하면\n"
         "목욕할 수 있는 빌드 파츠."),
        (""),
        ("交互後\n"
         "即可入浴的建造部件。"),
        ("Build Part ที่สามารถกดใช้งานเพื่อลงแช่น้ําได้"),
    ],
    # JP text: アクセスすると
    # シャワーを浴びられるビルドパーツ。
    "アクセスすると\nシャワーを浴びられるビルドパーツ。": [
        ("This Build Part can be accessed\n"
         "to take a shower."),
        ("액세스하면\n"
         "샤워할 수 있는 빌드 파츠."),
        (""),
        ("交互後\n"
         "即可淋浴的建造部件。"),
        ("Build Part ที่สามารถกดใช้งานเพื่ออาบน้ําฝักบัวได้"),
    ],
    # JP text: アクセスすると
    # 開閉できるビルドパーツ。
    "アクセスすると\n開閉できるビルドパーツ。": [
        ("This Build Part can be accessed\n"
         "to open and close it."),
        ("액세스하면\n"
         "여닫을 수 있는 빌드 파츠."),
        (""),
        ("交互後\n"
         "即可開閉的建造部件。"),
        ("Build Part ที่สามารถกดใช้งานเพื่อเปิด-ปิดได้"),
    ],
    # JP text: 攻撃すると
    # 破壊できるビルドパーツ。
    "攻撃すると\n破壊できるビルドパーツ。": [
        ("This Build Part can be destroyed\n"
         "by attacking it."),
        ("공격하면\n"
         "파괴할 수 있는 빌드 파츠."),
        (""),
        ("攻擊後\n"
         "即可破壞的建造部件。"),
        ("Build Part ที่สามารถทําลายได้ด้วยการโจมตี"),
    ],
    # JP text: アクセスすると
    # 獲れるビルドパーツ。
    "アクセスすると\n獲れるビルドパーツ。": [
        ("This Build Part can be accessed\n"
         "to collect it."),
        ("액세스하면\n"
         "채집할 수 있는 빌드 파츠."),
        (""),
        ("交互後\n"
         "即可捕獲的建造部件。"),
        ("Build Part ที่สามารถกดใช้งานเพื่อจับ/เก็บได้"),
    ],
    # JP text: 触れると
    # 取れるビルドパーツ。
    "触れると\n取れるビルドパーツ。": [
        ("This Build Part can be collected by\n"
         "touching it."),
        ("닿으면\n"
         "획득할 수 있는 빌드 파츠."),
        (""),
        ("觸碰後\n"
         "即可拿取的建造部件。"),
        ("Build Part ที่สามารถเก็บได้เมื่อสัมผัส"),
    ],
    # JP text: アクセスすると
    # 設定したメッセージを表示する
    # ビルドパーツ。
    "アクセスすると\n設定したメッセージを表示する\nビルドパーツ。": [
        ("This Build Part can be accessed\n"
         "to read the message it contains."),
        ("액세스하면\n"
         "설정한 메시지를 표시하는\n"
         "빌드 파츠."),
        (""),
        ("交互後\n"
         "就會顯示設置好的訊息的\n"
         "建造部件。"),
        ("Build Part ที่สามารถกดใช้งานเพื่ออ่านข้อความที่บันทึกไว้ได้"),
    ],
    # JP text: アクセスすると
    # オンオフが切り替わる
    # ビルドパーツ。
    "アクセスすると\nオンオフが切り替わる\nビルドパーツ。": [
        ("This Build Part acts as a switch\n"
         "that toggles on/off when accessed."),
        ("액세스하면\n"
         "켜짐과 꺼짐이 전환되는\n"
         "빌드 파츠."),
        (""),
        ("交互後\n"
         "就會切換開關的建造部件。"),
        ("Build Part ที่ทํางานเป็นสวิตช์เปิด-ปิดเมื่อกดใช้งาน"),
    ],
    # JP text: 上に乗ると
    # スイッチがオンになる
    # ビルドパーツ。
    "上に乗ると\nスイッチがオンになる\nビルドパーツ。": [
        ("This Build Part acts as a switch\n"
         "that turns on when stepped on."),
        ("위에 올라서면\n"
         "스위치가 켜지는\n"
         "빌드 파츠."),
        (""),
        ("踩在上面後\n"
         "開關就會設為開的建造部件。"),
        ("Build Part ที่ทํางานเป็นสวิตช์เปิดเมื่อขึ้นไปเหยียบ"),
    ],
    # JP text: 触れると
    # 爆発して吹き飛ばされる
    # ビルドパーツ。
    "触れると\n爆発して吹き飛ばされる\nビルドパーツ。": [
        ("This Build Part explodes on contact,\n"
         "blasting players away."),
        ("닿으면\n"
         "폭발해 몸이 날아가는\n"
         "빌드 파츠."),
        (""),
        ("觸碰後\n"
         "就會爆炸把人炸飛的建造部件。"),
        ("Build Part ที่จะระเบิดและซัดผู้เล่นกระเด็นเมื่อสัมผัสโดน"),
    ],
    # JP text: フォトングライド中に
    # 乗ると移動できる
    # ビルドパーツ。
    "フォトングライド中に\n乗ると移動できる\nビルドパーツ。": [
        ("This Build Part lets you ascend by\n"
         "riding it while Photon Gliding."),
        ("포톤 글라이드 중에\n"
         "올라타면 이동할 수 있는\n"
         "빌드 파츠."),
        (""),
        ("在光子滑翔中乘上後\n"
         "即可進行移動的建造部件。"),
        (""),
    ],
    # JP text: アクセスすると
    # 対応する番号のテレポーターに
    # 移動できるビルドパーツ。
    "アクセスすると\n対応する番号のテレポーターに\n移動できるビルドパーツ。": [
        ("This Build Part can be accessed\n"
         "to teleport to another Teleporter\n"
         "with a matching ID."),
        ("액세스하면\n"
         "대응하는 번호의 텔레포터로\n"
         "이동할 수 있는 빌드 파츠."),
        (""),
        ("交互後\n"
         "即可移動到相應號碼傳送器的\n"
         "建造部件。"),
        ("Build Part ที่สามารถกดใช้งานเพื่อวาร์ปไปยังเทเลพอร์ตเตอร์ที่มีหมายเลขตรงกันได้"),
    ],
    # JP text: エリア内に接触すると
    # 次のギミックパーツに
    # コネクトを送信するビルドパーツ。
    "エリア内に接触すると\n次のギミックパーツに\nコネクトを送信するビルドパーツ。": [
        ("When this Build Part detects that a\n"
         "player has entered its assigned area,\n"
         "it sends a signal to its connected parts."),
        ("영역 내부에 접촉하면\n"
         "다음 기믹 파츠에\n"
         "커넥트를 전송하는 빌드 파츠."),
        (""),
        ("碰撞到區域內後\n"
         "就會向下一個機關部件\n"
         "發送智聯信號的建造部件。"),
        ("Build Part ที่จะส่งสัญญาณเชื่อมต่อเมื่อตรวจพบผู้เล่นเข้ามาสัมผัสในพื้นที่"),
    ],
    # JP text: コネクトを受信すると
    # タイマーのカウントアップを開始する
    # ビルドパーツ。
    "コネクトを受信すると\nタイマーのカウントアップを開始する\nビルドパーツ。": [
        ("When this Build Part receives a signal,\n"
         "it starts a timer that counts up from 0."),
        ("커넥트를 수신하면\n"
         "타이머의 카운트업을 시작하는\n"
         "빌드 파츠."),
        (""),
        ("接收智聯信號後\n"
         "就會開始計時器正數的建造部件。"),
        ("Build Part ที่จะเริ่มนับเวลาเดินหน้าจาก 0 เมื่อได้รับสัญญาณเชื่อมต่อ"),
    ],
    # JP text: コネクトを受信すると
    # タイマーのカウントダウンを開始する
    # ビルドパーツ。
    "コネクトを受信すると\nタイマーのカウントダウンを開始する\nビルドパーツ。": [
        ("When this Build Part receives a signal,\n"
         "it starts a timer that counts down to 0."),
        ("커넥트를 수신하면\n"
         "타이머의 카운트다운을 시작하는\n"
         "빌드 파츠."),
        (""),
        ("接收智聯信號後\n"
         "就會開始計時器倒數的建造部件。"),
        ("Build Part ที่จะเริ่มนับเวลาถอยหลังลงไปยัง 0 เมื่อได้รับสัญญาณเชื่อมต่อ"),
    ],
    # JP text: エリア内で指定したアクションを行うと
    # 次のギミックパーツに
    # コネクトを送信するビルドパーツ。
    "エリア内で指定したアクションを行うと\n次のギミックパーツに\nコネクトを送信するビルドパーツ。": [
        ("When this Build Part detects a specific\n"
         "player action within its assigned area,\n"
         "it sends a signal to its connected parts."),
        ("영역 안에서 지정한 액션을 수행하면\n"
         "다음 기믹 파츠에\n"
         "커넥트를 전송하는 빌드 파츠."),
        (""),
        ("在區域內執行指定動作後\n"
         "就會向下一個機關部件\n"
         "發送智聯信號的建造部件。"),
        ("Build Part ที่จะส่งสัญญาณเชื่อมต่อเมื่อตรวจพบการกระทําที่กําหนดในพื้นที่"),
    ],
    # JP text: コネクトを受信すると
    # 設定したテキスト演出を再生する
    # ビルドパーツ。
    "コネクトを受信すると\n設定したテキスト演出を再生する\nビルドパーツ。": [
        ("When this Build Part receives a signal,\n"
         "it displays a set text string."),
        ("커넥트를 수신하면\n"
         "설정한 텍스트 연출을 재생하는\n"
         "빌드 파츠."),
        (""),
        ("接收智聯信號後\n"
         "就會播放設置好的文字演出的\n"
         "建造部件。"),
        ("Build Part ที่จะแสดงข้อความตามที่ตั้งไว้เมื่อได้รับสัญญาณเชื่อมต่อ"),
    ],
    # JP text: コネクトを受信すると
    # 設定したサウンドを再生する
    # ビルドパーツ。
    "コネクトを受信すると\n設定したサウンドを再生する\nビルドパーツ。": [
        ("When this Build Part receives a signal,\n"
         "it plays a specified sound effect."),
        ("커넥트를 수신하면\n"
         "설정한 사운드를 재생하는\n"
         "빌드 파츠."),
        (""),
        ("接收智聯信號後\n"
         "就會播放設置好的聲音的\n"
         "建造部件。"),
        ("Build Part ที่จะเล่นเสียงเอฟเฟกต์ตามที่ตั้งไว้เมื่อได้รับสัญญาณเชื่อมต่อ (Connect)"),
    ],
    # JP text: 2つのコネクトを受信すると
    # 次のギミックパーツに
    # コネクトを送信するビルドパーツ。
    "2つのコネクトを受信すると\n次のギミックパーツに\nコネクトを送信するビルドパーツ。": [
        ("When this Build Part receives 2 signals,\n"
         "it sends a signal to its connected parts."),
        ("2개의 커넥트를 수신하면\n"
         "다음 기믹 파츠에\n"
         "커넥트를 전송하는 빌드 파츠."),
        (""),
        ("接收2個智聯信號後\n"
         "就會向下一個機關部件\n"
         "發送智聯信號的建造部件。"),
        ("Build Part ที่จะส่งสัญญาณเชื่อมต่อไปยังชิ้นส่วนถัดไปเมื่อได้รับสัญญาณครบทั้ง 2 ทาง (AND Cube)"),
    ],
    # JP text: コネクトを受信すると
    # カウントを1つ増やす
    # ビルドパーツ。
    "コネクトを受信すると\nカウントを1つ増やす\nビルドパーツ。": [
        ("When this Build Part receives a signal,\n"
         "it increases its internal counter by 1."),
        ("커넥트를 수신하면\n"
         "카운트를 1 증가시키는\n"
         "빌드 파츠."),
        (""),
        ("接收智聯信號後\n"
         "計數就會增加1的建造部件。"),
        ("Build Part ที่จะเพิ่มตัวนับขึ้น 1 ค่าเมื่อได้รับสัญญาณเชื่อมต่อ"),
    ],
    # JP text: コネクトを受信してから
    # 一定時間後に次のギミックパーツに
    # コネクトを送信するビルドパーツ。
    "コネクトを受信してから\n一定時間後に次のギミックパーツに\nコネクトを送信するビルドパーツ。": [
        ("When this Build Part receives a signal,\n"
         "it waits for a set amount of time, then\n"
         "sends a signal to its connected parts."),
        ("커넥트를 수신한 뒤\n"
         "일정 시간이 지나면 다음 기믹 파츠에\n"
         "커넥트를 송신하는 빌드 파츠."),
        (""),
        ("接收智聯信號一定時間後\n"
         "就會向下一個機關部件\n"
         "發送智聯信號的建造部件。"),
        ("Build Part ที่จะหน่วงเวลาตามที่กําหนดก่อนส่งสัญญาณเชื่อมต่อไปยังชิ้นส่วนถัดไป"),
    ],
    # JP text: コネクトを受信すると
    # 指定したギミックパーツのいずれかに
    # コネクトを送信するビルドパーツ。
    "コネクトを受信すると\n指定したギミックパーツのいずれかに\nコネクトを送信するビルドパーツ。": [
        ("When this Build Part receives a signal,\n"
         "it sends a signal on to one of its\n"
         "connected parts, chosen at random."),
        ("커넥트를 수신하면\n"
         "지정한 기믹 파츠 중 하나에\n"
         "커넥트를 송신하는 빌드 파츠."),
        (""),
        ("接收智聯信號後\n"
         "就會向任意的指定機關部件\n"
         "發送智聯信號的建造部件。"),
        ("Build Part ที่จะสุ่มส่งสัญญาณเชื่อมต่อไปยังชิ้นส่วนใดชิ้นส่วนหนึ่งเมื่อได้รับสัญญาณ"),
    ],
    # JP text: アクセスするとアークス拠点に
    # 移動できるビルドパーツ。
    # Ｃスペース内の初期位置にもなる。
    "アクセスするとアークス拠点に\n移動できるビルドパーツ。\nＣスペース内の初期位置にもなる。": [
        ("This Build Part can be accessed to\n"
         "return to the ARKS Base. It is also\n"
         "where you first arrive in C. Space."),
        ("액세스하면 아크스 거점으로\n"
         "이동할 수 있는 빌드 파츠.\n"
         "Ｃ스페이스 내의 초기 위치로도 사용된다."),
        (""),
        ("交互後即可移動到\n"
         "ARKS據點的建造部件。\n"
         "也會成為創造空間內的初始位置。"),
        ("Build Part ที่สามารถกดใช้งานเพื่อกลับสู่ฐาน ARKS ได้ และยังเป็นจุดเกิดเริ่มต้นใน Creative Space"),
    ],
    # JP text: アクセスすると
    # 自身のキャラクターを投影する
    # ビルドパーツ。
    "アクセスすると\n自身のキャラクターを投影する\nビルドパーツ。": [
        ("This Build Part can be accessed\n"
         "to display the image of a character."),
        ("액세스하면\n"
         "자신의 캐릭터를 투영하는\n"
         "빌드 파츠."),
        (""),
        ("交互後\n"
         "就會投影出自己角色的建造部件。"),
        ("Build Part ที่สามารถกดใช้งานเพื่อฉายภาพโฮโลแกรมของตัวละครตนเองได้"),
    ],
    # JP text: 上に乗っているあいだだけ
    # スイッチがオンになる
    # ビルドパーツ。
    "上に乗っているあいだだけ\nスイッチがオンになる\nビルドパーツ。": [
        ("This Build Part acts as a switch\n"
         "that turns on only while stood on."),
        ("위에 올라가 있는 동안에만\n"
         "스위치가 켜지는\n"
         "빌드 파츠."),
        (""),
        ("僅在踩在上面的時間裡\n"
         "開關會設為開的建造部件。"),
        ("Build Part ที่ทํางานเป็นสวิตช์เปิดเฉพาะในขณะที่มีคนเหยียบค้างอยู่เท่านั้น"),
    ],
    # JP text: アクセスすると
    # 設計図の登録、取得ができる
    # ビルドパーツ。
    "アクセスすると\n設計図の登録、取得ができる\nビルドパーツ。": [
        ("This Build Part can be accessed\n"
         "to create and download Blueprints."),
        ("액세스하면\n"
         "설계도를 등록하고 획득할 수 있는\n"
         "빌드 파츠."),
        (""),
        ("交互後\n"
         "即可登錄、獲取設計圖的建造部件。"),
        ("Build Part ที่สามารถกดใช้งานเพื่อบันทึกหรือดาวน์โหลดพิมพ์เขียว (Blueprint) ได้"),
    ],
    # JP text: アクセスすると
    # ジェネシスポイントが獲得できる
    # ビルドパーツ。
    "アクセスすると\nジェネシスポイントが獲得できる\nビルドパーツ。": [
        ("This Build Part can be accessed\n"
         "to obtain Genesis Points."),
        ("액세스하면\n"
         "제네시스 포인트를 획득할 수 있는\n"
         "빌드 파츠."),
        (""),
        ("交互後\n"
         "即可獲得創世點數的建造部件。"),
        ("Build Part ที่สามารถกดใช้งานเพื่อรับแต้มเจเนซิส (Genesis Points) ได้"),
    ],
    # JP text: くぐると
    # 加速するビルドパーツ。
    "くぐると\n加速するビルドパーツ。": [
        ("This Build Part makes you accelerate\n"
         "when you pass through it."),
        ("통과하면\n"
         "가속시켜 주는 빌드 파츠."),
        (""),
        ("穿過後\n"
         "就會加速的建造部件。"),
        ("Build Part ที่ช่วยเร่งความเร็วเมื่อลอดผ่าน"),
    ],
    # JP text: 触れると
    # 大きくジャンプするビルドパーツ。
    "触れると\n大きくジャンプするビルドパーツ。": [
        ("This Build Part launches you a great\n"
         "distance when you touch it."),
        ("닿으면\n"
         "크게 점프하게 되는 빌드 파츠."),
        (""),
        ("觸碰後\n"
         "就會大幅跳躍的建造部件。"),
        ("Build Part ที่จะดีดตัวกระโดดสูงเมื่อสัมผัสโดน"),
    ],
    # JP text: アクセスすると
    # Ｃスペースメニューを操作できる
    # ビルドパーツ。
    "アクセスすると\nＣスペースメニューを操作できる\nビルドパーツ。": [
        ("This Build Part can be accessed\n"
         "to open the Creative Space Menu."),
        ("액세스하면\n"
         "Ｃ스페이스 메뉴를 이용할 수 있는\n"
         "빌드 파츠."),
        (""),
        ("交互後\n"
         "即可操作創造空間菜單的\n"
         "建造部件。"),
        ("Build Part ที่สามารถกดใช้งานเพื่อเปิดเมนู Creative Space ได้"),
    ],
    # JP text: アクセスすると
    # チームコマンドを操作できる
    # ビルドパーツ。
    "アクセスすると\nチームコマンドを操作できる\nビルドパーツ。": [
        ("This Build Part can be accessed\n"
         "to open the Team Commands Menu."),
        ("액세스하면\n"
         "팀 커맨드를 사용할 수 있는\n"
         "빌드 파츠."),
        (""),
        ("交互後\n"
         "即可操作公會指令的\n"
         "建造部件。"),
        ("Build Part ที่สามารถกดใช้งานเพื่อเปิดคําสั่งทีม (Team Commands) ได้"),
    ],
    # JP text: アクセスすると
    # チーム掲示板を操作できる
    # ビルドパーツ。
    "アクセスすると\nチーム掲示板を操作できる\nビルドパーツ。": [
        ("This Build Part can be accessed\n"
         "to open the Team Bulletin Board."),
        ("액세스하면\n"
         "팀 게시판을 이용할 수 있는\n"
         "빌드 파츠."),
        (""),
        ("交互後\n"
         "即可操作公會佈告欄的\n"
         "建造部件。"),
        ("Build Part ที่สามารถกดใช้งานเพื่อเปิดบอร์ดข่าวสารทีม (Team Bulletin Board) ได้"),
    ],
    # JP text: アクセスすると
    # チームスペースメニューを操作できる
    # ビルドパーツ。
    "アクセスすると\nチームスペースメニューを操作できる\nビルドパーツ。": [
        ("This Build Part can be accessed\n"
         "to open the Team Space Menu."),
        ("액세스하면\n"
         "팀 스페이스 메뉴를 이용할 수 있는\n"
         "빌드 파츠."),
        (""),
        ("交互後\n"
         "即可操作公會空間菜單的\n"
         "建造部件。"),
        ("Build Part ที่สามารถกดใช้งานเพื่อเปิดเมนู Team Space ได้"),
    ],
    # JP text: アクセスしてジェネシスポイントを
    # 使用すると、ブーストを発生させられる
    # ビルドパーツ。
    "アクセスしてジェネシスポイントを\n使用すると、ブーストを発生させられる\nビルドパーツ。": [
        ("This Build Part can be accessed\n"
         "to spend Genesis Points to\n"
         "trigger various boost effects."),
        ("액세스하여 제네시스 포인트를\n"
         "사용하면 부스트를 발동할 수 있는\n"
         "빌드 파츠."),
        (""),
        ("交互並使用創世點數後\n"
         "即可發動各種增益的\n"
         "建造部件。"),
        ("Build Part ที่สามารถกดใช้งานเพื่อใช้แต้ม Genesis Points เปิดเอฟเฟกต์บูสต์ได้"),
    ],
    # JP text: アクセスすると
    # ラインストライクで
    # 対戦できるビルドパーツ。
    "アクセスすると\nラインストライクで\n対戦できるビルドパーツ。": [
        ("This Build Part can be accessed\n"
         "to engage in a Line Strike Duel."),
        ("액세스하면\n"
         "라인 스트라이크에서\n"
         "대전할 수 있는 빌드 파츠."),
        (""),
        ("交互後\n"
         "即可在戰線牌鬥中對戰的\n"
         "建造部件。"),
        ("Build Part ที่สามารถกดใช้งานเพื่อประลองการ์ด Line Strike ได้"),
    ],
    # JP text: アクセスすると
    # 対応する番号の転移門に
    # 移動できるビルドパーツ。
    "アクセスすると\n対応する番号の転移門に\n移動できるビルドパーツ。": [
        ("This Build Part can be accessed\n"
         "to teleport to another Transition\n"
         "Gate with a matching ID."),
        ("액세스하면\n"
         "대응하는 번호의 전이문으로\n"
         "이동할 수 있는 빌드 파츠."),
        (""),
        ("交互後\n"
         "即可移動到相應號碼傳送門的\n"
         "建造部件。"),
        ("Build Part ที่สามารถกดใช้งานเพื่อวาร์ปไปยังประตูมิติ (Transition Gate) ที่มีหมายเลขตรงกันได้"),
    ],
    # JP text: アクセスすると
    # 登録したクリエイティブスペースに
    # 移動できるビルドパーツ。
    "アクセスすると\n登録したクリエイティブスペースに\n移動できるビルドパーツ。": [
        ("This Build Part can be accessed\n"
         "to teleport to another specified\n"
         "Creative Space."),
        ("액세스하면\n"
         "등록한 크리에이티브 스페이스로\n"
         "이동할 수 있는 빌드 파츠."),
        (""),
        ("交互後\n"
         "即可移動到已登錄創造空間的\n"
         "建造部件。"),
        ("Build Part ที่สามารถกดใช้งานเพื่อวาร์ปไปยัง Creative Space ที่ลงทะเบียนไว้ได้"),
    ],
    # JP text: コネクトを受信すると
    # クレーンを操作できる
    # ビルドパーツ。
    "コネクトを受信すると\nクレーンを操作できる\nビルドパーツ。": [
        ("When this Build Part receives a signal,\n"
         "its crane arm moves around."),
        ("커넥트를 수신하면\n"
         "크레인을 조작할 수 있는\n"
         "빌드 파츠."),
        (""),
        ("接收智聯信號後\n"
         "即可操作勾爪的建造部件。"),
        (""),
    ],
    # JP text: 上から入ると
    # 泳げるビルドパーツ。
    "上から入ると\n泳げるビルドパーツ。": [
        ("This Build Part can be swum in\n"
         "if entered through its top face."),
        ("위에서 들어가면\n"
         "수영할 수 있는 빌드 파츠."),
        (""),
        ("從上方進入後\n"
         "即可游泳的建造部件。"),
        ("Build Part ที่สามารถลงไปว่ายน้ําได้เมื่อเข้าจากด้านบน"),
    ],
}

# [FUNCTION] Translate build parts by exact JP-description lookup, retaining the table text verbatim.
def translate_part_desc(item, file_name, name_prefix):
    # No description to translate
    if item["jp_explain"] == "":
        return -3

    translations = build_part_formats.get(item["jp_explain"])
    if translations is None:
        return -4

    problem = get_translation_problem(item)
    if problem:
        return problem

    if not translations[LANG]:
        return -5
    return set_description(item, translations[LANG], normalize=False)

# ——————————————————————————————
# LOBBY-ACTION RULES & TRANSLATION
# ——————————————————————————————

# JP feature blocks and body recognizers.

# JP feature blocks use the same codes as the la_extras table below.
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

la_source_formats = {
    "old": r"ロビアク『(?P<iname>[^』\r\n<>]+)』\nを全キャラクターで使用可能になる。",
    "new": r"使用すると新しいロビーアクションが\n全キャラクターで選択可能になる。",
    "hand": r"使用すると新しい手のポーズが\n全キャラクターで選択可能になる。",
}

# Translated bodies and the supported feature codes.

la_formats = {
    # JP text:
    # ロビアク『{iname}』\n
    # を全キャラクターで使用可能になる。
    "old": [
        ("Unlocks the new Lobby Action\n"
         "\"{iname}\"."),
        ("『{iname}』 로비 액션을\n"
         "모든 캐릭터가 사용할 수 있게 된다."),
        ("Разблокирует новый лобби-экшн:\n"
         "\"{iname}\"."),
        ("所有角色均可選用大廳動作\n"
         "『{iname}』。"),
        ("เมื่อใช้งาน จะสามารถเลือกใช้ Lobby Action ใหม่ \"{iname}\" ได้กับทุกตัวละครในไอดี"),
    ],
    # JP text:
    # 使用すると新しいロビーアクションが\n
    # 全キャラクターで選択可能になる。
    "new": [
        ("Unlocks a new Lobby Action for use by\n"
         "all characters on your account."),
        ("사용하면 새로운 로비 액션을\n"
         "모든 캐릭터에서 선택할 수 있게 된다."),
        ("Разблокирует новый лобби-экшн\n"
         "для всех персонажей вашего акка."),
        ("使用後所有角色均可選用新的大廳動作。"),
        ("เมื่อใช้งาน จะสามารถเลือกใช้ Lobby Action ใหม่ได้กับทุกตัวละครในไอดี"),
    ],
    # JP text:
    # 使用すると新しい手のポーズが\n
    # 全キャラクターで選択可能になる。
    "hand": [
        ("When used, allows you to select a\n"
         "new hand pose for all characters."),
        ("사용하면 새로운 손 모양을\n"
         "모든 캐릭터에서 선택할 수 있다."),
        ("Даёт возможность использовать\n"
         "версию с двигающимися пальцами."),
        ("使用後所有角色均可選用新的手部姿勢。"),
        ("เมื่อใช้งาน จะสามารถเลือกใช้ Hand Pose ใหม่ได้กับทุกตัวละครในไอดี"),
    ],
}

la_extras = {
    # JP text:
    # ※対応機能：ボタン派生/一部表示適用外\n
    # 対応服指可動/『PSO2』ブロック非対応
    "*actnopreviewfingersngs": [
        ("\n<yellow>※Extra actions (cannot preview).\n"
         "Finger motion by outfit. Not in [PSO2].<c>"),
        ("\n<yellow>※지원 기능: 버튼으로 동작 전환/일부 표시 적용 제외\n"
         "지원 의상 착용 시 손가락 움직임/『PSO2』 블록 미지원<c>"),
        ("\n<yellow>※Доп. действие (нет превью).\n"
         "Движ. пальцев огранич. Не в [PSO2].<c>"),
        ("\n<yellow>※適用功能：按鍵衍生/不適用一部分顯示\n"
         "適用服裝可動手指/不適用於『PSO2』<c>"),
        ("\n<yellow>※ฟังก์ชันที่รองรับ: กดปุ่มแยกท่า (ยกเว้นบางเอฟเฟกต์) / นิ้วขยับตามชุด / ไม่รองรับในบล็อก \"PSO2\"<c>"),
    ],
    # JP text:
    # ※対応機能：ボタン派生／\n
    # 対応服指可動／『PSO2』ブロック非対応
    "*actfingersngs": [
        ("\n<yellow>Has button actions/Finger motion\n"
         "outfit-limited/Can't use in [PSO2].<c>"),
        ("\n<yellow>※지원 기능: 버튼으로 동작 전환／\n"
         "지원 의상에서 손가락 가동／『PSO2』 블록 미지원<c>"),
        ("\n<yellow>Есть действия/Движен. пальцев\n"
         "огранич./Недоступно в [PSO2].<c>"),
        ("\n<yellow>※適用功能：按鍵衍生/\n"
         "適用服裝可動手指/不適用於『PSO2』<c>"),
        ("\n<yellow>※ฟังก์ชันที่รองรับ: กดปุ่มแยกท่า / นิ้วขยับตามชุด / ไม่รองรับในบล็อก \"PSO2\"<c>"),
    ],
    # JP text:
    # ※対応機能：ボタン派生／\n
    # 『PSO2』ブロック非対応
    "*actngs": [
        ("\n<yellow>Has button actions/\n"
         "Can't use in [PSO2].<c>"),
        ("\n<yellow>※지원 기능: 버튼으로 동작 전환／\n"
         "『PSO2』 블록 미지원<c>"),
        (""),
        ("\n<yellow>※適用功能：按鍵衍生/\n"
         "不適用於『PSO2』<c>"),
        ("\n<yellow>※ฟังก์ชันที่รองรับ: กดปุ่มแยกท่า / ไม่รองรับในบล็อก \"PSO2\"<c>"),
    ],
    # JP text:
    # ※対応機能：ボタン派生／ランダム／\n
    # 対応服指可動
    "*actrandomfingers": [
        ("\n<yellow>※Has button actions/randomness.\n"
         "Finger motion limited based on outfit.<c>"),
        ("\n<yellow>※지원 기능: 버튼으로 동작 전환/무작위/\n"
         "지원 의상 착용 시 손가락 움직임<c>"),
        ("\n<yellow>Есть кнопка действия/рандом.\n"
         "Одежда влияет на движ-е пальцев<c>"),
        ("\n<yellow>※適用功能：按鍵衍生/隨機動作/\n"
         "適用服裝可動手指<c>"),
        ("\n<yellow>※ฟังก์ชันที่รองรับ: กดปุ่มแยกท่า / ท่าทางแบบสุ่ม / นิ้วขยับตามชุด<c>"),
    ],
    # JP text:
    # ※対応機能：ボタン派生／\n
    # 対応服指可動
    "*actfingers": [
        ("\n<yellow>※Use action buttons for extra actions.\n"
         "Finger motion limited based on outfit.<c>"),
        ("\n<yellow>※지원 기능: 버튼으로 동작 전환/\n"
         "지원 의상 착용 시 손가락 움직임<c>"),
        ("\n<yellow>Доступно доп действие.\n"
         "Одежда влияет на движ-е пальцев<c>"),
        ("\n<yellow>※適用功能：按鍵衍生/\n"
         "適用服裝可動手指<c>"),
        ("\n<yellow>※ฟังก์ชันที่รองรับ: กดปุ่มแยกท่า / นิ้วขยับตามชุด<c>"),
    ],
    # JP text:
    # ※対応機能：リアクション／\n
    # 対応服指可動／『PSO2』ブロック非対応
    "*reactfingersngs": [
        ("\n<yellow>Has reactions/Finger motion\n"
         "outfit-limited/Can't use in [PSO2].<c>"),
        ("\n<yellow>※지원 기능: 리액션／\n"
         "지원 의상에서 손가락 가동／『PSO2』 블록 미지원<c>"),
        ("\n<yellow>С реакцией/Движ. пальц.\n"
         "огранич./Не для [PSO2].<c>"),
        ("\n<yellow>※適用功能：反應動作/\n"
         "適用服裝可動手指/不適用於『PSO2』<c>"),
        ("\n<yellow>※ฟังก์ชันที่รองรับ: มีรีแอ็กชันโต้ตอบ / นิ้วขยับตามชุด / ไม่รองรับในบล็อก \"PSO2\"<c>"),
    ],
    # JP text:
    # ※対応機能：対応服指可動／\n
    # 武器装備反映／『PSO2』ブロック非対応
    "*fingersweaponsngs": [
        ("\n<yellow>※Finger motion outfit limited. Shows\n"
         "equipment. Cannot perform in [PSO2].<c>"),
        ("\n<yellow>※지원 기능: 지원 의상에서 손가락 가동／\n"
         "장비한 무기 반영／『PSO2』 블록 미지원<c>"),
        ("\n<yellow>※Движ. завис-т от одежды| Отображ.\n"
         "экип. оружие| Только для NGS.<c>"),
        ("\n<yellow>※適用功能：適用服裝可動手指/\n"
         "顯示裝備武器/不適用於『PSO2』<c>"),
        ("\n<yellow>※ฟังก์ชันที่รองรับ: นิ้วขยับตามชุด / แสดงผลตามอาวุธที่สวมใส่ / ไม่รองรับในบล็อก \"PSO2\"<c>"),
    ],
    # JP text:
    # ※対応機能：対応服指可動／\n
    # 『PSO2』ブロック非対応
    "*fingersngs": [
        ("\n<yellow>※Finger motion limited based on outfit.\n"
         "Cannot perform in [PSO2] Blocks.<c>"),
        ("\n<yellow>※지원 기능: 지원 의상에서 손가락 가동／\n"
         "『PSO2』 블록 미지원<c>"),
        ("\n<yellow>※Одежда влияет на движ-е пальцев\n"
         "Нельзя использовать в блоке PSO2<c>"),
        ("\n<yellow>※適用功能：適用服裝可動手指/\n"
         "不適用於『PSO2』<c>"),
        ("\n<yellow>※ฟังก์ชันที่รองรับ: นิ้วขยับตามชุด / ไม่รองรับในบล็อก \"PSO2\"<c>"),
    ],
    # JP text:
    # ※対応機能：対応服指可動
    "*fingers": [
        ("\n<yellow>※Finger motion limited based on outfit.<c>"),
        ("\n<yellow>※지원 기능: 지원 의상 착용 시 손가락 움직임<c>"),
        ("\n<yellow>※Одежда влияет на движ-е пальцев<c>"),
        ("\n<yellow>※適用功能：適用服裝可動手指<c>"),
        ("\n<yellow>※ฟังก์ชันที่รองรับ: นิ้วขยับตามชุด<c>"),
    ],
    # JP text:
    # 対応機能：ボタン派生\n
    # <yellow>対象服のみ指も可動<c>
    "actfingers": [
        ("\n※Use action buttons for extra actions.\n"
         "Finger motion limited based on outfit."),
        ("\n지원 기능: 버튼으로 동작 전환\n"
         "<yellow>지원 의상에서만 손가락도 움직임<c>"),
        ("\nДоступно доп действие.\n"
         "Одежда влияет на движ-е пальцев"),
        ("\n適用功能：按鍵衍生\n"
         "<yellow>適用服裝可動手指<c>"),
        ("\n<yellow>※ฟังก์ชันที่รองรับ: กดปุ่มแยกท่า (นิ้วขยับเฉพาะชุดที่รองรับ)<c>"),
    ],
    # JP text:
    # 対応機能：ボタン派生／武器装備反映\n
    # <yellow>一部武器反映不可<c>
    "actweapons": [
        ("\nShows equipment, has extra actions.\n"
         "<yellow>Doesn't show some weapons.<c>"),
        ("\n지원 기능: 버튼으로 동작 전환/장비한 무기 반영\n"
         "<yellow>일부 무기는 반영되지 않음<c>"),
        ("\nОтображ. оружие; доп действие.\n"
         "<yellow>Не показывает некоторое оружие.<c>"),
        ("\n適用功能：按鍵衍生/顯示裝備武器\n"
         "<yellow>無法顯示一部分武器<c>"),
        ("\n<yellow>※ฟังก์ชันที่รองรับ: กดปุ่มแยกท่า / แสดงผลตามอาวุธที่สวมใส่ (ไม่รองรับบางอาวุธ)<c>"),
    ],
    # JP text:
    # 対応機能：ボタン派生／ランダム
    "actrandom": [
        ("\nHas button actions/randomness."),
        ("\n지원 기능: 버튼으로 동작 전환/무작위"),
        ("\nЕсть кнопка действия/рандом."),
        ("\n適用功能：按鍵衍生/隨機動作"),
        ("\n<yellow>※ฟังก์ชันที่รองรับ: กดปุ่มแยกท่า / ท่าทางแบบสุ่ม<c>"),
    ],
    # JP text:
    # 対応機能：ボタン派生
    "act": [
        ("\nUse action buttons for extra actions."),
        ("\n지원 기능: 버튼으로 동작 전환"),
        ("\nДоступно доп действие."),
        ("\n適用功能：按鍵衍生"),
        ("\n<yellow>※ฟังก์ชันที่รองรับ: กดปุ่มแยกท่า<c>"),
    ],
    # JP text:
    # 対応機能：武器装備反映\n
    # <yellow>一部武器反映不可<c>
    "weapons": [
        ("\nShows equipped weapons.\n"
         "<yellow>Doesn't show some weapons.<c>"),
        ("\n지원 기능: 장비한 무기 반영\n"
         "<yellow>일부 무기는 반영되지 않음<c>"),
        ("\nПоказывает экип-е оружие.\n"
         "<yellow>Не показывает некоторое оружие.<c>"),
        ("\n適用功能：顯示裝備武器\n"
         "<yellow>無法顯示一部分武器<c>"),
        ("\n<yellow>※ฟังก์ชันที่รองรับ: แสดงผลตามอาวุธที่สวมใส่ (ไม่รองรับบางอาวุธ)<c>"),
    ],
    # JP text:
    # 対応機能：リアクション
    "react": [
        ("\nReaction has extra actions."),
        ("\n지원 기능: 리액션"),
        ("\nЕсть доп действие реакцией."),
        ("\n適用功能：反應動作"),
        ("\n<yellow>※ฟังก์ชันที่รองรับ: มีรีแอ็กชันโต้ตอบ<c>"),
    ],
    # JP text:
    # <yellow>※一部ロビーアクション非対応／
    # 『PSO2』ブロック非対応<c>
    "hand": [
        ("\n<yellow>※Does not support all Lobby Actions.\n"
         "※Cannot perform in [PSO2] Blocks.<c>"),
        ("\n<yellow>※일부 로비 액션 미지원/\n"
         "『PSO2』 블록 미지원<c>"),
        ("\n<yellow>※Поддерж-т не все лобби-экшены.\n"
         "※Нельзя использовать в блоке PSO2<c>"),
        ("\n<yellow>※不適用於一部分大廳動作/\n"
         "不適用於『PSO2』<c>"),
        ("\n<yellow>※ไม่รองรับบาง Lobby Action / ไม่รองรับในบล็อก \"PSO2\"<c>"),
    ],
}

# Source recognizers use the translated note keys defined above.

la_source_extras = {
    code: "(?:" + "|".join(r"\n(?:<yellow>)?(?:※)?" + regex.escape("対応機能：" + text)
                          for text, key in extras_names.items() if key == code) + ")"
    for code in la_extras if code != "hand"
}

la_source_extras.update({
    "hand": r"\n" + source_note_pattern(r"※一部ロビーアクション非対応／\n『PSO2』ブロック非対応"),
    "ngs_locks": shared_source_extras["ngs"],
})

# [FUNCTION] Translate lobby actions and hand poses with their allowed feature notes.
def translate_la_desc(item, file_name, name_prefix):
    description = match_description(item, la_source_formats, la_source_extras)
    if description is None:
        return -4
    desc_sort, _, source_extras = description
    if (len(source_extras) > 1 or "hand" in source_extras and desc_sort != "hand"
            or desc_sort == "hand" and source_extras and "hand" not in source_extras):
        return -4

    item_name = get_item_name(item, name_prefix)
    problem = get_translation_problem(item, item_name)
    if problem:
        return problem

    extras = next(iter(source_extras), "n")
    if desc_sort == "hand":
        body = la_formats["hand"][LANG]
        extra = la_extras["hand"][LANG]
        if not body or source_extras and not extra:
            return -5
    else:
        extra = ""
        if extras != "n":
            extra = shared_extras["ngs"][LANG] if extras == "ngs_locks" else la_extras[extras][LANG]
            if not extra:
                return -5
        if not la_formats[desc_sort][LANG]:
            return -5
        if desc_sort == "old":
            # Photon Chairs have no number before their name.
            splits = regex.split('["「」]', item_name)
            body = la_formats["old"][LANG].format(iname=splits[1] if len(splits) > 1 else splits[0])
        else:
            body = la_formats["new"][LANG]
    return set_description(item, body + extra)

# ——————————————————————————————
# VOICE RULES & TRANSLATION
# ——————————————————————————————

# JP restriction terms map to the codes used by voice_restriction_extras.

voice_source_restrictions = {
    "人間男性のみ使用可能。": "hm", "人間女性のみ使用可能。": "hf",
    "キャスト男性のみ使用可能。": "cm", "キャスト女性のみ使用可能。": "cf",
    "男性のみ使用可能。": "am", "女性のみ使用可能。": "af",
}

voice_source_formats = {
    "voice": r"使用すると、新しいボイスが選択可能。(?:\n(?P<restriction>{restriction}))?\nＣＶ(?P<actor>[^\r\n<>]*)",
}


# JP text:
# ＣＶ
cv_title = ["CV: ", "CV: ", "CV: ", "CV：", "CV: "]

# JP text:
# 使用すると、新しいボイスが選択可能。
voice_desc_formats = [
    ("Allows a new voice to be selected."),
    ("사용하면 새로운 보이스를\n"
     "선택할 수 있다."),
    ("Позволяет выбрать новый голос."),
    ("使用後，可選用新的語音。"),
    ("เมื่อใช้งาน จะสามารถเลือก Voice ใหม่ได้"),
]

voice_restriction_extras = {
    # JP text:
    # 人間男性のみ使用可能。
    "hm": [
        ("\nNon-Cast male characters only."),
        ("\n인간 남성만 사용 가능."),
        ("\nТолько для М не CAST'ов."),
        ("\n僅限非機人男性使用。"),
        (""),
    ],
    # JP text:
    # 人間女性のみ使用可能。
    "hf": [
        ("\nNon-Cast female characters only."),
        ("\n인간 여성만 사용 가능."),
        ("\nТолько для Ж не CAST'ов."),
        ("\n僅限非機人女性使用。"),
        (""),
    ],
    # JP text:
    # キャスト男性のみ使用可能。
    "cm": [
        ("\nMale Casts only."),
        ("\n캐스트 남성만 사용 가능."),
        ("\nТолько для М CAST'ов."),
        ("\n僅限男性機人使用。"),
        (""),
    ],
    # JP text:
    # キャスト女性のみ使用可能。
    "cf": [
        ("\nFemale Casts only."),
        ("\n캐스트 여성만 사용 가능."),
        ("\nТолько для Ж CAST'ов."),
        ("\n僅限女性機人使用。"),
        (""),
    ],
    # JP text:
    # 男性のみ使用可能。
    "am": [
        ("\nMale characters only (all races)."),
        ("\n남성만 사용 가능."),
        ("\nТолько М персонажей (все расы)."),
        ("\n僅限男性使用。"),
        (""),
    ],
    # JP text:
    # 女性のみ使用可能。
    "af": [
        ("\nFemale characters only (all races)."),
        ("\n여성만 사용 가능."),
        ("\nТолько Ж персонажей (все расы)."),
        ("\n僅限女性使用。"),
        (""),
    ],
    # JP source has no race/sex restriction line; the existing language defaults are retained.
    # JP text: ""
    "an": [
        ("\nUsable by all characters."),
        ("\n모두 사용 가능."),
        ("\nДоступно всем персонажам."),
        (""),
        (""),
    ],
}

# Translated actor-name vocabulary and language fallbacks; looked up only at run time.

# Japanese actor names are the dictionary keys below.
cv_names = {
    # JP text: ゆかな
    "ゆかな": ["Yukana Nogami", "유카나", "Ногами Юкана", "尤加奈", "Yukana Nogami"],
    # JP text: チョー
    "チョー": ["Cho", "쵸", "Чо", "長", "Cho"],
    # JP text: ポポナ
    "ポポナ": ["Popona", "포포나", "Попона", "波波娜", "Popona"],
    # JP text: 下野 紘
    "下野 紘": ["Hiro Shimono", "시모노 히로", "Хиро Симоно", "下野 紘", "Hiro Shimono"],
    # JP text: 中原 麻衣
    "中原 麻衣": ["Mai Nakahara", "나카하라 마이", "Маи Накахара", "中原 麻衣", "Mai Nakahara"],
    # JP text: 中尾 隆聖
    "中尾 隆聖": ["Ryusei Nakao", "나카오 류세이", "Рюсэй Накао", "中尾 隆聖", "Ryusei Nakao"],
    # JP text: 中村 悠一
    "中村 悠一": ["Yuichi Nakamura", "나카무라 유이치", "Юичи Накамура", "中村 悠一", "Yuichi Nakamura"],
    # JP text: 中田 譲治
    "中田 譲治": ["Joji Nakata", "나카타 조지", "Дзёдзи Наката", "中田 讓治", "Joji Nakata"],
    # JP text: 中西 茂樹
    "中西 茂樹": ["Shigeki Nakanishi", "나카니시 시게키", "Сигэки Наканиши", "中西 茂樹", "Shigeki Nakanishi"],
    # JP text: 久野 美咲
    "久野 美咲": ["Misaki Kuno", "쿠노 미사키", "Мисаки Куно", "久野 美咲", "Misaki Kuno"],
    # JP text: 井上 和彦
    "井上 和彦": ["Kazuhiko Inoue", "이노우에 카즈히코", "Казухико Иноэ", "井上 和彥", "Kazuhiko Inoue"],
    # JP text: 井上 喜久子
    "井上 喜久子": ["Kikuko Inoue", "이노우에 키쿠코", "Кикуко Иноуэ", "井上 喜久子", "Kikuko Inoue"],
    # JP text: 井上 麻里奈
    "井上 麻里奈": ["Marina Inoue", "이노우에 마리나", "Марина Иноуэ", "井上 麻里奈", "Marina Inoue"],
    # JP text: 井口 裕香
    "井口 裕香": ["Yuka Iguchi", "이구치 유카", "Юка Игути", "井口 裕香", "Yuka Iguchi"],
    # JP text: 今井 麻美
    "今井 麻美": ["Asami Imai", "이마이 아사미", "Асами Имаи", "今井 麻美", "Asami Imai"],
    # JP text: 伊瀬 茉莉也
    "伊瀬 茉莉也": ["Mariya Ise", "이세 마리야", "Мария Исэ", "伊瀨 茉莉也", "Mariya Ise"],
    # JP text: 伊藤 静
    "伊藤 静": ["Shizuka Ito", "이토 시즈카", "Сидзука Ито", "伊藤 靜", "Shizuka Ito"],
    # JP text: 会 一太郎
    "会 一太郎": ["Ichitaro Ai", "아이 이치타로", "Ичитаро Ай", "會 一太郎", "Ichitaro Ai"],
    # JP text: 住友 優子
    "住友 優子": ["Yuko Sumitomo", "스미토모 유코", "Юко Сумитомо", "住友 優子", "Yuko Sumitomo"],
    # JP text: 佐倉 綾音
    "佐倉 綾音": ["Ayane Sakura", "사쿠라 아야네", "Аянэ Сакура", "佐倉 綾音", "Ayane Sakura"],
    # JP text: 佐武 宇綺
    "佐武 宇綺": ["Uki Satake", "사타케 우키", "Уки Сатакэ", "佐武 宇綺", "Uki Satake"],
    # JP text: 佐藤 利奈
    "佐藤 利奈": ["Rina Sato", "사토 리나", "Рина Сато", "佐藤 利奈", "Rina Sato"],
    # JP text: 佐藤 友啓
    "佐藤 友啓": ["Tomohiro Sato", "사토 토모히로", "Томохиро Сато", "佐藤 友啓", "Tomohiro Sato"],
    # JP text: 佐藤 聡美
    "佐藤 聡美": ["Satomi Sato", "사토 사토미", "Сатоми Сато", "佐藤 聰美", "Satomi Sato"],
    # JP text: 佳村 はるか
    "佳村 はるか": ["Haruka Yoshimura", "요시무라 하루카", "Харука Ёсимура", "佳村 遙", "Haruka Yoshimura"],
    # JP text: 保志 総一朗
    "保志 総一朗": ["Soichiro Hoshi", "호시 소이치로", "Соичиро Хоши", "保志 總一朗", "Soichiro Hoshi"],
    # JP text: 光吉 猛修
    "光吉 猛修": ["Takenobu Mitsuyoshi", "미츠요시 타케노부", "Такэнобу Мицуёши", "光吉 猛修", "Takenobu Mitsuyoshi"],
    # JP text: 内田 真礼
    "内田 真礼": ["Maaya Uchida", "우치다 마아야", "Маая Утида", "內田 真禮", "Maaya Uchida"],
    # JP text: 千本木 彩花
    "千本木 彩花": ["Sayaka Senbongi", "센본기 사야카", "Саяка Сэмбонги", "千本木 彩花", "Sayaka Senbongi"],
    # JP text: 古賀 葵
    "古賀 葵": ["Aoi Koga", "코가 아오이", "Аой Кога", "古賀 葵", "Aoi Koga"],
    # JP text: 吉野 裕行
    "吉野 裕行": ["Hiroyuki Yoshino", "요시노 히로유키", "Хироюки Ёшино", "吉野 裕行", "Hiroyuki Yoshino"],
    # JP text: 名塚 佳織
    "名塚 佳織": ["Kaori Nazuka", "나즈카 카오리", "Каори Надзука", "名塚 佳織", "Kaori Nazuka"],
    # JP text: 喜多村 英梨
    "喜多村 英梨": ["Eri Kitamura", "키타무라 에리", "Эри Китамура", "喜多村 英梨", "Eri Kitamura"],
    # JP text: 坂本 真綾
    "坂本 真綾": ["Maaya Sakamoto", "사카모토 마아야", "Маая Сакамото", "坂本 真綾", "Maaya Sakamoto"],
    # JP text: 堀川 りょう
    "堀川 りょう": ["Ryo Horikawa", "호리카와 료", "Рё Хорикава", "堀川 亮", "Ryo Horikawa"],
    # JP text: 堀江 由衣
    "堀江 由衣": ["Yui Horie", "호리에 유이", "Юи Хориэ", "堀江 由衣", "Yui Horie"],
    # JP text: 増田 俊樹
    "増田 俊樹": ["Toshiki Masuda", "마스다 토시키", "Тошики Масуда", "增田 俊樹", "Toshiki Masuda"],
    # JP text: 天野 名雪
    "天野 名雪": ["Nayuki Amano", "아마노 나유키", "Наюки Амано", "天野 名雪", "Nayuki Amano"],
    # JP text: 子安 武人
    "子安 武人": ["Takehito Koyasu", "코야스 타케히토", "Такэхито Коясу", "子安 武人", "Takehito Koyasu"],
    # JP text: 安元 洋貴
    "安元 洋貴": ["Hiroki Yasumoto", "야스모토 히로키", "Хироки Ясумото", "安元 洋貴", "Hiroki Yasumoto"],
    # JP text: 安済 知佳
    "安済 知佳": ["Chika Anzai", "안자이 치카", "Чика Андзаи", "安濟 知佳", "Chika Anzai"],
    # JP text: 寺島 拓篤
    "寺島 拓篤": ["Takuma Terashima", "테라시마 타쿠마", "Такума Тэрашима", "寺島 拓篤", "Takuma Terashima"],
    # JP text: 小倉 唯
    "小倉 唯": ["Yui Ogura", "오구라 유이", "Юй Огура", "小倉 唯", "Yui Ogura"],
    # JP text: 小原 莉子
    "小原 莉子": ["Riko Kohara", "코하라 리코", "Рико Кохара", "小原 莉子", "Riko Kohara"],
    # JP text: 小山 茉美
    "小山 茉美": ["Mami Koyama", "코야마 마미", "Мами Кояма", "小山 茉美", "Mami Koyama"],
    # JP text: 小松 未可子
    "小松 未可子": ["Mikako Komatsu", "코마츠 미카코", "Микако Комацу", "小松 未可子", "Mikako Komatsu"],
    # JP text: 小林 ゆう
    "小林 ゆう": ["Yu Kobayashi", "코바야시 유우", "Ю Кобаяши", "小林 優", "Yu Kobayashi"],
    # JP text: 小清水 亜美
    "小清水 亜美": ["Ami Koshimizu", "코시미즈 아미", "Ами Косимидзу", "小清水 亞美", "Ami Koshimizu"],
    # JP text: 小西 克幸
    "小西 克幸": ["Katsuyuki Konishi", "코니시 카츠유키", "Кацуюки Кониши", "小西 克幸", "Katsuyuki Konishi"],
    # JP text: 小野 大輔
    "小野 大輔": ["Daisuke Ono", "오노 다이스케", "Дайсукэ Оно", "小野 大輔", "Daisuke Ono"],
    # JP text: 小野坂 昌也
    "小野坂 昌也": ["Masaya Onosaka", "오노사카 마사야", "Масая Оносака", "小野坂 昌也", "Masaya Onosaka"],
    # JP text: 山岡 ゆり
    "山岡 ゆり": ["Yuri Yamaoka", "야마오카 유리", "Юри Ямаока", "山岡 百合", "Yuri Yamaoka"],
    # JP text: 岡本 信彦
    "岡本 信彦": ["Nobuhiko Okamoto", "오카모토 노부히코", "Нобухико Окамото", "岡本 信彥", "Nobuhiko Okamoto"],
    # JP text: 岩下 読男
    "岩下 読男": ["Moai Iwashita", "이와시타 토쿠오", "Моаи Ивасита", "岩下 讀男", "Moai Iwashita"],
    # JP text: 島本 須美
    "島本 須美": ["Sumi Shimamoto", "시마모토 스미", "Суми Симамото", "島本 須美", "Sumi Shimamoto"],
    # JP text: 島﨑 信長
    "島﨑 信長": ["Nobunaga Shimazaki", "시마자키 노부나가", "Нобунага Симадзаки", "島崎 信長", "Nobunaga Shimazaki"],
    # JP text: 川村 万梨阿
    "川村 万梨阿": ["Maria Kawamura", "카와무라 마리아", "Мария Кавамура", "川村 萬梨阿", "Maria Kawamura"],
    # JP text: 川澄 綾子
    "川澄 綾子": ["Ayako Kawasumi", "카와스미 아야코", "Аяко Кавасуми", "川澄 綾子", "Ayako Kawasumi"],
    # JP text: 市来 光弘
    "市来 光弘": ["Mitsuhiro Ichiki", "이치키 미츠히로", "Мицухиро Ичики", "市來 光弘", "Mitsuhiro Ichiki"],
    # JP text: 引坂 理絵
    "引坂 理絵": ["Rie Hikisaka", "히키사카 리에", "Рие Хирисака", "引坂 理繪", "Rie Hikisaka"],
    # JP text: 悠木 碧
    "悠木 碧": ["Aoi Yuki", "유우키 아오이", "Аои Юки", "悠木 碧", "Aoi Yuki"],
    # JP text: 戸松 遥
    "戸松 遥": ["Haruka Tomatsu", "토마츠 하루카", "Харука Томацу", "戶松 遙", "Haruka Tomatsu"],
    # JP text: 斉藤 壮馬
    "斉藤 壮馬": ["Soma Saito", "사이토 소마", "Сома Сайто", "齊藤 壯馬", "Soma Saito"],
    # JP text: 斉藤 朱夏
    "斉藤 朱夏": ["Shuka Saito", "사이토 슈카", "Шюка Саито", "齊藤 朱夏", "Shuka Saito"],
    # JP text: 斎藤 千和
    "斎藤 千和": ["Chiwa Saito", "사이토 치와", "Тива Сайто", "齋藤 千和", "Chiwa Saito"],
    # JP text: 新田 恵海
    "新田 恵海": ["Emi Nitta", "닛타 에미", "Эми Нитта", "新田 惠海", "Emi Nitta"],
    # JP text: 日笠 陽子
    "日笠 陽子": ["Yoko Hikasa", "히카사 요코", "Ёко Хикаса", "日笠 陽子", "Yoko Hikasa"],
    # JP text: 早見 沙織
    "早見 沙織": ["Saori Hayami", "하야미 사오리", "Саори Хаями", "早見 沙織", "Saori Hayami"],
    # JP text: 木村 珠莉
    "木村 珠莉": ["Juri Kimura", "키무라 쥬리", "Дзюри Кимура", "木村 珠莉", "Juri Kimura"],
    # JP text: 木村 良平
    "木村 良平": ["Ryohei Kimura", "키무라 료헤이", "Рёхэй Кимура", "木村 良平", "Ryohei Kimura"],
    # JP text: 本渡 楓
    "本渡 楓": ["Kaede Hondo", "혼도 카에데", "Каэдэ Хондо", "本渡 楓", "Kaede Hondo"],
    # JP text: 杉田 智和
    "杉田 智和": ["Tomokazu Sugita", "스기타 토모카즈", "Томокадзу Сугита", "杉田 智和", "Tomokazu Sugita"],
    # JP text: 村川 梨衣
    "村川 梨衣": ["Rie Murakawa", "무라카와 리에", "Риэ Муракава", "村川 梨衣", "Rie Murakawa"],
    # JP text: "東山 奈央 "
    "東山 奈央 ": ["Nao Toyama", "토야마 나오", "Нао Тояма", "東山 奈央", "Nao Toyama"],
    # JP text: 松岡 禎丞
    "松岡 禎丞": ["Yoshitsugu Matsuoka", "마츠오카 요시츠구", "Ёсицугу Мацуока", "松岡 禎丞", "Yoshitsugu Matsuoka"],
    # JP text: 柿原 徹也
    "柿原 徹也": ["Tetsuya Kakihara", "카키하라 테츠야", "Тэцуя Какихара", "柿原 徹也", "Tetsuya Kakihara"],
    # JP text: 桃井 はるこ
    "桃井 はるこ": ["Haruko Momoi", "모모이 하루코", "Харуко Момои", "桃井 晴子", "Haruko Momoi"],
    # JP text: 桑島 法子
    "桑島 法子": ["Houko Kuwashima", "쿠와시마 호코", "Хоко Кувасима", "桑島 法子", "Houko Kuwashima"],
    # JP text: 梶 裕貴
    "梶 裕貴": ["Yuki Kaji", "카지 유우키", "Юки Кадзи", "梶 裕貴", "Yuki Kaji"],
    # JP text: 森久保 祥太郎
    "森久保 祥太郎": ["Showtaro Morikubo", "모리쿠보 쇼타로", "Сётаро Морикубо", "森久保 祥太郎", "Showtaro Morikubo"],
    # JP text: 植田 佳奈
    "植田 佳奈": ["Kana Ueda", "우에다 카나", "Кана Уэда", "植田 佳奈", "Kana Ueda"],
    # JP text: 榊原 良子
    "榊原 良子": ["Yoshiko Sakakibara", "사카키바라 요시코", "Ёсико Сакакибара", "榊原 良子", "Yoshiko Sakakibara"],
    # JP text: 榎本 温子
    "榎本 温子": ["Atsuko Enomoto", "에노모토 아츠코", "Ацуко Эномото", "榎本 溫子", "Atsuko Enomoto"],
    # JP text: 横山 智佐
    "横山 智佐": ["Chisa Yokoyama", "요코야마 치사", "Тиса Ёкояма", "橫山 智佐", "Chisa Yokoyama"],
    # JP text: 橘田 いずみ
    "橘田 いずみ": ["Izumi Kitta", "킷타 이즈미", "Идзуми Китта", "橘田 泉", "Izumi Kitta"],
    # JP text: 櫻井 孝宏
    "櫻井 孝宏": ["Takahiro Sakurai", "사쿠라이 타카히로", "Такахиро Сакураи", "櫻井 孝宏", "Takahiro Sakurai"],
    # JP text: 水樹 奈々
    "水樹 奈々": ["Nana Mizuki", "미즈키 나나", "Нана Мидзуки", "水樹 奈奈", "Nana Mizuki"],
    # JP text: 水橋 かおり
    "水橋 かおり": ["Kaori Mizuhashi", "미즈하시 카오리", "Каори Мидзухаси", "水橋 香織", "Kaori Mizuhashi"],
    # JP text: 江口 拓也
    "江口 拓也": ["Takuya Eguchi", "에구치 타쿠야", "Такуя Эгучи", "江口 拓也", "Takuya Eguchi"],
    # JP text: 沢城 みゆき
    "沢城 みゆき": ["Miyuki Sawashiro", "사와시로 미유키", "Миюки Саваширо", "澤城 美雪", "Miyuki Sawashiro"],
    # JP text: 沼倉 愛美
    "沼倉 愛美": ["Manami Numakura", "누마쿠라 마나미", "Манами Нумакура", "沼倉 愛美", "Manami Numakura"],
    # JP text: 洲崎 綾
    "洲崎 綾": ["Aya Suzaki", "스자키 아야", "Ая Судзаки", "洲崎 綾", "Aya Suzaki"],
    # JP text: 清水 彩香
    "清水 彩香": ["Ayaka Shimizu", "시미즈 아야카", "Аяка Симидзу", "清水 彩香", "Ayaka Shimizu"],
    # JP text: 渡辺 久美子
    "渡辺 久美子": ["Kumiko Watanabe", "와타나베 쿠미코", "Кумико Ватанабэ", "渡邊 久美子", "Kumiko Watanabe"],
    # JP text: 潘 めぐみ
    "潘 めぐみ": ["Megumi Han", "한 메구미", "Мэгуми Хан", "潘 惠美", "Megumi Han"],
    # JP text: 瀬戸 麻沙美
    "瀬戸 麻沙美": ["Asami Seto", "세토 아사미", "Асами Сэто", "瀨戶 麻沙美", "Asami Seto"],
    # JP text: 玄田 哲章
    "玄田 哲章": ["Tessho Genda", "겐다 텟쇼", "Тэссё Гэнда", "玄田 哲章", "Tessho Genda"],
    # JP text: 生天目 仁美
    "生天目 仁美": ["Hitomi Nabatame", "나바타메 히토미", "Хитоми Набатамэ", "生天目 仁美", "Hitomi Nabatame"],
    # JP text: 田中 理恵
    "田中 理恵": ["Rie Tanaka", "타나카 리에", "Риэ Танака", "田中 理惠", "Rie Tanaka"],
    # JP text: 田村 ゆかり
    "田村 ゆかり": ["Yukari Tamura", "타무라 유카리", "Юкари Тамура", "田村 由香里", "Yukari Tamura"],
    # JP text: 田辺 留依
    "田辺 留依": ["Rui Tanabe", "타나베 루이", "Руи Танабэ", "田邊 留依", "Rui Tanabe"],
    # JP text: 甲斐田 裕子
    "甲斐田 裕子": ["Yuko Kaida", "카이다 유코", "Юко Каида", "甲斐田 裕子", "Yuko Kaida"],
    # JP text: 白石 涼子
    "白石 涼子": ["Ryoko Shiraishi", "시라이시 료코", "Рёко Сираиси", "白石 涼子", "Ryoko Shiraishi"],
    # JP text: 白鳥 哲
    "白鳥 哲": ["Tetsu Shiratori", "시라토리 테츠", "Тэцу Сиратори", "白鳥 哲", "Tetsu Shiratori"],
    # JP text: 皆口 裕子
    "皆口 裕子": ["Yuko Minaguchi", "미나구치 유코", "Юко Минагучи", "皆口 裕子", "Yuko Minaguchi"],
    # JP text: 矢島 晶子
    "矢島 晶子": ["Akiko Yajima", "야지마 아키코", "Юко Минагучи", "矢島 晶子", "Akiko Yajima"],
    # JP text: 石田 彰
    "石田 彰": ["Akira Ishida", "이시다 아키라", "Акира Исида", "石田 彰", "Akira Ishida"],
    # JP text: 神原 大地
    "神原 大地": ["Daichi Kanbara", "칸바라 다이치", "Даичи Камбара", "神原 大地", "Daichi Kanbara"],
    # JP text: 神谷 浩史
    "神谷 浩史": ["Hiroshi Kamiya", "카미야 히로시", "Хироши Камия", "神谷 浩史", "Hiroshi Kamiya"],
    # JP text: 福山 潤
    "福山 潤": ["Jun Fukuyama", "후쿠야마 쥰", "Дзюн Фукуяма", "福山 潤", "Jun Fukuyama"],
    # JP text: 秋元 羊介
    "秋元 羊介": ["Yosuke Akimoto", "아키모토 요스케", "Ёсукэ Акимото", "秋元 羊介", "Yosuke Akimoto"],
    # JP text: 秦 佐和子
    "秦 佐和子": ["Sawako Hata", "하타 사와코", "Савако Хата", "秦 佐和子", "Sawako Hata"],
    # JP text: 種田 梨沙
    "種田 梨沙": ["Risa Taneda", "타네다 리사", "Риса Танеда", "種田 梨沙", "Risa Taneda"],
    # JP text: 立木 文彦
    "立木 文彦": ["Fumihiko Tachiki", "타치키 후미히코", "Фумихико Тачики", "立木 文彥", "Fumihiko Tachiki"],
    # JP text: 立花 理香
    "立花 理香": ["Rika Tachibana", "타치바나 리카", "Рика Тачибана", "立花 理香", "Rika Tachibana"],
    # JP text: 竹達 彩奈
    "竹達 彩奈": ["Ayana Taketatsu", "타케타츠 아야나", "Аяна Такэтацу", "竹達 彩奈", "Ayana Taketatsu"],
    # JP text: 細谷 佳正
    "細谷 佳正": ["Yoshimasa Hosoya", "호소야 요시마사", "Ёшимаса Хосоя", "細谷 佳正", "Yoshimasa Hosoya"],
    # JP text: 紲星 あかり
    "紲星 あかり": ["Kizuna Akari", "키즈나 아카리", "Кизуна Акари", "紲星 燈", "Kizuna Akari"],
    # JP text: 結月 ゆかり
    "結月 ゆかり": ["Yuzuki Yukari", "유즈키 유카리", "Юзуки Акари", "結月 緣", "Yuzuki Yukari"],
    # JP text: 緑川 光
    "緑川 光": ["Hikaru Midorikawa", "미도리카와 히카루", "Хикару Мидорикава", "綠川 光", "Hikaru Midorikawa"],
    # JP text: 緒方 恵美
    "緒方 恵美": ["Megumi Ogata", "오가타 메구미", "Мэгуми Огата", "緒方 惠美", "Megumi Ogata"],
    # JP text: 能登 麻美子
    "能登 麻美子": ["Mamiko Noto", "노토 마미코", "Мамико Ното", "能登 麻美子", "Mamiko Noto"],
    # JP text: 花江 夏樹
    "花江 夏樹": ["Natsuki Hanae", "하나에 나츠키", "Нацуки Ханаэ", "花江 夏樹", "Natsuki Hanae"],
    # JP text: 花澤 香菜
    "花澤 香菜": ["Kana Hanazawa", "하나자와 카나", "Кана Ханадзава", "花澤 香菜", "Kana Hanazawa"],
    # JP text: 若本 規夫
    "若本 規夫": ["Norio Wakamoto", "와카모토 노리오", "Норио Вакамото", "若本 規夫", "Norio Wakamoto"],
    # JP text: 茅野 愛衣
    "茅野 愛衣": ["Ai Kayano", "카야노 아이", "Аи Каяно", "茅野 愛衣", "Ai Kayano"],
    # JP text: 草尾 毅
    "草尾 毅": ["Takeshi Kusao", "쿠사오 타케시", "Такэши Кусао", "草尾 毅", "Takeshi Kusao"],
    # JP text: 菊地 美香
    "菊地 美香": ["Mika Kikuchi", "키쿠치 미카", "Мика Кикучи", "菊地 美香", "Mika Kikuchi"],
    # JP text: 蒼井 翔太
    "蒼井 翔太": ["Shouta Aoi", "아오이 쇼타", "Сёта Аои", "蒼井 翔太", "Shouta Aoi"],
    # JP text: 藤本 結衣
    "藤本 結衣": ["Yui Fujimoto", "후지모토 유이", "Юи Фудзимото", "藤本 結衣", "Yui Fujimoto"],
    # JP text: 藤田 曜子
    "藤田 曜子": ["Yoko Fujita", "후지타 요코", "Ёко Фудзита", "藤田 曜子", "Yoko Fujita"],
    # JP text: 藤田 茜
    "藤田 茜": ["Akane Fujita", "후지타 아카네", "Аканэ Фудзита", "藤田 茜", "Akane Fujita"],
    # JP text: 諏訪 彩花
    "諏訪 彩花": ["Ayaka Suwa", "스와 아야카", "Аяка Сува", "諏訪 彩花", "Ayaka Suwa"],
    # JP text: 諏訪部 順一
    "諏訪部 順一": ["Junichi Suwabe", "스와베 쥰이치", "Дзюнъичи Сувабэ", "諏訪部 順一", "Junichi Suwabe"],
    # JP text: 豊口 めぐみ
    "豊口 めぐみ": ["Megumi Toyoguchi", "토요구치 메구미", "Мэгуми Тоёгучи", "豐口 惠", "Megumi Toyoguchi"],
    # JP text: 豊崎 愛生
    "豊崎 愛生": ["Aki Toyosaki", "토요사키 아키", "Аки Тоёсаки", "豐崎 愛生", "Aki Toyosaki"],
    # JP text: 近藤 佳奈子
    "近藤 佳奈子": ["Kanako Kondo", "콘도 카나코", "Канако Кондо", "近藤 佳奈子", "Kanako Kondo"],
    # JP text: 速水 奨
    "速水 奨": ["Sho Hayami", "하야미 쇼", "Сё Хаями", "速水 獎", "Sho Hayami"],
    # JP text: 那須 晃行
    "那須 晃行": ["Akiyuki Nasu", "나스 아키유키", "Акаюки Насу", "那須 晃行", "Akiyuki Nasu"],
    # JP text: 金元 寿子
    "金元 寿子": ["Hisako Kanemoto", "카네모토 히사코", "Хисако Канэмото", "金元 壽子", "Hisako Kanemoto"],
    # JP text: 金田 アキ
    "金田 アキ": ["Aki Kanada", "카나다 아키", "Аки Канада", "金田 晶", "Aki Kanada"],
    # JP text: 釘宮 理恵
    "釘宮 理恵": ["Rie Kugimiya", "쿠기미야 리에", "Риэ Кугимия", "釘宮 理惠", "Rie Kugimiya"],
    # JP text: 鈴村 健一
    "鈴村 健一": ["Kenichi Suzumura", "스즈무라 켄이치", "Кэнъити Судзумура", "鈴村 健一", "Kenichi Suzumura"],
    # JP text: 銀河 万丈
    "銀河 万丈": ["Banjo Ginga", "긴가 반죠", "Бандзё Гинга", "銀河 萬丈", "Banjo Ginga"],
    # JP text: 長谷川 唯
    "長谷川 唯": ["Yui Hasegawa", "하세가와 유이", "Юи Хасэгава", "長谷川 唯", "Yui Hasegawa"],
    # JP text: 門脇 舞以
    "門脇 舞以": ["Mai Kadowaki", "카도와키 마이", "Маи Кадоваки", "門脇 舞以", "Mai Kadowaki"],
    # JP text: 関 智一
    "関 智一": ["Tomokazu Seki", "세키 토모카즈", "Томокадзу Сэки", "關 智一", "Tomokazu Seki"],
    # JP text: 阿澄 佳奈
    "阿澄 佳奈": ["Kana Asumi", "아스미 카나", "Кана Асуми", "阿澄 佳奈", "Kana Asumi"],
    # JP text: 陶山 章央
    "陶山 章央": ["Akio Suyama", "스야마 아키오", "Акио Суяма", "陶山 章央", "Akio Suyama"],
    # JP text: 雨宮 天
    "雨宮 天": ["Sora Amamiya", "아마미야 소라", "Сора Амамия", "雨宮 天", "Sora Amamiya"],
    # JP text: 飛田 展男
    "飛田 展男": ["Nobuo Tobita", "토비타 노부오", "Нобуо Тобита", "飛田 展男", "Nobuo Tobita"],
    # JP text: 飯田 友子
    "飯田 友子": ["Yuko Iida", "이이다 유우코", "Юко Иида", "飯田 友子", "Yuko Iida"],
    # JP text: 高木 友梨香
    "高木 友梨香": ["Yurika Takagi", "타카기 유리카", "Юрика Такаги", "高木 友梨香", "Yurika Takagi"],
    # JP text: 高橋 未奈美
    "高橋 未奈美": ["Minami Takahashi", "타카하시 미나미", "Минами Такахаши", "高橋 未奈美", "Minami Takahashi"],
    # JP text: 高橋 李依
    "高橋 李依": ["Rie Takahashi", "타카하시 리에", "Риэ Такахаши", "高橋 李依", "Rie Takahashi"],
    # JP text: 高野 麻里佳
    "高野 麻里佳": ["Marika Kono", "코우노 마리카", "Марика Коно", "高野 麻里佳", "Marika Kono"],
    # JP text: 黒沢 ともよ
    "黒沢 ともよ": ["Tomoyo Kurosawa", "쿠로사와 토모요", "Томоё Куросава", "黑澤 朋世", "Tomoyo Kurosawa"],
    # JP text: こおろぎさとみ
    "こおろぎさとみ": ["Satomi Korogi", "코오로기 사토미", "Сатоми Короги", "興梠 里美", "Satomi Korogi"],
    # JP text: 三宅 健太
    "三宅 健太": ["Kenta Miyake", "미야케 켄타", "Кэнта Миякэ", "三宅 健太", "Kenta Miyake"],
    # JP text: 諸星 すみれ
    "諸星 すみれ": ["Sumire Morohoshi", "모로호시 스미레", "Сумирэ Морохоси", "諸星 堇", "Sumire Morohoshi"],
    # JP text: 宮本 侑芽
    "宮本 侑芽": ["Yume Miyamoto", "미야모토 유메", "Юмэ Миямото", "宮本 侑芽", "Yume Miyamoto"],
    # JP text: 川島 得愛
    "川島 得愛": ["Tokuyoshi Kawashima", "카와시마 토쿠요시", "Токуёси Кавасима", "川島 得愛", "Tokuyoshi Kawashima"],
    # JP text: 田所 あずさ
    "田所 あずさ": ["Azusa Tadokoro", "타도코로 아즈사", "Адзуса Тадокоро", "田所 梓", "Azusa Tadokoro"],
    # JP text: 森田 順平
    "森田 順平": ["Junpei Morita", "모리타 쥰페이", "Дзюмпэи Морита", "森田 順平", "Junpei Morita"],
    # No existing KO translation; retain the established JP-name fallback.
    # JP text: 上田 麗奈
    "上田 麗奈": ["Reina Ueda", "", "Уэда Рэйна", "上田 麗奈", "Reina Ueda"],
    # JP text: 入野 自由
    "入野 自由": ["Miyu Irino", "이리노 미유", "Ирино Мию", "入野 自由", "Miyu Irino"],
    # JP text: 梅原 裕一郎
    "梅原 裕一郎": ["Yuichiro Umehara", "우메하라 유이치로", "Умэхара Юитиро", "梅原 裕一郎", "Yuichiro Umehara"],
    # JP text: 逢坂 良太
    "逢坂 良太": ["Ryota Osaka", "오오사카 료타", "Осака Рёта", "逢坂 良太", "Ryota Osaka"],
    # JP text: 小原 好美
    "小原 好美": ["Konomi Kohara", "코하라 코노미", "Кохара Кономи", "小原 好美", "Konomi Kohara"],
    # JP text: 白上 フブキ
    "白上 フブキ": ["Shirakami Fubuki", "시라카미 후부키", "Шираками Фубуки", "白上 吹雪", "Shirakami Fubuki"],
    # JP text: 影山 シエン
    "影山 シエン": ["Kageyama Shien", "카게야마 시엔", "Шиэн Кагеяма", "影山 紫炎", "Kageyama Shien"],
    # JP text: 一 伊那尓栖
    "一 伊那尓栖": ["Ninomae Ina'nis", "니노마에 이나니스", "Ина'нис Ниномае", "一 伊那爾棲", "Ninomae Ina'nis"],
    # JP text: 日野 聡
    "日野 聡": ["Satoshi Hino", "히노 사토시", "Хино Сатоси", "日野 聰", "Satoshi Hino"],
    # JP text: 原 由実
    "原 由実": ["Yumi Hara", "하라 유미", "Хара Юми", "原 由實", "Yumi Hara"],
    # JP text: 闇ノ シュウ
    "闇ノ シュウ": ["Shu Yamino", "야미노 슈", "Ямино Сю", "Shu Yamino", "Shu Yamino"],
    # JP text: 星川 サラ
    "星川 サラ": ["Hoshikawa Sara", "호시카와 사라", "Сара Хошикава", "星川 莎拉", "Hoshikawa Sara"],
    # JP text: 葉加瀬 冬雪
    "葉加瀬 冬雪": ["Hakase Fuyuki", "하카세 후유키", "Фуюки Хакасе", "葉加瀨 冬雪", "Hakase Fuyuki"],
    # JP text: 甲斐田 晴
    "甲斐田 晴": ["Haru Kaida", "카이다 하루", "Каида Хару", "甲斐田 晴", "Haru Kaida"],
    # JP text: 津田 健次郎
    "津田 健次郎": ["Kenjiro Tsuda", "츠다 켄지로", "Цуда Кенджо", "津田 健次郎", "Kenjiro Tsuda"],
    # JP text: 鬼頭 明里
    "鬼頭 明里": ["Akari Kito", "키토 아카리", "Кито Акари", "鬼頭 明里", "Akari Kito"],
    # JP text: Ｍ・Ａ・Ｏ
    "Ｍ・Ａ・Ｏ": ["M・A・O", "M・A・O", "M・A・O", "M·A·O", "M・A・O"],
    # JP text: 山口 勝平
    "山口 勝平": ["Kappei Yamaguchi", "야마구치 캇페이", "Каппэй Ямагути", "山口 勝平", "Kappei Yamaguchi"],
    # JP text: 楠 大典
    "楠 大典": ["Taiten Kusunoki", "쿠스노키 타이텐", "Таитэн Кусуноки", "楠 大典", "Taiten Kusunoki"],
    # JP text: 小澤 亜李
    "小澤 亜李": ["Ari Ozawa", "오자와 아리", "Ари Одзава", "小澤 亞李", "Ari Ozawa"],
    # JP text: 天宮 こころ
    "天宮 こころ": ["Amamiya Kokoro", "아마미야 코코로", "", "天宮 心", "Amamiya Kokoro"],
    # JP text: 長尾 景
    "長尾 景": ["Nagao Kei", "나가오 케이", "", "長尾 景", "Nagao Kei"],
    # JP text: 魔使 マオ
    "魔使 マオ": ["Matsukai Mao", "마츠카이 마오", "", "魔使 真央", "Matsukai Mao"],
    # JP text: 夜見 れな
    "夜見 れな": ["Yorumi Rena", "요루미 레나", "", "夜見 蕾娜", "Yorumi Rena"],
    # JP text: 石見 舞菜香
    "石見 舞菜香": ["Manaka Iwami", "이와미 마나카", "", "石見 舞菜香", "Manaka Iwami"],
    # JP text: 山下 誠一郎
    "山下 誠一郎": ["Seiichiro Yamashita", "야마시타 세이이치로", "", "山下 誠一郎", "Seiichiro Yamashita"],
    # JP text: 水瀬 いのり
    "水瀬 いのり": ["Inori Minase", "미나세 이노리", "", "水瀨 祈", "Inori Minase"],
    # JP text: 内田 雄馬
    "内田 雄馬": ["Yuma Uchida", "우치다 유우마", "", "內田 雄馬", "Yuma Uchida"],
    # JP text: 和氣 あず未
    "和氣 あず未": ["Azumi Waki", "와키 아즈미", "", "和氣 杏未", "Azumi Waki"],
    # JP text: 小市 眞琴
    "小市 眞琴": ["Makoto Koichi", "코이치 마코토", "", "小市 真琴", "Makoto Koichi"],
    # JP text: 福西 勝也
    "福西 勝也": ["Masaya Fukunishi", "후쿠니시 마사야", "", "福西 勝也", "Masaya Fukunishi"],
    # JP text: 加藤 渉
    "加藤 渉": ["Wataru Kato", "카토 와타루", "", "加藤 涉", "Wataru Kato"],
    # JP text: 河西 健吾
    "河西 健吾": ["Kengo Kawanishi", "카와니시 켄고", "", "河西 健吾", "Kengo Kawanishi"],
    # JP text: 福原 綾香
    "福原 綾香": ["Ayaka Fukuhara", "후쿠하라 아야카", "", "福原 綾香", "Ayaka Fukuhara"],
    # JP text: ファイルーズ あい
    "ファイルーズ あい": ["Ai Fairouz", "파이루즈 아이", "", "菲魯茲·藍", "Fairouz Ai"],
    # JP text: 種﨑 敦美
    "種﨑 敦美": ["Atsumi Tanezaki", "타네자키 아츠미", "", "種崎 敦美", "Atsumi Tanezaki"],
    # JP text: 市ノ瀬 加那
    "市ノ瀬 加那": ["Kana Ichinose", "이치노세 카나", "", "市之瀨 加那", "Kana Ichinose"],
    # JP text: 小林 千晃
    "小林 千晃": ["Chiaki Kobayashi", "코바야시 치아키", "", "小林 千晃", "Chiaki Kobayashi"],
    # JP text: 阿部 敦
    "阿部 敦": ["Atsushi Abe", "아베 아츠시", "", "阿部 敦", "Atsushi Abe"],
    # JP text: ささき のぞみ
    "ささき のぞみ": ["Nozomi Sasaki", "사사키 노조미", "", "佐佐木 望", "Nozomi Sasaki"],
    # JP text: でびでび・でびる
    "でびでび・でびる": ["Debidebi Debiru", "데비데비 데비루", "", "德比德比·德比魯", "Debidebi Debiru"],
    # JP text: アルス・アルマル
    "アルス・アルマル": ["Ars Almal", "아르스 아르말", "", "阿露絲·阿爾瑪", "Ars Almal"],
    # JP text: ニュイ・ソシエール
    "ニュイ・ソシエール": ["Nui Sociere", "뉴이 소시에르", "", "紐伊·索西艾瑞", "Nui Sociere"],
    # JP text: 竜胆 尊
    "竜胆 尊": ["Mikoto Rindou", "린도 미코토", "", "龍膽 尊", "Mikoto Rindou"],
    # JP text: 岡咲 美保
    "岡咲 美保": ["Miho Okasaki", "오카사키 미호", "", "岡咲 美保", "Miho Okasaki"],
    # JP text: 日高 里菜
    "日高 里菜": ["Rina Hidaka", "히다카 리나", "", "日高 里菜", "Rina Hidaka"],
    # JP text: 永瀬 アンナ
    "永瀬 アンナ": ["Anna Nagase", "나가세 안나", "", "永瀨 安奈", "Anna Nagase"],
    # JP text: 五十嵐 梨花
    "五十嵐 梨花": ["Rika Igarashi", "이가라시 리카", "", "五十嵐 梨花", "Rika Igarashi"],
    # JP text: 倉持 めると
    "倉持 めると": ["Meruto Kuramochi", "쿠라모치 메루토", "", "倉持 妹路特", "Meruto Kuramochi"],
    # JP text: ソフィア・ヴァレンタイン
    "ソフィア・ヴァレンタイン": ["Sophia Valentine", "소피아 발렌타인", "", "蘇菲婭·瓦綸玎", "Sophia Valentine"],
    # JP text: 狂蘭 メロコ
    "狂蘭 メロコ": ["Meloco Kyoran", "쿄란 메로코", "", "Meloco Kyoran", "Meloco Kyoran"],
    # JP text: 伊藤 ゆいな
    "伊藤 ゆいな": ["Yuina Ito", "이토 유이나", "", "伊藤 結衣奈", "Yuina Ito"],
    # JP text: 花守 ゆみり
    "花守 ゆみり": ["Yumiri Hanamori", "하나모리 유미리", "", "花守 由美里", "Yumiri Hanamori"],
    # JP text: ？？？
    "？？？": ["???", "???", "???", "？？？", "???"],
    # JP text: ""
    "": ["Unknown", "알 수 없는", "Неизвестно", "", ""],
}

# What to fall back to if a name hasn't been translated into your language.
# -1: Prefer falling back to JP over any other language
name_fallbacks = {0: -1,
                  1: -1,
                  2: 0,
                  3: -1,
                  4: -1}

# [FUNCTION] Translate voices and resolve actor names through the existing fallback chain.
def translate_voice(item, file_name, name_prefix):
    if item["jp_explain"] == "":
        return -1
    description = match_description(
        item, voice_source_formats, {},
        restriction="|".join(map(regex.escape, voice_source_restrictions)))
    if description is None:
        return -4
    _, fields, _ = description

    item_name = get_item_name(item, name_prefix)
    # Old Salon descriptions are retranslated even without -r.
    problem = get_translation_problem(item, item_name, redo="Salon" in item["tr_explain"])
    if problem:
        return problem

    racensex = voice_source_restrictions.get(fields["restriction"], "an")
    jp_cv_name = fields["actor"]
    cv_name = ""
    if (not voice_desc_formats[LANG] or not cv_title[LANG]
            or fields["restriction"] and not voice_restriction_extras[racensex][LANG]
            or LANG == 1 and (jp_cv_name not in cv_names or not cv_names[jp_cv_name][LANG])):
        return -5

    # We do, so try to translate it
    if jp_cv_name in cv_names: 
        curr_lang = LANG
        
        while cv_name == "":
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
    body = voice_desc_formats[LANG] + "{restriction}\n{cv}{actorname}".format(
        restriction = voice_restriction_extras[racensex][LANG],
        cv = cv_title[LANG],
        actorname = cv_name)

    return set_description(item, body)

# ——————————————————————————————
# OTHER ITEM RULES & TRANSLATION
# ——————————————————————————————


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

cosmeticsorted_source_types = {
    "FacePattern": ("顔バリエーション", "Facetype"),
    **dict.fromkeys(("Stack_ArmPartsF", "Stack_ArmPartsM"), ("アームパーツ", "Armparts")),
    **dict.fromkeys(("Stack_BodyPartsF", "Stack_BodyPartsM"), ("ボディパーツ", "Bodyparts")),
    **dict.fromkeys(("Stack_LegPartsF", "Stack_LegPartsM"), ("レッグパーツ", "Legparts")),
    "Stack_Headparts": ("ヘッドパーツ", "Headparts"),
}

# JP rules reuse the shared cosmetic body formats and add only this category's allowed notes.

cosmeticsorted_source_formats = {
    **{key: pattern for key, pattern in cosmetic_source_formats.items() if key in ("use_new", "ticket_new")},
    "MagDeviceEvol": r"マグの見た目を変更するデバイス。",
    "MagDeviceReset": r"マグのレベルや支援機能をリセットし\nマグを初期の状態に戻すデバイス。",
    "Capsule": r"特殊能力を\n武器、防具に追加するカプセル。",
    "CapsuleEX": r"EX特殊能力を\n武器に追加するカプセル。",
    "Personalcard": r"使用すると\n「(?P<iname>[^\r\n<>]+)」\nのパートナーカード（ＰＣ）を入手可能。",
}

cosmeticsorted_source_extras = {
    "lv100": r"\n" + source_note_pattern(r"※『PSO2』ではLv\.100以上の\n　マグにのみ使用可能"),
    "game": r"\n" + source_note_pattern(r"※『(?P<game>NGS|PSO2)』でのみ使用可能"),
    "exchange": r"\n" + source_note_pattern(r"アイテムラボの“強化素材交換”で\n特定のカプセルとの交換にも用いられる。"),
    "limit": r"\n" + source_note_pattern("★７以上のEX特殊能力は１つのみ追加可能"),
}

# Mag bodies and their category-specific notes.

mag_formats = {
    # JP text:
    # マグの見た目を変更するデバイス。
    "evol": [
        "A device that changes a Mag's form.",
        "마그의 외형을 변경하는 디바이스.",
        "Изменяет форму Mag'а.",
        "變更瑪古外觀的裝置。",
        "อุปกรณ์สําหรับเปลี่ยนรูปลักษณ์ของ Mag",
    ],
    # JP text:
    # マグのレベルや支援機能をリセットし\n
    # マグを初期の状態に戻すデバイス。
    "reset": [
        ("Resets a Mag's appearance, stats,\n"
         "and support functions back to its \n"
         "default state."),
        ("마그의 레벨과 지원 기능을 초기화해 초기 상태로 되돌리는 디바이스."),
        ("Сбрасывает внещний вид, хар-ки,\n"
         "и функции поддержки Mag'а до\n"
         "состояния по умолчанию."),
        ("重置瑪古的等級與支援功能\n"
         "並使瑪古變回初始狀態的裝置。"),
        ("อุปกรณ์สําหรับรีเซ็ตเลเวลและฟังก์ชันช่วยเหลือของ Mag\n"
         "เพื่อให้ Mag กลับคืนสู่สถานะเริ่มต้น"),
    ],
}

mag_extras = {
    # JP text:
    # ※『PSO2』ではLv.100以上の\n
    # 　マグにのみ使用可能
    "lv100": [
        ("\n<yellow>※Must be used in PSO2 on a Mag\n"
         "which has reached Lv.100 or above.<c>"),
        ("\n<yellow>※『PSO2』에서는 Lv.100 이상의\n"
         "마그에만 사용 가능<c>"),
        ("\n<yellow>※Только на MAG'e PSO2\n"
         "достигшем 100ур.+<c>"),
        ("\n<yellow>※在『PSO2』中僅可對\n"
         "　Lv.100或以上的瑪古使用<c>"),
        ("\n<yellow>※ใน \"PSO2\" สามารถใช้ได้กับ Mag ที่มี Lv.100 ขึ้นไปเท่านั้น<c>"),
    ],
    # JP text:
    # ※『{game}』でのみ使用可能
    "game": [
        ("\n<yellow>※Only usable in {game}.<c>"),
        ("\n<yellow>※『{game}』에서만 사용 가능<c>"),
        ("\n<yellow>※Только для {game}.<c>"),
        ("\n<yellow>※僅可在『{game}』中使用<c>"),
        ("\n<yellow>※สามารถใช้งานได้ใน \"{game}\" เท่านั้น<c>"),
    ],
}

# Capsule bodies and their category-specific notes.

capsule_formats = {
    # JP text:
    # 特殊能力を\n
    # 武器、防具に追加するカプセル。
    "normal": [
        ("A capsule that adds a Special Ability\n"
         "to a weapon or piece of armor."),
        ("무기와 방어구에\n"
         "특수 능력을 추가하는 캡슐."),
        (""),
        ("為武器、防具追加特殊能力的膠囊。"),
        ("แคปซูลสําหรับเพิ่ม Special Ability ให้แก่อาวุธหรือชุดป้องกัน"),
    ],
    # JP text:
    # EX特殊能力を\n
    # 武器に追加するカプセル。
    "ex": [
        ("A capsule that adds an EX Special\n"
         "Ability to a weapon."),
        ("EX 특수 능력을\n"
         "무기에 추가하는 캡슐."),
        (""),
        ("為武器追加EX特殊能力的膠囊。"),
        ("แคปซูลสําหรับเพิ่ม EX Special Ability ให้แก่อาวุธ"),
    ],
}

capsule_extras = {
    # JP text:
    # アイテムラボの“強化素材交換”で\n
    # 特定のカプセルとの交換にも用いられる。
    "exchange": [
        ("\nCan also be exchanged for specific\n"
         "capsules at the Item Lab."),
        ("\n아이템 랩의 “강화 소재 교환”에서\n"
         "특정 캡슐과 교환하는 데도 사용된다."),
        (""),
        ("\n也可在道具實驗室的“交換強化素材”處\n"
         "用於交換特定的膠囊。"),
        ("\nสามารถนําไปใช้แลกเปลี่ยนเป็นแคปซูลเฉพาะได้ที่ \"แลกเปลี่ยนวัสดุเสริมพลัง\" ณ Item Lab"),
    ],
    # JP text:
    # ★７以上のEX特殊能力は１つのみ追加可能
    "limit": [
        ("\n<yellow>Only 1 EX Special Ability of\n"
         "7★ or above can be added<c>"),
        ("\n<yellow>★７ 이상의 EX 특수 능력은 １개만 추가 가능<c>"),
        (""),
        ("\n<yellow>僅可追加1個★7或以上的EX特殊能力<c>"),
        ("\n<yellow>※อาวุธ 7★ ขึ้นไปสามารถเพิ่ม EX Special Ability ได้เพียง 1 ชนิดเท่านั้น<c>"),
    ],
}

# [FUNCTION] Translate parts, Mag devices and capsules, delegating matched NGS parts below.
def translate_cosmeticsorted_desc(item, file_name, name_prefix):
    description = match_description(
        item, cosmeticsorted_source_formats, {**ticket_source_extras, **cosmeticsorted_source_extras},
        intro="", itype="頭部")
    if description is None:
        if file_name not in cosmeticsorted_source_types:
            return -4
        jp_type, _ = cosmeticsorted_source_types[file_name]
        description = match_description(
            item, {"n": ncosmetic_source_formats["n"]},
            {**ticket_source_extras, "posture": r"\n" + source_note_pattern("※武器の構え位置自動調整")},
            itype=regex.escape(jp_type))
        if description is None:
            return -4
        return translate_ncosmeticsorted_desc(item, file_name, name_prefix, description)
    desc_sort, _, source_extras = description
    item_type = "Head" if desc_sort in ("use_new", "ticket_new") else desc_sort
    allowed_extras = ({"lv100", "game"} if item_type.startswith("MagDevice") else
                      {"exchange", "limit"} if item_type == "CapsuleEX" else
                      {"exchange"} if item_type == "Capsule" else set())
    if (set(source_extras) - ticket_extras.keys() - allowed_extras
            or "lv100" in source_extras and source_extras.get("game", {}).get("game") == "NGS"):
        return -4

    item_name = get_item_name(item, name_prefix)
    problem = get_translation_problem(item, item_name)
    if problem:
        return problem
    extras = get_ticket_extras(source_extras)
    if extras is None:
        return -5

    magdlv100 = "lv100" in source_extras
    magdgame = source_extras.get("game", {}).get("game")
    capsuleexchange = "exchange" in source_extras

    if item_type == "Personalcard":
        return -1
    elif item_type.startswith("MagDevice"):
        body = mag_formats["evol"][LANG] if item_type == "MagDeviceEvol" else mag_formats["reset"][LANG]
        if (not body or magdlv100 and not mag_extras["lv100"][LANG]
                or magdgame and not mag_extras["game"][LANG]):
            return -5
        description_extras = [
            mag_extras["lv100"][LANG] if magdlv100 == True else "",
            mag_extras["game"][LANG].format(game=magdgame) if magdgame else ""
        ]
        body += "".join(description_extras)
    elif item_type.startswith("Capsule"):
        capsule_format = capsule_formats["ex"][LANG] if item_type == "CapsuleEX" else capsule_formats["normal"][LANG]
        if not capsule_format or (capsuleexchange and not capsule_extras["exchange"][LANG]) or (item_type == "CapsuleEX" and not capsule_extras["limit"][LANG]):
            return -5
        body = capsule_format
        description_extras = [
            capsule_extras["exchange"][LANG] if capsuleexchange == True else "",
            capsule_extras["limit"][LANG] if item_type == "CapsuleEX" else ""
        ]
        body += "".join(description_extras)
    elif item_type in cosmeticsorted_types:
        # The shared Head template cannot represent the native KO face-variation wording.
        if LANG == 1 and item_type == "Head" and cosmeticsorted_source_types[file_name][1] == "Facetype":
            return -5
        if not cosmetic_desc_formats[desc_sort][LANG] or not cosmeticsorted_types[item_type][LANG]:
            return -5
        body = (cosmetic_desc_formats[desc_sort][LANG]).format(
            itype = cosmeticsorted_types[item_type][LANG],
            iname = item_name,
            sexlock = "")
    else:
        return -4

    return set_description(item, body + extras)

# [FUNCTION] Render matched NGS parts and the optional weapon-position note.
def translate_ncosmeticsorted_desc(item, file_name, name_prefix, description):
    _, item_type = cosmeticsorted_source_types[file_name]
    _, _, source_extras = description

    item_name = get_item_name(item, name_prefix)
    problem = get_translation_problem(item, item_name)
    if problem:
        return problem
    extras = get_ticket_extras(source_extras)
    if extras is None:
        return -5
    weaponposition = "posture" in source_extras
    if weaponposition and not cosmetic_extras["posture"][LANG]:
        return -5

    if item_type in cosmeticsorted_types:
        item_name = cosmeticsorted_types[item_type][LANG]
        if not item_name or not ndesc_formats["n"][LANG]:
            return -5
        body = ndesc_formats["n"][LANG].format(
            itype = item_name,
            a = get_korean_particle(item_name, "을", "를") if LANG == 1 else "" if item_type.endswith("s") else "a ",
            iname = item_name,
        )
        description_extras = [
            cosmetic_extras["posture"][LANG] if weaponposition == True else ""
        ]
        body += "".join(description_extras)
    else:
        return -4

    return set_description(item, body + extras)

# ——————————————————————————————
# WEAPON-CAMOUFLAGE (NGS Part) RULES & TRANSLATION
# ——————————————————————————————

avatar_file_names = [
    "AvatarWPN_Sword",
    "AvatarWPN_WiredLance",
    "AvatarWPN_Partizan",
    "AvatarWPN_TwinDagger",
    "AvatarWPN_DoubleSaber",
    "AvatarWPN_Knuckle",
    "AvatarWPN_GunSlash",
    "AvatarWPN_AssaultRifle",
    "AvatarWPN_Launcher",
    "AvatarWPN_TwinMachineGun",
    "AvatarWPN_Rod",
    "AvatarWPN_Talis",
    "AvatarWPN_Wand",
    "AvatarWPN_Katana",
    "AvatarWPN_Compoundbow",
    "AvatarWPN_JetBoots",
    "AvatarWPN_DualBlade",
    "AvatarWPN_Tact",
]

# JP compatibility lists use katakana aliases for the shared weapon-type terms.
avatar_source_types = {
    "ソード": "大剣",
    "ワイヤードランス": "自在槍",
    "パルチザン": "長槍",
    "ツインダガー": "双小剣",
    "ダブルセイバー": "両剣",
    "ナックル": "鋼拳",
    "ガンスラッシュ": "銃剣",
    "アサルトライフル": "長銃",
    "ランチャー": "大砲",
    "ツインマシンガン": "双機銃",
    "ロッド": "長杖",
    "タリス": "導具",
    "ウォンド": "短杖",
    "カタナ": "抜剣",
    "バレットボウ": "強弓",
    "ジェットブーツ": "魔装脚",
    "デュアルブレード": "飛翔剣",
    "タクト": "奏具",
}

# Existing JP lists can omit the closing tag or contain it twice.
avatar_source_formats = {
    "normal": r"装備の見た目を変更する武器迷彩。\n<yellow>※対応：(?P<weapons>{weapon}(?:／\n?{weapon})*)(?P<others>　ほか)?(?:<c>){{0,2}}",
}

# JP text:
# 装備の見た目を変更する武器迷彩。\n
# <yellow>※対応：{weapons}{others}<c>
avatar_desc_formats = [
    ("Weapon camouflage that changes the\n"
     "appearance of your equipment.\n"
     "<yellow>Type: {weapons}{others}<c>"),
    ("장비의 외형을 변경하는 무기 미채.\n"
     "<yellow>※지원: {weapons}{others}<c>"),
    (""),
    ("變更裝備外觀的武器迷彩。\n"
     "<yellow>※適用於：{weapons}{others}<c>"),
    ("ลายพรางอาวุธสําหรับเปลี่ยนรูปลักษณ์ของอุปกรณ์\n"
     "<yellow>※ รองรับ: {weapons}{others}<c>"),
]

avatar_extras = {
    # JP text: 　ほか
    "others": [
        ("\nand others"),
        (" 외"),
        (""),
        ("　等"),
        (" และอื่น ๆ"),
    ],
}

# [FUNCTION] Translate JP compatibility lists, preserving personalized descriptions verbatim.
def translate_avatar_desc(item, file_name, name_prefix):
    description = match_description(
        item, avatar_source_formats, {},
        weapon="(?:" + "|".join(map(regex.escape, avatar_source_types)) + ")")
    if description is None:
        if (item["jp_explain"].startswith("装備の見た目を変更する武器迷彩。")
                or "※対応：" in item["jp_explain"]):
            return -4
        return -2
    _, fields, _ = description

    problem = get_translation_problem(item)
    if problem:
        return problem

    weapons = [motion_weapon_types[avatar_source_types[weapon]][LANG]
               for weapon in regex.split(r"／\n?", fields["weapons"])]
    desc_format = avatar_desc_formats[LANG]
    others = avatar_extras["others"][LANG] if fields["others"] else ""
    if not desc_format or not all(weapons) or fields["others"] and not others:
        return -5

    separator = "/\n" if regex.search(r"[/／]\n", item["tr_explain"]) else "/"
    body = desc_format.format(
        weapons=separator.join(weapons),
        others=others)
    return set_description(item, body)

# ——————————————————————————————
# MUSIC RULES & TRANSLATION
# ——————————————————————————————

music_source_formats = {
    # Preserve the known newline/indent separator and the explicit 大地のアリア title prefix.
    "jukebox": r"ジュークボックス用音楽再生ディスク。\n(?P<game>[^ \r\n　＃（『<>]+) (?P<track>＃[０-９]+)?(?P<tune>（曲調変更可）)?(?P<separator>\n　?|　|)(?P<title_prefix>大地のアリア)?『(?P<title>[^『』\r<>]+)』",
    "unlock": r"使用すると新しいミュージックが\n再生可能になるディスク。(?P<tune><yellow>※曲調変更可<c>)?\n『(?P<title>[^『』\r<>]+)』",
}

# Copyright lines are retained verbatim in every language.
music_source_extras = {
    "copyright": r"(?P<text>(?:\n[^\r\n<>]*[Ⓒ©][^\r\n<>]*)+)",
}

# EN/RU share expanded game names; KO/CN use the JP code.
music_game_names = {
    # JP text: ＰＳＯ２
    "ＰＳＯ２": "Phantasy Star Online 2",
    # JP text: ＰＳＵ
    "ＰＳＵ": "Phantasy Star Universe",
    # JP text: ＰＳＯ２ｅｓ
    "ＰＳＯ２ｅｓ": "Phantasy Star Online 2 es",
    # JP text: ＰＳＯ
    "ＰＳＯ": "Phantasy Star Online",
    # JP text: ＮｉＧＨＴＳ
    "ＮｉＧＨＴＳ": "NiGHTS",
    # JP text: ＰＳＰｏ１
    "ＰＳＰｏ１": "Phantasy Star Portable",
    # JP text: ＰＳＰｏ２
    "ＰＳＰｏ２": "Phantasy Star Portable 2",
    # JP text: ＰＳＰｏ２ｉ
    "ＰＳＰｏ２ｉ": "Phantasy Star Portable 2 Infinity",
    # JP text: ＰＳＰｏ２ｉＯＳＴ
    "ＰＳＰｏ２ｉＯＳＴ": "Phantasy Star Portable 2i OST",
    # JP text: ＰＳＺ
    "ＰＳＺ": "Phantasy Star Zero",
    # JP text: ＰＳＮｏｖａ
    "ＰＳＮｏｖａ": "Phantasy Star Nova",
    # JP text: ＢＲ
    "ＢＲ": "Burning Rangers",
    # JP text: ＳＧ
    "ＳＧ": "Sonic Generations",
    # JP text: ＳＣ５
    "ＳＣ５": "Space Channel 5",
    # JP text: ＫＭＳＮ
    "ＫＭＳＮ": "Feel the Magic: XY/XX",
    # JP text: ＡＫＤＫ
    "ＡＫＤＫ": "The Rub Rabbits!",
    # JP text: ＶＡＬ１
    "ＶＡＬ１": "Valkyria Chronicles",
    # JP text: ＢＬＡＺＥ
    "ＢＬＡＺＥ": "Blazer Drive",
    # JP text: ＲｏＮ
    "ＲｏＮ": "Rise of Nightmares",
    # JP text: ＳＢ
    "ＳＢ": "Shining Blade",
    # JP text: ＢＥＹＯ
    "ＢＥＹＯ": "Bayonetta",
    # JP text: ＲＨＹＴＨＭ
    "ＲＨＹＴＨＭ": "Rhythm Thief",
    # JP text: ＲＹＵ１
    "ＲＹＵ１": "Yakuza",
    # JP text: ＲＹＵ２
    "ＲＹＵ２": "Yakuza 2",
    # JP text: ＲＹＵ３
    "ＲＹＵ３": "Yakuza 3",
    # JP text: ＲＹＵ４
    "ＲＹＵ４": "Yakuza 4",
    # JP text: ＢＤ
    "ＢＤ": "Binary Domain",
    # JP text: ＫＣ
    "ＫＣ": "Kingdom Conquest",
    # JP text: ＥＡ
    "ＥＡ": "Skies of Arcadia",
    # JP text: ７ＤＲ
    "７ＤＲ": "7th Dragon",
    # JP text: ＰＹＯ
    "ＰＹＯ": "Puyo Puyo",
    # JP text: ＢＢ
    "ＢＢ": "Border Break",
    # JP text: ＳＡＤＸ
    "ＳＡＤＸ": "Sonic Adventure DX",
    # JP text: ＳＣＯ
    "ＳＣＯ": "Sonic Colors",
    # JP text: ＭＡＩ
    "ＭＡＩ": "maimai",
    # JP text: ＰＳＯ２ＶＤ
    "ＰＳＯ２ＶＤ": "PSO2 Vocal Disc",
    # JP text: ＳＡ２
    "ＳＡ２": "Sonic Adventure 2",
    # JP text: ＳＣ５ｐ２
    "ＳＣ５ｐ２": "Space Channel 5 Part 2",
    # JP text: ＲＹＵ５
    "ＲＹＵ５": "Yakuza 5",
    # JP text: ＲＹＵＩ
    "ＲＹＵＩ": "Yakuza Ishin",
    # JP text: ＭＪ
    "ＭＪ": "SEGANET Mahjong MJ",
    # JP text: ＶＯＣＬ
    "ＶＯＣＬ": "Vocaloid",
    # JP text: ＶＯ４
    "ＶＯ４": "Virtual-On Force",
    # JP text: ＳＦＣ
    "ＳＦＣ": "Shining Force Cross",
    # JP text: ＤＦＣ
    "ＤＦＣ": "Dengeki Bunko: Fighting Climax",
    # JP text: ＰＳＯ２ＣＳ０１
    "ＰＳＯ２ＣＳ０１": "PSO2 Character Song",
    # JP text: ＳＲ
    "ＳＲ": "Shining Resonance",
    # JP text: ＳＬＷ
    "ＳＬＷ": "Sonic Lost World",
    # JP text: ＰＳＯ２ＡＮＩ
    "ＰＳＯ２ＡＮＩ": "PSO2 the Animation",
    # JP text: ＰＳＯ２ＣＳ０２
    "ＰＳＯ２ＣＳ０２": "PSO2 Character Song 2",
    # JP text: ＰＳＯ２ＡＮＩＣＳ
    "ＰＳＯ２ＡＮＩＣＳ": "PSO2 the Anime Character Song",
    # JP text: ＰＳＯ２ＡＮＩＣＳ２
    "ＰＳＯ２ＡＮＩＣＳ２": "PSO2 the Anime Chara Song 2",
    # JP text: ＰＳＯ２ＡＮＩＣＳＣＢ
    "ＰＳＯ２ＡＮＩＣＳＣＢ": "PSO2 the Anime Chara Song B",
    # JP text: ＰＤＳＳ
    "ＰＤＳＳ": "Panzer Dragoon",
    # JP text: ＰＳＯ２ＣＳＢ
    "ＰＳＯ２ＣＳＢ": "PSO2 Character Song B",
    # JP text: ＰＳＯ２ＣＯＭＩ
    "ＰＳＯ２ＣＯＭＩ": "Pusoni Comic",
    # JP text: ＰＳＯ２ＰＱＭ
    "ＰＳＯ２ＰＱＭ": "PSO2 Phantastic QM",
    # JP text: ＰＳＯ２ＣＳ０４
    "ＰＳＯ２ＣＳ０４": "PSO2 Character Song 4",
    # JP text: ＰＳＯ２ＥＯ
    "ＰＳＯ２ＥＯ": "PSO2 Episode Oracle",
    # JP text: ＰＳＯ２ＯＳ
    "ＰＳＯ２ＯＳ": "PSO2 On Stage",
    # JP text: ＢＢＣＰ
    "ＢＢＣＰ": "BlazBlue: Chrono Phantasma",
    # JP text: GGXrd
    "GGXrd": "Guilty Gear Xrd",
    # JP text: ＳＨＧ
    "ＳＨＧ": "Sega Hard Girls",
    # JP text: ７ＤＲ３
    "７ＤＲ３": "7th Dragon III Code: VFD",
    # JP text: ＤＡＹ
    "ＤＡＹ": "Daytona USA",
    # JP text: ＦＺ
    "ＦＺ": "Fantasy Zone",
    # JP text: ＡＭＩＧＯ
    "ＡＭＩＧＯ": "Samba de Amigo",
    # JP text: ＯＲ２
    "ＯＲ２": "OutRun 2",
    # JP text: ＳＫＲ
    "ＳＫＲ": "Sakura Wars",
    # JP text: ＳＫＲ２
    "ＳＫＲ２": "Sakura Wars 2",
    # JP text: ＰＳＯ２ＣＳ０３
    "ＰＳＯ２ＣＳ０３": "PSO2 Character Song 3",
    # JP text: ＰＥＲ５
    "ＰＥＲ５": "Persona 5",
    # JP text: ＮＩＥＲ
    "ＮＩＥＲ": "NieR: Automata",
    # JP text: ＤＮＫ
    "ＤＮＫ": "Don Quijote",
    # JP text: ＦＡＧＩＲＬ
    "ＦＡＧＩＲＬ": "Frame Arms Girl",
    # JP text: ＡＴＬ
    "ＡＴＬ": "Atelier",
    # JP text: ＤＯＡ
    "ＤＯＡ": "Dead or Alive",
    # JP text: ＹＫＲ
    "ＹＫＲ": "Yuzuki Yukari",
    # JP text: ＶＯＯＴ
    "ＶＯＯＴ": "Virtual-On: Oratorio Tangram",
    # JP text: ＴＶＯ
    "ＴＶＯ": "A Certain Magical Virtual-On",
    # JP text: Ｐ３Ｄ
    "Ｐ３Ｄ": "Persona 3: Dancing in Moonlight",
    # JP text: Ｐ５Ｄ
    "Ｐ５Ｄ": "Persona 5: Dancing in Starlight",
    # JP text: ＭＨＦ
    "ＭＨＦ": "Monster Hunter Frontier",
    # JP text: ＩＤＬ
    "ＩＤＬ": "IDOLA: Phantasy Star Saga",
    # JP text: ＰＥＲＱ
    "ＰＥＲＱ": "Persona Q",
    # JP text: ＰＥＲＱ２
    "ＰＥＲＱ２": "Persona Q2",
    # JP text: ＰＥＲ４Ｇ
    "ＰＥＲ４Ｇ": "Persona 4 Golden",
    # JP text: ＮＳＫＲ
    "ＮＳＫＲ": "Shin Sakura Wars",
    # JP text: ＡＫＲ
    "ＡＫＲ": "Kizuna Akari",
    # JP text: ＤＢＧ
    "ＤＢＧ": "DBG",
}

# These two source codes name different games; the complete JP title identifies them.
music_game_context_names = {
    # JP text: game=ＳＨ; title=SONIC HEROES
    ("ＳＨ", "SONIC HEROES"): "Sonic Heroes",
    # JP text: game=ＳＨ; title=Shining Hearts
    ("ＳＨ", "Shining Hearts"): "Shining Hearts",
    # JP text: game=ＳＨ; title=風疾る道
    ("ＳＨ", "風疾る道"): "Shining Hearts",
    # JP text: game=ＳＨ; title=心に届く詩
    ("ＳＨ", "心に届く詩"): "Shining Hearts",
    # JP text: game=ＳＡ; title=チエノトビラ
    ("ＳＡ", "チエノトビラ"): "Shining Arc",
    # JP text: game=ＳＡ; title=キェル・マーレ・セラ
    # ～はるかなる故郷へ～
    ("ＳＡ", "キェル・マーレ・セラ\n～はるかなる故郷へ～"): "Shining Arc",
    # JP text: game=ＳＡ; title=Open Your Heart
    ("ＳＡ", "Open Your Heart"): "Sonic Adventure",
    # JP text: game=ＳＡ; title=Welcome to Station Square
    ("ＳＡ", "Welcome to Station Square"): "Sonic Adventure",
}

# Complete scene templates delimit the native title display, including its quotes and prefix.
music_desc_formats = {
    # JP text:
    # ジュークボックス用音楽再生ディスク。\n
    # {game} {track}{separator}{title_prefix}『{title}』
    "jukebox": [
        (
            ("A music disc for your jukebox.\n"
             "{game}{track}\n"
             "{title}{copyright}"),
        ),
        (
            ("주크박스용 음악 재생 디스크.\n"
             "{game}{track}{separator}{title}{copyright}"),
        ),
        (
            ("Диск для вашего муз-автомата.\n"
             "{game}{track}\n"
             "{title}{copyright}"),
        ),
        (
            ("點唱機專用的音樂播放光盤。\n"
             "{game}{track}{separator}{title}{copyright}"),
        ),
        (
            ("แผ่นเพลงสําหรับเปิดเล่นใน Jukebox\n"
             "{game}{track}\n"
             "{title}{copyright}"),
        ),
    ],
    # JP text:
    # ジュークボックス用音楽再生ディスク。\n
    # {game} {track}（曲調変更可）{separator}{title_prefix}『{title}』
    "jukebox_tune": [
        (
            ("A multi-track disc for your jukebox.\n"
             "{game}{track}\n"
             "{title}{copyright}"),
        ),
        (
            ("주크박스용 음악 재생 디스크.\n"
             "{game}{track}（곡조 변경 가능）{separator}{title}{copyright}"),
        ),
        (
            ("Диск с несколькими композициями\n"
             "для вашего муз-автомата.\n"
             "{game}{track}\n"
             "{title}{copyright}"),
        ),
        (
            ("點唱機專用的音樂播放光盤。\n"
             "{game}{track}（可變更曲調）{separator}{title}{copyright}"),
        ),
        (
            ("แผ่นเพลงสําหรับเปิดเล่นใน Jukebox\n"
             "{game}{track}<yellow>※สามารถเปลี่ยนสไตล์ดนตรีได้<c>\n"
             "{title}{copyright}"),
        ),
    ],
    # JP text:
    # 使用すると新しいミュージックが\n
    # 再生可能になるディスク。{tune}\n
    # 『{title}』
    "unlock": [
        (
            ("A disc that you can use to play new\n"
             "music tracks.{tune}\n"
             "{title}{copyright}"),
        ),
        (
            ("사용하면 새로운 음악을\n"
             "재생할 수 있게 되는 디스크.{tune}\n"
             "{title}{copyright}"),
            ("사용하면 새로운 음악을\n"
             "재생할 수 있는 디스크.{tune}\n"
             "{title}{copyright}"),
        ),
        (
            ("Диск, предоставляющий новую\n"
             "композицию после использования.\n"
             "{title}{tune}{copyright}"),
        ),
        (
            ("使用後可以播放新音樂的光盤。{tune}\n"
             "{title}{copyright}"),
        ),
        (
            ("แผ่นเพลงสําหรับเปิดเล่นใน Jukebox{tune}\n"
             "{title}{copyright}"),
        ),
    ],
}

# JP text: <yellow>※曲調変更可<c>
music_tune_extras = [
    (" <yellow>※Multiple tracks.<c>"),
    ("<yellow>※곡조 변경 가능<c>"),
    ("\n※Композицию можно изменить."),
    ("\n<yellow>※可變更曲調<c>"),
    ("\n<yellow>※สามารถเปลี่ยนสไตล์ดนตรีได้<c>"),
]

# [FUNCTION] Rebuild music descriptions using the existing same-language title block.
def translate_music_desc(item, file_name, name_prefix):
    description = match_description(item, music_source_formats, music_source_extras)
    if description is None:
        return -4
    desc_sort, fields, source_extras = description
    if not fields["title"].strip():
        return -4

    problem = get_translation_problem(item)
    if problem:
        return problem

    game, track, separator, tune = "", "", "", ""
    if desc_sort == "jukebox":
        source_game = fields["game"]
        if source_game in ("ＳＨ", "ＳＡ"):
            game_name = music_game_context_names.get((source_game, fields["title"]))
        else:
            game_name = music_game_names.get(source_game)
        if game_name is None or (LANG in (0, 2) and not game_name):
            return -5
        if LANG in (0, 2):
            game = game_name
        elif LANG == 1:
            game = source_game
        else:
            game = source_game.translate(chartable[0])
        source_track = fields["track"] or ""
        if LANG != 1:
            source_track = source_track.replace("＃", "#").translate(chartable[0])
        track = " " + source_track if source_track or LANG in (1, 3) else ""
        separator = fields["separator"]
        if fields["tune"]:
            desc_sort = "jukebox_tune"
    elif fields["tune"]:
        tune = music_tune_extras[LANG]
        if not tune:
            return -5

    values = {
        "game": game, "track": track, "separator": separator,
        "tune": tune,
        "copyright": source_extras["copyright"]["text"] if "copyright" in source_extras else "",
    }
    if LANG in (0, 2):
        title_pattern = r'"(?P<text>[^\r<>]+)"'
    elif fields.get("title_prefix"):
        title_pattern = r'[^\s『』<>][^『』\r\n<>]*『(?P<text>[^『』\r<>]+)』'
    else:
        title_pattern = r'『(?P<text>[^『』\r<>]+)』'
    existing = item["tr_explain"]
    for desc_format in music_desc_formats[desc_sort][LANG]:
        if not desc_format:
            continue
        before, after = desc_format.split("{title}")
        before, after = before.format(**values), after.format(**values)
        if not existing.startswith(before) or not existing.endswith(after):
            continue
        title = existing[len(before):len(existing) - len(after)]
        title_match = regex.fullmatch(title_pattern, title)
        if title_match is None or not title_match["text"].strip():
            return -5
        return set_description(item, desc_format.format(title=title, **values), normalize=False)
    return -5

# ——————————————————————————————
# BOOST (NGS Part) RULES & TRANSLATION
# ——————————————————————————————

boost_source_types = {
    "獲得経験値": "experience",
    "レアドロップ倍率": "rare",
    "獲得N-メセタ": "meseta",
    "獲得N-メセタ、獲得経験値、\nレアドロップ倍率": "triple",
    "獲得経験値、\nレアドロップ倍率": "pair",
    "低温ダメージ耐性": "cold",
}

boost_source_formats = {
    "gain": "使用してから<yellow>(?P<duration>{number})(?P<unit>分間|時間|日間)<c>\n"
            "(?P<effect>{effect})が<yellow>(?P<rate>{number})%アップ<c>する。",
    "seasonal_wrapped": "使用してから<yellow>(?P<duration>{number})(?P<unit>分間|時間|日間)<c>、エネミー撃破時の\n"
                        "獲得シーズナルポイントが\n<yellow>(?P<rate>{number})%アップ<c>する。",
    "seasonal": "使用してから<yellow>(?P<duration>{number})(?P<unit>分間|時間|日間)<c>、エネミー撃破時の\n"
                "獲得シーズナルポイントが<yellow>(?P<rate>{number})[%％]アップ<c>。",
    "genesis": "使用してから<yellow>(?P<duration>{number})(?P<unit>分間|時間|日間)<c>\n"
               "獲得ジェネシスポイントが\n<yellow>(?P<rate>{number})%アップ<c>する。",
    "placeholder": "使用してから<yellow>(?P<duration>{number})分間<c>\n"
                   "獲得シーズナルポイントが\n<yellow>(?P<rate>{number})%アップ<c>する。\n"
                   "<yellow>※〇〇イベント期間限定<c>",
}

boost_source_extras = {
    "stack": "\n<yellow>※他ブーストアイテムと効果累積<c>",
    "logout": "\n<yellow>※ログアウト中も効果時間減少<c>",
    "event": "\n<yellow>※?(?P<event>[^\r\n<>]+)イベント期間限定<c>",
    "range": "\n<yellow>※(?P<event>[^\r\n<>]+～[^\r\n<>]+)限定<c>",
}

boost_unit_types = {"分間": "minute", "時間": "hour", "日間": "day"}

boost_units = {
    # JP text: 分間
    "minute": ["minute", "분 동안", "", "分", "นาที"],
    # JP text: 分間
    "minutes": ["minutes", "분 동안", "", "分", "นาที"],
    # JP text: 時間
    "hour": ["hour", "시간 동안", "", "小時", "ชั่วโมง"],
    # JP text: 時間
    "hours": ["hours", "시간 동안", "", "小時", "ชั่วโมง"],
    # JP text: 日間
    "day": ["day", "일 동안", "", "日", "วัน"],
    # JP text: 日間
    "days": ["days", "일 동안", "", "日", "วัน"],
}

boost_effects = {
    # JP text: 獲得経験値
    "experience": ["EXP gained", "획득 경험치", "", "獲得經驗值", "EXP ที่ได้รับ"],
    # JP text: レアドロップ倍率
    "rare": ["Rare Drop Rate", "레어 드롭 배율", "", "稀有道具掉落率", "Rare Drop Rate"],
    # JP text: 獲得N-メセタ
    "meseta": ["N-Meseta earned", "획득 N-메세타", "", "獲得N-美賽達", "N-Meseta ที่ได้รับ"],
    # JP text: 獲得N-メセタ、獲得経験値、\nレアドロップ倍率
    "triple": [
        ("EXP/RDR/N-Meseta"),
        ("획득 N-메세타와 획득 경험치,\n"
         "레어 드롭 배율"),
        (""),
        ("獲得N-美賽達、獲得經驗值、\n"
         "稀有道具掉落率"),
        ("EXP, อัตราดรอปไอเทมหายาก และ N-Meseta ที่ได้รับ"),
    ],
    # JP text: 獲得経験値、\nレアドロップ倍率
    "pair": [
        ("EXP and Rare Drop Rate"),
        ("획득 경험치와\n"
         "레어 드롭 배율"),
        (""),
        ("獲得經驗值、\n"
         "稀有道具掉落率"),
        ("EXP ที่ได้รับและ\n"
         "Rare Drop Rate"),
    ],
    # JP text: 低温ダメージ耐性
    "cold": [
        ("Cold Damage Resistance"),
        ("저온 피해 내성"),
        (""),
        ("低溫傷害抗性"),
        ("ความต้านทานความเสียหายจากความเย็น"),
    ],
    # JP text: シーズナルポイント
    "seasonal": ["Seasonal Points", "시즌 포인트", "", "季節點數", "Seasonal Point ที่ได้รับจากการกําจัดศัตรู"],
    # JP text: 獲得ジェネシスポイント
    "genesis": ["Genesis Points earned", "제네시스 포인트 획득량", "", "獲得創世點數", "Genesis Point ที่ได้รับ"],
}

# JP text: 使用してから<yellow>{duration}{unit}<c>
# {effect}が<yellow>{rate}%アップ<c>する。
boost_gain_formats = [
    ("Boosts {effect} by <yellow>{rate}%<c>\n"
     "for <yellow>{duration} {unit}<c> after use."),
    ("사용 후 <yellow>{duration}{unit}<c>\n"
     "{effect}{effect_particle} <yellow>{rate}% 증가<c>한다."),
    (""),
    ("在使用後<yellow>{duration}{unit}內<c>\n"
     "<yellow>提升{rate}%<c>{effect}。"),
    ("เมื่อใช้งาน จะเพิ่ม {effect} <yellow>{rate}%<c>\n"
     "เป็นเวลา <yellow>{duration} {unit}<c>"),
]

boost_desc_formats = {
    # JP text: 使用してから<yellow>{duration}{unit}<c>
    # 低温ダメージ耐性が<yellow>{rate}%アップ<c>する。
    "cold": [
        ("Grants {effect} by\n"
         "<yellow>{rate}%<c> for <yellow>{duration} {unit}<c> upon use."),
        (boost_gain_formats[1]),
        (boost_gain_formats[2]),
        (boost_gain_formats[3]),
        ("เมื่อใช้งาน จะเพิ่ม {effect} <yellow>{rate}%<c>\n"
         "เป็นเวลา <yellow>{duration} {unit}<c>"),
    ],
    # JP text: 使用してから<yellow>{duration}{unit}<c>、エネミー撃破時の
    # 獲得シーズナルポイントが<yellow>{rate}%アップ<c>。
    "seasonal": [
        ("Boosts {effect} from killing\n"
         "enemies by <yellow>{rate}%<c> for <yellow>{duration} {unit}<c>."),
        ("사용 후 <yellow>{duration}{unit}<c> 에너미 처치 시\n"
         "획득 {effect}{effect_particle} <yellow>{rate}% 증가<c>한다."),
        (""),
        ("在使用後<yellow>{duration}{unit}內<c>，<yellow>提升{rate}%<c>\n"
         "擊敗敵人時獲得的{effect}。"),
        ("เมื่อใช้งาน จะเพิ่ม {effect} <yellow>{rate}%<c>\n"
         "เป็นเวลา <yellow>{duration} {unit}<c>"),
    ],
}

boost_source_name_format = r"(?P<event>[^\r\n<>]+)[SＳ]ポイント[＋+][0-9０-９]+[%％]"

# JP text: {event}Ｓポイント＋{rate}%
boost_event_name_patterns = [
    r"(?P<event>[^\r\n<>]+?) (?:SP|S\.? Points?) [＋+][0-9０-９]+[%％]",
    r"(?P<event>[^\r\n<>]+?) [SＳ]포인트[＋+][0-9０-９]+[%％]",
    (""),
    r"(?P<event>[^\r\n<>]+?)季節點數[＋+][0-9０-９]+[%％]",
    "(?P<event>Autumn) S Point \\+[0-9]+%",
]

boost_extras = {
    # JP text:
    # <yellow>※他ブーストアイテムと効果累積<c>
    "stack": [
        ("\n<yellow>※Stacks with normal boosts<c>"),
        ("\n<yellow>※다른 부스트 아이템과 효과가 중첩된다.<c>"),
        (""),
        ("\n<yellow>※與其他增益道具積累效果<c>"),
        ("\n<yellow>※สามารถซ้อนทับกับไอเทมบูสต์อื่นได้<c>"),
    ],
    # JP text:
    # <yellow>※ログアウト中も効果時間減少<c>
    "logout": [
        ("\n<yellow>※Timer counts down while logged out<c>"),
        ("\n<yellow>※로그아웃 중에도 효과 시간이 줄어든다.<c>"),
        (""),
        ("\n<yellow>※登出期間也會減少效果時間<c>"),
        ("\n<yellow>※เวลานับถอยหลังต่อเนื่องแม้จะล็อกเอาต์<c>"),
    ],
    # JP text:
    # <yellow>※{event}イベント期間限定<c>
    "event": [
        ("\n<yellow>※Only applies during {event}<c>"),
        ("\n<yellow>※{event} 이벤트 기간 한정<c>"),
        (""),
        ("\n<yellow>※{event}活動期間限定<c>"),
        ("\n<yellow>※ใช้ได้เฉพาะช่วงเทศกาล {event} Event เท่านั้น<c>"),
    ],
}

# [FUNCTION] Translate complete NGS boosts, deriving event titles from the item's own name.
def translate_boost_desc(item, file_name, name_prefix):
    description = match_description(
        item, boost_source_formats, boost_source_extras,
        number=r"[0-9０-９]+",
        effect="(?:" + "|".join(map(regex.escape, boost_source_types)) + ")")
    if description is None:
        return -4
    desc_sort, fields, source_extras = description
    if desc_sort == "placeholder":
        return -2
    problem = get_translation_problem(item)
    if problem:
        return problem

    if desc_sort == "gain":
        desc_sort = boost_source_types[fields["effect"]]
    elif desc_sort == "seasonal_wrapped":
        desc_sort = "seasonal"
    duration = fields["duration"].translate(chartable[0])
    unit_type = boost_unit_types[fields["unit"]] + ("s" if duration != "1" else "")
    unit = boost_units[unit_type][LANG]
    effect = boost_effects[desc_sort][LANG]
    desc_format = boost_desc_formats.get(desc_sort, boost_gain_formats)[LANG]
    if not unit or not effect or not desc_format:
        return -5
    body = desc_format.format(
        duration=duration, unit=unit, effect=effect,
        effect_particle=get_korean_particle(effect, "이", "가") if LANG == 1 else "",
        rate=fields["rate"].translate(chartable[0]))

    extras = []
    for extra, extra_fields in source_extras.items():
        if extra in ("stack", "logout"):
            note = boost_extras[extra][LANG]
            if not note:
                return -5
            extras.append(note)
            continue

        source_name = regex.fullmatch(boost_source_name_format, item["jp_text"])
        if source_name is None or source_name["event"] != extra_fields["event"]:
            return -5
        note = boost_extras["event"][LANG]
        if not note:
            return -5
        event = get_existing_description_field(item, note, "event") if LANG in (0, 1) else None
        if event is None:
            name_parts = get_item_name_parts(item, name_prefix, boost_event_name_patterns)
            if name_parts is None:
                return -5
            event = name_parts["event"]
        extras.append(note.format(event=event))
    return set_description(item, body + "".join(extras))

# ——————————————————————————————
# PAID-PASS (NGS Part) RULES & TRANSLATION
# ——————————————————————————————

paidpass_source_formats = {
    "success_great": r"アイテム強化時に\n強化が大成功になる確率を\n上昇させる。",
    "success_ability": r"アイテムの特殊能力追加時に\n追加が成功する確率を\n上昇させる。",
    "success_preset": r"プリセット能力の\n強化成功率を上昇させる。",
    "protect_ability": r"アイテムの特殊能力追加失敗時に\n素材アイテムが\n消費されるのを防止する。",
    "protect_preset": r"プリセット能力の強化失敗時に\n素材アイテムが消費されるのを防止する。",
    "material_limit": r"アイテムの限界突破時に\n(?:レアリティ★(?P<rarity>{number})(?P<lower>以下の)?アイテムの\n)?強化限界値を(?P<start>{number})から(?P<end>{number})にするための\n必要素材アイテムを不要にする。",
    "material_potential": r"(?:アイテムの潜在能力を\n|レアリティ★(?P<rarity>{number})(?P<lower>以下の)?アイテムの\n潜在能力を)Lv\.(?P<level>{number})にするための\n必要素材アイテムを不要にする。",
    "material_preset": r"プリセット能力の強化時に\n必要素材アイテムを不要にする。",
    "guaranteed_material": r"プリセット能力の強化を(?P<rate>{number})％成功させ\n必要素材アイテムを不要にする。",
    "material_ring": r"スキルリングを(?P<steps>{number})段階強化するための\n必要素材アイテムを不要にする。",
    "skip": r"アイテム強化スキップで\n限界突破の上限値を基準として\nレアリティ★(?P<rarity>{number})以下の(?P<item_type>武器|防具)の\n強化値を最大(?P<level>{number})にする。",
    "scratch": r"アイテムパックに所持しておくことで\n<yellow>(?P<target>[^\r\n<>]+)<c>に\n(?P<count>{number})回挑戦できる(?P<item_type>チケット|メダル)。",
    "scratch_batch": r"アイテムパックに所持しておくことで\n(?P<tickets>{number})枚で(?P<count>{number})回、<yellow>(?P<target>[^\r\n<>]+)<c>に\n挑戦できるチケット。",
    "recycle": r"(?P<tickets>{number})枚集めることで\nアイテムリサイクルで\n<yellow>(?P<target>[^\r\n<>]+)<c>\nと交換できるチケット。",
    "recycle_unspecified": r"一定枚数集めることで\nアイテムリサイクルで\n<yellow>(?P<target>[^\r\n<>]+)<c>\nと交換できるチケット。",
    "color": r"エステで、装備している\nコスチューム等のカラー変更ができる。\n利用するごとにパスが必要。",
    "tree_add": r"新規スキルツリーを(?P<count>{number})枚追加する。\n1キャラクターにつき\n(?P<limit>{number})枚まで拡張可能。",
    "tree_shift": r"“N-スキルツリー追加”を\n使用前の状態に戻して\nスキルポイントを振り直せる。",
    "tree_reset": r"追加したツリーを含めて\n全スキルツリーを初期化し\nスキルポイントを振り直せる。",
    "class_title": r"(?P<class_name>[A-Z][a-z]|)クラスレベル(?P<level>{number})化(?P<equipment>＆適正装備セット)?",
    "trainia": r"『NGS』Ver\.(?P<version>{number})全トレイニア踏破",
    "shop": r"トレジャーショップの陳列更新パス。\n(?P<currency>ＳＧ|メセタ)で購入するトレジャーショップの\n陳列を変更し購入上限をリセットする。",
    "preset_random": r"Lv\.(?P<level>{number})のプリセット能力の\nいずれかを装備に追加する。",
    "transfer": r"アイテムの特殊能力を\n別のアイテムに移植するときに用いる。",
}

paidpass_source_extras = {
    "preset_add": r"\n" + source_note_pattern("※プリセット能力の追加でも使用可能"),
    "no_rate": r"\n" + source_note_pattern("※強化成功率は上昇しない"),
    "preset_level": r"\nベースアイテムのプリセット能力レベルが\n表示レベル以下の場合のみ使用可能。",
    "ring_level": r"\nベースアイテムの強化値が\n表示値以下の場合のみ使用可能。",
    "ring_any": r"\nベースアイテムの強化値に\n関係なく使用可能。",
}

# Each body accepts only its stated note; material_ring accepts either source condition.
paidpass_required_extras = {
    "success_preset": "preset_add",
    "protect_preset": "preset_level",
    "material_preset": "no_rate",
    "guaranteed_material": "preset_level",
    "preset_random": "preset_add",
}

paidpass_success_actions = {
    # JP text: アイテム強化時に強化が大成功になる確率
    "great": [
        ("the chance of a Great\n"
         "Success when enhancing an item"),
        ("아이템 강화 시\n"
         "강화가 대성공할 확률"),
        (""),
        ("強化道具時的強化大成功概率"),
        ("เมื่อเสริมพลังไอเทม\n"
         "จะช่วยเพิ่มโอกาสเกิด Great Success\n"
         "ให้สูงขึ้น"),
    ],
    # JP text: アイテムの特殊能力追加時に追加が成功する確率
    "ability": [
        ("the chance of successfully\n"
         "adding Special Abilities to an item"),
        ("아이템에 특수능력을 추가할 때\n"
         "추가에 성공할 확률"),
        (""),
        ("追加道具的特殊能力時的\n"
         "追加成功概率"),
        ("เมื่อเพิ่ม Special Ability ให้แก่ไอเทม\n"
         "จะช่วยเพิ่มอัตราความสําเร็จ\n"
         "ให้สูงขึ้น"),
    ],
    # JP text: プリセット能力の強化成功率
    "preset": [
        ("the success rate of\n"
         "Preset Ability Upgrade"),
        ("프리셋 능력의\n"
         "강화 성공률"),
        (""),
        ("預設能力的強化成功率"),
        ("เพิ่มอัตราความสําเร็จในการอัปเกรด\n"
         "Preset Ability"),
    ],
}

paidpass_protection_actions = {
    # JP text: アイテムの特殊能力追加失敗時に
    # 素材アイテムが
    # 消費されるのを防止する。
    "ability": [
        ("Prevents material item consumption\n"
         "if adding an Ability fails."),
        ("아이템에 특수능력을 추가하다 실패해도\n"
         "소재 아이템이\n"
         "소모되지 않도록 한다."),
        (""),
        ("防止追加道具的特殊能力失敗時\n"
         "素材道具被消耗。"),
        ("เมื่อการเพิ่ม Special Ability ล้มเหลว\n"
         "จะช่วยป้องกันไม่ให้ไอเทมวัตถุดิบ\n"
         "สูญหายไป"),
    ],
    # JP text: プリセット能力の強化失敗時に
    # 素材アイテムが消費されるのを防止する。
    "preset": [
        ("Prevents material item consumption\n"
         "if Preset Ability Upgrade fails."),
        ("프리셋 능력 강화에 실패했을 때\n"
         "소재 아이템이 소비되는 것을 방지한다."),
        (""),
        ("防止強化預設能力失敗時素材道具被消耗。"),
        ("ป้องกันการสูญเสียวัตถุดิบเมื่อการอัปเกรด\n"
         "Preset Ability ล้มเหลว"),
    ],
}

paidpass_material_scopes = {
    # JP text: アイテム
    "any": ["single item", "아이템의", "", "道具的", "ไอเทม"],
    # JP text: レアリティ★{rarity}アイテム
    "exact": ["★{rarity} item", "레어리티★{rarity} 아이템의", "", "稀有度★{rarity}道具的", "ไอเทมระดับ ★{rarity}"],
    # JP text: レアリティ★{rarity}以下のアイテム
    "maximum": [
        ("★{rarity} or\n"
         "lower item"),
        ("레어리티★{rarity} 이하 아이템의"),
        (""),
        ("稀有度★{rarity}或以下道具的"),
        ("ไอเทมระดับ ★{rarity} หรือต่ํากว่า"),
    ],
}

paidpass_material_operations = {
    # JP text: {item}の潜在能力をLv.{level}にするための
    "potential": [
        ("to unlock Potential Ability Lv.{level} on a\n"
         "{item}"),
        ("{item}\n"
         "잠재능력을 Lv.{level}{level_particle} 만드는 데"),
        (""),
        ("將{item}{item_break}潛在能力{level_break}提升至Lv.{level}"),
        ("ยกเว้นการใช้วัสดุที่จําเป็น\n"
         "ในการปลดล็อก Potential Ability Lv.{level}\n"
         "ให้แก่{item}"),
    ],
    # JP text: アイテムの限界突破時に{item}の強化限界値を{start}から{end}にするための
    "limit": [
        ("to raise the Grind Limit of a {item}{limit_break}from {start} to {end}"),
        ("아이템 한계 돌파 시\n"
         "{item}강화 한계치를 {start}에서 {end}{end_particle} 높이는 데"),
        (""),
        ("道具界限突破時\n"
         "將{item}強化界限值從{start}提升至{end}\n"),
        ("ยกเว้นการใช้วัสดุที่จําเป็นเมื่อทํา Limit Break\n"
         "เพื่อเพิ่มขีดจํากัด Grind Limit จาก {start} เป็น {end}\n"
         "ให้แก่{item}"),
    ],
    # JP text: プリセット能力の強化時に
    "preset": ["when enhancing a Preset Ability", "프리셋 능력 강화 시", "", "強化預設能力時", "ไม่ต้องใช้วัตถุดิบเมื่อทําการอัปเกรด\nPreset Ability"],
    # JP text: スキルリングを{steps}段階強化するための
    "ring": [
        ("to grind a Skill Ring by {steps} level{plural}"),
        ("스킬 링을 {steps}단계 강화하는 데"),
        (""),
        ("{steps}段強化技能戒指\n"),
        ("ไม่ต้องใช้วัตถุดิบในการอัปเกรด\n"
         "Skill Ring ขึ้น {steps} ขั้น"),
    ],
}

paidpass_level_objects = {
    # JP text: プリセット能力レベル
    "preset": ["Preset Ability\nlevel","프리셋 능력 레벨이", "","預設能力等級", "Preset Ability ของไอเทมหลักมีเลเวล"],
    # JP text: 強化値
    "ring": ["grind\nlevel", "강화치가", "", "強化值", "ระดับ Grind ของไอเทมหลัก"],
}

paidpass_level_units = {
    # JP text: レベル
    "preset": ["level", "레벨", "", "等級", "เลเวลที่ระบุไว้"],
    # JP text: 値
    "ring": ["value", "수치", "", "等級", "ค่าที่ระบุไว้"],
}

# JP text: ベースアイテムの{object}が
# 表示{unit}以下の場合のみ使用可能。
paidpass_level_format = [
    (" Only\n"
     "usable if base item's {object} is at or below the displayed {unit}."),
    ("\n베이스 아이템의 {object}\n"
     "표시된 {unit} 이하일 때만 사용 가능."),
    (""),
    ("\n僅可在基底道具的{object}\n"
     "為顯示的{unit}或以下時使用。"),
    ("\nใช้งานได้เฉพาะเมื่อ\n"
     "{object}เท่ากับหรือต่ํากว่า{unit}เท่านั้น"),
]

paidpass_skip_types = {
    # JP text: 武器
    "weapon": ["weapon", "무기", "", "武器", "อาวุธระดับ"],
    # JP text: 防具
    "armor": ["armor", "방어구", "", "防具", "ชุดป้องกันระดับ"],
}

paidpass_scratch_types = {
    # JP text: チケット
    "ticket": ["ticket", "티켓", "", "票券", "ตั๋ว"],
    # JP text: メダル
    "medal": ["medal", "메달", "", "獎章", "เหรียญรางวัล"],
}

paidpass_shop_currencies = {
    # JP text: ＳＧ
    "sg": ["SG", "ＳＧ", "", "SG", "SG"],
    # JP text: メセタ
    "meseta": ["Meseta", "메세타", "", "美賽達", "Meseta"],
}

paidpass_recycle_amounts = {
    # JP text: {tickets}枚
    "counted": ["batches of {tickets}", "{tickets}장", "", "{tickets}張", "{tickets} ใบ"],
    # JP text: 一定枚数
    "unspecified": ["batches", "일정 수량", "", "一定張數", "ตามจํานวนที่กําหนด"],
}

paidpass_class_extras = {
    # JP text: ＆適正装備セット
    "equipment": [" & Equipment Set", "＆적정 장비 세트", "", "&適配裝備套裝", "\nพร้อมอุปกรณ์ที่เหมาะสม"],
}

paidpass_extras = {
    # JP text:
    # <yellow>※プリセット能力の追加でも使用可能<c>
    "preset_add": [
        ("\n<yellow>※Can also be used to add\n"
         "Preset Abilities.<c>"),
        ("\n<yellow>※프리셋 능력 추가 시에도 사용 가능<c>"),
        (""),
        ("\n<yellow>※也可用於追加預設能力<c>"),
        ("\n<yellow>※สามารถใช้งานในการเพิ่ม Preset Ability ได้เช่นกัน<c>"),
    ],
    # JP text:
    # <yellow>※強化成功率は上昇しない<c>
    "no_rate": [
        ("\n<yellow>※Success rate is not affected.<c>"),
        ("\n<yellow>※강화 성공률은 상승하지 않음<c>"),
        (""),
        ("\n<yellow>※不會提升強化成功率<c>"),
        ("\n<yellow>※ไม่เพิ่มอัตราความสําเร็จในการอัปเกรด<c>"),
    ],
    # JP text:
    # ベースアイテムの強化値に
    # 関係なく使用可能。
    "ring_any": [
        ("\nCan be used regardless of\n"
         "the base item's grind level."),
        ("\n베이스 아이템의 강화치와\n"
         "관계없이 사용 가능."),
        (""),
        ("\n可無關基底道具的強化值使用。"),
        ("\nสามารถใช้งานได้\n"
         "โดยไม่คํานึงถึงระดับ Grind ของไอเทมหลัก"),
    ],
}

paidpass_desc_formats = {
    # JP text: {operation}を上昇させる。
    "success": ["Increases {operation}.", "{operation}을 높인다.", "", "提升{operation}。", "{operation}"],
    # JP text: {operation}
    "protect": ["{operation}", "{operation}", "", "{operation}", "{operation}"],
    # JP text: {operation}
    # 必要素材アイテムを不要にする。
    "material": [
        ("Removes the material requirement\n"
         "{operation}."),
        ("{operation}\n"
         "필요한 소재 아이템을 대체한다."),
        (""),
        ("免除{operation}所需的素材道具。"),
        ("{operation}"),
    ],
    # JP text: プリセット能力の強化を{rate}％成功させ
    # 必要素材アイテムを不要にする。
    "guaranteed_material": [
        ("Success Rate {rate}% & material requirement\n"
         "removed for Enhancing Preset Abilities."),
        ("프리셋 능력 강화를 {rate}％ 성공시키고\n"
         "소재 아이템이 필요 없게 한다."),
        (""),
        ("使強化預設能力{rate}%成功\n"
         "並免除所需的素材道具。"),
        ("ทําให้อัตราความสําเร็จในการอัปเกรด\n"
         "Preset Ability เป็น {rate}% โดยไม่ต้องใช้วัตถุดิบ"),
    ],
    # JP text: アイテム強化スキップで
    # 限界突破の上限値を基準として
    # レアリティ★{rarity}以下の{item_type}の
    # 強化値を最大{level}にする。
    "skip": [
        ("Allows you to skip grinding {article}★{rarity} or\n"
         "lower {item_type} to up to +{level}, subject\n"
         "to its current Grind Limit."),
        ("아이템 강화 스킵 시\n"
         "한계 돌파 상한을 기준으로\n"
         "레어리티★{rarity} 이하 {item_type}의\n"
         "강화 수치를 최대 {level}까지 높인다."),
        (""),
        ("通過跳過強化的方式\n"
         "以界限突破的上限值為基準\n"
         "將稀有度★{rarity}或以下{item_type}的\n"
         "強化值提升至最大{level}。"),
        ("ใช้ข้ามขั้นตอนการ Grind เพื่อเพิ่มค่าตีบวกของ\n"
         "{item_type} ★{rarity} หรือต่ํากว่าได้สูงสุดถึง +{level}\n"
         "โดยอิงตามขีดจํากัด Grind Limit ในปัจจุบัน"),
    ],
    # JP text: アイテムパックに所持しておくことで
    # <yellow>{target}<c>に
    # {count}回挑戦できる{item_type}。
    "scratch": [
        ("Allows you {count} chance{plural} at the\n"
         "<yellow>{target}<c>\n"
         "just by having it in your inventory."),
        ("아이템 팩에 소지하고 있으면\n"
         "<yellow>{target}<c>에\n"
         "{count}회 도전할 수 있는 {item_type}."),
        (""),
        ("放在道具背包內即可挑戰{count}次\n"
         "<yellow>{target}<c>的{item_type}。"),
        ("{item_type}สําหรับลุ้นรับรางวัลจาก <yellow>{target}<c> {count} ครั้ง\n"
         "เพียงแค่พกพาติดตัวไว้ใน Item Pack"),
    ],
    # JP text: アイテムパックに所持しておくことで
    # {tickets}枚で{count}回、<yellow>{target}<c>に
    # 挑戦できるチケット。
    "scratch_batch": [
        ("Allows you {count} chance{plural} at the\n"
         "<yellow>{target}<c> just by having\n"
         "{tickets} of these in your inventory."),
        ("아이템 팩에 소지하고 있으면\n"
         "{tickets}장으로 {count}회, <yellow>{target}<c>에\n"
         "도전할 수 있는 티켓."),
        (""),
        ("放在道具背包內即可用{tickets}張挑戰{count}次\n"
         "<yellow>{target}<c>的票券。"),
        ("ตั๋วที่เมื่อพกติดตัวไว้ใน Inventory ครบ {tickets} ใบ\n"
         "จะสามารถเข้าร่วมสุ่ม <yellow>\"{target}\"<c>\n"
         "ได้ {count} ครั้ง"),
    ],
    # JP text: {amount}集めることで
    # アイテムリサイクルで
    # <yellow>{target}<c>
    # と交換できるチケット。
    "recycle": [
        ("A ticket which can be recycled in\n"
         "{amount} to obtain\n"
         "<yellow>{target}<c>."),
        ("{amount}을 모으면\n"
         "아이템 리사이클에서\n"
         "<yellow>{target}<c>\n"
         "{particle} 교환할 수 있는 티켓."),
        (""),
        ("集齊{amount}即可在道具回收中\n"
         "交換<yellow>{target}<c>的票券。"),
        ("ตั๋วที่เมื่อสะสมครบ {amount}\n"
         "สามารถนําไปแลกรับ <yellow>\"{target}\"<c>\n"
         "ได้ที่ Item Recycle"),
    ],
    # JP text: エステで、装備している
    # コスチューム等のカラー変更ができる。
    # 利用するごとにパスが必要。
    "color": [
        ("Allows you to change the colors of\n"
         "your cosmetics at the Beauty Salon.\n"
         "One pass is required each time."),
        ("에스테에서 장비한\n"
         "코스튬 등의 색상을 변경할 수 있다.\n"
         "이용할 때마다 패스가 필요하다."),
        (""),
        ("可在美容院內，變更裝備中的\n"
         "服裝等內容的顏色。\n"
         "每次使用都需要票證。"),
        ("สามารถเปลี่ยนสีของ Costume ที่สวมใส่อยู่ได้ใน Salon\n"
         "จําเป็นต้องใช้บัตรในแต่ละครั้งที่ใช้งาน"),
    ],
    # JP text: 新規スキルツリーを{count}枚追加する。
    # 1キャラクターにつき
    # {limit}枚まで拡張可能。
    "tree_add": [
        ("Adds {count} new Skill Tree{plural} to one of your\n"
         "Classes. Up to {limit} Skill Trees can be\n"
         "added per character."),
        ("새 스킬 트리를 {count}개 추가한다.\n"
         "캐릭터당\n"
         "{limit}개까지 확장할 수 있다."),
        (""),
        ("追加{count}條新技能樹。\n"
         "每個角色最多可擴充{limit}條。"),
        ("เพิ่ม Skill Tree ใหม่ {count} แผ่น\n"
         "สามารถขยายได้สูงสุดไม่เกิน {limit} แผ่น\n"
         "ต่อ 1 ตัวละคร"),
    ],
    # JP text: “N-スキルツリー追加”を
    # 使用前の状態に戻して
    # スキルポイントを振り直せる。
    "tree_shift": [
        ("Lets you transfer one Skill Tree added\n"
         "with an N-Skill Tree Add and/or reset\n"
         "any SP assigned to that Skill Tree."),
        ("“N-스킬 트리 추가”를\n"
         "사용하기 전의 상태로 되돌려\n"
         "스킬 포인트를 다시 배분할 수 있다."),
        (""),
        ("可以將“N-技能樹追加”\n"
         "變回使用前的狀態並重點技能點數。"),
        ("รีเซ็ตสถานะของ \"N-Skill Tree Add\"\n"
         "ให้กลับไปเป็นเหมือนก่อนใช้งาน\n"
         "เพื่อทําการย้ายและจัดสรรแต้ม SP ใหม่อีกครั้ง"),
    ],
    # JP text: 追加したツリーを含めて
    # 全スキルツリーを初期化し
    # スキルポイントを振り直せる。
    "tree_reset": [
        ("Resets SP assigned to all Skill Trees,\n"
         "including Skill Trees added with\n"
         "N-Skill Tree Add passes."),
        ("추가한 트리를 포함해\n"
         "모든 스킬 트리를 초기화하고\n"
         "스킬 포인트를 다시 배분할 수 있다."),
        (""),
        ("可以對包含追加技能樹在內的\n"
         "所有技能樹進行初始化\n"
         "並重點技能點數。"),
        ("รีเซ็ต Skill Tree ทั้งหมดรวมถึงทรีที่เพิ่มเข้ามา\n"
         "เพื่อจัดสรรแต้ม SP ใหม่อีกครั้ง"),
    ],
    # JP text: {class_name}クラスレベル{level}化{equipment}
    "class_title": [
        "{class_prefix}Class Lv. {level}{equipment}",
        "{class_prefix}클래스 레벨 {level}{level_particle} 변경{equipment}",
        "",
        "{class_prefix}職業等級升至{level}{equipment}",
        "ตั๋วสําหรับปรับเลเวลคลาส {class_prefix}ให้เป็น Lv.{level}{equipment}",
    ],
    # JP text: 『NGS』Ver.{version}全トレイニア踏破
    "trainia": [
        "Clears all [NGS] Ver.{version} Trainia.",
        "『NGS』Ver.{version} 모든 트레이니아 돌파",
        "",
        "突破『NGS』Ver.{version}全訓練設施",
        "บัตรผ่านสําหรับปลดล็อกและเคลียร์ Trainia ทั้งหมดของ\n\"NGS\" Ver.{version} โดยอัตโนมัติ\n<yellow>※ไม่รวม Advanced Trainia<c>",
    ],
    # JP text: トレジャーショップの陳列更新パス。
    # {currency}で購入するトレジャーショップの
    # 陳列を変更し購入上限をリセットする。
    "shop": [
        ("Chooses a new selection of items for\n"
         "the {currency} Treasure Shop and resets\n"
         "any purchase limits for those items."),
        ("트레저 숍 진열 갱신 패스.\n"
         "{currency}로 구매하는 트레저 숍의 진열을\n"
         "바꾸고 구매 상한을 초기화한다."),
        (""),
        ("更新寶物商店陳列的票券。\n"
         "變更以{currency}購買的寶物商店的陳列\n"
         "並重置購買上限。"),
        ("บัตรสําหรับรีเฟรชสินค้าใน Treasure Shop\n"
         "จะสุ่มเปลี่ยนรายการสินค้าที่ซื้อด้วย {currency} ใหม่\n"
         "และรีเซ็ตขีดจํากัดการซื้อของสินค้าเหล่านั้น"),
    ],
    # JP text: Lv.{level}のプリセット能力の
    # いずれかを装備に追加する。
    "preset_random": [
        ("Adds a Lv.{level} Preset Ability to\n"
         "a piece of equipment."),
        ("Lv.{level} 프리셋 능력 중\n"
         "하나를 장비에 추가한다."),
        (""),
        ("為裝備追加任意Lv.{level}的預設能力。"),
        ("สุ่มมอบ Preset Ability ระดับ Lv.{level}\n"
         "อย่างใดอย่างหนึ่งให้กับอุปกรณ์สวมใส่"),
    ],
    # JP text: アイテムの特殊能力を
    # 別のアイテムに移植するときに用いる。
    "transfer": [
        ("Item used to transfer\n"
         "Special Abilities to another item."),
        ("아이템의 특수 능력을\n"
         "다른 아이템에 이식할 때 사용한다."),
        (""),
        ("用於將道具的特殊能力\n"
         "移植至其他道具上。"),
        ("ใช้เมื่อต้องการถ่ายโอน Special Ability\n"
         "ของไอเทมชิ้นหนึ่งไปยังอีกไอเทมหนึ่ง"),
    ],
}

# [FUNCTION] Translate recognized pass mechanisms with one canonical same-language template.
def translate_paidpass_desc(item, file_name, name_prefix):
    description = match_description(
        item, paidpass_source_formats, paidpass_source_extras,
        number=r"[0-9０-９]+")
    if description is None:
        return -4
    desc_sort, fields, source_extras = description
    required = paidpass_required_extras.get(desc_sort)
    if desc_sort == "material_ring":
        if list(source_extras) not in (["ring_level"], ["ring_any"]):
            return -4
    elif list(source_extras) != ([required] if required else []):
        return -4

    problem = get_translation_problem(item)
    if problem:
        return problem

    values = {key: (value or "").translate(chartable[0]) for key, value in fields.items()}
    if LANG == 1:
        for field in ("level", "end"):
            if field in values:
                values[field + "_particle"] = "으로" if values[field][-1] in "036" else "로"
    if "count" in values:
        count = int(values["count"])
        values["plural"] = "" if count == 1 else "s"
        if LANG == 0 and count == 1:
            values["count"] = "a" if desc_sort == "tree_add" else "one"

    if desc_sort.startswith("success_"):
        operation = desc_sort[len("success_"):]
        values["operation"] = paidpass_success_actions[operation][LANG]
        if not values["operation"]:
            return -5
        desc_sort = "success"
    elif desc_sort.startswith("protect_"):
        operation = desc_sort[len("protect_"):]
        values["operation"] = paidpass_protection_actions[operation][LANG]
        if not values["operation"]:
            return -5
        desc_sort = "protect"
    elif desc_sort.startswith("material_"):
        operation = desc_sort[len("material_"):]
        if operation in ("potential", "limit"):
            scope = "maximum" if fields["lower"] else "exact" if fields["rarity"] else "any"
            item_format = paidpass_material_scopes[scope][LANG]
            if not item_format:
                return -5
            values["item"] = item_format.format(**values)
            if LANG == 0:
                if operation == "potential":
                    values["item"] = values["item"].replace("\n", " ")
                else:
                    values["limit_break"] = " " if fields["lower"] else "\n"
            elif LANG == 3 and operation == "potential":
                values["item_break"] = "\n" if fields["rarity"] else ""
                values["level_break"] = "" if fields["rarity"] else "\n"
            if operation == "limit" and LANG in (1, 3):
                values["item"] = values["item"] + "\n" if fields["rarity"] else ""
        elif operation == "ring":
            values["plural"] = "" if int(values["steps"]) == 1 else "s"
        operation_format = paidpass_material_operations[operation][LANG]
        if not operation_format:
            return -5
        values["operation"] = operation_format.format(**values)
        desc_sort = "material"
    elif desc_sort == "skip":
        item_type = "weapon" if fields["item_type"] == "武器" else "armor"
        values["item_type"] = paidpass_skip_types[item_type][LANG]
        values["article"] = "a " if LANG == 0 and item_type == "weapon" else ""
        if not values["item_type"]:
            return -5
    elif desc_sort in ("scratch", "scratch_batch", "recycle", "recycle_unspecified"):
        target = get_ticket_target_name(item, name_prefix, fields["target"])
        if target is None:
            return -5
        values["target"] = target
        if desc_sort == "scratch":
            item_type = "ticket" if fields["item_type"] == "チケット" else "medal"
            values["item_type"] = paidpass_scratch_types[item_type][LANG]
            if not values["item_type"]:
                return -5
        elif desc_sort.startswith("recycle"):
            amount = "counted" if desc_sort == "recycle" else "unspecified"
            amount_format = paidpass_recycle_amounts[amount][LANG]
            if not amount_format:
                return -5
            values["amount"] = amount_format.format(**values)
            if LANG == 1:
                final = (ord(target[-1]) - 0xAC00) % 28
                values["particle"] = "로" if final in (0, 8) else "으로"
            desc_sort = "recycle"
    elif desc_sort == "class_title":
        values["class_prefix"] = fields["class_name"] + (" " if fields["class_name"] and LANG != 3 else "")
        values["equipment"] = ""
        if fields["equipment"]:
            values["equipment"] = paidpass_class_extras["equipment"][LANG]
            if not values["equipment"]:
                return -5
    elif desc_sort == "shop":
        currency = "sg" if fields["currency"] == "ＳＧ" else "meseta"
        values["currency"] = paidpass_shop_currencies[currency][LANG]
        if not values["currency"]:
            return -5

    desc_format = paidpass_desc_formats[desc_sort][LANG]
    if not desc_format:
        return -5
    body = desc_format.format(**values)
    for extra in source_extras:
        if extra in ("preset_level", "ring_level"):
            kind = "preset" if extra == "preset_level" else "ring"
            desc_format = paidpass_level_format[LANG]
            object_name = paidpass_level_objects[kind][LANG]
            unit = paidpass_level_units[kind][LANG]
            if not desc_format or not object_name or not unit:
                return -5
            body += desc_format.format(object=object_name, unit=unit)
        else:
            extra_format = paidpass_extras[extra][LANG]
            if not extra_format:
                return -5
            body += extra_format
    return set_description(item, body)

# ——————————————————————————————
# TOOL (NGS Part) RULES & TRANSLATION
# ——————————————————————————————

tool_source_formats = {
    "revive": r"所持者が戦闘不能になったときに\n使用可能な蘇生デバイス。\nHPが(?P<revive_hp>半分|最大)の状態で復活する。",
    "recycle_equal": r"アイテムリサイクルで\n(?P<scratch>AC|SG)スクラッチアイテムと同等品として\n交換に使用できるバッヂ。",
    "trade": r"(?P<trade_intro>(?:[^\r\n]+\n)?)アイテムトレーダーの\n“(?P<menu>[^\r\n“”]+)”で\n(?P<goods>アイテム|武器など|★(?P<rarity>[0-9]+)武器など)と交換できる。",
    "leso": r"(?P<leso_origin>[^\r\n]+)\n入手可能な謎めいたエネルギー物質。\nクヴァリスのレソに提示することで\n様々なアイテムと交換できる。",
    "local_trade": r"(?P<local_intro>(?:[^\r\n]+\n)+)特定の場所でアイテムと交換できる。",
    "event": r"対象(?:のイベント|イベントの)期間中\n(?P<event_npc>[^\r\n]+)に提示することで\n様々なアイテムと交換できるチケット。",
    "sale": r"(?P<sale_intro>[^\r\n]+)\n<yellow>(?P<price>[0-9]+)(?P<price_unit>万|)<c>N-メセタで\n売却することができる。",
    "quest_trigger": r"(?P<venue>クエストカウンターで用いるトリガー。|専用のポータルで使用するトリガー。)\n“想定演習：\n(?P<quest>[^\r\n“”]+)”の\nクリア時に消費される。",
    "portal_trigger": r"すべての(?P<color>イエロー|パープル)ポータルに\n対応するトリガー。\nクリア時に消費される。",
    "recycle_trigger": r"アイテムリサイクルで\n“Bトリガー/コモン(?P<color>イエロー|パープル)“\nと交換できる。\n<yellow>※Bトリガーとしては使用不可<c>",
    "class_cube": r"(?P<job>[^\r\n]+)クラスの求道者に\n与えられる特殊な結晶体。\nクラスカウンターで\nアドオンスキルの取得に用いる。",
    "ta": r"クラスカウンターで(?P<ta_type>打撃|射撃|法撃|すべての)武器の\n(?P<ta_level>高度な|さらに高度な|)テックアーツカスタマイズに(?:\n)?用いる。",
    "upgrade": r"特定の(?P<goods>武器|防具|装備)の(?P<purpose>入手と強化|入手|強化)に必要な素材。\nアイテムトレーダーの\n“(?P<menu>[^\r\n“”]+)”で\n(?P=goods)の交換に用いる。",
    "lab_use": r"(?P<lab_intro>[^。]+。)(?:\n)?アイテムラボでの(?:\n)?(?P<lab_use>潜在能力解放など|特殊能力分離|より高度な限界突破|限界突破)に用いる。",
    "refine": r"(?P<refine_intro>[^。]+。)(?:\n)?精錬することで\n(?P<refine_target>[^\r\n]+)に加工される。",
    "grinder": r"武器や防具の加工強化に用いる素材。\n強化を行うことで、限界以上の性能を\n引き出すことができる。",
    "mission_badge": r"アイテムリサイクルで\n交換に使用できるバッヂ。",
    "line_strike_badge": r"ヴィクトリアの\n“ラインストライクカードリサイクル”で\nアイテムの交換に使用できるバッヂ。",
    "master_cube": r"各クラスのさらなる求道者に\n与えられる特殊な結晶体。\nクラスカウンターで、強力な\nアドオンスキルの取得に用いる。",
    "mars": r"M\.A\.R\.S\.の能力向上用デバイス。\nクラスカウンターの\n“M\.A\.R\.S\.スキルポイント交換”で\nスキルポイントと交換できる。",
}

# JP text: Qトリガー/{quest} / Bトリガー/{quest}
tool_quest_name_patterns = [
    r"[QB]\. Trigger/(?P<quest>.+)",
    r"(?:Q 트리거|B트리거)/(?P<quest>.+)",
    "",
    r"[QB]觸發器/(?P<quest>.+)",
    "Q\\. Trigger/(?P<quest>.+)",
]

tool_menu_source_formats = {
    "weapon_upgrade": r"(?P<name>.+)武器強化",
    "armor_upgrade": r"(?P<name>.+)防具強化",
    "weapon_exchange": r"(?P<name>.+)武器交換",
    "exchange": r"(?P<name>.+)交換",
}

tool_menu_name_patterns = {
    "whole": (r"", [r"(?P<name>.+)", r"(?P<name>.+)", "", r"(?P<name>.+)", "(?P<name>.+)"]),
    "badge_variant": (r"[A-ZＡ-Ｚ]", [
        r"(?P<name>.+?)[ ]?[A-ZＡ-Ｚ]", r"(?P<name>.+?)[ ]?[A-ZＡ-Ｚ]", "", r"(?P<name>.+?)[ ]?[A-ZＡ-Ｚ]",
        "(?P<name>.+?)[ ]?[A-ZＡ-Ｚ]",
    ]),
    "badge": (r"バッヂ(?:（[^）]+）)?", [
        r"(?P<name>.+?) Badge(?: \([^)]*\))?",
        r"(?P<name>.+?) 배지(?:（[^）]*）)?",
        "",
        r"(?P<name>.+?)徽章(?:（[^）]*）)?",
        "(?P<name>.+?) Badge(?: \\([^)]*\\))?",
    ]),
    "vance": (r"ヴァンス", [
        r"(?P<name>.+?)(?:avance|vance)", r"(?P<name>.+?) 반스", "", r"(?P<name>.+?)進階零件",
        "",
    ]),
    "volt": (r"ヴォルト[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]*", [
        r"(?P<name>.+?)volt(?: [IVX]+)?", r"(?P<name>.+?) 볼트[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]*", "", r"(?P<name>.+?)變轉零件[0-9]*",
        "",
    ]),
    "integra": (r"インテグラ", [
        r"(?P<name>.+?) Integra", r"(?P<name>.+?) 인테그라", "", r"(?P<name>.+?)元件",
        "",
    ]),
    "cube": (r"キューブ", [
        r"(?P<name>.+?) Cube", r"(?P<name>.+?) 큐브", "", r"(?P<name>.+?)方塊",
        "",
    ]),
}

tool_preparation_name_patterns = {
    "expedition": [
        r"(?:.+? )?(?P<menu_head>Expedition(?: Preparation| Prep\.)?) (?P<menu_kind>Special (?:Ticket|Emblem))",
        r"(?:.+? )?(?P<menu_head>원정 준비) (?P<menu_kind>특별권)",
        "",
        r"(?:.+)?(?P<menu_head>遠征準備)(?P<menu_kind>特別票)",
        "(?:.+? )?(?P<menu_head>Expedition) (?P<menu_kind>Special Ticket)",
    ],
    "preparation": [
        r"(?P<menu_head>.+?) (?P<menu_kind>Special (?:Ticket|Emblem))",
        r"(?P<menu_head>.+ 준비) (?P<menu_kind>특별권)",
        "",
        r"(?P<menu_head>.+準備)(?P<menu_kind>特別票)",
        "(?P<menu_head>Expedition) (?P<menu_kind>Special Ticket)",
    ],
    "development": [
        r"(?:.+? )?(?P<menu_head>Development (?:Preparation|Prep\.)) (?P<menu_kind>Special (?:Ticket|Emblem))",
        r"(?:.+? )?(?P<menu_head>개발 준비) (?P<menu_kind>특별권)",
        "",
        r"(?:.+)?(?P<menu_head>開發準備)(?P<menu_kind>特別票)",
        "",
    ],
}

tool_source_words = {
    "revive_hp": {"half": "半分", "full": "最大"},
    "scratch": {"ac": "AC", "sg": "SG"},
    "trade_intro": {
        "none": "",
        "gigas": "ギガンティクスなどの複合装甲の一部。\n",
        "aegis": "ダークファルス・エイジスの基幹部品。\n",
        "leciel_inside": "ルシエル内部で入手可能な複合素材の一部。\n",
        "leciel": "ルシエルなどで入手可能な複合素材の一部。\n",
        "arks_badge": "活躍したアークスに贈られるバッヂ。\n",
        "arks_proof": "活躍したアークスに贈られる証。\n",
        "weapons_badge": "表面に特徴的な紋章が刻印されたバッヂ。\n",
    },
    "menu": {"legacy": "レガシーアイテム交換", "equipment_upgrade": "装備アップグレード", "equipment_upgrade2": r"装備アップグレード(?P<stage>[Ⅰ-Ⅿ]+)", "legendary3": r"レジェンダリー(?P<rarity>[0-9０-９]+)武器へ強化"},
    "goods": {"items": "アイテム", "weapons_etc": "武器など", "star_weapons": "★{rarity}武器など", "weapons": "武器", "armor": "防具", "equipment": "装備"},
    "leso_origin": {"ancient": "エンシェントエネミーなどから", "kvaris_trials": "クヴァリスでのトライアルなどで", "dread": "ドレッドエネミーなどから"},
    "local_intro": {
        "aelio_badge": "エアリオの紋章が刻印されたバッヂ。\n",
        "team_badge": "チームへの貢献者に贈られるバッヂ。\n",
        "manga_memory": "表面に特徴的なイラストが描かれた\n謎の記憶媒体。\n",
    },
    "event_npc": {"item_trader": "アイテムトレーダー", "xitrae": "シトレー", "phenomena_researcher": "アークス特異現象研究員"},
    "sale_intro": {
        "reactor": "なんらかの機械の動力炉。",
        "snow": "氷雪で磨かれたとされる石。",
        "meteor": "流星雨のときに降り注いだとされる石。",
        "broken_reactor": "破損したなんらかの機械の動力炉。",
    },
    "venue": {"quest_counter": "クエストカウンターで用いるトリガー。", "special_portal": "専用のポータルで使用するトリガー。"},
    "color": {"yellow": "イエロー", "purple": "パープル"},
    "job": {
        "hunter": "ハンター",
        "ranger": "レンジャー",
        "force": "フォース",
        "fighter": "ファイター",
        "gunner": "ガンナー",
        "techter": "テクター",
        "braver": "ブレイバー",
        "bouncer": "バウンサー",
        "waker": "ウェイカー",
        "slayer": "スレイヤー",
    },
    "ta_type": {"striking": "打撃", "shooting": "射撃", "tech": "法撃", "all": "すべての"},
    "ta_level": {"normal": "", "advanced": "高度な", "very_advanced": "さらに高度な"},
    "purpose": {"upgrade": "強化", "obtain_upgrade": "入手と強化", "obtain": "入手"},
    "lab_intro": {
        "ex_cube": "さらなる力の求道者に\n与えられる特殊な結晶体。",
        "refiner": "ストラグメントから精錬される素材。",
        "advanced_refiner": "戦闘セクションなどで\n入手可能な素材。",
        "capsule_remover": "カプタンなどから入手可能な加工具。",
    },
    "lab_use": {"potential": "潜在能力解放など", "limit": "限界突破", "advanced_limit": "より高度な限界突破", "detach": "特殊能力分離"},
    "refine_intro": {"stragments": "戦闘セクションなどで入手可能な\n複合装甲のかけら。", "master": "マスターキューブのかけら。"},
    "refine_target": {"arms_refiner": "アームズリファイナー", "master_cube": "N-マスターキューブ"},
}

tool_revive_hp_names = {
    # JP text: 半分
    "half": ["half", "절반인", "", "一半", "ครึ่งหนึ่ง"],
    # JP text: 最大
    "full": ["full", "가득 찬", "", "最大", "เต็มสูงสุด"],
}

tool_scratch_names = {
    # JP text: AC
    "ac": ["AC", "AC", "", "AC", "AC"],
    # JP text: SG
    "sg": ["SG", "SG", "", "SG", "SG"],
}

tool_trade_intro_names = {
    # JP text: ""
    "none": ["", "", "", "", ""],
    # JP text: ギガンティクスなどの複合装甲の一部。
    "gigas": [
        ("A fragment of plating from a Gigantix.\n"),
        ("기간틱스 등의 복합 장갑의 일부.\n"),
        (""),
        ("絕巨體等敵人複合裝甲的一部分。\n"),
        ("ชิ้นส่วนเกราะคอมโพสิตจาก Gigantix\n"),
    ],
    # JP text: ダークファルス・エイジスの基幹部品。
    "aegis": [
        ("A keystone component of Dark Falz\n"
         "Aegis. "),
        ("다크 펄스 에이지스의 핵심 부품.\n"),
        (""),
        ("黑暗法爾斯·神盾的基礎部件。\n"),
        ("ชิ้นส่วนโครงสร้างหลักของ Dark Falz Aegis\n"),
    ],
    # JP text: ルシエル内部で入手可能な複合素材の一部。
    "leciel_inside": [
        ("Composite material found in Leciel.\n"),
        ("루시엘 내부에서 얻을 수 있는 복합 소재의 일부.\n"),
        (""),
        ("可於天堡內部獲得的複合素材的一部分。\n"),
        ("ชิ้นส่วนวัตถุดิบคอมโพสิตที่หาได้ภายใน Leciel\n"),
    ],
    # JP text: ルシエルなどで入手可能な複合素材の一部。
    "leciel": [
        ("Composite material found in Leciel.\n"),
        ("루시엘 등에서 얻을 수 있는 복합 소재의 일부.\n"),
        (""),
        ("可於天堡等處獲得的複合素材的一部分。\n"),
        ("ชิ้นส่วนวัตถุดิบคอมโพสิตที่หาได้จาก Leciel และแหล่งอื่น ๆ\n"),
    ],
    # JP text: 活躍したアークスに贈られるバッヂ。
    "arks_badge": [
        ("Badge given to accomplished ARKS.\n"),
        ("활약한 아크스에게 주는 배지.\n"),
        (""),
        ("贈予活躍ARKS的徽章。\n"),
        ("เข็มกลัดที่มอบให้แก่ ARKS ผู้สร้างผลงานยอดเยี่ยม\n"),
    ],
    # JP text: 活躍したアークスに贈られる証。
    "arks_proof": [
        ("Insignia given to accomplished ARKS.\n"),
        ("활약한 아크스에게 주는 증표.\n"),
        (""),
        ("賜予活躍ARKS的證明。\n"),
        ("หลักฐานที่มอบให้แก่ ARKS ผู้สร้างผลงานยอดเยี่ยม\n"),
    ],
    # JP text: 表面に特徴的な紋章が刻印されたバッヂ。
    "weapons_badge": [
        ("A badge bearing a distinctive crest.\n"),
        ("표면에 독특한 상징 문양이 새겨진 배지.\n"),
        (""),
        ("正面銘刻著獨特紋章的徽章。\n"),
        ("Badge ที่มีตราสัญลักษณ์อันโดดเด่นสลักอยู่บนผิวหน้า\n"),
    ],
}

tool_menu_names = {
    # JP text: レガシーアイテム交換
    "legacy": ["Legacy Item Exchange", "레거시 아이템 교환", "", "經典道具交換", "Legacy SG Fashion Exchange"],
    # JP text: 装備アップグレード
    "equipment_upgrade": ["Equipment Upgrade", "장비 업그레이드", "", "裝備升級", "Equipment Upgrade"],
    # JP text: 装備アップグレード{stage}
    "equipment_upgrade2": ["Equipment Upgrade {stage_roman}", "장비 업그레이드{stage}", "", "裝備升級{stage_number}", "Equipment Upgrade {stage_roman}"],
    # JP text: レジェンダリー{rarity}武器へ強化
    "legendary3": ["Legendary {rarity} Weapon Upgrade", "레전더리 {rarity} 무기로 강화", "", "強化至傳奇{rarity}武器", "Upgrade to Legendary {rarity} Weapons"],
}

tool_menu_formats = {
    # JP text: {name}交換
    "exchange": ["{name} Exchange", "{name} 교환", "", "{name}交換", "{name} Exchange"],
    # JP text: {name}武器交換
    "weapon_exchange": ["{name} Weapon Exchange", "{name} 무기 교환", "", "{name}武器交換", "{name} Weapon Exchange"],
    # JP text: {name}武器強化
    "weapon_upgrade": ["{name} Weapon Upgrade", "{name} 무기 강화", "", "{name}武器強化", "{name} Weapon Enhancement"],
    # JP text: {name}防具強化
    "armor_upgrade": ["{name} Armor Upgrade", "{name} 방어구 강화", "", "{name}防具強化", "{name} Armor Enhancement"],
}

tool_goods_names = {
    # JP text: アイテム
    "items": ["items", "아이템", "", "道具", "ไอเทมต่าง ๆ"],
    # JP text: 武器など
    "weapons_etc": ["items like weapons", "무기 등", "", "武器等", "อาวุธและไอเทมอื่น ๆ"],
    # JP text: ★{rarity}武器など
    "star_weapons": [
        ("items like {rarity}-star weapons"),
        ("★{rarity} 무기 등"),
        (""),
        ("★{rarity}武器等"),
        ("อาวุธระดับ ★{rarity} และอื่น ๆ"),
    ],
    # JP text: 武器
    "weapons": ["weapons", "무기", "", "武器", "อาวุธ"],
    # JP text: 防具
    "armor": ["armor", "방어구", "", "防具", "ชุดเกราะ"],
    # JP text: 装備
    "equipment": ["equipment", "장비", "", "裝備", "อุปกรณ์"],
}

tool_leso_origin_names = {
    # JP text: エンシェントエネミーなどから
    # 入手可能な謎めいたエネルギー物質。
    "ancient": [
        ("A strange energy core obtainable\n"
         "from Ancient Enemies & more."),
        ("에인션트 에너미 등에게서\n"
         "얻을 수 있는 수수께끼의 에너지 물질."),
        (""),
        ("可以從遠古型敵人等處獲得的\n"
         "神秘能量物質。"),
        ("Ancient Enemy และแหล่งอื่น ๆ"),
    ],
    # JP text: クヴァリスでのトライアルなどで
    # 入手可能な謎めいたエネルギー物質。
    "kvaris_trials": [
        ("Odd energy from Kvaris Trials, etc."),
        ("크바리스의 트라이얼 등에서\n"
         "얻을 수 있는 수수께끼의 에너지 물질."),
        (""),
        ("可以從克瓦利斯的突發試煉等處獲得的\n"
         "神秘能量物質。"),
        ("Trial ใน Kvaris และแหล่งอื่น ๆ"),
    ],
    # JP text: ドレッドエネミーなどから
    # 入手可能な謎めいたエネルギー物質。
    "dread": [
        ("A strange energy core obtainable\n"
         "from Dread Enemies & more."),
        ("드레드 에너미 등에게서\n"
         "얻을 수 있는 수수께끼의 에너지 물질."),
        (""),
        ("可以從兇惡型敵人等處獲得的\n"
         "神秘能量物質。"),
        ("Dread Enemy และแหล่งอื่น ๆ"),
    ],
}

tool_local_intro_names = {
    # JP text: エアリオの紋章が刻印されたバッヂ。
    "aelio_badge": [
        ("A badge engraved with the emblem\n"
         "of Aelio. "),
        ("에아리오의 문양이 새겨진 뱃지.\n"),
        (""),
        ("銘刻著艾亞利奧紋章的徽章。\n"),
        ("เข็มกลัดที่สลักตราสัญลักษณ์แห่ง Aelio เอาไว้\n"),
    ],
    # JP text: チームへの貢献者に贈られるバッヂ。
    "team_badge": [
        ("A badge awarded to those who\n"
         "contribute to their Team. "),
        ("팀에 공헌한 사람에게 주는 배지.\n"),
        (""),
        ("贈予為公會做出貢獻之人的徽章。\n"),
        ("เข็มกลัดที่มอบให้แก่ผู้มีส่วนร่วมอุทิศตนเพื่อ Team\n"),
    ],
    # JP text: 表面に特徴的なイラストが描かれた
    # 謎の記憶媒体。
    "manga_memory": [
        ("Strange data storage device that\n"
         "displays distinct illustrations. "),
        ("앞면에 특징적인 일러스트가 그려진\n"
         "수수께끼의 기억 매체.\n"),
        (""),
        ("正面畫著獨特插圖的\n"
         "神秘記憶媒體。\n"),
        ("สื่อบันทึกข้อมูลปริศนาที่มีภาพวาดอันเป็นเอกลักษณ์อยู่บนพื้นผิว\n"),
    ],
}

tool_event_npc_names = {
    # JP text: アイテムトレーダー
    "item_trader": ["an item trader", "아이템 트레이더", "", "道具交易商", "Item Trader"],
    # JP text: シトレー
    "xitrae": ["Xitrae", "시트레", "", "希特蕾", "Xitrae"],
    # JP text: アークス特異現象研究員
    "phenomena_researcher": ["ARKS Researcher of Strange Phenomena", "아크스 특이 현상 연구원", "", "ARKS特異現象研究員", "นักวิจัยปรากฏการณ์พิเศษ ARKS"],
}

tool_sale_intro_names = {
    # JP text: なんらかの機械の動力炉。
    "reactor": [
        ("A power core from some kind of\n"
         "machine. "),
        ("어떤 기계의 동력로."),
        (""),
        ("某種機械的動力爐。"),
        ("เตาปฏิกรณ์พลังงานของเครื่องจักรบางอย่าง"),
    ],
    # JP text: 氷雪で磨かれたとされる石。
    "snow": [
        ("A stone that has been polished\n"
         "by ice and snow. "),
        ("얼음과 눈에 의해 연마되었다고 하는 돌."),
        (""),
        ("據說是被冰雪磨礪過的石頭。"),
        ("หินที่กล่าวกันว่าได้รับการขัดเกลาจากหิมะและน้ําแข็ง"),
    ],
    # JP text: 流星雨のときに降り注いだとされる石。
    "meteor": [
        ("A stone said to have appeared\n"
         "during a meteor shower.\n"),
        ("유성우가 내릴 때 쏟아졌다고 전해지는 돌."),
        (""),
        ("據說是流星雨時落下的石頭。"),
        ("หินที่กล่าวกันว่าตกลงมาพร้อมกับฝนดาวตก"),
    ],
    # JP text: 破損したなんらかの機械の動力炉。
    "broken_reactor": [
        ("A power core from some kind of\n"
         "a broken machine.\n"),
        ("손상된 어떤 기계의 동력로."),
        (""),
        ("破損了的某種機械的動力爐。"),
        ("เตาปฏิกรณ์พลังงานของเครื่องจักรที่ชํารุดเสียหาย"),
    ],
}

tool_venue_names = {
    # JP text: クエストカウンターで用いるトリガー。
    "quest_counter": ["Trigger used at Quest Counters.", "퀘스트 카운터에서 사용하는 트리거.", "", "在任務櫃檯處使用的觸發器。", "Trigger สําหรับใช้งานที่ Quest Counter"],
    # JP text: 専用のポータルで使用するトリガー。
    "special_portal": ["A Trigger used with special Portals.", "전용 포털에서 사용하는 트리거.", "", "在專用傳送陣處使用的觸發器。", "Trigger สําหรับใช้งานที่พอร์ทัลเฉพาะ"],
}


tool_color_names = {
    # JP text: イエロー
    "yellow": ["Yellow", "옐로", "", "黃", "Yellow"],
    # JP text: パープル
    "purple": ["Purple", "퍼플", "", "紫", "Purple"],
}

tool_job_names = {
    # JP text: ハンター
    "hunter": ["Hunters", "헌터", "", "獵人(Hu)", "Hunter"],
    # JP text: レンジャー
    "ranger": ["Rangers", "레인저", "", "遊俠(Ra)", "Ranger"],
    # JP text: フォース
    "force": ["Forces", "포스", "", "法師(Fo)", "Force"],
    # JP text: ファイター
    "fighter": ["Fighters", "파이터", "", "鬥士(Fi)", "Fighter"],
    # JP text: ガンナー
    "gunner": ["Gunners", "거너", "", "鷹眼(Gu)", "Gunner"],
    # JP text: テクター
    "techter": ["Techters", "텍터", "", "元素使(Te)", "Techter"],
    # JP text: ブレイバー
    "braver": ["Bravers", "브레이버", "", "武士(Br)", "Braver"],
    # JP text: バウンサー
    "bouncer": ["Bouncers", "바운서", "", "凌客(Bo)", "Bouncer"],
    # JP text: ウェイカー
    "waker": ["Wakers", "웨이커", "", "喚士(Wa)", "Waker"],
    # JP text: スレイヤー
    "slayer": ["Slayers", "슬레이어", "", "殺手(Sl)", "Slayer"],
}

tool_ta_type_names = {
    # JP text: 打撃
    "striking": ["striking", "타격", "", "打擊", "อาวุธประเภทโจมตีระยะประชิด Striking"],
    # JP text: 射撃
    "shooting": ["shooting", "사격", "", "射擊", "อาวุธประเภทโจมตีระยะไกล Ranged"],
    # JP text: 法撃
    "tech": ["Tech", "법격", "", "法擊", "อาวุธประเภทเวท Tech"],
    # JP text: すべての
    "all": ["all", "모든", "", "所有", "อาวุธทุกประเภท"],
}

tool_ta_level_names = {
    # JP text: ""
    "normal": ["", "", "", "", ""],
    # JP text: 高度な
    "advanced": ["advanced ", "고급 ", "", "高度的", "ระดับสูง"],
    # JP text: さらに高度な
    "very_advanced": ["very advanced ", "한층 더 높은 수준의 ", "", "更為高度的", "ขั้นสูงยิ่งขึ้น"],
}

tool_purpose_names = {
    # JP text: 強化
    "upgrade": ["upgrading", "강화", "", "強化", "การอัปเกรด"],
    # JP text: 入手と強化
    "obtain_upgrade": ["obtaining and upgrading", "얻고 강화", "", "獲得與強化", "การรับและอัปเกรด"],
    # JP text: 入手
    "obtain": ["obtaining", "획득", "", "獲得", "การรับ"],
}

tool_lab_intro_names = {
    # JP text: さらなる力の求道者に
    # 与えられる特殊な結晶体。
    "ex_cube": [
        ("A special crystal given to those who\n"
         "seek further strength. "),
        ("더 큰 힘을 추구하는 자에게\n"
         "주어지는 특수한 결정체.\n"),
        (""),
        ("一種特殊的結晶體，會賦予給\n"
         "追求更為強大力量的求道者。\n"),
        ("ผลึกพิเศษที่มอบให้แก่ผู้แสวงหาพลังที่ยิ่งใหญ่กว่า"),
    ],
    # JP text: ストラグメントから精錬される素材。
    "refiner": [
        ("A material created by refining\n"
         "Stragments. "),
        ("스트래그먼트를 제련해 얻는 소재.\n"),
        (""),
        ("從鬥爭碎片中精煉出的素材。\n"),
        ("วัตถุดิบที่หลอมสกัดขึ้นมาจาก Stragment"),
    ],
    # JP text: 戦闘セクションなどで
    # 入手可能な素材。
    "advanced_refiner": [
        ("Material obtained in the Combat\n"
         "Sectors & elsewhere.\n"),
        ("전투 섹션 등에서\n"
         "얻을 수 있는 재료. "),
        (""),
        ("可在戰鬥區域等地獲得的素材。\n"),
        ("วัตถุดิบที่หาได้จาก Combat Sector และพื้นที่อื่น ๆ"),
    ],
    # JP text: カプタンなどから入手可能な加工具。
    "capsule_remover": [
        ("Manufacturing tool from Captan etc.\n"),
        ("캡탄 등에게서 얻을 수 있는 가공 도구.\n"),
        (""),
        ("可以從膠囊仔等處獲得的加工用具。\n"),
        ("เครื่องมือแปรรูปที่หาได้จาก Captan และแหล่งอื่น ๆ"),
    ],
}

tool_lab_use_names = {
    # JP text: 潜在能力解放などに用いる。
    "potential": ["used to unlock Potentials and more", "잠재 능력 해방 등에 사용한다.", "", "用於解放潛在能力等。", "ใช้สําหรับการปลดปล่อย Potential ของอาวุธ\nและอื่น ๆ ที่ Item Lab"],
    # JP text: 限界突破に用いる。
    "limit": ["used to break item limits", "한계 돌파에 사용한다.", "", "用於界限突破。", "ใช้สําหรับการทะลวงขีดจํากัด (Limit Break) อุปกรณ์ที่ Item Lab"],
    # JP text: より高度な限界突破に用いる。
    "advanced_limit": ["used for advanced limit breaking", "더 높은 수준의 한계 돌파에 사용한다.", "", "用於更為高階的界限突破。", "ใช้สําหรับการทะลวงขีดจํากัด (Limit Break) อุปกรณ์ขั้นสูง\nที่ Item Lab"],
    # JP text: 特殊能力分離に用いる。
    "detach": [
        ("used to detach\n"
         "Special Abilities from equipment"),
        ("특수 능력 분리에 사용한다."),
        (""),
        ("用於分離特殊能力。"),
        ("ใช้สําหรับการแยก Special Ability ออกจากอุปกรณ์\n"
         "ที่ Item Lab"),
    ],
}

tool_refine_intro_names = {
    # JP text: 戦闘セクションなどで入手可能な
    # 複合装甲のかけら。
    "stragments": [
        ("A fragment of composite plating\n"
         "found in Combat Areas. "),
        ("전투 섹션 등에서 얻을 수 있는\n"
         "복합 장갑 조각. "),
        (""),
        ("可在戰鬥區域等地獲得的\n"
         "複合裝甲的碎片。"),
        ("ชิ้นส่วนเกราะผสมที่หาได้จาก Combat Sector และพื้นที่อื่น ๆ"),
    ],
    # JP text: マスターキューブのかけら。
    "master": [
        ("A fragment of a Master Cube.\n"),
        ("마스터 큐브의 조각.\n"),
        (""),
        ("大師方塊的碎片。"),
        ("เศษเสี้ยวของ Master Cube"),
    ],
}

tool_refine_target_names = {
    # JP text: アームズリファイナー
    "arms_refiner": ["an Arms Refiner", "암즈 리파이너", "", "武裝精煉塊", "Arms Refiner"],
    # JP text: N-マスターキューブ
    "master_cube": ["a N-Master Cube", "N-마스터 큐브", "", "N-大師方塊", "N-Master Cube"],
}

tool_word_translations = {
    "revive_hp": tool_revive_hp_names,
    "scratch": tool_scratch_names,
    "trade_intro": tool_trade_intro_names,
    "goods": tool_goods_names,
    "leso_origin": tool_leso_origin_names,
    "local_intro": tool_local_intro_names,
    "event_npc": tool_event_npc_names,
    "sale_intro": tool_sale_intro_names,
    "venue": tool_venue_names,
    "color": tool_color_names,
    "job": tool_job_names,
    "ta_type": tool_ta_type_names,
    "ta_level": tool_ta_level_names,
    "purpose": tool_purpose_names,
    "lab_intro": tool_lab_intro_names,
    "lab_use": tool_lab_use_names,
    "refine_intro": tool_refine_intro_names,
    "refine_target": tool_refine_target_names,
}

tool_desc_formats = {
    # JP text: 所持者が戦闘不能になったときに
    # 使用可能な蘇生デバイス。
    # HPが{revive_hp}の状態で復活する。
    "revive": [
        ("A revival device that can be used\n"
         "when its owner is incapacitated.\n"
         "Revives you with {revive_hp} HP."),
        ("소지자가 전투 불능이 되었을 때\n"
         "사용할 수 있는 소생 장치.\n"
         "HP가 {revive_hp} 상태로 부활한다."),
        (""),
        ("可在持有者無法戰鬥時使用的復活裝置。\n"
         "會以{revive_hp}HP的狀態復活。"),
        ("อุปกรณ์ชุบชีวิตที่สามารถใช้งานได้\n"
         "เมื่อผู้ครอบครองตกอยู่ในสถานะไม่สามารถต่อสู้ได้\n"
         "จะฟื้นคืนชีพกลับมาด้วย HP {revive_hp}"),
    ],
    # JP text: アイテムリサイクルで
    # {scratch}スクラッチアイテムと同等品として
    # 交換に使用できるバッヂ。
    "recycle_equal": [
        ("A badge that can be treated as an\n"
         "{scratch} Scratch item when making trades\n"
         "at the Recycle Shop."),
        ("아이템 리사이클에서\n"
         "{scratch} 스크래치 아이템과 동등한 교환 재료로\n"
         "사용할 수 있는 뱃지."),
        (""),
        ("可在道具回收中\n"
         "被視為{scratch}轉蛋道具的等價品\n"
         "用於交換的徽章。"),
        ("เข็มกลัดที่ใช้แลกเปลี่ยนในระบบ Item Recycle\n"
         "โดยสามารถใช้เทียบเท่ากับ\n"
         "ไอเทมจาก {scratch} Scratch ได้"),
    ],
    # JP text: {venue}
    # “想定演習：
    # {quest}”の
    # クリア時に消費される。
    "quest_trigger": [
        ("{venue}\n"
         "Consumed upon clearing the Quest\n"
         "\"Simulation:\n"
         "{quest}\"."),
        ("{venue}\n"
         "“모의 훈련：\n"
         "{quest}”\n"
         "클리어 시 소모된다."),
        (""),
        ("{venue}\n"
         "會在完成“設想演習: \n"
         "{quest}”時消耗。"),
        ("{venue}\n"
         "จะถูกใช้ไปเมื่อเคลียร์เควสต์จําลอง\n"
         "\"Simulation: {quest}\" สําเร็จ"),
    ],
    # JP text: すべての{color}ポータルに
    # 対応するトリガー。
    # クリア時に消費される。
    "portal_trigger": [
        ("Trigger used at all {color} Portals.\n"
         "Consumed upon clearing the Quest."),
        ("모든 {color} 포털에\n"
         "대응하는 트리거.\n"
         "클리어하면 소모된다."),
        (""),
        ("適用於所有{color}色傳送陣的觸發器。\n"
         "會在完成時消耗。"),
        ("Trigger ที่สามารถใช้งานได้กับ {color} Portal ทั้งหมด\n"
         "จะถูกใช้ไปเมื่อเคลียร์เควสต์สําเร็จ"),
    ],
    # JP text: アイテムリサイクルで
    # “Bトリガー/コモン{color}“
    # と交換できる。
    # <yellow>※Bトリガーとしては使用不可<c>
    "recycle_trigger": [
        ("Can be exchanged for \"B. Trigger/\n"
         "Common {color}\" at Item Recycling.\n"
         "<yellow>※Cannot be used as a Battle Trigger.<c>"),
        ("아이템 리사이클에서\n"
         "\"B트리거/커먼 {color}\"로 교환할 수 있다.\n"
         "<yellow>※B트리거로는 사용 불가.<c>"),
        (""),
        ("可在道具回收中\n"
         "交換“B觸發器/通用{color}”。\n"
         "<yellow>※不可作為B觸發器使用<c>"),
        ("สามารถนําไปแลกเป็น \"B. Trigger/Common {color}\"\n"
         "ได้ที่ Item Recycle\n"
         "<yellow>※ไม่สามารถใช้เป็น Battle Trigger ได้<c>"),
    ],
    # JP text: {job}クラスの求道者に
    # 与えられる特殊な結晶体。
    # クラスカウンターで
    # アドオンスキルの取得に用いる。
    "class_cube": [
        ("A special crystal given to {job}\n"
         "who seek strength. Used at Class\n"
         "Counters to create Add-On Skills."),
        ("{job} 클래스의 구도자에게\n"
         "부여되는 특수한 결정체.\n"
         "클래스 카운터에서\n"
         "애드온 스킬 획득에 사용한다."),
        (""),
        ("一種特殊的結晶體，會賦予給\n"
         "{job}職業的求道者。\n"
         "在職業櫃檯中用於獲得附件技能。"),
        ("ผลึกพิเศษที่มอบให้แก่ผู้แสวงหาพลังแห่งคลาส {job}\n"
         "ใช้สําหรับรับ Add-On Skill\n"
         "ที่ Class Counter"),
    ],
    # JP text: {trade_intro}アイテムトレーダーの
    # “{menu}”で
    # {goods}と交換できる。
    "trade": [
        ("{trade_intro}Trade it for {goods} at the Item\n"
         "Trader's {menu}."),
        ("{trade_intro}아이템 트레이더의\n"
         "“{menu}”에서\n"
         "{goods}과 교환할 수 있다."),
        (""),
        ("{trade_intro}可在道具交易商的\n"
         "“{menu}”處交換{goods}。"),
        ("{trade_intro}สามารถนําไปแลกเปลี่ยนเป็น{goods}\n"
         "ได้ที่ \"{menu}\" ของ Item Trader"),
    ],
    # JP text: {leso_origin}
    # クヴァリスのレソに提示することで
    # 様々なアイテムと交換できる。
    "leso": [
        ("{leso_origin}\n"
         "Can be given to Leso in Kvaris\n"
         "in exchange for various items."),
        ("{leso_origin}\n"
         "크바리스의 레소에게 보여 주면\n"
         "다양한 아이템과 교환할 수 있다."),
        (""),
        ("{leso_origin}\n"
         "向克瓦利斯的萊索出示後\n"
         "便可交換各種各樣的道具。"),
        ("สสารพลังงานลึกลับที่หาได้จาก {leso_origin}\n"
         "เมื่อนําไปแสดงต่อ Reso ใน Kvaris\n"
         "จะสามารถแลกเปลี่ยนเป็นไอเทมต่าง ๆ ได้มากมาย"),
    ],
    # JP text: {local_intro}特定の場所でアイテムと交換できる。
    "local_trade": [
        ("{local_intro}Can be traded for items at\n"
         "specific locations."),
        ("{local_intro}특정 장소에서 아이템과 교환할 수 있다."),
        (""),
        ("{local_intro}可在特定地點交換道具。"),
        ("{local_intro}สามารถนําไปแลกเปลี่ยนเป็นไอเทมได้ในสถานที่เฉพาะ"),
    ],
    # JP text: 対象イベントの期間中
    # {event_npc}に提示することで
    # 様々なアイテムと交換できるチケット。
    "event": [
        ("During the corresponding event,\n"
         "this ticket can be given to {event_npc}\n"
         "in exchange for various items."),
        ("해당 이벤트 기간 중에\n"
         "{event_npc}에게 제시하면\n"
         "다양한 아이템과 교환할 수 있는 티켓."),
        (""),
        ("在目標活動期間內\n"
         "向{event_npc}出示後\n"
         "便可交換各種道具的票券。"),
        ("ตั๋วที่สามารถนําไปแสดงต่อ {event_npc} ในช่วงกิจกรรมที่กําหนด\n"
         "เพื่อแลกเปลี่ยนเป็นไอเทมต่าง ๆ ได้มากมาย"),
    ],
    # JP text: {sale_intro}
    # <yellow>{price}<c>N-メセタで
    # 売却することができる。
    "sale": [
        ("{sale_intro}Can be sold for\n"
         "<yellow>{price}<c> N-Meseta."),
        ("{sale_intro}\n"
         "<yellow>{price}<c>N-메세타에\n"
         "판매할 수 있다."),
        (""),
        ("{sale_intro}\n"
         "可以出售為<yellow>{price}<c>N-美賽達。"),
        ("{sale_intro}\n"
         "สามารถนําไปขายได้ในราคา\n"
         "<yellow>{price}<c> N-Meseta"),
    ],
    # JP text: クラスカウンターで{ta_type}武器の
    # {ta_level}テックアーツカスタマイズに用いる。
    "ta": [
        ("Used at the Class Counter to perform\n"
         "{ta_level}Tech Arts Customization for {ta_type}\n"
         "weapons."),
        ("클래스 카운터에서 {ta_type} 무기의\n"
         "{ta_level}테크 아츠 커스터마이즈에 사용한다."),
        (""),
        ("在職業櫃檯中用於對{ta_type}武器\n"
         "進行{ta_level}法術PA自定義。"),
        ("ใช้ที่ Class Counter เพื่อทําการปรับแต่ง{ta_level}\n"
         "Tech Arts Customization\n"
         "สําหรับ{ta_type}"),
    ],
    # JP text: 特定の{goods}の{purpose}に必要な素材。
    # アイテムトレーダーの
    # “{menu}”で
    # {goods}の交換に用いる。
    "upgrade": [
        ("Material for {purpose} specific {goods}.\n"
         "Used when exchanging {goods} at\n"
         "the Item Trader with \"{menu}\"."),
        ("특정 {goods}를 {purpose}하는 데 필요한 소재.\n"
         "아이템 트레이더의\n"
         "“{menu}”에서\n"
         "{goods} 교환에 사용한다."),
        (""),
        ("{purpose}特定{goods}所必須的素材。\n"
         "在道具交易商的\n"
         "“{menu}”處用於交換{goods}。"),
        ("วัตถุดิบจําเป็นสําหรับ{purpose}{goods}เฉพาะ\n"
         "ใช้ในการแลกเปลี่ยน{goods}ผ่านระบบ\n"
         "\"{menu}\" ของ Item Trader"),
    ],
    # JP text: {lab_intro}
    # アイテムラボでの
    # {lab_use}
    "lab_use": [
        ("{lab_intro}Can be {lab_use}\n"
         "at the Item Lab."),
        ("{lab_intro}아이템 랩에서\n"
         "{lab_use}"),
        (""),
        ("{lab_intro}在道具實驗室中{lab_use}"),
        ("{lab_intro}\n"
         "{lab_use}"),
    ],
    # JP text: {refine_intro}精錬することで
    # {refine_target}に加工される。
    "refine": [
        ("{refine_intro}Can be\n"
         "refined into {refine_target}."),
        ("{refine_intro}제련하면\n"
         "{refine_target}로 가공된다."),
        (""),
        ("{refine_intro}\n"
         "精煉後會被加工為{refine_target}。"),
        ("{refine_intro}\n"
         "เมื่อนําไปหลอมสกัด จะสามารถแปรรูป\n"
         "เป็น {refine_target} ได้"),
    ],
    # JP text: 武器や防具の加工強化に用いる素材。
    # 強化を行うことで、限界以上の性能を
    # 引き出すことができる。
    "grinder": [
        ("Material used to improve equipment.\n"
         "The performance of equipment can\n"
         "be pushed beyond its limit."),
        ("무기와 방어구를 가공해 강화하는 소재.\n"
         "강화를 통해 한계를 뛰어넘는\n"
         "성능을 끌어낼 수 있다."),
        (""),
        ("用於武器與防具加工強化的素材。\n"
         "通過強化，可以發揮出\n"
         "超出界限的性能。"),
        ("วัสดุสําหรับใช้เสริมพลังให้อาวุธและชุดเกราะ\n"
         "การเสริมพลังจะช่วยดึงขีดความสามารถของอุปกรณ์\n"
         "ให้ออกมาได้สูงยิ่งกว่าขีดจํากัดเดิม"),
    ],
    # JP text: アイテムリサイクルで
    # 交換に使用できるバッヂ。
    "mission_badge": [
        ("Badges that can be used\n"
         "for exchanges at the Recycle Shop."),
        ("아이템 리사이클에서\n"
         "교환에 사용할 수 있는 배지."),
        (""),
        ("可在道具回收中\n"
         "用於交換的徽章。"),
        ("เข็มกลัดที่สามารถนําไปใช้แลกเปลี่ยนไอเทม\n"
         "ได้ที่ Item Recycle"),
    ],
    # JP text: ヴィクトリアの
    # “ラインストライクカードリサイクル”で
    # アイテムの交換に使用できるバッヂ。
    "line_strike_badge": [
        ("Badges that can be used\n"
         "for exchanges at\n"
         "Victoria's \"Line Strike Recycle Shop\"."),
        ("빅토리아의\n"
         "“라인 스트라이크 카드 리사이클”에서\n"
         "아이템 교환에 사용할 수 있는 배지."),
        (""),
        ("可在贏多利亞的\n"
         "“戰線牌鬥卡牌回收”中\n"
         "用於交換道具的徽章。"),
        ("Badge ที่สามารถนําไปใช้แลกเปลี่ยนไอเทมได้ที่\n"
         "\"Line Strike Card Recycle\" ของ Victoria"),
    ],
    # JP text: 各クラスのさらなる求道者に
    # 与えられる特殊な結晶体。
    # クラスカウンターで、強力な
    # アドオンスキルの取得に用いる。
    "master_cube": [
        ("A special crystal given to those who\n"
         "seek further strength in their Class.\n"
         "Used at the Class Counter to create\n"
         "powerful Add-On Skills."),
        ("각 클래스에서 더 높은 경지를 추구하는 자에게\n"
         "주어지는 특수한 결정체.\n"
         "클래스 카운터에서 강력한\n"
         "애드온 스킬 습득에 사용한다."),
        (""),
        ("一種特殊的結晶體，會賦予給\n"
         "追求各個職業更進一步的求道者。\n"
         "在職業櫃檯用於獲得強力的附件技能。"),
        ("ผลึกพิเศษที่มอบให้แก่ผู้แสวงหาความแข็งแกร่งยิ่งขึ้นในแต่ละคลาส\n"
         "ใช้สําหรับเรียนรู้ Add-On Skill อันทรงพลัง\n"
         "ได้ที่ Class Counter"),
    ],
    # JP text: M.A.R.S.の能力向上用デバイス。
    # クラスカウンターの
    # “M.A.R.S.スキルポイント交換”で
    # スキルポイントと交換できる。
    "mars": [
        ("A device that improves M.A.R.S. abilities.\n"
         "Can be exchanged for \"M.A.R.S. Skill\n"
         "Points\" at the Class Counter."),
        ("M.A.R.S.의 능력 향상용 장치.\n"
         "클래스 카운터의\n"
         "“M.A.R.S. 스킬 포인트 교환”에서\n"
         "스킬 포인트와 교환할 수 있다."),
        (""),
        ("用於提升M.A.R.S.能力的裝置。\n"
         "可在職業櫃檯的\n"
         "“交換M.A.R.S.技能點數”處\n"
         "交換技能點數。"),
        ("Device สําหรับพัฒนาความสามารถของ M.A.R.S.\n"
         "สามารถนําไปแลกเป็น Skill Point ได้ที่\n"
         "\"M.A.R.S. Skill Point Exchange\" ของ Class Counter"),
    ],
}

# JP text: {trade_intro}アイテムトレーダーの
# “{menu}”で
# {goods}と交換できる。
tool_preparation_formats = [
    ("{trade_intro}Trade it for {goods}\n"
     "at the Item Trader's {menu_head}\n"
     "{menu_kind} Exchange."),
    ("{trade_intro}아이템 트레이더의\n"
     "“{menu_head} {menu_kind} 교환”에서\n"
     "{goods}과 교환할 수 있다."),
    (""),
    ("{trade_intro}可在道具交易商的\n"
     "“{menu_head}{menu_kind}交換”處\n"
     "交換{goods}。"),
    ("{trade_intro}สามารถนําไปแลกเป็น{goods}ได้ที่\n"
     "เมนู \"แลกตั๋วพิเศษเตรียมการสํารวจ\" ของ Item Trader"),
]

# JP text: 万
tool_price_units = ["", "만", "", "萬", "0,000"]

tool_special_prices = {
    # JP text: 100万
    "million": ["1 Million", "100만", "", "100萬", "1,000,000"],
}
# [FUNCTION] Derive a menu from this item's translated name, or use an unrelated fixed menu.
def get_tool_menu_name(item, name_prefix, source):
    for menu_type, pattern in tool_menu_source_formats.items():
        menu = regex.fullmatch(pattern, source)
        if menu is None or not item["jp_text"].startswith(menu["name"]):
            continue
        suffix = item["jp_text"][len(menu["name"]):]
        for source_pattern, patterns in tool_menu_name_patterns.values():
            if regex.fullmatch(source_pattern, suffix) is None:
                continue
            parts = get_item_name_parts(item, name_prefix, patterns)
            template = tool_menu_formats[menu_type][LANG]
            if parts is None or not template:
                return None
            return template.format(**parts)
        return None

    for code, pattern in tool_source_words["menu"].items():
        match = regex.fullmatch(pattern, source)
        if match is None:
            continue
        template = tool_menu_names[code][LANG]
        if not template:
            return None
        values = match.groupdict()
        if "stage" in values:
            numbers = [int(unicodedata.numeric(char)) for char in values["stage"]]
            values["stage_number"] = sum(-number if number < following else number
                                         for number, following in zip(numbers, numbers[1:] + [0]))
            values["stage_roman"] = unicodedata.normalize("NFKC", values["stage"])
        if "rarity" in values:
            values["rarity"] = values["rarity"].translate(chartable[0])
        return template.format(**values)
    return None


# [FUNCTION] Render the complete JP Tool mechanism with canonical same-language terms.
def translate_tool_desc(item, file_name, name_prefix):
    if "jp_explain" not in item:
        return -4
    description = match_description(item, tool_source_formats, {})
    if description is None:
        return -4
    desc_sort, fields, _ = description

    problem = get_translation_problem(item)
    if problem:
        return problem
    preparation = desc_sort == "trade" and fields["menu"].endswith("準備特別票交換")
    desc_format = tool_preparation_formats[LANG] if preparation else tool_desc_formats[desc_sort][LANG]
    if not desc_format:
        return -5

    values = {}
    rarity = fields.pop("rarity", None)
    if rarity is not None:
        fields["goods"] = "★{rarity}武器など"
    if desc_sort == "quest_trigger":
        quest = fields.pop("quest")
        if not item["jp_text"].endswith("/" + quest):
            return -5
        parts = get_item_name_parts(item, name_prefix, tool_quest_name_patterns)
        if parts is None:
            return -5
        values["quest"] = parts["quest"]
    if "menu" in fields:
        menu = fields.pop("menu")
        if preparation:
            menu_name = menu[:-len("交換")]
            if menu_name not in item["jp_text"]:
                return -5
            if menu_name == item["jp_text"]:
                name_type = "preparation"
            elif menu_name == "遠征準備特別票":
                name_type = "expedition"
            elif menu_name == "開発準備特別票":
                name_type = "development"
            else:
                return -5
            parts = get_item_name_parts(item, name_prefix, tool_preparation_name_patterns[name_type])
            if parts is None:
                return -5
            values.update(parts)
        else:
            name = get_tool_menu_name(item, name_prefix, menu)
            if name is None:
                return -5
            values["menu"] = name
    if desc_sort == "sale":
        price, unit = fields.pop("price"), fields.pop("price_unit")
        if unit == "万":
            if price == "100":
                price = tool_special_prices["million"][LANG]
                if not price:
                    return -5
            elif LANG == 0:
                price = "{:,}".format(int(price) * 10000)
            else:
                if not tool_price_units[LANG]:
                    return -5
                price += tool_price_units[LANG]
        values["price"] = price

    for field, source in fields.items():
        code = next((key for key, word in tool_source_words[field].items() if word == source), None)
        if code is None:
            return -5
        word = tool_word_translations[field][code][LANG]
        if source and not word:
            return -5
        values[field] = word.format(rarity=rarity) if field == "goods" and rarity is not None else word

    return set_description(item, desc_format.format(**values), normalize=False)

# ——————————————————————————————
# GACHA-EXCHANGE (NGS Part) RULES & TRANSLATION
# ——————————————————————————————

gacha_source_formats = {
    "exchange": r"\A\Z",
}

# JP names identify the mechanism; translated names supply titles absent from native descriptions.
gacha_source_name_formats = {
    "special": r".*スペシャルセレクト券",
    "sp": r"(?P<title>.+?)(?P<date>'[0-9]+)?SPセレクト券(?P<suffix_date>'[0-9]+)?",
    "treasure": r"(?:超・)?トレジャーセレクト券Vol\.(?P<number>[0-9]+)",
    "prize": r"[0-9]+周年(?:サンクフル[A-Za-z]*|メモリーズ)景品交換券",
}

# Select/Exchange suffixes identify translated ticket names, never Scratch tickets.
gacha_item_name_formats = {
    # JP text: {title}スペシャルセレクト券
    "special": [
        r"(?P<title>.*?)(?:Special )?Select Ticket",
        r"(?P<title>.*?)(?:스페셜 )?셀렉트권",
        "",
        r"(?P<title>.*?)(?:特殊)?自選券",
        "(?P<title>.*?)(?:Special )?(?:Select|Scratch) Ticket",
    ],
    # JP text: {title}{date}SPセレクト券 / {title}SPセレクト券{date}
    "sp": [
        r"(?P<title>.+?)(?: (?P<date>'[0-9]+))?(?: (?:SP|Special))? Select Ticket",
        r"(?P<title>.+?)(?P<date>'[0-9]+)? SP 셀렉트권",
        "",
        r"(?P<title>.+?)(?P<date>'[0-9]+)?SP自選券",
        "(?P<title>.+?)(?: (?P<date>'[0-9]+))?(?: (?:SP|Special))? (?:Select )?Ticket",
    ],
    # JP text: {title}セレクト券Vol.{number}
    "treasure": [
        r"(?P<title>.+?) Select Ticket Vol\.(?P<number>[0-9]+)",
        r"(?P<title>.+?) 셀렉트권 Vol\.(?P<number>[0-9]+)",
        "",
        r"(?P<title>.+?)自選券Vol\.(?P<number>[0-9]+)",
        "(?P<title>.+?) Select Ticket Vol\\.(?P<number>[0-9]+)",
    ],
    # JP text: {title}景品交換券
    "prize": [
        r"(?P<title>.+?) Exchange Ticket",
        r"(?P<title>.+?) 경품 교환권",
        "",
        r"(?P<title>.+?)獎品交換券",
        "(?P<title>.+?) Exchange Ticket",
    ],
}

# Derive native scratch targets from ticket names when JP descriptions are empty.
gacha_title_formats = {
    # JP text: {title}スペシャルスクラッチ
    "special": ["{title} Special Scratch", "{title} 스페셜 스크래치", "", "{title}特殊轉蛋", "{title} Special Scratch"],
    # JP text: {title}{date}SPスクラッチ / {title}SPスクラッチ{date}
    "sp": ["{title}{date} SP Scratch", "{title}{date} SP 스크래치", "", "{title}{date}SP轉蛋", "{title}{date} SP Scratch"],
    # JP text: {title}SPスクラッチ{date}
    "collaboration": ["{title} SP Scratch{date}", "{title} SP 스크래치{date}", "", "{title}SP轉蛋{date}", "{title} SP Scratch{date}"],
    # JP text: {title}スクラッチ{number}
    "treasure": ["{title} Scratch Vol.{number}", "{title} 스크래치{number}", "", "{title}轉蛋{number}", "{title} Scratch Vol.{number}"],
}

# JP text: {date}
gacha_date_formats = [" {date}", "{date}", "", "{date}", " {date}"]

# JP text: "" (the exchange target is identified by the ticket name).
gacha_desc_formats = [
    ("During the target scratch, one gift\n"
     "can be selected and exchanged.\n"
     "<yellow>Target Scratch:\n"
     "{target}<c>"),
    ("대상 스크래치 판매 기간 중\n"
     "경품 1개를 선택해 교환할 수 있는 티켓.\n"
     "<yellow>※대상 스크래치:\n"
     "{target}<c>"),
    (""),
    ("可在對象轉蛋的販賣期間\n"
     "自選交換1件獎品的票券。\n"
     "<yellow>※對象轉蛋：\n"
     "　{target}<c>"),
    ("สามารถเลือกแลกของรางวัลได้ 1 ชิ้นในระหว่างช่วงเวลาของตั๋วสแครชเป้าหมาย\n"
     "ตั๋วสแครชเป้าหมาย:\n"
     "\"{target}\""),
]

# [FUNCTION] Keep native exchange targets, deriving missing targets from the current ticket's name.
def translate_gacha_desc(item, file_name, name_prefix):
    for target_type, pattern in gacha_source_name_formats.items():
        match = regex.fullmatch(pattern, item["jp_text"])
        if match is not None:
            break
    else:
        return -1
    if match_description(item, gacha_source_formats, {}) is None:
        return -4
    problem = get_translation_problem(item)
    if problem:
        return problem
    parts = get_item_name_parts(item, name_prefix, gacha_item_name_formats[target_type])
    if parts is None:
        return -5
    template = gacha_desc_formats[LANG]
    if not template:
        return -5

    values = {key: value.strip() for key, value in parts.items()}
    source = match.groupdict(default="")
    if target_type == "sp":
        if source["date"] and source["suffix_date"]:
            return -5
        date = source["date"] or source["suffix_date"]
        if date != values["date"]:
            return -5
        values["date"] = gacha_date_formats[LANG].format(date=date) if date else ""
        if "コラボ" in source["title"]:
            target_type = "collaboration"
    elif target_type == "treasure" and source["number"] != values["number"]:
        return -5
    target = values["title"] if target_type == "prize" else gacha_title_formats[target_type][LANG].format(**values).strip()
    if LANG == 0:
        native_target = get_existing_description_field(item, template, "target")
        if (target_type == "collaboration" and values["date"] and native_target
                and not native_target.endswith(values["date"])):
            native_target = None
        # These baseline captions name the exchange ticket instead of its scratch.
        if native_target and not regex.search(r"\b(?:Select|Prize Exchange)\b", native_target):
            if target_type in ("sp", "collaboration"):
                native_target = regex.sub(r"\bSpecial Scratch\b", "SP Scratch", native_target)
            target = native_target
        elif target_type == "prize":
            target = get_ticket_target_name(item, name_prefix, item["jp_text"].removesuffix("景品交換券"))
            if target is None:
                return -5
    return set_description(item, template.format(target=target))

# ——————————————————————————————
# MAPPINGS AND CONDITIONS
# ——————————————————————————————

# Map JSON name stems to category functions; insertion order preserves the original file order.
# All handlers take (item, file_name, name_prefix), replace the body on success and return:
#  0: processed; -1: ineligible/unsupported; -2: keep the existing body;
# -3: empty build-part source; -4: unknown source; -5: unavailable type/translation.
description_translators = {
    **dict.fromkeys(layered_file_names, translate_layer_desc),
    **dict.fromkeys(cosmetic_file_names, translate_cosmetic_desc),
    **dict.fromkeys(build_parts_file_names, translate_part_desc),
    "Stack_LobbyAction": translate_la_desc,
    "Stack_Voice": translate_voice,
    **dict.fromkeys(cosmeticsorted_file_names, translate_cosmeticsorted_desc),
    **dict.fromkeys(avatar_file_names, translate_avatar_desc),
    "Stack_Music": translate_music_desc,
    "Stack_Boost": translate_boost_desc,
    "Stack_PaidPass": translate_paidpass_desc,
    "Stack_Tool": translate_tool_desc,
    "Stack_GachaTradePass": translate_gacha_desc,
}

# Minimum assign lengths distinguish NGS records from classic items.
description_assign_lengths = {
    **dict.fromkeys(avatar_file_names, 9),
    "Stack_Boost": 8,
    "Stack_PaidPass": 9,
    "Stack_Tool": 8,
    "Stack_GachaTradePass": 9,
}

# ——————————————————————————————
# MAIN PROCESS
# ——————————————————————————————

# [FUNCTION] Run one file through shared I/O, name handling, category translation and reporting.
def main_update(file_name, debug=False):
    items_file_name = "Item_" + file_name + ".txt"
    path = os.path.join(json_loc, items_file_name)
    try:
        with open(path, mode='r', encoding='utf-8', newline='') as items_file:
            items = json.load(items_file)
    except FileNotFoundError:
        print("\t{0} not found.".format(items_file_name))
        return

    minimum_assign_length = description_assign_lengths.get(file_name)
    print("{0}{1} loaded. {{".format(
        items_file_name, " (NGS Part)" if minimum_assign_length is not None else ""))
    translate = description_translators[file_name]
    newtranslations = False
    for item in items:
        if minimum_assign_length is not None and (
                len(item["assign"]) < minimum_assign_length or item["jp_text"].startswith("￥仮")):
            continue
        old_explain = item["tr_explain"]
        # Translate only the body; restore the green prefix even when translation is skipped.
        if minimum_assign_length is None:
            fill_cn_name(item)
        name_prefix = split_name_prefix(item)
        problem = translate(item, file_name, name_prefix)
        if minimum_assign_length is not None and problem in (0, -5):
            fill_cn_name(item)
        item["tr_explain"] = name_prefix + item["tr_explain"]

        # Processing successfully counts as a new translation only when the description changes.
        if problem == 0 and item["tr_explain"] != old_explain:
            print("\tTranslated description for {0}".format(item["tr_text"] or item["jp_text"]))
            newtranslations = True
        elif problem == -4:
            print("\t{0} has a new kind of description".format(item["tr_text"] or item["jp_text"]))

    if not newtranslations:
        print("\tNo new translations.")
    print("}")

    # Save CN name fills even when no description changed; debug only prints logs.
    if debug:
        return
    with open(path, mode='w', encoding='utf-8', newline='') as items_file:
        json.dump(items, items_file, ensure_ascii=False, indent="\t", sort_keys=False)
        items_file.write("\n")

# [FUNCTION] Initialize the run once and dispatch every configured file through main_update.
def main(argv=None):
    global TRANS_ALL, LANG, REDO_ALL
    args = parse_arguments(argv)
    LANG = next(index for index, language in LANGS.items() if language == args.lang)
    # CN always reprocesses descriptions, independent of -r.
    TRANS_ALL, REDO_ALL = args.all, args.redo or LANG == 3
    print(f"TicketDescriptions ({args.lang})")
    if args.debug:
        print("  DEBUG    Log only; target files will not be written")
    for file_name in description_translators:
        main_update(file_name, args.debug)

if __name__ == '__main__':
    main()
