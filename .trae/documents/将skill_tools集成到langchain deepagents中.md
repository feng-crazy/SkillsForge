# 集成计划

## 1. 了解集成需求
- deepagents的agent使用普通Python函数作为工具，带有类型注解和docstring
- skill_tools目前使用异步类方法，返回特定的ToolResult对象
- 需要将skill_tools转换为deepagents兼容的格式

## 2. 实现集成步骤

### 2.1 修改skill_tool.py，创建deepagents兼容的工具
- 创建同步版本的get_skill工具，直接返回技能内容
- 保持现有的SkillLoader和相关逻辑不变

### 2.2 修改deepagent_example/agent.py
- 导入skill_tools模块
- 初始化技能加载器，发现并加载技能
- 将技能元数据添加到系统提示中
- 将get_skill工具添加到agent的工具列表中

### 2.3 确保技能加载路径正确
- 确保技能加载器能够正确找到skills目录（使用项目根目录下的skill-examples）

## 3. 测试集成效果
- 运行agent，验证技能是否被正确发现
- 测试agent是否能够使用get_skill工具获取技能内容

## 4. 预期结果
- agent能够在系统提示中看到可用技能列表
- agent能够使用get_skill工具获取技能详细内容
- 技能内容能够被正确注入到agent的上下文环境中

## 5. 代码修改点
- `skill_tool.py`: 添加deepagents兼容的工具创建函数
- `deepagent_example/agent.py`: 集成技能加载器和工具

## 6. 技术要点
- 将异步工具转换为同步函数
- 确保技能元数据正确添加到系统提示
- 保持现有代码结构不变，最小化修改

## 7. 集成后的工作流程
1. 启动agent时，自动发现并加载所有技能
2. 技能元数据（名称、描述）添加到系统提示中
3. Agent根据需求使用get_skill工具获取特定技能的完整内容
4. 技能内容被注入到agent的上下文，指导agent执行任务