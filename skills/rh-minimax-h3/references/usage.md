# 小白版 V2：任务构造、生成与恢复

Agent 按任务指定时长、画幅、提示词、参考图和交付目录；至少一张图片，纯文生未验证。不将素材或凭据写入技能目录。

从项目根目录执行；Windows 将 `./工具/运行.command python` 替换为 `.\工具\运行.bat python`，PowerShell 中按单行输入各命令。

```bash
SKILL_DIR="skills/rh-minimax-h3"
./工具/运行.command python "$SKILL_DIR/scripts/build_jobs.py" \
  --prompt-file 工作区/本轮任务/prompt.txt --name shot01 \
  --seconds 15 --aspect 9:16 --quality 720P \
  --image 工作区/本轮任务/人物.png --audio 工作区/本轮任务/音色.wav \
  --output 工作区/本轮任务/jobs.json
./工具/运行.command python "$SKILL_DIR/scripts/rh_minimax_h3.py" 工作区/本轮任务/jobs.json \
  --output 工作区/本轮任务/输出 --dry-run
./工具/运行.command python "$SKILL_DIR/scripts/rh_minimax_h3.py" 工作区/本轮任务/jobs.json \
  --output 工作区/本轮任务/输出
```

新 jobs 标记 `path_base: jobs_file`，素材相对 jobs 所在目录；共享项目内的素材应先放入项目再构造。

示例不规定所有任务的时长或画幅。构造器拒绝覆盖已有 jobs；dry-run 不上传、不提交、不验证线上节点或账户余额。

- `--quality 480P|720P|1080P` 分别设置 **0.5、1、2 MP**；默认 720P（1 MP）。这是用户指定的档位映射，实际输出宽高不一定是标准分辨率。也可 `--megapixels` 指定数值。默认 Plus；2 MP 及以上使用 Ultra，显式传入其他实例会拒绝。
- `--image` 重复 1–6 次，`--audio` 重复 0–2 次；单文件限 30 MB。未使用的图像槽复用最后一张参考图，`827` 保持真实图片数；上传按文件路径去重。未使用音频为 `None`。
- 四组 `--lora-N-name`、`--lora-N-strength`（N=1–4）可单次覆盖用户指定默认值；`--lora-trigger` 可覆盖触发词。换 LoRA 时应一起检查触发词，构造器不会推断新的触发词。
- 默认 `--output-format video`；`zip` 映射示例布尔开关 `true`，ZIP 输出未实测。版本开关默认沿用已成功样例的 `true`，可显式 `--version-switch true|false`；v1/v2 的布尔对应关系尚未核实。
- 本应用接口没有提示词优化开关、采样步数、视频参考或种子字段；不要传入或假称已控制这些参数。

`<name>_submitting.json` 保存不含 Key 的请求与状态，`<name>_<taskId>.json` 保存状态、usage 和结果检查。提交不明时先查平台，不盲目重试。已有 taskId：

```bash
./工具/运行.command python "$SKILL_DIR/scripts/rh_minimax_h3.py" --resume TASK_ID \
  --name 原任务名 --output 工作区/本轮任务/生成
```

其他应用的历史任务可恢复，但其他应用 ID 和缺 appId 的 jobs 拒绝提交；查询恢复与当前应用选择相互独立。
