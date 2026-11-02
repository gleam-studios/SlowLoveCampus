---
name: setup
description: Python script initialization and environment setup rules.
metadata:
  tags: setup, python, import, sys.path
---

# Environment Initialization

Use a single reliable bootstrap path. Do not assume helper files outside this repo.
Always support multiple editor layouts and allow explicit override.

## Recommended Bootstrap (Mandatory)

```python
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
env_root = os.getenv("JY_SKILL_ROOT", "").strip()
skill_candidates = [
    env_root,
    os.path.join(current_dir, ".agent", "skills", "jianying-editor"),
    os.path.join(current_dir, ".trae", "skills", "jianying-editor"),
    os.path.join(current_dir, ".claude", "skills", "jianying-editor"),
    os.path.join(current_dir, "skills", "jianying-editor"),
    os.path.abspath(".agent/skills/jianying-editor"),
    os.path.dirname(current_dir),  # when script is under examples/
]

scripts_path = None
attempted = []
for p in skill_candidates:
    if not p:
        continue
    p = os.path.abspath(p)
    attempted.append(p)
    if os.path.exists(os.path.join(p, "scripts", "jy_wrapper.py")):
        scripts_path = os.path.join(p, "scripts")
        break

if not scripts_path:
    raise ImportError(
        "Could not find jianying-editor/scripts/jy_wrapper.py\\nTried:\\n- "
        + "\\n- ".join(attempted)
    )

if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

from jy_wrapper import JyProject
```

## Notes

- Do not use `from jy import JyProject` unless your project explicitly provides `jy.py`.
- Prefer setting `JY_SKILL_ROOT` in mixed editor environments.
- Put business scripts in the user workspace, not inside the skill repo.
- Always call `project.save()` at the end.

## 本项目工具入口

从项目根目录用 `./工具/运行.command python 工作区/本轮任务/剪辑/剪辑.py` 执行。Windows 使用 `.\工具\运行.bat python ...`。包内 Python、依赖、FFmpeg 和 `JY_SKILL_ROOT` 已由入口设置，不配置 Homebrew 或其他电脑的绝对安装路径。
