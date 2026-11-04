# 研发技术调研与知识库 Agent

当前已实现配置加载、单次模型调用和 CLI，支持输入校验、错误分类、响应检查及可调 max_tokens。这是 Agent 的模型接入基础模块，尚无工具调用循环。

首日验收（2026-11-04）：十二项项目测试及四项本地批量验收方法共十六项通过。曾发现的 message=None 未分类错误已修复；缺失字段、错误候选结构和无效内容均在本次受控样例中归为 invalid_response。实现过程、设计取舍与学习复盘见首日进度记录。

## 开发环境

- 已核验：Windows、Python 3.12.7、uv 0.6.14。
- SDK：openai 3.42.1；配置文件加载：python-dotenv 1.2.4。
- requirements.in 列直接依赖，requirements.txt 固定本次解析的全部依赖版本；复现时安装 requirements.txt，不重新解析最新版。

在项目根目录使用 PowerShell：

```powershell
uv venv --python 3.12 .venv
uv pip sync requirements.txt --python .venv\Scripts\python.exe
.\.venv\Scripts\python.exe -c "import openai; print(openai.__version__)"
```

如 uv 无法定位解释器，可将 --python 3.12 替换为本地 Python 解释器的实际路径。若默认缓存目录不可写，可通过 --cache-dir 指定有写入权限的目录。

## 本地配置

首次配置时将 .env.example 复制为 .env，在本地编辑 DEEPSEEK_API_KEY。已有 .env 时不要覆盖；不要把密钥写入示例或提交到 Git。

- 服务：DeepSeek 官方 API。
- Base URL：https://api.deepseek.com。
- 模型 ID：deepseek-flash；已完成真实函数调用与 CLI 调用验证。
- 使用 OpenAI Python SDK 的 Chat Completions 兼容接口，实际请求目标由 base_url 指定。DeepSeek 参数与响应以 DeepSeek 文档为准。
- config.py/load_settings 显式加载 .env，已有进程环境变量优先，检查三个必要字段。

参考：[DeepSeek 首次调用](https://api-docs.deepseek.com/)、[OpenAI Python SDK](https://developers.openai.com/api/reference/python)。

## 当前验证边界

2026-11-04 本地合并验收：Ran 16 tests in 0.027s / OK。其中十二项位于 test/test_model_client.py 和 test/test_cli.py；另四项为仓库外的本地验收脚本，批量覆盖默认/自定义 token 上限、六种非法参数、十二种异常响应结构、五种 HTTP 状态到 CLI 的失败出口。仓库内命令仍运行十二项，不会显示十六项。PyCharm 使用项目 .venv/Scripts/python.exe。

真实联调完成函数调用和 CLI 调用各一次；手工 CLI 帮助、纯空白输入、正常问题的退出码分别为 0/2/0。上述合并验收使用模拟依赖，不发送真实请求。模拟验证不证明真实服务错误映射、网络故障或所有协议损坏情况；原始 JSON 解析失败等 SDK 解析边界尚未专项覆盖。完整证据见 plan/研发进度Day 1.md。

从项目根目录复现现有十二项测试：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s test -p "test_*.py"
```

## 运行（项目根目录）

```powershell
.\.venv\Scripts\python.exe cli.py --help
.\.venv\Scripts\python.exe cli.py "用一句话解释什么是 API。"
$LASTEXITCODE
```

正常问题会发送真实请求。成功输出回答并退出 0；已知输入/配置错误退出 2，已分类模型错误退出 1。

## 接口与设计边界

`config.py` 加载并校验必要配置；`model_client.py` 的 `ask_once(question: str, max_tokens: int = 1024) -> str` 构造请求、提取回答并转换 SDK 异常；`cli.py` 处理命令行参数、输出流和退出码。

`max_tokens` 控制生成输出的 token 上限，不是输入上下文窗口，也不保证生成固定长度。调用方可以指定该参数；当前 CLI 仍使用默认值，尚无对应的命令行选项。

请求使用非流式输出、关闭思考模式、30 秒 SDK 网络超时及 `max_retries=0`。网络超时不是整个任务的严格总时限。响应需满足候选列表有效、结束原因为 `stop`、正文为非空字符串；这些检查不保证回答事实正确。后续工具调用流程将沿用配置与错误处理职责，并扩展消息和响应接口。
