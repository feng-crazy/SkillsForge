"""SkillsForge middleware for deepagents.

This middleware integrates SkillsForge with deepagents, allowing agents to use
SkillsForge's skill loading capabilities with progressive disclosure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Callable, Awaitable

from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ModelRequest,
    ModelResponse,
    PrivateStateAttr,
)
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

from skill_loader import SkillLoader

if TYPE_CHECKING:
    from deepagents.backends.protocol import BackendProtocol


class SkillsForgeState(AgentState):
    """State for the SkillsForge middleware."""

    skills_metadata: Annotated[list[dict], PrivateStateAttr]
    """List of loaded skill metadata from SkillsForge."""


class SkillsForgeStateUpdate(AgentState):
    """State update for the SkillsForge middleware."""

    skills_metadata: list[dict]
    """List of loaded skill metadata to merge into state."""


SKILLS_SYSTEM_PROMPT = """

## Skills System (SkillsForge)

You have access to a skills library provided by SkillsForge that offers specialized capabilities and domain knowledge.

**Available Skills:**

{skills_list}

**How to Use Skills (Progressive Disclosure):**

Skills follow a **progressive disclosure** pattern - you see their name and description above, but only read full instructions when needed:

1. **Recognize when a skill applies**: Check if the user's task matches a skill's description
2. **Load the skill's full instructions**: Use the `get_skill` tool with the skill name
3. **Follow the skill's instructions**: The skill content contains step-by-step workflows, best practices, and examples
4. **Access supporting files**: Skills may include helper scripts, configs, or reference docs

**When to Use Skills:**
- User's request matches a skill's domain (e.g., "research X" -> web-research skill)
- You need specialized knowledge or structured workflows
- A skill provides proven patterns for complex tasks

Remember: Skills make you more capable and consistent. When in doubt, check if a skill exists for the task!
"""


class SkillsForgeMiddleware(AgentMiddleware):
    """Middleware for integrating SkillsForge with deepagents.

    Loads skills from SkillsForge and injects them into the system prompt
    using progressive disclosure (metadata first, full content on demand).

    Example:
        ```python
        from skillsforge.skill_middleware import SkillsForgeMiddleware

        middleware = SkillsForgeMiddleware(
            skills_dir="./skill-examples"
        )
        ```

    Args:
        skills_dir: Path to the directory containing skills
    """

    state_schema = SkillsForgeState

    def __init__(self, *, skills_dir: str = "./skill-examples") -> None:
        """Initialize the SkillsForge middleware.

        Args:
            skills_dir: Path to the directory containing skills
        """
        self.skills_dir = skills_dir
        self.skill_loader = SkillLoader(skills_dir)
        self.system_prompt_template = SKILLS_SYSTEM_PROMPT
        
        # Discover skills on initialization
        self.skills = self.skill_loader.discover_skills()
        print(f"✅ SkillsForge: 已发现 {len(self.skills)} 个 Claude 技能")

    def _format_skills_list(self) -> str:
        """Format skills metadata for display in system prompt."""
        if not self.skills:
            return f"(No skills available yet. You can create skills in {self.skills_dir})"

        lines = []
        for skill in self.skills:
            lines.append(f"- **{skill.name}**: {skill.description}")

        return "\n".join(lines)

    def modify_request(self, request: ModelRequest) -> ModelRequest:
        """Inject skills documentation into a model request's system prompt.

        Args:
            request: Model request to modify

        Returns:
            New model request with skills documentation injected into system prompt
        """
        skills_list = self._format_skills_list()

        skills_section = self.system_prompt_template.format(
            skills_list=skills_list,
        )

        if request.system_prompt:
            system_prompt = request.system_prompt + "\n\n" + skills_section
        else:
            system_prompt = skills_section

        return request.override(system_prompt=system_prompt)

    def before_agent(self, state: SkillsForgeState, runtime: Runtime, config: RunnableConfig) -> SkillsForgeStateUpdate | None:
        """Load skills metadata before agent execution (synchronous).

        Args:
            state: Current agent state.
            runtime: Runtime context.
            config: Runnable config.

        Returns:
            State update with skills_metadata populated
        """
        # Create metadata for each skill
        skills_metadata = []
        for skill in self.skills:
            metadata = {
                "name": skill.name,
                "description": skill.description,
                "path": str(skill.skill_path) if skill.skill_path else "",
                "license": skill.license,
                "allowed_tools": skill.allowed_tools or []
            }
            skills_metadata.append(metadata)

        return SkillsForgeStateUpdate(skills_metadata=skills_metadata)

    async def abefore_agent(self, state: SkillsForgeState, runtime: Runtime, config: RunnableConfig) -> SkillsForgeStateUpdate | None:
        """Load skills metadata before agent execution (async).

        Args:
            state: Current agent state.
            runtime: Runtime context.
            config: Runnable config.

        Returns:
            State update with skills_metadata populated
        """
        # Create metadata for each skill
        skills_metadata = []
        for skill in self.skills:
            metadata = {
                "name": skill.name,
                "description": skill.description,
                "path": str(skill.skill_path) if skill.skill_path else "",
                "license": skill.license,
                "allowed_tools": skill.allowed_tools or []
            }
            skills_metadata.append(metadata)

        return SkillsForgeStateUpdate(skills_metadata=skills_metadata)

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """Inject skills documentation into the system prompt.

        Args:
            request: Model request being processed
            handler: Handler function to call with modified request

        Returns:
            Model response from handler
        """
        modified_request = self.modify_request(request)
        return handler(modified_request)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        """Inject skills documentation into the system prompt (async version).

        Args:
            request: Model request being processed
            handler: Async handler function to call with modified request

        Returns:
            Model response from handler
        """
        modified_request = self.modify_request(request)
        return await handler(modified_request)


__all__ = ["SkillsForgeMiddleware"]