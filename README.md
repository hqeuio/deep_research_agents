# 研发技术调研与知识库 Agent

当前已实现配置加载、单次模型调用和 CLI，支持输入校验、错误分类、响应检查及可调 max_tokens。用户报告两次真实调用成功。这是 Agent 的模型接入基础模块，尚无工具调用循环。

最新首日验收（2026-11-04）：十二项项目测试及四项本地批量验收方法共十六项通过。曾发现的 message=None 未分类错误已修复；缺失字段、错误候选结构和无效内容均在本次受控样例中归为 invalid_response。主要理解检查通过，完整独立复述仍待确认。

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

本机已有解释器为 D:\user\conda\python.exe；必要时将 --python 3.12 改为该路径。若 uv 默认缓存写入受限，可添加全局参数 --cache-dir D:\job\work\uv-cache。

## 本地配置

首次配置时将 .env.example 复制为 .env，在本地编辑 DEEPSEEK_API_KEY。已有 .env 时不要覆盖；不要把密钥写入示例或提交到 Git。

- 服务：DeepSeek 官方 API。
- Base URL：https://api.deepseek.com。
- 模型 ID：deepseek-flash；2026-11-03 官方文档确认有效，用户已报告实际调用成功。
- 使用 OpenAI Python SDK 的 Chat Completions 兼容接口，实际请求目标由 base_url 指定。DeepSeek 参数与响应以 DeepSeek 文档为准。
- config.py/load_settings 显式加载 .env，已有进程环境变量优先，检查三个必要字段。

参考：[DeepSeek 首次调用](https://api-docs.deepseek.com/)、[OpenAI Python SDK](https://developers.openai.com/api/reference/python)。

## 当前验证边界

2026-11-04 本地合并验收：Ran 16 tests in 0.027s / OK。其中十二项位于 test/test_model_client.py 和 test/test_cli.py；另四项为仓库外的本地验收脚本，批量覆盖默认/自定义 token 上限、六种非法参数、十二种异常响应结构、五种 HTTP 状态到 CLI 的失败出口。仓库内命令仍运行十二项，不会显示十六项。PyCharm 使用项目 .venv/Scripts/python.exe。

用户手工 CLI 帮助/纯空白/真实问题退出码为 0/2/0。助手本轮仅使用模拟依赖，未重发真实请求。模拟验证不证明真实服务错误映射、网络故障或所有协议损坏情况；原始 JSON 解析失败等 SDK 解析边界尚未专项覆盖。完整证据见 plan/研发进度Day 1.md。

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
