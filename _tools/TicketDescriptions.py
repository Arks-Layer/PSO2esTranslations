#!/usr/bin/env python3
# coding=utf8

import json
import os
import regex
import argparse

# Layout: settings, basic tools, shared data/functions, six category sections, dispatch and main.

# ——————————————————————————————
# LANGUAGE & PATH SETTING
# ——————————————————————————————

# This tool translates descriptions from the JP text already stored in JSON.
json_loc = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "json")

# Indices follow the description-table order; -1 is the JP voice-actor fallback.
LANGS = {-1: "JP",
         0: "EN",
         1: "KO",
         2: "RU",
         3: "CN"}

# Full width character transtable for EN/KO/RU; CN keeps full width.
chartable = [
    "".maketrans("０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ　＝－＋／．＆（）：！",
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz =-+/.&():!"),
] * 3 + [{}]

# ——————————————————————————————
# BASIC FUNCTIONS
# ——————————————————————————————

# Define rule-building helpers before the tables that call them during module loading.

# [FUNCTION] Read the existing -a/-l/-r options; CN remains the default language.
def parse_arguments(argv=None):
    parser = argparse.ArgumentParser(
        description = "Translates ticket item descriptions.")

    # Switch for description on untranslated names
    parser.add_argument("-a", dest = "all", action = "store_true",
                        help = ("Translate descriptions even for items "
                                "with no translated names."))

    # Switch for language.
    parser.add_argument("-l", type = int, dest = "lang", action = "store",
                        choices = [0, 1, 2, 3], default = 3, metavar = "N",
                        help = ("Set a language to translate into. "
                                "Available options are 0 (EN), 1 (KO), 2 (RU) and 3 (CN). "
                                "Defaults to CN."))

    # Switch for retranslating all descriptions.
    parser.add_argument("-r", dest = "redo", action = "store_true",
                        help = ("Force all ticket descriptions to be processed, "
                                "even if already translated. "
                                "Always on for CN."))
    return parser.parse_args(argv)

# [FUNCTION] For CN, copy the JP name into any empty tr_text.
def fill_cn_name(item):
    if LANG == 3 and item["tr_text"] == "":
        item["tr_text"] = item["jp_text"]

# [FUNCTION] Detach the green name prefix added by TicketGenerateFromGamefile.
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

# [FUNCTION] Match existing note markers without requiring paired color tags.
def source_note_pattern(pattern):
    return r"(?:<yellow>)?" + pattern + r"(?:<c>)?"

# ——————————————————————————————
# SHARED DESCRIPTION DATA
# ——————————————————————————————

# Cross-category tables live here; each category below keeps its own allowed formats and notes.

# Type labels shared by layered wear, cosmetic tickets and character parts.

ntype_locks = {
    # No JP restriction text; this default does not add a type note.
    "a": ["All", "KO_All", "Все", "CN_All"],
    # JP text: ヒト型/キャストタイプ1
    "a1": ["Human/Cast Type 1", "인간형/캐스트타입1", "Человек/CAST (тип1)", "人類/機人類型1"],
    # JP text: ヒト型/キャストタイプ2
    "a2": ["Human/Cast Type 2", "인간형/캐스트타입2", "Человек/CAST (тип2)", "人類/機人類型2"],
    # JP text: ヒト型タイプ1
    "h1": ["Human Type 1", "인간형 타입1", "Человек (тип1)", "人類類型1"],
    # JP text: ヒト型タイプ2
    "h2": ["Human Type 2", "인간형 타입2", "Человек (тип2)", "人類類型2"],
    # JP text: キャストタイプ1
    "c1": ["Cast Type 1", "캐스트 타입1", "CAST (тип1)", "機人類型1"],
    # JP text: キャストタイプ2
    "c2": ["Cast Type 2", "캐스트 타입2", "CAST (тип2)", "機人類型2"]
}

# NGS Hairstyle tickets also use these labels when their JP source identifies Headparts.

cosmeticsorted_types = {
    # JP text: 頭部
    "Head": ["head", "헤드 파츠", "голова", "頭部"],
    # JP text: 顔バリエーション
    "Facetype": ["face type", "얼굴 바리에이션", "тип лица", "臉部類型"],
    # JP text: ヘッドパーツ
    "Headparts": ["head parts", "헤드 파츠", "части головы", "頭部部件"],
    # JP text: ボディパーツ
    "Bodyparts": ["body parts", "바디 파츠", "части тела", "身體部件"],
    # JP text: アームパーツ
    "Armparts": ["arm parts", "암 파츠", "части рук", "臂部部件"],
    # JP text: レッグパーツ
    "Legparts": ["leg parts", "레그 파츠", "части ног", "腿部部件"]
    }

# Translated body templates shared by cosmetic tickets and character parts.

cosmetic_desc_formats = {
    # JP text:
    # 使用すると、新しい{itype}の\n
    # {iname}が選択可能。
    # {sexlock} unavailable.
    "use_new": [
        "Unlocks the {sexlock}{itype}\n"
        "\"{iname}\"\n"
        "for use in the Beauty Salon.",
        "사용하면 새로운 {sexlock}{itype}\n"
        "\"{iname}\"\n"
        "의 사용이 가능해진다.",
        "Разблок-т {itype} {sexlock}\n"
        "\"{iname}\"\n"
        "для использования в салоне.",
        "使用後，可選用新的{sexlock}{itype}\n"
        "{iname}。",
    ],
    # JP text:
    # チケットを使用すると、{itype}\n
    # {iname}が選択可能。
    # {sexlock} unavailable.
    "ticket": [
        "Unlocks the {sexlock}{itype}\n"
        "\"{iname}\"\n"
        "for use in the Beauty Salon.",
        "사용하면 새로운 {sexlock}{itype}\n"
        "\"{iname}\"\n"
        "의 사용이 가능해진다.",
        "Разблок-т {itype} {sexlock}\n"
        "\"{iname}\"\n"
        "для использования в салоне.",
        "使用票券後，可選用{sexlock}{itype}\n"
        "{iname}。",
    ],
    # JP text:
    # チケットを使用すると、新しい{itype}の\n
    # {iname}が選択可能。
    # {sexlock} unavailable.
    "ticket_new": [
        "Unlocks the {sexlock}{itype}\n"
        "\"{iname}\"\n"
        "for use in the Beauty Salon.",
        "사용하면 새로운 {sexlock}{itype}\n"
        "\"{iname}\"\n"
        "의 사용이 가능해진다.",
        "Разблок-т {itype} {sexlock}\n"
        "\"{iname}\"\n"
        "для использования в салоне.",
        "使用票券後，可選用新的{sexlock}{itype}\n"
        "{iname}。",
    ],
    # JP text:
    # 特定ステッカーの装着許可チケット。\n
    # 使用すると、新しい{itype}の\n
    # {iname}が選択可能。
    # {sexlock} unavailable.
    "sticker_use_new": [
        "Unlocks the {sexlock}{itype}\n"
        "\"{iname}\"\n"
        "for use in the Beauty Salon.",
        "사용하면 새로운 {sexlock}{itype}\n"
        "\"{iname}\"\n"
        "의 사용이 가능해진다.",
        "Разблок-т {itype} {sexlock}\n"
        "\"{iname}\"\n"
        "для использования в салоне.",
        "許可著裝特定貼紙的票券。\n"
        "使用後，可選用新的{sexlock}{itype}\n"
        "{iname}。",
    ],
}

# NGS body templates shared by layered wear, cosmetic tickets and character parts.
ndesc_formats = {
    # JP text:
    # 使用すると新しい{itype}が\n
    # 選択可能になる。
    "n": [
        "Unlocks {a}new {itype} for use.",
        "사용하면 새로운 {itype}\n"
        "선택이 가능해집니다.",
        "Разблок {itype}.",
        "使用後可選用新的{itype}。",
    ],
    # JP text:
    # 使用すると新しい{itype}が\n
    # 全キャラクターで選択可能になる。
    "allcharacters": [
        "A {itype} that unlocks for all\n"
        "characters on your account.",
        "사용하면 새로운 {itype} 아이템을\n"
        "모든 캐릭터에 선택할 수 있게 됩니다.",
        "{itype}, разблок. для\n"
        "всех персонажей аккаунта.",
        "使用後所有角色均可選用新的{itype}。",
    ],
    # JP text:
    # 使用すると新しい{itype}パターンが\n
    # 選択可能になる。
    "pattern": [
        "Unlocks {a}new {itype} for use.",
        "사용하면 새로운 {itype}\n"
        "선택이 가능해집니다.",
        "Разблок {itype}.",
        "使用後可選用新的{itype}種類。",
    ],
    # JP text:
    # 使用すると新しい{itype}が\n
    # 全キャラクターで選択可能になる。
    "account_item": [
        "A {itype} that unlocks for all\n"
        "characters on your account.",
        "사용하면 새로운 {itype}\n"
        "모든 캐릭터에서 선택할 수 있게 된다.",
        "{itype}, разблок. для\n"
        "всех персонажей аккаунта.",
        "使用後所有角色均可選用新的{itype}。",
    ],
}

# Translated notes reused across categories; source recognizers still control which notes are allowed.

shared_extras = {
    # JP text: ※対応：{type}
    "type": [
        "\n<yellow>※Type: {type}<c>",
        "\n<yellow>※대응: {type}<c>",
        "\n<yellow>※Тип: {type}<c>",
        "\n<yellow>※適用於：{type}<c>",
    ],
    # JP text:
    # ※着用時はインナーが非表示になります。
    "hide_inner": [
        "\n<yellow>※Hides innerwear when worn.<c>",
        "\n<yellow>※착용 시 이너웨어는 표시하지 않음.<c>",
        "\n<yellow>※При экипировке скрывает In.<c>",
        "\n<yellow>※穿著時不會顯示內衣。<c>",
    ],
    # JP text:
    # ※カラー変更非対応
    "color": [
        "\n<yellow>※Color cannot be changed<c>",
        "\n<yellow>※컬러 변경 불가<c>",
        "\n<yellow>※Цвет нельзя изменить<c>",
        "\n<yellow>※不適用於顏色的變更<c>",
    ],
    # JP text:
    # ※『PSO2』ブロック非対応
    "ngs": [
        "\n<yellow>※Not available in [PSO2] Blocks.<c>",
        "\n<yellow>※『PSO2』블록 비대응<c>",
        "\n<yellow>※Нельзя использовать в блоке PSO2<c>",
        "\n<yellow>※不適用於『PSO2』<c>",
    ],
}

cosmetic_extras = {
    # JP text:
    # ※一部の顔、ヘッドパーツ非対応
    "face": [
        "\n<yellow>※Not compatible with some heads/faces.<c>",
        "\n<yellow>※일부 얼굴과 헤드 파츠 미지원<c>",
        "\n<yellow>※<c>",
        "\n<yellow>※不適用於部分面部、頭部部件<c>",
    ],
    # No existing KO source for the weapon-position note.
    # JP text:
    # ※武器の構え位置自動調整
    "posture": [
        "\n<yellow>※Uses adjusted weapon positions.<c>",
        "",
        "\n<yellow>※Исп. скоррект. положение.<c>",
        "\n<yellow>※自動調整武器架勢的位置<c>",
    ],
    # JP text:
    # ※サイズ調整はできません。
    "size": [
        "\n<yellow>※Size cannot be adjusted.<c>",
        "\n<yellow>※사이즈 조정은 할 수 없습니다.<c>",
        "\n<yellow>※Нельзя отрегулировать размер.<c>",
        "\n<yellow>※無法調整尺寸。<c>",
    ],
    # JP text:
    # ※カラーは変更できません
    "color": [
        "\n<yellow>※Color cannot be changed<c>",
        "\n<yellow>※색상은 변경할 수 없습니다<c>",
        "\n<yellow>※Цвет нельзщя изменить.<c>",
        "\n<yellow>※無法變更顏色<c>",
    ],
}

# The complete JP source lines, including the SANRIO notice, are the dictionary keys.
ticket_extras = {
    "※PS4表示不可": [
        "\n<yellow>※Cannot be used on PS4<c>",
        "\n<yellow>※PS4에서는 표시할 수 없음<c>",
        "",
        "\n<yellow>※PS4不可顯示<c>",
    ],
    "※PS4表示可": [
        "\n<yellow>※Can be displayed on PS4<c>",
        "\n<yellow>※PS4에서 표시 가능<c>",
        "",
        "\n<yellow>※PS4可顯示<c>",
    ],
    "※アニメーションはしません。": [
        "\n※Does not animate.",
        "\n※애니메이션 효과는 없다.",
        "",
        "\n※不會播放動畫。",
    ],
    "キャスト男性ボディ向け。": [
        "\nSuited to male CAST bodies.",
        "\n캐스트 남성 바디에 맞춘 액세서리.",
        "",
        "\n適合男性機人身體。",
    ],
    "c'76,'15 SANRIO APPR.NO.S564996": [
        "\nc'76,'15 SANRIO APPR.NO.S564996",
        "\nc'76,'15 SANRIO APPR.NO.S564996",
        "\nc'76,'15 SANRIO APPR.NO.S564996",
        "\nc'76,'15 SANRIO APPR.NO.S564996",
    ],
}

# JP body and note recognizers shared across categories.

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
# Build-part and no-sticker literals use normalize=False to preserve their established text.
def set_description(item, description, normalize=True):
    item["tr_explain"] = description.translate(chartable[LANG]) if normalize else description
    return 0

# [FUNCTION] Convert optional JP race/type restrictions to the existing translation-table keys.
def get_type_restrictions(extras):
    restriction = extras.get("type")
    if restriction is None:
        return "a"
    return {"ヒト型/キャスト": "a", "ヒト型": "h", "キャスト": "c"}[restriction["race"]] + restriction["number"]

# ——————————————————————————————
# LAYERED WEAR RULES & TRANSLATION
# ——————————————————————————————

# Keep file lists, type names, JP rules, translated templates and handlers together.

layered_file_names = ["BaseWear_Female",
                      "BaseWear_Male",
                      "InnerWear_Female",
                      "InnerWear_Male",
                      "Stack_OuterWearF",
                      "Stack_OuterWearM"]

layered_wear_types = {
    # JP item type:
    # インナーウェア
    "In": ["innerwear", "이너웨어", "внутреннюю одежду (In)", "內衣"],
    # JP item type:
    # ベースウェア
    "Ba": ["basewear", "베이스웨어", "верхнюю одежду (Ba)", "底衣"],
    # JP item type:
    # セットウェア
    "Se": ["setwear", "세트 웨어", "комплектную одежду (Se)", "套服"],
    # JP item type:
    # フルセットウェア
    "Fu": ["full setwear", "풀세트 웨어", "полн.компл.одежду (Fu)", "全身套服"],
    # JP item type:
    # アウターウェア
    "Ou": ["outerwear", "아우터 웨어", "внешнюю одежду (Ou)", "外套"],
    # JP item type:
    # トータルウェア
    "To": ["totalwear", "토탈웨어", "", "完整裝扮"],
}

layer_source_types = {
    "In": "インナーウェア", "Ba": "ベースウェア", "Se": "セットウェア",
    "Fu": "フルセットウェア", "Ou": "アウターウェア", "To": "トータルウェア",
}

# Source kinds are independent of the name suffix used to render the translation.
layer_source_type_pattern = "(?:" + "|".join(map(regex.escape, layer_source_types.values())) + ")"

# JP body and note recognizers for old and NGS layered wear.

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

# Translated layered-wear bodies and category-specific notes.

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

# Layered-wear notes include their own separators and color markup.
layer_extras = {
    # JP source has no sex restriction line; this extra is intentionally empty.
    "n": ["", "", "", ""],
    # JP text:
    # 男性のみ使用可能。
    "m": [
        "\nOnly usable on male characters.",
        " 남성만 가능.",
        "\nТолько для мужских персонажей.",
        "\n僅限男性使用。",
    ],
    # JP text:
    # 女性のみ使用可能。
    "f": [
        "\nOnly usable on female characters.",
        " 여성만 가능.",
        "\nТолько для женских персонажей.",
        "\n僅限女性使用。",
    ],
    # JP text:
    # ※一部[In]カラー同期
    "sync_inner": [
        "\n<yellow>※Synchronizes with [In] color.<c>",
        "\n<yellow>※일부 [In]컬러 동기화<c>",
        "\n<yellow>※Цвета некоторых [In] синхр-ся.<c>",
        "\n<yellow>※與一部分[In]同步顏色<c>",
    ],
    # JP text:
    # ※アクセサリー表示非対応
    "hide_accessories": [
        "\n<yellow>※Hides accessories when worn.<c>",
        "\n<yellow>※악세서리 표시 불가<c>",
        "\n<yellow>※Скрывает аксессуары.<c>",
        "\n<yellow>※不適用於飾品的顯示<c>",
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
    if not layered_wear_types[wear_type][LANG]:
        return -5
    extras = get_ticket_extras(source_extras)
    if extras is None:
        return -5

    sex = {"男": "m", "女": "f"}.get(source_extras.get("sex", {}).get("sex"), "n")
    hideinner = "hide_inner" in source_extras

    # Translate the description.
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
    if not layered_wear_types[wear_type][LANG]:
        return -5
    extras = get_ticket_extras(source_extras)
    if extras is None:
        return -5

    syncinner = "sync_inner" in source_extras
    types = get_type_restrictions(source_extras)
    hideinner = "hide_inner" in source_extras
    hideaccess = "hide_accessories" in source_extras
    ncolorlocked = "ncolor" in source_extras

    # Translate the description.
    body = ndesc_formats["n"][LANG].format(
        itype = layered_wear_types[wear_type][LANG],
        a = "a ",
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
        "background for your ARKS\n"
        "Card",
        "아크스 카드 배경을",
        "",
        "\nARKS名片背景",
    ],
    # JP text: ポータブルホログラム
    **dict.fromkeys(
        ("Stack_CS_Effect", "Stack_CS_Room_Goods", "Stack_CS_Stickers"),
        [
            "Portable Hologram",
            "포터블 홀로그램을",
            "",
            "\n便攜全息投影",
        ],
    ),
    # JP text: プレイマット
    "Stack_Duel_Card_Play_Mat": ["playmat", "플레이 매트를", "", "牌桌墊"],
    # JP text: カードスリーブ
    "Stack_Duel_Card_Sleeve": ["card sleeve", "카드 슬리브를", "", "牌套"],
    # JP text: カード
    "Stack_Duel_Card_Ticket": ["card", "카드를", "", "卡牌"],
    # JP text: バイタルゲージの背景
    "Stack_Vital_Gauge": [
        "Vital Gauge BG",
        "바이탈 게이지 배경을",
        "",
        "\n體征槽背景",
    ],
}

cosmetic_types = {
    **account_item_types,
    # JP text: アクセサリー
    "Stack_Accessory": ["accessory", "악세서리", "аксессуар", "飾品"],
    # JP text: ボディペイント
    "Stack_BodyPaint": ["body paint", "바디 페인트", "рис. тела", "身體彩繪"],
    # JP text: 耳
    "Stack_Ear": ["ear shape", "귀", "форма ушей", "耳朵"],
    # JP text: 瞳
    "Stack_Eye": ["eye pattern", "눈동자", "глаза", "瞳孔"],
    # JP text: まゆ
    "Stack_EyeBrow": ["eyebrow type", "눈썹", "брови", "眉毛"],
    # JP text: まつげ
    "Stack_EyeLash": ["eyelash type", "속눈썹", "ресницы", "睫毛"],
    # JP text: メイク
    "Stack_FacePaint": ["makeup", "메이크업", "макияж", "妝容"],
    # JP text: 髪型 / ヘアスタイル
    "Stack_Hairstyle": ["hairstyle", "헤어스타일", "причёску", "髪型"],
    # JP text: 角
    "Stack_Horn": ["horn type", "뿔", "тип рога", "角"],
    # JP text: モーション
    "Stack_MotionChange": ["motion", "모션", "движение", "行動方式"],
    # JP text: 肌
    "Stack_Skin": ["body type", "피부", "", "皮膚"],
    # JP text: スタンプ
    "Stack_Stamp": ["stamp", "스탬프", "штамп", "表情圖"],
    # JP text: ステッカー
    "Stack_Sticker": ["sticker", "스티커", "стикер", "貼紙"],
    # JP text: 歯・舌
    "Stack_Tooth": [
        "teeth and tongue\n"
        "set",
        "치아/혀",
        "зубы и язык",
        "牙齒、舌頭",
    ],
}

# The Japanese weapon-type terms are the dictionary keys below.
motion_weapon_types = {
    "大剣": ["Sword", "소드", "", "大劍"],
    "自在槍": ["Wired Lance", "와이어드 랜스", "", "自在槍"],
    "長槍": ["Partizan", "파르티잔", "", "長槍"],
    "双小剣": ["Twin Daggers", "트윈 대거", "", "雙小劍"],
    "両剣": ["Double Saber", "더블 세이버", "", "雙頭劍"],
    "鋼拳": ["Knuckle", "너클", "", "鋼拳"],
    "銃剣": ["Gunslash", "건슬래시", "", "槍刃"],
    "長銃": ["Rifle", "라이플", "", "步槍"],
    "大砲": ["Launcher", "런처", "", "大炮"],
    "双機銃": ["Twin Machineguns", "트윈 머신건", "", "雙機槍"],
    "長杖": ["Rod", "로드", "", "長杖"],
    "導具": ["Talis", "탈리스", "", "導具"],
    "短杖": ["Wand", "완드", "", "短杖"],
    "抜剣": ["Katana", "카타나", "", "拔劍"],
    "強弓": ["Bullet Bow", "불릿 보우", "", "強弓"],
    "魔装脚": ["Jet Boots", "제트 부츠", "", "魔裝腳"],
    "飛翔剣": ["Dual Blades", "듀얼 블레이드", "", "飛翔劍"],
    "奏具": ["Takt", "택트", "", "奏具"],
}

# Translated sex restrictions are type labels used by cosmetic_desc_formats.

cosmetic_sex_locks = {
    # JP text: 男性のみ
    "m": ["male-only ", "남성 전용 ", "только для М", "男性專用"],
    # JP text: 女性のみ
    "f": ["female-only ", "여성 전용 ", "только для Ж", "女性專用"]
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
scarf_name_patterns = [r"(.+) Muffler", r"(.+) 머플러", "", r"(.+)圍巾"]

# Translated bodies and category-specific notes.

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

# JP text: {owner}愛用の赤いマフラー。
scarf_intro_formats = ["{owner}'s favorite red muffler.\n", "{owner}이 즐겨 쓰는 붉은 머플러.\n", "", "{owner}愛用的紅色圍巾。\n"]

# Motion tickets use these notes; lobby actions keep their own feature rules below.

motion_extras = {
    # JP text:
    # 武器装備反映／\n
    # 『PSO2』ブロック非対応
    "weapons": [
        "\n<yellow>※Shows equipped weapons.\n"
        "Not available in [PSO2] Blocks.<c>",
        "\n<yellow>※지원 기능: 무기 장비 반영\n"
        "『PSO2』블록 비대응<c>",
        "\n<yellow>※Показывает экип-е оружие.\n"
        "Нельзя использовать в блоке PSO2<c>",
        "\n<yellow>※適用功能：顯示裝備武器\n"
        "不適用於『PSO2』<c>",
    ],
    # JP text: 武器装備反映（{weapon_type}）／\n『PSO2』ブロック非対応
    # KO: Item_Stack_MotionChange.txt, 394010944-394010947 and 394011051.
    "typed_weapons": [
        "\n<yellow>※Shows equipped weapons\n"
        "({weapon_type}).\n"
        "Not available in [PSO2] Blocks.<c>",
        "\n<yellow>※장비한 무기 반영（{weapon_type}）／\n"
        "『PSO2』 블록 미지원<c>",
        "",
        "\n<yellow>※適用功能：顯示裝備武器（{weapon_type}）\n"
        "不適用於『PSO2』<c>",
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
        return set_description(item, no_sticker_desc[LANG], normalize=False)

    if file_name == "Stack_Sticker" and fields["iname"] != item["jp_text"]:
        item_name = item_name.replace(" Sticker", "")
        item_name = item_name.replace("ステッカー", "")

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

    # Translate the description.
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
    if ngsfacelocked and not cosmetic_extras["face"][LANG]:
        return -5

    # Translate the description.
    body = ndesc_formats[desc_sort][LANG].format(
        itype = item_type,
        a = "" if fields["itype"] == "ヘッドパーツ" else "a ",
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
    "アクセスすると\n座れるビルドパーツ。": [
        "This Build Part can be accessed\n"
        "to sit on it.",
        "액세스하면\n"
        "앉을 수 있는 빌드 파츠.",
        "",
        "交互後\n"
        "即可坐下的建造部件。",
    ],
    "アクセスすると\n座れるビルドパーツだが……。": [
        "This Build Part can be accessed\n"
        "to sit on it, but...",
        "액세스하면\n"
        "앉을 수 있는 빌드 파츠지만…….",
        "",
        "交互後\n"
        "即可坐下的建造部件，但……",
    ],
    "アクセスすると\n横になれるビルドパーツ。": [
        "This Build Part can be accessed\n"
        "to lie down on it.",
        "액세스하면\n"
        "누울 수 있는 빌드 파츠.",
        "",
        "交互後\n"
        "即可躺下的建造部件。",
    ],
    "アクセスすると\n入浴できるビルドパーツ。": [
        "This Build Part can be accessed\n"
        "to take a bath.",
        "액세스하면\n"
        "목욕할 수 있는 빌드 파츠.",
        "",
        "交互後\n"
        "即可入浴的建造部件。",
    ],
    "アクセスすると\nシャワーを浴びられるビルドパーツ。": [
        "This Build Part can be accessed\n"
        "to take a shower.",
        "액세스하면\n"
        "샤워할 수 있는 빌드 파츠.",
        "",
        "交互後\n"
        "即可淋浴的建造部件。",
    ],
    "アクセスすると\n開閉できるビルドパーツ。": [
        "This Build Part can be accessed\n"
        "to open and close it.",
        "액세스하면\n"
        "여닫을 수 있는 빌드 파츠.",
        "",
        "交互後\n"
        "即可開閉的建造部件。",
    ],
    "攻撃すると\n破壊できるビルドパーツ。": [
        "This Build Part can be destroyed\n"
        "by attacking it.",
        "공격하면\n"
        "파괴할 수 있는 빌드 파츠.",
        "",
        "攻擊後\n"
        "即可破壞的建造部件。",
    ],
    "アクセスすると\n獲れるビルドパーツ。": [
        "This Build Part can be accessed\n"
        "to collect it.",
        "액세스하면\n"
        "채집할 수 있는 빌드 파츠.",
        "",
        "交互後\n"
        "即可捕獲的建造部件。",
    ],
    "触れると\n取れるビルドパーツ。": [
        "This Build Part can be collected by\n"
        "touching it.",
        "닿으면\n"
        "획득할 수 있는 빌드 파츠.",
        "",
        "觸碰後\n"
        "即可拿取的建造部件。",
    ],
    "アクセスすると\n設定したメッセージを表示する\nビルドパーツ。": [
        "This Build Part can be accessed\n"
        "to read the message it contains.",
        "액세스하면\n"
        "설정한 메시지를 표시하는\n"
        "빌드 파츠.",
        "",
        "交互後\n"
        "就會顯示設置好的訊息的\n"
        "建造部件。",
    ],
    "アクセスすると\nオンオフが切り替わる\nビルドパーツ。": [
        "This Build Part acts as a switch\n"
        "that toggles on/off when accessed.",
        "액세스하면\n"
        "켜짐과 꺼짐이 전환되는\n"
        "빌드 파츠.",
        "",
        "交互後\n"
        "就會切換開關的建造部件。",
    ],
    "上に乗ると\nスイッチがオンになる\nビルドパーツ。": [
        "This Build Part acts as a switch\n"
        "that turns on when stepped on.",
        "위에 올라서면\n"
        "스위치가 켜지는\n"
        "빌드 파츠.",
        "",
        "踩在上面後\n"
        "開關就會設為開的建造部件。",
    ],
    "触れると\n爆発して吹き飛ばされる\nビルドパーツ。": [
        "This Build Part explodes on contact,\n"
        "blasting players away.",
        "닿으면\n"
        "폭발해 몸이 날아가는\n"
        "빌드 파츠.",
        "",
        "觸碰後\n"
        "就會爆炸把人炸飛的建造部件。",
    ],
    "フォトングライド中に\n乗ると移動できる\nビルドパーツ。": [
        "This Build Part lets you ascend by\n"
        "riding it while Photon Gliding.",
        "포톤 글라이드 중에\n"
        "올라타면 이동할 수 있는\n"
        "빌드 파츠.",
        "",
        "在光子滑翔中乘上後\n"
        "即可進行移動的建造部件。",
    ],
    "アクセスすると\n対応する番号のテレポーターに\n移動できるビルドパーツ。": [
        "This Build Part can be accessed\n"
        "to teleport to another Teleporter\n"
        "with a matching ID.",
        "액세스하면\n"
        "대응하는 번호의 텔레포터로\n"
        "이동할 수 있는 빌드 파츠.",
        "",
        "交互後\n"
        "即可移動到相應號碼傳送器的\n"
        "建造部件。",
    ],
    "エリア内に接触すると\n次のギミックパーツに\nコネクトを送信するビルドパーツ。": [
        "When this Build Part detects that a\n"
        "player has entered its assigned area,\n"
        "it sends a signal to its connected parts.",
        "영역 내부에 접촉하면\n"
        "다음 기믹 파츠에\n"
        "커넥트를 전송하는 빌드 파츠.",
        "",
        "碰撞到區域內後\n"
        "就會向下一個機關部件\n"
        "發送智聯信號的建造部件。",
    ],
    "コネクトを受信すると\nタイマーのカウントアップを開始する\nビルドパーツ。": [
        "When this Build Part receives a signal,\n"
        "it starts a timer that counts up from 0.",
        "커넥트를 수신하면\n"
        "타이머의 카운트업을 시작하는\n"
        "빌드 파츠.",
        "",
        "接收智聯信號後\n"
        "就會開始計時器正數的建造部件。",
    ],
    "コネクトを受信すると\nタイマーのカウントダウンを開始する\nビルドパーツ。": [
        "When this Build Part receives a signal,\n"
        "it starts a timer that counts down to 0.",
        "커넥트를 수신하면\n"
        "타이머의 카운트다운을 시작하는\n"
        "빌드 파츠.",
        "",
        "接收智聯信號後\n"
        "就會開始計時器倒數的建造部件。",
    ],
    "エリア内で指定したアクションを行うと\n次のギミックパーツに\nコネクトを送信するビルドパーツ。": [
        "When this Build Part detects a specific\n"
        "player action within its assigned area,\n"
        "it sends a signal to its connected parts.",
        "영역 안에서 지정한 액션을 수행하면\n"
        "다음 기믹 파츠에\n"
        "커넥트를 전송하는 빌드 파츠.",
        "",
        "在區域內執行指定動作後\n"
        "就會向下一個機關部件\n"
        "發送智聯信號的建造部件。",
    ],
    "コネクトを受信すると\n設定したテキスト演出を再生する\nビルドパーツ。": [
        "When this Build Part receives a signal,\n"
        "it displays a set text string.",
        "커넥트를 수신하면\n"
        "설정한 텍스트 연출을 재생하는\n"
        "빌드 파츠.",
        "",
        "接收智聯信號後\n"
        "就會播放設置好的文字演出的\n"
        "建造部件。",
    ],
    "コネクトを受信すると\n設定したサウンドを再生する\nビルドパーツ。": [
        "When this Build Part receives a signal,\n"
        "it plays a specified sound effect.",
        "커넥트를 수신하면\n"
        "설정한 사운드를 재생하는\n"
        "빌드 파츠.",
        "",
        "接收智聯信號後\n"
        "就會播放設置好的聲音的\n"
        "建造部件。",
    ],
    "2つのコネクトを受信すると\n次のギミックパーツに\nコネクトを送信するビルドパーツ。": [
        "When this Build Part receives 2 signals,\n"
        "it sends a signal to its connected parts.",
        "2개의 커넥트를 수신하면\n"
        "다음 기믹 파츠에\n"
        "커넥트를 전송하는 빌드 파츠.",
        "",
        "接收2個智聯信號後\n"
        "就會向下一個機關部件\n"
        "發送智聯信號的建造部件。",
    ],
    "コネクトを受信すると\nカウントを1つ増やす\nビルドパーツ。": [
        "When this Build Part receives a signal,\n"
        "it increases its internal counter by 1.",
        "커넥트를 수신하면\n"
        "카운트를 1 증가시키는\n"
        "빌드 파츠.",
        "",
        "接收智聯信號後\n"
        "計數就會增加1的建造部件。",
    ],
    "コネクトを受信してから\n一定時間後に次のギミックパーツに\nコネクトを送信するビルドパーツ。": [
        "When this Build Part receives a signal,\n"
        "it waits for a set amount of time, then\n"
        "sends a signal to its connected parts.",
        "커넥트를 수신한 뒤\n"
        "일정 시간이 지나면 다음 기믹 파츠에\n"
        "커넥트를 송신하는 빌드 파츠.",
        "",
        "接收智聯信號一定時間後\n"
        "就會向下一個機關部件\n"
        "發送智聯信號的建造部件。",
    ],
    "コネクトを受信すると\n指定したギミックパーツのいずれかに\nコネクトを送信するビルドパーツ。": [
        "When this Build Part receives a signal,\n"
        "it sends a signal on to one of its\n"
        "connected parts, chosen at random.",
        "커넥트를 수신하면\n"
        "지정한 기믹 파츠 중 하나에\n"
        "커넥트를 송신하는 빌드 파츠.",
        "",
        "接收智聯信號後\n"
        "就會向任意的指定機關部件\n"
        "發送智聯信號的建造部件。",
    ],
    "アクセスするとアークス拠点に\n移動できるビルドパーツ。\nＣスペース内の初期位置にもなる。": [
        "This Build Part can be accessed to\n"
        "return to the ARKS Base. It is also\n"
        "where you first arrive in C. Space.",
        "액세스하면 아크스 거점으로\n"
        "이동할 수 있는 빌드 파츠.\n"
        "Ｃ스페이스 내의 초기 위치로도 사용된다.",
        "",
        "交互後即可移動到\n"
        "ARKS據點的建造部件。\n"
        "也會成為創造空間內的初始位置。",
    ],
    "アクセスすると\n自身のキャラクターを投影する\nビルドパーツ。": [
        "This Build Part can be accessed\n"
        "to display the image of a character.",
        "액세스하면\n"
        "자신의 캐릭터를 투영하는\n"
        "빌드 파츠.",
        "",
        "交互後\n"
        "就會投影出自己角色的建造部件。",
    ],
    "上に乗っているあいだだけ\nスイッチがオンになる\nビルドパーツ。": [
        "This Build Part acts as a switch\n"
        "that turns on only while stood on.",
        "위에 올라가 있는 동안에만\n"
        "스위치가 켜지는\n"
        "빌드 파츠.",
        "",
        "僅在踩在上面的時間裡\n"
        "開關會設為開的建造部件。",
    ],
    "アクセスすると\n設計図の登録、取得ができる\nビルドパーツ。": [
        "This Build Part can be accessed\n"
        "to create and download Blueprints.",
        "액세스하면\n"
        "설계도를 등록하고 획득할 수 있는\n"
        "빌드 파츠.",
        "",
        "交互後\n"
        "即可登錄、獲取設計圖的建造部件。",
    ],
    "アクセスすると\nジェネシスポイントが獲得できる\nビルドパーツ。": [
        "This Build Part can be accessed\n"
        "to obtain Genesis Points.",
        "액세스하면\n"
        "제네시스 포인트를 획득할 수 있는\n"
        "빌드 파츠.",
        "",
        "交互後\n"
        "即可獲得創世點數的建造部件。",
    ],
    "くぐると\n加速するビルドパーツ。": [
        "This Build Part makes you accelerate\n"
        "when you pass through it.",
        "통과하면\n"
        "가속시켜 주는 빌드 파츠.",
        "",
        "穿過後\n"
        "就會加速的建造部件。",
    ],
    "触れると\n大きくジャンプするビルドパーツ。": [
        "This Build Part launches you a great\n"
        "distance when you touch it.",
        "닿으면\n"
        "크게 점프하게 되는 빌드 파츠.",
        "",
        "觸碰後\n"
        "就會大幅跳躍的建造部件。",
    ],
    "アクセスすると\nＣスペースメニューを操作できる\nビルドパーツ。": [
        "This Build Part can be accessed\n"
        "to open the Creative Space Menu.",
        "액세스하면\n"
        "Ｃ스페이스 메뉴를 이용할 수 있는\n"
        "빌드 파츠.",
        "",
        "交互後\n"
        "即可操作創造空間菜單的\n"
        "建造部件。",
    ],
    "アクセスすると\nチームコマンドを操作できる\nビルドパーツ。": [
        "This Build Part can be accessed\n"
        "to open the Team Commands Menu.",
        "액세스하면\n"
        "팀 커맨드를 사용할 수 있는\n"
        "빌드 파츠.",
        "",
        "交互後\n"
        "即可操作公會指令的\n"
        "建造部件。",
    ],
    "アクセスすると\nチーム掲示板を操作できる\nビルドパーツ。": [
        "This Build Part can be accessed\n"
        "to open the Team Bulletin Board.",
        "액세스하면\n"
        "팀 게시판을 이용할 수 있는\n"
        "빌드 파츠.",
        "",
        "交互後\n"
        "即可操作公會佈告欄的\n"
        "建造部件。",
    ],
    "アクセスすると\nチームスペースメニューを操作できる\nビルドパーツ。": [
        "This Build Part can be accessed\n"
        "to open the Team Space Menu.",
        "액세스하면\n"
        "팀 스페이스 메뉴를 이용할 수 있는\n"
        "빌드 파츠.",
        "",
        "交互後\n"
        "即可操作公會空間菜單的\n"
        "建造部件。",
    ],
    "アクセスしてジェネシスポイントを\n使用すると、ブーストを発生させられる\nビルドパーツ。": [
        "This Build Part can be accessed\n"
        "to spend Genesis Points to\n"
        "trigger various boost effects.",
        "액세스하여 제네시스 포인트를\n"
        "사용하면 부스트를 발동할 수 있는\n"
        "빌드 파츠.",
        "",
        "交互並使用創世點數後\n"
        "即可發動各種增益的\n"
        "建造部件。",
    ],
    # KO has two existing wordings; keep both descriptions until a shared wording is approved.
    "アクセスすると\nラインストライクで\n対戦できるビルドパーツ。": [
        "This Build Part can be accessed\n"
        "to engage in a Line Strike Duel.",
        "",
        "",
        "交互後\n"
        "即可在戰線牌鬥中對戰的\n"
        "建造部件。",
    ],
    "アクセスすると\n対応する番号の転移門に\n移動できるビルドパーツ。": [
        "This Build Part can be accessed\n"
        "to teleport to another Transition\n"
        "Gate with a matching ID.",
        "액세스하면\n"
        "대응하는 번호의 전이문으로\n"
        "이동할 수 있는 빌드 파츠.",
        "",
        "交互後\n"
        "即可移動到相應號碼傳送門的\n"
        "建造部件。",
    ],
    "アクセスすると\n登録したクリエイティブスペースに\n移動できるビルドパーツ。": [
        "This Build Part can be accessed\n"
        "to teleport to another specified\n"
        "Creative Space.",
        "액세스하면\n"
        "등록한 크리에이티브 스페이스로\n"
        "이동할 수 있는 빌드 파츠.",
        "",
        "交互後\n"
        "即可移動到已登錄創造空間的\n"
        "建造部件。",
    ],
    "コネクトを受信すると\nクレーンを操作できる\nビルドパーツ。": [
        "When this Build Part receives a signal,\n"
        "its crane arm moves around.",
        "커넥트를 수신하면\n"
        "크레인을 조작할 수 있는\n"
        "빌드 파츠.",
        "",
        "接收智聯信號後\n"
        "即可操作勾爪的建造部件。",
    ],
    "上から入ると\n泳げるビルドパーツ。": [
        "This Build Part can be swum in\n"
        "if entered through its top face.",
        "위에서 들어가면\n"
        "수영할 수 있는 빌드 파츠.",
        "",
        "從上方進入後\n"
        "即可游泳的建造部件。",
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

# This single-file category is registered directly in description_translators.
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
        "Unlocks the new Lobby Action\n"
        "\"{iname}\".",
        "『{iname}』 로비 액션을\n"
        "모든 캐릭터에 등록한다.",
        "Разблокирует новый лобби-экшн:\n"
        "\"{iname}\".",
        "所有角色均可選用大廳動作\n"
        "『{iname}』。",
    ],
    # JP text:
    # 使用すると新しいロビーアクションが\n
    # 全キャラクターで選択可能になる。
    "new": [
        "Unlocks a new Lobby Action for use by\n"
        "all characters on your account.",
        "사용하면 새로운 로비 액션이\n"
        "모든 캐릭터에서 사용 가능해진다.",
        "Разблокирует новый лобби-экшн\n"
        "для всех персонажей вашего акка.",
        "使用後所有角色均可選用新的大廳動作。",
    ],
    # JP text:
    # 使用すると新しい手のポーズが\n
    # 全キャラクターで選択可能になる。
    "hand": [
        "When used, allows you to select a\n"
        "new hand pose for all characters.",
        "사용하면 새로운 손가락 포즈가\n"
        "모든 캐릭터로 선택할 수 있게 된다.",
        "Даёт возможность использовать\n"
        "версию с двигающимися пальцами.",
        "使用後所有角色均可選用新的手部姿勢。",
    ],
}

la_extras = {
    # JP text:
    # ※対応機能：ボタン派生/一部表示適用外\n
    # 対応服指可動/『PSO2』ブロック非対応
    "*actnopreviewfingersngs": [
        "\n<yellow>※Extra actions (cannot preview).\n"
        "Finger motion by outfit. Not in [PSO2].<c>",
        "\n<yellow>※지원 기능: 버튼 파생/일부 표시 적용 제외\n"
        "대응 복장 손가락 움직임/『PSO2』 블록 미지원<c>",
        "\n<yellow>※Доп. действие (нет превью).\n"
        "Движ. пальцев огранич. Не в [PSO2].<c>",
        "\n<yellow>※適用功能：按鍵衍生/不適用一部分顯示\n"
        "適用服裝可動手指/不適用於『PSO2』<c>",
    ],
    # JP text:
    # ※対応機能：ボタン派生／\n
    # 対応服指可動／『PSO2』ブロック非対応
    "*actfingersngs": [
        "\n<yellow>Has button actions/Finger motion\n"
        "outfit-limited/Can't use in [PSO2].<c>",
        "\n<yellow>대응 기능: 버튼 파생/대응 복장\n"
        "손가락 가동/『PSO2』 블록 비지원<c>",
        "\n<yellow>Есть действия/Движен. пальцев\n"
        "огранич./Недоступно в [PSO2].<c>",
        "\n<yellow>※適用功能：按鍵衍生/\n"
        "適用服裝可動手指/不適用於『PSO2』<c>",
    ],
    # JP text:
    # ※対応機能：ボタン派生／\n
    # 『PSO2』ブロック非対応
    "*actngs": [
        "\n<yellow>Has button actions/\n"
        "Can't use in [PSO2].<c>",
        "\n<yellow>대응 기능: 버튼 파생/\n"
        "『PSO2』 블록 비지원<c>",
        "",
        "\n<yellow>※適用功能：按鍵衍生/\n"
        "不適用於『PSO2』<c>",
    ],
    # JP text:
    # ※対応機能：ボタン派生／ランダム／\n
    # 対応服指可動
    "*actrandomfingers": [
        "\n<yellow>※Has button actions/randomness.\n"
        "Finger motion limited based on outfit.<c>",
        "\n<yellow>지원 기능: 버튼 파생/랜덤\n"
        "대응복 손가락 가동<c>",
        "\n<yellow>Есть кнопка действия/рандом.\n"
        "Одежда влияет на движ-е пальцев<c>",
        "\n<yellow>※適用功能：按鍵衍生/隨機動作/\n"
        "適用服裝可動手指<c>",
    ],
    # JP text:
    # ※対応機能：ボタン派生／\n
    # 対応服指可動
    "*actfingers": [
        "\n<yellow>※Use action buttons for extra actions.\n"
        "Finger motion limited based on outfit.<c>",
        "\n<yellow>지원 기능: 버튼 파생\n"
        "대응복 손가락 가동<c>",
        "\n<yellow>Доступно доп действие.\n"
        "Одежда влияет на движ-е пальцев<c>",
        "\n<yellow>※適用功能：按鍵衍生/\n"
        "適用服裝可動手指<c>",
    ],
    # KO source wording is retained; only the long second line is split.
    # JP text:
    # ※対応機能：リアクション／\n
    # 対応服指可動／『PSO2』ブロック非対応
    "*reactfingersngs": [
        "\n<yellow>Has reactions/Finger motion\n"
        "outfit-limited/Can't use in [PSO2].<c>",
        "\n<yellow>※지원 기능: 리액션／\n"
        "지원 의상에서 손가락 가동／\n"
        "『PSO2』 블록 미지원<c>",
        "\n<yellow>С реакцией/Движ. пальц.\n"
        "огранич./Не для [PSO2].<c>",
        "\n<yellow>※適用功能：反應動作/\n"
        "適用服裝可動手指/不適用於『PSO2』<c>",
    ],
    # JP text:
    # ※対応機能：対応服指可動／\n
    # 武器装備反映／『PSO2』ブロック非対応
    "*fingersweaponsngs": [
        "\n<yellow>※Finger motion outfit limited. Shows\n"
        "equipment. Cannot perform in [PSO2].<c>",
        "\n<yellow>※지원 기능: 대응복 손가락 가동/\n"
        "무기 장비 반영/『PSO2』블록 비대응<c>",
        "\n<yellow>※Движ. завис-т от одежды| Отображ.\n"
        "экип. оружие| Только для NGS.<c>",
        "\n<yellow>※適用功能：適用服裝可動手指/\n"
        "顯示裝備武器/不適用於『PSO2』<c>",
    ],
    # JP text:
    # ※対応機能：対応服指可動／\n
    # 『PSO2』ブロック非対応
    "*fingersngs": [
        "\n<yellow>※Finger motion limited based on outfit.\n"
        "Cannot perform in [PSO2] Blocks.<c>",
        "\n<yellow>※지원 기능: 대응복 손가락 가동<c>\n"
        "『PSO2』블록 비대응<c>",
        "\n<yellow>※Одежда влияет на движ-е пальцев\n"
        "Нельзя использовать в блоке PSO2<c>",
        "\n<yellow>※適用功能：適用服裝可動手指/\n"
        "不適用於『PSO2』<c>",
    ],
    # JP text:
    # ※対応機能：対応服指可動
    "*fingers": [
        "\n<yellow>※Finger motion limited based on outfit.<c>",
        "\n<yellow>※지원 기능: 대응복 손가락 가동<c>",
        "\n<yellow>※Одежда влияет на движ-е пальцев<c>",
        "\n<yellow>※適用功能：適用服裝可動手指<c>",
    ],
    # JP text:
    # 対応機能：ボタン派生\n
    # <yellow>対象服のみ指も可動<c>
    # Only on a dummy LA but the script crashes when run with -a if not included
    "actfingers": [
        "\n※Use action buttons for extra actions.\n"
        "Finger motion limited based on outfit.",
        "\n지원 기능: 버튼 파생\n"
        "대응복 손가락 가동",
        "\nДоступно доп действие.\n"
        "Одежда влияет на движ-е пальцев",
        "\n適用功能：按鍵衍生\n"
        "<yellow>適用服裝可動手指<c>",
    ],
    # JP text:
    # 対応機能：ボタン派生／武器装備反映\n
    # <yellow>一部武器反映不可<c>
    "actweapons": [
        "\nShows equipment, has extra actions.\n"
        "<yellow>Doesn't show some weapons.<c>",
        "\n지원 기능: 버튼 파생/무기 장비 반영\n"
        "<yellow>일부 무기 반영 불가<c>",
        "\nОтображ. оружие; доп действие.\n"
        "<yellow>Не показывает некоторое оружие.<c>",
        "\n適用功能：按鍵衍生/顯示裝備武器\n"
        "<yellow>無法顯示一部分武器<c>",
    ],
    # JP text:
    # 対応機能：ボタン派生／ランダム
    "actrandom": [
        "\nHas button actions/randomness.",
        "\n지원 기능: 버튼 파생/랜덤",
        "\nЕсть кнопка действия/рандом.",
        "\n適用功能：按鍵衍生/隨機動作",
    ],
    # JP text:
    # 対応機能：ボタン派生
    "act": [
        "\nUse action buttons for extra actions.",
        "\n지원 기능: 버튼 파생",
        "\nДоступно доп действие.",
        "\n適用功能：按鍵衍生",
    ],
    # JP text:
    # 対応機能：武器装備反映\n
    # <yellow>一部武器反映不可<c>
    "weapons": [
        "\nShows equipped weapons.\n"
        "<yellow>Doesn't show some weapons.<c>",
        "\n지원 기능: 무기 장비 반영\n"
        "<yellow>일부 무기 반영 불가<c>",
        "\nПоказывает экип-е оружие.\n"
        "<yellow>Не показывает некоторое оружие.<c>",
        "\n適用功能：顯示裝備武器\n"
        "<yellow>無法顯示一部分武器<c>",
    ],
    # JP text:
    # 対応機能：リアクション
    "react": [
        "\nReaction has extra actions.",
        "\n지원 기능: 리액션",
        "\nЕсть доп действие реакцией.",
        "\n適用功能：反應動作",
    ],
    # JP text:
    # <yellow>※一部ロビーアクション非対応／
    # 『PSO2』ブロック非対応<c>
    "hand": [
        "\n<yellow>※Does not support all Lobby Actions.\n"
        "※Cannot perform in [PSO2] Blocks.<c>",
        "\n<yellow>※일부 로비 액션 미지원/\n"
        "『PSO2』블록 비대응<c>",
        "\n<yellow>※Поддерж-т не все лобби-экшены.\n"
        "※Нельзя использовать в блоке PSO2<c>",
        "\n<yellow>※不適用於一部分大廳動作/\n"
        "不適用於『PSO2』<c>",
    ],
}

# Initialization-order exception: this comprehension reads la_extras during module loading.
# Keep it after la_extras so accepted feature codes come from that table without duplication.

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
    else:
        extra = ""
        if extras != "n":
            extra = shared_extras["ngs"][LANG] if extras == "ngs_locks" else la_extras[extras][LANG]
            if not extra:
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

# This single-file category is registered directly in description_translators.
# JP restriction terms map to the codes used by voice_restriction_extras.

voice_source_restrictions = {
    "人間男性のみ使用可能。": "hm", "人間女性のみ使用可能。": "hf",
    "キャスト男性のみ使用可能。": "cm", "キャスト女性のみ使用可能。": "cf",
    "男性のみ使用可能。": "am", "女性のみ使用可能。": "af",
}

# JP body recognizers.
voice_source_formats = {
    "voice": r"使用すると、新しいボイスが選択可能。(?:\n(?P<restriction>{restriction}))?\nＣＶ(?P<actor>[^\r\n<>]*)",
}

# Translated voice title, body and restriction notes.

# JP text:
# ＣＶ
cv_title = ["CV: ", "CV: ", "CV: ", "CV："]

# JP text:
# 使用すると、新しいボイスが選択可能。
voice_desc_formats = ["Allows a new voice to be selected.",
                      "사용하면 새로운 보이스 사용 가능.",
                      "Позволяет выбрать новый голос.",
                      "使用後，可選用新的語音。"]

voice_restriction_extras = {
    # JP text:
    # 人間男性のみ使用可能。
    "hm": [
        "\nNon-Cast male characters only.",
        "\n인간 남성만 사용 가능.",
        "\nТолько для М не CAST'ов.",
        "\n僅限非機人男性使用。",
    ],
    # JP text:
    # 人間女性のみ使用可能。
    "hf": [
        "\nNon-Cast female characters only.",
        "\n인간 여성만 사용 가능.",
        "\nТолько для Ж не CAST'ов.",
        "\n僅限非機人女性使用。",
    ],
    # JP text:
    # キャスト男性のみ使用可能。
    "cm": [
        "\nMale Casts only.",
        "\n캐스트 남성만 사용 가능.",
        "\nТолько для М CAST'ов.",
        "\n僅限男性機人使用。",
    ],
    # JP text:
    # キャスト女性のみ使用可能。
    "cf": [
        "\nFemale Casts only.",
        "\n캐스트 여성만 사용 가능.",
        "\nТолько для Ж CAST'ов.",
        "\n僅限女性機人使用。",
    ],
    # JP text:
    # 男性のみ使用可能。
    "am": [
        "\nMale characters only (all races).",
        "\n남성만 사용 가능.",
        "\nТолько М персонажей (все расы).",
        "\n僅限男性使用。",
    ],
    # JP text:
    # 女性のみ使用可能。
    "af": [
        "\nFemale characters only (all races).",
        "\n여성만 사용 가능.",
        "\nТолько Ж персонажей (все расы).",
        "\n僅限女性使用。",
    ],
    # JP source has no race/sex restriction line; the existing language defaults are retained.
    "an": [
        "\nUsable by all characters.",
        "\n모두 사용 가능.",
        "\nДоступно всем персонажам.",
        "",
    ],
}

# Translated actor-name vocabulary and language fallbacks; looked up only at run time.

# Japanese actor names are the dictionary keys below.
cv_names = {
    "ゆかな": ["Yukana Nogami", "유카나", "Ногами Юкана", "尤加奈"],
    "チョー": ["Cho", "쵸", "Чо", "長"],
    "ポポナ": ["Popona", "포포나", "Попона", "波波娜"],
    "下野 紘": ["Hiro Shimono", "시모노 히로", "Хиро Симоно", "下野 紘"],
    "中原 麻衣": ["Mai Nakahara", "나카하라 마이", "Маи Накахара", "中原 麻衣"],
    "中尾 隆聖": ["Ryusei Nakao", "나카오 류세이", "Рюсэй Накао", "中尾 隆聖"],
    "中村 悠一": ["Yuichi Nakamura", "유이치 나카무라", "Юичи Накамура", "中村 悠一"],
    "中田 譲治": ["Joji Nakata", "나카타 조지", "Дзёдзи Наката", "中田 讓治"],
    "中西 茂樹": ["Shigeki Nakanishi", "나카니시 시게키", "Сигэки Наканиши", "中西 茂樹"],
    "久野 美咲": ["Misaki Kuno", "쿠노 미사키", "Мисаки Куно", "久野 美咲"],
    "井上 和彦": ["Kazuhiko Inoue", "이노우에 카즈히코", "Казухико Иноэ", "井上 和彥"],
    "井上 喜久子": ["Kikuko Inoue", "이노우에 키쿠코", "Кикуко Иноуэ", "井上 喜久子"],
    "井上 麻里奈": ["Marina Inoue", "이노우에 마리나", "Марина Иноуэ", "井上 麻里奈"],
    "井口 裕香": ["Yuka Iguchi", "이구치 유카", "Юка Игути", "井口 裕香"],
    "今井 麻美": ["Asami Imai", "이마이 아사미", "Асами Имаи", "今井 麻美"],
    "伊瀬 茉莉也": ["Mariya Ise", "이세 마리야", "Мария Исэ", "伊瀨 茉莉也"],
    "伊藤 静": ["Shizuka Ito", "이토 시즈카", "Сидзука Ито", "伊藤 靜"],
    "会 一太郎": ["Ichitaro Ai", "아이 이치타로", "Ичитаро Ай", "會 一太郎"],
    "住友 優子": ["Yuko Sumitomo", "스미토모 유코", "Юко Сумитомо", "住友 優子"],
    "佐倉 綾音": ["Ayane Sakura", "사쿠라 아야네", "Аянэ Сакура", "佐倉 綾音"],
    "佐武 宇綺": ["Uki Satake", "사타케 우키", "Уки Сатакэ", "佐武 宇綺"],
    "佐藤 利奈": ["Rina Sato", "사토 리나", "Рина Сато", "佐藤 利奈"],
    "佐藤 友啓": ["Tomohiro Sato", "사토 토모히로", "Томохиро Сато", "佐藤 友啓"],
    "佐藤 聡美": ["Satomi Sato", "사토 사토미", "Сатоми Сато", "佐藤 聰美"],
    "佳村 はるか": ["Haruka Yoshimura", "요시무라 하루카", "Харука Ёсимура", "佳村 遙"],
    "保志 総一朗": ["Soichiro Hoshi", "호시 소이치로", "Соичиро Хоши", "保志 總一朗"],
    "光吉 猛修": ["Takenobu Mitsuyoshi", "미츠요시 타케노부", "Такэнобу Мицуёши", "光吉 猛修"],
    "内田 真礼": ["Maaya Uchida", "우치다 마아야", "Маая Утида", "內田 真禮"],
    "千本木 彩花": ["Sayaka Senbongi", "센본기 사야카", "Саяка Сэмбонги", "千本木 彩花"],
    "古賀 葵": ["Aoi Koga", "코가 아오이", "Аой Кога", "古賀 葵"],
    "吉野 裕行": ["Hiroyuki Yoshino", "요시노 히로유키", "Хироюки Ёшино", "吉野 裕行"],
    "名塚 佳織": ["Kaori Nazuka", "나즈카 카오리", "Каори Надзука", "名塚 佳織"],
    "喜多村 英梨": ["Eri Kitamura", "키타무라 에리", "Эри Китамура", "喜多村 英梨"],
    "坂本 真綾": ["Maaya Sakamoto", "사카모토 마아야", "Маая Сакамото", "坂本 真綾"],
    "堀川 りょう": ["Ryo Horikawa", "호리카와 료", "Рё Хорикава", "堀川 亮"],
    "堀江 由衣": ["Yui Horie", "호리에 유이", "Юи Хориэ", "堀江 由衣"],
    "増田 俊樹": ["Toshiki Masuda", "마스다 토시키", "Тошики Масуда", "增田 俊樹"],
    "天野 名雪": ["Nayuki Amano", "아마노 나유키", "Наюки Амано", "天野 名雪"],
    "子安 武人": ["Takehito Koyasu", "코야스 타케히토", "Такэхито Коясу", "子安 武人"],
    "安元 洋貴": ["Hiroki Yasumoto", "야스모토 히로키", "Хироки Ясумото", "安元 洋貴"],
    "安済 知佳": ["Chika Anzai", "안자이 치카", "Чика Андзаи", "安濟 知佳"],
    "寺島 拓篤": ["Takuma Terashima", "테라시마 타쿠마", "Такума Тэрашима", "寺島 拓篤"],
    "小倉 唯": ["Yui Ogura", "오구라 유이", "Юй Огура", "小倉 唯"],
    "小原 莉子": ["Riko Kohara", "코하라 리코", "Рико Кохара", "小原 莉子"],
    "小山 茉美": ["Mami Koyama", "코야마 마미", "Мами Кояма", "小山 茉美"],
    "小松 未可子": ["Mikako Komatsu", "코마츠 미카코", "Микако Комацу", "小松 未可子"],
    "小林 ゆう": ["Yu Kobayashi", "코바야시 유우", "Ю Кобаяши", "小林 優"],
    "小清水 亜美": ["Ami Koshimizu", "코시미즈 아미", "Ами Косимидзу", "小清水 亞美"],
    "小西 克幸": ["Katsuyuki Konishi", "코니시 카츠유키", "Кацуюки Кониши", "小西 克幸"],
    "小野 大輔": ["Daisuke Ono", "오노 다이스케", "Дайсукэ Оно", "小野 大輔"],
    "小野坂 昌也": ["Masaya Onosaka", "오노사카 마사야", "Масая Оносака", "小野坂 昌也"],
    "山岡 ゆり": ["Yuri Yamaoka", "야마오카 유리", "Юри Ямаока", "山岡 百合"],
    "岡本 信彦": ["Nobuhiko Okamoto", "오카모토 노부히코", "Нобухико Окамото", "岡本 信彥"],
    "岩下 読男": ["Moai Iwashita", "이와시타 토쿠오", "Моаи Ивасита", "岩下 讀男"],
    "島本 須美": ["Sumi Shimamoto", "시마모토 스미", "Суми Симамото", "島本 須美"],
    "島﨑 信長": ["Nobunaga Shimazaki", "시마자키 노부나가", "Нобунага Симадзаки", "島崎 信長"],
    "川村 万梨阿": ["Maria Kawamura", "카와무라 마리아", "Мария Кавамура", "川村 萬梨阿"],
    "川澄 綾子": ["Ayako Kawasumi", "카와스미 아야코", "Аяко Кавасуми", "川澄 綾子"],
    "市来 光弘": ["Mitsuhiro Ichiki", "이치키 미츠히로", "Мицухиро Ичики", "市來 光弘"],
    "引坂 理絵": ["Rie Hikisaka", "히키사카 리에", "Рие Хирисака", "引坂 理繪"],
    "悠木 碧": ["Aoi Yuki", "유우키 아오이", "Аои Юки", "悠木 碧"],
    "戸松 遥": ["Haruka Tomatsu", "토마츠 하루카", "Харука Томацу", "戶松 遙"],
    "斉藤 壮馬": ["Soma Saito", "사이토 소마", "Сома Сайто", "齊藤 壯馬"],
    "斉藤 朱夏": ["Shuka Saito", "사이토 슈카", "Шюка Саито", "齊藤 朱夏"],
    "斎藤 千和": ["Chiwa Saito", "사이토 치와", "Тива Сайто", "齋藤 千和"],
    "新田 恵海": ["Emi Nitta", "닛타 에미", "Эми Нитта", "新田 惠海"],
    "日笠 陽子": ["Yoko Hikasa", "히카사 요코", "Ёко Хикаса", "日笠 陽子"],
    "早見 沙織": ["Saori Hayami", "하야미 사오리", "Саори Хаями", "早見 沙織"],
    "木村 珠莉": ["Juri Kimura", "키무라 쥬리", "Дзюри Кимура", "木村 珠莉"],
    "木村 良平": ["Ryohei Kimura", "키무라 료헤이", "Рёхэй Кимура", "木村 良平"],
    "本渡 楓": ["Kaede Hondo", "혼도 카에데", "Каэдэ Хондо", "本渡 楓"],
    "杉田 智和": ["Tomokazu Sugita", "스기타 토모카즈", "Томокадзу Сугита", "杉田 智和"],
    "村川 梨衣": ["Rie Murakawa", "무라카와 리에", "Риэ Муракава", "村川 梨衣"],
    "東山 奈央 ": ["Nao Toyama", "토야마 나오", "Нао Тояма", "東山 奈央"],
    "松岡 禎丞": ["Yoshitsugu Matsuoka", "마츠오카 요시츠구", "Ёсицугу Мацуока", "松岡 禎丞"],
    "柿原 徹也": ["Tetsuya Kakihara", "카키하라 테츠야", "Тэцуя Какихара", "柿原 徹也"],
    "桃井 はるこ": ["Haruko Momoi", "모모이 하루코", "Харуко Момои", "桃井 晴子"],
    "桑島 法子": ["Houko Kuwashima", "쿠와시마 호코", "Хоко Кувасима", "桑島 法子"],
    "梶 裕貴": ["Yuki Kaji", "카지 유우키", "Юки Кадзи", "梶 裕貴"],
    "森久保 祥太郎": ["Showtaro Morikubo", "모리쿠보 쇼타로", "Сётаро Морикубо", "森久保 祥太郎"],
    "植田 佳奈": ["Kana Ueda", "우에다 카나", "Кана Уэда", "植田 佳奈"],
    "榊原 良子": ["Yoshiko Sakakibara", "사카키바라 요시코", "Ёсико Сакакибара", "榊原 良子"],
    "榎本 温子": ["Atsuko Enomoto", "에노모토 아츠코", "Ацуко Эномото", "榎本 溫子"],
    "横山 智佐": ["Chisa Yokoyama", "요코야마 치사", "Тиса Ёкояма", "橫山 智佐"],
    "橘田 いずみ": ["Izumi Kitta", "킷타 이즈미", "Идзуми Китта", "橘田 泉"],
    "櫻井 孝宏": ["Takahiro Sakurai", "사쿠라이 타카히로", "Такахиро Сакураи", "櫻井 孝宏"],
    "水樹 奈々": ["Nana Mizuki", "미즈키 나나", "Нана Мидзуки", "水樹 奈奈"],
    "水橋 かおり": ["Kaori Mizuhashi", "미즈하시 카오리", "Каори Мидзухаси", "水橋 香織"],
    "江口 拓也": ["Takuya Eguchi", "에구치 타쿠야", "Такуя Эгучи", "江口 拓也"],
    "沢城 みゆき": ["Miyuki Sawashiro", "사와시로 미유키", "Миюки Саваширо", "澤城 美雪"],
    "沼倉 愛美": ["Manami Numakura", "누마쿠라 마나미", "Манами Нумакура", "沼倉 愛美"],
    "洲崎 綾": ["Aya Suzaki", "스자키 아야", "Ая Судзаки", "洲崎 綾"],
    "清水 彩香": ["Ayaka Shimizu", "시미즈 아야카", "Аяка Симидзу", "清水 彩香"],
    "渡辺 久美子": ["Kumiko Watanabe", "와타나베 쿠미코", "Кумико Ватанабэ", "渡邊 久美子"],
    "潘 めぐみ": ["Megumi Han", "한 메구미", "Мэгуми Хан", "潘 惠美"],
    "瀬戸 麻沙美": ["Asami Seto", "세토 아사미", "Асами Сэто", "瀨戶 麻沙美"],
    "玄田 哲章": ["Tessho Genda", "겐다 텟쇼", "Тэссё Гэнда", "玄田 哲章"],
    "生天目 仁美": ["Hitomi Nabatame", "나바타메 히토미", "Хитоми Набатамэ", "生天目 仁美"],
    "田中 理恵": ["Rie Tanaka", "타나카 리에", "Риэ Танака", "田中 理惠"],
    "田村 ゆかり": ["Yukari Tamura", "타무라 유카리", "Юкари Тамура", "田村 由香里"],
    "田辺 留依": ["Rui Tanabe", "타나베 루이", "Руи Танабэ", "田邊 留依"],
    "甲斐田 裕子": ["Yuko Kaida", "카이다 유코", "Юко Каида", "甲斐田 裕子"],
    "白石 涼子": ["Ryoko Shiraishi", "시라이시 료코", "Рёко Сираиси", "白石 涼子"],
    "白鳥 哲": ["Tetsu Shiratori", "시라토리 테츠", "Тэцу Сиратори", "白鳥 哲"],
    "皆口 裕子": ["Yuko Minaguchi", "미나구치 유코", "Юко Минагучи", "皆口 裕子"],
    "矢島 晶子": ["Akiko Yajima", "야지마 아키코", "Юко Минагучи", "矢島 晶子"],
    "石田 彰": ["Akira Ishida", "이시다 아키라", "Акира Исида", "石田 彰"],
    "神原 大地": ["Daichi Kanbara", "칸바라 다이치", "Даичи Камбара", "神原 大地"],
    "神谷 浩史": ["Hiroshi Kamiya", "카미야 히로시", "Хироши Камия", "神谷 浩史"],
    "福山 潤": ["Jun Fukuyama", "후쿠야마 쥰", "Дзюн Фукуяма", "福山 潤"],
    "秋元 羊介": ["Yosuke Akimoto", "아키모토 요스케", "Ёсукэ Акимото", "秋元 羊介"],
    "秦 佐和子": ["Sawako Hata", "하타 사와코", "Савако Хата", "秦 佐和子"],
    "種田 梨沙": ["Risa Taneda", "타네다 리사", "Риса Танеда", "種田 梨沙"],
    "立木 文彦": ["Fumihiko Tachiki", "타치키 후미히코", "Фумихико Тачики", "立木 文彥"],
    "立花 理香": ["Rika Tachibana", "타치바나 리카", "Рика Тачибана", "立花 理香"],
    "竹達 彩奈": ["Ayana Taketatsu", "타케타츠 아야나", "Аяна Такэтацу", "竹達 彩奈"],
    "細谷 佳正": ["Yoshimasa Hosoya", "호소야 요시마사", "Ёшимаса Хосоя", "細谷 佳正"],
    "紲星 あかり": ["Kizuna Akari", "키즈나 아카리", "Кизуна Акари", "紲星 燈"],
    "結月 ゆかり": ["Yuzuki Yukari", "유즈키 유카리", "Юзуки Акари", "結月 緣"],
    "緑川 光": ["Hikaru Midorikawa", "미도리카와 히카루", "Хикару Мидорикава", "綠川 光"],
    "緒方 恵美": ["Megumi Ogata", "오가타 메구미", "Мэгуми Огата", "緒方 惠美"],
    "能登 麻美子": ["Mamiko Noto", "노토 마미코", "Мамико Ното", "能登 麻美子"],
    "花江 夏樹": ["Natsuki Hanae", "하나에 나츠키", "Нацуки Ханаэ", "花江 夏樹"],
    "花澤 香菜": ["Kana Hanazawa", "하나자와 카나", "Кана Ханадзава", "花澤 香菜"],
    "若本 規夫": ["Norio Wakamoto", "와카모토 노리오", "Норио Вакамото", "若本 規夫"],
    "茅野 愛衣": ["Ai Kayano", "카야노 아이", "Аи Каяно", "茅野 愛衣"],
    "草尾 毅": ["Takeshi Kusao", "쿠사오 타케시", "Такэши Кусао", "草尾 毅"],
    "菊地 美香": ["Mika Kikuchi", "키쿠치 미카", "Мика Кикучи", "菊地 美香"],
    "蒼井 翔太": ["Shouta Aoi", "아오이 쇼타", "Сёта Аои", "蒼井 翔太"],
    "藤本 結衣": ["Yui Fujimoto", "후지모토 유이", "Юи Фудзимото", "藤本 結衣"],
    "藤田 曜子": ["Yoko Fujita", "후지타 요코", "Ёко Фудзита", "藤田 曜子"],
    "藤田 茜": ["Akane Fujita", "후지타 아카네", "Аканэ Фудзита", "藤田 茜"],
    "諏訪 彩花": ["Ayaka Suwa", "스와 아야카", "Аяка Сува", "諏訪 彩花"],
    "諏訪部 順一": ["Junichi Suwabe", "스와베 쥰이치", "Дзюнъичи Сувабэ", "諏訪部 順一"],
    "豊口 めぐみ": ["Megumi Toyoguchi", "토요구치 메구미", "Мэгуми Тоёгучи", "豐口 惠"],
    "豊崎 愛生": ["Aki Toyosaki", "토요사키 아키", "Аки Тоёсаки", "豐崎 愛生"],
    "近藤 佳奈子": ["Kanako Kondo", "콘도 카나코", "Канако Кондо", "近藤 佳奈子"],
    "速水 奨": ["Sho Hayami", "하야미 쇼", "Сё Хаями", "速水 獎"],
    "那須 晃行": ["Akiyuki Nasu", "나스 아키유키", "Акаюки Насу", "那須 晃行"],
    "金元 寿子": ["Hisako Kanemoto", "카네모토 히사코", "Хисако Канэмото", "金元 壽子"],
    "金田 アキ": ["Aki Kanada", "카나다 아키", "Аки Канада", "金田 晶"],
    "釘宮 理恵": ["Rie Kugimiya", "쿠기미야 리에", "Риэ Кугимия", "釘宮 理惠"],
    "鈴村 健一": ["Kenichi Suzumura", "스즈무라 켄이치", "Кэнъити Судзумура", "鈴村 健一"],
    "銀河 万丈": ["Banjo Ginga", "긴가 반죠", "Бандзё Гинга", "銀河 萬丈"],
    "長谷川 唯": ["Yui Hasegawa", "하세가와 유이", "Юи Хасэгава", "長谷川 唯"],
    "門脇 舞以": ["Mai Kadowaki", "카도와키 마이", "Маи Кадоваки", "門脇 舞以"],
    "関 智一": ["Tomokazu Seki", "세키 토모카즈", "Томокадзу Сэки", "關 智一"],
    "阿澄 佳奈": ["Kana Asumi", "아스미 카나", "Кана Асуми", "阿澄 佳奈"],
    "陶山 章央": ["Akio Suyama", "스야마 아키오", "Акио Суяма", "陶山 章央"],
    "雨宮 天": ["Sora Amamiya", "아마미야 소라", "Сора Амамия", "雨宮 天"],
    "飛田 展男": ["Nobuo Tobita", "토비타 노부오", "Нобуо Тобита", "飛田 展男"],
    "飯田 友子": ["Yuko Iida", "이이다 유우코", "Юко Иида", "飯田 友子"],
    "高木 友梨香": ["Yurika Takagi", "타카기 유리카", "Юрика Такаги", "高木 友梨香"],
    "高橋 未奈美": ["Minami Takahashi", "타카하시 미나미", "Минами Такахаши", "高橋 未奈美"],
    "高橋 李依": ["Rie Takahashi", "타카하시 리에", "Риэ Такахаши", "高橋 李依"],
    "高野 麻里佳": ["Marika Kono", "코우노 마리카", "Марика Коно", "高野 麻里佳"],
    "黒沢 ともよ": ["Tomoyo Kurosawa", "쿠로사와 토모요", "Томоё Куросава", "黑澤 朋世"],
    "こおろぎさとみ": ["Satomi Korogi", "코오로기 사토미", "Сатоми Короги", "興梠 里美"],
    "三宅 健太": ["Kenta Miyake", "미야케 켄타", "Кэнта Миякэ", "三宅 健太"],
    "諸星 すみれ": ["Sumire Morohoshi", "모로호시 스미레", "Сумирэ Морохоси", "諸星 堇"],
    "宮本 侑芽": ["Yume Miyamoto", "미야모토 유메", "Юмэ Миямото", "宮本 侑芽"],
    "川島 得愛": ["Tokuyoshi Kawashima", "카와시마 토쿠요시", "Токуёси Кавасима", "川島 得愛"],
    "田所 あずさ": ["Azusa Tadokoro", "타도코로 아즈사", "Адзуса Тадокоро", "田所 梓"],
    "森田 順平": ["Junpei Morita", "모리타 쥰페이", "Дзюмпэи Морита", "森田 順平"],
    # No existing KO translation; retain the established JP-name fallback.
    "上田 麗奈": ["Reina Ueda", "", "Уэда Рэйна", "上田 麗奈"],
    "入野 自由": ["Miyu Irino", "이리노 미유", "Ирино Мию", "入野 自由"],
    "梅原 裕一郎": ["Yuichiro Umehara", "우메하라 유이치로", "Умэхара Юитиро", "梅原 裕一郎"],
    "逢坂 良太": ["Ryota Osaka", "오오사카 료타", "Осака Рёта", "逢坂 良太"],
    "小原 好美": ["Konomi Kohara", "코하라 코노미", "Кохара Кономи", "小原 好美"],
    "白上 フブキ": ["Shirakami Fubuki", "시라카미 후부키", "Шираками Фубуки", "白上 吹雪"],
    "影山 シエン": ["Kageyama Shien", "카게야마 시엔", "Шиэн Кагеяма", "影山 紫炎"],
    "一 伊那尓栖": ["Ninomae Ina'nis", "니노마에 이나니스", "Ина'нис Ниномае", "一 伊那爾棲"],
    "日野 聡": ["Satoshi Hino", "히노 사토시", "Хино Сатоси", "日野 聰"],
    "原 由実": ["Yumi Hara", "하라 유미", "Хара Юми", "原 由實"],
    "闇ノ シュウ": ["Shu Yamino", "야미노 슈", "Ямино Сю", "Shu Yamino"],
    "星川 サラ": ["Hoshikawa Sara", "호시카와 사라", "Сара Хошикава", "星川 莎拉"],
    "葉加瀬 冬雪": ["Hakase Fuyuki", "하카세 후유키", "Фуюки Хакасе", "葉加瀨 冬雪"],
    "甲斐田 晴": ["Haru Kaida", "카이다 하루", "Каида Хару", "甲斐田 晴"],
    "津田 健次郎": ["Kenjiro Tsuda", "츠다 켄지로", "Цуда Кенджо", "津田 健次郎"],
    "鬼頭 明里": ["Akari Kito", "키토 아카리", "Кито Акари", "鬼頭 明里"],
    "Ｍ・Ａ・Ｏ": ["M・A・O", "M・A・O", "M・A・O", "M·A·O"],
    "山口 勝平": ["Kappei Yamaguchi", "야마구치 캇페이", "Каппэй Ямагути", "山口 勝平"],
    "楠 大典": ["Taiten Kusunoki", "쿠스노키 타이텐", "Таитэн Кусуноки", "楠 大典"],
    "小澤 亜李": ["Ari Ozawa", "오자와 아리", "Ари Одзава", "小澤 亞李"],
    "天宮 こころ": ["Amamiya Kokoro", "아마미야 코코로", "", "天宮 心"],
    "長尾 景": ["Nagao Kei", "나가오 케이", "", "長尾 景"],
    "魔使 マオ": ["Matsukai Mao", "마츠카이 마오", "", "魔使 真央"],
    "夜見 れな": ["Yorumi Rena", "요루미 레나", "", "夜見 蕾娜"],
    "石見 舞菜香": ["Manaka Iwami", "이와미 마나카", "", "石見 舞菜香"],
    "山下 誠一郎": ["Seiichiro Yamashita", "야마시타 세이이치로", "", "山下 誠一郎"],
    "水瀬 いのり": ["Inori Minase", "미나세 이노리", "", "水瀨 祈"],
    "内田 雄馬": ["Yuma Uchida", "우치다 유우마", "", "內田 雄馬"],
    "和氣 あず未": ["Azumi Waki", "와키 아즈미", "", "和氣 杏未"],
    "小市 眞琴": ["Makoto Koichi", "코이치 마코토", "", "小市 真琴"],
    "福西 勝也": ["Masaya Fukunishi", "후쿠니시 마사야", "", "福西 勝也"],
    "加藤 渉": ["Wataru Kato", "카토 와타루", "", "加藤 涉"],
    "河西 健吾": ["Kengo Kawanishi", "카와니시 켄고", "", "河西 健吾"],
    "福原 綾香": ["Ayaka Fukuhara", "후쿠하라 아야카", "", "福原 綾香"],
    "ファイルーズ あい": ["Ai Fairouz", "파이루즈 아이", "", "菲魯茲·藍"],
    "種﨑 敦美": ["Atsumi Tanezaki", "타네자키 아츠미", "", "種崎 敦美"],
    "市ノ瀬 加那": ["Kana Ichinose", "이치노세 카나", "", "市之瀨 加那"],
    "小林 千晃": ["Chiaki Kobayashi", "코바야시 치아키", "", "小林 千晃"],
    "阿部 敦": ["Atsushi Abe", "아베 아츠시", "", "阿部 敦"],
    "ささき のぞみ": ["Nozomi Sasaki", "사사키 노조미", "", "佐佐木 望"],
    "でびでび・でびる": ["Debidebi Debiru", "데비데비 데비루", "", "德比德比·德比魯"],
    "アルス・アルマル": ["Ars Almal", "아르스 아르말", "", "阿露絲·阿爾瑪"],
    "ニュイ・ソシエール": ["Nui Sociere", "뉴이 소시에르", "", "紐伊·索西艾瑞"],
    "竜胆 尊": ["Mikoto Rindou", "린도 미코토", "", "龍膽 尊"],
    "岡咲 美保": ["Miho Okasaki", "오카사키 미호", "", "岡咲 美保"],
    "日高 里菜": ["Rina Hidaka", "히다카 리나", "", "日高 里菜"],
    "永瀬 アンナ": ["Anna Nagase", "나가세 안나", "", "永瀨 安奈"],
    "五十嵐 梨花": ["Rika Igarashi", "이가라시 리카", "", "五十嵐 梨花"],
    "倉持 めると": ["Meruto Kuramochi", "쿠라모치 메루토", "", "倉持 妹路特"],
    "ソフィア・ヴァレンタイン": ["Sophia Valentine", "소피아 발렌타인", "", "蘇菲婭·瓦綸玎"],
    "狂蘭 メロコ": ["Meloco Kyoran", "쿄란 메로코", "", "Meloco Kyoran"],
    "伊藤 ゆいな": ["Yuina Ito", "이토 유이나", "", "伊藤 結衣奈"],
    "花守 ゆみり": ["Yumiri Hanamori", "하나모리 유미리", "", "花守 由美里"],
    "？？？": ["???", "???", "???", "？？？"],
    "": ["Unknown", "알 수 없는", "Неизвестно", ""],
}

# What to fall back to if a name hasn't been translated into your language.
# -1: Prefer falling back to JP over any other language
name_fallbacks = {0: -1,
                  1: -1,
                  2: 0,
                  3: -1}

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
    body = voice_desc_formats[LANG] + "{restriction}\n{cv}{actorname}".format(
        restriction = voice_restriction_extras[racensex][LANG],
        cv = cv_title[LANG],
        actorname = cv_name)

    return set_description(item, body)

# ——————————————————————————————
# OTHER ITEM RULES & TRANSLATION
# ——————————————————————————————

# This group covers face/head/CAST parts, Mag devices and capsules.

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
    ],
    # JP text:
    # マグのレベルや支援機能をリセットし\n
    # マグを初期の状態に戻すデバイス。
    "reset": [
        "Resets a Mag's appearance, stats,\n"
        "and support functions back to its \n"
        "default state.",
        "마그의 레벨과 지원 기능을 재설정 하고\n"
        "마그를 초기 상태로 되롤릴 수 있는 장치",
        "Сбрасывает внещний вид, хар-ки,\n"
        "и функции поддержки Mag'а до\n"
        "состояния по умолчанию.",
        "重置瑪古的等級與支援功能\n"
        "並使瑪古變回初始狀態的裝置。",
    ],
}

mag_extras = {
    # JP text:
    # ※『PSO2』ではLv.100以上の\n
    # 　マグにのみ使用可能
    "lv100": [
        "\n<yellow>※Must be used in PSO2 on a Mag\n"
        "which has reached Lv.100 or above.<c>",
        "\n<yellow>※『PSO2』에선 Lv.100이상의\n"
        "마그에서만 사용 가능<c>",
        "\n<yellow>※Только на MAG'e PSO2\n"
        "достигшем 100ур.+<c>",
        "\n<yellow>※在『PSO2』中僅可對\n"
        "　Lv.100或以上的瑪古使用<c>",
    ],
    # JP text:
    # ※『{game}』でのみ使用可能
    "game": [
        "\n<yellow>※Only usable in {game}.<c>",
        "\n<yellow>※『{game}』에서만 사용 가능<c>",
        "\n<yellow>※Только для {game}.<c>",
        "\n<yellow>※僅可在『{game}』中使用<c>",
    ],
}

# Capsule bodies and their category-specific notes.

capsule_formats = {
    # JP text:
    # 特殊能力を\n
    # 武器、防具に追加するカプセル。
    "normal": [
        "A capsule that adds a Special Ability\n"
        "to a weapon or piece of armor.",
        "무기와 방어구에\n"
        "특수 능력을 추가하는 캡슐.",
        "",
        "為武器、防具追加特殊能力的膠囊。",
    ],
    # JP text:
    # EX特殊能力を\n
    # 武器に追加するカプセル。
    "ex": [
        "A capsule that adds an EX Special\n"
        "Ability to a weapon.",
        "EX 특수 능력을\n"
        "무기에 추가하는 캡슐.",
        "",
        "為武器追加EX特殊能力的膠囊。",
    ],
}

capsule_extras = {
    # JP text:
    # アイテムラボの“強化素材交換”で\n
    # 特定のカプセルとの交換にも用いられる。
    "exchange": [
        "\nCan also be exchanged for specific\n"
        "capsules at the Item Lab.",
        "\n아이템 랩의 “강화 소재 교환”에서\n"
        "특정 캡슐과 교환하는 데도 사용된다.",
        "",
        "\n也可在道具實驗室的“交換強化素材”處\n"
        "用於交換特定的膠囊。",
    ],
    # KO source wording is retained; split the limit before the quantity.
    # JP text:
    # ★７以上のEX特殊能力は１つのみ追加可能
    "limit": [
        "\n<yellow>Only 1 EX Special Ability of\n"
        "7★ or above can be added<c>",
        "\n<yellow>★７ 이상의 EX 특수 능력은\n"
        "１개만 추가 가능<c>",
        "",
        "\n<yellow>僅可追加1個★7或以上的EX特殊能力<c>",
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

    # Translate the description.
    if item_type == "Personalcard":
        # Need to expand if needed
        return -1
    elif item_type.startswith("MagDevice"):
        body = mag_formats["evol"][LANG] if item_type == "MagDeviceEvol" else mag_formats["reset"][LANG]
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

    # Translate the description.
    if item_type in cosmeticsorted_types:
        body = ndesc_formats["n"][LANG].format(
            itype = cosmeticsorted_types[item_type][LANG],
            a = "" if item_type.endswith("s") else "a ",
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
}

# ——————————————————————————————
# MAIN PROCESS
# ——————————————————————————————

# [FUNCTION] Run one file through shared I/O, name handling, category translation and reporting.
def main_update(file_name):
    items_file_name = "Item_" + file_name + ".txt"
    path = os.path.join(json_loc, items_file_name)
    try:
        with open(path, mode='r', encoding='utf-8', newline='') as items_file:
            items = json.load(items_file)
    except FileNotFoundError:
        print("\t{0} not found.".format(items_file_name))
        return

    print("{0} loaded.".format(items_file_name) + " {")
    translate = description_translators[file_name]
    newtranslations = False
    for item in items:
        old_explain = item["tr_explain"]
        # Translate only the body; restore the green prefix even when translation is skipped.
        fill_cn_name(item)
        name_prefix = split_name_prefix(item)
        problem = translate(item, file_name, name_prefix)
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

    # Save CN name fills even when no description changed.
    with open(path, mode='w', encoding='utf-8', newline='') as items_file:
        json.dump(items, items_file, ensure_ascii=False, indent="\t", sort_keys=False)
        items_file.write("\n")

# [FUNCTION] Initialize the run once and dispatch every configured file through main_update.
def main(argv=None):
    global TRANS_ALL, LANG, REDO_ALL
    args = parse_arguments(argv)
    # CN always reprocesses descriptions, independent of -r.
    TRANS_ALL, LANG, REDO_ALL = args.all, args.lang, args.redo or args.lang == 3
    for file_name in description_translators:
        main_update(file_name)

if __name__ == '__main__':
    main()
