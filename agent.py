from model_client import request_turn, parse_turn
from tools import NOTE_TOOL, execute_tool

class AgentRunError(RuntimeError):
    pass

def run_agent(question: str,max_model_calls: int = 3,max_tokens: int | None = None) -> str:
    question = question.strip()
    if not question:
        raise ValueError("question cannot be empty")
    if type(max_model_calls) is not int or max_model_calls < 1:
        raise ValueError("max_model_calls must be a positive integer")
    messages = [
        {
            "role": "system",
            "content": "你是技术资料助手。涉及演示笔记内容时先调用工具，依据返回的笔记回答，不编造查询结果。",
        },
        {"role": "user", "content": question},
    ]
    for i in range(max_model_calls):
        response = request_turn(messages, tools=[NOTE_TOOL], max_tokens=max_tokens)
        reason, message = parse_turn(response)
        if reason == "stop":
            return message.content.strip()
        elif i == max_model_calls - 1:
            raise AgentRunError("达到模型请求上限，任务尚未完成")

        call = message.tool_calls[0]
        result = execute_tool(call.function.name, call.function.arguments)

        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": [{
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments,
                },
            }]
        })
        messages.append({
            "role": "tool",
            "tool_call_id": call.id,
            "content": result,
        })


if __name__ == "__main__":
    print(run_agent("用一句话解释什么是 rag"))
