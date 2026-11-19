from agent_graph import build_graph, build_initial_state

class AgentRunError(RuntimeError):
    pass
# 放在函数外，因此模块加载时只编译一次图。开头的 _ 是 Python 的命名惯例，表示这是模块内部使用的变量
_GRAPH = build_graph()

def run_agent(
    question: str,
    max_model_calls: int = 3,
    max_tokens: int | None = None,
) -> str:
    initial_state = build_initial_state(
        question,
        max_model_calls=max_model_calls,
        max_tokens=max_tokens,
    )
    final_state = _GRAPH.invoke(
        initial_state,
        config={"recursion_limit": 2 * max_model_calls + 1},
    )
    answer = final_state["answer"]
    if answer is None:
        raise AgentRunError("达到模型请求上限，但任务尚未完成")
    return answer


if __name__ == "__main__":
    print(run_agent("用一句话解释什么是 rag"))
