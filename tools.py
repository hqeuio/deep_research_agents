import json
NOTES = {
    "tool_calling": "[demo:tool_calling] 模型提出工具调用请求，程序校验并执行，再回传结果。",
    "rag": "[demo:rag] RAG 先检索资料，再将相关内容作为上下文交给模型生成回答。",
}

def lookup_note(topic: str) -> str:
    if not isinstance(topic, str):
        raise ValueError("topic must be a string")
    if topic not in NOTES:
        raise ValueError("unsupported topic")
    return NOTES[topic]

NOTE_TOOL = {
    "type": "function",
    "function": {
        "name": "lookup_note",
        "description": "按主题读取一条固定演示技术笔记；只支持 tool_calling 和 rag，不搜索外部资料。",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "enum": list(NOTES),
                    "description": "要读取的技术主题",
                }
            },
            "required": ["topic"],
            "additionalProperties": False,
        },
    },
}
# 注册表，关联工具名称和对应的工具执行函数
TOOL_REGISTRY = {"lookup_note": lookup_note}
class ToolCallError(RuntimeError):
    def __init__(self, kind:str, message:str):
        super().__init__(message)
        self.kind = kind

def execute_tool(name: str, arguments: str) -> str:
    if not isinstance(name, str) or name not in TOOL_REGISTRY:
        raise ToolCallError("unknown_tool", "工具未注册")
    if not isinstance(arguments, str):
        raise ToolCallError("invalid_arguments", "工具参数必须是 json 字符串")

    try:
        params = json.loads(arguments)
    except json.JSONDecodeError:
        raise ToolCallError("invalid_arguments", "工具参数不是有效 json") from None
    if not isinstance(params, dict) or set(params) != {"topic"}:
        raise ToolCallError("invalid_arguments", "工具参数必须且只能包含 topic")
    topic = params["topic"]
    if not isinstance(topic, str) or topic not in NOTES:
        raise ToolCallError("invalid_arguments", "topic 必须是受支持的主题字符串")

    try:
        result = TOOL_REGISTRY[name](topic=topic)
    except Exception:
        raise ToolCallError("execution", "工具执行失败") from None

    if not isinstance(result, str) or not result.strip():
        raise ToolCallError("execution", "工具未返回有效文本")
    return result
