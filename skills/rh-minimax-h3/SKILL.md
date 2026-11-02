---
name: rh-minimax-h3
description: 使用 RunningHub MiniMax H3 多图生视频自动提示词 V2 应用生成视频；支持多图、音频参考、四组 LoRA、分辨率档位、安全凭据、任务构造与结果恢复。用户提到 RH-minimax-H3 或 RunningHub H3 时使用。
metadata:
  version: "4.0.0"
---

# RH-minimax-H3

本项目入口优先遵循 [PROJECT_COPY.md](PROJECT_COPY.md) 与[使用规范](../../README.md)：使用包内 Python，新 jobs 使用相对路径，凭据各电脑独立配置。

当前生成只提交 RunningHub **MiniMax-H3 多图生视频自动提示词 V2－小白全能版**，应用 `2101232638873858050`。旧应用的任务可用 taskId 查询恢复；旧应用 jobs 禁止直接提交。依赖 Python 3.9+、`requests`，可选 `ffprobe`。接口或工作流可能更新，按需核对当前节点。

## 参数和默认配置

Agent 根据任务指定提示词、**时长 5–15 秒、画幅、1–6 张参考图和输出目录**；可选最多 2 段音频。纯文生未验证。支持 1:1、2:3、3:2、3:4、4:3、9:16、16:9、21:9。

用户指定画质档：**480P→0.5 MP、720P→1 MP、1080P→2 MP**。默认 720P（1 MP）+ Plus，1080P 使用 Ultra；可按任务指定其他 MP 或实例，2 MP 及以上须 Ultra。MP 是生成目标像素量，不保证准确输出标准宽高，实际尺寸以文件为准。应用节点提示超过 0.8 MP 使用 Plus，不代表任何时长与组合必定成功。

默认四组 LoRA 与触发词按用户 2026-10-28 的截图固定：

| 槽位 | 文件名 | 强度 |
|---|---|---:|
| 1 | `MysticXXX_MMH3-V5.1.safetensors` | 0.4 |
| 2 | `Minimax-H3-Digicam-Realism Improve Lora.safetensors` | 0.5 |
| 3 | `h3-realism-people-t2v-i2v-r2v_new.safetensors` | 0.5 |
| 4 | `H3电影感V2.safetensors` | 0.5 |

触发词为 `dynv2,r34l1sm`。默认配置是用户指定值，可以按任务显式覆盖；更换 LoRA 时同步检查触发词。**该四 LoRA 组合和三个画质档尚未在本应用实测，接口成功构造不等于 LoRA 已加载或画质达标。**

沿用应用已测 API 示例的版本布尔值 `true` 与模型名；节点标注“版本<v1 / v2>”，未证明布尔值与版本的对应关系。应用名称包含自动提示词，但接口没有开放单独的优化开关，也没有采样步数或种子字段；不要声称可以控制它们。默认直接输出视频；视频、额外音频及效果以真实返回为准。

## 凭据与执行

先运行 `python3 "$SKILL_DIR/scripts/credentials.py" status`；优先读取环境变量 `RUNNINGHUB_API_KEY`，其次 `~/.config/rh-minimax-h3/.env`，可通过 `RUNNINGHUB_ENV_FILE` 指定。新 Key 用隐藏输入保存、权限 0600；禁止泄露凭据，详见 [credentials.md](references/credentials.md)。

按 [usage.md](references/usage.md) 创建 jobs 并先 `--dry-run`；dry-run 不联网、不验证账户或节点。经任务授权才能提交，每批最多 3 个在途。保存无 Key 的提交回执和 taskId；提交结果不明、查询超时或连接中断不得盲目重提。已有 taskId 用 `--resume TASK_ID --name 原名称 --output 原目录` 查询并下载，不重新提交。报告 taskId、平台 usage、文件、实际尺寸与时长；usage 缺失如实说明。用户要求生成后直接交付时不增加画面审查。

## 参考与验证

- [usage.md](references/usage.md)：构造、可选参数与恢复。
- [api.md](references/api.md)：当前节点、限制和实测范围。
- [sources.md](references/sources.md)：来源及版本。
- 离线行为：`python3 "$SKILL_DIR/tests/test_helpers.py"`；假服务：`python3 "$SKILL_DIR/tests/mock_test.py"`。假服务不调用 RunningHub。
