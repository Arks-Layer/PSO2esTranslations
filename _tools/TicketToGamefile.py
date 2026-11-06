#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Update local text.ini/CSV gamefiles from JSON, using online JP text IDs."""

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from http.client import IncompleteRead
import json
from pathlib import Path
import re
import subprocess
from time import sleep
import unicodedata
from urllib.error import HTTPError
from urllib.request import urlopen

from _ticket_gamefile import rules
from _ticket_gamefile.rules import effective_name, width_key
from _ticket_gamefile.io import (GameFile, preserve_padding, replace_ring_name, replace_series_name,
                              strip_ring_name, web_pages)


# ——————————————————————————————
# LANGUAGE SETTING
# ——————————————————————————————

# This tool fills local gamefiles directly from existing JSON translations.
# Edit the settings below, then run this script without a long list of arguments.
# Append --debug to keep the normal logs without writing local gamefiles.

# None follows the current branch; --lang overrides this setting.
# 1: CN (text.ini); 2: EN, 3: KO, 4: RU, 5: TH (CSV).
LANG = None


# ——————————————————————————————
# PATH & URL SETTING
# ——————————————————————————————

# Path of this tool, its repository, and the parent folder of local checkouts.
root_dir = Path(__file__).resolve().parent
project_dir = root_dir.parent
repositories_dir = project_dir.parent

# JSON translation sources. Source JSON is never modified.
jsonfile_dir = project_dir / 'json'
# Optional explicit local Git revision; None reads the current working JSON.
# --json-dir overrides both this directory and the revision.
json_ref = None

# JP source URLs match TicketFromGamefile.py. These downloads only provide
# the original names and text IDs; no local JP checkout is required or modified.
PSO2CSV_url = 'https://raw.githubusercontent.com/Arks-Layer/PSO2ENPatchCSV/'
csv_jp_url = 'JP/Files/'
csv_reboot_jp_url = 'JP_Reboot/Files/'

# Local CN gamefiles: UI/*.text.ini and Unsorted/ngs/lineduel_text.text.ini.
PSO2CN_path = repositories_dir / 'PSO2_CHN_Translation'

# Local Arks-Layer CSV checkouts for the selected language.
PSO2CSV_path = repositories_dir / 'PSO2ENPatchCSV(EN_win32)'
PSO2CSV_reboot_path = repositories_dir / 'PSO2ENPatchCSV(EN_win32reboot)'

# ——————————————————————————————
# MAPPINGS AND CONDITIONS
# ——————————————————————————————

# A placeholder separates translated name components from ticket decorations.
MARKER = '譯名佔位符'


# ——————————————————————————————
# FUNCTION
# ——————————————————————————————

# [FUNCTION] Print the title of a stage, following TicketFromGamefile.py's output style.
def print_stage(title):
    print(f"\n{'=' * 64}\n  {title}\n{'=' * 64}")


# [FUNCTION] Print a status line and its associated path or result.
def print_status(status, message):
    print(f'  {status:<9}{message}')


@dataclass(frozen=True)
class Field:
    """One unknown component of a reversible name pattern."""

    name: tuple


# [FUNCTION] Recover name components only if exactly one assignment fits the whole name.
def extract_name(tokens, text, known=None):
    """Accept a decomposition only when exactly one assignment explains the name."""
    known = known or {}
    solutions = []

    def visit(index, offset, values):
        # Two different solutions already prove ambiguity; do not pick the first.
        if len(solutions) > 1:
            return
        if index == len(tokens):
            if offset == len(text) and values not in solutions:
                solutions.append(dict(values))
            return
        token = tokens[index]
        value = token if isinstance(token, str) else values.get(token, known.get(token))
        if value is not None:
            if text.startswith(value, offset):
                visit(index + 1, offset + len(value), values)
            return
        for end in range(offset + 1, len(text) + 1):
            values[token] = text[offset:end]
            visit(index + 1, end, values)
        values.pop(token, None)

    visit(0, 0, {})
    if len(solutions) != 1:
        return None
    values = {token: known[token] for token in tokens if isinstance(token, Field) and token in known} | solutions[0]
    return {token: value.strip() for token, value in values.items()}


# [FUNCTION] Turn a ticket format into literal decorations and one translated-name field.
def format_tokens(template, **fields):
    prefix, suffix = template.format(tr_text=MARKER, jp_text=MARKER, **fields).split(MARKER)
    return [prefix, Field(('name',)), suffix]


# [FUNCTION] Rebuild a name or series value from its recovered components.
def render_tokens(tokens, values):
    return ''.join(token if isinstance(token, str) else values[token] for token in tokens)


# [FUNCTION] Remove only the localized gender, type, number and voice decorations.
def csv_voice_name(entry, item_name, japanese_item, language):
    """Remove only the gender/type/Voice decorations whose JP structure is known."""
    source_name = entry['jp'].split('/')[0]
    parts = {key: values[language] for key, values in rules.vo_name_parts.items()}
    if any(value is None for value in parts.values()):
        return None
    voice_pattern = '(?:' + parts['voice'] + ')'
    prefix, suffix = entry['source_prefix'], entry['source_suffix']
    if prefix in ('T1', 'T2') and suffix.isdigit():
        match = re.fullmatch(re.escape(prefix) + r' (.+?) ' + voice_pattern + r'\s*' + re.escape(suffix), item_name)
        # KO keeps its number attached; EN/TH retain their existing spaces.
        number_separator = '' if language == 3 else ' '
        return f'{prefix} {match[1].strip()}{number_separator}{suffix}' if match else None
    if japanese_item.startswith(('T1', 'T2')):
        match = re.fullmatch(re.escape(japanese_item[:2]) + r' (.+) ' + voice_pattern, item_name)
        if not match:
            return None
        return f'{japanese_item[:2]} {match[1].strip()}' if source_name.startswith(('T1', 'T2')) else match[1].strip()
    gender = parts['male'] if japanese_item.startswith('男性') else parts['female'] if japanese_item.startswith('女性') else None
    if gender is None:
        return None
    match = re.fullmatch('(' + parts['all'] + ')?' + gender + r'\s*(.+)', item_name)
    if not match:
        return None
    label = match[2].strip()
    if '共通' in japanese_item or 'Ｃ' in japanese_item:
        label = re.sub('^' + parts['common'], '', label, count=1).strip()
    elif match[1]:
        return None
    for jp_prefix, translated_prefix in [('追加ボイス', parts['extra']), ('［ＥＸ］ボイス', parts['ex'])]:
        if source_name.startswith(jp_prefix):
            number = unicodedata.normalize('NFKC', source_name.removeprefix(jp_prefix))
            match = re.fullmatch(translated_prefix + r'\s*([A-ZＡ-Ｚ]?[0-9０-９]+)', label)
            if not match or unicodedata.normalize('NFKC', match[1]).lstrip('0') != number.lstrip('0'):
                return None
            return label
    if source_name.endswith(('ボイス', 'Ｖｏ')):
        return label if re.search(' ' + voice_pattern + '$', label) else None
    match = re.fullmatch(r'(.+) ' + voice_pattern, label)
    return match[1].strip() if match else None


@dataclass
class EquipmentPattern:
    """A name pattern and the source-series values it can restore."""

    tokens: list
    writes: dict


class ReverseGenerator:
    """Collect evidence first; conflicting or incomplete evidence never becomes a write."""

    # [FUNCTION] Index JP item structures without trusting the old gamefile translations.
    def __init__(self, lang, japanese, targets):
        self.lang = lang
        self.language = rules.lang_names.index(lang)
        self.json_paths = rules.get_json_paths(lang, forward=False)
        self.japanese = japanese
        self.targets = targets
        self.jp_pairs = {name: japanese[name].pairs if name in japanese else [] for name in rules.source_files}
        self.items = []
        self.proposals = defaultdict(lambda: defaultdict(set))
        self.equipment = []
        self.series_keys = defaultdict(list)
        self.series_records = []
        for text_id, name in self.jp_pairs['item_series_name']:
            base = rules.strip_series_suffix(name)
            if base and not base.startswith('￥'):
                self.series_records.append({'jp_base': base})
                self.series_keys[base].append(self.target_key('item_series_name', text_id, name))
        # These commented CN aliases are read as data by TicketFromGamefile.py too.
        if lang == 'CN' and 'item_series_name' in targets:
            for key, value in targets['item_series_name'].pairs:
                if key.startswith(';') and value:
                    base = key[1:]
                    self.series_keys[base].append(key)
                    self.series_records.append({'jp_base': base})
        self.series_records.sort(key=lambda row: len(row['jp_base']), reverse=True)
        self.series_by_base = {record['jp_base']: record for record in self.series_records}
        self.ring_skills = defaultdict(list)
        for text_id, text in self.jp_pairs['ui_item']:
            if text_id.startswith('ring_') and text_id.endswith('#1'):
                self.ring_skills[strip_ring_name(text)].append(text_id)
        self.direct = defaultdict(list)
        for category, entries in rules.get_target_lines(self.jp_pairs).items():
            if category not in self.json_paths:
                continue
            for text_id, name, *refer in entries:
                source = rules.source_for_prefix[category]
                if category == 'vo':
                    self._index_voice(text_id, name)
                    continue
                jp_name, translated = rules.edit_special_text(category, name, MARKER, refer, self.language)
                if translated is None:
                    continue
                fields = {'jp_itype': '', 'tr_itype': '', 'cv_tr_name': ''}
                if category == 'mo':
                    motion_type = rules.mo_itypes.get(text_id.split('_')[1])
                    if motion_type is None:
                        raise ValueError(f'Unknown motion type: {text_id}')
                    if motion_type[self.language] is None:
                        continue
                    fields.update(jp_itype=motion_type[0], tr_itype=motion_type[self.language])
                elif category in rules.ring_hand_translations:
                    hand = rules.ring_hand_translations[category]
                    fields.update(jp_itype=hand[0], tr_itype=hand[self.language])
                templates = getattr(rules, category + '_texts', rules.plain_formats)
                if templates[self.language] is None:
                    continue
                lookup = jp_name if category == 'ca' else templates[0].format(jp_text=jp_name, **fields)
                self.direct[category, width_key(lookup)].append({
                    'source': source, 'id': text_id, 'jp': name, 'jp_name': jp_name, 'refer': refer,
                    'translation': translated, 'template': templates[self.language], 'fields': fields,
                })

    # [FUNCTION] Locate CN entries by full JP text and EN entries by their original text ID.
    def target_key(self, source, text_id, japanese):
        return japanese if self.lang == 'CN' else text_id

    # [FUNCTION] Index voice variants while retaining their letters, spaces and NGS numbers.
    def _index_voice(self, text_id, name):
        jp_name, _ = rules.edit_special_text('vo', name, MARKER, [], self.language)
        suffix = re.search(r'([A-ZＡ-Ｚ])$', jp_name.split('/')[0])
        # CN spacing differs for Chinese and Latin names; retain both possibilities.
        markers = [MARKER, 'TranslationMarker']
        if suffix:
            markers += [marker + unicodedata.normalize('NFKC', suffix[1]) for marker in markers]
        for marker in markers:
            placeholder = MARKER if marker.startswith(MARKER) else 'TranslationMarker'
            numbered = re.fullmatch(r'(T[12]).*(\d{3})', jp_name.split('/')[0])
            source_marker = numbered[1] + marker + numbered[2] if numbered else marker
            source_prefix, source_suffix = source_marker.split(placeholder)
            jp_names, patterns, _ = rules.form_vo_names(text_id, jp_name, source_marker + '/CVMarker')
            for jp, pattern in zip(jp_names, patterns):
                if placeholder in pattern:
                    self.direct['vo', width_key(jp)].append({
                        'source': 'ui_charamake_parts', 'id': text_id, 'jp': name,
                        'pattern': pattern, 'marker': placeholder, 'effective_jp': jp_name,
                        'source_prefix': source_prefix, 'source_suffix': source_suffix,
                    })

    # [FUNCTION] Check JSON fields and the existing category scope, then collect all candidates.
    def add_items(self, files):
        self.filenames = set(files)
        for category, filenames in self.json_paths.items():
            for filename in filenames:
                if filename not in files:
                    continue
                rows = files[filename]
                if not isinstance(rows, list):
                    raise ValueError(f'{filename}: expected a JSON list')
                start_assign = rules.start_assigns.get(category)
                if start_assign and not any(str(row['assign']) == start_assign for row in rows):
                    raise ValueError(f'{filename}: missing scope boundary {start_assign}')
                started = not start_assign
                for index, item in enumerate(rows):
                    required = ('assign', 'jp_text', 'tr_text', 'tr_explain')
                    if category in rules.explain_prefixes:
                        required += ('jp_explain',)
                    if (not isinstance(item, dict) or any(key not in item for key in required)
                            or any(not isinstance(item[key], str) for key in required[1:])
                            or not isinstance(item['assign'], (str, int)) or isinstance(item['assign'], bool)):
                        raise ValueError(f'{filename}:{index}: invalid item fields')
                    started = started or str(item['assign']) == start_assign
                    record = {'id': len(self.items), 'file': filename, 'index': index,
                              'assign': str(item['assign']), 'category': category,
                              'jp_text': item['jp_text'], 'name': '', 'status': 'pending',
                              'reason': '', 'targets': [], 'dependencies': []}
                    self.items.append(record)
                    if not started or len(record['assign']) < rules.min_assign_digits.get(category, 0):
                        record.update(status='excluded', reason='outside_forward_scope')
                        continue
                    source = rules.source_for_prefix.get(category, 'ui_item' if category == 'rg' else 'item_series_name')
                    if source not in self.targets:
                        record.update(status='skipped', reason='target_file_missing')
                        continue
                    if (getattr(rules, category + '_texts', rules.plain_formats)[self.language] is None
                            or category == 'vo' and self.lang != 'CN'
                            and rules.vo_name_parts['male'][self.language] is None):
                        record.update(status='skipped', reason='missing_language_dictionary')
                        continue
                    try:
                        record['name'] = effective_name(item, self.lang)
                        same_name = width_key(record['name']) == width_key(item['jp_text'])
                        if not record['name'] or (same_name and (self.lang == 'CN' or rules.contains_japanese(record['name']))):
                            raise ValueError('no_translated_name')
                        if category in ('wp', 'wc', 'un', 'um'):
                            patterns = self.equipment_patterns(category, filename, item['jp_text'], record['name'])
                            if not patterns:
                                raise ValueError('no_reversible_series_structure')
                            self.equipment.append((record, patterns))
                        elif category == 'rg':
                            self.reverse_ring(record)
                        elif category == 'vo':
                            self.reverse_voice(record, item)
                        else:
                            self.reverse_direct(record, item)
                    except ValueError as error:
                        record.update(status='skipped', reason=str(error))
        self.reverse_equipment()
        return self.finish()

    # [FUNCTION] Recover simple names and ticket contents, including card variant references.
    def reverse_direct(self, record, item):
        category = record['category']
        lookup = record['jp_text']
        if category == 'ca':
            match = re.fullmatch(r'Ca「([^：]+)：(.+)」', lookup)
            if not match:
                raise ValueError('invalid_card_structure')
            lookup = match[2]
        sources = self.direct.get((category, width_key(lookup)), [])
        if category in rules.disk_prefixes:
            sources = [entry for entry in sources if rules.disk_matches_file(record['file'], entry['id'])]
        if not sources:
            raise ValueError('japanese_source_missing')
        pending = []
        for entry in sources:
            translated = entry['translation']
            if translated.count(MARKER) != 1:
                raise ValueError('noninvertible_special_name')
            inner_prefix, inner_suffix = translated.split(MARKER)
            if category == 'ca':
                element = next((key for key in rules.ca_itype_translations if match[1].startswith(key)), None)
                if element is None:
                    raise ValueError('invalid_card_element')
                cost = match[1][len(element):]
                translated_element = rules.ca_itype_translations[element][self.language]
                tokens = format_tokens(rules.ca_texts[self.language], tr_itype=translated_element, cost=cost)
            else:
                tokens = format_tokens(entry['template'], **entry['fields'])
            tokens[0] += inner_prefix
            tokens[-1] = inner_suffix + tokens[-1]
            values = extract_name(tokens, record['name'])
            if values is None:
                raise ValueError('translated_name_does_not_fit_template')
            key = self.target_key(entry['source'], entry['id'], entry['jp'])
            pending.append((entry['source'], key, values[Field(('name',))]))
            if category in rules.explain_prefixes:
                templates = getattr(rules, category + '_explains')
                field = rules.get_explain_source(category, item['jp_explain'], entry['jp_name'], entry['refer'][0])
                if field is None:
                    continue
                body = item['tr_explain']
                if self.lang == 'CN':
                    body = re.sub(r'^<green>“[^\n]*”<c>\n', '', body, count=1)
                body = body.split('\n<yellow>', 1)[0]
                template = templates[self.language].split('\n<yellow>', 1)[0]
                values = extract_name(format_tokens(template, tr_explain=MARKER, **entry['fields']), body)
                if values is None:
                    continue
                value = values[Field(('name',))]
                if category in ('pa', 'tec'):
                    value = value.replace('\n', '<br>')
                japanese = entry['refer'][0] if field == 1 else entry['jp']
                key = self.target_key(entry['source'], entry['id'][:-1] + str(field), japanese)
                target = self.targets[entry['source']].entries.get(key)
                if category in rules.ring_hand_translations and field == 1 and target is not None:
                    value = replace_ring_name(target.text, value, preserve_suffix=False)
                pending.append((entry['source'], key, value))
        self._commit_candidates(record, pending, 'direct_name')

    # [FUNCTION] Validate every field of an item before contributing it to shared targets.
    def _commit_candidates(self, record, candidates, rule):
        # Validate the complete item before contributing any field to a shared target.
        for source, key, value in candidates:
            target = self.targets[source]
            if key not in target.entries or key in target.ambiguous:
                raise ValueError('target_key_missing_or_ambiguous')
            if not value:
                raise ValueError('empty_translation_value')
        for source, key, value in candidates:
            value = preserve_padding(self.targets[source].entries[key].text, value)
            self.proposals[source, key][value].add(record['id'])
            proposal = {'source': source, 'key': key, 'value': value, 'rule': rule}
            if proposal not in record['targets']:
                record['targets'].append(proposal)

    # [FUNCTION] Replace only the skill-name part and preserve the gamefile description.
    def reverse_ring(self, record):
        kind, separator, skill = record['jp_text'].partition('／')
        if not separator or kind not in rules.ring_type_translations:
            raise ValueError('invalid_ring_structure')
        translated_type = rules.ring_type_translations[kind][self.language]
        if translated_type is None:
            raise ValueError('missing_language_dictionary')
        prefix = translated_type + rules.ring_slash_translations[self.language]
        values = extract_name([prefix, Field(('name',))], record['name'])
        if values is None or not values[Field(('name',))]:
            raise ValueError('translated_name_does_not_fit_template')
        translated_skill = values[Field(('name',))]
        matches = self.ring_skills.get(skill, [])
        if len(matches) != 1:
            raise ValueError('ring_skill_source_not_unique')
        text_id = matches[0]
        key = self.target_key('ui_item', text_id, skill)
        target = self.targets['ui_item']
        if key not in target.entries or key in target.ambiguous:
            raise ValueError('target_key_missing_or_ambiguous')
        value = replace_ring_name(target.entries[key].text, translated_skill)
        self._commit_candidates(record, [('ui_item', key, value)], 'ring_name_only')

    # [FUNCTION] Recover a voice name and its explicit CV without copying the full description.
    def reverse_voice(self, record, item):
        sources = self.direct.get(('vo', width_key(record['jp_text'])), [])
        if not sources:
            raise ValueError('japanese_voice_source_missing')
        cv_match = re.search(r'(?:^|\n)(?:CV[：:]|ＣＶ[：:]?)\s*([^\n]+)(?:\n<yellow>.*)?$', item['tr_explain'], re.S)
        if not cv_match:
            raise ValueError('voice_cv_missing_or_wrapped')
        cv = cv_match[1].strip()
        candidates = set()
        for entry in sources:
            if self.lang == 'CN':
                marker = entry['marker']
                prefix, suffix = entry['pattern'].split(marker, 1)
                tokens = [prefix, Field(('name',)), suffix]
                values = extract_name(tokens, record['name'])
                if values is None:
                    continue
                voice = values[Field(('name',))]
                voice = entry['source_prefix'] + voice + entry['source_suffix']
                raw_voice = entry['effective_jp'].split('/')[0]
                if raw_voice.startswith(('追加ボイス', '［ＥＸ］ボイス')):
                    number = re.search(r'([A-Z]?\d+)$', unicodedata.normalize('NFKC', raw_voice))
                    translated_number = re.search(r'([A-Z]?\d+)$', unicodedata.normalize('NFKC', voice))
                    if not number or not translated_number or number[1].lstrip('0') != translated_number[1].lstrip('0'):
                        continue
                if re.search(r'[\u4e00-\u9fa5][A-Z]$', voice) and not re.search(r'[A-ZＡ-Ｚ]$', raw_voice):
                    continue
                jp_names, tr_names, _ = rules.form_vo_names(entry['id'], entry['effective_jp'], voice + '/' + cv)
                if not any(width_key(jp) == width_key(record['jp_text']) and tr == render_tokens(tokens, values)
                           for jp, tr in zip(jp_names, tr_names)):
                    continue
            else:
                voice = csv_voice_name(entry, record['name'], record['jp_text'], self.language)
                if voice is None:
                    continue
            key = self.target_key('ui_charamake_parts', entry['id'], entry['jp'])
            if '/' in entry['jp']:
                value = voice + '/' + cv
                original = self.targets['ui_charamake_parts'].entries.get(key)
                if original is not None and '/' in original.text:
                    original_voice, original_cv = original.text.split('/', 1)
                    value = preserve_padding(original_voice, voice) + '/' + preserve_padding(original_cv, cv)
            else:
                _, expected = rules.edit_special_text('vo', entry['jp'], voice, [], self.language)
                if expected is None:
                    continue
                expected_cv = expected.split('/', 1)[-1]
                if expected_cv != cv:
                    continue
                value = voice
            candidates.add(('ui_charamake_parts', key, value))
        if len({(key, value) for _, key, value in candidates}) != 1:
            raise ValueError('voice_translation_not_uniquely_recoverable')
        self._commit_candidates(record, candidates, 'voice_name_and_cv')

    # [FUNCTION] Build reversible series/type/suffix patterns for equipment and materials.
    def equipment_patterns(self, category, filename, japanese, translated):
        camo_prefix = camo_suffix = ''
        if category == 'wc':
            if not japanese.startswith('＊'):
                return []
            japanese = japanese[1:]
            camo_prefix = '＊'
            match = re.search(r'CV(?:\d+|-M\d+)?$', japanese)
            if match:
                camo_suffix, japanese = match.group(), japanese[:match.start()]
        stem, suffix = rules.split_common_suffix(japanese)
        separator = rules.equipment_space_translations[self.language]
        suffix_separator = rules.equipment_suffix_separators[self.language]
        tail = ''
        if suffix:
            tail += suffix_separator + rules.format_common_suffix(suffix, self.language)
        if camo_suffix:
            tail += suffix_separator + camo_suffix
        if category == 'um':
            for jp_type, names in rules.upgrade_material_types.items():
                base = stem.removesuffix(jp_type)
                if base != stem and base in self.series_keys and any(not key.startswith(';') for key in self.series_keys[base]):
                    if names[self.language] is None:
                        return []
                    field = Field(('series', base))
                    gap = rules.upgrade_material_type_separators[self.language].get(jp_type, separator)
                    return [EquipmentPattern([field, gap + names[self.language] + tail], {base: [field]})]
            return []
        names = rules.equipment_types[filename]
        if names[self.language] is None:
            return []
        stem, parentheses = rules.split_type_parentheses(stem, names[0])
        patterns = []
        for structure in rules.iter_equipment_structures(stem, names[0], self.series_records, self.series_by_base):
            if parentheses and structure['has_type']:
                continue
            base = structure['record']['jp_base']
            root = Field(('series', base))
            tokens = [camo_prefix, root]
            writes = {base: [root]}
            complete = True
            for position in ('pre', 'post'):
                if position == 'post' and structure['has_type']:
                    tokens += [separator + names[self.language]]
                for parent, small, has_dot in structure[position]:
                    gap = ('·' if has_dot else '') if self.lang == 'CN' else ' '
                    field = Field(('small', parent, small))
                    tokens += [gap, field]
                    full = next((parent + dot + small for dot in ('・', '') if parent + dot + small in self.series_keys), None)
                    if small in self.series_keys and any(key.startswith(';') for key in self.series_keys[small]):
                        writes[small] = [field]
                    elif full is None:
                        complete = False
                        break
                    if full is not None and parent in writes:
                        writes[full] = writes[parent] + [gap, field]
            if not complete:
                continue
            if parentheses:
                left, right = rules.equipment_parentheses_translations[self.language]
                tokens += [separator + left + names[self.language] + right]
            tokens += [tail]
            patterns.append(EquipmentPattern(tokens, writes))
        return patterns

    # [FUNCTION] Reuse only a series spelling supported consistently by JSON candidates.
    def known_series(self):
        values = {}
        for base, keys in self.series_keys.items():
            candidates = set()
            for key in keys:
                candidates.update(self.proposals.get(('item_series_name', key), {}))
            if len(candidates) == 1:
                values[Field(('series', base))] = rules.strip_series_suffix(next(iter(candidates)))
        return values

    # [FUNCTION] Resolve independent names first, then use their consensus for dependent series.
    def reverse_equipment(self):
        pending = list(self.equipment)
        # Old target translations must not decide how an ambiguous name is split.
        while pending:
            known = self.known_series()
            solved = []
            remaining = []
            for record, patterns in pending:
                alternatives = {}
                for pattern in patterns:
                    values = extract_name(pattern.tokens, record['name'])
                    used_known = values is None
                    if used_known:
                        values = extract_name(pattern.tokens, record['name'], known)
                    if values is None:
                        continue
                    names = {base: render_tokens(formula, values) for base, formula in pattern.writes.items()}
                    signature = tuple(sorted(names.items()))
                    dependencies = {token.name[1] for token in pattern.tokens
                                    if used_known and isinstance(token, Field)
                                    and token in known and token.name[0] == 'series'}
                    alternatives[signature] = (names, dependencies)
                if len(alternatives) != 1:
                    remaining.append((record, patterns))
                    continue
                names, dependencies = next(iter(alternatives.values()))
                candidates = []
                for base, name in names.items():
                    for key in self.series_keys[base]:
                        entry = self.targets['item_series_name'].entries.get(key)
                        if entry is None:
                            candidates.append(('item_series_name', key, name))
                        else:
                            value = name if key.startswith(';') else replace_series_name(entry.text, name, self.lang)
                            candidates.append(('item_series_name', key, value))
                record['dependencies'] = sorted(dependencies)
                solved.append((record, candidates))
            if not solved:
                for record, _ in remaining:
                    record.update(status='skipped', reason='series_decomposition_ambiguous_or_inconsistent')
                break
            for record, candidates in solved:
                try:
                    self._commit_candidates(record, candidates, 'equipment_series')
                except ValueError as error:
                    record.update(status='skipped', reason=str(error))
            pending = remaining

    # [FUNCTION] Propagate conflicts and produce replacements only for agreed target values.
    def finish(self):
        conflicts = {location for location, values in self.proposals.items() if len(values) > 1}
        blocked = set()
        # A conflicting root also invalidates every value derived from that root.
        while True:
            old = set(conflicts)
            for record in self.items:
                dependencies = {('item_series_name', key) for base in record['dependencies'] for key in self.series_keys[base]}
                locations = {(entry['source'], entry['key']) for entry in record['targets']}
                if dependencies & conflicts or locations & conflicts:
                    blocked.add(record['id'])
                    conflicts.update(locations)
            if old == conflicts:
                break
        replacements = defaultdict(dict)
        changes = []
        for (source, key), values in sorted(self.proposals.items()):
            target = self.targets[source]
            before = target.entries[key].text
            contributors = sorted(set().union(*values.values()))
            conflict = (source, key) in conflicts
            after = next(iter(values)) if not conflict else before
            if not conflict:
                replacements[source][key] = after
            changes.append({'source': source, 'key': key, 'line': target.entries[key].line + 1,
                            'old': before, 'new': after,
                            'status': 'conflict' if conflict else 'unchanged' if before == after else 'changed',
                            'candidates': [{'value': value, 'items': sorted(ids)} for value, ids in sorted(values.items())],
                            'items': contributors})
        for record in self.items:
            if record['id'] in blocked:
                record.update(status='conflict', reason='conflicting_translation_or_dependency')
            elif record['targets']:
                changed = any(self.targets[target['source']].entries[target['key']].text != target['value'] for target in record['targets'])
                record['status'] = 'changed' if changed else 'unchanged'
            elif record['status'] == 'pending':
                record.update(status='skipped', reason='no_candidate')
        self.replacements = dict(replacements)
        return {'language': self.lang,
                'summary': {'items': dict(Counter(item['status'] for item in self.items)),
                            'targets': dict(Counter(change['status'] for change in changes)),
                            'reasons': dict(Counter(item['reason'] for item in self.items if item['reason'])),
                            'json_files': len(self.filenames)},
                'items': self.items, 'targets': changes}


# [FUNCTION] Load a JP CSV from the same URL layout as TicketFromGamefile.py.
def get_web(url, report=print_status):
    # Retry transient connection failures, keeping TLS verification enabled.
    # A missing/forbidden source or a third failure must stop the run.
    for attempt in range(3):
        try:
            with urlopen(url, timeout=30) as response:
                content = response.read()
        except (OSError, IncompleteRead) as error:
            if isinstance(error, HTTPError) and error.code == 404:
                error.close()
                report('FAILED', f'File does not exist: {url} (skipped)')
                return None
            if attempt == 2 or (isinstance(error, HTTPError) and error.code < 500):
                raise OSError(f'{url}: {error}') from error
            report('RETRY', f"{url.rsplit('/', 1)[-1]} (attempt {attempt + 2}/3; {error})")
            sleep(attempt + 1)
        else:
            report('LOADED', url.rsplit('/', 1)[-1])
            return content


# [FUNCTION] Read JP CSVs online and local text.ini/CSV translation targets.
def load_gamefiles(args):
    # JP stays in memory; only existing local targets can be written.
    japanese, targets = {}, {}
    print_stage('Loading JP game files from the network')
    urls = {name: PSO2CSV_url + (csv_reboot_jp_url if reboot else csv_jp_url) + name + '.csv'
            for name, (reboot, _) in rules.source_files.items()}
    with web_pages(urls.values(), get_web, print_status) as pages:
        for name, (reboot, cn_path) in rules.source_files.items():
            url = urls[name]
            content = pages[url]()
            japanese[name] = GameFile.from_bytes(content or b'', url)
            if content is None:
                continue
            if japanese[name].ambiguous:
                raise ValueError(f'{url}: duplicate JP text IDs')
            if not japanese[name].pairs:
                raise ValueError(f'{url}: JP gamefile contains no entries')
            if args.lang == 'CN':
                known = [text for _, text in japanese[name].pairs]
                if name == 'ui_item':
                    known += [strip_ring_name(text) for key, text in japanese[name].pairs
                              if key.startswith('ring_') and key.endswith('#1')]
                path = args.cn_root / cn_path
                kind = 'ini'
            else:
                csv_root = args.csv_ngs if reboot else args.csv_classic
                path = csv_root / rules.csv_path(name, args.lang)
                kind, known = 'csv', ()
            try:
                targets[name] = GameFile(path, kind, known, name == 'item_series_name' and kind == 'ini')
            except FileNotFoundError:
                print_status('FAILED', f'File does not exist: {path} (skipped)')
    return japanese, targets


# [FUNCTION] Load working JSON or an explicitly configured local Git revision.
def load_json(args):
    filenames = sorted({name for names in rules.get_json_paths(args.lang, forward=False).values() for name in names})
    if args.json_ref:
        repository = args.json_dir.parent
        try:
            commit = subprocess.check_output(
                ['git', '-C', str(repository), 'rev-parse', '--verify', args.json_ref + '^{commit}'],
                stderr=subprocess.PIPE, text=True).strip()
            source_bytes = {}
            for name in filenames:
                source = f'{commit}:{args.json_dir.name}/{name}'
                existing = subprocess.run(['git', '-C', str(repository), 'cat-file', '-e', source],
                                          capture_output=True)
                if existing.returncode:
                    print_status('FAILED', f'File does not exist: {source} (skipped)')
                    continue
                source_bytes[name] = subprocess.check_output(
                    ['git', '-C', str(repository), 'show', source], stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as error:
            message = error.stderr.decode('utf-8', errors='replace') if isinstance(error.stderr, bytes) else error.stderr
            raise ValueError(f'Cannot read JSON from {repository} at {args.json_ref}: {message.strip()}') from error
        print_status('JSON', f'{args.json_dir} @ {commit}')
        return {name: json.loads(data) for name, data in source_bytes.items()}, {}
    source_bytes = {}
    for name in filenames:
        path = (args.json_dir / name).resolve()
        try:
            source_bytes[path] = path.read_bytes()
        except FileNotFoundError:
            print_status('FAILED', f'File does not exist: {path} (skipped)')
    print_status('JSON', args.json_dir)
    return {path.name: json.loads(data) for path, data in source_bytes.items()}, source_bytes


# [FUNCTION] Print a changed key and its old/new value under the file summary.
def print_change(change):
    old = json.dumps(change['old'], ensure_ascii=False)
    new = json.dumps(change['new'], ensure_ascii=False)
    print_status('CHANGED', f"[{change['key']}] {old} → {new}")


# [FUNCTION] Show conflicting translations and support counts without a long JSON source list.
def print_conflict(change, japanese):
    entry = japanese.entries.get(change['key'])
    jp_text = entry.text if entry else change['key'].removeprefix(';')
    print_status('CONFLICT', f"[{change['key']}] {json.dumps(jp_text, ensure_ascii=False)} (left unchanged)")
    for candidate in change['candidates']:
        value = json.dumps(candidate['value'], ensure_ascii=False)
        print_status('OPTION', f"{value} (JSON items: {len(candidate['items'])})")


# [FUNCTION] Summarize normal exclusions and show only problems that need attention.
def report_skipped(summary):
    reasons = summary['reasons']
    normal_reasons = {'outside_forward_scope', 'no_translated_name', 'no_reversible_series_structure',
                      'noninvertible_special_name', 'no_candidate'}
    skipped = sum(reasons.get(reason, 0) for reason in normal_reasons)
    if skipped:
        print_status('SKIPPED', f'{skipped} JSON items outside scope or without a reversible translation')
    problems = {
        'target_file_missing': 'local gamefile does not exist',
        'missing_language_dictionary': 'no dictionary translation in the selected language JSON',
        'green_note_conflicts_with_name': 'name and green-note translations disagree',
        'invalid_card_structure': 'invalid card name format',
        'invalid_card_element': 'unknown card element',
        'japanese_source_missing': 'JP text not found',
        'translated_name_does_not_fit_template': 'translated name does not match the expected format',
        'target_key_missing_or_ambiguous': 'local gamefile key missing or duplicated',
        'empty_translation_value': 'translated component is empty',
        'invalid_ring_structure': 'invalid ring name format',
        'ring_skill_source_not_unique': 'ring skill does not have a unique JP match',
        'japanese_voice_source_missing': 'JP voice not found',
        'voice_cv_missing_or_wrapped': 'voice CV missing or split across lines',
        'voice_translation_not_uniquely_recoverable': 'voice translation cannot be uniquely recovered',
        'series_decomposition_ambiguous_or_inconsistent': 'series translation cannot be uniquely recovered',
    }
    for reason, count in sorted(reasons.items()):
        if reason not in normal_reasons and reason != 'conflicting_translation_or_dependency':
            print_status('CAUTION', f'{count} JSON items: {problems.get(reason, reason)} (left unchanged)')


# [FUNCTION] Process every translation, skipping the final writes only in debug mode.
def run(args):
    if args.debug:
        print_status('DEBUG', 'Log only; target files will not be written')
    files, source_bytes = load_json(args)
    japanese, targets = load_gamefiles(args)
    generator = ReverseGenerator(args.lang, japanese, targets)
    result = generator.add_items(files)
    # Render every file and check all inputs before starting the first write.
    rendered = {name: target.render(generator.replacements.get(name, {}))
                for name, target in targets.items()}
    for path, data in source_bytes.items():
        if path.read_bytes() != data:
            raise ValueError(f'JSON changed during generation: {path}')
    for target in targets.values():
        if target.path.read_bytes() != target.original:
            raise ValueError(f'Gamefile changed during generation: {target.path}')
    print_stage('Updating local gamefiles')
    for name, target in targets.items():
        changes = sorted((change for change in result['targets'] if change['source'] == name),
                         key=lambda change: change['line'])
        updated = rendered[name] != target.original
        if not args.debug:
            target.write(rendered[name])
        changed = [change for change in changes if change['status'] == 'changed']
        print()
        print_status('UPDATED' if updated else 'UNCHANGED', f'{len(changed):>5} changed  {target.path.name}')
        for change in changed:
            print_change(change)
        for change in changes:
            if change['status'] == 'conflict':
                print_conflict(change, japanese[name])
    return result


# [FUNCTION] Offer optional command-line overrides for the settings at the top of this file.
def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument('--debug', action='store_true', help='Print normal logs without writing target files')
    result.add_argument('--lang', choices=rules.lang_names[1:], help='Override the current branch language')
    result.add_argument('--json-dir', type=Path, help='Override the current working JSON source')
    result.add_argument('--cn-root', type=Path, default=PSO2CN_path, help='Override the local CN checkout')
    result.add_argument('--csv-classic', '--en-classic', type=Path, default=PSO2CSV_path,
                        help='Override the local Arks-Layer classic CSV checkout')
    result.add_argument('--csv-ngs', '--en-ngs', type=Path, default=PSO2CSV_reboot_path,
                        help='Override the local Arks-Layer Reboot CSV checkout')
    return result


# [FUNCTION] Apply the language, input and command-line debug options.
def parse_arguments(argv=None):
    arguments = parser()
    args = arguments.parse_args(argv)
    try:
        args.lang = rules.resolve_language(args.lang if args.lang is not None else LANG, project_dir)
    except ValueError as error:
        arguments.error(str(error))
    args.json_ref = json_ref if args.json_dir is None else None
    args.json_dir = args.json_dir or jsonfile_dir
    return args


# ——————————————————————————————
# MAIN PROCESS
# ——————————————————————————————

# [FUNCTION] Run the selected language and print file-grouped changes and completion counts.
def main():
    args = parse_arguments()
    print_stage(f'TicketToGamefile ({args.lang}; online JP, local gamefiles)')
    if args.lang != 'CN':
        print_status('GAMEFILE', args.csv_classic)
        print_status('GAMEFILE', args.csv_ngs)
    else:
        print_status('GAMEFILE', args.cn_root)
    try:
        result = run(args)
    except (OSError, ValueError) as error:
        raise SystemExit(f'FAILED: {error}') from error
    print_stage('TicketToGamefile results')
    summary = result['summary']
    print_status('DONE', f"{summary['targets'].get('changed', 0)} values changed; "
                 f"{summary['targets'].get('conflict', 0)} targets skipped due to conflicts")
    report_skipped(summary)


if __name__ == '__main__':
    main()
