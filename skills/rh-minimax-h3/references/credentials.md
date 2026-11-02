# 本机凭据

使用同事自己的 RunningHub API Key（不是 MiniMax Key）。凭据只保存在当前用户的私有配置或运行环境，不随项目分发。默认读取 `~/.config/rh-minimax-h3/.env`；也可用 `RUNNINGHUB_ENV_FILE` 指定已获授权的本机私有文件。

读取顺序：非空 `RUNNINGHUB_API_KEY` → 指定私有文件或默认私有文件。指定文件缺 Key 时不自动尝试其他项目；不执行 env 文件内容。状态输出不展示 Key、片段或哈希。

从项目根目录运行，隐藏输入，真实密钥不放命令参数、聊天或 shell 历史：

macOS：

```sh
./工具/运行.command python skills/rh-minimax-h3/scripts/credentials.py set
./工具/运行.command python skills/rh-minimax-h3/scripts/credentials.py status
```

Windows PowerShell：

```powershell
.\工具\运行.bat python skills/rh-minimax-h3/scripts/credentials.py set
.\工具\运行.bat python skills/rh-minimax-h3/scripts/credentials.py status
```

只有明确换 Key 时才加 `--replace`。不要用它覆盖包含其他业务内容的 env 文件。`import-env --from-env` 仅在用户明确授权时从当前电脑的私有文件导入，不复制作者的配置。

macOS 使用目录 0700 / 文件 0600；Windows 写入密钥之前通过 `whoami` 取得当前用户 SID，使用 `icacls` 限制文件 ACL。无法设置权限时不写入 Key。保存与状态检查均不联网，不验证余额或服务认证。
