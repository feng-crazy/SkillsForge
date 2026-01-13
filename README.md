# SkillsForge

SkillsForge 是一个轻量级、开源的 **Agent 能力扩展框架**，旨在让任意基于大语言模型（LLM）的智能体（Agent）能够通过加载标准化的 `skill.md` 文件动态获得新能力。

## 🌟 核心特性

- **模块化**：技能封装为独立的 `skill.md` 文件，便于共享和复用
- **零侵入**：只需集成 SkillsForge 即可扩展现有 Agent 能力
- **按需加载**：仅在需要时才加载技能完整内容，优化性能
- **兼容 Claude Skills 格式**：复用为 Claude 编写的 Skills 生态，实现"一次编写，多处运行"
- **渐进披露**：先提供技能元数据，再按需加载完整内容

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/skillsforge.git
cd skillsforge

# 安装依赖
pip3 install -e .
```

### 基本使用

```python
from skill_tool import create_skill_tools

# 创建技能工具
skill_tools, skill_loader = create_skill_tools(skills_dir="./skill-examples")

# 获取技能元数据
skills_metadata = skill_loader.get_skills_metadata_prompt()
print(skills_metadata)

# 使用 get_skill 工具获取技能详细内容
get_skill = skill_tools[0]
skill_content = get_skill("brand-guidelines")
print(skill_content)
```

## 📦 项目结构

```
skillsforge/
├── base.py                # 基础工具类定义
├── skill_loader.py        # 技能加载器，负责发现和加载技能
├── skill_tool.py          # 技能工具，提供 get_skill 功能
├── deepagent_example/     # 与 deepagents 集成示例
│   ├── agent.py           # 集成了技能工具的 deepagent
│   ├── bash_tool.py       # 示例 bash 工具
│   └── search_tool.py     # 示例搜索工具
├── skill-examples/        # 示例技能集合
│   ├── brand-guidelines/  # 品牌指南技能
│   ├── file-organizer/    # 文件组织技能
│   └── ...                # 更多示例技能
├── skills-ref/            # 技能参考实现
└── pyproject.toml         # 项目依赖配置
```

## 🛠️ 与 deepagents 集成

### 示例代码

```python
from skill_tool import create_deepagent_skill_tools
from deepagents import create_deep_agent

# 初始化技能工具和加载器
skill_tools, skill_loader = create_deepagent_skill_tools(
    skills_dir="./skill-examples"
)

# 添加技能元数据到系统提示
SYSTEM_PROMPT += "\n" + skill_loader.get_skills_metadata_prompt()

# 创建 DeepAgent
agent = create_deep_agent(
    model=llm,
    tools=[internet_search, run_bash_command] + skill_tools,
    system_prompt=SYSTEM_PROMPT,
    debug=True
)
```

### 集成步骤

1. **导入技能工具**：`from skill_tool import create_deepagent_skill_tools`
2. **初始化技能加载器**：创建技能工具和加载器实例
3. **添加技能元数据到系统提示**：将技能列表添加到系统提示中
4. **将技能工具添加到 agent**：将 `get_skill` 工具添加到 agent 的工具列表中

## 📝 skill.md 格式

SkillsForge 支持标准的 Claude Skills 格式，示例如下：

```markdown
---
name: brand-guidelines
description: 品牌指南技能，用于生成符合品牌规范的内容
license: MIT
allowed-tools: [read_file, write_file]
---

# 品牌指南

## 品牌色调
- 主色：#007bff
- 辅助色：#6c757d
- 强调色：#ffc107

## 品牌语音
- 专业、友好、清晰
- 避免使用行话和复杂术语
- 保持一致的语调

## 使用方法
1. 了解品牌需求
2. 遵循品牌色调和语音
3. 生成符合规范的内容
```

## 🔧 技能加载器 API

### 初始化

```python
from skill_loader import SkillLoader

# 创建技能加载器
loader = SkillLoader(skills_dir="./skills")
```

### 方法

- `discover_skills()`：发现并加载所有技能
- `get_skill(skill_name)`：获取指定技能的详细信息
- `list_skills()`：列出所有可用技能名称
- `get_skills_metadata_prompt()`：生成包含所有技能元数据的提示

## 🤝 贡献指南

### 提交新技能

1. 在 `skill-examples` 目录下创建新的技能目录
2. 编写符合规范的 `skill.md` 文件
3. 确保技能描述清晰、使用方法明确
4. 提交 Pull Request

### 开发新功能

1. Fork 仓库
2. 创建功能分支
3. 编写代码和测试
4. 运行测试确保通过
5. 提交 Pull Request

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## 📞 联系方式

如有问题或建议，欢迎通过以下方式联系：

- 提交 [Issue](https://github.com/yourusername/skillsforge/issues)
- 发送邮件到：your.email@example.com

## 🙏 致谢

感谢所有为 SkillsForge 项目做出贡献的开发者！

---

**SkillsForge** - 让 Agent 能力无限扩展 🚀