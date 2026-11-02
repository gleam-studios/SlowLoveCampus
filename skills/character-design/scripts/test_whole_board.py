#!/usr/bin/env python3
"""Regression checks for the three whole-source-image assembly contract."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image

spec = importlib.util.spec_from_file_location('compose_board', Path(__file__).with_name('compose_board.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class WholeImageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = self.root / 'layout.json'
        self.output = self.root / 'board.png'
        for role, size, color in [('head', (160, 90), 'red'), ('half', (120, 160), 'green'), ('body', (90, 160), 'blue')]:
            Image.new('RGB', size, color).save(self.root / f'{role}.png')

    def fixture(self, **changes):
        return dict({'style': 'realistic', 'head': 'head.png', 'half': 'half.png', 'body': 'body.png', 'output_width': 210}, **changes)

    def run_board(self, config):
        self.config.write_text(json.dumps(config))
        return module.compose(self.config, self.output)

    def test_equal_height_then_equal_width_no_added_gaps(self):
        receipt = self.run_board(self.fixture())
        self.assertEqual(receipt['sources']['head']['source'], 'head.png')
        self.assertEqual(receipt['output_size'], [210, 278])
        with Image.open(self.output) as image:
            self.assertEqual(image.size, (210, 278))
            self.assertEqual(dict((color, count) for count, color in image.getcolors()),
                             {(255, 0, 0): 24780, (0, 128, 0): 19200, (0, 0, 255): 14400})
            self.assertEqual(image.getpixel((119, 118)), (0, 128, 0))
            self.assertEqual(image.getpixel((120, 118)), (0, 0, 255))

    def test_whole_borders_survive_and_sources_unchanged(self):
        before = {}
        for role in ['half', 'body']:
            p = self.root / f'{role}.png'
            with Image.open(p) as image:
                image.putpixel((0, 0), (20, 40, 60));image.putpixel((image.width-1, image.height-1), (60, 40, 20));image.save(p)
            before[role] = p.read_bytes()
        receipt = self.run_board(self.fixture())
        with Image.open(self.output) as image:
            for role, data in before.items():
                x, y, w, h = receipt['sources'][role]['placed']
                self.assertEqual(image.getpixel((x, y)), (20, 40, 60))
                self.assertEqual(image.getpixel((x+w-1, y+h-1)), (60, 40, 20))
                self.assertEqual((self.root/f'{role}.png').read_bytes(), data)
        self.assertTrue(all('crop' not in s for s in receipt['sources'].values()))

    def test_natural_height_not_fixed_canvas(self):
        config = self.fixture();config.pop('output_width')
        receipt = self.run_board(config)
        self.assertEqual(receipt['output_size'], [160, 212])
        self.assertEqual(receipt['sources']['head']['scale'], [1, 1])

    def test_real_source_dimensions_match_photoshop(self):
        for role, size in [('head', (1672, 941)), ('half', (1086, 1448)), ('body', (941, 1672))]:
            Image.new('RGB', size, 'red').save(self.root/f'{role}.png')
        config = self.fixture();config.pop('output_width')
        receipt = self.run_board(config)
        self.assertEqual(receipt['output_size'], [1672, 2215])
        self.assertEqual(receipt['sources']['head']['placed'], [0, 0, 1672, 941])
        with Image.open(self.output) as board, Image.open(self.root/'head.png') as source:
            self.assertEqual(board.crop((0, 0, 1672, 941)).tobytes(), source.tobytes())

    def test_actual_input_ratios(self):
        Image.new('RGB', (180, 90), 'red').save(self.root/'head.png')
        receipt = self.run_board(self.fixture())
        self.assertEqual(receipt['output_size'], [210, 265])
        self.assertTrue(any('aspect ratio' in w for w in receipt['warnings']))

    def test_aaa_uses_one_complete_body_sheet(self):
        receipt = self.run_board(self.fixture(style='aaa'))
        self.assertEqual(set(receipt['sources']), {'head', 'half', 'body'})
        self.assertEqual(receipt['layout'], 'head-over-half-left-body-right')

    def test_mixed_crop_config_rejected(self):
        config = self.fixture();config['panels'] = []
        with self.assertRaisesRegex(ValueError, 'unsupported|Unsupported'):
            self.run_board(config)
        self.assertFalse(self.output.exists())

    def test_invalid_inputs_do_not_write(self):
        for change in [{'body':'missing.png'}, {'body':'half.png'}, {'output_width':0}, {'output_width':True}]:
            with self.assertRaises((OSError, ValueError)):self.run_board(self.fixture(**change))
            self.assertFalse(self.output.exists())

    def test_no_overwrite(self):
        self.output.write_bytes(b'KEEP')
        with self.assertRaises(FileExistsError):self.run_board(self.fixture())
        self.assertEqual(self.output.read_bytes(), b'KEEP')


if __name__ == '__main__':unittest.main()
