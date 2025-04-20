from pydantic_ai import Agent, Tool
from pydantic_ai.mcp import MCPServerStdio
import asyncio
from datetime import datetime

mcp_fetch = MCPServerStdio(
    command="uvx",
    args=["mcp-server-fetch"],
)


def get_time() -> str:
  return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


agent = Agent(
    "gpt-4.1-mini",
    system_prompt=(
        "You are a helpful assistant. Use tools to achieve the user's goal."),
    mcp_servers=[mcp_fetch],
    tools=[Tool(get_time)])


async def main():
  async with agent.run_mcp_servers():
    prompt = """
        Please get the content of docs.replit.com/updates and summarize them. 
        Return the summary as well as the time you got the content.
        """
    result = await agent.run(prompt)
    print(result.output)


if __name__ == "__main__":
  asyncio.run(main())
