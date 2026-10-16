"""命令行测试脚本：不起 HTTP 服务，直接在终端模拟骗子和 AI 对话"""
import uuid
from agent.graph import run_turn
from utils.logger import logger
from rag.vector_store import ensure_vector_store


def main():
    ensure_vector_store()  # 自动就绪向量库，用户无感

    print("=" * 60)
    print("反诈诱饵 Agent - 命令行测试")
    print("输入骗子说的话，AI 会扮演王阿姨回复")
    print("输入 quit 退出")
    print("=" * 60)

    session_id = f"sess_{uuid.uuid4().hex[:12]}"

    while True:
        scammer_input = input("\n骗子> ").strip()
        if scammer_input.lower() in ("quit", "exit", "q"):
            print("结束对话。")
            break

        result = run_turn(session_id, scammer_input, caller_number="cli_test")
        print(f"王阿姨> {result['reply']}")
        if result.get("leads"):
            print(f"  [抽到线索: {result['leads']}]")


if __name__ == "__main__":
    main()
