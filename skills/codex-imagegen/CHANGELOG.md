# 版本记录

## 2.0.0 — 2026-10-16

- Python 3.10+ 标准库入口，保留原 gen-image.sh 参数兼容。
- 当前 CLI 登录、feature flag 和 exec 接口只读探测；不把预检当成实际生图证明。
- 固定 workspace-write，隔离单次运行输出，独占创建避免覆盖，只回收本次明确返回的新图片。
- 新增 UTF-8 prompt-file，移除对 Bash、BSD stat、file 与 sips 的依赖。
- 不修改模型、登录、客户端配置；无原生工具时不递归或生成占位图。
