from openai import OpenAI # 导入负责请求和响应处理的 SDK 客户端
from config import load_settings
from openai import (
    AuthenticationError,
    APITimeoutError,
    APIConnectionError,
    APIStatusError,
)

class ModelCallError(RuntimeError):  # 自定义调用失败类型
    def __init__(self, kind: str, message: str):
        super().__init__(message)  # 保存异常说明，给用户看的
        self.kind = kind  # 保存分类，上层通过 error.kind 判断原因，给程序看的

def ask_once(question: str, max_tokens: int = 1024) -> str:
    question = question.strip()
    if not question:
        raise ValueError("question cannot be empty")
    if type(max_tokens) is not int or max_tokens < 1:
        raise ValueError("max_tokens must be a positive integer")
    # 获取地址，密钥和模型名称
    settings = load_settings()
    try:
        with OpenAI(
                api_key=settings["api_key"],
                base_url=settings["base_url"],
                timeout=30.0,
                max_retries=0,
        ) as client:
            response = client.chat.completions.create(
                model=settings["model"],
                messages=[
                    {"role": "system",
                     "content": "你是一个精通Agents相关知识的技术专家，请充分运用你的专业知识给出精确无误的回答"},
                    {"role": "user", "content": question},
                ],
                stream=False,
                max_tokens=max_tokens,
                extra_body={"thinking": {"type": "disabled"}},
            )
            choices = getattr(response, "choices", None)

            if not isinstance(choices, list) or not choices:
                raise ModelCallError("invalid_response", "模型响应没有有效候选回答")

            choice = choices[0]
            if getattr(choice, "finish_reason", None) != "stop":
                raise ModelCallError("invalid_response", "模型响应未正常结束")

            message = getattr(choice, "message", None)
            content = getattr(message, "content", None)
            if not isinstance(content, str) or not content.strip():
                raise ModelCallError("invalid_response", "模型响应没有有效文本")

            return content.strip()
    except AuthenticationError:
        raise ModelCallError("auth", "认证失败，请检查您的 API key 是否正确") from None
    except APITimeoutError:
        raise ModelCallError("timeout", "模型请求超时") from None
    except APIConnectionError:
        raise ModelCallError("connection", "无法连接模型服务") from None
    # from None 表示隐藏默认 traceback 中原始异常上下文的展示
    except APIStatusError as error:
        raise ModelCallError("service", f"模型服务返回 HTTP {error.status_code}，请求未成功") from None



if __name__ == "__main__":
    question = "用一句话解释什么是 API。"
    answer = ask_once(question)
    print(answer)
