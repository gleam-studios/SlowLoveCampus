# Multi-Shot Prompt

通用多镜头视频提示词 Skill。单个完整提示词按固定顺序输出四个部分：`# 视频梗概`、`# 影片质感`、`# 素材锁定`、`# 分镜`。支持 `standalone_mode` 与 `managed_mode`，以及按需的执行清单、审片与单变量返修。

## 结构与关键输出约定
- `SKILL.md`：技能入口及完整规则，统一 Skill ID `multi-shot-prompt`
- `templates/`：四部分提示词、执行、成片审查及返修模板
- `references/`：权限、资产分类、背景场景、音色/台词、分镜连续性和平台执行规则
- `checklists/`：各模块审查合同
- `examples/`：完整多镜头及模拟参考资产的格式验证案例
- `scripts/validate_skill_contract.py`：结构、顺序、分镜台词与背景引用的自动校验

影片质感必须按 `影像风格：`、`摄影偏好：`、`材质与氛围：`、`光影与色彩：` 四行分别填写，并验证字段顺序和非空值。

素材锁定内固定为 `场景：`、`角色：`、`道具：`，可用真实 `@文件名.格式：` 分别绑定对应资产。场景图仅在素材锁定区引用，镜头中的背景以文字描述动态环境。每镜用 `视频内容：` 下的连续时间段叙述事件，时间沿用全片绝对秒数。对白在实际开口处写 `@人物图.png说（@音色.mp3）：“台词内容”`，并在独立 `台词：` 栏按顺序逐句复写；两处引用、文字、引号和次数一致。无对白写 `台词：无`，无音色文件省略音色括号。

## 运行与检查
将整个目录安装至 Agent Skills 路径。独立创作明确 `execution_mode: standalone_mode`；导演托管明确 `execution_mode: managed_mode`，并提供已批准的输入。运行 `python3 scripts/validate_skill_contract.py` 检查资源与内置格式用例；运行 `python3 scripts/validate_skill_contract.py --prompt 路径/提示词.txt` 检查实际输出的文本结构。自动检查覆盖时间段、引用、台词配对与格式；叙事合理性、表演和成片效果仍需人工及实际生成验证。

本 Skill 至少使用1镜，不设独立的镜头数量上限，总时长≤30秒；平台实际单次生成能力需独立核实。来源及重建范围见 `RECOVERY_NOTICE.md`。
