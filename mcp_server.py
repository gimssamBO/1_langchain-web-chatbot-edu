from fastmcp import FastMCP
from dotenv import load_dotenv
from notion_client import Client
import json
import os

load_dotenv()

mcp = FastMCP("ExperimentResultServer")

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")

notion = Client(auth=NOTION_TOKEN)


@mcp.tool()
def read_experiment_result(file_path: str) -> dict:
    """
    모델 학습 결과 JSON 파일을 읽어 dict로 반환합니다.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


@mcp.tool()
def upload_experiment_to_notion(title: str, summary: str) -> str:
    """
    요약된 실험 결과를 Notion 페이지로 업로드합니다.
    """
    notion.pages.create(
        parent={"page_id": NOTION_PAGE_ID},
        properties={
            "title": {
                "title": [
                    {"text": {"content": title}}
                ]
            }
        },
        children=[
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": summary}
                        }
                    ]
                }
            }
        ]
    )
    return "Notion 업로드 완료"


if __name__ == "__main__":
    print("Experiment MCP Server is running...")
    mcp.run(transport="stdio")