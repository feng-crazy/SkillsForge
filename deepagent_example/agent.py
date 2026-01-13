# main.py
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent

from search_tool import internet_search
from bash_tool import run_bash_command

# 导入技能工具
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from skill_tool import create_deepagent_skill_tools

load_dotenv()

# 1. 初始化 LLM（支持 OpenAI 兼容模型）
llm = init_chat_model(
    model="qwen-plus",  # 或 "deepseek-chat", "claude-3-5-sonnet"
    model_provider="openai",  # 明确指定模型提供商为openai，使用兼容的API接口
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),  # 可选
    temperature=0.3
)

# 2. 初始化技能工具和加载器
# 使用项目根目录下的skill-examples目录作为技能目录
skill_tools, skill_loader = create_deepagent_skill_tools(
    skills_dir=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skill-examples")
)

# 3. 系统提示词（引导 Agent 使用规划和文件）
SYSTEM_PROMPT = """
你是一位专业研究助理。你的任务是根据用户需求完成深度研究并撰写报告。

## 工作流程
1. 首先使用 write_todos 工具制定详细研究计划（至少3个步骤）
2. 逐步执行每个待办事项，使用 internet_search 收集信息
3. 大量内容会自动保存到文件，请用 read_file 查看
4. 完成研究后，使用 task 工具委派子 Agent 撰写最终报告
5. 最终输出结构清晰、引用来源的研究报告

## 注意
- 不要一次性搜索太多内容
- 每完成一个步骤，更新 todo 列表
- 报告需包含摘要、正文、参考文献
"""

# 4. 添加技能元数据到系统提示
if skill_loader:
    skills_metadata = skill_loader.get_skills_metadata_prompt()
    SYSTEM_PROMPT += "\n" + skills_metadata

# 5. 创建 DeepAgent（自动启用所有内置 Middleware）
agent = create_deep_agent(
    model=llm,
    tools=[internet_search, run_bash_command] + skill_tools,
    system_prompt=SYSTEM_PROMPT,
    debug=True  # 开启调试日志
)


# 继续在 main.py 末尾添加
async def run_agent():
    user_input = "请研究量子计算在2025年的最新突破，并写一份1000字报告。"
    
    async for chunk in agent.astream({"messages": [{"role": "user", "content": user_input}]}):
        if "messages" in chunk:
            message = chunk["messages"][-1]
            if hasattr(message, 'content') and message.content:
                print(message.content, end="", flush=True)
    print("\n✅ 任务完成！")

# 运行
import asyncio
asyncio.run(run_agent())