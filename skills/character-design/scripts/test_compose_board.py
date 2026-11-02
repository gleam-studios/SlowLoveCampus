#!/usr/bin/env python3
"""Synthetic image tests; no image-generation service calls or user images."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image

spec = importlib.util.spec_from_file_location('compose_board', Path(__file__).with_name('compose_board.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class BoardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = self.root / 'layout.json'
        self.output = self.root / 'board.png'

    def fixture(self, style='realistic', source_size=(40, 80), size=(300, 400)):
        roles = module.HEADS + module.BODIES + (['body_right'] if style == 'aaa' else []) + ['half']
        panels = []
        for i, role in enumerate(roles):
            color = (20 + i * 20, 30, 120)
            Image.new('RGB', source_size, color).save(self.root / f'{role}.png')
            panels.append({'role': role, 'source': f'{role}.png'})
        return {'style': style, 'output_size': list(size), 'panels': panels}

    def run_board(self, config):
        self.config.write_text(json.dumps(config))
        return module.compose(self.config, self.output)

    def test_default_4k_and_role_order(self):
        config = self.fixture(size=(3072, 4096))
        config['panels'].reverse()  # placement follows roles, not incidental input order
        receipt = self.run_board(config)
        self.assertEqual(next(p['source'] for p in receipt['panels'] if p['role'] == 'head_front'), 'head_front.png')
        with Image.open(self.output) as image:
            self.assertEqual(image.size, (3072, 4096))
            for panel in receipt['panels']:
                x, y, w, h = panel['placed']
                role = panel['role']
                with Image.open(self.root / f'{role}.png') as source:
                    self.assertEqual(image.getpixel((x + w // 2, y + h // 2)), source.getpixel((0, 0)))
        self.assertEqual(receipt['output_size'], [3072, 4096])
        self.assertTrue(self.output.with_suffix('.png.json').is_file())

    def test_fit_preserves_ratio_and_edges(self):
        config = self.fixture(source_size=(200, 100))
        source = self.root / 'half.png'
        image = Image.open(source)
        image.putpixel((0, 0), (255, 0, 0)); image.putpixel((199, 99), (0, 255, 0)); image.save(source)
        receipt = self.run_board(config)
        p = next(p for p in receipt['panels'] if p['role'] == 'half')
        self.assertEqual(p['placed'][2:], [120, 60])
        self.assertEqual(p['scale'], .6)
        self.assertEqual(p['crop'], [0, 0, 200, 100])

    def test_aaa_requires_four_bodies(self):
        receipt = self.run_board(self.fixture('aaa'))
        self.assertEqual(len(receipt['panels']), 9)
        self.output.unlink(); self.output.with_suffix('.png.json').unlink()
        config = self.fixture('aaa'); config['panels'] = config['panels'][:-2] + config['panels'][-1:]
        with self.assertRaises(ValueError): self.run_board(config)
        self.assertFalse(self.output.exists())

    def test_missing_duplicate_or_unknown_roles(self):
        for operation in ['missing', 'duplicate', 'unknown']:
            config = self.fixture()
            if operation == 'missing': config['panels'].pop()
            if operation == 'duplicate': config['panels'].append(config['panels'][0])
            if operation == 'unknown': config['panels'][0]['role'] = 'someone_else'
            with self.assertRaises(ValueError): self.run_board(config)
            self.assertFalse(self.output.exists())

    def test_crop_known_sheet_and_alpha(self):
        config = self.fixture()
        sheet = Image.new('RGBA', (100, 80), (0, 0, 0, 0))
        sheet.paste((220, 15, 50, 255), (60, 0, 100, 80)); sheet.save(self.root / 'sheet.png')
        config['panels'][0].update(source='sheet.png', crop=[60, 0, 40, 80])
        receipt = self.run_board(config)
        panel = receipt['panels'][0]; x, y, _, _ = panel['placed']
        with Image.open(self.output) as image:self.assertEqual(image.getpixel((x, y)), (220, 15, 50))

    def test_no_upscale_by_default(self):
        receipt = self.run_board(self.fixture(source_size=(10, 20)))
        self.assertTrue(receipt['warnings'])
        self.assertTrue(all(p['scale'] == 1 for p in receipt['panels']))

    def test_allowed_upscale_is_recorded(self):
        config = self.fixture(source_size=(10, 20)); config['allow_upscale'] = True
        receipt = self.run_board(config)
        self.assertTrue(any(p['scale'] > 1 for p in receipt['panels']))
        self.assertTrue(any('upscaled' in w for w in receipt['warnings']))

    def test_invalid_crop_and_layout_fail_without_outputs(self):
        for operation in ['crop', 'bounds', 'overlap', 'partial']:
            config = self.fixture()
            if operation == 'crop': config['panels'][0]['crop'] = [0, 0, 999, 80]
            if operation == 'partial': config['panels'][0]['box'] = [0, 0, 10, 10]
            if operation in ['bounds', 'overlap']:
                for p in config['panels']:p['box'] = [0, 0, 10, 10]
                if operation == 'bounds':config['panels'][0]['box'] = [299, 0, 10, 10]
            with self.assertRaises(ValueError): self.run_board(config)
            self.assertFalse(self.output.exists())

    def test_custom_layout_reproduces_placement(self):
        config = self.fixture()
        boxes = module.default_boxes(300, 400, module.BODIES)
        for p in config['panels']:p['box'] = boxes[p['role']]
        receipt = self.run_board(config)
        self.assertEqual({p['role']:p['box'] for p in receipt['panels']}, boxes)

    def test_existing_output_or_receipt_never_overwritten(self):
        config = self.fixture()
        for path in [self.output, self.output.with_suffix('.png.json')]:
            path.write_bytes(b'KEEP')
            with self.assertRaises(FileExistsError):self.run_board(config)
            self.assertEqual(path.read_bytes(), b'KEEP')
            path.unlink()


if __name__ == '__main__':
    unittest.main()
