
import asyncio
import sys
from pathlib import Path
from contextlib import AsyncExitStack
from dotenv import load_dotenv

from mcp import ClientSession
from mcp.client.stdio import (
    stdio_client,
    StdioServerParameters
)

from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.agents import create_agent

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env", override=True)


async def run():
    async with AsyncExitStack() as stack:

        # 1. MCP Server 연결
        params = StdioServerParameters(
            command=sys.executable,
            args=[str(BASE_DIR / "mcp_server.py")],
            cwd=str(BASE_DIR)
        )

        read, write = await stack.enter_async_context(
            stdio_client(params)
        )

        session = await stack.enter_async_context(
            ClientSession(read, write)
        )

        await session.initialize()

        print("MCP 서버 연결 성공")

        # 2. MCP Tool 로드
        tools = await load_mcp_tools(session)

        print("등록된 MCP Tools:")
        for tool in tools:
            print("-", tool.name)

        # 3. LLM 준비
        llm = ChatOpenAI(
            model="gpt-5-nano",
            temperature=0
        )

        # 4. Agent 생성
        agent = create_agent(llm, tools)

        # 5. 사용자 질문
        user_question = """
        train_result.json 파일을 읽고
        모델 학습 결과를 요약해줘.

        요약에는 주요 성능 지표와
        실험 결과에 대한 핵심 내용을 포함해줘.

        요약한 결과를 Notion에 기록해줘.

        제목은 '모델 실험 결과 - step 500'으로 해줘.
        """

        result = await agent.ainvoke({
            "messages": [
                ("user", user_question)
            ]
        })

        print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(run())
