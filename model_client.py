from openai import OpenAI # 导入负责请求和响应处理的 SDK 客户端
from config import load_settings
from openai import (
    AuthenticationError,
    APITimeoutError,
    APIConnectionError,
    APIStatusError,
)
from openai.types.chat import ChatCompletion, ChatCompletionMessage

class ModelCallError(RuntimeError):  # 自定义调用失败类型
    def __init__(self, kind: str, message: str):
        super().__init__(message)  # 保存异常说明，给用户看的
        self.kind = kind  # 保存分类，上层通过 error.kind 判断原因，给程序看的

def request_turn(messages: list[dict], *,
                 tools:list[dict] | None = None,
                 max_tokens: int | None = None)->ChatCompletion:
    if not isinstance(messages, list) or not messages:
        raise ValueError("messages must be a non-empty list")
    if max_tokens is not None:
        if type(max_tokens) is not int or max_tokens < 1:
            raise ValueError("max_tokens must be a positive integer")
    request_options = {}
    if max_tokens is not None:
        request_options["max_tokens"] = max_tokens
    if tools is not None:
        request_options["tools"] = tools
    # 获取地址，密钥和模型名称
    settings = load_settings()
    try:
        with OpenAI(
                api_key=settings["api_key"],
                base_url=settings["base_url"],
                timeout=30.0,
                max_retries=0,
        ) as client:
            return client.chat.completions.create(
                model=settings["model"],
                messages=messages,
                stream=False,
                extra_body={"thinking": {"type": "disabled"}},
                **request_options
            )
    except AuthenticationError:
        raise ModelCallError("auth", "认证失败，请检查您的 API key 是否正确") from None
    except APITimeoutError:
        raise ModelCallError("timeout", "模型请求超时") from None
    except APIConnectionError:
        raise ModelCallError("connection", "无法连接模型服务") from None
    # from None 表示隐藏默认 traceback 中原始异常上下文的展示
    except APIStatusError as error:
        raise ModelCallError("service", f"模型服务返回 HTTP {error.status_code}，请求未成功") from None

def parse_turn(response: ChatCompletion) -> tuple[str, ChatCompletionMessage]:
    choices = getattr(response, "choices", None)
    if not isinstance(choices, list) or not choices:
        raise ModelCallError("invalid_response", "模型响应没有有效候选回答")
    choice = choices[0]
    reason = getattr(choice, "finish_reason", None)
    if reason not in ("stop", "tool_calls"):
        raise ModelCallError("invalid_response", "模型响应未正常结束")
    message = getattr(choice, "message", None)
    if message is None:
        raise ModelCallError("invalid_response", "模型响应缺少消息")
    content = getattr(message, "content", None)
    calls = getattr(message, "tool_calls", None)
    if calls is not None and not isinstance(calls, list):
        raise ModelCallError("invalid_response", "工具调用列表格式错误")

    if reason == "stop":
        if calls:
            raise ModelCallError("invalid_response", "文本结束标志与工具请求冲突")
        if not isinstance(content, str) or not content.strip():
            raise ModelCallError("invalid_response", "模型响应没有有效文本")
    else:
        if not calls or len(calls) != 1:
            raise ModelCallError("invalid_response", "当前每轮必须恰好包含一个工具调用")
        if content is not None and not isinstance(content, str):
            raise ModelCallError("invalid_response", "工具请求正文格式错误")

        call = calls[0]
        call_id = getattr(call, "id", None)
        if not isinstance(call_id, str) or not call_id.strip():
            raise ModelCallError("invalid_response", "工具调用缺少有效编号")
        if getattr(call, "type", None) != "function":
            raise ModelCallError("invalid_response", "不支持的工具调用类型")

        function = getattr(call, "function", None)
        name = getattr(function, "name", None)
        arguments = getattr(function, "arguments", None)
        if not isinstance(name, str) or not name.strip():
            raise ModelCallError("invalid_response", "工具调用缺少有效名称")
        if not isinstance(arguments, str):
            raise ModelCallError("invalid_response", "工具调用缺少参数字符串")
    return reason, message
