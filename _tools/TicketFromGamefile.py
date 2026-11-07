import argparse
import os
import re
import json
import requests
from collections import Counter, defaultdict
from functools import cache
from html import unescape
from time import sleep
from urllib.parse import quote
# Internal shared rules and gamefile helpers; this is the TicketFromGamefile.py entry point.
from _ticket_gamefile import rules
from _ticket_gamefile.io import strip_ring_name, web_pages
from _ticket_gamefile.rules import (
    no_explains,
    plain_formats,
    ca_itype_translations,
    contains_japanese,
    disk_matches_file,
    disk_prefixes,
    edit_special_text,
    equipment_dot_translations,
    equipment_parentheses_translations,
    equipment_space_translations,
    equipment_suffix_separators,
    equipment_types,
    explain_prefixes,
    format_common_suffix,
    form_vo_names,
    get_explain_source,
    get_explain_text,
    get_json_paths,
    get_target_lines,
    iter_equipment_structures,
    lang_names,
    min_assign_digits,
    mo_itypes,
    resolve_language,
    ring_hand_translations,
    ring_slash_translations,
    ring_type_translations,
    source_for_prefix,
    source_files,
    csv_path,
    split_common_suffix,
    split_type_parentheses,
    start_assigns,
    strip_series_suffix,
    upgrade_material_type_separators,
    upgrade_material_types,
    width_key,
    width_process_string,
)

# ——————————————————————————————
# LANGUAGE SETTING
# ——————————————————————————————

# This tool updates existing JSON translations from the main game files.
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

# JP URL directories; source filenames and CN paths come from source_files.
csv_url = "JP/Files/"
csv_reboot_url = "JP_Reboot/Files/"

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
    'ngs_eye': ('エステ/瞳・まゆ・まつげ#eyes', ("eye", )),
    'ngs_brow': ('エステ/瞳・まゆ・まつげ#eyebrow', ("brow", )),
    'ngs_lash': ('エステ/瞳・まゆ・まつげ#eyelash', ("lash", )),
    'ngs_hair': ('エステ/ヘアスタイル', ("hair", )),
    'ngs_ac_head': ('エステ/アクセサリー（頭部）', ("ac", )),
    'ngs_ac_other': ('エステ/アクセサリー（その他）', ("ac", )),
    'ngs_bpa': ('エステ/ボディペイント', ("bpa", )),
    'ngs_mou': ('エステ/口・歯・耳・角#mouth', ("mou", )),
    'ngs_ear': ('エステ/口・歯・耳・角#ear', ("ear", )),
    'ngs_horn': ('エステ/口・歯・耳・角#horn', ("horn", )),
    'ngs_body': ('エステ/肌', ("body", )),
    'ngs_head': ('エステ/ヘッドパーツ', ("head", )),
    'ngs_stk': ('エステ/ステッカー', ("stk", )),
    'ngs_fpa': ('エステ/メイクパターン', ("fpa", )),
    'ngs_face': ('エステ/顔', ("face", )),
    'ngs_wear_m': ('エステ/ウェア/男性型レイヤリング', ("ou", "ba", "in", "cp")),
    'ngs_wear_f': ('エステ/ウェア/女性型レイヤリング', ("ou", "ba", "in", "cp")),
    'ngs_wear_common': ('エステ/ウェア/男女共用', ("ba", )),
    'ngs_wear_total': ('エステ/ウェア/トータルウェア', ("ba", )),
    'ngs_rg': ('スキルリング', ("rg", )),
    # Music trade lookup stays disabled; uncomment to use the table parser below.
    # 'ngs_md': ('ミュージックディスク', ("md", ))
    }
# swiki pages with one item per table row, and the column of item names
# (weapons of other types are found by sword series)
row_wiki_pages = {'防具': 2, 'ソード': 2, 'ミュージックディスク': 1,
                  '武器迷彩': 1, '武器迷彩/実装情報（過去分）': 1,
                  '素材アイテム': 2,
                  'エステ/瞳・まゆ・まつげ#eyes': 1,
                  'エステ/瞳・まゆ・まつげ#eyebrow': 1,
                  'エステ/瞳・まゆ・まつげ#eyelash': 1,
                  'エステ/ヘアスタイル': 1, 'エステ/ボディペイント': 1,
                  'エステ/アクセサリー（頭部）': 2, 'エステ/アクセサリー（その他）': 2,
                  'エステ/口・歯・耳・角#mouth': 1,
                  'エステ/口・歯・耳・角#ear': 1, 'エステ/口・歯・耳・角#horn': 1,
                  'エステ/肌': 1, 'エステ/ヘッドパーツ': 1, 'エステ/ステッカー': 1,
                  'エステ/メイクパターン': 1, 'エステ/顔': 1}
# These wiki sources provide AH evidence independently of translated gamefile names.
row_trade_prefixes = ('eye', 'brow', 'lash', 'hair', 'ac', 'bpa', 'md',
                      'mou', 'ear', 'horn', 'body', 'head', 'stk', 'fpa', 'face',
                      'ou', 'ba', 'in', 'cp', 'rg')
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
    parser.add_argument('--reject-copied-jp', action=argparse.BooleanOptionalAction, default=None,
                        help='Reject translations copied from Japanese (default: off for CN, on otherwise)')
    arguments = parser.parse_args(argv)
    try:
        arguments.lang = resolve_language(arguments.lang if arguments.lang is not None else LANG,
                                          os.path.dirname(root_dir))
    except ValueError as error:
        parser.error(str(error))
    if arguments.reject_copied_jp is None:
        arguments.reject_copied_jp = arguments.lang != 'CN'
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
@cache
def get_web(url, report=print_status):
    url_part = url.rsplit('/', 1)[-1].split('?', 1)[-1]
    # Match TicketToGamefile.py's timeout/retries; requests retains URL and charset handling.
    for attempt in range(3):
        try:
            with requests.get(url, timeout=30) as response:
                response.raise_for_status()
                lines = response.text
        except requests.RequestException as error:
            status = error.response.status_code if error.response is not None else None
            if status == 404:
                report("FAILED", f"File does not exist: {url} (skipped)")
                return None
            if attempt == 2 or (status is not None and status < 500):
                report("FAILED", f"{url} ({error})")
                raise
            report("RETRY", f"{url_part} (attempt {attempt + 2}/3; {error})")
            sleep(attempt + 1)
        else:
            report("LOADED", url_part)
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

# [FUNCTION] Strip tags without changing each caller's entity or whitespace rules.
def strip_html(data, separator=''):
    return re.sub(r'<[^>]+>', separator, data)


# [FUNCTION] Read visible names or notes separated by HTML line breaks.
def split_html_lines(data):
    return [unescape(strip_html(text)).strip() for text in re.split(r'<br\b[^>]*>', data)]


# [FUNCTION] Recognize explicit restrictions in a row's own explanation.
def has_trade_prohibition(text):
    return bool(re.search(r'(?:マイショップ(?:への)?出品|取引|トレード)(?:は)?(?:不可|できない|できません)', text))


# [FUNCTION] Recognize the shared variant prefix while leaving its scope to the category.
def match_note_branch(note):
    return re.match(r'^\(([-A-Za-z0-9/]+)\)(.*)', note)


# [FUNCTION] Read currencies from visible source text and actual currency icons only.
def get_source_types(data):
    text = unescape(strip_html(data, ' '))
    sources = set(re.findall(r'(?<![A-Za-z_%])(AC|SG|GP|SP)(?=スクラッチ|\s|$)', text))
    if 'スペシャルスクラッチ' in text:
        sources.add('SP')
    for image in re.findall(r'<img\b[^>]*>', data, re.I):
        for _, label in re.findall(r'\s(?:alt|title)\s*=\s*([\"\'])(.*?)\1', image, re.I):
            icon = re.fullmatch(r'(AC|SG|GP|SP)(?:\.png)?', unescape(label), re.I)
            if icon:
                sources.add(icon[1].upper())
    return sources


# [FUNCTION] Normalize table headers once while keeping source cells unchanged.
def get_table_headers(cells):
    return {column: re.sub(r'\s+', '', strip_html(text)) for column, text in cells.items()}


# [FUNCTION] Locate source/notes columns in the normalized category table headers.
def get_source_columns(headers):
    return [column for column, text in headers.items()
            if any(label in text
                   for label in ('入手', '備考', 'ｽｸﾗｯﾁ区分', '必要GP', '必要SG'))]


# [FUNCTION] Collect raw source cells and their shared evidence before category decisions.
def get_source_evidence(cells, columns):
    source_cells = [cells[column] for column in columns if column in cells]
    return {'cells': source_cells, 'types': get_source_types(''.join(source_cells))}


# [FUNCTION] Keep conflicting evidence unknown regardless of page or row order.
def merge_trade_infos(current, incoming):
    for name, info in incoming.items():
        previous = current.get(name)
        current[name] = 'Unknown' if previous and info and previous != info else previous or info


# [FUNCTION] Expand table cells once, keeping shared cells inside their own table.
def iter_html_tables(data):
    start = 0
    for match in re.finditer(r'<table\b[^>]*>(.*?)</table>', data, re.S):
        before, table = data[start:match.start()], match[1]
        start = match.end()
        rows = []
        spans = {}
        for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>', table, re.S):
            cells = {column: text for column, (_, text) in spans.items()}
            spans = {column: (remaining - 1, text) for column, (remaining, text) in spans.items()
                     if remaining > 1}
            column = 0
            for attrs, text in re.findall(r'<t[dh]\b([^>]*)>(.*?)</t[dh]>', row, re.S):
                while column in cells:
                    column += 1
                rowspan = re.search(r'rowspan="(\d+)"', attrs)
                colspan = re.search(r'colspan="(\d+)"', attrs)
                for _ in range(int(colspan[1]) if colspan else 1):
                    cells[column] = text
                    if rowspan and int(rowspan[1]) > 1:
                        spans[column] = (int(rowspan[1]) - 1, text)
                    column += 1
            rows.append((bool(re.search(r'<th\b', row)), dict(sorted(cells.items()))))
        yield before, rows


# [FUNCTION] Associate explicit shop prohibitions with full names in salon/music/wear tables.
def parse_row_trade_infos(data, name_column, salon_page, shared_prohibition=False):
    trade_infos = {}
    for _, rows in iter_html_tables(data):
        note_column = None
        name_columns = []
        source_columns = []
        for is_header, cells in rows:
            if is_header:
                headers = get_table_headers(cells)
                note_column = next((column for column, text in headers.items() if text.endswith('備考')), None)
                source_columns = get_source_columns(headers)
                name_columns = ([name_column] if name_column is not None else
                                [column for column, text in headers.items()
                                 if text in ('名称', '種類', 'ボディ', 'アーム', 'レッグ')])
                if name_column is not None and headers.get(name_column) not in ('名称', 'アイテム名'):
                    note_column = None
                    name_columns = []
                continue
            if not name_columns or (note_column not in cells and not shared_prohibition):
                continue
            names = [name for column in name_columns if column in cells
                     for name in split_html_lines(cells[column])]
            names = [name for name in names if name]
            if name_column is None:
                # Wear tables also contain character/series labels; keep actual item names.
                names = [name.lstrip('┣┗━├└│ ') for name in names
                         if re.search(r'\[(?:Ou|Ba|Se|In|Fu|To)\]$|・(?:アーム|ボディ|レッグ)(?:V\d+)?(?:/[A-Za-z0-9]+)?$', name)]
            notes = split_html_lines(cells.get(note_column, ''))
            if not names or not (shared_prohibition or any(has_trade_prohibition(note) for note in notes)):
                continue
            branches = defaultdict(list)
            for note in notes:
                match = match_note_branch(note)
                if match:
                    for variant in match[1].split('/'):
                        branches[variant].append(match[2])
            if branches:
                # Only a branch's own prohibition applies; /B, /2, etc. stay distinct.
                for variant, explains in branches.items():
                    if any(has_trade_prohibition(text) for text in explains):
                        stem, suffix = re.fullmatch(r'(.*?)(\[[^]]+\])?', names[0]).groups()
                        name = names[0] if variant == '-' else f'{stem}/{variant}{suffix or ""}'
                        if name in names:
                            mixed_source = any('ACスクラッチ' in text and not has_trade_prohibition(text)
                                               for text in explains)
                            merge_trade_infos(trade_infos, {name: 'Unknown' if mixed_source else 'Untradable'})
                # Unqualified prohibitions on mixed-source rows are ambiguous.
                if any(has_trade_prohibition(text) for texts in branches.values() for text in texts):
                    continue
            source_types = get_source_evidence(cells, source_columns)['types']
            mixed_sources = 'AC' in source_types and bool(branches or source_types & {'SG', 'SP'})
            if salon_page and mixed_sources:
                merge_trade_infos(trade_infos, dict.fromkeys(names, 'Unknown'))
                continue
            merge_trade_infos(trade_infos, dict.fromkeys(names, 'Untradable'))
    return trade_infos


# [FUNCTION] Read section-wide declarations and row notes on the four wear category pages.
def parse_wear_trade_infos(data):
    trade_infos = {}
    for section in re.split(r'<h[1-6]\b[^>]*>.*?</h[1-6]>', data, flags=re.S):
        explanation = unescape(strip_html(re.sub(r'<table\b.*?</table>', '', section, flags=re.S)))
        shared_prohibition = has_trade_prohibition(explanation) and bool(re.search(r'全て|すべて|以下|下記', explanation))
        merge_trade_infos(trade_infos, parse_row_trade_infos(section, None, False, shared_prohibition))
    return trade_infos


# [FUNCTION] Parse the web or file
def parse_data(file_path, file_type, download=None, comment_translations=None):
    page_path = file_path.split("#", 1)[0]
    is_upgrade_page = file_type == "html" and page_path.endswith("素材アイテム")
    # Determine the type of file_path
    if file_path.startswith("http"):
        try:
            data = get_web(page_path) if download is None else download()
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
    if file_type == "ini" and comment_translations is not None:
        comment_translations.update(parse_ini_comment_translations(lines))

    row_page = next((page for page in row_wiki_pages if file_path.endswith(page)), '')
    if file_type == 'html':
        # Only article content is evidence; comments can quote unrelated restrictions.
        data = re.split(r'<h[1-6]\b[^>]*id="comment"[^>]*>', '\n'.join(lines), maxsplit=1)[0]
        if 'エステ/ウェア/' in page_path:
            return [], parse_wear_trade_infos(data)
        if page_path.endswith('スキルリング'):
            for title, section in re.findall(r'<h3\b[^>]*>(.*?)</h3>(.*?)(?=<h[1-3]\b|\Z)', data, re.S):
                name = unescape(strip_html(title)).strip()
                effect = re.search(r'<table\b.*?</table>.*?(?=<table\b|\Z)', section, re.S)
                if re.fullmatch(r'タイプ[12]／.+', name) and effect and has_trade_prohibition(strip_html(effect[0])):
                    merge_trade_infos(trade_infos, {name: 'Untradable'})
            return [], trade_infos
        if row_page.startswith('エステ/') or row_page == 'ミュージックディスク':
            if '#' in row_page:
                anchor = re.escape(row_page.split('#', 1)[1])
                section = re.search(rf'<h2\b[^>]*id="{anchor}"[^>]*>.*?(?=<h2\b|\Z)', data, re.S)
                if section is None:
                    return [], {}
                data = section.group()
            return [], parse_row_trade_infos(data, row_wiki_pages[row_page], row_page.startswith('エステ/'))

        quote_pattern = r'(Mo|BP|PH|Bg|Ma|Sv)「([^」]+)」'
        is_camo_page = "武器迷彩" in file_path
        name_column = next((column for page, column in row_wiki_pages.items() if page_path.endswith(page)), None)
        for before, rows in iter_html_tables(data):
            source_columns = []
            makapo_started = '<span id="GPNGS">' in before
            for is_header, cells in rows:
                if is_header:
                    source_columns = get_source_columns(get_table_headers(cells))
                    if any('<span id="GPNGS">' in cell for cell in cells.values()):
                        makapo_started = True
                    continue
                if name_column is not None:
                    if name_column not in cells:
                        continue
                    source_column = max(cells)
                    source_cell = cells[source_column]
                    source = unescape(strip_html(source_cell))
                    trade_info = "Untradable"
                    if is_upgrade_page:
                        explanation = cells.get(4, '')
                        if "#equipment_upgrade" not in explanation:
                            continue
                        trade_info = "Untradable" if has_trade_prohibition(strip_html(explanation)) else ""
                    elif is_camo_page:
                        if source_column <= name_column:
                            continue
                        if 'SG' not in get_source_types(source_cell) and not any(keyword in source for keyword in (
                            'マイショップ出品不可', 'SGスクラッチ',
                            'スペシャルスクラッチ', 'SPスクラッチ', 'イベント', 'キャンペーン', '称号', '交換', 'タスク', 'Task')):
                            continue
                    elif "マイショップ出品不可" not in ''.join(cells.values()):
                        continue
                    at_only_prohibition = (page_path.endswith('ソード') and '[AT]' in source
                                           and not has_trade_prohibition(source.split('[AT]', 1)[0]))
                    names = split_html_lines(cells[name_column])
                    merge_trade_infos(trade_infos, {name: trade_info for name in names
                                                   if name and not (at_only_prohibition and not name.endswith('AT'))})
                elif "ngs" in file_path and "エステ" not in file_path:
                    visible = {column: unescape(strip_html(text)) for column, text in cells.items()}
                    quote_columns = {}
                    for column, text in visible.items():
                        matches = re.findall(quote_pattern, text)
                        for headname in dict.fromkeys(head for head, _ in matches):
                            quote_columns.setdefault(headname, (column, [name for head, name in matches if head == headname]))
                    for quote_column, names in quote_columns.values():
                        columns = source_columns or [quote_column + 1, quote_column + 3]
                        evidence = get_source_evidence(cells, columns)
                        source_cells, source_types = evidence['cells'], evidence['types']
                        notes = [note for cell in source_cells for note in split_html_lines(cell)]
                        branch_prohibition = any(match_note_branch(note)
                                                 and has_trade_prohibition(note) for note in notes)
                        mixed_sources = 'AC' in source_types and bool(source_types & {'SG', 'SP'})
                        if branch_prohibition or mixed_sources:
                            row_infos = dict.fromkeys(names, 'Unknown')
                            base_notes = [note for note in notes if note.startswith('(-)')]
                            if (names and any(has_trade_prohibition(note) for note in base_notes)
                                    and not any('ACスクラッチ' in note and not has_trade_prohibition(note)
                                                for note in base_notes)):
                                row_infos[names[0]] = 'Untradable'
                            merge_trade_infos(trade_infos, row_infos)
                        else:
                            source_prohibition = (has_trade_prohibition(''.join(strip_html(cell) for cell in source_cells))
                                                  or bool(source_types & {'GP', 'SG'})
                                                  or any(keyword in note for note in notes for keyword in
                                                         ('初期', 'トレジャースクラッチ', 'クラス育成特別プログラム'))
                                                  or any(cell.rstrip().endswith(('交換', '季節イベント', 'SPスクラッチ',
                                                                                 '開発準備特別票', '初期登録')) for cell in source_cells))
                            if source_prohibition or makapo_started:
                                merge_trade_infos(trade_infos, dict.fromkeys(names, 'Untradable'))
                    if any('<span id="GPNGS">' in cell for cell in cells.values()):
                        makapo_started = True
                else:
                    columns = source_columns or (1, 3 if 'ngs' in file_path else 4)
                    evidence = get_source_evidence(cells, columns)
                    source = ''.join(evidence['cells'])
                    if not (has_trade_prohibition(strip_html(source)) or 'SG' in evidence['types']):
                        continue
                    names = split_html_lines(cells.get(0, ''))
                    merge_trade_infos(trade_infos, {name: 'Untradable' for name in names
                                                   if name.startswith(('男性', '女性', 'T1', 'T2'))})
        return [], trade_infos

    for i, line in enumerate(lines):
        line = line.rstrip('\n')

        # Process .text.ini files
        if file_type == "ini":
            # Get ori_text and tr_text besides the "="
            if "=" in line:
                ori_text, tr_text = split_ini_line(line)
                merge_trade_infos(trade_infos, {ori_text: ""})
                parsed_lines.append((ori_text, tr_text))
            # Get the trade_infos from comments (mainly for augments)
            if line.startswith(";不可交易") and i > 0:
                ori_text = split_ini_line(lines[i - 1].rstrip('\n'))[0]
                merge_trade_infos(trade_infos, {ori_text: "Untradable"})

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

    return parsed_lines, trade_infos

# [FUNCTION] Parse the commented translations (";JP=TR") of .ini file
def parse_ini_comment_translations(lines):
    translations = {}
    for line in lines:
        if line.startswith(";") and "=" in line:
            key, value = line[1:].rstrip("\r\n").split("=", 1)
            translations[key] = value
    return translations


# [FUNCTION] Parse the web to get trade info
def parse_info(full_url, prefixes, download=None):
    n_infos = parse_data(full_url, "html", download)[1]
    # Also record items with names in a different width
    for jp_text, trade_info in list(n_infos.items()):
        merge_trade_infos(n_infos, {width_process_string(jp_text): trade_info})
    for prefix in prefixes:
        prefix_infos = trade_infos[prefix]
        merge_trade_infos(prefix_infos, n_infos)
        normalized_infos = {}
        for jp_text, trade_info in prefix_infos.items():
            merge_trade_infos(normalized_infos, {width_key(jp_text): trade_info})
        # All spellings of one width-normalized name share its evidence.
        for jp_text in list(prefix_infos):
            prefix_infos[jp_text] = normalized_infos[width_key(jp_text)]
        merge_trade_infos(prefix_infos, normalized_infos)


# [FUNCTION] Get translations of jp_target_lines from tr_lines (None if not found)
def get_translation(jp_target_lines, tr_lines, text_part=str):
    # CN translations are found by JP text, others are found by text_id
    translations = {}
    for key, tr_text in tr_lines:
        translations.setdefault(key, tr_text)

    tr_target_texts = []
    for text_id, jp_text, *jp_refer in jp_target_lines:
        tr_text = translations.get(jp_text if LANG == 1 else text_id)
        jp_text = text_part(jp_text)
        if tr_text is None:
            print_status("CAUTION", f"No translation record for {jp_text}")
        else:
            tr_text = text_part(tr_text).strip()
            if not tr_text:
                print_status("CAUTION", f"Empty translation for {jp_text}")
            # A copied JP source must not erase a JSON name when rejection is enabled.
            elif args.reject_copied_jp and tr_text == jp_text and contains_japanese(jp_text):
                print_status("CAUTION", f"Copied Japanese translation for {jp_text} (rejected)")
                tr_text = None
        tr_target_texts.append(tr_text)
    return tr_target_texts


# [FUNCTION] Build series records (sorted by length of JP name) from "item_series_name"
def build_equipment_series_records():
    jp_target_lines = [(text_id, jp_text) for text_id, jp_text in jp_sources["item_series_name"]
                       if (jp_base := strip_series_suffix(jp_text)) and not jp_base.startswith("￥")]
    translated_bases = get_translation(
        jp_target_lines, translation_sources["item_series_name"], strip_series_suffix)
    records = []
    for (text_id, jp_text), translated_base in zip(jp_target_lines, translated_bases):
        jp_base = strip_series_suffix(jp_text)
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
    for side in ("pre", "post"):
        if side == "post" and structure["has_type"]:
            result += (get_equipment_separator(False) if type_separator is None else type_separator) + translated_type
        for parent_base, small_name, has_dot in structure[side]:
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
def form_card_texts(stack_text, translated_name, parsed_text):
    _, jp_prefix, element, cost_and_rarity = parsed_text
    translated_element = ca_itype_translations[element]
    texts = [template.format(tr_itype=translated_element[index], cost=cost_and_rarity,
                             tr_text=translated_name) if template and translated_element[index] else ""
            for index, template in enumerate(rules.ca_texts)]
    texts[0] = stack_text
    return texts

# [FUNCTION] Format language templates, leaving unsupported slots empty.
def format_templates(templates, fields):
    return [template.format(**fields) if template is not None else "" for template in templates]


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
    if "\n<yellow>" in tr_explain and "\n<yellow>" in rec_tr_explain:
        if tr_explain.split("\n", 1)[0] == rec_tr_explain.split("\n", 1)[0]:
            tr_explain = tr_explain.split("\n<yellow>", 1)[0] + "\n<yellow>" + rec_tr_explain.split("\n<yellow>", 1)[1]
    if tr_explain in rec_tr_explain:
        tr_explain += rec_tr_explain[rec_tr_explain.find(tr_explain) + len(tr_explain):]

    # For untranslated items when copied Japanese names are rejected
    if args.reject_copied_jp and entry["untranslated"] and contains_japanese(names[LANG]):
        item["tr_text"] = ""
    # For tradable items in CN mode
    elif LANG == 1 and entry["trade_info"] != "Untradable":
        item["tr_text"] = item["jp_text"]
        if texts[0] != texts[LANG]:
            tr_explain = f"<green>“{texts[LANG]}”<c>\n{tr_explain}"
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
json_paths = get_json_paths(args.lang, forward=True)
print_stage(f"TicketFromGamefile ({args.lang}; online JP, "
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
jp_sources = {}
jp_urls = {name: f"{PSO2CSV_url}{csv_reboot_url if reboot else csv_url}{name}.csv"
           for name, (reboot, _) in source_files.items()}
with web_pages(jp_urls.values(), get_web, print_status) as pages:
    for name, url in jp_urls.items():
        jp_sources[name] = parse_data(url, "csv", pages[url])[0]

# Parse CN text.ini or the selected language's CSV translations.
print_stage(f"Loading {lang_names[LANG]} translations")
translation_sources = {}
item_series_name_comment_tr = {}
if LANG == 1:
    for name, (_, cn_path) in source_files.items():
        path = os.path.join(PSO2CN_path, cn_path)
        translation_sources[name], tradable = parse_data(
            path, "ini", comment_translations=item_series_name_comment_tr if name == "item_series_name" else None)
        if name == "item_element_name_reb":
            trade_infos["aug"] = tradable
        elif name == "ui_item":
            trade_infos["rg"] = tradable
else:
    csv_urls = {name: f"{PSO2CSV_url}{args.lang}{'_Reboot' if reboot else ''}/{quote(csv_path(name, args.lang))}"
                for name, (reboot, _) in source_files.items()}
    with web_pages(csv_urls.values(), get_web, print_status) as pages:
        for name, url in csv_urls.items():
            translation_sources[name] = parse_data(url, "csv", pages[url])[0]

# Material rows also identify the supported equipment upgrade scope in CSV modes.
print_stage("Loading material/tradable info from swiki/makapo")
info_pages = [(f"{wiki_urls[key.split('_')[0]]}{page}", prefixes)
              for key, (page, prefixes) in trade_mapping.items() if LANG == 1 or key == "ngs_um"]
with web_pages((url.split("#", 1)[0] for url, _ in info_pages), get_web, print_status) as pages:
    for url, prefixes in info_pages:
        parse_info(url, prefixes, pages[url.split("#", 1)[0]])

# Find series records of weapons and units
equipment_series_records, equipment_series_by_base = build_equipment_series_records()

# ——————————————————————————————
# MAPPINGS AND CONDITIONS
# ——————————————————————————————


def edit_sp_texts(prefix, jp_text, tr_text, jp_refer):
    return edit_special_text(prefix, jp_text, tr_text, jp_refer, LANG)

# Select the same JP tables in both directions.
game_target_lines = {
    prefix: (entries, translation_sources[source_for_prefix[prefix]])
    for prefix, entries in get_target_lines(jp_sources).items()
    if prefix in json_paths
}


# [FUNCTION] Conditions of force to change the tradable info (only for CN)
def extra_condition(prefix, jp_text, text_id, trade_info="", card_text=None):
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
        if card_text is None:
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
    tr_explain_texts = [""] * len(jp_target_lines)
    if prefix in explain_prefixes:
        jp_explain_lines = [(text_id[:-1] + "1", jp_explain) for text_id, _, jp_explain in jp_target_lines]
        tr_explain_texts = get_translation(jp_explain_lines, tr_lines, lambda text: get_explain_text(prefix, text))
    prefix_trade_infos = trade_infos[prefix]
    # Cards are found by name, others are found by text
    entries = {}
    missing_translation_count = 0
    text_formats = plain_formats if prefix == "ca" else getattr(rules, f"{prefix}_texts", plain_formats)

    for (text_id, jp_text, *jp_refer), tr_text, tr_explain in zip(jp_target_lines, tr_target_texts, tr_explain_texts):
        missing_translation = not tr_text
        # Edit special texts of special item
        jp_text, tr_text = edit_sp_texts(prefix, jp_text, tr_text or "", jp_refer)
        fields = {"jp_itype": "", "tr_itype": "", "cv_tr_name": "",
                  "jp_explain": "", "tr_explain": tr_explain or ""}
        if prefix in explain_prefixes:
            fields["jp_explain"] = get_explain_text(prefix, jp_refer[0])
        # Get category and the category name for certain prefixes
        if prefix == "mo":
            itype = mo_itypes[text_id.split("_")[1]]
            fields.update(jp_itype = itype[0], tr_itype = itype[LANG])
            missing_translation |= itype[LANG] is None
        elif prefix in ring_hand_translations:
            itype = ring_hand_translations[prefix]
            fields.update(jp_itype = itype[0], tr_itype = itype[LANG])
        missing_translation |= tr_text is None or text_formats[LANG] is None
        # Get all names of voice
        name_pairs = [(jp_text, tr_text)]
        if prefix == "vo":
            jp_texts, tr_texts, fields["cv_tr_name"] = form_vo_names(text_id, jp_text, tr_text)
            name_pairs = zip(jp_texts, tr_texts)

        for jp_name, tr_name in name_pairs:
            # Get names, texts and explains from shared rules
            fields.update(jp_text = jp_name, tr_text = tr_name)
            names = format_templates(getattr(rules, f"{prefix}_names", plain_formats), fields)
            texts = format_templates(text_formats, fields)
            explains = format_templates(getattr(rules, f"{prefix}_explains", no_explains), fields)
            if prefix in explain_prefixes and not tr_explain:
                explains = no_explains
            # Get tradable info of all lines (e.g. a card is untradable if any of its lines is untradable)
            if extra_condition(prefix, jp_name, text_id):
                prefix_trade_infos[names[0]] = "Untradable"
            key = names[0] if prefix == "ca" else texts[0]
            if missing_translation or key in entries:
                continue
            entries[key] = {"text_id": text_id, "names": names, "texts": texts, "explains": explains,
                            "refer": jp_refer, "untranslated": names[0] == names[LANG] or jp_name == tr_name}
        missing_translation_count += missing_translation

    # Keep both width conversions; either alias must identify a unique source record.
    normalized_entries = {}
    alt_entries = {}
    for key, entry in entries.items():
        normalized_key = width_key(key)
        alt_key = key.replace(entry["names"][0], width_process_string(entry["names"][0]), 1)
        for aliases, alias_key in ((normalized_entries, normalized_key), (alt_entries, alt_key)):
            if alias_key not in aliases:
                aliases[alias_key] = entry
            elif aliases[alias_key] is not entry:
                aliases[alias_key] = None

    def get_entry(path, item):
        key = item["jp_text"]
        if prefix == "ca":
            card_text = parse_card_stack_text(key)
            if card_text is None:
                return None
            key = card_text[0]
        entry = entries.get(key)
        if entry is None:
            normalized_key = width_key(key)
            entry = (normalized_entries[normalized_key] if normalized_key in normalized_entries
                     else alt_entries.get(key))
        if entry is None:
            return None
        if prefix in disk_prefixes and not disk_matches_file(path, entry["text_id"]):
            return None
        jp_name = entry["names"][0]
        entry = {**entry, "trade_info": prefix_trade_infos.get(jp_name, prefix_trade_infos.get(width_key(jp_name), ""))}
        if prefix in explain_prefixes:
            field = get_explain_source(prefix, item["jp_explain"], entry["names"][0], entry["refer"][0])
            if field is None:
                entry["explains"] = no_explains
            elif field == 0:
                hand = ring_hand_translations[prefix]
                fields = {"jp_itype": hand[0], "tr_itype": hand[LANG],
                          "jp_explain": entry["names"][0], "tr_explain": entry["names"][LANG]}
                entry["explains"] = [explain.format(**fields) for explain in getattr(rules, prefix + "_explains")]
        if prefix == "ca":
            entry["texts"] = form_card_texts(item["jp_text"], entry["names"][LANG], card_text)
            if not entry["texts"][LANG]:
                return None
            entry["trade_info"] = "Untradable" if extra_condition(
                prefix, item["jp_text"], "", entry["trade_info"], card_text) else ""
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
    for text_id, jp_text in jp_sources["ui_item"]:
        if text_id.startswith("ring_") and text_id.endswith("#1"):
            ui_item_jp_by_skill.setdefault(strip_ring_name(jp_text), []).append(text_id)
    jp_target_lines = [(text_ids[0], skill_name) for skill_name, text_ids in ui_item_jp_by_skill.items()
                       if len(text_ids) == 1]
    translated_skills = get_translation(jp_target_lines, translation_sources["ui_item"], strip_ring_name)
    ui_item_translations = {skill_name: translated_skill
                            for (_, skill_name), translated_skill in zip(jp_target_lines, translated_skills)}
    untranslated_texts = []

    def get_entry(path, item):
        type_name, separator, skill_name = item["jp_text"].partition("／")
        type_names = ring_type_translations.get(type_name)
        translated_skill = ui_item_translations.get(skill_name)
        # Skip rings without a unique translation
        if not separator or type_names is None or type_names[LANG] is None or not translated_skill:
            untranslated_texts.append(item["jp_text"])
            return None
        translated_name = f"{type_names[LANG]}{ring_slash_translations[LANG]}{translated_skill}"
        trade_info = trade_infos[prefix].get(item["jp_text"], trade_infos[prefix].get(skill_name, ""))
        return form_name_entry(item["jp_text"], translated_name, trade_info)

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
    summary = Counter()
    json_items = {}
    for path in json_paths[prefix]:
        try:
            with open(os.path.join(jsonfile_dir, path), "r", encoding='utf-8') as f:
                json_items[path] = json.load(f)
        except FileNotFoundError:
            print_status("FAILED", f"File does not exist: {os.path.join(jsonfile_dir, path)} (skipped)")
            summary["missing_files"] += 1
            continue
    if LANG == 1 and prefix in row_trade_prefixes:
        # One wiki name cannot identify multiple es assigns, including across files.
        name_counts = Counter(width_key(item['jp_text']) for items in json_items.values() for item in items)
        for name in list(trade_infos[prefix]):
            if name_counts[width_key(name)] > 1:
                trade_infos[prefix].pop(name, None)
    get_entry, report = entry_builders.get(prefix, build_game_entries)(prefix)
    for path, items in json_items.items():
        summary["files"] += 1
        summary["items"] += len(items)
        start = [item["assign"] for item in items].index(start_assigns[prefix]) if prefix in start_assigns else 0
        summary["excluded"] += start
        _count = 0
        changed_items = []
        for item in items[start:]:
            if len(str(item["assign"])) < min_assign_digits.get(prefix, 0):
                summary["excluded"] += 1
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
            else:
                summary["unmatched"] += 1
        summary["changed"] += len(changed_items)
        summary["unchanged"] += _count - len(changed_items)
        summary["changed_files"] += bool(changed_items)
        write_to_json(items, jsonfile_dir, path)
        print_status("UPDATED", f"{len(changed_items):>5} / {_count:>5} / {len(items):<5}  {path}")
        for assign, jp_text, changes in changed_items:
            print_status("CHANGED", f"[{assign}] {json.dumps(jp_text, ensure_ascii=False)} | {' | '.join(changes)}")
    report()
    return summary

# Update json files from the shared category scope
print_stage(f"Updating json files ({lang_names[LANG]} mode; changed /  / total)")
summary = Counter()
for prefix in json_paths:
    summary.update(main_update(prefix))

# ——————————————————————————————

print_stage("TicketFromGamefile results")
print_status("PREVIEW" if args.debug else "DONE",
             f"{summary['changed']} JSON items {'would change' if args.debug else 'changed'} in "
             f"{summary['changed_files']} files; {summary['unchanged']} matched items unchanged")
print_status("FILES", f"{summary['files']} read; {summary['missing_files']} missing")
print_status("SKIPPED", f"{summary['unmatched']} JSON items without a match; {summary['excluded']} outside scope")
print_stage("All completed")
