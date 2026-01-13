"""
技能工具 - 用于代理按需加载技能

实现渐进披露（第2级）：需要时才加载完整技能内容
"""

from typing import Any, Dict, List, Optional

from base import Tool, ToolResult
from skill_loader import SkillLoader


class GetSkillTool(Tool):
    """用于获取特定技能详细信息的工具"""

    def __init__(self, skill_loader: SkillLoader):
        self.skill_loader = skill_loader

    @property
    def name(self) -> str:
        return "get_skill"

    @property
    def description(self) -> str:
        return "获取指定技能的完整内容和指导信息，用于执行特定类型的任务"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "skill_name": {
                    "type": "string",
                    "description": "要检索的技能名称（使用 list_skills 查看可用技能）",
                }
            },
            "required": ["skill_name"],
        }

    async def execute(self, skill_name: str) -> ToolResult:
        """获取指定技能的详细信息"""
        skill = self.skill_loader.get_skill(skill_name)

        if not skill:
            available = ", ".join(self.skill_loader.list_skills())
            return ToolResult(
                success=False,
                content="",
                error=f"技能 '{skill_name}' 不存在。可用技能：{available}",
            )

        # 返回完整的技能内容
        result = skill.to_prompt()
        return ToolResult(success=True, content=result)


def create_deepagent_skill_tools(
    skills_dir: str = "./skills",
) -> tuple[List[Any], Optional[SkillLoader]]:
    """
    创建deepagents兼容的技能工具
    
    参数：
        skills_dir: 技能目录路径
    
    返回：
        包含（工具列表，技能加载器）的元组
    """
    # 创建技能加载器
    loader = SkillLoader(skills_dir)
    
    # 发现并加载技能
    skills = loader.discover_skills()
    print(f"✅ 已发现 {len(skills)} 个 Claude 技能")
    
    # 定义同步版本的get_skill函数，兼容deepagents
    def get_skill(skill_name: str) -> str:
        """获取指定技能的完整内容和指导信息，用于执行特定类型的任务"""
        skill = loader.get_skill(skill_name)
        
        if not skill:
            available = ", ".join(loader.list_skills())
            return f"错误：技能 '{skill_name}' 不存在。可用技能：{available}"
        
        # 返回完整的技能内容
        return skill.to_prompt()
    
    # 仅创建get_skill工具
    tools = [
        get_skill,
    ]
    
    return tools, loader


def create_skill_tools(
    skills_dir: str = "./skills",
) -> tuple[List[Tool], Optional[SkillLoader]]:
    """
    创建技能工具以实现渐进披露

    仅提供 get_skill 工具 —— 代理通过系统提示中的元数据了解可用技能，
    然后按需加载。

    参数：
        skills_dir: 技能目录路径

    返回：
        包含（工具列表，技能加载器）的元组
    """
    # 创建技能加载器
    loader = SkillLoader(skills_dir)

    # 发现并加载技能
    skills = loader.discover_skills()
    print(f"✅ 已发现 {len(skills)} 个 Claude 技能")

    # 仅创建 get_skill 工具（渐进披露第2级）
    tools = [
        GetSkillTool(loader),
    ]

    return tools, loader
