# 项目适配

本项目按 [使用规范](../../README.md)运行；通过包内 Python 执行，不依赖系统 Python。

- `build_jobs.py` 新配置写入 `path_base: jobs_file`，`$upload` 以 jobs 文件所在目录为基准，使用 `/` 分隔。
- 执行器按 jobs 的实际位置解析，支持整项目移动。旧格式仅用于恢复旧任务，不批量改写既有回执。
- 新回执中的本地文件引用以项目根目录为基准。生成参数、应用与默认 LoRA 不变；未进行付费或线上验证。
- 凭据仍存当前用户的私有配置或环境变量；macOS 使用 0600，Windows 使用当前用户 SID 的文件 ACL，设置失败不写入 Key。
- 本副本的离线回归测试随项目保存；共享技能库未修改。上游来源与许可保留在 [SOURCE.md](SOURCE.md)、[LICENSE](LICENSE)。
