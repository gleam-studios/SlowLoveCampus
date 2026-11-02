# Single Shot Prompt 1.1.1

用于不切镜的单镜头短视频提示词创作、修改、审查与反馈改写。曾用名 `ai-video-prompt`、`short-video-prompt`；根据用户长期使用经验，将适用范围明确为单镜头短视频。通过简洁的导演角色发挥创意、美术与设计能力，用模板统一新稿格式。

提供目标、明确要求和参考素材即可；未锁定的设计空间自主发挥。新建完整提示词在一个代码块中包含视频梗概、参考素材和同一镜头内按时间连续推进的内容，按需在末尾补充全片要求。通过主体动作、运镜和视觉变化推进节奏，时间分段不代表切镜；不预设固定秒数或画幅。局部修改、讨论、审查和用户指定的格式按实际请求处理。

入口为 `SKILL.md`，完整新稿使用 `templates/video_prompt_template.md`，调用元数据位于 `agents/openai.yaml`。职责聚焦提示词文本创作。

目录名称和机器标识均为 `single-shot-prompt`，可用 `$single-shot-prompt` 调用。

开发目录为 `skills/video/ai/single-shot-prompt/`；本机安装路径为 `~/.agents/skills/video/ai/single-shot-prompt/`，保留独立实体副本。Claude 发现入口 `~/.claude/skills/single-shot-prompt` 指向本机安装目录。同步顺序见项目 `AGENTS.md`。

文本试用只能反映提示词设计；素材与生成模型也影响最终视频质量。Not-tested: live video generation。
