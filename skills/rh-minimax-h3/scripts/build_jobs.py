#!/usr/bin/env python3
"""Build a RunningHub MiniMax H3 beginner V2 job from its node snapshot."""
import argparse
import json
import math
import os
from pathlib import Path

MAP = Path(__file__).resolve().parents[1] / 'references/node_map.json'
APP_ID = '2101232638873858050'
ASPECTS = {
    '1:1': '1:1 (Square)', '2:3': '2:3 (Portrait Photo)', '3:2': '3:2 (Photo)',
    '3:4': '3:4 (Portrait Standard)', '4:3': '4:3 (Standard)',
    '9:16': '9:16 (Portrait Widescreen)', '16:9': '16:9 (Widescreen)',
    '21:9': '21:9 (Ultrawide)',
}
QUALITY_MP = {'480P': 0.5, '720P': 1.0, '1080P': 2.0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prompt-file', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--name', default='video')
    parser.add_argument('--seconds', type=int, required=True, help='任务指定时长，5–15 秒')
    parser.add_argument('--aspect', choices=ASPECTS, required=True)
    pixels = parser.add_mutually_exclusive_group()
    pixels.add_argument('--quality', choices=tuple(QUALITY_MP), help='480P→0.5 MP；720P→1 MP；1080P→2 MP')
    pixels.add_argument('--megapixels', type=float, help='任务指定目标 MP，默认 1')
    parser.add_argument('--instance', choices=('default', 'plus', 'ultra'), help='默认 Plus；2 MP 或以上使用 Ultra')
    parser.add_argument('--image', type=Path, action='append', default=[])
    parser.add_argument('--audio', type=Path, action='append', default=[])
    parser.add_argument('--output-format', choices=('video', 'zip'), default='video')
    parser.add_argument('--version-switch', choices=('true', 'false'), help='应用 v1/v2 布尔开关，默认沿用已测示例 true')
    for number in (1, 2, 3, 4):
        parser.add_argument(f'--lora-{number}-name')
        parser.add_argument(f'--lora-{number}-strength', type=float)
    parser.add_argument('--lora-trigger')
    parser.add_argument('--node-map', type=Path)
    args = parser.parse_args()
    if not 5 <= args.seconds <= 15:
        parser.error('时长须为 5–15 秒')
    if not 1 <= len(args.image) <= 6 or len(args.audio) > 2:
        parser.error('须提供 1–6 张参考图，最多 2 段音频；纯文生未验证')
    megapixels = args.megapixels if args.megapixels is not None else QUALITY_MP.get(args.quality or '720P')
    if not math.isfinite(megapixels) or not 0.1 <= megapixels <= 16:
        parser.error('MP 须为 0.1–16 的有限数值；线上实用范围仍需验证')
    if megapixels >= 2 and args.instance and args.instance != 'ultra':
        parser.error('2 MP 或以上须使用 Ultra')
    instance = args.instance or ('ultra' if megapixels >= 2 else 'plus')
    prompt = args.prompt_file.read_text(encoding='utf-8').strip()
    if not prompt:
        parser.error('提示词不能为空')
    mapping = json.loads((args.node_map or MAP).read_text(encoding='utf-8'))
    if mapping.get('appId') != APP_ID:
        parser.error('节点映射的应用 ID 不匹配')
    nodes = [{k: n[k] for k in ('nodeId', 'fieldName', 'fieldValue')}
             for n in mapping['nodeInfoList']]
    by_key = {(str(n['nodeId']), n['fieldName']): n for n in nodes}

    def set_value(node_id, field, value):
        if (node_id, field) not in by_key:
            parser.error('节点映射已变化，须核对当前应用接口后更新构造器')
        by_key[(node_id, field)]['fieldValue'] = str(value)

    def media(node_id, field, path):
        path = path.expanduser().resolve()
        if not path.is_file() or path.stat().st_size > 30 * 1024 * 1024:
            parser.error('素材不存在或超过 30MB：' + str(path))
        if (node_id, field) not in by_key:
            parser.error('素材节点缺失，须核对当前应用接口')
        relative = Path(os.path.relpath(path, args.output.resolve().parent)).as_posix()
        by_key[(node_id, field)]['fieldValue'] = {'$upload': relative}

    for node in nodes:
        if node['fieldName'] in ('image', 'audio'):
            node['fieldValue'] = 'None'
    set_value('456', 'text', prompt)
    set_value('804', 'value', args.seconds)
    set_value('462', 'megapixels', megapixels)
    set_value('462', 'aspect_ratio', ASPECTS[args.aspect])
    set_value('827', 'value', len(args.image))
    set_value('824', 'value', str(args.output_format == 'zip').lower())
    if args.version_switch is not None:
        set_value('881', 'value', args.version_switch)
    image_nodes = ('438', '435', '437', '439', '431', '429')
    for node_id, path in zip(image_nodes, args.image):
        media(node_id, 'image', path)
    # The user's successful V2 task used the last real image for unused sockets.
    for node_id in image_nodes[len(args.image):]:
        media(node_id, 'image', args.image[-1])
    for node_id, path in zip(('841', '842'), args.audio):
        media(node_id, 'audio', path)
    for number, node_id in enumerate(('813', '817', '815', '888'), 1):
        name = getattr(args, f'lora_{number}_name')
        strength = getattr(args, f'lora_{number}_strength')
        if name is not None:
            set_value(node_id, 'lora_name', name)
        if strength is not None:
            if not math.isfinite(strength) or not -100 <= strength <= 100:
                parser.error('LoRA 强度须为 -100–100 的有限数值')
            set_value(node_id, 'strength_model', strength)
    if args.lora_trigger is not None:
        set_value('816', 'text', args.lora_trigger)
    job = {'name': args.name, 'appId': APP_ID, 'instanceType': instance,
           'usePersonalQueue': False, 'nodeInfoList': nodes}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump({'path_base': 'jobs_file', 'mapping_date': mapping.get('snapshot_date'), 'jobs': [job]},
                  stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print('已生成任务配置（未上传、未提交）：' + str(args.output))


if __name__ == '__main__':
    main()
