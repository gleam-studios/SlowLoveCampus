#!/usr/bin/env python3
"""RunningHub MiniMax H3 AI App v2: jobs.json -> concurrent tasks -> saved outputs.

用法：
  python3 rh_minimax_h3.py jobs.json --output DIR [--dry-run] [--max-wait 秒]
  python3 rh_minimax_h3.py --resume TASKID --output DIR [--name 名字]   # 只查询/下载，不提交，不扣费

防重复扣费：提交前先把最终请求（不含 Key）写进 <name>_submitting.json；
提交结果不明（超时/断线/无 taskId）时标 SUBMIT_UNKNOWN，不自动重提，
同名任务只要还处在 SUBMITTING / SUBMIT_UNKNOWN / SUBMITTED 就拒绝再次提交。
"""
import argparse
import copy
import json
import math
import os
import re
import shutil
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlsplit

import requests

APP_ID = '2101232638873858050'
SUPPORTED_APP_IDS = {APP_ID}
BASE = os.getenv('RUNNINGHUB_BASE_URL', 'https://www.runninghub.ai').rstrip('/')
MAX_CONCURRENT = 3
POLL_SECONDS = float(os.getenv('RH_POLL_SECONDS', '15'))
DEFAULT_MAX_WAIT = 2400
SUBMIT_TIMEOUT = (15, float(os.getenv('RH_SUBMIT_READ_TIMEOUT', '90')))
VIDEO_EXT = {'mp4', 'mov', 'webm'}
ALLOWED_EXT = VIDEO_EXT | {'png', 'jpg', 'jpeg', 'webp', 'zip', 'mp3', 'wav', 'txt'}
OPEN_STATES = {'SUBMITTING', 'SUBMIT_UNKNOWN', 'SUBMITTED'}


from credentials import configured_api_key

API_KEY = configured_api_key()
HALT = threading.Event()  # 有任务等待超时仍在远端运行时置位，不再启动新的提交


def checked_json(response):
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise RuntimeError('API 返回的 JSON 不是对象')
    if data.get('code') not in (None, 0, 200, '0', '200'):
        raise RuntimeError(f"API code={data.get('code')}: {data.get('message') or data.get('msg')}")
    if data.get('errorCode') not in (None, '', 0, '0') and data.get('status') not in ('FAILED', 'CANCEL', 'CANCELLED'):
        raise RuntimeError(f"errorCode={data.get('errorCode')}: {data.get('errorMessage')}")
    return data


def headers():
    return {'Authorization': f'Bearer {API_KEY}'}


def post_json(path, body, timeout=(15, 90)):
    response = requests.post(BASE + path, headers={**headers(), 'Content-Type': 'application/json'},
                             json=body, timeout=timeout)
    return checked_json(response)


def redact(value):
    if isinstance(value, str):
        return value.replace(API_KEY, '[REDACTED]') if API_KEY else value
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        return {redact(k): redact(v) for k, v in value.items()}
    return value


def save_json(path, data):
    def relative_file(value):
        return Path(os.path.relpath(value, Path(__file__).resolve().parents[3])).as_posix() if Path(value).is_absolute() else value
    # Only these fields contain local file references. Prompts and remote responses are opaque.
    portable = dict(data)
    portable['path_base'] = 'project'
    for field in ('files', 'videos'):
        if field in portable:
            portable[field] = [relative_file(value) for value in portable[field]]
    if 'uploads' in portable:
        portable['uploads'] = {relative_file(key): value for key, value in portable['uploads'].items()}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(redact(portable), ensure_ascii=False, indent=2), encoding='utf-8')


def safe_name(value):
    return re.sub(r'[^\w-]+', '_', str(value or 'video')).strip('_') or 'video'


# ---------- 校验 ----------

def is_placeholder(value):
    return isinstance(value, str) and (value.startswith(('（填', '(填')) or
        bool(re.search(r'<(?:真实|填)[^<>]*>', value)))


def validate_jobs(jobs):
    """只做结构校验；节点是否真实、时长/像素是否合法仍须由 Agent 对照真实节点映射确认。"""
    problems = []
    names = set()
    for index, job in enumerate(jobs, 1):
        label = f"任务{index}({job.get('name') if isinstance(job, dict) else '?'})"
        if not isinstance(job, dict):
            problems.append(f'{label}: 不是对象')
            continue
        name = safe_name(job.get('name'))
        if name in names:
            problems.append(f'{label}: name 重复（{name}），回执文件会互相覆盖')
        names.add(name)
        if not isinstance(job.get('appId'), str) or job.get('appId') not in SUPPORTED_APP_IDS:
            problems.append(f'{label}: 须显式指定当前应用 appId；旧应用 jobs 不能直接提交')
        nodes = job.get('nodeInfoList')
        if isinstance(nodes, list):
            pixels = [n.get('fieldValue') for n in nodes if isinstance(n, dict)
                      and str(n.get('nodeId')) == '462' and n.get('fieldName') == 'megapixels']
            if len(pixels) == 1:
                try:
                    mp = float(pixels[0])
                    if not math.isfinite(mp) or mp <= 0:
                        problems.append(f'{label}: MP 须为有限正数')
                    elif mp >= 2 and job.get('instanceType', 'plus') != 'ultra':
                        problems.append(f'{label}: 2 MP 或以上须使用 Ultra')
                except (TypeError, ValueError):
                    problems.append(f'{label}: MP 不是有效数值')
        if not isinstance(nodes, list) or not nodes:
            problems.append(f'{label}: 缺少 nodeInfoList')
            continue
        for node in nodes:
            if not isinstance(node, dict) or not all(k in node for k in ('nodeId', 'fieldName', 'fieldValue')):
                problems.append(f'{label}: 有节点缺 nodeId/fieldName/fieldValue')
                continue
            for key in ('nodeId', 'fieldName'):
                if not str(node[key]).strip() or '<' in str(node[key]) or is_placeholder(str(node[key])):
                    problems.append(f'{label}: {key} 是占位符或为空：{node[key]!r}，须换成真实节点')
            if is_placeholder(node['fieldValue']):
                problems.append(f'{label}: fieldValue 是占位符：{node["fieldValue"]!r}')
            value = node['fieldValue']
            if isinstance(value, dict) and set(value) == {'$upload'}:
                p = Path(str(value['$upload'])).expanduser()
                if not p.is_file():
                    problems.append(f'{label}: 素材不存在：{p}')
                elif p.stat().st_size > 30 * 1024 * 1024:
                    problems.append(f'{label}: 素材超过 30MB：{p}')
    return problems


def summarize_jobs(jobs):
    lines = [f'共 {len(jobs)} 个任务，最多同时 {MAX_CONCURRENT} 个在途']
    for job in jobs:
        uploads = len({str(Path(str(n['fieldValue']['$upload'])).expanduser().resolve())
                       for n in job['nodeInfoList']
                       if isinstance(n.get('fieldValue'), dict) and set(n['fieldValue']) == {'$upload'}})
        lines.append(f"- {safe_name(job.get('name'))}: appId={job.get('appId')}，节点 {len(job['nodeInfoList'])} 个，"
                     f"待上传素材 {uploads} 个，instanceType={job.get('instanceType', 'plus')}")
    lines.append('时长、像素档位、费用须对照真实节点映射与平台计价确认；dry-run 不校验这些。')
    return '\n'.join(lines)


# ---------- 上传与准备 ----------

def upload_local(path):
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise FileNotFoundError(f'素材不存在：{p}')
    if p.stat().st_size > 30 * 1024 * 1024:
        raise ValueError(f'单文件超过 30MB，请先压缩或按节点要求使用外链：{p}')
    with p.open('rb') as handle:
        response = requests.post(BASE + '/openapi/v2/media/upload/binary', headers=headers(),
                                 files={'file': (p.name, handle)}, timeout=(20, 240))
    data = checked_json(response).get('data') or {}
    name = data.get('fileName') or data.get('filename')
    if not name:
        raise RuntimeError(f'上传未返回 fileName/filename：{p.name}')
    return name


def prepare_jobs(jobs):
    cache = {}
    ready = []
    for job in jobs:
        nodes = copy.deepcopy(job['nodeInfoList'])
        uploads = {}
        for node in nodes:
            value = node['fieldValue']
            if isinstance(value, dict) and set(value) == {'$upload'}:
                path = str(Path(value['$upload']).expanduser().resolve())
                if path not in cache:
                    print('上传素材:', Path(path).name, flush=True)
                    cache[path] = upload_local(path)
                node['fieldValue'] = cache[path]
                uploads[path] = cache[path]
        ready.append({**job, 'nodeInfoList': nodes, '_uploads': uploads})
    return ready


# ---------- 输出验收 ----------

def looks_like_video(path, ext):
    with path.open('rb') as handle:
        head = handle.read(16)
    if ext in {'mp4', 'mov'}:
        return len(head) >= 12 and head[4:8] == b'ftyp'
    if ext == 'webm':
        return head[:4] == b'\x1a\x45\xdf\xa3'
    return False


def probe_video(path):
    """返回 (ok, info)。有 ffprobe 时核对视频流；没有时只做魔数检查并标明未解码。"""
    ext = path.suffix.lower().lstrip('.')
    if path.stat().st_size == 0:
        return False, {'error': '文件为空'}
    if not looks_like_video(path, ext):
        return False, {'error': '文件头不是视频容器'}
    if not shutil.which('ffprobe'):
        return True, {'probe': '未验证（本机没有 ffprobe，仅检查了文件头）'}
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
         'stream=width,height,codec_name,r_frame_rate:format=duration', '-of', 'json', str(path)],
        capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        return False, {'error': 'ffprobe 无法解析：' + result.stderr.strip()[:200]}
    try:
        info = json.loads(result.stdout)
        stream = (info.get('streams') or [{}])[0]
        duration = float((info.get('format') or {}).get('duration') or 0)
    except (ValueError, IndexError):
        return False, {'error': 'ffprobe 输出无法解析'}
    if not stream.get('width') or duration <= 0:
        return False, {'error': '没有视频流或时长为 0'}
    return True, {'width': stream['width'], 'height': stream['height'], 'codec': stream.get('codec_name'),
                  'duration': round(duration, 3), 'fps': stream.get('r_frame_rate')}


def download_outputs(task_id, name, results, out):
    """下载所有输出；返回 (全部文件, 通过验收的视频, 验收记录)。"""
    files, videos, checks = [], [], {}
    for index, result in enumerate(results, 1):
        url = result.get('url')
        if not isinstance(url, str) or not url.startswith(('https://', 'http://')):
            continue
        ext = str(result.get('outputType') or '').lower().lstrip('.')
        if ext not in ALLOWED_EXT:
            ext = Path(urlsplit(url).path).suffix.lower().lstrip('.')
        if ext not in ALLOWED_EXT:
            ext = 'bin'
        dst = out / f'{name}_{task_id}_{index}.{ext}'
        temp = Path(str(dst) + '.part')
        with requests.get(url, stream=True, timeout=(20, 240)) as response:
            response.raise_for_status()
            if 'text/html' in response.headers.get('Content-Type', '').lower():
                raise RuntimeError('输出链接返回 HTML，可能已经过期')
            with temp.open('wb') as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
        temp.replace(dst)
        files.append(str(dst))
        if ext in VIDEO_EXT:
            ok, info = probe_video(dst)
            checks[dst.name] = {'ok': ok, **info}
            if ok:
                videos.append(str(dst))
        else:
            checks[dst.name] = {'ok': dst.stat().st_size > 0, 'note': '非视频输出，不计入成功判定',
                                'bytes': dst.stat().st_size}
    return files, videos, checks


# ---------- 任务流程 ----------

class RemoteTaskFailed(RuntimeError):
    pass

def poll_until_done(task_id, name, out, receipt, max_wait):
    """轮询到终态。返回 query 的 JSON；超时抛 TimeoutError（任务仍在远端运行，名额不释放给新提交）。"""
    deadline = time.monotonic() + max_wait
    while True:
        status_json = post_json('/openapi/v2/query', {'taskId': task_id})
        status = str(status_json.get('status') or '').upper()
        save_json(receipt, {'taskId': task_id, 'status': status, 'name': name,
                            'usage': status_json.get('usage'), 'response': status_json})
        if status == 'SUCCESS':
            return status_json
        if status in {'FAILED', 'CANCEL', 'CANCELLED'}:
            raise RemoteTaskFailed(f'任务结束：{name}, {task_id}, {status}, {redact(status_json.get("errorMessage"))}')
        if time.monotonic() >= deadline:
            HALT.set()
            raise TimeoutError(f'等待超过 {int(max_wait)} 秒，任务仍可能在远端运行，不要重复提交；'
                               f'用 --resume {task_id} 继续查询')
        time.sleep(POLL_SECONDS)


def finish_task(task_id, name, out, status_json, receipt):
    results = status_json.get('results') or []
    files, videos, checks = download_outputs(task_id, name, results, out)
    save_json(receipt, {'taskId': task_id, 'status': 'SUCCESS', 'name': name, 'usage': status_json.get('usage'),
                        'response': status_json, 'files': files, 'videos': videos, 'checks': checks})
    if not videos:
        raise RuntimeError(f'任务返回 SUCCESS 但没有通过验收的视频输出，taskId={task_id}，验收见 {receipt.name}')
    print(f'已完成：{name} -> {videos}', flush=True)
    return videos


def run_one(job, out, max_wait):
    name = safe_name(job.get('name'))
    app_id = job['appId']
    pending = out / f'{name}_submitting.json'
    if HALT.is_set():
        raise RuntimeError(f'{name}: 未提交，因为已有任务等待超时仍在远端运行（避免超出并发额度）')
    if pending.is_file():
        try:
            previous = json.loads(pending.read_text(encoding='utf-8'))
        except ValueError:
            previous = {'status': 'SUBMIT_UNKNOWN'}
        if previous.get('status') in OPEN_STATES:
            raise RuntimeError(
                f'{name}: 已有未结束的同名提交（{previous.get("status")} taskId={previous.get("taskId")}），'
                f'拒绝重复提交；有 taskId 用 --resume，没有就先去平台核对任务/消费记录，再删 {pending.name}')
    payload = {'nodeInfoList': job['nodeInfoList'], 'instanceType': job.get('instanceType', 'plus')}
    for optional in ('usePersonalQueue',):
        if optional in job:
            payload[optional] = job[optional]
    record = {'name': name, 'status': 'SUBMITTING', 'payload': payload, 'uploads': job.get('_uploads', {}),
              'appId': app_id, 'savedAt': time.strftime('%Y-%m-%d %H:%M:%S')}
    save_json(pending, record)  # 先落盘再提交（不含 Key）
    try:
        submitted = post_json('/openapi/v2/run/ai-app/' + app_id, payload, timeout=SUBMIT_TIMEOUT)
    except Exception as error:
        record.update(status='SUBMIT_UNKNOWN', error=str(error)[:300])
        save_json(pending, record)
        HALT.set()
        raise RuntimeError(f'{name}: 提交结果不明（{type(error).__name__}），远端可能已建任务并扣费，已停止自动重提。'
                           f'请到 RunningHub 任务/消费记录核对；详情见 {pending.name}') from error
    task_id = submitted.get('taskId')
    if not task_id:
        record.update(status='SUBMIT_UNKNOWN', error='响应里没有 taskId', response=submitted)
        save_json(pending, record)
        HALT.set()
        raise RuntimeError(f'{name}: 未返回 taskId，按"结果不明"处理，不自动重提：{submitted}')
    task_id = str(task_id)
    record.update(status='SUBMITTED', taskId=task_id)
    save_json(pending, record)
    receipt = out / f'{name}_{task_id}.json'
    save_json(receipt, {'taskId': task_id, 'status': submitted.get('status'), 'name': name})
    print(f'已提交：{name} / taskId={task_id}', flush=True)
    try:
        status_json = poll_until_done(task_id, name, out, receipt, max_wait)
    except TimeoutError:
        raise
    except RemoteTaskFailed:
        record.update(status='FAILED')
        save_json(pending, record)
        raise
    except Exception:
        # A query transport error does not prove that the remote job failed.
        HALT.set()
        raise
    try:
        return finish_task(task_id, name, out, status_json, receipt)
    finally:
        record.update(status='DONE')
        save_json(pending, record)


def resume_task(task_id, name, out, max_wait):
    name = safe_name(name or 'resume')
    receipt = out / f'{name}_{task_id}.json'
    status_json = poll_until_done(task_id, name, out, receipt, max_wait)
    files = finish_task(task_id, name, out, status_json, receipt)
    pending = out / f'{name}_submitting.json'
    if pending.is_file():
        record = json.loads(pending.read_text(encoding='utf-8'))
        if str(record.get('taskId')) == str(task_id):
            record.update(status='DONE')
            save_json(pending, record)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('jobs_json', nargs='?', help='包含 jobs 数组的 JSON 文件')
    parser.add_argument('--output', required=True, help='当前任务输出目录，必须显式指定')
    parser.add_argument('--dry-run', action='store_true', help='只校验并打印摘要，不上传、不提交')
    parser.add_argument('--resume', metavar='TASKID', help='只查询并下载已有 taskId，不提交')
    parser.add_argument('--name', help='配合 --resume 指定输出文件名前缀')
    parser.add_argument('--max-wait', type=float, default=DEFAULT_MAX_WAIT,
                        help='单任务最长等待秒数，超时不代表远端已停止')
    args = parser.parse_args()
    out = Path(args.output).expanduser().resolve()

    if args.resume:
        if not API_KEY:
            parser.error('先使用 credentials.py set 保存 RunningHub Key，或设置 RUNNINGHUB_API_KEY')
        out.mkdir(parents=True, exist_ok=True)
        resume_task(args.resume, args.name, out, args.max_wait)
        return

    if not args.jobs_json:
        parser.error('需要 jobs_json，或使用 --resume TASKID')
    jobs_file = Path(args.jobs_json).resolve()
    data = json.loads(jobs_file.read_text(encoding='utf-8'))
    jobs = data.get('jobs')
    if not isinstance(jobs, list) or not jobs:
        parser.error('jobs_json 须包含非空 jobs 数组')
    if data.get('path_base') == 'jobs_file':
        for job in jobs:
            if not isinstance(job, dict):
                continue
            for node in job.get('nodeInfoList', []):
                value = node.get('fieldValue') if isinstance(node, dict) else None
                if isinstance(value, dict) and set(value) == {'$upload'}:
                    ref = Path(str(value['$upload']))
                    if ref.is_absolute():
                        parser.error('新 jobs 的素材须为相对路径；请重新构造 jobs，不沿用其他电脑路径。')
                    value['$upload'] = str((jobs_file.parent / ref).resolve())
    elif data.get('path_base') is not None:
        parser.error('无法识别 jobs 的 path_base')
    problems = validate_jobs(jobs)
    if problems:
        raise SystemExit('提交前检查未通过：\n- ' + '\n- '.join(problems))
    if args.dry_run:
        print(summarize_jobs(jobs))
        print('dry-run 通过：未上传、未提交。')
        return
    if not API_KEY:
        parser.error('先使用 credentials.py set 保存 RunningHub Key，或设置 RUNNINGHUB_API_KEY')
    out.mkdir(parents=True, exist_ok=True)
    prepared = prepare_jobs(jobs)
    failures = []
    with ThreadPoolExecutor(max_workers=min(MAX_CONCURRENT, len(prepared))) as pool:
        futures = {pool.submit(run_one, job, out, args.max_wait): job.get('name') for job in prepared}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as error:
                failures.append((futures[future], redact(str(error))))
                print('任务异常：', futures[future], redact(str(error)), flush=True)
    if failures:
        raise SystemExit('有任务未成功，请查看任务 JSON：' + str(failures))


if __name__ == '__main__':
    main()
