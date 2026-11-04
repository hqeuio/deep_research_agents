import argparse
import sys
from model_client import ask_once, ModelCallError

def main(argv: list[str] | None=None) -> int:
    parser = argparse.ArgumentParser(description="研发技术问答，目前支持单次模型调用")
    parser.add_argument("question", help="要询问模型的问题")
    args = parser.parse_args(argv)

    try:
        answer = ask_once(args.question)
    except ValueError as error:
        print(f"输入或配置错误：{error}", file=sys.stderr)
        return 2
    except ModelCallError as error:
        print(f"[{error.kind}] {error}", file=sys.stderr)
        return 1

    print(answer)
    return 0
if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))