
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from notion_client import Client
from pathlib import Path
import json
import os
import sys

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

mcp = FastMCP("ExperimentResultServer")

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")


@mcp.tool()
def read_experiment_result(file_path: str) -> dict:
    """모델 학습 결과 JSON 파일을 읽습니다."""

    path = Path(file_path)

    if not path.is_absolute():
        path = BASE_DIR / path

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@mcp.tool()
def upload_experiment_to_notion(
    title: str,
    summary: str
) -> str:
    """실험 결과를 Notion에 기록합니다."""

    if not NOTION_TOKEN or not NOTION_PAGE_ID:
        raise ValueError(
            "NOTION_TOKEN 또는 NOTION_PAGE_ID가 없습니다."
        )

    notion = Client(auth=NOTION_TOKEN)

    notion.pages.create(
        parent={"type": "page_id", "page_id": NOTION_PAGE_ID},
        properties={
            "title": {
                "type": "title",
                "title": [
                    {
                        "type": "text",
                        "text": {"content": title}
                    }
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
                            "text": {
                                "content": summary[:2000]
                            }
                        }
                    ]
                }
            }
        ]
    )

    return "Notion 업로드 완료"


if __name__ == "__main__":
    mcp.run(transport="stdio")
