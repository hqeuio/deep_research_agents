# 研发技术调研与知识库 Agent

这个项目希望让程序读过技术资料再回答问题。比如，给它一份聊天室的设计说明，问「为什么需要发送队列」，回答应当指出哪一段资料解释了这个设计。资料没有给出依据时，回答也应说明缺少什么。

目前可以在命令行向 DeepSeek 提问。CLI 统一调用 [agent.py](agent.py) 的 `run_agent`，模型可以直接回答，也可以请求查询固定笔记。一次任务默认最多请求模型三次，循环与命令行的错误出口已通过本地模拟检查。文档检索和来源引用留待后续。

## 在本地运行一次问答

在项目根目录使用 PowerShell。已用 Windows、Python 3.12.7 和 uv 0.6.14 搭建环境。直接依赖列在 `requirements.in`，安装时读取锁定版本的 `requirements.txt`。若 uv 找不到 Python，可以把 `3.12` 换成本机解释器路径。默认缓存不可写时可指定 `--cache-dir`。

```powershell
uv venv --python 3.12 .venv
uv pip sync requirements.txt --python .venv\Scripts\python.exe
.\.venv\Scripts\python.exe -c "import openai; print(openai.__version__)"
```

首次运行时把 `.env.example` 复制为 `.env`，在本地填入 `DEEPSEEK_API_KEY`。示例使用 `https://api.deepseek.com` 和模型 `deepseek-flash`。已有同名进程变量时，程序优先使用进程变量。已有 `.env` 可直接编辑，密钥留在本地。

下面的命令运行仓库中的 12 项自动测试。测试使用模拟依赖。

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s test -p "test_*.py"
```

帮助命令可直接运行。示例问题会发送真实网络请求并产生服务用量。

```powershell
.\.venv\Scripts\python.exe cli.py --help
.\.venv\Scripts\python.exe cli.py "用一句话解释什么是 API。"
$LASTEXITCODE
```

成功时标准输出显示正文，退出码为 `0`。输入或配置有误时退出码为 `2`。模型调用失败、工具失败或请求次数用尽时，退出码为 `1`。错误都写入标准错误流。

## 一次问答经过哪些代码

[config.py](config.py) 提供地址、密钥和模型名。[model_client.py](model_client.py) 的 `request_turn` 借助 OpenAI Python SDK 3.42.1 调用 DeepSeek Chat Completions，处理鉴权、超时、连接和 HTTP 状态错误，成功时返回完整响应。`run_agent` 用 `parse_turn` 判断这轮是文本还是工具请求。工具结果带原编号发回模型，直到得到最终正文或达到请求上限。最后由 [cli.py](cli.py) 输出正文或错误。`ask_once` 仍可作为独立的普通问答函数使用。

请求采用非流式输出，关闭思考模式和 SDK 自动重试，SDK 网络超时为 30 秒。调用方可以用正整数 `max_tokens` 限制单次生成长度。默认 `None` 会省略该字段，使用服务端默认值。整个任务的模型请求次数由 `run_agent` 的 `max_model_calls` 限制，CLI 使用默认值。

[tools.py](tools.py) 目前只注册了 `lookup_note`。例如模型请求 `{"topic":"rag"}`，`execute_tool` 会核对工具名，解析 JSON，确认参数对象恰好包含一个允许的主题字段，然后才查笔记。未知工具、参数有误和执行失败都有各自的错误类别。

## 已验证到哪一步

Day 1 的 Python 函数和 CLI 各完成了一次真实问答。Day 2 的 `run_agent` 手工试跑中既见到直接回答，也见到调工具后根据笔记组织答案。随后用模拟模型响应集中检查了回传顺序与编号、最后一次请求的处理、非法上限及工具失败。CLI 接入后，原有三项检查与新增的临时分组检查一并通过，覆盖正常输出、模型和工具错误、输入错误及请求耗尽。此次 CLI 检查使用替身，真实试跑来自此前的 `run_agent`。

- [Day 1 · 从配置到命令行问答](plan/研发进度Day%201.md)
- [Day 2 · 从模型请求到工具结果](plan/研发进度Day%202.md)

[DeepSeek 接口说明](https://api-docs.deepseek.com/) · [OpenAI Python SDK](https://developers.openai.com/api/reference/python)
