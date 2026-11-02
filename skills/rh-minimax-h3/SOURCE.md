# 来源记录

- skill: `rh-minimax-h3`
- kind: `local`
- status: `confirmed`
- source: 已确认的用户二创／整合版本；本地开发／维护目录 `skills/video/ai/rh-minimax-h3`；当前维护仓库 https://github.com/oTATo-Boss/my-skills
- version: 4.0.0
- author: oTATo-Boss（用户本人）；2026-10-30 在当前对话明确确认本人制作，Agent 辅助编写／整理。
- license: MIT（2026-10-14 本人决定，见 [LICENSE](<LICENSE>)）
- collected_at: unknown；没有可靠安装／导入日期。
- recorded_at: `2026-10-30`
- evidence: 当前维护仓库的 SOURCE_NOTES.md 与 INSTALL_MAP.json；[sources.md](references/sources.md)、[变更记录](CHANGELOG.md)；用户 2026-10-19 提供新应用 API 示例，原文 SHA-256 `c3d1f0899d6bffc64eb882bc04af7c6af3fb0b93ac1146e18f1e64bf4df5d466`；本人 2026-10-14 决定以 MIT 许可发布。

- v2.0.0 evidence: 用户 2026-10-27 提供应用 `2104753059472990209` 的 API 示例，SHA-256 `326f18351a2382904abc9b9fc8eb8643e50c9e56d003cd5ea972b7a6cedfc0d5`；线上节点查询及真实 5 秒任务，详见 [sources.md](references/sources.md)。

- v3.0.0 evidence: 用户 2026-10-27 提供应用 `2084320751339032577` 的 API 示例，SHA-256 `95dcb076fbb1e4742dfea9a899564e2559b0660705bb76c97e3e92fc78256c0d`；任务 `2115032448303980545` 输出 15.083 秒视频，用户在三款对照中选中该应用；截图页面称 V3，节点查询名称仍为 V2。

- 2026-10-27 用户指定真人写实 LoRA：[fal 原作者模型卡](https://huggingface.co/fal/MiniMax-H3-Realism-People-LoRA)，MiniMax H3 Community License；仅保存模型名、强度和触发词，不再分发权重。目标应用已接受该配置并成功出片；无加载日志，权重实际应用尚未独立确认。

- v4.0.0 evidence: 用户 2026-10-28 选择小白版 V2 应用 `2101232638873858050` 并提供四组 LoRA、触发词与画质映射截图；原 API 示例 SHA-256 `cd7c983c620e0459b600ef6d97231c63bada5a5b5fb31ebc84da86594a644dff`。四组组合与各画质档尚未线上验证。

## 本地调整与边界

- MIT 只覆盖本人编写和修改的代码与文档；RunningHub 的应用、接口和服务条款归 RunningHub 及应用作者，不在许可范围内。
- 封装已有 RunningHub 项目工具；原应用、API 和第三方代码不声明为用户原创，原工具作者与独立许可仍待确认。
- 开发目录与本机安装目录保留独立实体副本，来源资料按项目约定同步。
- v1.1.0 新增用户指定长视频应用的独立节点映射、构造器分支与双应用提交路由；来源确认状态和离线验证不等于该新应用已线上生成成功。
- v1.1.1 按用户 2026-10-19 要求，两种模式和缺省实例的旧 jobs 默认使用 Plus；显式实例选择继续保留，未据此提交生成任务。

归属说明：当前用户二创／整合版本已确认；上游作者、仓库或许可缺口仅表示第三方资料不全。

## 2026-10-30 · 当前作者归属最终确认

用户明确确认本技能为本人制作；以本次直接确认取代此前“仅记录为本人／二创版本”的归属表述。Agent 辅助实现不改变本项目作者登记。工具、第三方依赖、参考资料、继承模板及素材的原作者与许可仍分别保留，不将技能归属扩展为这些外部资源的原创声明。

## 本项目后续适配

上述哈希与来源保留为导入快照；跨电脑修改见 [PROJECT_COPY.md](PROJECT_COPY.md)，仅修改本项目副本。
