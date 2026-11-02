# 来源与版本

- `rh-minimax-h3` 当前版本 4.0.0（2026-10-28）；用户确认的二创／整合技能，见 [SOURCE.md](../SOURCE.md) 与 [CHANGELOG.md](../CHANGELOG.md)。本技能 MIT 许可不覆盖 RunningHub 的应用、服务、模型或 LoRA。
- 用户提供 [小白版 V2 应用](https://www.runninghub.ai/zh-cn/call-api/api-detail/2101232638873858050?apiType=4)的 API 示例，2026-10-28 只读核对线上节点；原示例与此前三应用对照中第一份示例一致。用户随后指定截图中的四组 LoRA、强度、触发词和画质映射。未在技能中保存用户素材、提示词或凭据。
- 第一组 `MysticXXX_MMH3-V5.1.safetensors`：用户 RunningHub 截图确认文件名，作者、许可和精确权重来源未核实。
- 第二组 `Minimax-H3-Digicam-Realism Improve Lora.safetensors`：用户截图指定，RunningHub 发布的[模型说明](https://huggingface.co/RunningHubAI/rh-minimax-h3-digicam-realism-improve-lora)列出相同文件名；版权归作者，许可须遵循原项目或上游条款。
- 第三组 `h3-realism-people-t2v-i2v-r2v_new.safetensors`：用户截图指定；[fal 模型卡](https://huggingface.co/fal/MiniMax-H3-Realism-People-LoRA)给出触发词 `r34l1sm` 和 MiniMax H3 Community License。RunningHub 的 `_new` 文件与原作者权重是否逐字节一致未核实。
- 第四组 `H3电影感V2.safetensors`：用户截图指定，作者、许可和精确权重来源未核实。用户截图指定组合触发词 `dynv2,r34l1sm`。
- 小白版 V2 真实任务 `2115032446445903873` 以作者示例 LoRA、0.8 MP + Plus、15 秒、多图双音频，输出 1248×672、15.083 秒视频，183 RH 币；完整解码通过。它不验证当前用户指定的四 LoRA 组合、三个画质档、音色相似度或精细口型。
- 更早应用的节点和验证范围见历史变更记录；其他应用 jobs 不再接受，查询恢复不依赖应用 ID。
