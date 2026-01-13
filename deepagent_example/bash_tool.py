import subprocess
from langchain.tools import tool

@tool
def run_bash_command(command: str) -> str:
    """Run a bash command and return its stdout. Only allow safe commands like 'ls', 'cat', 'pwd'."""
    allowed_prefixes = ("ls", "cat", "pwd", "echo", "grep", "find")
    if not any(command.strip().startswith(prefix) for prefix in allowed_prefixes):
        return "Error: Command not allowed for security reasons."

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
            cwd="/tmp/sandbox"  # 限定工作目录增强安全
        )
        if result.returncode == 0:
            return result.stdout[:1000]  # 截断长输出
        else:
            return f"Error: {result.stderr}"
    except Exception as e:
        return f"Execution failed: {str(e)}"