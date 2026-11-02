# Managed 输入合同

## 输入对象
`execution_mode: managed_mode`; `approval:{status:"approved",authority:"master-director-agent",shot_brief_hash:"sha256:<hex>"}`; `shot_brief:{purpose,shots:[{id,start_s,end_s,framing,camera,action,performance,blocking,composition_lock,end_state}],duration_s}`；`material_lock:{status:"locked",hash:"sha256:<hex>",content:<已批准文本>}`；`style:{status:"approved",hash:"sha256:<hex>",content:<已批准风格>}`。可额外提供 `asset_map`。哈希针对上游声明的规范化原文；缺少既定规范时由上游提供可比较的准确摘要，不能擅自编造正确摘要。

## 阻断条件
1. 审批状态或权限不匹配：`E_MANAGED_NOT_APPROVED`。
2. 任一哈希缺失、不匹配或锁定未生效：`E_MANAGED_HASH_OR_LOCK_INVALID`。
3. 镜头目的、顺序、时长、构图、人物行为、空间调度或落点不完整：`E_SHOT_BRIEF_INCOMPLETE`。
4. 素材身份、风格或分镜之间存在无法机械消解的冲突：`E_MANAGED_CONFLICT`。
5. 任一请求需要创作额外镜头或改变意图：`E_UPSTREAM_DIRECTOR_REQUIRED`。

## 输出原则
拒绝时只输出 `error_code`、`field_path`、`return_to`，不制造临时版本。成功时逐项映射输入；同时输出可审计的原文指纹，不生成第二份变体提示词。事件、构图、起止时间及最后画面须与批准输入一一对应。对白沿用上游已批准的原文、说话者与时间；映射到视频内容的说话时刻，并在台词栏逐句复写。上游未细分镜内时间时可用该镜完整时间段，已批准的时间边界原样保留。
