#!/usr/bin/env python3
"""Local credential storage; never prints the value or executes env-file content."""
import argparse
import getpass
import os
import stat
import tempfile
import csv
import re
import subprocess
from pathlib import Path


def config_path():
    return Path(os.getenv('RUNNINGHUB_ENV_FILE') or
                '~/.config/rh-minimax-h3/.env').expanduser()


def read_key(path):
    path = Path(path).expanduser()
    if not path.is_file():
        return ''
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line.startswith('export '):
            line = line[7:].strip()
        if '=' not in line or line.startswith('#'):
            continue
        name, value = line.split('=', 1)
        if name.strip() == 'RUNNINGHUB_API_KEY':
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in '\"\'':
                value = value[1:-1]
            return value.strip()
    return ''


def configured_api_key():
    return os.getenv('RUNNINGHUB_API_KEY', '').strip() or read_key(config_path())


def restrict_file(fd, path):
    if os.name != 'nt':
        os.fchmod(fd, 0o600)
        return
    # Windows chmod is not a private ACL. Restrict the empty file before writing a Key.
    identity = subprocess.run(['whoami', '/user', '/fo', 'csv', '/nh'],
                              capture_output=True, text=True, encoding='utf-8', errors='replace', check=True, timeout=15)
    rows = list(csv.reader(identity.stdout.splitlines()))
    sid = rows[0][-1].strip() if rows else ''
    if not re.fullmatch(r'S-1-\d+(?:-\d+)+', sid):
        raise RuntimeError('无法识别当前 Windows 用户 SID，未保存凭据')
    subprocess.run(['icacls', str(path), '/inheritance:r', '/grant:r', '*' + sid + ':(F)'],
                   capture_output=True, check=True, timeout=15)


def store_key(key, destination, replace=False):
    key = key.strip()
    if not key or any(c.isspace() for c in key):
        raise ValueError('Key 不能为空或包含空白字符')
    destination = Path(destination).expanduser().absolute()
    if destination.is_symlink() or destination.parent.is_symlink():
        raise ValueError('凭据位置不能是软链接')
    if destination.exists() and not replace:
        raise ValueError('配置已存在；明确要替换时使用 --replace')
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name != 'nt' and destination == Path.home() / '.config/rh-minimax-h3/.env':
        destination.parent.chmod(0o700)
    fd, tmp = tempfile.mkstemp(prefix='.credential-', dir=destination.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            restrict_file(stream.fileno(), tmp)
            stream.write('RUNNINGHUB_API_KEY=' + key + '\n')
        os.replace(tmp, destination)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('set', 'import-env', 'status'))
    parser.add_argument('--from-env', type=Path, help='import-env 的源配置路径')
    parser.add_argument('--env-file', type=Path, help='保存/检查位置；默认本机私有配置')
    parser.add_argument('--replace', action='store_true', help='明确替换已有配置')
    args = parser.parse_args()
    destination = args.env_file or config_path()
    if args.action == 'status':
        key = (read_key(destination) if args.env_file else configured_api_key())
        source = ('环境变量' if not args.env_file and os.getenv('RUNNINGHUB_API_KEY', '').strip()
                  else str(destination.expanduser()))
        print(('已配置' if key else '未配置') + '；来源：' + source + '；未联网验证')
        if destination.is_file() and os.name != 'nt':
            mode = stat.S_IMODE(destination.stat().st_mode)
            print(f'配置权限：{mode:04o}')
            if mode & 0o077:
                print('配置可被其他本机用户读取，请将该文件权限设为 0600')
        return
    try:
        if args.action == 'import-env':
            if not args.from_env:
                parser.error('import-env 需要 --from-env')
            key = read_key(args.from_env)
        else:
            key = getpass.getpass('RunningHub API Key（输入隐藏）：')
        saved = store_key(key, destination, args.replace)
    except (OSError, ValueError, RuntimeError, EOFError, subprocess.SubprocessError):
        parser.exit(1, '保存失败：检查源配置、目标权限和是否需要 --replace；未输出密钥。\n')
    protection = '当前用户私有 ACL' if os.name == 'nt' else '0600'
    print('已安全保存：' + str(saved) + '（' + protection + '，未联网验证）')


if __name__ == '__main__':
    main()
