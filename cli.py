import argparse
import sys
from model_client import ModelCallError
from agent import run_agent, AgentRunError
from tools import ToolCallError

def main(argv: list[str] | None=None) -> int:
    parser = argparse.ArgumentParser(description="研发技术问答")
    parser.add_argument("question", help="要询问模型的问题")
    args = parser.parse_args(argv)

    try:
        answer = run_agent(args.question)
    except ValueError as error:
        print(f"输入或配置错误：{error}", file=sys.stderr)
        return 2
    except (ModelCallError, ToolCallError) as error:
        print(f"[{error.kind}] {error}", file=sys.stderr)
        return 1
    except AgentRunError as error:
        print(f"模型调用次数到达上限：{error}", file=sys.stderr)
        return 1

    print(answer)
    return 0
if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))