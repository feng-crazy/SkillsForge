# search_tool.py
import os
from tavily import TavilyClient
from typing import Literal
from dotenv import load_dotenv

load_dotenv()

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def internet_search(
    query: str,
    max_results: int = 3,
    topic: Literal["general", "news", "finance"] = "general",  # 移除不支持的 "science" 选项
    include_raw_content: bool = True,  # 关键：返回完整网页内容以触发文件保存
) -> dict:
    """Perform a web search and return results with raw HTML content."""
    print(f"[🔍 Searching] {query}")
    return tavily_client.search(
        query=query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic
    )