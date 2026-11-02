# 模板选择与使用

只读取当前阶段与当前画风需要的文件。模板中现有占位符填写本次内容，不把某个角色写入共享模板。未提供的参考不虚构。

## 写实用途选型

先按[写实模板分流](realistic-routes.md)选择用途，再选阶段。下表三套保留完整基础流程；原写实路线仅保留[一步到位快速综合板](../assets/templates/realistic/board.txt)，无默认服装，实际参考图与结尾设计插槽共同控制最终角色设计。

| 阶段 | 通用基础服装版 | 美女专用版 | 帅哥专用基础版 |
|---|---|---|---|
| 正面肖像 | [portrait](../assets/templates/realistic-base/portrait.txt) | [portrait](../assets/templates/beauty/portrait.txt) | [portrait](../assets/templates/handsome/portrait.txt) |
| 头部四视图 | [head-four](../assets/templates/realistic-base/head-four.txt) | [head-four](../assets/templates/beauty/head-four.txt) | [head-four](../assets/templates/handsome/head-four.txt) |
| 正面半身 | [half](../assets/templates/realistic-base/half.txt) | [half](../assets/templates/beauty/half.txt) | [half](../assets/templates/handsome/half.txt) |
| 全身三视图 | [body-three](../assets/templates/realistic-base/body-three.txt) | [body-three](../assets/templates/beauty/body-three.txt) | [body-three](../assets/templates/handsome/body-three.txt) |
| 综合板 | [board](../assets/templates/realistic-base/board.txt) | [board](../assets/templates/beauty/board.txt) | [board](../assets/templates/handsome/board.txt) |

新基础版和帅哥版快速板默认采用16:9左半身、右上头部四视、右下全身四视；分阶段仍用原三张整图拼接结构。美女版恢复整体重写前的女模特模板，仅服装为纯白色基础款合身短袖T恤和黑色基础款运动短裤（裤长至大腿中部）；原文阶段冲突沿用分流说明中的历史适配。已有分阶段源图时使用拼接脚本。原写实快速综合板只生成新整板，不提供分阶段或拼接模式；下文CG／AAA模式不覆盖各写实模板的明确规格。

## CG／AAA基础模板

| 阶段 | 通用3D-CG | AAA-CG |
|---|---|---|
| 正面肖像 | [portrait](../assets/templates/cg/portrait.txt) | [portrait](../assets/templates/aaa/portrait.txt) |
| 头部四视图 | [head-four](../assets/templates/cg/head-four.txt) | [head-four](../assets/templates/aaa/head-four.txt) |
| 正面半身 | [half](../assets/templates/cg/half.txt) | [half](../assets/templates/aaa/half.txt) |
| 全身 | [body-four](../assets/templates/cg/body-four.txt) | [body-four](../assets/templates/aaa/body-four.txt) |
| 综合板 | [board](../assets/templates/cg/board.txt) | [board](../assets/templates/aaa/board.txt) |

软件模板已纠错的快照是版本起点；随包适配阶段独立排版和模块化风格字段。输出是参考图片，不包含真实绑定、网格或三维模型数据。

## CG／AAA综合模板的运行模式

CG／AAA综合模板均提供 `{{输出模式}}`、`{{本次输入与参考职责}}`。运行前明确填一种模式；不让图片模型自行选择：

- `快速整板生成`：三类画风均支持。实际人物/服装/妆造/特征参考＋文字说明，直接生成完整多视角角色板；无需已有头部、半身或全身中间图，不强制使用打底服或先拼接。已定身份保持，其余按本次整体设计要求执行。
- `综合板`：作为排版规格与裂变参考，不默认再次调用生图。三张完整源图交[排版脚本](board-composition.md)拼接，不拆分任何视角。若某一源图有生成缺陷，沿用其原始输入重抽，仅替换采用版本，不改其提示词或其他合格图。

头部与全身分别使用独立head-four、body-four模板，综合模板不再承担补齐模式。同一阶段只需要一张最终可用的9:16全身四视图，随机缺陷允许原条件重抽。已有可用全身图时禁止再次补齐，拼接阶段不生成新图；发现生成缺陷直接在任务授权内沿用原提示词、参考和规格重抽，不改成横版或自动更改设计。

快速模式是生成新整板；`综合板`模式是已有源图的排版规格，二者不可混用。写实基础路线已有源图直接按其拼接说明处理，原写实快速综合板不进入分阶段。各模板都不要求“为了排版统一”重绘已确认面部。

通用CG与AAA快速综合板的全身区域统一2×2四宫格；AAA独立全身及通用CG独立全身同样为9:16、2×2四宫格。头部和半身区域照常保留。

## 服装与裂变模板

- [原创服装四视图](../assets/four-view-template.txt)：填服装设计与风格字段，写实使用真实服装质感，CG/AAA使用对应角色的材质表现。
- [原穿搭提取](../assets/templates/outfit/extract.txt)：保留原款式、配饰和穿戴关系，不重新设计；新增风格字段用于匹配角色目标表现。
- [角色换装与受控妆造](../assets/character-styling-template.txt)：图1锁身份及排版，图2锁造型，图3～N补细节。仅妆造时不强行要求新服装图；使用模板内“不换装”分支。
- [剧情状态修改](../assets/templates/outfit/state.txt)：以已确认造型板为编辑目标，明确改变与保持项；支持无服装变化的伤口、泪痕、情绪等。

模板只负责本阶段输出，不追加完整镜头、场景或生视频指令。角色参数中不写未经用户确认的“已批准”。

## 更新与来源

当前包为模板维护源，不在执行时依赖oTATo Prompt。软件快照的标题和原始内容摘要见[来源清单](template-sources.json)，原服装技能来源保存在[历史来源](legacy-outfit-source.md)。以后修订保留来源记录，并在用户要求时同步软件；不做隐式双向覆盖。
