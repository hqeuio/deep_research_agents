from typing import TypedDict
from model_client import request_turn, parse_turn
from tools import NOTE_TOOL, execute_tool
from langgraph.graph import START, END, StateGraph

class AgentState(TypedDict):
    messages: list[dict]
    model_calls: int
    max_model_calls: int
    max_tokens: int | None
    answer: str | None
# 构建图的初始状态
def build_initial_state(question: str, max_model_calls: int=3, max_tokens: int | None=None) -> AgentState:
    question = question.strip()
    if not question:
        raise ValueError("question cannot be empty")
    if type(max_model_calls) is not int or max_model_calls < 1:
        raise ValueError("max_model_calls must be a positive integer")

    return AgentState(
        messages=[
            {"role": "system","content": "你是技术资料助手。涉及演示笔记内容时先调用工具，依据返回的笔记回答，不编造查询结果。"},
            {"role": "user", "content": question},
        ],
        model_calls = 0,
        max_model_calls = max_model_calls,
        max_tokens = max_tokens,
        answer = None,
    )
# 模型节点请求模型并返回状态更新
def model_node(state: AgentState) -> dict:
    response = request_turn(
        state["messages"],
        tools=[NOTE_TOOL],
        max_tokens=state["max_tokens"]
    )
    reason, message = parse_turn(response)
    model_calls = state["model_calls"] + 1

    if reason == "stop":
        return {
            "model_calls": model_calls,
            "answer": message.content.strip(),
        }
    call = message.tool_calls[0]
    new_message = [
        {
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
        },
    ]

    return {
        "model_calls": model_calls,
        "messages": state["messages"] + new_message,
    }

# 工具节点执行请求并追加结果消息
def tool_node(state: AgentState) -> dict:
    # -1 是因为我们要处理的是最新的一次工具调用请求
    assistant_message = state["messages"][-1]
    call = assistant_message["tool_calls"][0]
    # 这里用 call["function"]，模型节点里用 call.function。
    # 模型节点拿到的是 SDK 对象，用点号读属性。它把请求放进历史时组装成了字典，
    # 所以工具节点用方括号取值。
    function = call["function"]

    result = execute_tool(function["name"], function["arguments"])
    tool_message = {
        "role": "tool",
        "tool_call_id": call["id"],
        "content": result,
    }
    return {
        "messages": state["messages"] + [tool_message],
    }
# 模型节点结束后，选择结束或进入工具节点
def router(state: AgentState) -> str:
    # 在模型调用次数耗尽之前得到了最终答案
    if state["answer"] is not None:
        return "done"
    # 次数用完后还想调用工具
    if state["model_calls"] >= state["max_model_calls"]:
        return "exhausted"
    # 合法的工具调用
    return "tool"

def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("model", model_node)
    builder.add_node("tools", tool_node)

    builder.add_edge(START, "model")
    builder.add_conditional_edges(
        "model",
        router,
        {
            "done": END,
            "exhausted": END,
            "tool": "tools",
        },
    )
    builder.add_edge("tools", "model")

    return builder.compile()
