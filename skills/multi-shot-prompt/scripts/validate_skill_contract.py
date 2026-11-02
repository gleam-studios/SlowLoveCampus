#!/usr/bin/env python3
"""Validate prompt syntax, reference bindings, timelines and dialogue pairing.

Default: check packaged resources and simulated positive/negative fixtures.
--prompt FILE: additionally validate a generated prompt, or use with
--prompt-only to check only those files. No live video quality is inferred.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_HEADINGS = ['视频梗概', '影片质感', '素材锁定', '分镜']
REQUIRED_SHOT_FIELDS = ['视频内容', '拍摄手法', '光影执行', '声音', '台词', '结束落点']
REQUIRED_FILM_FIELDS = ['影像风格', '摄影偏好', '材质与氛围', '光影与色彩']
RETIRED_SHOT_FIELDS = ['画面起点', '动作过程']
IMAGE_EXT = r'(?:png|jpg|jpeg|webp|gif|avif|heic)'
AUDIO_EXT = r'(?:mp3|wav|m4a|ogg|flac|aac)'
ASSET_RE = re.compile(
    r'@([^@\r\n：,，。;；！？!?（）()“”\[\]`]+?\.'
    + r'(?:png|jpg|jpeg|webp|gif|avif|heic|mp3|wav|m4a|ogg|flac|aac|mp4|mov))'
    + r'(?=$|[^A-Za-z0-9])', re.I)
VOICE_RE = re.compile(r'@([^@\r\n：,，。;；（）()“”]+?\.' + AUDIO_EXT + r')', re.I)
SHOT_RE = re.compile(r'^镜头(\d{2})｜(\d+)—(\d+)秒[ \t]*$', re.M)
TIME_RE = re.compile(r'^[ \t]*(\d+(?:\.\d+)?)\s*[—–-]\s*(\d+(?:\.\d+)?)秒：[ \t]*', re.M)
FIELD_RE = re.compile(r'^(' + '|'.join(REQUIRED_SHOT_FIELDS + RETIRED_SHOT_FIELDS) + r')：[ \t]*', re.M)
SPEECH_RE = re.compile(
    r'(?P<speaker>[^\r\n：，。；！？“”（）]+?)说'
    r'(?:（@(?P<voice>[^@（）\r\n]+?\.' + AUDIO_EXT + r')）)?'
    r'：“(?P<words>[^\r\n”]+)”', re.I)


def parse_entities(block: str) -> dict[str, str]:
    """Material entries occupy one line; retain their original names verbatim."""
    return {m.group(1).strip(): m.group(2).strip()
            for m in re.finditer(r'^([^：\r\n]+)：([^\r\n]*)$', block, re.M)}


def check_prompt(text: str, name: str = 'prompt') -> list[str]:
    """Return explicit structural errors; not a semantic or live-video review."""
    issues: list[str] = []

    def issue(message: str) -> None:
        issues.append(f'{name}: {message}')

    # Accept a delivered txt fence; ignore example metadata before the prompt.
    text = re.sub(r'^```(?:txt|text|markdown|md)?[^\r\n]*\n?', '', text, flags=re.M)
    headings = list(re.finditer(r'^# (视频梗概|影片质感|素材锁定|分镜)[ \t]*$', text, re.M))
    if [m.group(1) for m in headings] != REQUIRED_HEADINGS:
        issue('heading order incorrect')
        return issues
    blocks = {m.group(1): text[m.end():headings[i+1].start() if i+1 < len(headings) else len(text)]
              for i, m in enumerate(headings)}
    for key, block in blocks.items():
        if not block.strip():
            issue(f'empty section: {key}')

    film_lines = [line.strip() for line in blocks['影片质感'].splitlines() if line.strip()]
    film = [re.fullmatch(r'(影像风格|摄影偏好|材质与氛围|光影与色彩)：(.*)', line) for line in film_lines]
    if len(film) != 4 or any(m is None for m in film):
        issue('film texture must contain exactly four labeled nonempty fields')
    else:
        if [m.group(1) for m in film] != REQUIRED_FILM_FIELDS:
            issue('film texture fields out of order')
        if any(not m.group(2).strip() for m in film):
            issue('film texture field empty')

    material = blocks['素材锁定']
    categories = list(re.finditer(r'^(场景|角色|道具)：[ \t]*$', material, re.M))
    if [m.group(1) for m in categories] != ['场景', '角色', '道具']:
        issue('material lock must contain 场景/角色/道具 in exact order')
        return issues
    groups = {m.group(1): material[m.end():categories[i+1].start() if i+1 < len(categories) else len(material)]
              for i, m in enumerate(categories)}
    scenes, roles, props = (parse_entities(groups[k]) for k in ['场景', '角色', '道具'])
    role_voices = {speaker: set(VOICE_RE.findall(description)) for speaker, description in roles.items()}
    allowed_assets = {key[1:] for key in (*roles, *props) if key.startswith('@')}
    allowed_assets.update(voice for voices in role_voices.values() for voice in voices)
    storyboard = blocks['分镜']
    for scene in scenes:
        if scene.startswith('@') and scene in storyboard:
            issue(f'background scene reference leaked into storyboard: {scene}')
    for asset in sorted(set(ASSET_RE.findall(storyboard)) - allowed_assets):
        issue(f'unregistered storyboard asset: @{asset}')

    # Prefer known character identifiers, including original filenames with spaces.
    # Generic image identifiers also detect unregistered speaking characters.
    generic_image = r'@[^@\r\n：，。；！？“”（）]+?\.' + IMAGE_EXT
    speaker_pattern = '(?:' + '|'.join([re.escape(s) for s in sorted(roles, key=len, reverse=True)] + [generic_image]) + ')'
    speech_start = re.compile(speaker_pattern + r'说(?=（|：|:|[ \t]*[“"])', re.I)
    inline_speech = re.compile(
        r'(?P<speaker>' + speaker_pattern + r')说'
        r'(?:（@(?P<voice>[^@（）\r\n]+?\.' + AUDIO_EXT + r')）)?'
        r'：“(?P<words>[^\r\n”]+)”', re.I)

    def validate_speech(match: re.Match[str], serial: int) -> None:
        speaker, voice, words = match.group('speaker', 'voice', 'words')
        if speaker not in roles:
            issue(f'shot {serial} unregistered speaking character: {speaker}')
        elif voice and voice not in role_voices[speaker]:
            issue(f'shot {serial} voice does not belong to {speaker}: @{voice}')
        elif not voice and role_voices[speaker]:
            issue(f'shot {serial} missing bound voice for {speaker}')
        if not words.strip():
            issue(f'shot {serial} empty spoken words')

    shots = list(SHOT_RE.finditer(storyboard))
    if not shots:
        issue(f'shot count out of range: {len(shots)}')
        return issues
    if len(re.findall(r'^镜头\d+', storyboard, re.M)) != len(shots):
        issue('invalid shot time header')
    previous_end = 0
    for i, shot in enumerate(shots):
        serial, start, end = map(int, shot.groups())
        if serial != i + 1:
            issue(f'shot serial gap at {serial}')
        if start != previous_end or end <= start:
            issue(f'invalid shot timeline at {serial}: {start}-{end} after {previous_end}')
        previous_end = end
        body = storyboard[shot.end():shots[i+1].start() if i+1 < len(shots) else len(storyboard)]
        matches = list(FIELD_RE.finditer(body))
        labels = [m.group(1) for m in matches]
        if labels != REQUIRED_SHOT_FIELDS:
            issue(f'shot {serial} field contract incorrect: {labels}')
        fields = {m.group(1): body[m.end():matches[j+1].start() if j+1 < len(matches) else len(body)].strip()
                  for j, m in enumerate(matches)}
        for field in REQUIRED_SHOT_FIELDS:
            if not fields.get(field):
                issue(f'shot {serial} empty or missing {field}')
        video = fields.get('视频内容', '')
        time_segments = list(TIME_RE.finditer(video))
        if not time_segments:
            issue(f'shot {serial} video timeline missing')
        else:
            if video[:time_segments[0].start()].strip():
                issue(f'shot {serial} video timeline has untimed opening content')
            segment_end = Decimal(start)
            for j, segment in enumerate(time_segments):
                a, b = map(Decimal, segment.groups())
                if a != segment_end or b <= a or a < start or b > end:
                    issue(f'shot {serial} video timeline invalid segment {a}-{b}')
                segment_end = b
                event = video[segment.end():time_segments[j+1].start() if j+1 < len(time_segments) else len(video)]
                if not event.strip():
                    issue(f'shot {serial} video timeline empty segment')
            if segment_end != end:
                issue(f'shot {serial} video timeline does not cover shot end')

        spoken_in_video: list[str] = []
        for opening in speech_start.finditer(video):
            utterance = inline_speech.match(video, opening.start())
            if utterance is None:
                issue(f'shot {serial} malformed timeline speech; use complete quoted dialogue')
            else:
                spoken_in_video.append(utterance.group(0))
                validate_speech(utterance, serial)

        dialogue = fields.get('台词', '')
        dialogue_matches = [m for m in matches if m.group(1) == '台词']
        if len(dialogue_matches) != 1:
            issue(f'shot {serial} needs exactly one dialogue field')
        elif dialogue != '无':
            first_line = body[dialogue_matches[0].end():].split('\n', 1)[0].strip()
            if first_line:
                issue(f'shot {serial} put spoken lines below the dialogue label')
        indexed: list[str] = []
        if dialogue == '无':
            indexed = []
        elif dialogue:
            for line in dialogue.splitlines():
                if not line.strip():
                    continue
                utterance = SPEECH_RE.fullmatch(line.strip())
                if utterance is None:
                    issue(f'shot {serial} malformed dialogue index; use complete quoted dialogue')
                else:
                    indexed.append(utterance.group(0))
                    validate_speech(utterance, serial)
        if spoken_in_video != indexed:
            issue(f'shot {serial} timeline/dialogue mismatch: speaker, voice, words, quotes, order or count')

    if previous_end > 30:
        issue('total duration exceeds 30 seconds')
    if len(blocks['分镜']) > 5000:
        issue('storyboard exceeds 5000 characters')
    for section in ['影片质感', '素材锁定']:
        if len(blocks[section]) > 1000:
            issue(f'{section} exceeds 1000 characters')
    return issues


def check_package() -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    source = (ROOT/'SKILL.md').read_text(encoding='utf-8')
    if not source.startswith('---\nname: multi-shot-prompt\n'):
        errors.append('SKILL.md frontmatter name mismatch')
    paths = set(re.findall(r'`((?:templates|references|checklists|examples|agents|evals|scripts)/[^`\s]+)`', source))
    for path in sorted(paths):
        if not ((ROOT/path).is_dir() if path.endswith('/') else (ROOT/path).is_file()):
            errors.append(f'missing referenced resource: {path}')
    managed = json.loads((ROOT/'templates/managed_input_template.json').read_text(encoding='utf-8'))
    if managed.get('execution_mode') != 'managed_mode' or managed.get('approval', {}).get('authority') != 'master-director-agent':
        errors.append('managed template contract invalid')
    manifest = (ROOT/'templates/execution_manifest_template.md').read_text(encoding='utf-8')
    if 'prompt_order: [video_summary, film_texture, material_lock, storyboard]' not in manifest:
        errors.append('execution manifest prompt order incorrect')
    for rel in ['templates/material_lock_template.md', 'references/material_lock_rules.md', 'references/reference_asset_roles.md', 'checklists/material_lock_qc.md']:
        text = (ROOT/rel).read_text(encoding='utf-8')
        if not all(token in text for token in ['@', '场景', '角色', '道具']):
            errors.append(f'asset classification contract missing: {rel}')
    for path in ROOT.rglob('*.md'):
        text = path.read_text(encoding='utf-8')
        if re.search(r'@\[[^\]]+\]', text):
            errors.append(f'obsolete semantic handle: {path.relative_to(ROOT)}')
        if any(label in text for label in RETIRED_SHOT_FIELDS):
            errors.append(f'noncanonical shot field in authoring resource: {path.relative_to(ROOT)}')
    for rel in ['SKILL.md', 'templates/storyboard_module_template.md', 'references/storyboard_module_rules.md', 'checklists/storyboard_module_qc.md']:
        text = (ROOT/rel).read_text(encoding='utf-8')
        if not all(word in text for word in ['视频内容', '台词', '：“']):
            errors.append(f'timeline/dialogue contract missing: {rel}')
    if 'Not-tested: live video generation' not in (ROOT/'evals/live_generation_ledger.md').read_text(encoding='utf-8'):
        errors.append('live test status marker missing')

    positives = {rel: (ROOT/rel).read_text(encoding='utf-8') for rel in [
        'examples/product_ad_10s.md',
        'examples/rainy_bus_stop_20s_mock.md',
    ]}
    fixture = positives['examples/rainy_bus_stop_20s_mock.md']
    def count_fixture(count: int) -> str:
        prefix = positives['examples/product_ad_10s.md'].split('# 分镜\n', 1)[0]
        return prefix + '# 分镜\n' + '\n'.join(
            f'镜头{i+1:02d}｜{i}—{i+1}秒\n视频内容：\n'
            f'{i}—{i+1}秒：暖灰棚内纸筒居中，花瓣落下。\n'
            '拍摄手法：固定近景。\n光影执行：柔光稳定。\n'
            '声音：气流声。\n台词：无\n结束落点：纸筒居中。\n'
            for i in range(count))

    positives['ten shots within duration limit'] = count_fixture(10)
    positives['thirty shots at duration limit'] = count_fixture(30)
    a = '@人物A.png说（@人物A音色.mp3）：“你真的不和我一起走吗？”'
    b = '@人物B.png说（@人物B音色.mp3）：“我送你到这里就好。”'
    short_a = '@人物A.png说（@人物A音色.mp3）：“一起走吗？”'
    short_b = '@人物B.png说（@人物B音色.mp3）：“不了。”'
    multi = fixture.replace(a, short_a + '\n' + short_b)
    no_voice = fixture.replace('音色参考：@人物A音色.mp3，轻柔偏低、语速较慢。', '').replace('（@人物A音色.mp3）', '')
    named_role = no_voice.replace('@人物A.png', '女子')
    positives.update({
        'no voice reference': no_voice,
        'named role without image': named_role,
        'decimal inner timeline': fixture.replace('0—2秒：', '0—1.5秒：', 1).replace('2—4秒：', '1.5—4秒：', 1),
        'two speakers in one shot': multi,
        'same utterance twice': fixture.replace(a, a + '\n' + a),
        'filenames preserve spaces': fixture.replace('人物A.png', '人物 A.png').replace('人物A音色.mp3', '人物 A 音色.mp3'),
        'one interval per shot': fixture.replace('0—2秒：', '0—4秒：', 1).replace('\n2—4秒：', '', 1),
    })
    for label, prompt in positives.items():
        errors.extend(check_prompt(prompt, label))

    # Each mutation must change its baseline and trigger the intended error class.
    negatives: list[tuple[str, str, str, str]] = []
    def bad(label: str, malformed: str, expected: str, baseline: str = fixture) -> None:
        negatives.append((label, malformed, expected, baseline))

    bad('thirty-one seconds', count_fixture(31), 'total duration exceeds 30 seconds', count_fixture(30))
    bad('no shots', count_fixture(0), 'shot count', count_fixture(10))
    bad('wrong visible order', fixture.replace('# 影片质感\n', '# TEMP\n', 1).replace('# 素材锁定\n', '# 影片质感\n', 1).replace('# TEMP\n', '# 素材锁定\n', 1), 'heading order')
    bad('scene ref in shot', fixture.replace('0—2秒：公交站顶棚下', '0—2秒：@雨夜公交站.png公交站顶棚下', 1), 'background scene reference')
    bad('missing speech field', fixture.replace('台词：无\n', '', 1), 'dialogue field')
    bad('unknown voice', fixture.replace('（@人物A音色.mp3）', '（@陌生人音色.mp3）'), 'voice does not belong')
    bad('wrong registered voice', fixture.replace('（@人物A音色.mp3）', '（@人物B音色.mp3）'), 'voice does not belong')
    bad('omitted bound voice', fixture.replace('（@人物A音色.mp3）', ''), 'missing bound voice')
    bad('film texture collapsed', re.sub(r'(# 影片质感\n).*?(?=\n# 素材锁定)', r'\1写实都市电影，雨夜自然光线。', fixture, count=1, flags=re.S), 'film texture')
    bad('film texture missing field', re.sub(r'^材质与氛围：[^\n]*\n', '', fixture, count=1, flags=re.M), 'film texture')
    bad('film texture empty field', re.sub(r'^光影与色彩：[^\n]*', '光影与色彩：', fixture, count=1, flags=re.M), 'film texture')
    bad('film texture field order', fixture.replace('影像风格：', 'TEMP：', 1).replace('摄影偏好：', '影像风格：', 1).replace('TEMP：', '摄影偏好：', 1), 'film texture fields out of order')
    bad('split initial and action fields', fixture.replace('视频内容：\n', '画面起点：初始画面。\n动作过程：\n', 1), 'field contract')
    bad('empty video content', re.sub(r'视频内容：\n.*?(?=拍摄手法：)', '视频内容：\n', fixture, count=1, flags=re.S), 'empty or missing 视频内容')
    bad('untimed paragraph', fixture.replace('0—2秒：', '', 1).replace('2—4秒：', '', 1), 'video timeline missing')
    bad('inner timeline reset', fixture.replace('4—6秒：', '0—2秒：', 1), 'video timeline invalid')
    bad('inner timeline gap', fixture.replace('2—4秒：', '3—4秒：', 1), 'video timeline invalid')
    bad('inner timeline overlap', fixture.replace('2—4秒：', '1—4秒：', 1), 'video timeline invalid')
    bad('inner timeline reversed', fixture.replace('2—4秒：', '3—2秒：', 1), 'video timeline invalid')
    bad('inner timeline incomplete', fixture.replace('2—4秒：', '2—3秒：', 1), 'does not cover shot end')
    bad('empty timed interval', re.sub(r'0—2秒：[^\n]+', '0—2秒：', fixture, count=1), 'empty segment')
    unquoted = a.replace('：“', '：').replace('”', '')
    bad('timeline quotes missing', fixture.replace(a, unquoted, 1), 'malformed timeline speech')
    bad('index quotes missing', fixture.replace('台词：\n' + a, '台词：\n' + unquoted, 1), 'malformed dialogue index')
    bad('straight quotes', fixture.replace(a, a.replace('“', '"').replace('”', '"')), 'malformed')
    bad('dialogue only in index', fixture.replace(a, '女子抬眼等待。', 1), 'timeline/dialogue mismatch')
    bad('dialogue only in timeline', fixture.replace('台词：\n' + a, '台词：无', 1), 'timeline/dialogue mismatch')
    bad('different text in index', fixture.replace('台词：\n' + a, '台词：\n' + a.replace('不和我', '要和我'), 1), 'timeline/dialogue mismatch')
    bad('different speaker in index', fixture.replace('台词：\n' + a, '台词：\n' + b, 1), 'timeline/dialogue mismatch')
    bad('duplicate index utterance', fixture.replace('台词：\n' + a, '台词：\n' + a + '\n' + a, 1), 'timeline/dialogue mismatch')
    bad('reordered index', multi.replace('台词：\n' + short_a + '\n' + short_b, '台词：\n' + short_b + '\n' + short_a, 1), 'timeline/dialogue mismatch', multi)
    bad('inline dialogue label', fixture.replace('台词：\n' + a, '台词：' + a, 1), 'below the dialogue label')
    bad('empty spoken words', fixture.replace(a, a.replace('你真的不和我一起走吗？', ' ')), 'empty spoken words')
    bad('unknown prop', fixture.replace('手持收拢的 @红色雨伞.png', '手持收拢的 @紫色雨伞.png', 1), 'unregistered storyboard asset')
    bad('shot time gap', fixture.replace('镜头02｜4—8秒', '镜头02｜5—8秒', 1), 'invalid shot timeline')
    for label, malformed, expected, baseline in negatives:
        if malformed == baseline:
            errors.append(f'negative test was not mutated: {label}')
            continue
        detected = check_prompt(malformed, label)
        if not any(expected in error for error in detected):
            errors.append(f'negative test missed {expected}: {label}; got {detected}')
    return errors, {'resource_paths': len(paths), 'positive_cases': len(positives), 'negative_cases': len(negatives)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prompt', type=Path, action='append', default=[], help='Validate a UTF-8 prompt file; repeatable.')
    parser.add_argument('--prompt-only', action='store_true', help='Skip packaged self-tests; requires --prompt.')
    parser.add_argument('--json', action='store_true', help='Print a JSON report.')
    args = parser.parse_args()
    if args.prompt_only and not args.prompt:
        parser.error('--prompt-only requires --prompt')
    errors: list[str] = []
    stats: dict[str, int] = {}
    try:
        if not args.prompt_only:
            errors, stats = check_package()
        for path in args.prompt:
            errors.extend(check_prompt(path.read_text(encoding='utf-8'), str(path)))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f'cannot read validation input: {exc}')
    report = {
        'status': 'PASS' if not errors else 'FAIL',
        'scope': 'Text structure, timeline boundaries, asset bindings and dialogue equality only',
        'live_generation': 'Not-tested: live video generation',
        **stats,
        'prompt_files': len(args.prompt),
        'errors': errors,
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        if (ROOT/'SKILL.md').is_file():
            print('SKILL.md sha256:', hashlib.sha256((ROOT/'SKILL.md').read_bytes()).hexdigest())
        for key, value in stats.items():
            print(f'{key}: {value}')
        for error in errors:
            print('ERROR:', error)
        print(report['status'])
        print(report['live_generation'])
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
