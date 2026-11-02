#!/usr/bin/env python3
"""Offline behavior tests; private configuration isolated in temporary directories."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('credentials', ROOT/'scripts/credentials.py')
credentials = importlib.util.module_from_spec(spec)
spec.loader.exec_module(credentials)


class Helpers(unittest.TestCase):
    def test_secret_storage_and_priority(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)/'private/.env'
            key = 'offline-secret-12345'
            credentials.store_key(key, dest)
            self.assertEqual(dest.stat().st_mode & 0o777, 0o600)
            self.assertEqual(credentials.read_key(dest), key)
            with self.assertRaises(ValueError):
                credentials.store_key('replacement', dest)
            env = {**os.environ, 'RUNNINGHUB_ENV_FILE': str(dest), 'RUNNINGHUB_API_KEY': ''}
            result = subprocess.run([sys.executable, str(ROOT/'scripts/credentials.py'), 'status'],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertIn('已配置', result.stdout)
            self.assertNotIn(key, result.stdout + result.stderr)
            with patch.dict(os.environ, env):
                self.assertEqual(credentials.configured_api_key(), key)
                os.environ['RUNNINGHUB_API_KEY'] = 'override'
                self.assertEqual(credentials.configured_api_key(), 'override')
            source = Path(tmp)/'project.env'
            source.write_text('OTHER=untouched\nexport RUNNINGHUB_API_KEY="import-secret"\n')
            result = subprocess.run([sys.executable, str(ROOT/'scripts/credentials.py'),
                                     'import-env', '--from-env', str(source),
                                     '--env-file', str(dest), '--replace'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(credentials.read_key(dest), 'import-secret')
            self.assertIn('OTHER=untouched', source.read_text())
            self.assertNotIn('import-secret', result.stdout + result.stderr)

    def test_selected_app_defaults_and_reference_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            prompt = tmp/'prompt.txt'; prompt.write_text('test prompt', encoding='utf-8')
            images = [tmp/f'image{i}.png' for i in range(4)]
            audios = [tmp/f'voice{i}.wav' for i in range(2)]
            for f in images + audios: f.write_bytes(b'fixture')
            output = tmp/'job.json'
            cmd = [sys.executable, str(ROOT/'scripts/build_jobs.py'), '--prompt-file', str(prompt),
                   '--seconds', '15', '--aspect', '16:9', '--output', str(output)]
            for f in images: cmd += ['--image', str(f)]
            for f in audios: cmd += ['--audio', str(f)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            job = json.loads(output.read_text())['jobs'][0]
            nodes = {(str(n['nodeId']), n['fieldName']): n['fieldValue'] for n in job['nodeInfoList']}
            self.assertEqual(job['appId'], '2101232638873858050')
            self.assertEqual(job['instanceType'], 'plus')
            for node, file in zip(('438','435','437','439'), images):
                self.assertEqual(nodes[(node,'image')], {'$upload': file.name})
            for node in ('431','429'):
                self.assertEqual(nodes[(node,'image')], {'$upload': images[-1].name})
            for node, file in zip(('841','842'), audios):
                self.assertEqual(nodes[(node,'audio')], {'$upload': file.name})
            for key, value in [(('456','text'),'test prompt'),(('462','megapixels'),'1.0'),
                               (('804','value'),'15'),(('827','value'),'4'),(('881','value'),'true'),
                               (('824','value'),'false'),(('816','text'),'dynv2,r34l1sm')]:
                self.assertEqual(nodes[key], value)
            expected=[('813','MysticXXX_MMH3-V5.1.safetensors',0.4),
                      ('817','Minimax-H3-Digicam-Realism Improve Lora.safetensors',0.5),
                      ('815','h3-realism-people-t2v-i2v-r2v_new.safetensors',0.5),
                      ('888','H3电影感V2.safetensors',0.5)]
            for node,name,strength in expected:
                self.assertEqual(nodes[(node,'lora_name')],name)
                self.assertEqual(float(nodes[(node,'strength_model')]),strength)
            dry = subprocess.run([sys.executable, str(ROOT/'scripts/rh_minimax_h3.py'), str(output),
                                  '--dry-run', '--output', str(tmp/'out')], capture_output=True, text=True)
            self.assertEqual(dry.returncode, 0, dry.stderr)
            self.assertIn('待上传素材 6 个', dry.stdout)
            self.assertFalse((tmp/'out').exists())

    def test_quality_and_controls(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp); prompt = tmp/'p.txt'; prompt.write_text('test')
            image = tmp/'img.png'; image.write_bytes(b'fixture')
            base = [sys.executable, str(ROOT/'scripts/build_jobs.py'), '--prompt-file', str(prompt),
                    '--seconds', '15', '--aspect', '16:9', '--image', str(image)]
            def run(extra, filename):
                return subprocess.run(base + extra + ['--output', str(tmp/filename)], capture_output=True, text=True)
            for quality, mp, instance in [('480P',0.5,'plus'),('720P',1.0,'plus'),('1080P',2.0,'ultra')]:
                name=quality+'.json';r=run(['--quality',quality],name);self.assertEqual(r.returncode,0,r.stderr)
                job=json.loads((tmp/name).read_text())['jobs'][0];nodes={(str(n['nodeId']),n['fieldName']):n['fieldValue'] for n in job['nodeInfoList']}
                self.assertEqual(float(nodes[('462','megapixels')]),mp);self.assertEqual(job['instanceType'],instance)
            self.assertNotEqual(run(['--seconds','16'], 'bad-length.json').returncode, 0)
            self.assertNotEqual(run(['--quality','1080P','--instance','plus'], 'bad-instance.json').returncode, 0)
            self.assertNotEqual(run(['--audio',str(image),'--audio',str(image),'--audio',str(image)], 'too-many-audio.json').returncode, 0)
            r=run(['--output-format','zip','--lora-4-strength','0','--lora-trigger','custom','--version-switch','false'],'custom.json')
            self.assertEqual(r.returncode,0,r.stderr)
            n={(str(x['nodeId']),x['fieldName']):x['fieldValue'] for x in json.loads((tmp/'custom.json').read_text())['jobs'][0]['nodeInfoList']}
            self.assertEqual(n[('824','value')],'true');self.assertEqual(n[('881','value')],'false')
            self.assertEqual(float(n[('888','strength_model')]),0);self.assertEqual(n[('816','text')],'custom')

    def test_reject_other_app_and_high_resolution_on_plus(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp)
            jobs=[{'name':'old','appId':'2084320751339032577','nodeInfoList':[{'nodeId':'150','fieldName':'value','fieldValue':'x'}]},
                  {'name':'noid','nodeInfoList':[{'nodeId':'456','fieldName':'text','fieldValue':'x'}]},
                  {'name':'bad','appId':'2101232638873858050','instanceType':'plus','nodeInfoList':[{'nodeId':'462','fieldName':'megapixels','fieldValue':'2'}]}]
            for index,job in enumerate(jobs):
                file=tmp/f'{index}.json';file.write_text(json.dumps({'jobs':[job]}))
                dry=subprocess.run([sys.executable,str(ROOT/'scripts/rh_minimax_h3.py'),str(file),'--dry-run','--output',str(tmp/'out')],capture_output=True,text=True)
                self.assertNotEqual(dry.returncode,0)
                self.assertFalse((tmp/'out').exists())


if __name__ == '__main__':
    unittest.main()
