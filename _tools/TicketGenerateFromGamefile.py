import argparse
import os
import re
import json
import requests
import unicodedata
from collections import defaultdict
from time import sleep
from urllib.parse import quote, unquote
# Internal shared rules; this file remains the forward entry point.
from _ticket_gamefile.rules import (
    aug_texts,
    bg_texts,
    bp_texts,
    ca_texts,
    ha_texts,
    ma_texts,
    mo_names,
    mo_texts,
    no_explains,
    ph_texts,
    plain_formats,
    sv_texts,
    vo_explains,
    ca_itype_translations,
    contains_japanese,
    edit_special_text,
    equipment_common_suffixes,
    equipment_dot_translations,
    equipment_parentheses_translations,
    equipment_space_translations,
    equipment_suffix_separators,
    equipment_types,
    format_common_suffix,
    form_vo_names,
    get_table_jp_target_lines,
    get_target_lines,
    iter_equipment_structures,
    json_paths,
    lang_names,
    min_assign_digits,
    mo_itypes,
    numeric_order,
    remove_dummy_lines,
    resolve_language,
    ring_slash_translations,
    ring_type_translations,
    source_for_prefix,
    source_files,
    csv_path,
    split_common_suffix,
    split_type_parentheses,
    start_assigns,
    strip_series_suffix,
    upgrade_material_en_separators,
    upgrade_material_type_separators,
    upgrade_material_types,
    width_process_string,
)

# ——————————————————————————————
# LANGUAGE SETTING
# ——————————————————————————————

# This tool updates existing json files ("Stack_", weapons, weapon camos, units and rings) from the main game files.
# Append --debug to run normally and print changes without writing JSON.

# None follows the current branch; --lang overrides this setting.
# 1: CN (local text.ini); 2: EN, 3: KO, 4: RU, 5: TH (online CSV).
LANG = None

# ——————————————————————————————
# PATH & URL SETTING
# ——————————————————————————————

# Path of root folder
root_dir = os.path.dirname(os.path.abspath(__file__))

# Path of main game file CN respository (Won't affect other modes)
PSO2CN_path = os.path.abspath(os.path.join(root_dir, os.pardir, os.pardir, r"PSO2_CHN_Translation"))
# URL of the Arks-Layer CSV repository
PSO2CSV_url = "https://raw.githubusercontent.com/Arks-Layer/PSO2ENPatchCSV/"

# Paths of CN main game files
UI_path = r"UI"
ngs_path = os.path.join("Unsorted", "ngs")
common_cn_path = os.path.join(PSO2CN_path, UI_path, "common.text.ini")
accessories_cn_path = os.path.join(PSO2CN_path, UI_path, "ui_accessories_text.text.ini")
charamake_parts_cn_path = os.path.join(PSO2CN_path, UI_path, "ui_charamake_parts.text.ini")
element_name_cn_path = os.path.join(PSO2CN_path, UI_path, "item_element_name_reb.text.ini")
lineduel_text_cn_path = os.path.join(PSO2CN_path, ngs_path,"lineduel_text.text.ini")
item_series_name_cn_path = os.path.join(PSO2CN_path, UI_path, "item_series_name.text.ini")
ui_item_cn_path = os.path.join(PSO2CN_path, UI_path, "ui_item.text.ini")
bgmlist_text_cn_path = os.path.join(PSO2CN_path, UI_path, "ui_bgmlist_text.text.ini")
# URLs of JP main game files
csv_url = "JP/Files/"
csv_reboot_url = "JP_Reboot/Files/"
common_jp_url = f"{PSO2CSV_url}{csv_reboot_url}common.csv"
accessories_jp_url = f"{PSO2CSV_url}{csv_url}ui_accessories_text.csv"
charamake_parts_jp_url = f"{PSO2CSV_url}{csv_url}ui_charamake_parts.csv"
element_name_jp_url = f"{PSO2CSV_url}{csv_url}item_element_name_reb.csv"
lineduel_text_jp_url = f"{PSO2CSV_url}{csv_reboot_url}lineduel_text.csv"
item_series_name_jp_url = f"{PSO2CSV_url}{csv_url}item_series_name.csv"
ui_item_jp_url = f"{PSO2CSV_url}{csv_reboot_url}ui_item.csv"
bgmlist_text_jp_url = f"{PSO2CSV_url}{csv_reboot_url}ui_bgmlist_text.csv"

# Initialize tradable info of each prefix
trade_infos = defaultdict(dict)

# URLs of swiki/makapo
wiki_urls = {
    'ngs': 'https://pso2ngs.swiki.jp/index.php?',
    'o2': 'https://pso2.swiki.jp/index.php?',
    'makapo': 'https://ngs.pso2-makapo.com/'}
# URLs and prefixes of trade_infos mapping of swiki/makapo pages (only for CN)
trade_mapping = {
    'ngs_mo': ('モーション', ("mo", )),
    'makapo_bp': ('build-parts-list', ("bp", )),
    'ngs_bp1': ('ビルドパーツ/建材', ("bp", )),
    'ngs_bp2': ('ビルドパーツ/建築物・道具・器具', ("bp", )),
    'ngs_bp3': ('ビルドパーツ/自然物', ("bp", )),
    'ngs_bp4': ('ビルドパーツ/家具', ("bp", )),
    'ngs_bp5': ('ビルドパーツ/ギミックパーツ', ("bp", )),
    'ngs_bp6': ('ビルドパーツ/立体図形', ("bp", )),
    'ngs_bp7': ('ビルドパーツ/コラボ', ("bp", )),
    'ngs_ph': ('ポータブルホログラム', ("ph", )),
    'ngs_bg': ('アークスカード', ("bg", )),
    'ngs_ma': ('ラインストライク', ("ma", "sv", )),
    'ngs_vo': ('エステ/ボイス', ("vo", )),
    'o2_vo': ('エステ/ボイス', ("vo", )),
    'ngs_un': ('防具', ("un", )),
    'ngs_wp': ('ソード', ("wp", )),
    'ngs_wc': ('武器迷彩', ("wc", )),
    'ngs_wc_old': ('武器迷彩/実装情報（過去分）', ("wc", )),
    'ngs_um': ('素材アイテム', ("um", )),
    # All music discs are tradable by default (uncomment to get untradable ones from swiki)
    # 'ngs_md': ('ミュージックディスク', ("md", ))
    }
# swiki pages with one item per table row, and the column of item names
# (weapons of other types are found by sword series)
row_wiki_pages = {'防具': 2, 'ソード': 2, 'ミュージックディスク': 1,
                  '武器迷彩': 1, '武器迷彩/実装情報（過去分）': 1,
                  '素材アイテム': 2}
# Path of json folder
jsonfile_dir = os.path.abspath(os.path.join(root_dir, os.pardir, "json"))


# ——————————————————————————————
# FUNCTION
# ——————————————————————————————

# [FUNCTION] Override the branch language and enable log-only debugging.
def parse_arguments(argv=None):
    parser = argparse.ArgumentParser(description="Update JSON translations from game files.")
    parser.add_argument('--debug', action='store_true', help='Print normal logs without writing target files')
    parser.add_argument('--lang', choices=lang_names[1:], help='Override the current branch language')
    arguments = parser.parse_args(argv)
    try:
        arguments.lang = resolve_language(arguments.lang if arguments.lang is not None else LANG,
                                          os.path.dirname(root_dir))
    except ValueError as error:
        parser.error(str(error))
    return arguments

# [FUNCTION] Print the title of a stage
def print_stage(title):
    print(f"\n{'=' * 64}\n  {title}\n{'=' * 64}")

# [FUNCTION] Print a status line, e.g. "  LOADED   common.csv"
def print_status(status, message):
    print(f"  {status:<9}{message}")

# [FUNCTION] Report the json items without complete translations
def report_untranslated(untranslated_texts):
    if untranslated_texts:
        print_status("CAUTION", f"{len(untranslated_texts)} items without complete translations (left unchanged)")

# [FUNCTION] Load and read the webpage from URL
def get_web(url):
    url_part = url.rsplit('/', 1)[-1].split('?', 1)[-1]
    # Match the reverse tool's timeout/retries; requests retains URL and charset handling.
    for attempt in range(3):
        try:
            with requests.get(url, timeout=30) as response:
                response.raise_for_status()
                lines = response.text
        except requests.RequestException as error:
            status = error.response.status_code if error.response is not None else None
            if status == 404:
                print_status("FAILED", f"File does not exist: {url} (skipped)")
                return None
            if attempt == 2 or (status is not None and status < 500):
                print_status("FAILED", f"{url} ({error})")
                raise
            print_status("RETRY", f"{url_part} (attempt {attempt + 2}/3; {error})")
            sleep(attempt + 1)
        else:
            print_status("LOADED", url_part)
            return lines

# [FUNCTION] Split .ini line into ori_text and tr_text besides the "="
def split_ini_line(line):
    equals_count = line.count("=")
    if equals_count % 2 == 1:  # Odd number =
        middle_index = equals_count // 2
        split_pos = line.index("=", line.index("=") * middle_index + middle_index)
    else:  # Even number =
        split_pos = line.rindex("=")
    return line[:split_pos], line[split_pos + 1:]

# [FUNCTION] Parse the web or file
def parse_data(file_path, file_type):
    page_path = file_path.split("#", 1)[0]
    is_upgrade_page = file_type == "html" and page_path.endswith("素材アイテム")
    # Determine the type of file_path
    if file_path.startswith("http"):
        try:
            data = get_web(file_path)
        except requests.RequestException:
            if not is_upgrade_page:
                raise
            return [], {}
        if data is None:
            return [], {}
        if is_upgrade_page:
            section = re.search(r'<h2\b[^>]*id="strengthening"[^>]*>.*?(?=<h2\b)', data or "", re.S)
            if section is None:
                return [], {}
            data = section.group()
        lines = data.splitlines()
    else:
        try:
            with open(file_path, encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            print_status("FAILED", f"File does not exist: {file_path} (skipped)")
            return [], {}
        print_status("LOADED", os.path.basename(file_path))

    parsed_lines = []
    trade_infos = {}

    for i, line in enumerate(lines):
        line = line.rstrip('\n')

        # Process .text.ini files
        if file_type == "ini":
            # Get ori_text and tr_text besides the "="
            if "=" in line:
                ori_text, tr_text = split_ini_line(line)
                trade_infos[ori_text] = ""
                parsed_lines.append((ori_text, tr_text))
            # Get the trade_infos from comments (mainly for augments)
            if line.startswith(";"):
                if line.startswith(";不可交易") and i > 0:
                    ori_text = split_ini_line(lines[i - 1].rstrip('\n'))[0]
                    trade_infos[ori_text] = "Untradable"

        # Process .csv files
        elif file_type == "csv":
            if ',"""' not in line:
                continue
            text_id, jp_text = line.strip().split(',"""', 1)
            # Remove """ at the end of line
            jp_text = jp_text[:-3]
            # Replace some characters
            jp_text = jp_text.replace('\\u3000', '　').replace('\\""', '"')
            parsed_lines.append((text_id.strip(), jp_text))

        # Process .html files
        elif file_type == "html":
            is_camo_page = "武器迷彩" in file_path
            if is_camo_page:
                line = line.lstrip()
            if line.startswith('<div class="ie5">') or line.startswith(' data-ad-slot='):
                # For items in table rows (one item per table row)
                name_column = next((column for page, column in row_wiki_pages.items() if page_path.endswith(page)), None)
                if name_column is not None:
                    shared_explain, shared_rows = "", 0
                    for row in line.split("<tr>"):
                        cell_data = re.findall(r"<td([^>]*)>(.*?)</td>", row)
                        cells = [text for _, text in cell_data]
                        if len(cells) <= name_column:
                            shared_explain, shared_rows = "", 0
                            continue
                        trade_info = "Untradable"
                        if is_upgrade_page:
                            # The material's own explanation may span its I/II/III rows.
                            if len(cells) == 5:
                                shared_explain = cells[4]
                                span = re.search(r'rowspan="(\d+)"', cell_data[4][0])
                                shared_rows = int(span.group(1)) if span else 1
                            elif len(cells) != 4 or shared_rows <= 0:
                                shared_explain, shared_rows = "", 0
                                continue
                            shared_rows -= 1
                            if "#equipment_upgrade" not in shared_explain:
                                continue
                            trade_info = "Untradable" if "マイショップ出品不可" in shared_explain else ""
                        elif is_camo_page:
                            if len(cells) <= name_column + 1:
                                continue
                            source = unquote(cells[-1])
                            source += re.sub(r"<[^>]+>", "", source)
                            if not any(keyword in source for keyword in (
                                'マイショップ出品不可', 'SGスクラッチ', 'alt="SG"', 'SG.png',
                                'スペシャルスクラッチ', 'SPスクラッチ', 'イベント', 'キャンペーン', '称号', '交換', 'タスク', 'Task')):
                                continue
                        elif "マイショップ出品不可" not in row:
                            continue
                        # The cell of item names, which are separated by <br>
                        for name in cells[name_column].split('<br class="spacer" />'):
                            jp_text = re.sub(r"<[^>]+>", "", name).strip()
                            if jp_text:
                                trade_infos[jp_text] = trade_info
                # For items with "「」"
                elif "ngs" in file_path and not "エステ" in file_path:
                    headnames = ['Mo', 'BP', 'PH', 'Bg', 'Ma', 'Sv']
                    for headname in headnames:
                        # Do regex replacement, to ensure each line starts with item names
                        n_lines = re.sub(f"{headname}「", f"\n{headname}「", line).splitlines()
                        makapo_started = False
                        for n_line in n_lines:
                            if n_line.startswith(f"{headname}「"):
                                jp_text = n_line[n_line.find(f"{headname}「") + 3:n_line.find('」')]
                                if makapo_started or any(keyword in n_line for keyword in
                                    ['マイショップ出品不可', '初期', 'alt="GP"', 'alt="SG"', '交換</td>', '季節イベント</td>','トレジャースクラッチ', 'SPスクラッチ</td>', '開発準備特別票</td>', 'クラス育成特別プログラム', '初期登録</td>']):
                                    trade_infos[jp_text] = "Untradable"
                            # Force to change the makapo tradable info after specific line
                            if any(keyword in n_line for keyword in
                                ['<span id="GPNGS">']):
                                makapo_started = True
                            
                # For items without "「」"
                else: 
                    headnames = ['男性', '女性', 'T1', 'T2']
                    for headname in headnames:
                        # Do regex replacement, to ensure each line starts with item names
                        n_lines = re.sub(f"{headname}", f"\n{headname}", line).splitlines()
                        for n_line in n_lines:
                            if n_line.startswith(f"{headname}"):
                                jp_text = n_line[n_line.find(f"{headname}") :n_line.find('</td>')]
                                if any(keyword in n_line for keyword in
                                    ['マイショップ出品不可', 'SG.png']):
                                    trade_infos[jp_text] = "Untradable"

    return parsed_lines, trade_infos

# [FUNCTION] Parse the commented translations (";JP=TR") of .ini file
def parse_ini_comment_translations(file_path):
    translations = {}
    if not os.path.isfile(file_path):
        return translations
    with open(file_path, encoding='utf-8') as f:
        for line in f:
            if line.startswith(";") and "=" in line:
                key, value = line[1:].rstrip("\r\n").split("=", 1)
                translations[key] = value
    return translations


# [FUNCTION] Parse the web to get trade info
def parse_info(key, mapping):
    suffix_url, prefixes = mapping[key]
    source = key.split('_')[0]
    full_url = f"{wiki_urls[source]}{suffix_url}"

    n_infos = parse_data(full_url, "html")[1]
    # Also record items with names in a different width
    for jp_text, trade_info in list(n_infos.items()):
        n_infos[width_process_string(jp_text)] = trade_info
    for prefix in prefixes:
        trade_infos[prefix].update(n_infos)


# [FUNCTION] Get translations of jp_target_lines from tr_lines (None if not found)
def get_translation(jp_target_lines, tr_lines):
    # CN translations are found by JP text, others are found by text_id
    translations = {}
    for key, tr_text in tr_lines:
        translations.setdefault(key, tr_text)

    tr_target_texts = []
    for text_id, jp_text, *jp_refer in jp_target_lines:
        tr_text = translations.get(jp_text if LANG == 1 else text_id)
        # A copied JP source is not a translation and must not erase a JSON name.
        if LANG != 1 and tr_text == jp_text and contains_japanese(jp_text):
            tr_text = None
        if not tr_text:
            print_status("CAUTION", f"No translation for {jp_text}")
        tr_target_texts.append(tr_text)
    return tr_target_texts


# [FUNCTION] Build series records (sorted by length of JP name) from "item_series_name"
def build_equipment_series_records():
    translated_by_source = dict(item_series_name_tr_lines)
    records = []
    for text_id, jp_text in item_series_name_jp_lines:
        jp_base = strip_series_suffix(jp_text)
        if not jp_base or jp_base.startswith("￥"):
            continue
        translated_key = jp_text if LANG == 1 else text_id
        translated_base = strip_series_suffix(translated_by_source.get(translated_key, ""))
        if not translated_base or translated_base == "-" or translated_base.startswith("￥"):
            continue
        if LANG != 1 and contains_japanese(translated_base):
            continue
        records.append({
            "text_id": text_id,
            "jp_base": jp_base,
            "translated_base": translated_base
        })
    # Commented translations also contain series which are not in game files (e.g. ";ディケイム=拾式")
    for jp_base, translated_text in item_series_name_comment_tr.items():
        records.append({
            "jp_base": jp_base,
            "translated_base": strip_series_suffix(translated_text)
        })
    records.sort(key=lambda record: len(record["jp_base"]), reverse=True)
    records_by_base = {}
    for record in records:
        records_by_base.setdefault(record["jp_base"], record)
    return records, records_by_base

# [FUNCTION] Get translation of small series from comments or full series name
def get_small_series_translation(parent_base, small_name, records_by_base):
    translated = item_series_name_comment_tr.get(small_name, "")
    if translated:
        return strip_series_suffix(translated)

    root_record = records_by_base.get(parent_base)
    if not root_record:
        return None
    root_name = root_record["translated_base"]
    for jp_separator in ("・", ""):
        full_record = records_by_base.get(f"{parent_base}{jp_separator}{small_name}")
        if not full_record:
            continue
        full_name = full_record["translated_base"]
        for separator in ("·", "・", " ", "-", ""):
            prefix = root_name + separator
            if full_name.startswith(prefix):
                small_translation = full_name[len(prefix):].strip()
                if small_translation:
                    return small_translation
    return None


# [FUNCTION] Translate the common suffix
# Roman numerals: JP/KO keep "Ⅱ", CN uses "2", EN/RU/TH use "II".
def translate_common_suffix(jp_suffix):
    return format_common_suffix(jp_suffix, LANG)


# [FUNCTION] Get the separator between parts of translated equipment name
# CN only adds "·" where JP has "・"; non-CN always uses space
def get_equipment_separator(has_dot):
    return equipment_dot_translations[LANG] if has_dot else equipment_space_translations[LANG]

# [FUNCTION] Render the translated name from structure, return None if any part has no translation
def render_equipment_structure(structure, translated_type, records_by_base, type_separator=None):
    result = structure["record"]["translated_base"]
    for parent_base, small_name, has_dot in structure["pre"]:
        translated_small = get_small_series_translation(parent_base, small_name, records_by_base)
        if not translated_small:
            return None
        result += get_equipment_separator(has_dot) + translated_small
    if structure["has_type"]:
        result += (get_equipment_separator(False) if type_separator is None else type_separator) + translated_type
    for parent_base, small_name, has_dot in structure["post"]:
        translated_small = get_small_series_translation(parent_base, small_name, records_by_base)
        if not translated_small:
            return None
        result += get_equipment_separator(has_dot) + translated_small
    return result

# [FUNCTION] Match the equipment name, return (structure, translated name, common suffix)
# (None, None, common suffix) if there is no complete translation
def match_equipment_name(jp_text, type_names, series_records, records_by_base, type_separator=None):
    jp_type = type_names[0]
    translated_type = type_names[LANG]
    if translated_type is None:
        return None, None, ""
    stem, jp_suffix = split_common_suffix(jp_text)
    stem, in_parentheses = split_type_parentheses(stem, jp_type)

    for structure in iter_equipment_structures(stem, jp_type, series_records, records_by_base):
        # The stem has no type if the type is in parentheses
        if in_parentheses and structure["has_type"]:
            continue
        translated_name = render_equipment_structure(structure, translated_type, records_by_base, type_separator)
        if translated_name is None:
            continue
        if in_parentheses:
            left, right = equipment_parentheses_translations[LANG]
            translated_name += f"{get_equipment_separator(False)}{left}{translated_type}{right}"
        if jp_suffix:
            translated_name += equipment_suffix_separators[LANG] + translate_common_suffix(jp_suffix)
        return structure, translated_name, jp_suffix
    return None, None, jp_suffix

# [FUNCTION] Get the series key of equipment, which is shared by all weapon types
# (series, small series after type, common suffix), e.g. ("クレス", (), "AT") for "クレス・デイブルソードAT"
def get_equipment_series_key(structure, jp_suffix):
    post_names = tuple(small_name for _, small_name, _ in structure["post"])
    return structure["series_record"]["jp_base"], post_names, jp_suffix

# [FUNCTION] Get series keys of untradable equipment from trade info
def get_untradable_series_keys(trade_infos, type_names, series_records, records_by_base):
    series_keys = set()
    for jp_text, trade_info in trade_infos.items():
        if trade_info != "Untradable":
            continue
        structure, _, jp_suffix = match_equipment_name(jp_text, type_names, series_records, records_by_base)
        if structure:
            series_keys.add(get_equipment_series_key(structure, jp_suffix))
    return series_keys

# [FUNCTION] Get tradable info of equipment by its name or series
def get_equipment_trade_info(jp_text, structure, jp_suffix, trade_infos, untradable_series_keys):
    if trade_infos.get(jp_text) == "Untradable" or get_equipment_series_key(structure, jp_suffix) in untradable_series_keys:
        return "Untradable"
    return ""

# [FUNCTION] Remove "／リング" and descriptions from ring skill name
def strip_ring_skill_name(text):
    return text.split("<br>", 1)[0].replace("／リング", "").replace("/リング", "").strip()

# [FUNCTION] Split the card text of "Stack_" json file into (name, prefix, element, cost and rarity)
def parse_card_stack_text(stack_text):
    if not stack_text.startswith("Ca「") or not stack_text.endswith("」"):
        return None
    separator = stack_text.find("：", 3)
    if separator < 0:
        return None
    type_and_cost = stack_text[3:separator]
    element = next((key for key in ca_itype_translations if type_and_cost.startswith(key)), None)
    if element is None:
        return None
    return stack_text[separator + 1:-1], stack_text[:separator + 1], element, type_and_cost[len(element):]

# [FUNCTION] Form the card texts using the shared language templates.
def form_card_texts(stack_text, translated_name):
    parsed_text = parse_card_stack_text(stack_text)
    if parsed_text is None:
        return [stack_text] * len(lang_names)
    _, jp_prefix, element, cost_and_rarity = parsed_text
    translated_element = ca_itype_translations[element]
    texts = [template.format(tr_itype=translated_element[index], cost=cost_and_rarity,
                             tr_text=translated_name) if template and translated_element[index] else ""
             for index, template in enumerate(ca_texts)]
    texts[0] = stack_text
    return texts

# [FUNCTION] Form the entry of item which only has a translated name (equipment, rings and upgrade materials)
def form_name_entry(jp_text, translated_name, trade_info):
    names = [jp_text] + [translated_name] * (len(lang_names) - 1)
    return {"names": names, "texts": names, "explains": no_explains,
            "trade_info": trade_info, "untranslated": jp_text == translated_name}

# [FUNCTION] Update the translation of json item from the entry
# entry: names/texts/explains in lang_names order, trade info, and untranslated status
def form_itemdata(item, entry):
    names, texts = entry["names"], entry["texts"]

    # Remove the translated name from the existing explain
    rec_tr_explain = item["tr_explain"]
    if "<green>“" in rec_tr_explain:
        rec_tr_explain = rec_tr_explain[rec_tr_explain.find('”<c>\n') + 5:]
    # Retain the extra part of the existing explain
    tr_explain = entry["explains"][LANG]
    if tr_explain in rec_tr_explain:
        tr_explain += rec_tr_explain[rec_tr_explain.find(tr_explain) + len(tr_explain):]

    # For tradable items in CN mode
    if LANG == 1 and (names[0] != names[LANG]) and entry["trade_info"] != "Untradable":
        item["tr_text"] = texts[0]
        item["tr_explain"] = f"<green>“{texts[LANG]}”<c>\n{tr_explain}"
    # For untranslated items in CSV modes
    elif LANG != 1 and entry["untranslated"] and contains_japanese(names[LANG]):
        item["tr_text"] = ""
        item["tr_explain"] = tr_explain
    # For untradable items or CSV modes
    else:
        item["tr_text"] = texts[LANG]
        item["tr_explain"] = tr_explain

# [FUNCTION] Render JSON and write it unless command-line debugging is enabled
def write_to_json(processed_items, jsonfile_dir, path):
    processed_lines = json.dumps(list(processed_items), ensure_ascii=False, indent="\t") + "\n"
    if args.debug:
        return
    with open(os.path.join(jsonfile_dir, path), "w", encoding='utf-8') as f:
        f.write(processed_lines)

# ——————————————————————————————
# PRESET PROCESSES
# ——————————————————————————————

args = parse_arguments()
LANG = lang_names.index(args.lang)
print_stage(f"Forward update ({args.lang}; online JP, "
            f"{'local' if LANG == 1 else 'online'} gamefiles)")
if LANG == 1:
    print_status("GAMEFILE", PSO2CN_path)
else:
    print_status("GAMEFILE", f"{PSO2CSV_url}{args.lang}/")
    print_status("GAMEFILE", f"{PSO2CSV_url}{args.lang}_Reboot/")
print_status("JSON", jsonfile_dir)
if args.debug:
    print_status("DEBUG", "Log only; target files will not be written")

# Parse JP webs, to read the lines need to be considered
print_stage("Loading JP game files")
common_jp_lines = parse_data(common_jp_url, "csv")[0]
accessories_jp_lines = parse_data(accessories_jp_url, "csv")[0]
charamake_parts_jp_lines = parse_data(charamake_parts_jp_url, "csv")[0]
element_name_jp_lines = parse_data(element_name_jp_url, "csv")[0]
lineduel_text_jp_lines = parse_data(lineduel_text_jp_url, "csv")[0]
item_series_name_jp_lines = parse_data(item_series_name_jp_url, "csv")[0]
ui_item_jp_lines = parse_data(ui_item_jp_url, "csv")[0]
bgmlist_text_jp_lines = parse_data(bgmlist_text_jp_url, "csv")[0]

# Parse CN text.ini or the selected language's CSV translations.
if LANG == 1:
    print_stage(f"Loading {lang_names[LANG]} translations")
    common_tr_lines = parse_data(common_cn_path, "ini")[0]
    accessories_tr_lines = parse_data(accessories_cn_path, "ini")[0]
    charamake_parts_tr_lines = parse_data(charamake_parts_cn_path, "ini")[0]
    element_name_tr_lines, trade_infos["aug"] = parse_data(element_name_cn_path, "ini")
    lineduel_text_tr_lines = parse_data(lineduel_text_cn_path, "ini")[0]
    item_series_name_tr_lines = parse_data(item_series_name_cn_path, "ini")[0]
    item_series_name_comment_tr = parse_ini_comment_translations(item_series_name_cn_path)
    ui_item_tr_lines, trade_infos["rg"] = parse_data(ui_item_cn_path, "ini")
    bgmlist_text_tr_lines = parse_data(bgmlist_text_cn_path, "ini")[0]
else:
    print_stage(f"Loading {lang_names[LANG]} translations")
    csv_urls = {name: f"{PSO2CSV_url}{args.lang}{'_Reboot' if reboot else ''}/{quote(csv_path(name, args.lang))}"
                for name, (reboot, _) in source_files.items()}
    common_tr_lines = parse_data(csv_urls["common"], "csv")[0]
    accessories_tr_lines = parse_data(csv_urls["ui_accessories_text"], "csv")[0]
    charamake_parts_tr_lines = parse_data(csv_urls["ui_charamake_parts"], "csv")[0]
    element_name_tr_lines = parse_data(csv_urls["item_element_name_reb"], "csv")[0]
    lineduel_text_tr_lines = parse_data(csv_urls["lineduel_text"], "csv")[0]
    item_series_name_tr_lines = parse_data(csv_urls["item_series_name"], "csv")[0]
    item_series_name_comment_tr = {}
    ui_item_tr_lines = parse_data(csv_urls["ui_item"], "csv")[0]
    bgmlist_text_tr_lines = parse_data(csv_urls["ui_bgmlist_text"], "csv")[0]

# Material rows also identify the supported equipment upgrade scope in CSV modes.
print_stage("Loading material/tradable info from swiki/makapo")
for key in trade_mapping:
    if LANG == 1 or key == "ngs_um":
        parse_info(key, trade_mapping)

# Find series records of weapons and units
equipment_series_records, equipment_series_by_base = build_equipment_series_records()

# ——————————————————————————————
# MAPPINGS AND CONDITIONS
# ——————————————————————————————


def edit_sp_texts(prefix, jp_text, tr_text, jp_refer):
    return edit_special_text(prefix, jp_text, tr_text, jp_refer, LANG)

# Select the same JP tables in both directions.
translation_sources = {
    "common": common_tr_lines,
    "ui_accessories_text": accessories_tr_lines,
    "ui_charamake_parts": charamake_parts_tr_lines,
    "item_element_name_reb": element_name_tr_lines,
    "lineduel_text": lineduel_text_tr_lines,
    "ui_bgmlist_text": bgmlist_text_tr_lines,
    "item_series_name": item_series_name_tr_lines,
    "ui_item": ui_item_tr_lines,
}
jp_sources = {
    "common": common_jp_lines,
    "ui_accessories_text": accessories_jp_lines,
    "ui_charamake_parts": charamake_parts_jp_lines,
    "item_element_name_reb": element_name_jp_lines,
    "lineduel_text": lineduel_text_jp_lines,
    "ui_bgmlist_text": bgmlist_text_jp_lines,
    "item_series_name": item_series_name_jp_lines,
    "ui_item": ui_item_jp_lines,
}
game_target_lines = {
    prefix: (entries, translation_sources[source_for_prefix[prefix]])
    for prefix, entries in get_target_lines(jp_sources).items()
}


# [FUNCTION] Conditions of force to change the tradable info (only for CN)
def extra_condition(prefix, jp_text, text_id, trade_info=""):
    if prefix == "mo":
        return jp_text.endswith("EX")
    elif prefix == "bp":
        return (jp_text.startswith((
        # NGS
        "エアル：", "リテナ：", "ノクト：", "エウロ：", "クヴァル：", "ピエド：", "ワフウ：", "スティラ：", "ネムレス：", "ネオネム：",
        "『NGS", "『PSO2", "超・", "立体図形：", "立体数字：", "アクリル台座・", "ラインストライク",
        # PSO2 Theme
        "ベーシック", "モダン", "ゴシック", "クラシック", "スイート", "エキゾチックトラッド", "ウェスタン", "ワノ", "レトロ", "オールド", "ファンシー", "ラボラトリー", "エレガント", "ナイトクラブ", "ウッディ", "学校の", "リゾート", "ビンテージ",
        # PSO2 Others
        "スペースシップ", "オッソリア",
        # Mini
        "ミニ")) and not jp_text.startswith("ミニミニ")
        )
    elif prefix == "aug":
        return jp_text.endswith(("S", "LC"))
    elif prefix == "ca":
        card_text = parse_card_stack_text(jp_text)
        return (text_id.endswith("0#0") or trade_info == "Untradable") and not (
            card_text and card_text[3].endswith(("G", "Ex")))
    elif prefix == "ha":
        return True
    elif prefix in ("un", "wp"):
        return jp_text.endswith("AT")
    return False

# ——————————————————————————————
# MAIN PROCESS
# ——————————————————————————————

# [FUNCTION] Get entries of game items
# Entry builders return get_entry(path, item) to find the entry of json item (None to leave it unchanged),
# and report() to print the missing translation info
def build_game_entries(prefix):
    jp_target_lines, tr_lines = game_target_lines[prefix]
    tr_target_texts = get_translation(jp_target_lines, tr_lines)
    prefix_trade_infos = trade_infos[prefix]
    # Cards are found by name, others are found by text
    entries = {}
    missing_translation_count = 0
    text_formats = plain_formats if prefix == "ca" else globals().get(f"{prefix}_texts", plain_formats)

    for (text_id, jp_text, *jp_refer), tr_text in zip(jp_target_lines, tr_target_texts):
        missing_translation = not tr_text
        # Edit special texts of special item
        jp_text, tr_text = edit_sp_texts(prefix, jp_text, tr_text or "", jp_refer)
        fields = {"jp_itype": "", "tr_itype": "", "cv_tr_name": ""}
        # Get category and the category name for certain prefixes
        if prefix == "mo":
            itype = mo_itypes[text_id.split("_")[1]]
            fields.update(jp_itype = itype[0], tr_itype = itype[LANG])
            missing_translation |= itype[LANG] is None
        missing_translation |= tr_text is None or text_formats[LANG] is None
        # Get all names of voice
        name_pairs = [(jp_text, tr_text)]
        if prefix == "vo":
            jp_texts, tr_texts, fields["cv_tr_name"] = form_vo_names(text_id, jp_text, tr_text)
            name_pairs = zip(jp_texts, tr_texts)

        for jp_name, tr_name in name_pairs:
            # Get names, texts and explains from global variables
            fields.update(jp_text = jp_name, tr_text = tr_name)
            names = [name.format(**fields) if name is not None else "" for name in globals().get(f"{prefix}_names", plain_formats)]
            texts = [text.format(**fields) if text is not None else "" for text in text_formats]
            explains = [explain.format(**fields) if explain is not None else "" for explain in globals().get(f"{prefix}_explains", no_explains)]
            # Get tradable info of all lines (e.g. a card is untradable if any of its lines is untradable)
            if extra_condition(prefix, jp_name, text_id):
                prefix_trade_infos[names[0]] = "Untradable"
            key = names[0] if prefix == "ca" else texts[0]
            if missing_translation or key in entries:
                continue
            entries[key] = {"names": names, "texts": texts, "explains": explains,
                            "untranslated": names[0] == names[LANG] or jp_name == tr_name}
        missing_translation_count += missing_translation

    # Also find items with names in a different width
    alt_entries = {}
    for key, entry in entries.items():
        alt_entries.setdefault(key.replace(entry["names"][0], width_process_string(entry["names"][0]), 1), entry)

    def get_entry(path, item):
        key = item["jp_text"]
        if prefix == "ca":
            card_text = parse_card_stack_text(key)
            key = card_text[0] if card_text else None
        entry = entries.get(key) or alt_entries.get(key)
        if entry is None:
            return None
        entry = {**entry, "trade_info": prefix_trade_infos.get(entry["names"][0], "")}
        if prefix == "ca":
            entry["texts"] = form_card_texts(item["jp_text"], entry["names"][LANG])
            if not entry["texts"][LANG]:
                return None
            entry["trade_info"] = "Untradable" if extra_condition(prefix, item["jp_text"], "", entry["trade_info"]) else ""
        return entry

    def report():
        if missing_translation_count:
            print_status("CAUTION", f"{missing_translation_count} game items without translations (left unchanged)")

    return get_entry, report

# [FUNCTION] Get entries of weapons, camos and units by matching series names
def build_equipment_entries(prefix):
    # Weapons of other types are also untradable if the swords of the same series are untradable
    untradable_series_keys = get_untradable_series_keys(
        trade_infos["wp"], equipment_types["Item_Weapon_Sword.txt"],
        equipment_series_records, equipment_series_by_base) if prefix == "wp" else set()
    untranslated_texts = []

    def get_entry(path, item):
        jp_text = item["jp_text"]
        match_text = jp_text
        camo_suffix = ""
        if prefix == "wc":
            if not jp_text.startswith("＊"):
                return None
            match_text = jp_text[1:]
            if match := re.search(r"CV(?:\d+|-M\d+)?$", match_text):
                match_text, camo_suffix = match_text[:match.start()], match.group()
        structure, translated_name, jp_suffix = match_equipment_name(
            match_text, equipment_types[path], equipment_series_records, equipment_series_by_base)
        if translated_name is None:
            untranslated_texts.append(jp_text)
            return None
        if prefix == "wc":
            translated_name = "＊" + translated_name
            if camo_suffix:
                translated_name += equipment_suffix_separators[LANG] + camo_suffix
        # Get tradable info from global variable
        if extra_condition(prefix, jp_text, ""):
            trade_infos[prefix][jp_text] = "Untradable"
        trade_info = get_equipment_trade_info(
            jp_text, structure, jp_suffix, trade_infos[prefix], untradable_series_keys)
        return form_name_entry(jp_text, translated_name, trade_info)

    return get_entry, lambda: report_untranslated(untranslated_texts)

# [FUNCTION] Get entries of rings by matching skill names
def build_ring_entries(prefix):
    ui_item_jp_by_skill = {}
    for text_id, jp_text in ui_item_jp_lines:
        if text_id.startswith("ring_") and text_id.endswith("#1"):
            ui_item_jp_by_skill.setdefault(strip_ring_skill_name(jp_text), []).append(text_id)
    ui_item_translations = dict(ui_item_tr_lines)
    untranslated_texts = []

    def get_entry(path, item):
        type_name, separator, skill_name = item["jp_text"].partition("／")
        type_names = ring_type_translations.get(type_name)
        ui_item_keys = ui_item_jp_by_skill.get(skill_name, [])
        # Skip rings without a unique translation
        translated_skill = ""
        if separator and type_names is not None and type_names[LANG] is not None and len(ui_item_keys) == 1:
            translation_key = skill_name if LANG == 1 else ui_item_keys[0]
            translated_skill = strip_ring_skill_name(ui_item_translations.get(translation_key, ""))
        if not translated_skill:
            untranslated_texts.append(item["jp_text"])
            return None
        translated_name = f"{type_names[LANG]}{ring_slash_translations[LANG]}{translated_skill}"
        return form_name_entry(item["jp_text"], translated_name, trade_infos[prefix].get(skill_name, ""))

    return get_entry, lambda: report_untranslated(untranslated_texts)

# [FUNCTION] Get entries of equipment upgrade materials by matching full series names
def build_upgrade_material_entries(prefix):
    series_translations = defaultdict(set)
    for record in equipment_series_records:
        if "text_id" in record:
            series_translations[record["jp_base"]].add(record["translated_base"])
    untranslated_texts = []

    def get_entry(path, item):
        jp_text = item["jp_text"]
        # Missing wiki rows are unknown, not a default trade status or material scope.
        if jp_text not in trade_infos[prefix]:
            return None
        stem, _ = split_common_suffix(jp_text)
        type_names = next((names for jp_type, names in upgrade_material_types.items()
                           if stem.endswith(jp_type)), None)
        if type_names is None:
            return None
        jp_base = stem[:-len(type_names[0])]
        record = equipment_series_by_base.get(jp_base)
        # Comment-only aliases and conflicting source translations are not full series.
        if record is None or "text_id" not in record or len(series_translations[jp_base]) != 1:
            untranslated_texts.append(jp_text)
            return None
        type_separator = upgrade_material_type_separators[LANG].get(type_names[0])
        structure, translated_name, _ = match_equipment_name(
            jp_text, type_names, [record], equipment_series_by_base, type_separator)
        if translated_name is None or not structure["has_type"] or structure["pre"] or structure["post"]:
            untranslated_texts.append(jp_text)
            return None
        return form_name_entry(jp_text, translated_name, trade_infos[prefix][jp_text])

    return get_entry, lambda: report_untranslated(untranslated_texts)

# Entry builders of prefixes (build_game_entries if not defined)
entry_builders = {
    "wp": build_equipment_entries,
    "wc": build_equipment_entries,
    "un": build_equipment_entries,
    "rg": build_ring_entries,
    "um": build_upgrade_material_entries}


# [FUNCTION] Update existing json files of the prefix
def main_update(prefix):
    print(f"\n  [{prefix}]")
    get_entry, report = entry_builders.get(prefix, build_game_entries)(prefix)
    for path in json_paths[prefix]:
        try:
            with open(os.path.join(jsonfile_dir, path), "r", encoding='utf-8') as f:
                items = json.load(f)
        except FileNotFoundError:
            print_status("FAILED", f"File does not exist: {os.path.join(jsonfile_dir, path)} (skipped)")
            continue
        start = [item["assign"] for item in items].index(start_assigns[prefix]) if prefix in start_assigns else 0
        _count = 0
        changed_items = []
        for item in items[start:]:
            if len(str(item["assign"])) < min_assign_digits.get(prefix, 0):
                continue
            entry = get_entry(path, item)
            if entry is not None:
                previous = {key: item[key] for key in ("tr_text", "tr_explain")}
                form_itemdata(item, entry)
                _count += 1
                changes = [f"{key}: {json.dumps(old, ensure_ascii=False)} → {json.dumps(item[key], ensure_ascii=False)}"
                           for key, old in previous.items() if old != item[key]]
                if changes:
                    changed_items.append((item["assign"], item["jp_text"], changes))
        write_to_json(items, jsonfile_dir, path)
        print_status("UPDATED", f"{len(changed_items):>5} / {_count:>5} / {len(items):<5}  {path}")
        for assign, jp_text, changes in changed_items:
            print_status("CHANGED", f"[{assign}] {json.dumps(jp_text, ensure_ascii=False)} | {' | '.join(changes)}")
    report()

# Update json files from game files
process_prefixes = [
    "mo", "bp", "ph", "bg", "aug", "ou", "cp", "mou", "ear", "horn", "body", "ba", "in",
    "bpa", "stk", "eye", "brow", "lash", "fpa", "hair", "head", "face", "ac", "md", "ca", "ma", "sv", "wp", "wc", "un", "rg", "um"]
# Update "Stack_" json files of lobby actions and voices (only for CN)
if LANG == 1:
    process_prefixes += ["ha", "vo"]
print_stage(f"Updating json files ({lang_names[LANG]} mode; changed /  / total)")
for prefix in process_prefixes:
    main_update(prefix)

# ——————————————————————————————

print_stage("All completed")
