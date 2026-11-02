"""Read Jianying's actual setting once, then remember it on this computer."""
import configparser
import json
import os
import platform
import re
import tempfile
from pathlib import Path


def cache_path(home=None, system=None, environ=None):
    home = Path(home) if home is not None else Path.home()
    system = system or platform.system()
    env = os.environ if environ is None else environ
    if system == "Darwin":
        base = home / "Library/Application Support"
    elif system == "Windows":
        base = Path(env.get("LOCALAPPDATA") or home / "AppData/Local")
    else:
        raise RuntimeError("剪映草稿定位仅支持 macOS / Windows。")
    return base / "SlowLoveCampus/jianying.json"


def settings_files(home, system, env):
    if system == "Darwin":
        roots = [home / "Movies/JianyingPro/User Data",
                 home / "Library/Application Support/JianyingPro/User Data"]
        for bundle in ("com.lemon.lvpro", "com.bytedance.JianyingPro"):
            container = home / "Library/Containers" / bundle / "Data"
            roots.extend([container / "Movies/JianyingPro/User Data",
                          container / "Library/Application Support/JianyingPro/User Data"])
    elif system == "Windows":
        roots = [Path(env.get("LOCALAPPDATA") or home / "AppData/Local") / "JianyingPro/User Data"]
    else:
        raise RuntimeError("不支持的电脑系统。")
    return [root / "Config/globalSetting" for root in roots]


def configured_root(config):
    raw = config.read_bytes()
    text = raw.decode("utf-16" if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig")
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.read_string(text)
    values = set()
    for section in parser.sections():
        value = parser.get(section, "currentCustomDraftPath", fallback="").strip().strip('"')
        if value:
            # QSettings escapes Windows backslashes and may encode Unicode as \xNNNN.
            value = re.sub(r"\\x([0-9a-fA-F]{1,4})", lambda m: chr(int(m[1], 16)), value)
            values.add(value.replace("\\\\", "\\"))
    if len(values) > 1:
        raise RuntimeError("同一剪映设置中存在多个草稿位置，请核对剪映设置。")
    if not values:
        return None
    path = Path(values.pop()).expanduser()
    if not path.is_absolute():
        raise RuntimeError("剪映设置中的草稿位置不是可识别的本机绝对路径。")
    return path.resolve()


def checked_root(path):
    if not path.is_dir() or not os.access(path, os.R_OK | os.W_OK):
        raise RuntimeError("剪映已配置/记录的草稿目录不存在或不可读写；请核对剪映设置，未创建替代目录。")
    return path


def resolve_drafts_root(home=None, system=None, environ=None, refresh=False):
    home = Path(home) if home is not None else Path.home()
    system = system or platform.system()
    env = os.environ if environ is None else environ
    cache = cache_path(home, system, env)
    if cache.is_file() and not refresh:
        try:
            record = json.loads(cache.read_text(encoding="utf-8"))
            if record.get("version") != 1 or record.get("system") != system:
                raise ValueError("Unsupported local record")
            root = Path(record["drafts_root"])
            if not root.is_absolute():
                raise ValueError("Invalid local record")
            root = checked_root(root)
        except (ValueError, KeyError, OSError) as exc:
            raise RuntimeError("本机草稿位置记录无法读取，请运行 drafts --refresh 重新识别。") from exc
    else:
        found = {}
        for config in settings_files(home, system, env):
            if not config.is_file():
                continue
            try:
                candidate = configured_root(config)
            except (UnicodeError, configparser.Error, OSError) as exc:
                raise RuntimeError("无法读取剪映路径设置，请核对本机剪映配置。") from exc
            if candidate is not None:
                found.setdefault(candidate, config)
        if len(found) != 1:
            raise RuntimeError("未找到唯一的剪映实际草稿设置；请先启动剪映并检查草稿保存位置。未猜测或创建草稿根目录。")
        root, config = next(iter(found.items()))
        root = checked_root(root)
        cache.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".jianying-", dir=cache.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump({"version": 1, "system": system, "drafts_root": str(root),
                           "config_file": str(config)}, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            os.replace(temporary, cache)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    override = env.get("JY_PROJECTS_ROOT", "").strip()
    if override and Path(override).expanduser().resolve() != root:
        raise RuntimeError("JY_PROJECTS_ROOT 与本机已核验的剪映目录不同；请取消此覆盖。")
    return root
