# 执行清单（提示词外部元数据）
```yaml
execution_mode: standalone_mode # 或 managed_mode
provider: <已核实的服务>
generation_mode: T2V # T2V/I2V/R2V/FLF2V/EXTEND/EDIT
project_aspect_ratio: <执行层比例>
prompt_assembly: verbatim_concat
prompt_order: [video_summary, film_texture, material_lock, storyboard]
components:
  video_summary: {id: <id>, version: <version>, sha256: <hash>}
  film_texture: {id: <id>, version: <version>, sha256: <hash>}
  material_lock: {id: <id>, version: <version>, sha256: <hash>}
  storyboard: {id: <id>, version: <version>, sha256: <hash>}
assets: [] # {filename,category,role,source,rights_status,platform_slot}
continuation_take_id: null
rights_status: pending
```
