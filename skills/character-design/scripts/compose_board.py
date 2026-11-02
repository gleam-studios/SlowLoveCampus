#!/usr/bin/env python3
"""Join three complete reference images without crops or added gaps. Requires Pillow."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys

from PIL import Image, ImageColor, ImageOps

HEADS = ['head_front', 'head_45', 'head_side', 'head_back']
BODIES = ['body_front', 'body_side', 'body_back']


def ints(value, count, label):
    if not isinstance(value, list) or len(value) != count or any(type(n) is not int for n in value):
        raise ValueError(f'{label} must be {count} integers')
    return value


def rect(value, size, label):
    x, y, w, h = ints(value, 4, label)
    if min(x, y) < 0 or min(w, h) <= 0 or x + w > size[0] or y + h > size[1]:
        raise ValueError(f'{label} is outside {size}')
    return x, y, w, h


def default_boxes(width, height, bodies):
    top = round(height * .28)
    split = round(width * .60)
    boxes = {}
    for i, role in enumerate(HEADS):
        x, right = round(width * i / 4), round(width * (i + 1) / 4)
        boxes[role] = [x, 0, right - x, top]
    for i, role in enumerate(bodies):
        x, right = round(split * i / len(bodies)), round(split * (i + 1) / len(bodies))
        boxes[role] = [x, top, right - x, height - top]
    boxes['half'] = [split, top, width - split, height - top]
    return boxes


def compose_panels(config_path: Path, output: Path):
    config_path, output = config_path.resolve(), output.resolve()
    receipt_path = output.with_suffix(output.suffix + '.json')
    if output.suffix.lower() != '.png':
        raise ValueError('Output must be PNG')
    if output.exists() or receipt_path.exists():
        raise FileExistsError('Output or receipt exists; choose a new version')
    config = json.loads(config_path.read_text(encoding='utf-8'))
    style = config.get('style')
    if style not in {'realistic', 'cg', 'aaa'}:
        raise ValueError('style must be realistic, cg or aaa')
    width, height = ints(config.get('output_size', [3072, 4096]), 2, 'output_size')
    if min(width, height) < 4 or width * height > 100_000_000:
        raise ValueError('Unsupported canvas size')
    upscale = config.get('allow_upscale', False)
    if type(upscale) is not bool:
        raise ValueError('allow_upscale must be boolean')
    background = ImageColor.getcolor(config.get('background', '#ffffff'), 'RGB')
    bodies = BODIES + (['body_right'] if style == 'aaa' else [])
    roles = HEADS + bodies + ['half']
    panels = config.get('panels')
    if not isinstance(panels, list) or any(not isinstance(p, dict) for p in panels):
        raise ValueError('panels must be a list of objects')
    names = [p.get('role') for p in panels]
    if any(not isinstance(n, str) for n in names) or len(names) != len(set(names)) or set(names) != set(roles):
        raise ValueError(f'Provide exactly one of each role: {roles}')
    boxes = default_boxes(width, height, bodies)
    explicit = ['box' in p for p in panels]
    if any(explicit) and not all(explicit):
        raise ValueError('Custom layouts must specify box for every panel')
    prepared, receipts, warnings = [], [], []
    for panel in panels:
        role = panel['role']
        source = Path(panel['source'])
        source = (config_path.parent / source).resolve() if not source.is_absolute() else source.resolve()
        if source in {output, receipt_path, config_path}:
            raise ValueError('Output, receipt, config and sources must be distinct')
        box = rect(panel.get('box', boxes[role]), (width, height), f'{role}.box')
        with Image.open(source) as raw:
            image = ImageOps.exif_transpose(raw).convert('RGBA')
        crop = rect(panel.get('crop', [0, 0, *image.size]), image.size, f'{role}.crop')
        x, y, w, h = crop
        image = image.crop((x, y, x + w, y + h))
        scale = min(box[2] / w, box[3] / h)
        if scale > 1 and not upscale:
            scale = 1
            warnings.append(f'{role}: source kept at native size; improve source for more detail')
        if scale > 1:
            warnings.append(f'{role}: upscaled; no new source detail established')
        fitted = (max(1, math.floor(w * scale)), max(1, math.floor(h * scale)))
        image = image.resize(fitted, Image.Resampling.LANCZOS)
        px, py = box[0] + (box[2] - fitted[0]) // 2, box[1] + (box[3] - fitted[1]) // 2
        prepared.append((image, (px, py), box))
        receipts.append({'role': role, 'source': Path(os.path.relpath(source, receipt_path.parent)).as_posix(), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                         'crop': list(crop), 'box': list(box), 'placed': [px, py, *fitted], 'scale': scale})
    for i, (_, _, a) in enumerate(prepared):
        for _, _, b in prepared[i + 1:]:
            if max(a[0], b[0]) < min(a[0] + a[2], b[0] + b[2]) and max(a[1], b[1]) < min(a[1] + a[3], b[1] + b[3]):
                raise ValueError('Panel boxes overlap')
    canvas = Image.new('RGB', (width, height), background)
    for image, pos, _ in prepared:
        canvas.paste(image, pos, image)
    receipt = {'path_base': 'receipt_file', 'style': style, 'output_size': [width, height], 'allow_upscale': upscale,
               'panels': receipts, 'warnings': warnings, 'review': 'composition only; identity and artistic review not performed'}
    # Reserve both new files exclusively; a failure cleans up only files created by this invocation.
    created = []
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open('xb') as stream:
            created.append(output)
            canvas.save(stream, format='PNG')
        with receipt_path.open('x', encoding='utf-8') as stream:
            created.append(receipt_path)
            json.dump(receipt, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    except BaseException:
        for path in created:
            path.unlink(missing_ok=True)
        raise
    return receipt



def compose_whole(config_path: Path, output: Path, config):
    """Concatenate half+body at equal height, then head above at equal width."""
    config_path, output = config_path.resolve(), output.resolve()
    receipt_path = output.with_suffix(output.suffix + '.json')
    if output.exists() or receipt_path.exists():
        raise FileExistsError('Output or receipt exists; choose a new version')
    if output.suffix.lower() != '.png':
        raise ValueError('Output must be PNG')
    unsupported = set(config) - {'style', 'head', 'half', 'body', 'output_width', 'background'}
    if unsupported:
        raise ValueError(f'Unsupported whole-image configuration fields: {sorted(unsupported)}')
    style = config.get('style', 'realistic')
    if style not in {'realistic', 'cg', 'aaa'}:
        raise ValueError('style must be realistic, cg or aaa')
    background = ImageColor.getcolor(config.get('background', '#ffffff'), 'RGB')
    images, sources, warnings, seen = {}, {}, [], set()
    ratios = {'head': 16 / 9, 'half': 3 / 4, 'body': 9 / 16}
    for role in ['head', 'half', 'body']:
        if role not in config or not isinstance(config[role], str):
            raise ValueError('Provide three complete images: head, half, body')
        source = Path(config[role])
        source = (config_path.parent / source).resolve() if not source.is_absolute() else source.resolve()
        if source in seen or source in {output, receipt_path, config_path}:
            raise ValueError('The three source images and output/config files must be distinct')
        seen.add(source)
        with Image.open(source) as raw:
            images[role] = ImageOps.exif_transpose(raw).convert('RGBA')
        w, h = images[role].size
        if abs((w / h) / ratios[role] - 1) > .03:
            warnings.append(f'{role}: actual aspect ratio {w}:{h} differs from requested source; kept entire image')
        sources[role] = {'source': Path(os.path.relpath(source, receipt_path.parent)).as_posix(), 'source_size': [w, h],
                         'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
    width = config.get('output_width', images['head'].width)
    if type(width) is not int or not 4 <= width <= 16384:
        raise ValueError('output_width must be an integer between 4 and 16384')
    lower_ratio = sum(images[r].width / images[r].height for r in ['half', 'body'])
    lower_h = max(1, round(width / lower_ratio))
    half_w = min(width - 1, max(1, round(width * (images['half'].width / images['half'].height) / lower_ratio)))
    head_h = max(1, round(width * images['head'].height / images['head'].width))
    height = head_h + lower_h
    if width * height > 100_000_000:
        raise ValueError('Unsupported canvas size')
    placements = {'head': [0, 0, width, head_h],
                  'half': [0, head_h, half_w, lower_h],
                  'body': [half_w, head_h, width - half_w, lower_h]}
    canvas = Image.new('RGB', (width, height), background)
    for role, image in images.items():
        x, y, w, h = placements[role]
        scale = [w / image.width, h / image.height]
        if max(scale) > 1:
            warnings.append(f'{role}: resized larger for equal-height/width join; no new source detail established')
        fitted = image if image.size == (w, h) else image.resize((w, h), Image.Resampling.LANCZOS)
        canvas.paste(fitted, (x, y), fitted)
        sources[role].update(placed=placements[role], scale=scale)
    receipt = {'path_base': 'receipt_file', 'layout': 'head-over-half-left-body-right', 'style': style,
               'output_size': [width, height], 'sources': sources, 'warnings': warnings,
               'review': 'whole-image joining only; no cropping or generation; visual review still required'}
    created = []
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open('xb') as stream:
            created.append(output)
            canvas.save(stream, format='PNG')
        with receipt_path.open('x', encoding='utf-8') as stream:
            created.append(receipt_path)
            json.dump(receipt, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    except BaseException:
        for path in created:
            path.unlink(missing_ok=True)
        raise
    return receipt


def compose(config_path: Path, output: Path):
    config = json.loads(config_path.read_text(encoding='utf-8'))
    if not isinstance(config, dict):
        raise ValueError('Configuration must be an object')
    # Retain only explicit old-config compatibility; new workflows always pass three whole images.
    if 'panels' in config and not any(role in config for role in ['head', 'half', 'body']):
        return compose_panels(config_path, output)
    return compose_whole(config_path, output, config)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        receipt = compose(args.config, args.output)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'Composition failed: {exc}', file=sys.stderr)
        return 1
    print(json.dumps({'output': str(args.output.resolve()), 'warnings': receipt['warnings']}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
