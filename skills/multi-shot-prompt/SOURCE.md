# 来源记录

- skill: `multi-shot-prompt`
- kind: `local`
- status: `confirmed`
- source: 用户提供的 `multi-shot-prompt.skill` 中的 `multi-shot-prompt/`；当前维护目录 `skills/video/ai/multi-shot-prompt/`；维护仓库 https://github.com/oTATo-Boss/my-skills
- version: unknown；原包未声明独立发布版本，原始记录为 2026-10-21 导入快照；当前本地维护修订为 2026-10-31。
- author: oTATo-Boss（用户本人）；2026-10-30 在当前对话明确确认本人制作，Agent 辅助编写／整理。
- license: unknown；原包未附 LICENSE 或许可声明，本次导入不新增许可。
- collected_at: `2026-10-21`
- recorded_at: `2026-10-31`
- evidence: 用户在本次会话要求安装至本机和项目，并明确声明本人开发；原包 `multi-shot-prompt.skill`（原始导入归档，不作为运行路径） 的 SHA-256 `1225b59d433f983ed55e06a79c256f92df247621ed6c6d0f5c0842a8c656760b`；入口 SHA-256 `7ffe1f98975b243829d62bfb07d582bc06cbec4a0c979182db07ee24a5359249`；原包 [README.md](README.md)、[来源与恢复范围](RECOVERY_NOTICE.md) 及 [导入记录](CHANGELOG.md)。

## 本地调整与边界

- 2026-10-21 原包 46 个文件完整导入，保留归档指定的 0644 权限，并新增本文件与 CHANGELOG.md；后续本地修改与删除记录见 CHANGELOG.md，索引和安装映射在包外维护。
- 用户原创归属已确认。原包说明：主文件基于历史主文档修改，配套参考、模板、清单、示例、元数据及脚本按主文件与修改要求重建；详细范围保留在 RECOVERY_NOTICE.md，不声明为历史完整包逐字恢复。
- 原包未单独声明当前发布版本和许可证；保留这些缺口，不影响已确认的本人开发归属。
- 导入时运行原包只读校验脚本，38 个资源引用、10 个正向用例和 32 个错误变体通过；该检查只覆盖文本结构、时间边界、素材绑定和台词一致性，不代表实际视频生成质量。
- 开发目录与本机安装副本保留独立实体，Claude 发现软链接指向安装副本。Not-tested: live video generation。

## 2026-10-30 · 当前作者归属最终确认

用户明确确认本技能为本人制作；以本次直接确认取代此前“仅记录为本人／二创版本”的归属表述。Agent 辅助实现不改变本项目作者登记。工具、第三方依赖、参考资料、继承模板及素材的原作者与许可仍分别保留，不将技能归属扩展为这些外部资源的原创声明。

## 2026-10-31 · 本地维护修订

按用户要求取消独立的最多9镜限制，保留总时长≤30秒，并移除真人感日常自拍模式及专属资源。当前入口指纹与验证证据以本次校验输出为准；上文入口指纹保留为原始导入证据。Not-tested: live video generation。
