"""
技能加载器 - 加载 Claude 技能

支持从 SKILL.md 文件加载技能并将其提供给 Agent
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml


@dataclass
class Skill:
    """技能数据结构"""

    name: str
    description: str
    content: str
    license: Optional[str] = None
    allowed_tools: Optional[List[str]] = None
    metadata: Optional[Dict[str, str]] = None
    skill_path: Optional[Path] = None

    def to_prompt(self) -> str:
        """将技能转换为提示格式"""
        return f"""
# Skill: {self.name}

{self.description}

---

{self.content}
"""


class SkillLoader:
    """技能加载器"""

    def __init__(self, skills_dir: str = "./skills"):
        """
        初始化技能加载器

        参数:
            skills_dir: 技能目录路径
        """
        self.skills_dir = Path(skills_dir)
        self.loaded_skills: Dict[str, Skill] = {}

    def load_skill(self, skill_path: Path) -> Optional[Skill]:
        """
        从单个 SKILL.md 文件加载技能

        参数:
            skill_path: SKILL.md 文件路径

        返回:
            Skill 对象；加载失败时返回 None
        """
        try:
            content = skill_path.read_text(encoding="utf-8")

            # 解析 YAML 头信息
            frontmatter_match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)

            if not frontmatter_match:
                print(f"⚠️  {skill_path} missing YAML frontmatter")
                return None

            frontmatter_text = frontmatter_match.group(1)
            skill_content = frontmatter_match.group(2).strip()

            # 解析 YAML
            try:
                frontmatter = yaml.safe_load(frontmatter_text)
            except yaml.YAMLError as e:
                print(f"❌ Failed to parse YAML frontmatter: {e}")
                return None

            # 必需字段
            if "name" not in frontmatter or "description" not in frontmatter:
                print(f"⚠️  {skill_path} missing required fields (name or description)")
                return None

            # 获取技能目录（SKILL.md 的父目录）
            skill_dir = skill_path.parent

            # 将内容中的相对路径替换为绝对路径。
            # 这样可以确保脚本和资源在任意工作目录下都能被找到
            processed_content = self._process_skill_paths(skill_content, skill_dir)

            # 创建 Skill 对象
            skill = Skill(
                name=frontmatter["name"],
                description=frontmatter["description"],
                content=processed_content,
                license=frontmatter.get("license"),
                allowed_tools=frontmatter.get("allowed-tools"),
                metadata=frontmatter.get("metadata"),
                skill_path=skill_path,
            )

            return skill

        except Exception as e:
            print(f"❌ Failed to load skill ({skill_path}): {e}")
            return None

    def _process_skill_paths(self, content: str, skill_dir: Path) -> str:
        """
        处理技能内容，将相对路径替换为绝对路径。

        支持 Progressive Disclosure Level 3+：将相对文件引用转换为绝对路径，便于 Agent 读取嵌套资源。

        参数:
            content: 原始技能内容
            skill_dir: 技能目录路径

        返回:
            已处理、包含绝对路径的内容
        """
        import re

        # 模式1：目录路径（scripts/, examples/, templates/, reference/）
        def replace_dir_path(match):
            prefix = match.group(1)  # 例如 "python " 或 "`"
            rel_path = match.group(2)  # 例如 "scripts/with_server.py"

            abs_path = skill_dir / rel_path
            if abs_path.exists():
                return f"{prefix}{abs_path}"
            return match.group(0)

        pattern_dirs = r"(python\s+|`)((?:scripts|examples|templates|reference)/[^\s`\)]+)"
        content = re.sub(pattern_dirs, replace_dir_path, content)

        # 模式2：直接的 markdown/文档引用（forms.md, reference.md 等）
        # 匹配类似 "see reference.md" 或 "read forms.md" 的短语
        def replace_doc_path(match):
            prefix = match.group(1)  # 例如 "see ", "read "
            filename = match.group(2)  # 例如 "reference.md"
            suffix = match.group(3)  # 例如 标点或空白

            abs_path = skill_dir / filename
            if abs_path.exists():
                # 为 Agent 提供有用的读取说明
                return f"{prefix}`{abs_path}` (use read_file to access){suffix}"
            return match.group(0)

        # 匹配模式，例如: "see reference.md" 或 "read forms.md"
        pattern_docs = r"(see|read|refer to|check)\s+([a-zA-Z0-9_-]+\.(?:md|txt|json|yaml))([.,;\s])"
        content = re.sub(pattern_docs, replace_doc_path, content, flags=re.IGNORECASE)

        # 模式3：Markdown 链接 - 支持多种格式：
        # - [`filename.md`](filename.md) - 简单文件名
        # - [text](./reference/file.md) - 带 ./ 的相对路径
        # - [text](scripts/file.js) - 目录路径
        # 匹配类似: "Read [`docx-js.md`](docx-js.md)" 或 "Load [Guide](./reference/guide.md)"
        def replace_markdown_link(match):
            prefix = match.group(1) if match.group(1) else ""  # 例如 "Read ", "Load ", 或空
            link_text = match.group(2)  # 例如 "`docx-js.md`" 或 "Guide"
            filepath = match.group(3)  # 例如 "docx-js.md", "./reference/file.md", "scripts/file.js"

            # 如果存在则移除前导的 ./
            clean_path = filepath[2:] if filepath.startswith("./") else filepath

            abs_path = skill_dir / clean_path
            if abs_path.exists():
                # 保持链接文本样式（有无反引号）
                return f"{prefix}[{link_text}](`{abs_path}`) (use read_file to access)"
            return match.group(0)

        # 匹配带有可选前缀词的 markdown 链接模式
        # 捕获：（可选前缀词）[链接文本]（包含 ./ 的完整文件路径）
        pattern_markdown = (
            r"(?:(Read|See|Check|Refer to|Load|View)\s+)?\[(`?[^`\]]+`?)\]\(((?:\./)?[^)]+\.(?:md|txt|json|yaml|js|py|html))\)"
        )
        content = re.sub(pattern_markdown, replace_markdown_link, content, flags=re.IGNORECASE)

        return content

    def discover_skills(self) -> List[Skill]:
        """
        在技能目录中发现并加载所有技能

        返回:
            技能列表
        """
        skills = []

        if not self.skills_dir.exists():
            print(f"⚠️  Skills directory does not exist: {self.skills_dir}")
            return skills

        # 递归查找所有 SKILL.md 文件
        for skill_file in self.skills_dir.rglob("SKILL.md"):
            skill = self.load_skill(skill_file)
            if skill:
                skills.append(skill)
                self.loaded_skills[skill.name] = skill

        return skills

    def get_skill(self, name: str) -> Optional[Skill]:
        """
        获取已加载的技能

        参数:
            name: 技能名称

        返回:
            Skill 对象；未找到时返回 None
        """
        return self.loaded_skills.get(name)

    def list_skills(self) -> List[str]:
        """
        列出所有已加载技能的名称

        返回:
            技能名称列表
        """
        return list(self.loaded_skills.keys())

    def get_skills_metadata_prompt(self) -> str:
        """
        生成仅包含所有技能元数据（名称 + 描述）的提示。
        这实现了 Progressive Disclosure - Level 1。

        返回:
            仅包含元数据的提示字符串
        """
        if not self.loaded_skills:
            return ""

        prompt_parts = ["## Available Skills\n"]
        prompt_parts.append("You have access to specialized skills. Each skill provides expert guidance for specific tasks.\n")
        prompt_parts.append("Load a skill's full content using the appropriate skill tool when needed.\n")

        # 列出所有技能及其描述
        for skill in self.loaded_skills.values():
            prompt_parts.append(f"- `{skill.name}`: {skill.description}")

        return "\n".join(prompt_parts)
