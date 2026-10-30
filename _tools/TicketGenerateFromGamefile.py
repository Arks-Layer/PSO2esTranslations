import os
import re
import json
import requests
import unicodedata
import urllib3
from collections import defaultdict

# ——————————————————————————————
# LANGUAGE SETTING
# ——————————————————————————————

# This tool updates existing json files ("Stack_", weapons, units and rings) from the main game files.

LANG = 1

# [ 0 for Non-translation mode ]
# Will update matched items and retain the existing translation.

# [ 1 for CN mode ]
# Will update "Stack_" items in Chinese.
# (Translations will be retrieved from the LOCAL "PSO2_CHN_Translation" repository)

# [ 2 for EN mode ]
# Will update "Stack_" items in English.
# (Translations will be retrieved from the "PSO2ENPatchCSV" repository)

lang_names = ("Non-translation", "CN", "EN")

# ——————————————————————————————
# PATH & URL SETTING
# ——————————————————————————————

# Path of root folder
root_dir = os.path.dirname(os.path.abspath(__file__))

# Path of main game file CN respository (Won't affect other modes)
PSO2CN_path = os.path.abspath(os.path.join(root_dir, os.pardir, os.pardir, r"PSO2_CHN_Translation"))
# URL of main game file JP/EN respository
PSO2EN_url = "https://raw.githubusercontent.com/Arks-Layer/PSO2ENPatchCSV/"

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
common_jp_url = f"{PSO2EN_url}{csv_reboot_url}common.csv"
accessories_jp_url = f"{PSO2EN_url}{csv_url}ui_accessories_text.csv"
charamake_parts_jp_url = f"{PSO2EN_url}{csv_url}ui_charamake_parts.csv"
element_name_jp_url = f"{PSO2EN_url}{csv_url}item_element_name_reb.csv"
lineduel_text_jp_url = f"{PSO2EN_url}{csv_reboot_url}lineduel_text.csv"
item_series_name_jp_url = f"{PSO2EN_url}{csv_url}item_series_name.csv"
ui_item_jp_url = f"{PSO2EN_url}{csv_reboot_url}ui_item.csv"
bgmlist_text_jp_url = f"{PSO2EN_url}{csv_reboot_url}ui_bgmlist_text.csv"
# URLs of EN main game files
csv_en_url = "EN/UI/"
csv_reboot_en_url = "EN_Reboot/Translated/UI/"
common_en_url = f"{PSO2EN_url}{csv_reboot_en_url}common.csv"
accessories_en_url = f"{PSO2EN_url}{csv_en_url}ui_accessories_text.csv"
charamake_parts_en_url = f"{PSO2EN_url}{csv_en_url}ui_charamake_parts.csv"
element_name_en_url = f"{PSO2EN_url}{csv_en_url}item_element_name_reb.csv"
lineduel_text_en_url = f"{PSO2EN_url}{csv_reboot_en_url}lineduel_text.csv"
item_series_name_en_url = f"{PSO2EN_url}{csv_en_url}item_series_name.csv"
ui_item_en_url = f"{PSO2EN_url}{csv_reboot_en_url}ui_item.csv"
bgmlist_text_en_url = f"{PSO2EN_url}{csv_reboot_en_url}ui_bgmlist_text.csv"

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
    # All music discs are tradable by default (uncomment to get untradable ones from swiki)
    # 'ngs_md': ('ミュージックディスク', ("md", ))
    }
# swiki pages with one item per table row, and the column of item names
# (weapons of other types are found by sword series)
row_wiki_pages = {'防具': 2, 'ソード': 2, 'ミュージックディスク': 1}
# Path of json folder
jsonfile_dir = os.path.abspath(os.path.join(root_dir, os.pardir, "json"))

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
    "md": ["Item_Stack_Music.txt"],
    "ca": ["Item_Stack_Duel_Card_Ticket.txt"],
    "ma": ["Item_Stack_Duel_Card_Play_Mat.txt"],
    "sv": ["Item_Stack_Duel_Card_Sleeve.txt"],
    "ha": ["Item_Stack_LobbyAction.txt"],
    "vo": ["Item_Stack_Voice.txt"],
    "un": ["Item_Addon_Unit.txt"],
    "rg": ["Item_NGSRing1.txt", "Item_NGSRing2.txt"]
}

# ——————————————————————————————
# FUNCTION
# ——————————————————————————————

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
    # Send the get request
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.get(url, verify=False)
    # If successed, load the data
    if response.status_code == 200:
        lines = response.text
        print_status("LOADED", url_part)
        return lines
    # If failed, print the status code
    else:
        print_status("FAILED", f"{url} (status code {response.status_code})")

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
    # Determine the type of file_path
    if file_path.startswith("http"):
        lines = get_web(file_path).splitlines()
    else:
        with open(file_path, encoding='utf-8') as f:
            lines = f.readlines()
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
            if line.startswith('<div class="ie5">') or line.startswith(' data-ad-slot='):
                # For items in table rows (one item per table row)
                name_column = next((column for page, column in row_wiki_pages.items() if file_path.endswith(page)), None)
                if name_column is not None:
                    for row in line.split("<tr>"):
                        if "マイショップ出品不可" not in row:
                            continue
                        cells = re.findall(r"<td[^>]*>(.*?)</td>", row)
                        if len(cells) <= name_column:
                            continue
                        # The cell of item names, which are separated by <br>
                        for name in cells[name_column].split('<br class="spacer" />'):
                            jp_text = re.sub(r"<[^>]+>", "", name).strip()
                            if jp_text:
                                trade_infos[jp_text] = "Untradable"
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
    with open(file_path, encoding='utf-8') as f:
        for line in f:
            if line.startswith(";") and "=" in line:
                key, value = line[1:].rstrip("\r\n").split("=", 1)
                translations[key] = value
    return translations

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

# [FUNCTION] Check if text contains Japanese or Chinese characters
def contains_japanese(text):
    return bool(re.search(r'[\u3040-\u30ff\u4e00-\u9fff]', text))

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

# [FUNCTION] Get translations of jp_target_lines from tr_lines (None if not found)
def get_translation(jp_target_lines, tr_lines):
    if LANG == 0:
        return [""] * len(jp_target_lines)

    # CN translations are found by JP text, others are found by text_id
    translations = {}
    for key, tr_text in tr_lines:
        translations.setdefault(key, tr_text)

    tr_target_texts = []
    for text_id, jp_text, *jp_refer in jp_target_lines:
        tr_text = translations.get(jp_text if LANG == 1 else text_id)
        if not tr_text:
            print_status("CAUTION", f"No translation for {jp_text}")
        tr_target_texts.append(tr_text)
    return tr_target_texts

# [FUNCTION] Form names of voice (only compatible with CN)
def form_vo_names(text_id, jp_fulltext, tr_fulltext):
    # Split the full text to get vo name and cv name
    # (voices without cv name are voiced by the characters themselves, e.g. "でびでび・でびる")
    vo_jp_name = jp_fulltext.split("/")[0]
    vo_tr_name, cv_tr_name = tr_fulltext.split("/") if "/" in tr_fulltext else (tr_fulltext, tr_fulltext)

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
    return re.sub(r"(?:シ?リーズ|系列|\s+Series)$", "", text).strip()

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
        if LANG == 2 and contains_japanese(translated_base):
            continue
        records.append({
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

# [FUNCTION] Split the common suffix (AT, roman numerals, etc.) from the end of equipment name
def split_common_suffix(jp_text):
    for jp_suffix in sorted(equipment_common_suffixes, key=len, reverse=True):
        if jp_text.endswith(jp_suffix) and len(jp_text) > len(jp_suffix):
            return jp_text[:-len(jp_suffix)], jp_suffix
    # Roman numerals from "Ⅰ" to "Ⅻ" (e.g. "レジェスソードⅡ")
    if len(jp_text) > 1 and "Ⅰ" <= jp_text[-1] <= "Ⅻ":
        return jp_text[:-1], jp_text[-1]
    return jp_text, ""

# [FUNCTION] Translate the common suffix
# Roman numerals: JP keeps "Ⅱ", CN uses Arabic numeral "2", EN uses letters "II"
def translate_common_suffix(jp_suffix):
    if jp_suffix in equipment_common_suffixes:
        return equipment_common_suffixes[jp_suffix][LANG]
    roman_numerals = (jp_suffix, str(int(unicodedata.numeric(jp_suffix))), unicodedata.normalize("NFKC", jp_suffix))
    return roman_numerals[LANG]

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

# [FUNCTION] Get the separator between parts of translated equipment name
# CN only adds "·" where JP has "・"; non-CN always uses space
def get_equipment_separator(has_dot):
    return equipment_dot_translations[LANG] if has_dot else equipment_space_translations[LANG]

# [FUNCTION] Render the translated name from structure, return None if any part has no translation
def render_equipment_structure(structure, translated_type, records_by_base):
    result = structure["record"]["translated_base"]
    for parent_base, small_name, has_dot in structure["pre"]:
        translated_small = get_small_series_translation(parent_base, small_name, records_by_base)
        if not translated_small:
            return None
        result += get_equipment_separator(has_dot) + translated_small
    if structure["has_type"]:
        result += get_equipment_separator(False) + translated_type
    for parent_base, small_name, has_dot in structure["post"]:
        translated_small = get_small_series_translation(parent_base, small_name, records_by_base)
        if not translated_small:
            return None
        result += get_equipment_separator(has_dot) + translated_small
    return result

# [FUNCTION] Match the equipment name, return (structure, translated name, common suffix)
# (None, None, common suffix) if there is no complete translation
def match_equipment_name(jp_text, type_names, series_records, records_by_base):
    jp_type = type_names[0]
    translated_type = type_names[LANG]
    stem, jp_suffix = split_common_suffix(jp_text)
    stem, in_parentheses = split_type_parentheses(stem, jp_type)

    for structure in iter_equipment_structures(stem, jp_type, series_records, records_by_base):
        # The stem has no type if the type is in parentheses
        if in_parentheses and structure["has_type"]:
            continue
        translated_name = render_equipment_structure(structure, translated_type, records_by_base)
        if translated_name is None:
            continue
        if in_parentheses:
            left, right = equipment_parentheses_translations[LANG]
            translated_name += f"{get_equipment_separator(False)}{left}{translated_type}{right}"
        if jp_suffix:
            translated_name += get_equipment_separator(False) + translate_common_suffix(jp_suffix)
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

# [FUNCTION] Form the card texts ([JP, CN, EN]) with translated name
def form_card_texts(stack_text, translated_name):
    parsed_text = parse_card_stack_text(stack_text)
    if parsed_text is None:
        return [stack_text, stack_text, stack_text]
    _, jp_prefix, element, cost_and_rarity = parsed_text
    translated_element = ca_itype_translations[element]
    cn_prefix = jp_prefix.replace(element, translated_element[1], 1)
    en_prefix = f"Ca \"{translated_element[2]} {cost_and_rarity}: "
    return [stack_text, f"{cn_prefix}{translated_name}」", f"{en_prefix}{translated_name}\""]

# [FUNCTION] Form the entry of item which only has a translated name (weapons, units and rings)
def form_name_entry(jp_text, translated_name, trade_info):
    names = [jp_text, translated_name, translated_name]
    return {"names": names, "texts": names, "explains": no_explains,
            "trade_info": trade_info, "untranslated": jp_text == translated_name}

# [FUNCTION] Update the translation of json item from the entry
# entry: names, texts and explains ([JP, CN, EN]), trade info, and if the item is untranslated
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

    # For non-translation mode
    if LANG == 0:
        item["tr_explain"] = rec_tr_explain
    # For tradable items in CN mode
    elif LANG == 1 and (names[0] != names[LANG]) and entry["trade_info"] != "Untradable":
        item["tr_text"] = texts[0]
        item["tr_explain"] = f"<green>“{texts[LANG]}”<c>\n{tr_explain}"
    # For untranslated items in EN mode
    elif LANG != 1 and entry["untranslated"] and contains_japanese(names[LANG]):
        item["tr_text"] = ""
        item["tr_explain"] = tr_explain
    # For untradable items or EN mode
    else:
        item["tr_text"] = texts[LANG]
        item["tr_explain"] = tr_explain

# [FUNCTION] Write to json file
def write_to_json(processed_items, jsonfile_dir, path):
    processed_lines = json.dumps(list(processed_items), ensure_ascii=False, indent="\t") + "\n"
    with open(os.path.join(jsonfile_dir, path), "w", encoding='utf-8') as f:
        f.write(processed_lines)

# ——————————————————————————————
# PRESET PROCESSES
# ——————————————————————————————

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

# Parse CN/EN files or webs, to read the lines need to be considered
if LANG == 0:
    common_tr_lines = []
    accessories_tr_lines = []
    charamake_parts_tr_lines = []
    element_name_tr_lines = []
    lineduel_text_tr_lines = []
    item_series_name_tr_lines, item_series_name_comment_tr = [], {}
    ui_item_tr_lines = []
    bgmlist_text_tr_lines = []
elif LANG == 1:
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
elif LANG == 2:
    print_stage(f"Loading {lang_names[LANG]} translations")
    common_tr_lines = parse_data(common_en_url, "csv")[0]
    accessories_tr_lines = parse_data(accessories_en_url, "csv")[0]
    charamake_parts_tr_lines = parse_data(charamake_parts_en_url, "csv")[0]
    element_name_tr_lines = parse_data(element_name_en_url, "csv")[0]
    lineduel_text_tr_lines = parse_data(lineduel_text_en_url, "csv")[0]
    item_series_name_tr_lines = parse_data(item_series_name_en_url, "csv")[0]
    item_series_name_comment_tr = {}
    ui_item_tr_lines = parse_data(ui_item_en_url, "csv")[0]
    bgmlist_text_tr_lines = parse_data(bgmlist_text_en_url, "csv")[0]

# Parse swiki/makapo webs to get tradable info (only for CN)
if LANG == 1:
    print_stage("Loading tradable info from swiki/makapo")
    for key in trade_mapping:
        parse_info(key, trade_mapping)

# Find series records of weapons and units
equipment_series_records, equipment_series_by_base = build_equipment_series_records()

# ——————————————————————————————
# MAPPINGS AND CONDITIONS
# ——————————————————————————————

# Categories of items
mo_itypes = {
    "Idle": ("待機", "待機", "Idle"),
    "Jump": ("ジャンプ", "跳躍", "Jump"),
    "Landing": ("着地", "落地", "Land"),
    "Move": ("移動", "移動", "Move"),
    "Sprint": ("ダッシュ", "衝刺", "Dash"),
    "Glide": ("グライド", "滑翔", "Glide"),
    "Swim": ("泳ぐ", "游泳", "Swim")}
# Types of weapons and units (keyed by json file)
equipment_types = {
    "Item_Weapon_AssaultRifle.txt": ("ライフル", "步槍", "Rifle"),
    "Item_Weapon_Compoundbow.txt": ("ボウ", "強弓", "Bow"),
    "Item_Weapon_DoubleSaber.txt": ("セイバー", "雙頭劍", "Saber"),
    "Item_Weapon_DualBlade.txt": ("ブレード", "飛翔劍", "Blades"),
    "Item_Weapon_GunSlash.txt": ("スラッシュ", "槍刃", "Slash"),
    "Item_Weapon_JetBoots.txt": ("ブーツ", "魔裝腳", "Boots"),
    "Item_Weapon_Katana.txt": ("カタナ", "拔劍", "Katana"),
    "Item_Weapon_Knuckle.txt": ("ナックル", "鋼拳", "Knuckles"),
    "Item_Weapon_Launcher.txt": ("ランチャー", "大炮", "Launcher"),
    "Item_Weapon_Partizan.txt": ("スピア", "長槍", "Spear"),
    "Item_Weapon_Rod.txt": ("ロッド", "長杖", "Rod"),
    "Item_Weapon_Sword.txt": ("ソード", "大劍", "Sword"),
    "Item_Weapon_Tact.txt": ("タクト", "奏具", "Takt"),
    "Item_Weapon_Talis.txt": ("タリス", "導具", "Talis"),
    "Item_Weapon_TwinDagger.txt": ("ダガー", "雙小劍", "Daggers"),
    "Item_Weapon_TwinMachineGun.txt": ("マシンガン", "雙機槍", "Machineguns"),
    "Item_Weapon_Wand.txt": ("ウォンド", "短杖", "Wand"),
    "Item_Weapon_WiredLance.txt": ("ワイヤー", "自在槍", "Wire"),
    "Item_Addon_Unit.txt": ("アーマ", "防具", "Armor")}
json_paths["wp"] = [path for path in equipment_types if path.startswith("Item_Weapon_")]
# Common suffixes of equipment names except roman numerals (e.g. "トワル・シュメッターソードAT")
equipment_common_suffixes = {
    "AT": ("AT", "AT", "AT")}
# Separators of equipment names (with "・" in JP / without "・" in JP) and parentheses of type
equipment_dot_translations = ("・", "·", " ")
equipment_space_translations = ("", "", " ")
equipment_parentheses_translations = (("（", "）"), ("（", "）"), ("(", ")"))
# Types and separators of rings
ring_type_translations = {
    "タイプ1": ("タイプ1", "類型1", "Type 1"),
    "タイプ2": ("タイプ2", "類型2", "Type 2")}
ring_slash_translations = ("／", "/", "/")
igens = {
    "a1": ["ヒト型/キャストタイプ1", "人類/機人類型1", "Human/Cast Type 1"],
    "a2": ["ヒト型/キャストタイプ2", "人類/機人類型2", "Human/Cast Type 2"],
    "h1": ["ヒト型タイプ1", "人類類型1", "Human Type 1"],
    "h2": ["ヒト型タイプ2", "人類類型2", "Human Type 2"],
    "c1": ["キャストタイプ1", "機人類型1", "Cast Type 1"],
    "c2": ["キャストタイプ2", "機人類型2", "Cast Type 2"]}
# Card element translations; costs and rarity markers are retained from Stack text.
ca_itype_translations = {
    "炎": ("炎", "炎", "Fire"),
    "氷": ("氷", "冰", "Ice"),
    "風": ("風", "風", "Wind"),
    "雷": ("雷", "雷", "Lightning"),
    "光": ("光", "光", "Light"),
    "闇": ("闇", "暗", "Dark")}
# Names and texts of items (plain_formats if not defined; texts of cards are formed by form_card_texts)
plain_formats = ["{jp_text}", "{tr_text}", "{tr_text}"]
mo_names = ["{jp_itype}：{jp_text}", "{tr_itype}：{tr_text}", "{tr_itype}: {tr_text}"]

mo_texts = [
    "Mo「{jp_itype}：{jp_text}」", "Mo「{tr_itype}：{tr_text}」", "Mo \"{tr_itype}: {tr_text}\""]
bp_texts = [
    "BP「{jp_text}」",  "BP「{tr_text}」", "BP \"{tr_text}\""]
ph_texts = [
    "PH「{jp_text}」",  "PH「{tr_text}」", "PH \"{tr_text}\""]
bg_texts = [
    "Bg「{jp_text}」",  "Bg「{tr_text}」", "Bg \"{tr_text}\""]
aug_texts = [
    "C/{jp_text}", "C/{tr_text}", "C/{tr_text}"]
ma_texts = [
    "Ma「{jp_text}」", "Ma「{tr_text}」", "Ma \"{tr_text}\""]
sv_texts = [
    "Sv「{jp_text}」", "Sv「{tr_text}」", "Sv \"{tr_text}\""]
ha_texts = [
    "Ha「{jp_text}」",  "Ha「{tr_text}」", "Ha \"{tr_text}\""]

# Explains of items, only for information from game files
# (other explains are translated by TicketDescriptions.py, existing ones are retained)
no_explains = ["", "", ""]
body_explains = [
    "使用すると新しい肌パターンが\n選択可能になる。\n<yellow>※対応：{jp_igen}<c>",
    "使用後可選用新的皮膚種類。\n<yellow>※適用於：{tr_igen}<c>",
    "Unlocks a new body type for use.\n<yellow>※Type: {tr_igen}<c>"]
vo_explains = [
    "",
    "使用後，可選用新的語音。\nCV：{cv_tr_name}", 
    "Allows a new voice to be selected.\nUsable by all characters.\nCV: {cv_tr_name}"]

# [FUNCTION] Special item texts of special items
def edit_sp_texts(prefix, jp_text, tr_text, jp_refer):
    jp_refer = jp_refer[0] if jp_refer else ""
    
    if prefix == "ca" and jp_text == "アルクェイド・ブリュンスタッド":
        sp_texts = ["アルクェイド", "愛爾奎特", "Arcueid"]
        jp_text = sp_texts[0]
        tr_text = sp_texts[LANG]
    elif prefix == "ca" and jp_refer == "サマーバケーション"and "せんとらるっ！" not in jp_text:
        sp_texts = ["（サマー）", "（夏季）", " (Summer)"]
        jp_text += sp_texts[0]
        tr_text += sp_texts[LANG]
    elif prefix == "ca" and jp_refer == "ハッピーホリデイ":
        sp_texts = ["（ホリデイ）", "（假日）", " (Holiday)"]
        jp_text += sp_texts[0]
        tr_text += sp_texts[LANG]
    elif prefix == "ca" and jp_refer == "超・夢幻祭":
        sp_texts = ["（夢幻祭）", "（夢幻祭）", " (Super Phantasy Festival)"]
        jp_text += sp_texts[0]
        tr_text += sp_texts[LANG]
    elif prefix == "ca" and jp_text == "先代ダークファルス【若人】":
        sp_texts = ["先代DF【若人】", "前代DF【若人】", "Previous DF [Apprentice]"]
        jp_text = sp_texts[0]
        tr_text = sp_texts[LANG]
    elif prefix == "ca" and jp_refer == "スクルル":
        sp_texts = ["（スクルル）", "（學園風尚）", " (Schoolu)"]
        jp_text += sp_texts[0]
        tr_text += sp_texts[LANG]
    elif prefix == "ca" and "せんとらるっ！　" in jp_text:
        sp_char = "！"
        jp_text = jp_text.replace(sp_char + "　", sp_char)
    # Voices voiced by the characters themselves, whose cv names are written differently
    elif prefix == "vo" and jp_text == "五十嵐梨花":
        sp_texts = ["/五十嵐 梨花", "/五十嵐 梨花", "/Rika Igarashi"]
        jp_text += sp_texts[0]
        tr_text += sp_texts[LANG]
    elif prefix == "vo" and jp_text == "倉持めると":
        sp_texts = ["/倉持 めると", "/倉持 妹路特", "/Meruto Kuramochi"]
        jp_text += sp_texts[0]
        tr_text += sp_texts[LANG]

    return jp_text, tr_text

# Find target JP lines
mo_jp_target_lines = [
    (text_id, jp_text) for text_id, jp_text in common_jp_lines
    if text_id.startswith("Substitute_") and not jp_text.startswith("￥")]
bp_jp_target_lines = [
    (text_id, jp_text) for text_id, jp_text in accessories_jp_lines
    if text_id.startswith(("ob_1", "ob_6")) and not jp_text.startswith(("￥", "text_"))]
ph_jp_target_lines = [
    (text_id, jp_text) for text_id, jp_text in accessories_jp_lines
    if text_id.startswith("ob_7") and not jp_text.startswith(("￥", "text_"))]
bg_jp_target_lines = remove_dummy_lines(
    get_table_jp_target_lines(charamake_parts_jp_lines, "10#0", r'^\d{1,3}#'))
aug_jp_target_lines = [
    (text_id, jp_text) for text_id, jp_text in element_name_jp_lines
    if not jp_text.startswith(("ダミー", "レガロ・", "セズン・", "EX", "ウェポンコネクタ", "￥", "-"))
    or re.search(r"(EX.*A$)", jp_text)]
ou_jp_target_lines = [
    (text_id, jp_text) for text_id, jp_text in charamake_parts_jp_lines
    if re.match(r'^No\d{6}#', text_id)
    and jp_text.endswith("[Ou]")
    and not jp_text.startswith(("￥", "text_")) and "NPC" not in jp_text]
cp_jp_target_lines = [
    (text_id, jp_text) for text_id, jp_text in charamake_parts_jp_lines
    if re.match(r'^No[34]\d{5}#', text_id)
    and any(keyword in jp_text for keyword in ("・アーム", "・ボディ", "・レッグ"))
    and not jp_text.startswith(("￥", "text_")) and "NPC" not in jp_text]
mou_jp_target_lines = get_table_jp_target_lines(charamake_parts_jp_lines, "No100010#10", r'^No1\d{5}#')
ear_jp_target_lines = get_table_jp_target_lines(charamake_parts_jp_lines, "No100000#4", r'^No1\d{5}#')
horn_jp_target_lines = get_table_jp_target_lines(charamake_parts_jp_lines, "No100000#5", r'^No1\d{5}#')
body_jp_target_lines = [
    (text_id, jp_text) for text_id, jp_text in
    get_table_jp_target_lines(charamake_parts_jp_lines, "No100000#6", r'^No\d{6}#')
    if not jp_text.startswith(("￥", "text_")) and "NPC" not in jp_text]
ba_jp_target_lines = remove_dummy_lines(get_table_jp_target_lines(charamake_parts_jp_lines, "No100010#0"))
in_jp_target_lines = remove_dummy_lines(get_table_jp_target_lines(charamake_parts_jp_lines, "No100010#8"))
bpa_jp_target_lines = remove_dummy_lines(get_table_jp_target_lines(charamake_parts_jp_lines, "1250#0"))
stk_jp_target_lines = remove_dummy_lines(get_table_jp_target_lines(charamake_parts_jp_lines, "No00000#2"))
eye_jp_target_lines = remove_dummy_lines(get_table_jp_target_lines(charamake_parts_jp_lines, "243#0"))
brow_jp_target_lines = remove_dummy_lines(get_table_jp_target_lines(charamake_parts_jp_lines, "10780#0"))
lash_jp_target_lines = remove_dummy_lines(get_table_jp_target_lines(charamake_parts_jp_lines, "10750#0"))
fpa_jp_target_lines = remove_dummy_lines(get_table_jp_target_lines(charamake_parts_jp_lines, "No00000#5"))
# Hairstyles and head parts share a table; cast head parts are also in the table of cast parts
hair_jp_target_lines = remove_dummy_lines(
    get_table_jp_target_lines(charamake_parts_jp_lines, "50670#0", r'^No([01]\d{4}|1\d{5})#'))
head_jp_target_lines = remove_dummy_lines(
    get_table_jp_target_lines(charamake_parts_jp_lines, "50670#0", r'^No(5\d{4}|3\d{5})#')
    + get_table_jp_target_lines(charamake_parts_jp_lines, "-#0", r'^cast_'))
# Face variations are in the table of face variations and the table of voices
face_jp_target_lines = remove_dummy_lines(
    get_table_jp_target_lines(charamake_parts_jp_lines, "No100000#2", r'^No[12]\d{5}#')
    + get_table_jp_target_lines(charamake_parts_jp_lines, "11_voice_201000#0", r'^No\d{6}#'))
ac_jp_target_lines = remove_dummy_lines(get_table_jp_target_lines(accessories_jp_lines, "No00000#0"))
md_jp_target_lines = remove_dummy_lines(bgmlist_text_jp_lines)
ca_jp_target_lines = get_table_jp_target_lines(lineduel_text_jp_lines, ("10#0", "10#1"), order_key=numeric_order)
ma_jp_target_lines = get_table_jp_target_lines(lineduel_text_jp_lines, "0#2", order_key=numeric_order)
sv_jp_target_lines = get_table_jp_target_lines(lineduel_text_jp_lines, "0#3", order_key=numeric_order)
ha_jp_target_lines = [
    (text_id, jp_text) for text_id, jp_text in common_jp_lines
    if text_id.startswith("LobbyAction_")]
vo_jp_target_lines = [
    (text_id, jp_text) for text_id, jp_text in charamake_parts_jp_lines
    if re.match(r'11_voice_(c|[34]\d{5}#)', text_id)]

# JP target lines and translated lines of game items
game_target_lines = {
    "mo": (mo_jp_target_lines, common_tr_lines),
    "bp": (bp_jp_target_lines, accessories_tr_lines),
    "ph": (ph_jp_target_lines, accessories_tr_lines),
    "bg": (bg_jp_target_lines, charamake_parts_tr_lines),
    "aug": (aug_jp_target_lines, element_name_tr_lines),
    "ou": (ou_jp_target_lines, charamake_parts_tr_lines),
    "cp": (cp_jp_target_lines, charamake_parts_tr_lines),
    "mou": (mou_jp_target_lines, charamake_parts_tr_lines),
    "ear": (ear_jp_target_lines, charamake_parts_tr_lines),
    "horn": (horn_jp_target_lines, charamake_parts_tr_lines),
    "body": (body_jp_target_lines, charamake_parts_tr_lines),
    "ba": (ba_jp_target_lines, charamake_parts_tr_lines),
    "in": (in_jp_target_lines, charamake_parts_tr_lines),
    "bpa": (bpa_jp_target_lines, charamake_parts_tr_lines),
    "stk": (stk_jp_target_lines, charamake_parts_tr_lines),
    "eye": (eye_jp_target_lines, charamake_parts_tr_lines),
    "brow": (brow_jp_target_lines, charamake_parts_tr_lines),
    "lash": (lash_jp_target_lines, charamake_parts_tr_lines),
    "fpa": (fpa_jp_target_lines, charamake_parts_tr_lines),
    "hair": (hair_jp_target_lines, charamake_parts_tr_lines),
    "head": (head_jp_target_lines, charamake_parts_tr_lines),
    "face": (face_jp_target_lines, charamake_parts_tr_lines),
    "ac": (ac_jp_target_lines, accessories_tr_lines),
    "md": (md_jp_target_lines, bgmlist_text_tr_lines),
    "ca": (ca_jp_target_lines, lineduel_text_tr_lines),
    "ma": (ma_jp_target_lines, lineduel_text_tr_lines),
    "sv": (sv_jp_target_lines, lineduel_text_tr_lines),
    "ha": (ha_jp_target_lines, common_tr_lines),
    "vo": (vo_jp_target_lines, charamake_parts_tr_lines)}

# Only update items with assign of these digits or more (NGS equipment)
min_assign_digits = {
    "wp": 8,
    "un": 8}
# Only update items from the item of this assign (NGS music discs)
start_assigns = {
    "md": "319010000"}

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
# and report() to print the unmatched info
def build_game_entries(prefix):
    jp_target_lines, tr_lines = game_target_lines[prefix]
    tr_target_texts = get_translation(jp_target_lines, tr_lines)
    prefix_trade_infos = trade_infos[prefix]
    # Cards are found by name, others are found by text
    entries = {}
    # Entries added by each game line (a voice line has entries of all possible names)
    line_entries = []
    missing_translation_count = 0

    for (text_id, jp_text, *jp_refer), tr_text in zip(jp_target_lines, tr_target_texts):
        missing_translation = tr_text is None
        # Edit special texts of special item
        jp_text, tr_text = edit_sp_texts(prefix, jp_text, tr_text or "", jp_refer)
        fields = {"jp_itype": "", "tr_itype": "", "jp_igen": "", "tr_igen": "", "cv_tr_name": ""}
        # Get category and the category name for certain prefixes
        if prefix == "mo":
            itype = mo_itypes[text_id.split("_")[1]]
            fields.update(jp_itype = itype[0], tr_itype = itype[LANG])
        # Get gender and the gender name for certain prefixes
        elif prefix == "body":
            igen = igens["a1" if text_id.startswith("No1") else "a2"]
            fields.update(jp_igen = igen[0], tr_igen = igen[LANG])
        # Get all names of voice
        name_pairs = [(jp_text, tr_text)]
        if prefix == "vo":
            jp_texts, tr_texts, fields["cv_tr_name"] = form_vo_names(text_id, jp_text, tr_text)
            name_pairs = zip(jp_texts, tr_texts)

        added_entries = []
        for jp_name, tr_name in name_pairs:
            # Get names, texts and explains from global variables
            fields.update(jp_text = jp_name, tr_text = tr_name)
            names = [name.format(**fields) for name in globals().get(f"{prefix}_names", plain_formats)]
            texts = [text.format(**fields) for text in globals().get(f"{prefix}_texts", plain_formats)]
            explains = [explain.format(**fields) for explain in globals().get(f"{prefix}_explains", no_explains)]
            # Get tradable info of all lines (e.g. a card is untradable if any of its lines is untradable)
            if extra_condition(prefix, jp_name, text_id):
                prefix_trade_infos[names[0]] = "Untradable"
            key = names[0] if prefix == "ca" else texts[0]
            if missing_translation or key in entries:
                continue
            entries[key] = {"names": names, "texts": texts, "explains": explains,
                            "untranslated": names[0] == names[LANG] or jp_name == tr_name}
            added_entries.append(entries[key])
        if added_entries:
            line_entries.append(added_entries)
        missing_translation_count += missing_translation

    # Also find items with names in a different width
    alt_entries = {}
    for key, entry in entries.items():
        alt_entries.setdefault(key.replace(entry["names"][0], width_process_string(entry["names"][0]), 1), entry)
    matched_entry_ids = set()

    def get_entry(path, item):
        key = item["jp_text"]
        if prefix == "ca":
            card_text = parse_card_stack_text(key)
            key = card_text[0] if card_text else None
        entry = entries.get(key) or alt_entries.get(key)
        if entry is None:
            return None
        matched_entry_ids.add(id(entry))
        entry = {**entry, "trade_info": prefix_trade_infos.get(entry["names"][0], "")}
        if prefix == "ca":
            entry["texts"] = form_card_texts(item["jp_text"], entry["names"][LANG])
            entry["trade_info"] = "Untradable" if extra_condition(prefix, item["jp_text"], "", entry["trade_info"]) else ""
        return entry

    def report():
        unmatched_count = sum(all(id(entry) not in matched_entry_ids for entry in added_entries)
                              for added_entries in line_entries)
        if unmatched_count:
            print_status("CAUTION", f"{unmatched_count} game items not found in json files (not added)")
        if missing_translation_count:
            print_status("CAUTION", f"{missing_translation_count} game items without translations (left unchanged)")

    return get_entry, report

# [FUNCTION] Get entries of weapons and units by matching series names
def build_equipment_entries(prefix):
    # Weapons of other types are also untradable if the swords of the same series are untradable
    untradable_series_keys = get_untradable_series_keys(
        trade_infos["wp"], equipment_types["Item_Weapon_Sword.txt"],
        equipment_series_records, equipment_series_by_base) if prefix == "wp" else set()
    untranslated_texts = []

    def get_entry(path, item):
        jp_text = item["jp_text"]
        structure, translated_name, jp_suffix = match_equipment_name(
            jp_text, equipment_types[path], equipment_series_records, equipment_series_by_base)
        if translated_name is None:
            untranslated_texts.append(jp_text)
            return None
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
        if separator and type_names is not None and len(ui_item_keys) == 1:
            translation_key = skill_name if LANG == 1 else ui_item_keys[0]
            translated_skill = strip_ring_skill_name(ui_item_translations.get(translation_key, ""))
        if not translated_skill:
            untranslated_texts.append(item["jp_text"])
            return None
        translated_name = f"{type_names[LANG]}{ring_slash_translations[LANG]}{translated_skill}"
        return form_name_entry(item["jp_text"], translated_name, trade_infos[prefix].get(skill_name, ""))

    return get_entry, lambda: report_untranslated(untranslated_texts)

# Entry builders of prefixes (build_game_entries if not defined)
entry_builders = {
    "wp": build_equipment_entries,
    "un": build_equipment_entries,
    "rg": build_ring_entries}


# [FUNCTION] Update existing json files of the prefix
def main_update(prefix):
    print(f"\n  [{prefix}]")
    get_entry, report = entry_builders.get(prefix, build_game_entries)(prefix)
    for path in json_paths[prefix]:
        with open(os.path.join(jsonfile_dir, path), "r", encoding='utf-8') as f:
            items = json.load(f)
        start = [item["assign"] for item in items].index(start_assigns[prefix]) if prefix in start_assigns else 0
        updated_count = 0
        for item in items[start:]:
            if len(str(item["assign"])) < min_assign_digits.get(prefix, 0):
                continue
            entry = get_entry(path, item)
            if entry is not None:
                form_itemdata(item, entry)
                updated_count += 1
        write_to_json(items, jsonfile_dir, path)
        print_status("UPDATED", f"{updated_count:>5} / {len(items):<5}  {path}")
    report()

# Update json files from game files
process_prefixes = [
    "mo", "bp", "ph", "bg", "aug", "ou", "cp", "mou", "ear", "horn", "body", "ba", "in",
    "bpa", "stk", "eye", "brow", "lash", "fpa", "hair", "head", "face", "ac", "md", "ca", "ma", "sv", "wp", "un", "rg"]
# Update "Stack_" json files of lobby actions and voices (only for CN)
if LANG == 1:
    process_prefixes += ["ha", "vo"]
print_stage(f"Updating json files ({lang_names[LANG]} mode)")
for prefix in process_prefixes:
    main_update(prefix)

# ——————————————————————————————

print_stage("All completed")
