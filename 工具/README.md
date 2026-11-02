# 项目工具

使用规范统一见[项目 README](../README.md)。仓库保存部署脚本和固定版本／SHA-256 清单；Python、FFmpeg、Whisper 和平台依赖首次运行时下载，后续在本机离线复用。已有本机完整工具包保留并校验，不重新安装相同版本。

目标平台为 macOS ARM64、macOS Intel、Windows x64。自动引导不要求事先安装 Python：Mac 用系统原生工具引导；Windows 用 PowerShell 5.1、curl.exe、tar.exe，并在首次启动 Python 前配置所需 MSVC DLL。

## 入口

Mac 使用 `./工具/运行.command`；Windows 使用 `.\工具\运行.bat`。以下示例从项目根目录执行，Windows 将入口替换即可：

```sh
# 自动部署后检查环境；首次会联网下载所需内容
./工具/运行.command check --load-model

# 仅部署，不检查剪映
./工具/运行.command setup

# 本机离线识别台词
./工具/运行.command transcribe "工作区/本轮任务/源视频.mp4" --language en --output "工作区/本轮任务/台词"

# 媒体工具与业务脚本
./工具/运行.command ffprobe -v error -show_format -show_streams "工作区/本轮任务/源视频.mp4"
./工具/运行.command python "工作区/本轮任务/剪辑/剪辑.py"

# 读取本机剪映位置；用户在剪映中改过位置才刷新
./工具/运行.command drafts
./工具/运行.command drafts --refresh

# 回归测试
./工具/运行.command python -m unittest discover -s 工具/验证 -v
```

所有相对业务参数以实际项目根目录为基准。转录输出 SRT 与逐词 JSON，已有输出不覆盖。启动器设置当前项目的 Python 依赖、FFmpeg 和 `JY_SKILL_ROOT`，识别使用本地模型，不调用云端转录。首次之后无需网络即可运行已有环境；线上图片／视频服务另按各自账户和授权执行。

## 版本与来源

- `部署锁定.json`：运行时唯一下载清单，固定每个 wheel、模型文件、运行时与 FFmpeg 的 URL 和 SHA-256。
- `requirements.txt`：核心版本意图；`依赖清单-*.txt`：各平台完整包版本。
- `python-sources.json`、`ffmpeg-sources.json`、`msvc-sources.json`、`SOURCES.json`：上游及原本机包的来源记录。
- `维护/生成部署清单.py`：维护时从既有精确版本和官方 PyPI 元数据重建锁定文件；普通使用不运行它，不自动升级。

下载内容、`.part`、安装暂存和部署状态保存在被 Git 忽略的目录，失败后保留必要的下载进度。校验失败不发布正式文件；已有文件不符时停止并保留原件。依赖安装只从已下载并验证的 wheel 进行，使用 pip 的哈希校验和禁止源码构建选项。

剪映路径仍首次读取实际设置并保存在用户配置，后续复用；不存在、歧义或不可访问时停止，绝不另建草稿根目录。工作区与输出仅本机保存，活动排除清单在新电脑从空清单开始。

Windows 与 Intel Mac 的原生首次部署仍需对应真机验证，源码、平台清单或离线测试通过不代替真机与剪映应用预览。
