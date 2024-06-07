import os
import re
import json
import requests
import unicodedata

# ——————————————————————————————
# LANGUAGE SETTING
# ——————————————————————————————

# This tool is used to generate "NGS_" json files
# or to edit "Stack_" json files from the main game files.

LANG = 1

# [ 0 for Non-translation mode ]
# Will only generate items, and retain the existing translation.

# [ 1 for CN mode ]
# Will generate "NGS_" items and edit "Stack_" items in Chinese.
# (Local repository required)

# [ 2 for EN mode ]
# Will generate "NGS_" items in English.

# ——————————————————————————————
# PATH & URL SETTING
# ——————————————————————————————

# Path of root folder
root_dir = os.path.dirname(os.path.abspath(__file__))

# Path of main game file CN respository (Won't affect other modes)
PSO2CN_path = os.path.abspath(os.path.join(root_dir, os.pardir, os.pardir, os.pardir, r"gitee\PSO2_CHN_Translation\UI"))
# URL of main game file JP/EN respository
PSO2EN_url = "https://raw.githubusercontent.com/Arks-Layer/PSO2ENPatchCSV/"

# Paths of CN main game files
common_cn_path = os.path.join(PSO2CN_path, "common.text.ini")
accessories_cn_path = os.path.join(PSO2CN_path, "ui_accessories_text.text.ini")
charamake_parts_cn_path = os.path.join(PSO2CN_path, "ui_charamake_parts.text.ini")
element_name_cn_path = os.path.join(PSO2CN_path, "item_element_name_reb.text.ini")
# URLs of JP main game files
csv_url = f"JP/Files/"
csv_reboot_url = f"JP_Reboot/Files/"
common_jp_url = f"{PSO2EN_url}{csv_reboot_url}common.csv"
accessories_jp_url = f"{PSO2EN_url}{csv_url}ui_accessories_text.csv"
charamake_parts_jp_url = f"{PSO2EN_url}{csv_url}ui_charamake_parts.csv"
element_name_jp_url = f"{PSO2EN_url}{csv_url}item_element_name_reb.csv"
# URLs of EN main game files
csv_en_url = f"EN/UI/"
csv_reboot_en_url = f"EN_Reboot/Translated/UI/"
common_en_url = f"{PSO2EN_url}{csv_reboot_en_url}common.csv"
accessories_en_url = f"{PSO2EN_url}{csv_en_url}ui_accessories_text.csv"
charamake_parts_en_url = f"{PSO2EN_url}{csv_en_url}ui_charamake_parts.csv"
element_name_en_url = f"{PSO2EN_url}{csv_en_url}item_element_name_reb.csv"

# Initialize tradable info
mo_trade_infos = {}
bp_trade_infos = {}
ph_trade_infos = {}
bg_trade_infos = {}
aug_trade_infos = {}
ou_m_trade_infos = {}
ou_f_trade_infos = {}
cp_m_trade_infos = {}
cp_f_trade_infos = {}
mou_trade_infos = {}
ear_trade_infos = {}
horn_trade_infos = {}
body_trade_infos = {}
ha_trade_infos = {}
vo_trade_infos = {}

# URLs of swiki/makapo (only for CN)
wiki_urls = {
    'ngs': 'https://pso2ngs.swiki.jp/index.php?',
    'o2': 'https://pso2.swiki.jp/index.php?',
    'makapo': 'https://ngs.pso2-makapo.com/'}
# URLs and trade_infos mapping of swiki/makapo pages (only for CN)
suffix_mapping = {
    'ngs_mo': ('モーション', mo_trade_infos),
    'makapo_bp': ('build-parts-list', bp_trade_infos),
    'ngs_bp1': ('クリエイティブスペース/ビルドパーツ/建材', bp_trade_infos),
    'ngs_bp2': ('クリエイティブスペース/ビルドパーツ/建築物・道具・器具', bp_trade_infos),
    'ngs_bp3': ('クリエイティブスペース/ビルドパーツ/自然物', bp_trade_infos),
    'ngs_bp4': ('クリエイティブスペース/ビルドパーツ/家具', bp_trade_infos),
    'ngs_bp5': ('クリエイティブスペース/ビルドパーツ/ギミックパーツ', bp_trade_infos),
    'ngs_bp6': ('クリエイティブスペース/ビルドパーツ/立体図形', bp_trade_infos),
    'ngs_bp7': ('クリエイティブスペース/ビルドパーツ/コラボ', bp_trade_infos),
    'ngs_ph': ('ポータブルホログラム', ph_trade_infos),
    'ngs_bg': ('アークスカード', bg_trade_infos),
    'ngs_vo': ('エステ/ボイス', vo_trade_infos),
    'o2_vo': ('エステ/ボイス', vo_trade_infos)}

# Path of json folder
jsonfile_dir = os.path.abspath(os.path.join(root_dir, os.pardir, "json"))

# Paths of .txt files
mo_path = "Item_NGS_Motion.txt"
bp_path = "Item_NGS_BuildParts.txt"
ph_path = "Item_NGS_Portableholograms.txt"
bg_path = "Item_NGS_Backgrounds.txt"
aug_path = "Item_NGS_CapsuleAbilities.txt"
ou_m_path = "Item_NGS_Outer_Male.txt"
ou_f_path = "Item_NGS_Outer_Female.txt"
cp_m_path = "Item_NGS_Parts_Male.txt"
cp_f_path = "Item_NGS_Parts_Female.txt"
mou_path = "Item_NGS_Mouth.txt"
ear_path = "Item_NGS_Ear.txt"
horn_path = "Item_NGS_Horn.txt"
body_path = "Item_NGS_Body.txt"
ha_path = "Item_Stack_LobbyAction.txt"
vo_path = "Item_Stack_Voice.txt"

# ——————————————————————————————
# FUNCTION
# ——————————————————————————————

# [FUNCTION] Load and read the webpage from URL
def get_web(url):
    url_part = url.rsplit('/', 1)[-1].split('?', 1)[-1]
    # Send the get request
    response = requests.get(url)
    # If successed, load the data
    if response.status_code == 200:
        lines = response.text
        print(f'LOADED: {url_part}')
        return lines
    # If failed, print the status code
    else:
        print(f'FAILED TO LOAD: {url}.\nStatus Code: {response.status_code}')

# [FUNCTION] Parse the web or file
def parse_data(file_path, file_type):
    # Determine the type of file_path
    if file_path.startswith("http"):
        lines = get_web(file_path).splitlines()
    else:
        with open(file_path, encoding='utf-8') as f:
            lines = f.readlines()

    parsed_lines = []
    trade_infos = {}

    for i, line in enumerate(lines):
        # Process .text.ini files
        if file_type == "ini":
            # Get ori_text and tr_text besides the "="
            if "=" in line:
                ori_text, tr_text = line.strip().split("=", 1)
                trade_infos[ori_text] = ""
                parsed_lines.append((ori_text, tr_text))
            # Get the trade_infos from comments (mainly for augments)
            if line.startswith(";"):
                if line.startswith(";不可交易") and i > 0:
                    ori_text = lines[i - 1].strip().split("=", 1)[0]
                    trade_infos[ori_text] = "Untradable"

        # Process .csv files
        elif file_type == "csv":
            if '"""' not in line:
                continue
            text_id, jp_text = line.strip().split('"""', 1)
            # Remove """ at the end of line
            jp_text = jp_text[:-3]
            # Replace some characters
            jp_text = jp_text.replace('\\u3000', '　').replace('\\""', '"')
            parsed_lines.append((text_id.strip(), jp_text))

        # Process .html files
        elif file_type == "html":
            if line.startswith('<div class="ie5">') or line.startswith(' data-ad-slot='):
                # For items with "「」"
                if "ngs" in file_path and not "エステ" in file_path:
                    headnames = ['Mo', 'BP', 'PH', 'Bg']
                    for headname in headnames:
                        # Do regex replacement, to ensure each line starts with item names.
                        n_lines = re.sub(f"{headname}「", f"\n{headname}「", line).splitlines()
                        for n_line in n_lines:
                            if n_line.startswith(f"{headname}「"):
                                jp_text = n_line[n_line.find(f"{headname}「") + 3:n_line.find('」')]
                                if any(keyword in n_line for keyword in
                                    ['マイショップ出品不可', '初期', 'alt="GP"', 'alt="SG"', "交換</td>", "季節イベント</td>","トレジャースクラッチ", "SPスクラッチ</td>", "開発準備特別票</td>", "クラス育成特別プログラム", "初期登録</td>"]):
                                    trade_infos[jp_text] = "Untradable"

                # For items without "「」"
                else: 
                    headnames = ['男性', '女性', 'T1', 'T2']
                    for headname in headnames:
                        # Do regex replacement, to ensure each line starts with item names.
                        n_lines = re.sub(f"{headname}", f"\n{headname}", line).splitlines()
                        for n_line in n_lines:
                            if n_line.startswith(f"{headname}"):
                                jp_text = n_line[n_line.find(f"{headname}") :n_line.find('</td>')]
                                if any(keyword in n_line for keyword in
                                    ['マイショップ出品不可', 'SG.png']):
                                    trade_infos[jp_text] = "Untradable"

    return parsed_lines, trade_infos

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

# [FUNCTION] Get JP target lines from ordered lines
def get_order_jp_target_lines(prefix):
    # Initialize
    order_jp_lines = []
    # Get the lines of ordered lines
    matching_started = False
    for text_id, jp_text in charamake_parts_jp_lines:
        if prefix == "mou_to_body" and (matching_started or "MoveMotion_2" in text_id):
            matching_started = True
            match_result = re.match(r'^No(1|2)(\d{5})#', text_id)
            if match_result:
                order_jp_lines.append((text_id, jp_text))
        elif prefix == "bg" and (matching_started or jp_text == "ベースボディT2"):
            matching_started = True
            match_result = re.match(r'^^\d{1,3}#', text_id)
            if match_result:
                order_jp_lines.append((text_id, jp_text))

    # Initialize
    start_row = 0

    if prefix == "mou_to_body":
        order_jp_target_lines = [[], [], [], []]
        # Find target lines from each loop, from ordered lines
        for i in range(len(order_jp_target_lines)):
            current_row = start_row
            # Get text_ids of current line and next line
            while current_row < len(order_jp_lines) - 1:
                current_id, next_id = order_jp_lines[current_row][0], order_jp_lines[current_row + 1][0]
                # If both current line and next line matched
                if re.match(r'^No(\d{6})#', current_id) and re.match(r'^No(\d{6})#', next_id):
                    # Get the numbers after "No" from text_id, and extend the target lines
                    current_num, next_num = [int(re.search(r'^No(\d+)#', num).group(1)) for num in [current_id, next_id]]
                    order_jp_target_lines[i].append(order_jp_lines[current_row])
                    # Compare, if current number < next number, then continue
                    if current_num < next_num:
                        current_row += 1
                    # Compare, if current number >= next number, then break
                    else:     
                        start_row, current_row = current_row + 1, current_row + 1
                        break
                else:
                    break
            # Append the last line if current_row reaches the end
            if current_row == len(order_jp_lines) - 1:
                order_jp_target_lines[i].append(order_jp_lines[current_row])
                    
    elif prefix == "bg":
        order_jp_target_lines = order_jp_lines

    return order_jp_target_lines

# [FUNCTION] Form names of voice (only compatible with CN)
def form_vo_names(text_id, jp_fulltext, tr_fulltext):
    # Split the full text to get vo name and cv name
    vo_jp_name, cv_jp_name = jp_fulltext.split("/")
    vo_tr_name, cv_tr_name = tr_fulltext.split("/")

    # Determine version and gender of the voice based on text id
    vo_ver = "ngs" if re.match(r'.*9\d{2}#0,', text_id) else "o2"
    if vo_ver == "o2":
        vo_gender = "男性" if text_id.startswith("11_voice_cman") else "女性"
    elif vo_ver == "ngs":
        vo_gender = "T1" if text_id.startswith("11_voice_cman") else "T2"

    # Initialize
    vo_jp_type = vo_tr_type = [""]
    vo_jp_name_prefix = vo_tr_name_prefix = ""
    vo_jp_suffix = vo_tr_suffix = [""]
    vo_jp_suffix2 = vo_tr_suffix2 = ""

    # Generate all remaining parts of the final text
    if vo_ver == "ngs":
        vo_jp_suffix, vo_tr_suffix = ["ボイス"], ["語音"]
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
    jp_texts = [f"{vo_gend}{vo_jp_typ}{vo_jp_name_pref}{vo_jp_nam}{vo_jp_suff}{vo_jp_suff2}"
        for vo_gend in [vo_gender]
        for vo_jp_typ in vo_jp_type
        for vo_jp_name_pref in [vo_jp_name_prefix]
        for vo_jp_nam in [vo_jp_name]
        for vo_jp_suff in vo_jp_suffix
        for vo_jp_suff2 in [vo_jp_suffix2]]
    tr_texts = [f"{vo_gend}{vo_tr_typ}{' ' if re.match(r'^[a-zA-Z]', vo_tr_name) and (vo_ver == 'ngs' or vo_tr_typ == 'C') else ''}{vo_tr_nam}{vo_tr_suff}{vo_tr_suff2}"
        for vo_gend in [vo_gender]
        for vo_tr_typ in vo_tr_type
        for vo_tr_name_prefix in [' ' if re.match(r'^[a-zA-Z]', vo_tr_name) and (vo_ver == 'ngs' or vo_tr_typ == 'C') else '']
        for vo_tr_nam in [vo_tr_name]
        for vo_tr_suff in vo_tr_suffix
        for vo_tr_suff2 in [vo_tr_suffix2]]

    return jp_texts, tr_texts, cv_tr_name

# [FUNCTION] Record descriptions
def record_desc(path, jp_text):
    # Initialize
    desc_jp_explain = ""
    desc_tr_explain = ""
    desc_tr_text= ""
    # To determine if item is newly added
    desc_jp_text = ""
    # Open the file and read the data
    with open(os.path.join(jsonfile_dir, path), "r", encoding='utf-8') as f:
        data = json.load(f)
        # Set search_condition
        for item in data:
            # Search and record the descriptions 
            if jp_text == item["jp_text"]:
                desc_jp_text = item["jp_text"]
                desc_jp_explain = item["jp_explain"]
                if f"<green>“" not in item["tr_explain"]:
                    desc_tr_explain = item["tr_explain"]
                elif f"<green>“" in item["tr_explain"]:
                    desc_tr_explain = item["tr_explain"][item["tr_explain"].find('”<c>\n') + 5:]
                desc_tr_text = item["tr_text"]
    # Print jp_text if item is newly added
    if desc_jp_text == "" and "_NGS_" in path:
        print(f'ADDED: {jp_text}.')
    return desc_jp_explain, desc_tr_explain, desc_tr_text, desc_jp_text

# [FUNCTION] Get translation from tr_lines
def get_translation(jp_target_lines, tr_lines):
    tr_target_texts = []
    for text_id, jp_text in jp_target_lines:
        if LANG == 1:
            tr_text = next((tr_text for ori_text, tr_text in tr_lines if ori_text == jp_text), None)
        else:
            tr_text = next((tr_text for tr_text_id, tr_text in tr_lines if tr_text_id == text_id), None)

        if tr_text:
            tr_target_texts.append(tr_text)
        elif LANG != 0:
            tr_target_texts.append(tr_text)
            print(f"CAUTION: Can't find the translation of {jp_text}.")
            continue
    return tr_target_texts

# [FUNCTION] Form the item data
def form_itemdata(item_format, names, texts, jp_text, tr_text, ori_explains, rec_descs, trade_info):
    # Record extra parts of explains
    rec_descs_ex = ["", ""]

    # ori_explains: [JP, CN, EN], rec_descs: [JP, TR, TR_text]
    jp_explain = ori_explains[0]
    tr_explain = ori_explains[LANG]
    # explains: [JP, TR]
    explains = (jp_explain, tr_explain)

    # Form rec_descs_ex: [JP, TR]
    for i, explain in enumerate(explains):
        if explain in rec_descs[i]:
            if explain != "":
                index = rec_descs[i].find(explain)
                rec_descs_ex[i] = rec_descs[i][index + len(explain):]
            else:
                rec_descs_ex[i] = rec_descs[i]
    
    item = item_format
    # For "_NGS" generation
    if item["assign"] == 0:
        item["jp_text"] = texts[0]
        item["jp_explain"] = f"{explains[0]}{rec_descs_ex[0]}"
    # For non-translation mode
    if LANG == 0:
        item["tr_text"] = rec_descs[2]
        item["tr_explain"] = rec_descs[1]
    # For tradable items in CN mode
    elif LANG == 1 and (names[0] != names[LANG]) and trade_info != "Untradable": 
        item["tr_text"] = texts[0]
        item["tr_explain"] = f"<green>“{texts[LANG]}”<c>\n{explains[1]}{rec_descs_ex[1]}"
    # For untranslated items in EN mode
    elif LANG != 1 and (names[0] == names[LANG] or jp_text == tr_text) and re.search(r'[\u4e00-\u9fff\u3040-\u30ff]', names[LANG]):
        item["tr_text"] = ""
        item["tr_explain"] = explains[1] + rec_descs_ex[1]
    # For untradable items or EN mode
    else:
        item["tr_text"] = texts[LANG]
        item["tr_explain"] = explains[1] + rec_descs_ex[1]
    
    return item

# [FUNCTION] Check if newly deleted
def check_if_delete(rec_texts, path):
    # Open the file and read the data
    with open(os.path.join(jsonfile_dir, path), "r", encoding='utf-8') as f:
        data = json.load(f)
        for item in data:
            if item["jp_text"] not in rec_texts:
                print(f'DELETED: {item["jp_text"]}.')

# [FUNCTION] Write to json file
def write_to_json(processed_items, jsonfile_dir, path):
    processed_lines = json.dumps(list(processed_items), ensure_ascii=False, indent="\t") + "\n"
    with open(os.path.join(jsonfile_dir, path), "w", encoding='utf-8') as f:
        f.write(processed_lines)
    return

# ——————————————————————————————
# PRESET PROCESSES
# ——————————————————————————————

# Parse JP webs, to read the lines need to be considered
common_jp_lines = common_jp_lines = parse_data(common_jp_url, "csv")[0]
accessories_jp_lines = parse_data(accessories_jp_url, "csv")[0]
charamake_parts_jp_lines = parse_data(charamake_parts_jp_url, "csv")[0]
element_name_jp_lines = parse_data(element_name_jp_url, "csv")[0]

# Parse CN/EN files or webs, to read the lines need to be considered
if LANG == 0:
    common_tr_lines =  []
    accessories_tr_lines =  []
    charamake_parts_tr_lines = []
    element_name_tr_lines = []
elif LANG == 1:
    common_tr_lines = parse_data(common_cn_path, "ini")[0]
    accessories_tr_lines = parse_data(accessories_cn_path, "ini")[0]
    charamake_parts_tr_lines = parse_data(charamake_parts_cn_path, "ini")[0]
    element_name_tr_lines, aug_trade_infos = parse_data(element_name_cn_path, "ini")
elif LANG == 2:
    common_tr_lines = parse_data(common_en_url, "csv")[0]
    accessories_tr_lines = parse_data(accessories_en_url, "csv")[0]
    charamake_parts_tr_lines = parse_data(charamake_parts_en_url, "csv")[0]
    element_name_tr_lines = parse_data(element_name_en_url, "csv")[0]

# Parse swiki/makapo webs to get tradable info (only for CN)
if LANG == 1:
    for key, (suffix_url, trade_infos) in suffix_mapping.items():
        # Form full_url to get tradable info
        source = key.split('_')[0]
        full_url = f"{wiki_urls[f'{source}']}{suffix_url}"
        n_trade_infos = parse_data(full_url, "html")[1]

        # Make tradable info compatible
        original_n_trade_infos = n_trade_infos.copy()
        for jp_text, info in original_n_trade_infos.items():
            # Form the alternative version of jp_text
            alt_jp_text = width_process_string(jp_text)
            n_trade_infos[alt_jp_text] = info

        # Form the final tradable info
        trade_infos.update(n_trade_infos)

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
cp_itypes = {
    "Arm": ("アームパーツ", "臂部部件", "arm parts"),
    "Body": ("ボディパーツ", "身體部件", "body parts"),
    "Leg": ("レッグパーツ", "腿部部件", "leg parts")}
igens = {
    "a1": ["ヒト型/キャストタイプ1", "人類/機人類型1", "Human/Cast Type 1"],
    "a2": ["ヒト型/キャストタイプ2", "人類/機人類型2", "Human/Cast Type 2"],
    "h1": ["ヒト型タイプ1", "人類類型1", "Human Type 1"],
    "h2": ["ヒト型タイプ2", "人類類型2", "Human Type 2"],
    "c1": ["キャストタイプ1", "機人類型1", "Cast Type 1"],
    "c2": ["キャストタイプ2", "機人類型2", "Cast Type 2"]}

# Names of items
mo_names = ["{jp_itype}：{jp_text}", "{tr_itype}：{tr_text}", "{tr_itype}: {tr_text}"]
bp_names = ph_names = bg_names = aug_names = ou_m_names = ou_f_names = cp_m_names = cp_f_names = mou_names = ear_names = horn_names = body_names = ha_names = vo_names = ["{jp_text}", "{tr_text}", "{tr_text}"]

# Texts of items
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
ou_m_texts = ou_f_texts = cp_m_texts = cp_f_texts = mou_texts = ear_texts = horn_texts = body_texts = [
    "{jp_text}", "{tr_text}", "{tr_text}"]
ha_texts = [
    "Ha「{jp_text}」",  "Ha「{tr_text}」", "Ha \"{tr_text}\""]
vo_texts = [
    "{jp_text}", "{tr_text}", "{tr_text}"]

# Common explains of items
mo_explains = [
    "使用すると新しいモーションが\n全キャラクターで選択可能になる。\n<yellow>※『PSO2』ブロック非対応<c>",
    "使用後所有角色均可選用新的行動方式。\n<yellow>※不適用於『PSO2』<c>",
    "A motion that unlocks for all\ncharacters on your account.\n<yellow>※Not available in [PSO2] Blocks.<c>"]
bp_explains = [
    "",
    "",
    ""]
ph_explains = [
    "使用すると新しいポータブルホログラムが\n全キャラクターで選択可能になる。",
    "使用後所有角色均可選用\n新的便攜全息投影。",
    "Unlocks a new Portable Hologram for\nall characters on your account."]
bg_explains = [
    "使用すると新しいアークスカードの背景が\n全キャラクターで選択可能になる。",
    "使用後所有角色均可選用\n新的ARKS名片背景。",
    "Unlocks a new ARKS Card background\nfor all characters on your account."]
aug_explains = [
    "特殊能力を\n武器、防具に追加するカプセル。",
    "為武器、防具追加特殊能力的膠囊。",
    "A capsule that adds a Special Ability\nto a weapon or piece of armor."]
ou_m_explains = ou_f_explains = [
    "使用すると新しいアウターウェアが\n選択可能になる。",
    "使用後可選用新的外套。",
    "Unlocks a new outerwear for use."]
cp_m_explains = cp_f_explains = [
    "使用すると新しい{jp_itype}が\n選択可能になる。",
    "使用後可選用新的{tr_itype}。",
    "Unlocks new {tr_itype} for use."]
mou_explains = [
    "使用すると新しい歯・舌が\n選択可能になる。",
    "使用後可選用新的牙齒、舌頭。",
    "Unlocks a new teeth and tongue\nset for use."]
ear_explains = [
    "使用すると新しい耳が\n選択可能になる。",
    "使用後可選用新的耳朵。",
    "Unlocks a new ear shape for use."]
horn_explains = [
    "使用すると新しい角が\n選択可能になる。",
    "使用後可選用新的角。",
    "Unlocks a new horn type for use."]
body_explains = [
    "使用すると新しい肌パターンが\n選択可能になる。\n<yellow>※対応：{jp_igen}<c>",
    "使用後可選用新的皮膚種類。\n<yellow>※適用於：{tr_igen}<c>",
    "Unlocks a new body type for use.\n<yellow>※Type: {tr_igen}<c>"]
ha_explains = [
    "",
    "使用後所有角色均可選用新的手部姿勢。\n<yellow>※不適用於一部分大廳動作/\n不適用於『PSO2』<c>",
    "When used, allows you to select a\nnew hand pose for all characters.\n<yellow>※Does not support all Lobby Actions.\n※Cannot perform in [PSO2] Blocks.<c>"]
vo_explains = [
    "",
    "使用後，可選用新的語音。\nCV：{cv_tr_name}", 
    "Allows a new voice to be selected.\nUsable by all characters.\nCV: {cv_tr_name}"]

# [FUNCTION] Conditions and explains of special items
def edit_sp_explains(prefix, jp_text, explains):
    if prefix == "aug" and any(keyword in jp_text for keyword in ("フュージア", "ソブリナ", "ファウンデーター", "ディロドライエ")):
        explains = [
            f"{explains[0]}\nアイテムラボの“強化素材交換”で\n特定のカプセルとの交換にも用いられる。",
            f"{explains[1]}\n也可在道具實驗室的“交換強化素材”處\n用於交換特定的膠囊。",
            f"{explains[2]}\nCan also be exchanged for specific\ncapsules at the Item Lab."]
    if prefix == "cp_f" and "クロウリック・アーム" in jp_text:
        explains = [
            f"{explains[0]}\n<yellow>※武器の構え位置自動調整<c>",
            f"{explains[1]}\n<yellow>※自動調整武器架勢的位置<c>",
            f"{explains[2]}\n<yellow>※Uses adjusted weapon positions.<c>"]
    return explains

# Find target JP lines
mo_jp_target_lines = [
    (text_id, jp_text) for text_id, jp_text in common_jp_lines
    if text_id.startswith("Substitute_") and not jp_text.startswith(("￥"))]
bp_jp_target_lines = [
    (text_id, jp_text) for text_id, jp_text in accessories_jp_lines
    if text_id.startswith(("ob_1", "ob_6")) and not jp_text.startswith(("￥", "text_"))]
ph_jp_target_lines = [
    (text_id, jp_text) for text_id, jp_text in accessories_jp_lines
    if text_id.startswith("ob_7") and not jp_text.startswith(("￥", "text_"))]
bg_jp_target_lines = [
    (text_id, jp_text) for text_id, jp_text in get_order_jp_target_lines("bg")
    if not jp_text.startswith(("￥", "text_"))]
aug_jp_target_lines = [
    (text_id, jp_text) for text_id, jp_text in element_name_jp_lines
    if not jp_text.startswith(("ダミー", "レガロ・", "セズン・", "エスペリオ", "EX", "￥", "-"))]
ou_jp_target_lines = [
    (text_id, jp_text) for text_id, jp_text in charamake_parts_jp_lines
    if re.match(r'^No\d{6}#', text_id)
    and jp_text.endswith("[Ou]")
    and not jp_text.startswith(("￥", "text_")) and (("NPC")) not in jp_text]
ou_m_jp_target_lines = [
    (text_id, jp_text) for text_id, jp_text in ou_jp_target_lines
    if re.match(r'^No1\d{5}#', text_id)]
ou_f_jp_target_lines = [
    (text_id, jp_text) for text_id, jp_text in ou_jp_target_lines
    if re.match(r'^No2\d{5}#', text_id)]
cp_jp_target_lines = [
    (text_id, jp_text) for text_id, jp_text in charamake_parts_jp_lines
    if re.match(r'^No\d{6}#', text_id)
    and any(keyword in jp_text for keyword in ("・アーム", "・ボディ", "・レッグ"))
    and not jp_text.startswith(("￥", "text_")) and (("NPC")) not in jp_text]
cp_m_jp_target_lines = [
    (text_id, jp_text) for text_id, jp_text in cp_jp_target_lines
    if re.match(r'^No3\d{5}#', text_id)]
cp_f_jp_target_lines = [
    (text_id, jp_text) for text_id, jp_text in cp_jp_target_lines
    if re.match(r'^No4\d{5}#', text_id)]
mou_jp_target_lines, ear_jp_target_lines, horn_jp_target_lines, body_jp_target_lines = get_order_jp_target_lines("mou_to_body")
body_jp_target_lines = [
    (text_id, jp_text) for text_id, jp_text in body_jp_target_lines
    if not jp_text.startswith(("￥", "text_")) and (("NPC")) not in jp_text]
ha_jp_target_lines = [
    (text_id, jp_text) for text_id, jp_text in common_jp_lines
    if text_id.startswith("LobbyAction_")]
vo_jp_target_lines = [
    (text_id, jp_text) for text_id, jp_text in charamake_parts_jp_lines
    if text_id.startswith("11_voice_c") and (("/")) in jp_text]

# Find target translated texts
mo_tr_target_texts = get_translation(mo_jp_target_lines, common_tr_lines)
bp_tr_target_texts = get_translation(bp_jp_target_lines, accessories_tr_lines)
ph_tr_target_texts = get_translation(ph_jp_target_lines, accessories_tr_lines)
bg_tr_target_texts = get_translation(bg_jp_target_lines, charamake_parts_tr_lines)
aug_tr_target_texts = get_translation(aug_jp_target_lines, element_name_tr_lines)
ou_m_tr_target_texts = get_translation(ou_m_jp_target_lines, charamake_parts_tr_lines)
ou_f_tr_target_texts = get_translation(ou_f_jp_target_lines, charamake_parts_tr_lines)
cp_m_tr_target_texts = get_translation(cp_m_jp_target_lines, charamake_parts_tr_lines)
cp_f_tr_target_texts = get_translation(cp_f_jp_target_lines, charamake_parts_tr_lines)
mou_tr_target_texts = get_translation(mou_jp_target_lines, charamake_parts_tr_lines)
ear_tr_target_texts = get_translation(ear_jp_target_lines, charamake_parts_tr_lines)
horn_tr_target_texts = get_translation(horn_jp_target_lines, charamake_parts_tr_lines)
body_tr_target_texts = get_translation(body_jp_target_lines, charamake_parts_tr_lines)
ha_tr_target_texts = get_translation(ha_jp_target_lines, common_tr_lines)
vo_tr_target_texts = get_translation(vo_jp_target_lines, charamake_parts_tr_lines)

# [FUNCTION] Conditions of force to change the tradable info (only for CN)
def extra_condition(prefix, jp_text):
    if prefix == "mo":
       return jp_text.endswith(("EX"))
    elif prefix == "bp":
        return jp_text.startswith(("エアル：", "リテナ：", "ノクト：", "エウロ：", "クヴァル：", "ピエド：", "ワフウ：", "立体図形：", "立体数字：", "アクリル台座・", "ベーシック", "モダン", "クラシック", "ゴシック", "スイーツ", "チャイナ", "ウェスタン", "オリエント", "レトロ", "オールド", "ファンシー", "ラボラトリー", "エレガント", "ナイトクラブ", "ウッディ", "学校の", "リゾート", "ビンテージ", "ワノ", "ミニ")) and not jp_text.startswith(("ミニミニ"))
    elif prefix == "ph":
        return jp_text == ""
    elif prefix == "bg":
        return jp_text == ""
    elif prefix == "aug":
        return jp_text.endswith(("S", "LC"))
    elif prefix == "ou_m":
        return jp_text == ""
    elif prefix == "ou_f":
        return jp_text == ""
    elif prefix == "cp_m":
        return jp_text == ""
    elif prefix == "cp_f":
        return jp_text == ""
    elif prefix == "fp":
        return jp_text == ""
    elif prefix == "ha":
        return jp_text == jp_text
    elif prefix == "vo":
        return jp_text == ""

# ——————————————————————————————
# MAIN PROCESS
# ——————————————————————————————

# [FUNCTION] Generate "NGS_" json files
def main_generate_NGS(prefix):
    # Get jp target lines and tr target texts from global variables
    path = globals()[f"{prefix}_path"]
    jp_target_lines = globals()[f"{prefix}_jp_target_lines"]
    tr_target_texts = globals()[f"{prefix}_tr_target_texts"]
    trade_infos = globals()[f"{prefix}_trade_infos"]

    # Initialize the processed items
    processed_items = []
    processed_item_texts = []

    # Start the loop to generate item
    for i, (text_id, jp_text) in enumerate(jp_target_lines):
        # Get translated text from texts
        if LANG != 0:
            tr_text = tr_target_texts[i]
        else:
            tr_text = ""
        # Get category and the category name for certain prefixes
        if prefix == "mo":
            itype = text_id.split("_")[1]
            jp_itype = mo_itypes[itype][0]
            tr_itype = mo_itypes[itype][LANG]
        elif prefix.startswith("cp_"):
            if "・アーム" in jp_text:
                itype = "Arm"
            elif "・ボディ" in jp_text:
                itype = "Body"
            elif "・レッグ" in jp_text:
                itype = "Leg"
            jp_itype = cp_itypes[itype][0]
            tr_itype = cp_itypes[itype][LANG]
        else:
            jp_itype = tr_itype = ""
        # Get gender and the gender name for certain prefixes
        if prefix == "body":
            if text_id.startswith("No1"):
                igen = "a1"
            elif text_id.startswith("No2"):
                igen = "a2"
            jp_igen = igens[igen][0]
            tr_igen = igens[igen][LANG]
        else:
            jp_igen = tr_igen = ""
        
        # Get names and texts from global variables
        names = [name.format(
            jp_itype = jp_itype, tr_itype = tr_itype,
            jp_text = jp_text, tr_text = tr_text)
            for name in globals()[f"{prefix}_names"]]
        texts = [text.format(
            jp_itype = jp_itype, tr_itype = tr_itype,
            jp_text = jp_text, tr_text = tr_text)
            for text in globals()[f"{prefix}_texts"]]
        explains = [explain.format(
            jp_itype = jp_itype, tr_itype = tr_itype,
            jp_igen = jp_igen, tr_igen = tr_igen)
            for explain in globals()[f"{prefix}_explains"]]
        # Edit the explains of special item
        explains = edit_sp_explains(prefix, jp_text, explains)

        # Determine if generating the same item
        repeated = False
        for item in processed_items:
            if texts[0] == item["jp_text"]:
                repeated = True
        if repeated == True:
            continue 
        # Get tradable info from global variable
        trade_info = trade_infos.get(names[0], "")
        if extra_condition(prefix, jp_text):
            trade_info = "Untradable"
        # Record descriptions
        rec_descs = record_desc(path, texts[0])
        # Item format
        item_format = {
            "jp_text": "",
            "tr_text": "",
            "jp_explain": "",
            "tr_explain": "",
            "assign": 0}
        
        # Generate item
        item = form_itemdata(item_format, names, texts, jp_text, tr_text, explains, rec_descs, trade_info)
        # Form the processed data
        processed_items.append(item)
        processed_item_texts.append(rec_descs[3])

    # Write to json file
    check_if_delete(processed_item_texts, path)
    write_to_json(processed_items, jsonfile_dir, path)
    print(f'PROGRESS: processed {len(processed_items)} items in "{path}".')

# [FUNCTION] Generate "Stack_" json files
def main_edit_Stack(prefix):
    # Get jp target lines and tr target texts from global variables
    path = globals()[f"{prefix}_path"]
    jp_target_lines = globals()[f"{prefix}_jp_target_lines"]
    tr_target_texts = globals()[f"{prefix}_tr_target_texts"]
    trade_infos = globals()[f"{prefix}_trade_infos"]

     # Initialize the processed items
    with open(os.path.join(jsonfile_dir, path), "r", encoding='utf-8') as f:
        processed_items = json.load(f)
    processed_count = 0

    # Start the loop to generate item
    for i, (text_id, jp_text) in enumerate(jp_target_lines):
        # Get translated text from texts
        if LANG != 0:
            tr_text = tr_target_texts[i]
        else:
            tr_text = ""
        # Get category and the category name for certain prefixes
        jp_itype = tr_itype = ""
        # Get special item names for vo
        if prefix == "vo":
            jp_texts, tr_texts, cv_tr_name = form_vo_names(text_id, jp_text, tr_text)
        else:
            jp_texts = [jp_text]
            tr_texts = [tr_text]
            cv_tr_name = ""
        
        for i, jp_text in enumerate(jp_texts):
            tr_text = tr_texts[i]

            # Get names and texts from global variables
            names = [name.format(
                jp_text = jp_text, tr_text = tr_text)
                for name in globals()[f"{prefix}_names"]]
            texts = [text.format(
                jp_text = jp_text, tr_text = tr_text)
                for text in globals()[f"{prefix}_texts"]]
            explains = [explain.format(
                jp_itype = jp_itype, tr_itype = tr_itype,
                cv_tr_name = cv_tr_name if prefix == "vo" else None)
                for explain in globals()[f"{prefix}_explains"]]
            # Edit the explains of special item
            explains = edit_sp_explains(prefix, jp_text, explains)

            # Get tradable info from global variable
            trade_info = trade_infos.get(names[0], "")
            if extra_condition(prefix, jp_text):
                trade_info = "Untradable"
            # Record descriptions
            rec_descs = record_desc(path, texts[0])

            # Item formats
            items_format = []
            # Form the alter version of texts[0]
            text_index = texts[0].index(names[0])
            text0_left = texts[0][:text_index]
            text0_right = texts[0][text_index + len(names[0]):]
            alt_name0 = width_process_string(names[0])
            alt_text0 = text0_left + alt_name0 + text0_right
            # Get the item format
            for processed_item in processed_items:
                if processed_item["jp_text"] in (texts[0], alt_text0):
                    items_format.append(processed_item)
            for item_format in items_format:
                assign = item_format["assign"]
                # Generate item
                item = form_itemdata(item_format, names, texts, jp_text, tr_text, explains, rec_descs, trade_info)
                for processed_item in processed_items:
                    # Find lines with existing descriptions
                    if processed_item["assign"] == assign:
                        for key in processed_item:
                            processed_item[key] = item.get(key, processed_item[key])
                # Add the count
                processed_count = processed_count + 1

    # Write to json file
    write_to_json(processed_items, jsonfile_dir, path)
    print(f'PROGRESS: processed {processed_count} items in "{path}".')

# Generate "NGS_" json files
process_prefixes = ["mo", "bp", "ph", "bg", "aug", "ou_m", "ou_f", "cp_m", "cp_f", "mou", "ear", "horn", "body"]
for prefix in process_prefixes:
     main_generate_NGS(prefix)

# Generate "Stack_" json files (only for CN)
if LANG == 1:
    process_prefixes = ["ha", "vo"]
    for prefix in process_prefixes:
        main_edit_Stack(prefix)

# ——————————————————————————————

print("ALL COMPLETED.")
