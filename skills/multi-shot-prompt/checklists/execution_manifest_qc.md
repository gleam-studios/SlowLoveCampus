# 执行清单 QC

- [ ] 目标生成服务的模式、附件限制等能力已经核实
- [ ] 生成模式与素材数量/类型一致
- [ ] 四部分的ID、版本和SHA256齐全，`verbatim_concat` 顺序为 video_summary → film_texture → material_lock → storyboard
- [ ] 完整提示词原文拼接为 `verbatim_concat`
- [ ] 提示词中的 `@文件名.格式` 对应真实附件；如需平台槽位，由执行层按已核实附件顺序机械映射并记录一一对应关系
- [ ] 续写仅使用通过实际审查的 accepted observed take
- [ ] 授权与安全检查通过
